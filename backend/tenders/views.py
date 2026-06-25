"""
Django REST API Views for Tender Intelligence
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from decimal import Decimal, InvalidOperation
import traceback
import re

from .models import (
    Tender,
    TenderSection,
    TenderWorkItem,
    TenderEligibility,
    TenderRisk,
    TenderConflict,
    BidScenario,
    TenderProposal,
    TenderNegotiation,
    PreBidQuestion,
    CompanyProfile
)

from .serializers import (
    TenderListSerializer,
    TenderDetailSerializer,
    TenderUploadSerializer,
    TenderSectionSerializer,
    TenderWorkItemSerializer,
    TenderRiskSerializer,
    TenderConflictSerializer,
    BidScenarioSerializer,
    TenderProposalSerializer,
    TenderNegotiationSerializer,
    PreBidQuestionSerializer,
    CompanyProfileSerializer
)

from .tender_parser import TenderParser, BOQClassifier
from .tender_vector_service import tender_vector_service
from .tender_intelligence import (
    MetadataExtractor,
    RiskDetector,
    ConflictDetector,
    EligibilityValidator,
    ProposalGenerator,
    WinSimulator,
    PreBidQuestionGenerator
)
from .boq_optimizer import BOQCostModeler, MarginOptimizer, NegotiationAutomation


class TenderViewSet(viewsets.ModelViewSet):
    """ViewSet for Tender CRUD operations"""

    permission_classes = [IsAuthenticated]
    queryset = Tender.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return TenderListSerializer
        elif self.action == 'create':
            return TenderUploadSerializer
        else:
            return TenderDetailSerializer

    def get_queryset(self):
        # Filter by user
        return Tender.objects.filter(uploaded_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    @action(detail=False, methods=['post'])
    def upload_and_analyze(self, request):
        """
        Upload tender PDF and perform complete analysis

        POST /api/tenders/upload_and_analyze/
        Body: { "title": "...", "pdf_file": file }
        """
        try:
            # Validate upload
            serializer = TenderUploadSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Create tender
            tender = serializer.save(
                uploaded_by=request.user,
                status='ANALYZING'
            )

            # Get PDF path
            _tmp_pdf_path = None
            if tender.pdf_file:
                pdf_path = tender.pdf_file.path
            elif tender.pdf_url:
                # Download PDF from URL
                import requests as http_requests
                import tempfile
                import os
                try:
                    r = http_requests.get(tender.pdf_url, timeout=60, stream=True)
                    r.raise_for_status()
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                        for chunk in r.iter_content(chunk_size=8192):
                            tmp.write(chunk)
                        pdf_path = tmp.name
                    _tmp_pdf_path = pdf_path
                except Exception as url_err:
                    return Response(
                        {'error': f'Failed to download PDF from URL: {url_err}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {'error': 'No PDF file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Parse PDF
            parser = TenderParser()
            try:
                parsed_data = parser.parse_pdf(pdf_path)
            finally:
                # Clean up temp file if created from URL download
                if _tmp_pdf_path:
                    try:
                        os.unlink(_tmp_pdf_path)
                    except Exception:
                        pass

            # Save metadata
            metadata = parsed_data['metadata']

            # Set metadata with fallbacks
            tender.reference_number = metadata.get('reference_number', tender.title[:50] if tender.title else 'REF-UNKNOWN')

            if 'estimated_value' in metadata and metadata['estimated_value']:
                tender.estimated_value = Decimal(str(metadata['estimated_value']))

            if 'submission_deadline' in metadata and metadata['submission_deadline']:
                try:
                    from datetime import datetime
                    import pytz
                    dl = metadata['submission_deadline']
                    tz = pytz.timezone('Asia/Kolkata')
                    if isinstance(dl, str):
                        for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y', '%Y-%m-%d'):
                            try:
                                dt = datetime.strptime(dl, fmt)
                                tender.submission_deadline = tz.localize(dt)
                                break
                            except ValueError:
                                continue
                    else:
                        tender.submission_deadline = tz.localize(datetime.combine(dl, datetime.min.time()))
                except Exception:
                    pass

            cp = metadata.get('completion_period_days') or metadata.get('completion_period')
            if cp:
                tender.completion_period_days = int(cp)
            else:
                tender.completion_period_days = 180

            if 'emd_amount' in metadata and metadata['emd_amount']:
                tender.emd_amount = Decimal(str(metadata['emd_amount']))

            # Set scope of work from full text preview
            if parsed_data['full_text']:
                tender.scope_of_work = parsed_data['full_text'][:1000]

            tender.save()

            # Save sections
            for section_data in parsed_data['sections']:
                TenderSection.objects.create(
                    tender=tender,
                    section_number=section_data['number'],
                    title=section_data['title'],
                    content=section_data['content'],
                    level=section_data['level'],
                    parent=None  # Can implement hierarchy later
                )

            # Vectorize sections
            vector_ids = tender_vector_service.vectorize_tender(
                tender.id,
                parsed_data['sections']
            )

            # Extract and save BOQ items
            boq_classifier = BOQClassifier()
            boq_items = parser.extract_boq_items(parsed_data['tables'])

            # Fallback 1: fixed-width text tables (space-separated columns)
            if not boq_items and parsed_data['full_text']:
                boq_items = parser.extract_fixed_width_boq(parsed_data['full_text'])
            # Fallback 2: pipe-delimited text table (e.g. Word-exported PDFs)
            if not boq_items and parsed_data['full_text']:
                boq_items = parser.extract_pipe_table_boq(parsed_data['full_text'])
            # Fallback 3: bullet/numbered scope text
            if not boq_items and parsed_data['full_text']:
                boq_items = parser.extract_scope_from_text(parsed_data['full_text'])

            for item_data in boq_items:
                category = boq_classifier.classify(item_data.get('description', ''))

                # Truncate item_code to database limit (100 chars)
                item_code = item_data.get('item_code')
                if item_code and len(str(item_code)) > 100:
                    item_code = str(item_code)[:100]

                # Truncate unit to database limit (50 chars)
                unit = item_data.get('unit')
                if unit and len(str(unit)) > 50:
                    unit = str(unit)[:50]

                TenderWorkItem.objects.create(
                    tender=tender,
                    item_code=item_code,
                    description=item_data.get('description', ''),
                    category=category,
                    quantity=item_data.get('quantity'),
                    unit=unit,
                    estimated_cost=item_data.get('amount')
                )

            # Run intelligence engines
            self._run_intelligence_analysis(tender, parsed_data['full_text'], metadata)

            # Update status
            tender.status = 'ANALYZED'
            tender.save()

            # Return tender details
            return Response(
                TenderDetailSerializer(tender).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            # Log error
            print(f"Error analyzing tender: {e}")
            print(traceback.format_exc())

            if 'tender' in locals():
                tender.status = 'DRAFT'
                tender.save()

            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _run_intelligence_analysis(self, tender, full_text, base_metadata):
        """Run all intelligence engines on tender"""

        # 1. Extract comprehensive metadata with LLM
        try:
            import ollama
            llm_client = ollama
        except:
            llm_client = None

        extractor = MetadataExtractor(llm_client=llm_client)
        metadata = extractor.extract(full_text, base_metadata)

        # Update tender with extracted metadata
        if 'estimated_value' in metadata and metadata['estimated_value']:
            try:
                tender.estimated_value = Decimal(str(metadata['estimated_value']))
            except (ValueError, TypeError, InvalidOperation):
                pass  # Skip if value is invalid
        if 'bid_security' in metadata and metadata['bid_security']:
            try:
                tender.bid_security = Decimal(str(metadata['bid_security']))
            except (ValueError, TypeError, InvalidOperation):
                pass  # Skip if value is invalid
        if 'emd_amount' in metadata and metadata['emd_amount']:
            # EMD and bid_security are the same thing - populate both fields
            try:
                emd_value = Decimal(str(metadata['emd_amount']))
                tender.emd_amount = emd_value
                tender.bid_security = emd_value
            except (ValueError, TypeError, InvalidOperation):
                pass  # Skip if value is invalid
        if 'organization' in metadata and metadata['organization']:
            tender.organization = metadata['organization']
        if 'submission_deadline' in metadata and metadata['submission_deadline']:
            try:
                from datetime import datetime
                import pytz
                # Clean the date string - remove extra whitespace and common artifacts
                date_str = str(metadata['submission_deadline']).strip()
                date_str = re.sub(r'\s+', ' ', date_str)  # Normalize whitespace
                date_str = date_str.split()[0] if ' ' in date_str else date_str  # Take first part if multiple dates

                tz = pytz.timezone('Asia/Kolkata')
                for fmt in ('%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d.%m.%y', '%d/%m/%y', '%d-%m-%y'):
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        # Handle 2-digit years (assume 20xx if < 50, else 19xx)
                        if dt.year < 100:
                            dt = dt.replace(year=2000 + dt.year if dt.year < 50 else 1900 + dt.year)
                        tender.submission_deadline = tz.localize(dt)
                        print(f"✓ Parsed submission deadline: {date_str} -> {tender.submission_deadline}")
                        break
                    except ValueError:
                        continue
            except Exception as e:
                print(f"✗ Failed to parse submission deadline '{metadata.get('submission_deadline')}': {e}")
                pass
        _DATE_FMTS = ('%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d',
                      '%d.%m.%y', '%d/%m/%y', '%d-%m-%y')
        for field_name, meta_key, model_attr in [
            ('technical_opening', 'technical_opening', 'technical_opening_date'),
            ('financial_opening', 'financial_opening', 'financial_opening_date'),
        ]:
            if metadata.get(meta_key):
                try:
                    from datetime import datetime
                    import pytz
                    # Clean the date string - remove extra whitespace and common artifacts
                    date_str = str(metadata[meta_key]).strip()
                    date_str = re.sub(r'\s+', ' ', date_str)  # Normalize whitespace
                    date_str = date_str.split()[0] if ' ' in date_str else date_str  # Take first part

                    tz = pytz.timezone('Asia/Kolkata')
                    for fmt in _DATE_FMTS:
                        try:
                            dt = datetime.strptime(date_str, fmt)
                            # Handle 2-digit years
                            if dt.year < 100:
                                dt = dt.replace(year=2000 + dt.year if dt.year < 50 else 1900 + dt.year)
                            parsed_dt = tz.localize(dt)
                            # Don't store if it's identical to submission_deadline (parser fallback artifact)
                            if tender.submission_deadline and parsed_dt == tender.submission_deadline:
                                print(f"⚠ Skipping {field_name} — identical to submission_deadline (parser artifact)")
                                break
                            setattr(tender, model_attr, parsed_dt)
                            print(f"✓ Parsed {field_name}: {date_str} -> {getattr(tender, model_attr)}")
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    print(f"✗ Failed to parse {field_name} '{metadata.get(meta_key)}': {e}")
                    pass

        # Update completion period if intelligence extractor found it
        cp = metadata.get('completion_period_days') or metadata.get('completion_period')
        if cp:
            try:
                tender.completion_period_days = int(cp)
            except Exception:
                pass

        tender.save()

        # Save eligibility criteria (min_turnover, min_net_worth, min_projects from extractor)
        TenderEligibility.objects.create(
            tender=tender,
            min_turnover=metadata.get('min_turnover'),
            min_net_worth=metadata.get('min_net_worth'),
            min_projects=metadata.get('min_projects'),
        )

        # 2. Detect risks
        risk_detector = RiskDetector()
        risks = risk_detector.detect_risks(full_text, metadata)

        for risk_data in risks:
            TenderRisk.objects.create(
                tender=tender,
                category=risk_data['category'],
                description=risk_data['description'],
                clause_reference=risk_data.get('clause_reference'),
                severity=risk_data.get('severity', 'MEDIUM'),
                severity_score=risk_data['severity_score'],
                financial_exposure=risk_data.get('financial_exposure')
            )

        # 3. Detect conflicts
        sections = list(tender.sections.values('section_number', 'title', 'content'))
        conflict_detector = ConflictDetector()
        conflicts = conflict_detector.detect_conflicts(sections)

        for conflict_data in conflicts:
            TenderConflict.objects.create(
                tender=tender,
                clause_a=conflict_data['clause_a'],
                clause_a_reference=conflict_data.get('clause_a_reference'),
                clause_b=conflict_data['clause_b'],
                clause_b_reference=conflict_data.get('clause_b_reference'),
                contradiction_score=conflict_data['contradiction_score'],
                explanation=conflict_data['explanation']
            )

        # 4. Generate pre-bid questions
        question_generator = PreBidQuestionGenerator()
        questions = question_generator.generate(
            {'summary': full_text[:1000]},
            risks,
            conflicts
        )

        for question_data in questions:
            PreBidQuestion.objects.create(
                tender=tender,
                category=question_data['category'],
                question=question_data['question'],
                rationale=question_data.get('rationale')
            )

    @action(detail=True, methods=['post'])
    def check_eligibility(self, request, pk=None):
        """
        Check company eligibility against tender requirements

        POST /api/tenders/{id}/check_eligibility/
        """
        tender = self.get_object()

        # Get or create company profile
        try:
            company_profile = request.user.company_profile
        except CompanyProfile.DoesNotExist:
            # Auto-create a basic profile
            company_profile = CompanyProfile.objects.create(
                user=request.user,
                company_name="Default Company",
                annual_turnover=Decimal('10000000'),
                net_worth=Decimal('5000000'),
                similar_projects_completed=5,
                past_win_rate=0.6
            )

        # Validate eligibility
        validator = EligibilityValidator()

        tender_eligibility = {}
        if hasattr(tender, 'eligibility'):
            tender_eligibility = {
                'min_turnover': tender.eligibility.min_turnover,
                'min_net_worth': tender.eligibility.min_net_worth,
                'min_projects': tender.eligibility.min_projects,
            }

        company_data = {
            'annual_turnover': company_profile.annual_turnover,
            'net_worth': company_profile.net_worth,
            'similar_projects_completed': company_profile.similar_projects_completed,
        }

        eligibility_result = validator.validate(tender_eligibility, company_data)

        return Response(eligibility_result)

    @action(detail=True, methods=['post'])
    def generate_proposal(self, request, pk=None):
        """
        Generate proposal for tender

        POST /api/tenders/{id}/generate_proposal/
        """
        tender = self.get_object()

        try:
            company_profile = request.user.company_profile
        except CompanyProfile.DoesNotExist:
            # Auto-create a basic profile
            company_profile = CompanyProfile.objects.create(
                user=request.user,
                company_name="Default Company",
                annual_turnover=Decimal('10000000'),
                net_worth=Decimal('5000000'),
                similar_projects_completed=5,
                past_win_rate=0.6
            )

        # Build rich tender context for proposal generation
        from django.conf import settings
        work_items = list(tender.work_items.values('description', 'category', 'quantity', 'unit', 'estimated_cost')[:20])
        risks = list(tender.risks.values('category', 'severity', 'description')[:10])
        boq_total = sum(float(wi.get('estimated_cost') or 0) for wi in work_items)

        tender_ctx = {
            'title': tender.title,
            'reference_number': tender.reference_number or '',
            'scope_of_work': tender.scope_of_work or "General construction and engineering works",
            'estimated_value': tender.estimated_value,
            'submission_deadline': str(tender.submission_deadline) if tender.submission_deadline else '',
            'completion_period': tender.completion_period_days or '',
            'work_items': work_items,
            'risks': risks,
            'boq_total': boq_total,
            'emd_amount': tender.emd_amount,
        }
        company_ctx = {
            'company_name': company_profile.company_name or 'Our Company',
            'company_strengths': company_profile.company_strengths or "Experienced EPC contractor with proven track record",
            'annual_turnover': company_profile.annual_turnover,
            'similar_projects_completed': company_profile.similar_projects_completed or 5,
        }

        ollama_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        generator = ProposalGenerator(llm_client=ollama_url)
        proposal_data = generator.generate(tender_ctx, company_ctx)

        # Save or update proposal
        proposal, created = TenderProposal.objects.update_or_create(
            tender=tender,
            defaults=proposal_data
        )

        return Response(TenderProposalSerializer(proposal).data)

    @action(detail=True, methods=['post'])
    def optimize_margin(self, request, pk=None):
        """
        Generate margin optimization scenarios

        POST /api/tenders/{id}/optimize_margin/
        Body: { "margin_range": [5, 25], "step": 5 }
        """
        try:
            tender = self.get_object()

            try:
                company_profile = request.user.company_profile
            except CompanyProfile.DoesNotExist:
                # Auto-create a basic profile
                company_profile = CompanyProfile.objects.create(
                    user=request.user,
                    company_name="Default Company",
                    annual_turnover=Decimal('10000000'),
                    net_worth=Decimal('5000000'),
                    similar_projects_completed=5,
                    past_win_rate=0.6
                )

            # Calculate base cost
            cost_modeler = BOQCostModeler()
            work_items = list(tender.work_items.values())

            if work_items:
                cost_breakdown = cost_modeler.calculate_project_cost(work_items)
                total_cost_val = cost_breakdown['total_cost']
                import math
                if total_cost_val is None or (isinstance(total_cost_val, float) and (math.isnan(total_cost_val) or math.isinf(total_cost_val))) or total_cost_val == 0:
                    base_cost = tender.estimated_value if tender.estimated_value else Decimal('10000000')
                    base_cost_f = float(base_cost)
                    cost_breakdown = {
                        'base_cost': base_cost_f,
                        'total_cost': base_cost_f,
                        'material_cost': base_cost_f * 0.5,
                        'labor_cost': base_cost_f * 0.3,
                        'equipment_cost': base_cost_f * 0.2,
                    }
                else:
                    base_cost = Decimal(str(total_cost_val))
            else:
                # Use estimated value as base cost if no BOQ items
                base_cost = tender.estimated_value if tender.estimated_value else Decimal('10000000')
                base_cost_f = float(base_cost)
                cost_breakdown = {
                    'base_cost': base_cost_f,
                    'total_cost': base_cost_f,
                    'material_cost': base_cost_f * 0.5,
                    'labor_cost': base_cost_f * 0.3,
                    'equipment_cost': base_cost_f * 0.2,
                }

            # Calculate risk score
            risks = list(tender.risks.all())
            avg_risk = sum(r.severity_score for r in risks) / len(risks) if risks else 0.3

            # Generate scenarios
            optimizer = MarginOptimizer()
            margin_range = request.data.get('margin_range', [5, 25])
            step = request.data.get('step', 5)

            scenarios = optimizer.generate_scenarios(
                base_cost=float(base_cost),
                tender_risk_score=avg_risk,
                company_competitiveness=company_profile.past_win_rate,
                margin_range=tuple(margin_range),
                step=step
            )

            # Find optimal
            optimal = optimizer.select_optimal(scenarios)

            # First, set all existing scenarios for this tender to not recommended
            BidScenario.objects.filter(tender=tender).update(is_recommended=False)

            # Save scenarios
            for scenario_data in scenarios:
                BidScenario.objects.update_or_create(
                    tender=tender,
                    margin_percentage=scenario_data['margin_percentage'],
                    defaults={
                        'total_cost': scenario_data['total_cost'],
                        'bid_price': scenario_data['bid_price'],
                        'win_probability': scenario_data['win_probability'],
                        'expected_profit': scenario_data['expected_profit'],
                        'is_recommended': scenario_data == optimal
                    }
                )

            return Response({
                'cost_breakdown': cost_breakdown,
                'scenarios': scenarios,
                'optimal': optimal
            })

        except Exception as e:
            print(f"Error in optimize_margin: {e}")
            print(traceback.format_exc())
            return Response(
                {'error': str(e), 'detail': 'Margin optimization failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def simulate_win_probability(self, request, pk=None):
        """
        Simulate win probability

        POST /api/tenders/{id}/simulate_win_probability/
        """
        tender = self.get_object()

        try:
            company_profile = request.user.company_profile
        except CompanyProfile.DoesNotExist:
            return Response(
                {'error': 'Please create company profile first'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Run simulation
        simulator = WinSimulator()
        risks = list(tender.risks.values())

        # Prepare eligibility data
        eligibility_data = {}
        try:
            if hasattr(tender, 'eligibility') and tender.eligibility:
                eligibility_data = {
                    'min_turnover': float(tender.eligibility.min_turnover) if tender.eligibility.min_turnover else None,
                    'min_net_worth': float(tender.eligibility.min_net_worth) if tender.eligibility.min_net_worth else None,
                    'min_projects': int(tender.eligibility.min_projects) if tender.eligibility.min_projects else None,
                }
        except Exception as e:
            print(f"Error preparing eligibility data: {e}")

        simulation_result = simulator.simulate(
            {'eligibility': eligibility_data},
            {
                'annual_turnover': float(company_profile.annual_turnover) if company_profile.annual_turnover else 0,
                'similar_projects_completed': int(company_profile.similar_projects_completed) if company_profile.similar_projects_completed else 0,
                'past_win_rate': float(company_profile.past_win_rate) if company_profile.past_win_rate else 0.5
            },
            risks
        )

        return Response(simulation_result)

    @action(detail=True, methods=['post'])
    def generate_negotiations(self, request, pk=None):
        """
        Generate negotiation counter-proposals

        POST /api/tenders/{id}/generate_negotiations/
        """
        tender = self.get_object()
        risks = tender.risks.all()

        automation = NegotiationAutomation()

        # Prioritize risks for negotiation
        prioritized_risks = automation.prioritize_negotiations(
            list(risks.values())
        )

        # Generate counter-proposals for top risks
        for risk_data in prioritized_risks[:5]:  # Top 5
            counter = automation.generate_counter_proposal(risk_data)

            TenderNegotiation.objects.create(
                tender=tender,
                issue_type=counter['issue_type'],
                original_clause=counter['original_clause'],
                counter_proposal=counter['counter_proposal'],
                rationale=counter.get('rationale'),
                acceptance_probability=counter.get('acceptance_probability')
            )

        negotiations = tender.negotiations.all()
        return Response(TenderNegotiationSerializer(negotiations, many=True).data)

    @action(detail=True, methods=['get'])
    def export_report(self, request, pk=None):
        """
        Export a comprehensive tender report as plain-text (downloadable).

        GET /api/tenders/{id}/export_report/
        """
        tender = self.get_object()
        lines = []

        # ── Title block ──────────────────────────────────────────────────────
        lines.append('=' * 80)
        lines.append(f'  TENDER INTELLIGENCE REPORT')
        lines.append(f'  {tender.title}')
        if tender.reference_number:
            lines.append(f'  Ref: {tender.reference_number}')
        lines.append('=' * 80)
        lines.append('')

        # ── Commercials ───────────────────────────────────────────────────────
        lines.append('1. COMMERCIAL SUMMARY')
        lines.append('-' * 40)
        if tender.estimated_value:
            cr = float(tender.estimated_value) / 10_000_000
            lines.append(f'  Estimated Value    : INR {cr:.2f} Crore')
        if tender.emd_amount:
            lines.append(f'  EMD Amount         : INR {float(tender.emd_amount):,.0f}')
        if tender.bid_security:
            lines.append(f'  Bid Security       : INR {float(tender.bid_security):,.0f}')
        if tender.submission_deadline:
            lines.append(f'  Submission Deadline: {tender.submission_deadline.strftime("%d %b %Y")}')
        if tender.technical_opening_date:
            lines.append(f'  Technical Opening  : {tender.technical_opening_date.strftime("%d %b %Y")}')
        if tender.financial_opening_date:
            lines.append(f'  Financial Opening  : {tender.financial_opening_date.strftime("%d %b %Y")}')
        if tender.completion_period_days:
            lines.append(f'  Completion Period  : {tender.completion_period_days} days')
        if tender.organization:
            lines.append(f'  Organisation       : {tender.organization}')
        lines.append('')

        # ── Eligibility ───────────────────────────────────────────────────────
        if hasattr(tender, 'eligibility') and tender.eligibility:
            el = tender.eligibility
            lines.append('2. ELIGIBILITY CRITERIA')
            lines.append('-' * 40)
            if el.min_turnover:
                lines.append(f'  Min Annual Turnover : INR {float(el.min_turnover)/10_000_000:.2f} Cr')
            if el.min_net_worth:
                lines.append(f'  Min Net Worth       : INR {float(el.min_net_worth)/10_000_000:.2f} Cr')
            if el.min_projects:
                lines.append(f'  Min Similar Projects: {el.min_projects}')
            if el.other_requirements:
                lines.append(f'  Other Requirements  : {el.other_requirements[:200]}')
            lines.append('')

        # ── Risks ─────────────────────────────────────────────────────────────
        risks = list(tender.risks.all().order_by('-severity_score'))
        if risks:
            lines.append('3. SALIENT RISKS')
            lines.append('-' * 40)
            for i, r in enumerate(risks, 1):
                lines.append(f'  {i}. [{r.severity}] {r.category}')
                lines.append(f'     {r.description[:200]}')
                if r.mitigation_suggestion:
                    lines.append(f'     Mitigation: {r.mitigation_suggestion[:150]}')
            lines.append('')

        # ── Conflicts ─────────────────────────────────────────────────────────
        conflicts = list(tender.conflicts.all())
        if conflicts:
            lines.append('4. CLAUSE CONFLICTS')
            lines.append('-' * 40)
            for i, c in enumerate(conflicts, 1):
                lines.append(f'  {i}. Contradiction ({c.contradiction_score:.0%})')
                lines.append(f'     Clause A: {c.clause_a[:120]}')
                lines.append(f'     Clause B: {c.clause_b[:120]}')
                lines.append(f'     Reason  : {c.explanation[:200]}')
            lines.append('')

        # ── BOQ ───────────────────────────────────────────────────────────────
        work_items = list(tender.work_items.all())
        if work_items:
            lines.append('5. BILL OF QUANTITIES (BOQ)')
            lines.append('-' * 40)
            for cat in ['CIVIL', 'MECHANICAL', 'MEP', 'OTHER']:
                cat_items = [w for w in work_items if w.category == cat]
                if cat_items:
                    lines.append(f'  [{cat}]')
                    for w in cat_items:
                        cost_str = f' | Est. INR {float(w.estimated_cost):,.0f}' if w.estimated_cost else ''
                        qty_str = f' | Qty: {w.quantity} {w.unit or ""}' if w.quantity else ''
                        lines.append(f'    - {w.description[:80]}{qty_str}{cost_str}')
            lines.append('')

        # ── Bid Scenarios ─────────────────────────────────────────────────────
        scenarios = list(tender.bid_scenarios.all().order_by('margin_percentage'))
        if scenarios:
            lines.append('6. MARGIN OPTIMISATION SCENARIOS')
            lines.append('-' * 40)
            lines.append(f'  {"Margin":>8} | {"Bid Price (Cr)":>16} | {"Win Prob":>10} | {"Exp Profit (Cr)":>16} | Recommended')
            lines.append(f'  {"-"*8}-+-{"-"*16}-+-{"-"*10}-+-{"-"*16}-+-{"-"*12}')
            for s in scenarios:
                rec = ' *** OPTIMAL ***' if s.is_recommended else ''
                bid_cr = float(s.bid_price) / 10_000_000 if s.bid_price else 0
                ep_cr = float(s.expected_profit) / 10_000_000 if s.expected_profit else 0
                lines.append(f'  {s.margin_percentage:>7.1f}% | {bid_cr:>15.2f} | {s.win_probability:>9.1f}% | {ep_cr:>15.2f} |{rec}')
            lines.append('')

        # ── Proposal ──────────────────────────────────────────────────────────
        if hasattr(tender, 'proposal') and tender.proposal:
            p = tender.proposal
            lines.append('7. PROPOSAL SECTIONS')
            lines.append('-' * 40)
            for attr, label in [
                ('technical_compliance', 'Technical Compliance'),
                ('construction_methodology', 'Construction Methodology'),
                ('resource_mobilization', 'Resource Mobilisation'),
                ('risk_mitigation', 'Risk Mitigation'),
                ('commercial_positioning', 'Commercial Positioning'),
                ('schedule_assurance', 'Schedule Assurance'),
                ('value_engineering', 'Value Engineering'),
            ]:
                val = getattr(p, attr, None)
                if val:
                    lines.append(f'  {label}:')
                    lines.append(f'    {val[:300]}')
            lines.append('')

        # ── Negotiations ──────────────────────────────────────────────────────
        negotiations = list(tender.negotiations.all())
        if negotiations:
            lines.append('8. NEGOTIATION COUNTER-PROPOSALS')
            lines.append('-' * 40)
            for n in negotiations:
                lines.append(f'  Issue : {n.issue_type}')
                lines.append(f'  Status: {n.negotiation_status}')
                lines.append(f'  Counter Proposal:')
                lines.append(f'    {n.counter_proposal[:300]}')
                if n.acceptance_probability:
                    lines.append(f'  Acceptance Probability: {n.acceptance_probability:.0%}')
                lines.append('')

        # ── Pre-bid Questions ─────────────────────────────────────────────────
        questions = list(tender.prebid_questions.all())
        if questions:
            lines.append('9. PRE-BID QUESTIONNAIRE')
            lines.append('-' * 40)
            for i, q in enumerate(questions, 1):
                lines.append(f'  Q{i}. [{q.category}] {q.question}')
                if q.rationale:
                    lines.append(f'       Rationale: {q.rationale}')
            lines.append('')

        lines.append('=' * 80)
        lines.append('  Report generated by PrimeContractAI Tender Intelligence Engine')
        lines.append('=' * 80)

        report_text = '\n'.join(lines)

        from django.http import HttpResponse
        filename = f'Tender_Report_{tender.reference_number or tender.id}.txt'
        response_http = HttpResponse(report_text, content_type='text/plain; charset=utf-8')
        response_http['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response_http

    @action(detail=True, methods=['post'])
    def upload_amendment(self, request, pk=None):
        """
        Upload a revised/amended version of the tender PDF.

        POST /api/tenders/{id}/upload_amendment/
        Body: { "pdf_file": <file>, "amendment_note": "..." }
        """
        tender = self.get_object()

        pdf_file = request.FILES.get('pdf_file')
        if not pdf_file:
            return Response({'error': 'No PDF file provided'}, status=status.HTTP_400_BAD_REQUEST)

        amendment_note = request.data.get('amendment_note', 'Amendment uploaded')

        # Save current snapshot before overwriting
        from .models import TenderAmendment
        TenderAmendment.objects.create(
            tender=tender,
            version_number=tender.amendments.count() + 1,
            amendment_note=amendment_note,
            snapshot={
                'estimated_value': str(tender.estimated_value),
                'submission_deadline': str(tender.submission_deadline),
                'completion_period_days': tender.completion_period_days,
                'risks_count': tender.risks.count(),
                'conflicts_count': tender.conflicts.count(),
                'work_items_count': tender.work_items.count(),
            },
            uploaded_by=request.user,
        )

        # Replace pdf_file and re-analyze
        tender.pdf_file = pdf_file
        tender.status = 'ANALYZING'
        tender.save()

        pdf_path = tender.pdf_file.path

        # Delete old analysis data
        tender.sections.all().delete()
        tender.work_items.all().delete()
        tender.risks.all().delete()
        tender.conflicts.all().delete()
        tender.prebid_questions.all().delete()
        if hasattr(tender, 'eligibility'):
            try:
                tender.eligibility.delete()
            except Exception:
                pass

        try:
            parser = TenderParser()
            parsed_data = parser.parse_pdf(pdf_path)

            metadata = parsed_data['metadata']
            if metadata.get('estimated_value'):
                tender.estimated_value = Decimal(str(metadata['estimated_value']))
            if metadata.get('completion_period_days') or metadata.get('completion_period'):
                cp = metadata.get('completion_period_days') or metadata.get('completion_period')
                tender.completion_period_days = int(cp)

            tender.save()

            for section_data in parsed_data['sections']:
                TenderSection.objects.create(
                    tender=tender,
                    section_number=section_data['number'],
                    title=section_data['title'],
                    content=section_data['content'],
                    level=section_data['level'],
                )

            boq_classifier = BOQClassifier()
            boq_items = parser.extract_boq_items(parsed_data['tables'])
            if not boq_items and parsed_data['full_text']:
                boq_items = parser.extract_scope_from_text(parsed_data['full_text'])
            for item_data in boq_items:
                category = boq_classifier.classify(item_data.get('description', ''))
                TenderWorkItem.objects.create(
                    tender=tender,
                    item_code=item_data.get('item_code'),
                    description=item_data.get('description', ''),
                    category=category,
                    quantity=item_data.get('quantity'),
                    unit=item_data.get('unit'),
                    estimated_cost=item_data.get('amount'),
                )

            self._run_intelligence_analysis(tender, parsed_data['full_text'], metadata)
            tender.status = 'ANALYZED'
            tender.save()

        except Exception as e:
            tender.status = 'DRAFT'
            tender.save()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'message': 'Amendment processed successfully',
            'version': tender.amendments.count(),
            'tender': TenderDetailSerializer(tender).data,
        })

    @action(detail=True, methods=['post'])
    def reanalyze(self, request, pk=None):
        """
        Re-parse the existing PDF and re-run all intelligence engines.
        Useful when the tender was uploaded before extraction improvements.

        POST /api/tenders/{id}/reanalyze/
        """
        tender = self.get_object()

        if not tender.pdf_file:
            return Response({'error': 'No PDF file attached to this tender'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pdf_path = tender.pdf_file.path

            # Clear old derived data
            tender.sections.all().delete()
            tender.work_items.all().delete()
            tender.risks.all().delete()
            tender.conflicts.all().delete()
            tender.prebid_questions.all().delete()
            if hasattr(tender, 'eligibility'):
                try:
                    tender.eligibility.delete()
                except Exception:
                    pass

            tender.status = 'ANALYZING'
            tender.save()

            parser = TenderParser()
            parsed_data = parser.parse_pdf(pdf_path)

            metadata = parsed_data['metadata']
            if metadata.get('estimated_value'):
                tender.estimated_value = Decimal(str(metadata['estimated_value']))
            tender.save()

            for section_data in parsed_data['sections']:
                TenderSection.objects.create(
                    tender=tender,
                    section_number=section_data['number'],
                    title=section_data['title'],
                    content=section_data['content'],
                    level=section_data['level'],
                )

            boq_classifier = BOQClassifier()
            boq_items = parser.extract_boq_items(parsed_data['tables'])

            # Fallback 1: fixed-width text tables (space-separated columns)
            if not boq_items and parsed_data['full_text']:
                boq_items = parser.extract_fixed_width_boq(parsed_data['full_text'])
            # Fallback 2: pipe-delimited text table (e.g. Word-exported PDFs)
            if not boq_items and parsed_data['full_text']:
                boq_items = parser.extract_pipe_table_boq(parsed_data['full_text'])
            # Fallback 3: bullet/numbered scope text
            if not boq_items and parsed_data['full_text']:
                boq_items = parser.extract_scope_from_text(parsed_data['full_text'])

            for item_data in boq_items:
                category = boq_classifier.classify(item_data.get('description', ''))

                # Truncate item_code to database limit (500 chars)
                item_code = item_data.get('item_code')
                if item_code and len(str(item_code)) > 500:
                    item_code = str(item_code)[:500]

                # Truncate unit to database limit (50 chars)
                unit = item_data.get('unit')
                if unit and len(str(unit)) > 50:
                    unit = str(unit)[:50]

                TenderWorkItem.objects.create(
                    tender=tender,
                    item_code=item_code,
                    description=item_data.get('description', ''),
                    category=category,
                    quantity=item_data.get('quantity'),
                    unit=unit,
                    estimated_cost=item_data.get('amount') or item_data.get('rate'),
                )

            self._run_intelligence_analysis(tender, parsed_data['full_text'], metadata)
            tender.status = 'ANALYZED'
            tender.save()

            return Response(TenderDetailSerializer(tender).data)

        except Exception as e:
            print(traceback.format_exc())
            tender.status = 'DRAFT'
            tender.save()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def amendments(self, request, pk=None):
        """
        List all amendments/versions for a tender.

        GET /api/tenders/{id}/amendments/
        """
        tender = self.get_object()
        from .models import TenderAmendment
        from .serializers import TenderAmendmentSerializer
        amends = tender.amendments.all().order_by('-created_at')
        return Response(TenderAmendmentSerializer(amends, many=True).data)


class CompanyProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for Company Profile"""

    permission_classes = [IsAuthenticated]
    serializer_class = CompanyProfileSerializer

    def get_queryset(self):
        return CompanyProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
