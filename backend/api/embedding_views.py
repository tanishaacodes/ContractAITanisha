"""
API Views for Embedding-Based Contract Analysis
Deterministic, explainable, LLM-free analysis
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from core.models import (
    Contract, Clause, RiskPlaybook, IntentTemplate, ApprovedClause,
    ClauseDeviationScore, MissingSafeguardDetection, GoldStandardTemplate, ExpectedObligation
)
from api.embedding_risk_scorer import embedding_risk_scorer
from api.embedding_intent_detector import embedding_intent_detector
from api.embedding_redline_engine import embedding_redline_engine
from api.embedding_chat_service import embedding_chat_service
from api.embedding_service import embedding_service
from api.embedding_deviation_service import DeviationDetectionService
from api.embedding_safeguard_service import SafeguardDetectionService
import logging

logger = logging.getLogger(__name__)


# =========================
# RISK SCORING ENDPOINTS
# =========================

@api_view(['POST'])
def analyze_risk_embedding(request, contract_id):
    """
    Analyze contract risk using embedding-based scoring (no LLM).

    POST /api/embedding/contracts/{contract_id}/analyze-risk

    Query params:
    - jurisdiction: Optional jurisdiction filter

    Returns deterministic risk scores based on similarity to risk playbooks.
    """
    try:
        contract = get_object_or_404(Contract, id=contract_id)
        jurisdiction = request.query_params.get('jurisdiction', contract.jurisdiction)

        clauses = contract.clauses.all()

        if not clauses:
            return Response({
                'error': 'No clauses found in contract'
            }, status=status.HTTP_404_NOT_FOUND)

        # Score all clauses
        clause_scores = embedding_risk_scorer.score_multiple_clauses(
            clauses=list(clauses),
            jurisdiction=jurisdiction
        )

        # Compute aggregate statistics
        total_clauses = len(clause_scores)
        high_risk_count = sum(1 for c in clause_scores if c['risk_level'] == 'HIGH')
        medium_risk_count = sum(1 for c in clause_scores if c['risk_level'] == 'MEDIUM')
        low_risk_count = sum(1 for c in clause_scores if c['risk_level'] == 'LOW')

        avg_risk_score = sum(c['risk_score'] for c in clause_scores) / total_clauses if total_clauses else 0

        # Determine overall risk level
        if high_risk_count > 0:
            overall_risk_level = 'HIGH'
        elif medium_risk_count > total_clauses * 0.3:  # >30% medium risk
            overall_risk_level = 'MEDIUM'
        else:
            overall_risk_level = 'LOW'

        return Response({
            'contract_id': contract_id,
            'contract_name': contract.original_filename,
            'overall_risk_level': overall_risk_level,
            'average_risk_score': round(avg_risk_score, 1),
            'total_clauses': total_clauses,
            'high_risk_count': high_risk_count,
            'medium_risk_count': medium_risk_count,
            'low_risk_count': low_risk_count,
            'clause_scores': clause_scores,
            'analysis_method': 'embedding-based (deterministic)',
            'model': embedding_service.active_model_name
        })

    except Exception as e:
        logger.error(f"Error analyzing risk: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def score_clause_risk(request, clause_id):
    """
    Score a single clause for risk.

    POST /api/embedding/clauses/{clause_id}/score-risk
    """
    try:
        clause = get_object_or_404(Clause, id=clause_id)
        jurisdiction = request.data.get('jurisdiction')

        risk_analysis = embedding_risk_scorer.score_clause(clause, jurisdiction)

        return Response({
            'clause_id': clause_id,
            'clause_name': clause.clause_name,
            **risk_analysis
        })

    except Exception as e:
        logger.error(f"Error scoring clause risk: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================
# INTENT DETECTION ENDPOINTS
# =========================

@api_view(['POST'])
def detect_contract_intents(request, contract_id):
    """
    Detect legal intents across all clauses in a contract.

    POST /api/embedding/contracts/{contract_id}/detect-intents

    Returns intent distribution and analysis.
    """
    try:
        contract = get_object_or_404(Contract, id=contract_id)
        clauses = list(contract.clauses.all())

        if not clauses:
            return Response({
                'error': 'No clauses found in contract'
            }, status=status.HTTP_404_NOT_FOUND)

        # Analyze intents
        analysis = embedding_intent_detector.analyze_contract_intents(clauses)

        return Response({
            'contract_id': contract_id,
            'contract_name': contract.original_filename,
            **analysis,
            'analysis_method': 'embedding-based (deterministic)',
            'model': embedding_service.active_model_name
        })

    except Exception as e:
        logger.error(f"Error detecting intents: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def detect_clause_intent(request, clause_id):
    """
    Detect intent of a single clause.

    POST /api/embedding/clauses/{clause_id}/detect-intent

    Query params:
    - top_k: Number of top intents to return (default: 3)
    """
    try:
        clause = get_object_or_404(Clause, id=clause_id)
        top_k = int(request.query_params.get('top_k', 3))

        intents = embedding_intent_detector.detect_clause_intent(clause, top_k=top_k)

        return Response({
            'clause_id': clause_id,
            'clause_name': clause.clause_name,
            'detected_intents': intents,
            'primary_intent': intents[0] if intents else None
        })

    except Exception as e:
        logger.error(f"Error detecting clause intent: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def find_clauses_by_intent(request, contract_id):
    """
    Find clauses matching specific intent criteria.

    POST /api/embedding/contracts/{contract_id}/find-by-intent

    Body:
    {
        "intent_name": "Shift liability to counterparty",
        "intent_category": "LIABILITY_SHIFT",
        "party_impact": "FAVOR_COUNTERPARTY",
        "min_confidence": 0.7
    }
    """
    try:
        contract = get_object_or_404(Contract, id=contract_id)
        clauses = list(contract.clauses.all())

        intent_name = request.data.get('intent_name')
        intent_category = request.data.get('intent_category')
        party_impact = request.data.get('party_impact')
        min_confidence = float(request.data.get('min_confidence', 0.7))

        matches = embedding_intent_detector.find_clauses_by_intent(
            clauses=clauses,
            intent_name=intent_name,
            intent_category=intent_category,
            party_impact=party_impact,
            min_confidence=min_confidence
        )

        return Response({
            'contract_id': contract_id,
            'filters': {
                'intent_name': intent_name,
                'intent_category': intent_category,
                'party_impact': party_impact,
                'min_confidence': min_confidence
            },
            'matches': matches,
            'total_matches': len(matches)
        })

    except Exception as e:
        logger.error(f"Error finding clauses by intent: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================
# REDLINING ENDPOINTS
# =========================

@api_view(['POST'])
def suggest_contract_redlines(request, contract_id):
    """
    Suggest redlines for all risky clauses in a contract.

    POST /api/embedding/contracts/{contract_id}/suggest-redlines

    Body:
    {
        "protection_level": "BALANCED",  // MAXIMUM, BALANCED, MINIMUM
        "min_risk_level": "MEDIUM"       // LOW, MEDIUM, HIGH
    }

    Returns approved clause alternatives with diffs.
    """
    try:
        contract = get_object_or_404(Contract, id=contract_id)

        protection_level = request.data.get('protection_level', 'BALANCED')
        min_risk_level = request.data.get('min_risk_level', 'MEDIUM')

        suggestions = embedding_redline_engine.suggest_redlines_for_contract(
            contract=contract,
            protection_level=protection_level,
            min_risk_level=min_risk_level
        )

        return Response({
            'contract_id': contract_id,
            'contract_name': contract.original_filename,
            'protection_level': protection_level,
            'min_risk_level': min_risk_level,
            'total_suggestions': len(suggestions),
            'suggestions': suggestions,
            'analysis_method': 'embedding-based redlining (zero hallucination)'
        })

    except Exception as e:
        logger.error(f"Error suggesting redlines: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def suggest_clause_redline(request, clause_id):
    """
    Suggest redline for a single clause.

    POST /api/embedding/clauses/{clause_id}/suggest-redline

    Body:
    {
        "protection_level": "BALANCED",
        "jurisdiction": "USA"
    }
    """
    try:
        clause = get_object_or_404(Clause, id=clause_id)

        protection_level = request.data.get('protection_level', 'BALANCED')
        jurisdiction = request.data.get('jurisdiction')

        suggestion = embedding_redline_engine.suggest_redline(
            clause=clause,
            protection_level=protection_level,
            jurisdiction=jurisdiction
        )

        if not suggestion:
            return Response({
                'clause_id': clause_id,
                'message': 'No redline needed - clause is low risk or no approved alternative found'
            })

        return Response(suggestion)

    except Exception as e:
        logger.error(f"Error suggesting clause redline: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================
# CHAT ENDPOINTS
# =========================

@api_view(['POST'])
def query_contract_embedding(request, contract_id):
    """
    Query a contract using semantic search (no LLM generation).

    POST /api/embedding/contracts/{contract_id}/query

    Body:
    {
        "query": "Where is liability capped?",
        "top_k": 3,
        "min_similarity": 0.6
    }

    Returns relevant clauses without hallucination.
    """
    try:
        contract = get_object_or_404(Contract, id=contract_id)

        query = request.data.get('query', '')
        top_k = int(request.data.get('top_k', 3))
        min_similarity = float(request.data.get('min_similarity', 0.6))

        if not query:
            return Response({
                'error': 'Query is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = embedding_chat_service.query_contract(
            contract=contract,
            query=query,
            top_k=top_k,
            min_similarity=min_similarity
        )

        return Response({
            'contract_id': contract_id,
            'contract_name': contract.original_filename,
            **result,
            'analysis_method': 'pure semantic retrieval (no generation)'
        })

    except Exception as e:
        logger.error(f"Error querying contract: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def query_multiple_contracts(request):
    """
    Query across multiple contracts.

    POST /api/embedding/contracts/query-multiple

    Body:
    {
        "contract_ids": ["id1", "id2", "id3"],
        "query": "What are the termination clauses?",
        "top_k": 5,
        "min_similarity": 0.6
    }
    """
    try:
        contract_ids = request.data.get('contract_ids', [])
        query = request.data.get('query', '')
        top_k = int(request.data.get('top_k', 5))
        min_similarity = float(request.data.get('min_similarity', 0.6))

        if not contract_ids or not query:
            return Response({
                'error': 'contract_ids and query are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        contracts = Contract.objects.filter(id__in=contract_ids)

        result = embedding_chat_service.query_multiple_contracts(
            contracts=list(contracts),
            query=query,
            top_k=top_k,
            min_similarity=min_similarity
        )

        return Response({
            **result,
            'analysis_method': 'pure semantic retrieval (no generation)'
        })

    except Exception as e:
        logger.error(f"Error querying multiple contracts: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def suggest_questions(request, contract_id):
    """
    Suggest common questions for a contract.

    GET /api/embedding/contracts/{contract_id}/suggest-questions
    """
    try:
        contract = get_object_or_404(Contract, id=contract_id)

        questions = embedding_chat_service.suggest_questions(contract)

        return Response({
            'contract_id': contract_id,
            'contract_type': contract.contract_type,
            'suggested_questions': questions
        })

    except Exception as e:
        logger.error(f"Error suggesting questions: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================
# ADMIN ENDPOINTS (Manage Libraries)
# =========================

@api_view(['GET', 'POST'])
def manage_risk_playbooks(request):
    """
    GET: List all risk playbooks
    POST: Create new risk playbook with embedding
    """
    if request.method == 'GET':
        playbooks = RiskPlaybook.objects.filter(is_active=True)

        return Response({
            'total': playbooks.count(),
            'playbooks': [{
                'id': pb.id,
                'risk_name': pb.risk_name,
                'risk_type': pb.risk_type,
                'severity_weight': pb.severity_weight,
                'jurisdiction': pb.jurisdiction,
                'has_embedding': bool(pb.embedding)
            } for pb in playbooks]
        })

    elif request.method == 'POST':
        # Create new risk playbook
        risk_name = request.data.get('risk_name')
        risk_type = request.data.get('risk_type')
        risk_description = request.data.get('risk_description')
        example_text = request.data.get('example_clause_text')
        severity_weight = float(request.data.get('severity_weight', 0.5))

        if not all([risk_name, risk_type, risk_description, example_text]):
            return Response({
                'error': 'risk_name, risk_type, risk_description, and example_clause_text are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Generate embedding
        embedding = embedding_service.embed_text(example_text)

        playbook = RiskPlaybook.objects.create(
            risk_name=risk_name,
            risk_type=risk_type,
            risk_description=risk_description,
            example_clause_text=example_text,
            severity_weight=severity_weight,
            embedding=embedding,
            embedding_model=embedding_service.active_model_name,
            created_by=request.user if hasattr(request, 'user') else None
        )

        return Response({
            'message': 'Risk playbook created successfully',
            'playbook_id': playbook.id
        }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
def manage_intent_templates(request):
    """
    GET: List all intent templates
    POST: Create new intent template with embedding
    """
    if request.method == 'GET':
        templates = IntentTemplate.objects.filter(is_active=True)

        return Response({
            'total': templates.count(),
            'templates': [{
                'id': t.id,
                'intent_name': t.intent_name,
                'intent_category': t.intent_category,
                'party_impact': t.party_impact,
                'risk_level': t.risk_level,
                'has_embedding': bool(t.embedding)
            } for t in templates]
        })

    elif request.method == 'POST':
        intent_name = request.data.get('intent_name')
        intent_category = request.data.get('intent_category')
        intent_description = request.data.get('intent_description')
        example_text = request.data.get('example_clause_text')
        party_impact = request.data.get('party_impact', 'NEUTRAL')
        risk_level = request.data.get('risk_level', 'MEDIUM')

        if not all([intent_name, intent_category, intent_description, example_text]):
            return Response({
                'error': 'intent_name, intent_category, intent_description, and example_clause_text are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Generate embedding
        embedding = embedding_service.embed_text(example_text)

        template = IntentTemplate.objects.create(
            intent_name=intent_name,
            intent_category=intent_category,
            intent_description=intent_description,
            example_clause_text=example_text,
            party_impact=party_impact,
            risk_level=risk_level,
            embedding=embedding,
            embedding_model=embedding_service.active_model_name,
            created_by=request.user if hasattr(request, 'user') else None
        )

        return Response({
            'message': 'Intent template created successfully',
            'template_id': template.id
        }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
def manage_approved_clauses(request):
    """
    GET: List all approved clauses
    POST: Create new approved clause with embedding
    """
    if request.method == 'GET':
        clauses = ApprovedClause.objects.filter(is_active=True)

        return Response({
            'total': clauses.count(),
            'clauses': [{
                'id': c.id,
                'clause_name': c.clause_name,
                'clause_type': c.clause_type,
                'intent_name': c.intent_name,
                'protection_level': c.protection_level,
                'jurisdiction': c.jurisdiction,
                'has_embedding': bool(c.embedding)
            } for c in clauses]
        })

    elif request.method == 'POST':
        clause_name = request.data.get('clause_name')
        clause_type = request.data.get('clause_type')
        clause_text = request.data.get('clause_text')
        intent_name = request.data.get('intent_name')
        protection_level = request.data.get('protection_level', 'BALANCED')
        jurisdiction = request.data.get('jurisdiction', 'Common Law')

        if not all([clause_name, clause_type, clause_text, intent_name]):
            return Response({
                'error': 'clause_name, clause_type, clause_text, and intent_name are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Generate embedding
        embedding = embedding_service.embed_text(clause_text)

        approved_clause = ApprovedClause.objects.create(
            clause_name=clause_name,
            clause_type=clause_type,
            clause_text=clause_text,
            intent_name=intent_name,
            protection_level=protection_level,
            jurisdiction=jurisdiction,
            embedding=embedding,
            embedding_model=embedding_service.active_model_name,
            created_by=request.user if hasattr(request, 'user') else None
        )

        return Response({
            'message': 'Approved clause created successfully',
            'clause_id': approved_clause.id
        }, status=status.HTTP_201_CREATED)


# =========================
# DEVIATION DETECTION ENDPOINTS (Feature 1)
# =========================

@api_view(['POST'])
def analyze_clause_deviation(request, clause_id):
    """
    Analyze how far a clause deviates from gold-standard templates and industry benchmarks.

    POST /api/embedding/clauses/{clause_id}/analyze-deviation

    Feature 1: Clause Deviation & Negotiation Intelligence

    Returns:
    - Deviation score (0-1, higher = more similar = less deviation)
    - Risk level (SAFE/REVIEW/HIGH_RISK)
    - Suggested replacement text
    - Explainability
    """
    try:
        clause = get_object_or_404(Clause, id=clause_id)

        if not clause.extracted_text or not clause.extracted_text.strip():
            return Response({
                'error': 'Clause has no extracted text'
            }, status=status.HTTP_400_BAD_REQUEST)

        deviation_service = DeviationDetectionService()

        result = deviation_service.analyze_clause_deviation(
            clause_id=clause.id,
            contract_id=clause.contract_id,
            clause_text=clause.extracted_text,
            clause_category=deviation_service._map_clause_name_to_category(clause.clause_name)
        )

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error analyzing clause deviation: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def analyze_contract_deviations(request, contract_id):
    """
    Analyze all clauses in a contract for deviations.

    POST /api/embedding/contracts/{contract_id}/analyze-deviations

    Feature 1: Clause Deviation & Negotiation Intelligence

    Returns contract-level deviation summary with all clause results.
    """
    from core.models import ClauseDeviationScore

    try:
        contract = get_object_or_404(Contract, id=contract_id)

        # Delete existing deviation scores for this contract to prevent duplicates
        ClauseDeviationScore.objects.filter(contract_id=contract_id).delete()

        deviation_service = DeviationDetectionService()
        result = deviation_service.analyze_contract_deviations(contract_id)

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error analyzing contract deviations: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_clause_deviation_score(request, clause_id):
    """
    Get stored deviation score for a clause.

    GET /api/embedding/clauses/{clause_id}/deviation-score

    Returns previously computed deviation score if exists.
    """
    from core.models import ClauseDeviationScore

    try:
        deviation_score = ClauseDeviationScore.objects.filter(
            clause_id=clause_id
        ).order_by('-created_at').first()

        if not deviation_score:
            return Response({
                'message': 'No deviation score found for this clause',
                'clause_id': clause_id
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'clause_id': clause_id,
            'deviation_score': deviation_score.overall_deviation_score,
            'risk_level': deviation_score.overall_risk_level,
            'risk_type': deviation_score.risk_type,
            'gold_standard_similarity': deviation_score.gold_standard_similarity,
            'industry_benchmark_similarity': deviation_score.industry_benchmark_similarity,
            'past_accepted_similarity': deviation_score.past_accepted_similarity,
            'suggested_replacement': deviation_score.suggested_replacement_text,
            'explanation': deviation_score.explanation,
            'court_precedent': deviation_score.court_precedent,
            'created_at': deviation_score.created_at
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting deviation score: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================
# MISSING SAFEGUARD DETECTION ENDPOINTS (Feature 2)
# =========================

@api_view(['POST'])
@permission_classes([AllowAny])
def detect_missing_safeguards(request, contract_id):
    """
    Detect missing or weak safeguards in a contract.

    POST /api/embedding/contracts/{contract_id}/detect-safeguards

    Feature 2: Contract Obligation Leakage & Missed Safeguards Detection

    Query params:
    - contract_type: Optional contract type filter

    Returns:
    - Missing safeguards
    - Weak safeguards
    - Present safeguards
    - AI insights and suggested actions
    """
    from core.models import MissingSafeguardDetection

    try:
        contract = get_object_or_404(Contract, id=contract_id)
        contract_type = request.query_params.get('contract_type', contract.contract_type)

        # Delete existing safeguard detections for this contract to prevent duplicates
        MissingSafeguardDetection.objects.filter(contract_id=contract_id).delete()

        safeguard_service = SafeguardDetectionService()
        result = safeguard_service.detect_missing_safeguards(
            contract_id=contract_id,
            contract_type=contract_type
        )

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error detecting missing safeguards: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_safeguard_summary_table(request, contract_id):
    """
    Get safeguard summary in table format for UI display.

    GET /api/embedding/contracts/{contract_id}/safeguard-table

    Feature 2: UI table data

    Returns formatted table rows with safeguard status.
    """
    try:
        safeguard_service = SafeguardDetectionService()
        table_rows = safeguard_service.get_safeguard_summary_table(contract_id)

        return Response({
            'contract_id': contract_id,
            'safeguards': table_rows
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting safeguard table: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_contract_risk_heatmap(request, contract_id):
    """
    Get risk heatmap data for contract (combines deviation + safeguard data).

    GET /api/embedding/contracts/{contract_id}/risk-heatmap

    Feature 3: Risk Heatmap UI Component

    Returns:
    - Risk heatmap by clause category
    - Color-coded risk levels
    - Missing safeguards
    """
    from core.models import ClauseDeviationScore, MissingSafeguardDetection

    try:
        contract = get_object_or_404(Contract, id=contract_id)

        # Get deviation scores
        deviation_scores = ClauseDeviationScore.objects.filter(
            contract_id=contract_id
        )

        # Get missing safeguards
        missing_safeguards = MissingSafeguardDetection.objects.filter(
            contract_id=contract_id,
            status__in=['MISSING', 'WEAK']
        )

        # Build heatmap data
        heatmap_items = []

        # Add deviation-based risks
        for dev_score in deviation_scores:
            try:
                clause = Clause.objects.get(id=dev_score.clause_id)

                # Fetch gold standard template if exists
                gold_standard = None
                if dev_score.gold_standard_id:
                    try:
                        gold_standard = GoldStandardTemplate.objects.get(id=dev_score.gold_standard_id)
                    except GoldStandardTemplate.DoesNotExist:
                        pass

                heatmap_items.append({
                    'clauseType': clause.clause_name,
                    'category': gold_standard.clause_category if gold_standard else 'OTHER',
                    'riskScore': dev_score.overall_deviation_score,
                    'status': dev_score.overall_risk_level,
                    'type': 'DEVIATION',
                    'originalText': clause.extracted_text or clause.context_sentences or '',
                    'suggestedText': dev_score.suggested_replacement_text,
                    'details': {
                        'risk_type': dev_score.risk_type,
                        'explanation': dev_score.explanation,
                        'suggested_replacement': dev_score.suggested_replacement_text,
                        'similarity': dev_score.overall_deviation_score,
                        'goldStandardSimilarity': dev_score.gold_standard_similarity,
                        'standardClause': gold_standard.approved_clause_text if gold_standard else None
                    }
                })
            except Clause.DoesNotExist:
                continue

        # Add missing safeguards
        for safeguard in missing_safeguards:
            # Fetch expected obligation
            obligation = None
            if safeguard.expected_obligation_id:
                try:
                    obligation = ExpectedObligation.objects.get(id=safeguard.expected_obligation_id)
                except ExpectedObligation.DoesNotExist:
                    continue

            if not obligation:
                continue

            # Get matched clause text if available
            matched_text = ''
            if safeguard.matched_clause_id:
                try:
                    matched_clause = Clause.objects.get(id=safeguard.matched_clause_id)
                    matched_text = matched_clause.extracted_text or matched_clause.context_sentences or ''
                except Clause.DoesNotExist:
                    pass

            heatmap_items.append({
                'clauseType': obligation.obligation_name,
                'category': obligation.obligation_category,
                'riskScore': 1.0 - safeguard.confidence,  # Invert confidence for risk score
                'status': safeguard.status,
                'type': 'MISSING_SAFEGUARD',
                'originalText': matched_text,
                'suggestedText': safeguard.suggested_clause_text or '',
                'details': {
                    'criticality': obligation.criticality,
                    'ai_insight': safeguard.ai_insight,
                    'suggested_action': safeguard.suggested_action,
                    'suggested_clause': safeguard.suggested_clause_text,
                    'reason': f"Missing {obligation.criticality} safeguard",
                    'explanation': safeguard.ai_insight,
                    'riskType': f"Missing {obligation.obligation_category}",
                    'confidenceLevel': safeguard.confidence
                }
            })

        return Response({
            'contract_id': contract_id,
            'contract_name': contract.original_filename,
            'total_items': len(heatmap_items),
            'heatmap_items': heatmap_items
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error generating risk heatmap: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================
# ADMIN ENDPOINTS - Gold Standards & Expected Obligations
# =========================

@api_view(['POST'])
def create_gold_standard_template(request):
    """
    Create a new gold-standard template.

    POST /api/embedding/admin/gold-standards

    Body:
    {
        "template_name": str,
        "clause_category": str,
        "approved_clause_text": str,
        "jurisdiction": str (optional),
        "safe_threshold": float (default 0.90),
        "review_threshold": float (default 0.75)
    }
    """
    from core.models import GoldStandardTemplate

    try:
        template_name = request.data.get('template_name')
        clause_category = request.data.get('clause_category')
        approved_clause_text = request.data.get('approved_clause_text')
        jurisdiction = request.data.get('jurisdiction')
        safe_threshold = request.data.get('safe_threshold', 0.90)
        review_threshold = request.data.get('review_threshold', 0.75)
        legal_notes = request.data.get('legal_notes')

        if not all([template_name, clause_category, approved_clause_text]):
            return Response({
                'error': 'Missing required fields'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Generate embedding
        embedding = embedding_service.embed_text(approved_clause_text)

        template = GoldStandardTemplate.objects.create(
            template_name=template_name,
            clause_category=clause_category,
            approved_clause_text=approved_clause_text,
            embedding=embedding,
            embedding_model=embedding_service.active_model_name,
            jurisdiction=jurisdiction,
            safe_threshold=safe_threshold,
            review_threshold=review_threshold,
            legal_notes=legal_notes
        )

        return Response({
            'message': 'Gold-standard template created successfully',
            'template_id': template.id
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating gold-standard template: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_expected_obligation(request):
    """
    Create a new expected obligation for safeguard detection.

    POST /api/embedding/admin/expected-obligations

    Body:
    {
        "obligation_name": str,
        "obligation_category": str,
        "criticality": str (CRITICAL/IMPORTANT/RECOMMENDED),
        "expected_clause_text": str,
        "absence_risk_description": str,
        "suggested_clause_text": str (optional),
        "contract_type": str (optional),
        "presence_threshold": float (default 0.70)
    }
    """
    from core.models import ExpectedObligation

    try:
        obligation_name = request.data.get('obligation_name')
        obligation_category = request.data.get('obligation_category')
        criticality = request.data.get('criticality')
        expected_clause_text = request.data.get('expected_clause_text')
        absence_risk_description = request.data.get('absence_risk_description')
        suggested_clause_text = request.data.get('suggested_clause_text')
        contract_type = request.data.get('contract_type')
        presence_threshold = request.data.get('presence_threshold', 0.70)

        if not all([obligation_name, obligation_category, criticality, expected_clause_text, absence_risk_description]):
            return Response({
                'error': 'Missing required fields'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Generate embedding
        embedding = embedding_service.embed_text(expected_clause_text)

        obligation = ExpectedObligation.objects.create(
            obligation_name=obligation_name,
            obligation_category=obligation_category,
            criticality=criticality,
            expected_clause_text=expected_clause_text,
            embedding=embedding,
            embedding_model=embedding_service.active_model_name,
            presence_threshold=presence_threshold,
            absence_risk_description=absence_risk_description,
            absence_risk_example=request.data.get('absence_risk_example'),
            suggested_clause_text=suggested_clause_text,
            contract_type=contract_type,
            party_protected=request.data.get('party_protected'),
            jurisdiction=request.data.get('jurisdiction')
        )

        return Response({
            'message': 'Expected obligation created successfully',
            'obligation_id': obligation.id
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating expected obligation: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
