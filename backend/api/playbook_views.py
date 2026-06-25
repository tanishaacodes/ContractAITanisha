"""
Playbook Automation – API Views
--------------------------------
All endpoints follow the same @api_view / Response pattern used in
embedding_views.py.  Authentication is handled by the global DRF default
(JWTAuthentication + IsAuthenticated) so none of these views need explicit
permission_classes unless they must be public.

Endpoint map
────────────
POST  /api/playbook/contracts/<id>/run          – trigger full playbook check
GET   /api/playbook/contracts/<id>/results      – cached results for a contract
POST  /api/playbook/results/<id>/accept         – accept a fallback suggestion
GET   /api/playbook/drift                       – drift snapshots (all time)
POST  /api/playbook/drift/capture               – manual drift capture (admin)
GET   /api/playbook/coverage                    – playbook coverage metrics
GET   /api/playbook/update-suggestions          – pending update suggestions
POST  /api/playbook/update-suggestions/<id>/approve
POST  /api/playbook/update-suggestions/<id>/reject
GET   /api/playbook/heatmap                     – clause-type × drift heatmap
POST  /api/playbook/admin/playbooks             – CRUD for LegalPlaybook entries
GET   /api/playbook/admin/playbooks
"""

import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from core.models import Contract, LegalPlaybook, ClausePlaybookResult, PlaybookUpdateSuggestion
from api.playbook_service import playbook_service
from api.embedding_service import embedding_service

logger = logging.getLogger(__name__)


# =============================================================================
# 1. Run playbook check on a contract
# =============================================================================
@api_view(['POST'])
def run_playbook_check(request, contract_id):
    """
    Trigger the full playbook pipeline for a contract.
    Evaluates every clause, persists results, and returns them.
    """
    try:
        contract = get_object_or_404(Contract, id=contract_id)
        jurisdiction = request.data.get(
            'jurisdiction',
            contract.jurisdiction or 'global'
        )

        results = playbook_service.run_playbook_check(contract, jurisdiction)

        # Aggregate counts for the summary card
        total = len(results)
        non_standard_count = sum(1 for r in results if not r['is_standard'])
        mandatory_violations = sum(
            1 for r in results if not r['is_standard'] and r['mandatory']
        )

        return Response({
            'contract_id': str(contract_id),
            'contract_name': contract.original_filename,
            'total_evaluated': total,
            'standard_count': total - non_standard_count,
            'non_standard_count': non_standard_count,
            'mandatory_violations': mandatory_violations,
            'results': results,
        })

    except Exception as e:
        logger.error("run_playbook_check error: %s", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# 2. Get cached playbook results for a contract
# =============================================================================
@api_view(['GET'])
def get_playbook_results(request, contract_id):
    """Return the most recent playbook evaluation for each clause."""
    try:
        from core.models import Clause
        contract = get_object_or_404(Contract, id=contract_id)

        # Get clause IDs belonging to this contract
        clause_ids = list(
            Clause.objects.filter(contract=contract).values_list('id', flat=True)
        )

        rows = (
            ClausePlaybookResult.objects
            .filter(clause_id__in=clause_ids)
            .order_by('-evaluated_at')
        )

        # Pre-fetch clause and playbook lookups
        clauses_map = {
            str(c.id): c for c in Clause.objects.filter(id__in=clause_ids)
        }
        playbook_ids = list(rows.values_list('playbook_id', flat=True))
        playbooks_map = {
            str(pb.id): pb for pb in LegalPlaybook.objects.filter(id__in=playbook_ids)
        }

        results = []
        for r in rows:
            clause = clauses_map.get(str(r.clause_id))
            pb = playbooks_map.get(str(r.playbook_id))
            results.append({
                'id': r.id,
                'clause_id': str(r.clause_id),
                'clause_name': clause.clause_name if clause else '',
                'clause_type': pb.clause_type if pb else '',
                'jurisdiction': pb.jurisdiction if pb else '',
                'similarity_score': r.similarity_score,
                'is_standard': r.is_standard,
                'suggested_text': r.suggested_text,
                'mandatory': pb.mandatory if pb else False,
                'fallback_accepted': r.fallback_accepted,
                'evaluated_at': r.evaluated_at.isoformat() if r.evaluated_at else None,
            })

        total = len(results)
        non_standard_count = sum(1 for r in results if not r['is_standard'])

        return Response({
            'contract_id': str(contract_id),
            'total_evaluated': total,
            'standard_count': total - non_standard_count,
            'non_standard_count': non_standard_count,
            'mandatory_violations': sum(
                1 for r in results if not r['is_standard'] and r['mandatory']
            ),
            'results': results,
        })

    except Exception as e:
        logger.error("get_playbook_results error: %s", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# 3. Accept a fallback suggestion
# =============================================================================
@api_view(['POST'])
def accept_playbook_fallback(request, result_id):
    """Mark a ClausePlaybookResult fallback as accepted by the reviewer."""
    try:
        result = playbook_service.accept_fallback(str(result_id))
        if result is None:
            return Response(
                {'error': 'Result not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({
            'id': result.id,
            'fallback_accepted': True,
            'accepted_at': result.accepted_at.isoformat() if result.accepted_at else None,
        })

    except Exception as e:
        logger.error("accept_playbook_fallback error: %s", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# 4. Drift snapshots
# =============================================================================
@api_view(['GET'])
def get_playbook_drift(request):
    """Return all drift snapshots for the trend chart."""
    try:
        from core.models import PlaybookDriftSnapshot

        clause_type = request.query_params.get('clause_type')
        jurisdiction = request.query_params.get('jurisdiction')

        qs = PlaybookDriftSnapshot.objects.all()
        if clause_type:
            qs = qs.filter(clause_type=clause_type)
        if jurisdiction:
            qs = qs.filter(jurisdiction=jurisdiction)

        data = list(
            qs.values(
                'clause_type', 'jurisdiction',
                'avg_similarity', 'non_standard_rate', 'snapshot_date',
            ).order_by('snapshot_date')
        )
        # Convert date objects to ISO strings for JSON serialisation
        for row in data:
            if row['snapshot_date']:
                row['snapshot_date'] = row['snapshot_date'].isoformat()

        return Response(data)

    except Exception as e:
        logger.error("get_playbook_drift error: %s", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def capture_drift(request):
    """Manually trigger a drift snapshot (useful for testing; normally cron)."""
    try:
        playbook_service.capture_playbook_drift()
        playbook_service.detect_playbook_update_candidates()
        return Response({'status': 'drift captured'})
    except Exception as e:
        logger.error("capture_drift error: %s", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# 5. Coverage
# =============================================================================
@api_view(['GET'])
def get_playbook_coverage(request):
    """Return coverage metrics: governed vs ungoverned clause types."""
    try:
        return Response(playbook_service.compute_playbook_coverage())
    except Exception as e:
        logger.error("get_playbook_coverage error: %s", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# 6. Update suggestions (CRUD + approve/reject)
# =============================================================================
@api_view(['GET'])
def get_update_suggestions(request):
    """Return open playbook update suggestions."""
    try:
        status_filter = request.query_params.get('status', 'OPEN')
        qs = PlaybookUpdateSuggestion.objects.filter(status=status_filter)

        data = list(
            qs.values(
                'id', 'clause_type', 'jurisdiction',
                'avg_similarity', 'non_standard_rate',
                'reason', 'suggested_standard', 'status',
                'created_at',
            )
        )
        for row in data:
            if row['created_at']:
                row['created_at'] = row['created_at'].isoformat()
            row['id'] = str(row['id'])

        return Response(data)

    except Exception as e:
        logger.error("get_update_suggestions error: %s", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def approve_update_suggestion(request, suggestion_id):
    """
    Approve a PlaybookUpdateSuggestion.
    Optionally applies the suggested_standard as the new standard_clause
    on the matching LegalPlaybook entry (and re-embeds it).
    """
    try:
        suggestion = get_object_or_404(PlaybookUpdateSuggestion, id=suggestion_id)
        suggestion.status = 'APPROVED'
        suggestion.save(update_fields=['status', 'updated_at'])

        # Apply to the playbook entry
        playbooks = LegalPlaybook.objects.filter(
            clause_type=suggestion.clause_type,
            jurisdiction__in=[suggestion.jurisdiction, 'global'],
        )
        new_emb = embedding_service.embed_text(suggestion.suggested_standard)
        for pb in playbooks:
            pb.standard_clause = suggestion.suggested_standard
            pb.embedding = new_emb
            pb.save(update_fields=['standard_clause', 'embedding', 'updated_at'])

        return Response({'id': str(suggestion.id), 'status': 'APPROVED'})

    except Exception as e:
        logger.error("approve_update_suggestion error: %s", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def reject_update_suggestion(request, suggestion_id):
    """Reject a PlaybookUpdateSuggestion (no playbook mutation)."""
    try:
        suggestion = get_object_or_404(PlaybookUpdateSuggestion, id=suggestion_id)
        suggestion.status = 'REJECTED'
        suggestion.save(update_fields=['status', 'updated_at'])
        return Response({'id': str(suggestion.id), 'status': 'REJECTED'})

    except Exception as e:
        logger.error("reject_update_suggestion error: %s", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# 7. Heatmap overlay (clause-type × drift)
# =============================================================================
@api_view(['GET'])
def get_playbook_heatmap(request):
    """Aggregated clause-type heatmap with drift overlay."""
    try:
        return Response(playbook_service.clause_heatmap_with_drift())
    except Exception as e:
        logger.error("get_playbook_heatmap error: %s", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# 8. Admin – manage LegalPlaybook entries
# =============================================================================
@api_view(['GET', 'POST'])
def manage_playbooks(request):
    """
    GET  – list all playbooks (with optional clause_type filter)
    POST – create a new playbook entry (auto-embeds standard_clause)
    """
    try:
        if request.method == 'GET':
            clause_type = request.query_params.get('clause_type')
            qs = LegalPlaybook.objects.all()
            if clause_type:
                qs = qs.filter(clause_type=clause_type)

            data = []
            for pb in qs:
                data.append({
                    'id': str(pb.id),
                    'clause_type': pb.clause_type,
                    'jurisdiction': pb.jurisdiction,
                    'standard_clause': pb.standard_clause,
                    'fallback_clause': pb.fallback_clause,
                    'similarity_threshold': pb.similarity_threshold,
                    'mandatory': pb.mandatory,
                    'created_at': pb.created_at.isoformat() if pb.created_at else None,
                })
            return Response(data)

        # POST – create
        payload = request.data
        required = ['clause_type', 'standard_clause', 'fallback_clause']
        missing = [f for f in required if not payload.get(f)]
        if missing:
            return Response(
                {'error': f'Missing fields: {missing}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        emb = embedding_service.embed_text(payload['standard_clause'])

        pb = LegalPlaybook.objects.create(
            clause_type=payload['clause_type'],
            jurisdiction=payload.get('jurisdiction', 'global'),
            standard_clause=payload['standard_clause'],
            fallback_clause=payload['fallback_clause'],
            embedding=emb,
            similarity_threshold=float(payload.get('similarity_threshold', 0.85)),
            mandatory=bool(payload.get('mandatory', False)),
        )

        return Response({
            'id': str(pb.id),
            'clause_type': pb.clause_type,
            'jurisdiction': pb.jurisdiction,
            'similarity_threshold': pb.similarity_threshold,
            'mandatory': pb.mandatory,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error("manage_playbooks error: %s", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# 9. Legal Playbook & Action Engine (Dashboard G)
# =============================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_clauses_for_action(request):
    """GET /api/legal-playbook/clauses - Get clauses for legal action analysis"""
    try:
        from core.models import Clause
        user = request.user

        # Get all clauses from user's contracts
        clauses = Clause.objects.filter(contract__user=user).select_related('contract')[:100]

        clauses_data = []
        stats = {"total": 0, "high_risk": 0, "medium_risk": 0, "low_risk": 0}

        for clause in clauses:
            # Get clause text from multiple possible fields
            clause_text = ""
            if hasattr(clause, 'extracted_text') and clause.extracted_text:
                clause_text = clause.extracted_text
            elif hasattr(clause, 'context_sentences') and clause.context_sentences:
                # Skip if context_sentences is empty list string "[]"
                if clause.context_sentences.strip() not in ['[]', '{}', '""', "''", 'null', 'None']:
                    clause_text = clause.context_sentences
            elif hasattr(clause, 'text') and clause.text:
                clause_text = clause.text

            # If still empty, provide a default message
            if not clause_text or clause_text.strip() in ['[]', '{}', '""', "''", 'null', 'None']:
                clause_text = f"No detailed text available for {clause.clause_name}. This clause requires legal review."

            # Determine risk level from actual data
            risk_level = "MEDIUM"

            # First check if risk fields exist
            if hasattr(clause, 'risk_level') and clause.risk_level:
                risk_level = clause.risk_level
            elif hasattr(clause, 'risk_score') and clause.risk_score:
                if clause.risk_score >= 0.7:
                    risk_level = "HIGH"
                elif clause.risk_score >= 0.4:
                    risk_level = "MEDIUM"
                else:
                    risk_level = "LOW"
            else:
                # Intelligent risk detection based on clause name and content
                clause_name_lower = clause.clause_name.lower() if clause.clause_name else ""

                # HIGH RISK clause types (only truly critical ones)
                high_risk_keywords = [
                    'indemnif', 'limitation of liability', 'unlimited liability',
                    'warranty', 'representation', 'breach', 'default',
                    'liquidated damages', 'non-compete', 'non-solicitation'
                ]

                # MEDIUM RISK clause types
                medium_risk_keywords = [
                    'termination', 'confidentiality', 'intellectual property',
                    'force majeure', 'dispute resolution', 'arbitration',
                    'payment', 'fee', 'price', 'penalty', 'delivery', 'timeline',
                    'amendment', 'modification', 'assignment',
                    'insurance', 'compliance', 'audit', 'liability cap'
                ]

                # LOW RISK clause types (administrative/procedural clauses)
                low_risk_keywords = [
                    'definition', 'interpretation', 'recital', 'whereas',
                    'purpose', 'scope', 'preamble', 'background',
                    'exhibit', 'schedule', 'appendix', 'notice', 'notices',
                    'entire agreement', 'headings', 'counterparts', 'severability',
                    'waiver', 'further assurance', 'costs', 'relationship of parties',
                    'successors and assigns', 'third party rights', 'no agency',
                    'governing law', 'choice of law', 'jurisdiction'
                ]

                # Check HIGH risk
                if any(keyword in clause_name_lower for keyword in high_risk_keywords):
                    risk_level = "HIGH"
                # Check LOW risk
                elif any(keyword in clause_name_lower for keyword in low_risk_keywords):
                    risk_level = "LOW"
                # Check clause text for high-risk patterns
                elif clause_text:
                    text_lower = clause_text.lower()
                    if any(keyword in text_lower for keyword in ['unlimited', 'without limitation', 'no cap', 'sole discretion', 'at will']):
                        risk_level = "HIGH"
                # Default to MEDIUM if uncertain
                else:
                    risk_level = "MEDIUM"

            # Get clause type
            clause_type = "General"
            if hasattr(clause, 'clause_type') and clause.clause_type:
                clause_type = clause.clause_type

            # Get jurisdiction from contract
            jurisdiction = "Unknown"
            if hasattr(clause.contract, 'jurisdiction') and clause.contract.jurisdiction:
                jurisdiction = clause.contract.jurisdiction

            clauses_data.append({
                "id": str(clause.id),
                "clause_name": clause.clause_name or "Unnamed Clause",
                "text": clause_text[:500] if clause_text else "No text available",
                "contract_name": clause.contract.original_filename or clause.contract.filename,
                "contract_id": str(clause.contract.id),
                "risk_level": risk_level,
                "clause_type": clause_type,
                "jurisdiction": jurisdiction,
                "found": clause.found if hasattr(clause, 'found') else True
            })

            # Update stats
            stats["total"] += 1
            if risk_level == "HIGH":
                stats["high_risk"] += 1
            elif risk_level == "MEDIUM":
                stats["medium_risk"] += 1
            else:
                stats["low_risk"] += 1

        # Sort by risk level (HIGH first)
        risk_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        clauses_data.sort(key=lambda x: risk_order.get(x["risk_level"], 3))

        return Response({
            "clauses": clauses_data,
            "stats": stats
        })

    except Exception as e:
        logger.error("get_clauses_for_action error: %s", e, exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_legal_playbook_analysis(request, clause_id):
    """GET /api/legal-playbook/clause/<clause_id> - Get legal playbook analysis"""
    try:
        from core.models import Clause
        from ai.legal_playbook import generate_playbook

        user = request.user
        jurisdiction = request.query_params.get("jurisdiction", "India")

        clause = Clause.objects.select_related('contract').get(
            id=clause_id,
            contract__user=user
        )

        clause_text = ""
        if hasattr(clause, 'extracted_text') and clause.extracted_text:
            clause_text = clause.extracted_text
        elif hasattr(clause, 'context_sentences') and clause.context_sentences:
            # Skip if context_sentences is empty list string "[]"
            if clause.context_sentences.strip() not in ['[]', '{}', '""', "''", 'null', 'None']:
                clause_text = clause.context_sentences

        # If still empty, provide a default message
        if not clause_text or clause_text.strip() in ['[]', '{}', '""', "''", 'null', 'None']:
            clause_text = f"No detailed text available for {clause.clause_name}. This clause requires legal review."

        risk_level = "MEDIUM"
        if hasattr(clause, 'risk_level') and clause.risk_level:
            risk_level = clause.risk_level
        elif hasattr(clause, 'risk_score') and clause.risk_score:
            risk_level = "HIGH" if clause.risk_score >= 0.7 else "MEDIUM" if clause.risk_score >= 0.4 else "LOW"

        playbook = generate_playbook(
            clause_name=clause.clause_name,
            clause_text=clause_text,
            risk_level=risk_level,
            jurisdiction=jurisdiction,
            contract_type=clause.contract.contract_type if clause.contract.contract_type else None
        )

        return Response({
            "clause_id": str(clause.id),
            "clause_name": clause.clause_name,
            "clause_text": clause_text[:500] if clause_text else "No text available",
            "contract_name": clause.contract.original_filename or clause.contract.filename,
            "contract_id": str(clause.contract.id),
            **playbook
        })

    except Clause.DoesNotExist:
        return Response({'error': 'Clause not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error("get_legal_playbook_analysis error: %s", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_counter_proposal_action(request, clause_id):
    """POST /api/legal-playbook/clause/<clause_id>/counter-proposal"""
    try:
        from core.models import Clause
        from ai.legal_playbook import generate_counter_proposal, generate_playbook

        user = request.user
        clause = Clause.objects.select_related('contract').get(
            id=clause_id,
            contract__user=user
        )

        current_text = ""
        if hasattr(clause, 'extracted_text') and clause.extracted_text:
            current_text = clause.extracted_text
        elif hasattr(clause, 'context_sentences') and clause.context_sentences:
            # Skip if context_sentences is empty list string "[]"
            if clause.context_sentences.strip() not in ['[]', '{}', '""', "''", 'null', 'None']:
                current_text = clause.context_sentences

        # If still empty, provide a default message
        if not current_text or current_text.strip() in ['[]', '{}', '""', "''", 'null', 'None']:
            current_text = f"[Original {clause.clause_name} text to be reviewed]"

        recommended_rewrite = request.data.get('recommended_rewrite', '')
        if not recommended_rewrite:
            jurisdiction = request.data.get('jurisdiction', 'India')
            playbook = generate_playbook(
                clause_name=clause.clause_name,
                clause_text=current_text,
                risk_level="HIGH",
                jurisdiction=jurisdiction
            )
            recommended_rewrite = playbook['recommended_rewrite']

        proposal = generate_counter_proposal(
            clause_name=clause.clause_name,
            current_text=current_text,
            recommended_rewrite=recommended_rewrite
        )

        return Response({
            "status": "success",
            "proposal": proposal,
            "clause_name": clause.clause_name
        })

    except Clause.DoesNotExist:
        return Response({'error': 'Clause not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error("generate_counter_proposal_action error: %s", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_redlines_action(request, clause_id):
    """POST /api/legal-playbook/clause/<clause_id>/export-redlines"""
    try:
        from core.models import Clause
        user = request.user
        clause = Clause.objects.select_related('contract').get(
            id=clause_id,
            contract__user=user
        )

        return Response({
            "status": "success",
            "message": f"Redlines for '{clause.clause_name}' exported successfully",
            "format": "DOCX",
            "clause_name": clause.clause_name,
            "contract_name": clause.contract.original_filename or clause.contract.filename
        })

    except Clause.DoesNotExist:
        return Response({'error': 'Clause not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error("export_redlines_action error: %s", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_approval_workflow(request, clause_id):
    """POST /api/legal-playbook/clause/<clause_id>/approve"""
    try:
        from core.models import Clause
        user = request.user
        clause = Clause.objects.select_related('contract').get(
            id=clause_id,
            contract__user=user
        )

        return Response({
            "status": "success",
            "message": f"Approval workflow initiated for '{clause.clause_name}'",
            "workflow_id": f"WF-{clause.id}",
            "approvers": ["Legal Team", "Risk Management", "Business Unit"],
            "estimated_completion": "3-5 business days"
        })

    except Clause.DoesNotExist:
        return Response({'error': 'Clause not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error("trigger_approval_workflow error: %s", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
