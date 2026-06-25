"""
Negotiation & Counter-Proposal API Views
=========================================
API endpoints for generating counter-proposals and predicting negotiation outcomes.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from core.models import Clause, Contract
from negotiation.models import Counterparty
from .services.counter_proposal import CounterProposalGenerator

logger = logging.getLogger(__name__)


@api_view(['POST'])
def generate_counter_proposal(request, clause_id):
    """
    Generate AI-powered counter-proposal for a clause.

    POST /api/clauses/{clause_id}/counter-proposal

    Request body:
    {
        "concerns": ["Unlimited liability", "No cap on damages"],  // Optional
        "your_position": "client",  // client or vendor (optional)
        "counterparty_id": "uuid",  // Optional counterparty ID
        "provider": "openai"  // openai or anthropic (default: openai)
    }

    Response:
    {
        "success": true,
        "proposed_clause": "...",
        "concerns": [...],
        "counter_proposals": [
            {
                "text": "Counter-proposal text...",
                "rationale": "Why this addresses concerns...",
                "compromises": ["Alternative 1", "Alternative 2"],
                "acceptance_likelihood": 0.75,
                "quality_score": 0.85,
                "rank": 1
            }
        ],
        "recommended_proposal": {...},
        "negotiation_strategy": {
            "approach": "CONFIDENT",
            "reasoning": "...",
            "suggested_action": "...",
            "acceptance_likelihood": 75.0,
            "fallback_positions": [...]
        }
    }
    """
    try:
        clause = get_object_or_404(Clause, id=clause_id)

        # Get request data
        concerns = request.data.get('concerns', [])
        your_position = request.data.get('your_position')
        counterparty_id = request.data.get('counterparty_id')
        provider = request.data.get('provider', 'openai')

        # Get clause text
        clause_text = (
            clause.extracted_text or
            clause.context_sentences or
            clause.text_spans or
            ''
        )

        if not clause_text or len(clause_text.strip()) < 10:
            return Response({
                'success': False,
                'error': 'Clause text is too short or empty'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get counterparty profile if provided
        counterparty_profile = None
        if counterparty_id:
            try:
                counterparty = Counterparty.objects.get(id=counterparty_id)
                counterparty_profile = {
                    'name': counterparty.name,
                    'aggressiveness_score': counterparty.aggressiveness_score,
                    'risk_profile': counterparty.risk_profile
                }
            except Counterparty.DoesNotExist:
                logger.warning(f"[COUNTER-PROPOSAL] Counterparty {counterparty_id} not found")

        # Initialize generator
        generator = CounterProposalGenerator(provider=provider)

        # Generate counter-proposal
        result = generator.generate_counter_proposal(
            proposed_clause=clause_text,
            concerns=concerns,
            your_position=your_position,
            counterparty_profile=counterparty_profile
        )

        if not result['success']:
            return Response({
                'success': False,
                'error': result.get('error', 'Failed to generate counter-proposal')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.info(f"[COUNTER-PROPOSAL] Generated for clause {clause_id}")

        return Response(result, status=status.HTTP_200_OK)

    except Clause.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Clause {clause_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"[COUNTER-PROPOSAL] Error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def analyze_clause_for_negotiation(request, clause_id):
    """
    Analyze if a clause requires negotiation.

    POST /api/clauses/{clause_id}/analyze-negotiation

    Request body:
    {
        "counterparty_id": "uuid"  // Optional
    }

    Response:
    {
        "success": true,
        "clause_text": "...",
        "clause_type": "indemnity",
        "risk_score": 0.85,
        "detected_risks": [
            {"keyword": "unlimited", "severity": "high"},
            {"keyword": "consequential damages", "severity": "high"}
        ],
        "should_negotiate": true,
        "recommendation": "⚠️ HIGH RISK: This clause has 2 risk factors..."
    }
    """
    try:
        clause = get_object_or_404(Clause, id=clause_id)

        # Get clause text
        clause_text = (
            clause.extracted_text or
            clause.context_sentences or
            clause.text_spans or
            ''
        )

        if not clause_text or len(clause_text.strip()) < 10:
            return Response({
                'success': False,
                'error': 'Clause text is too short or empty'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get counterparty profile if provided
        counterparty_id = request.data.get('counterparty_id')
        counterparty_profile = None

        if counterparty_id:
            try:
                counterparty = Counterparty.objects.get(id=counterparty_id)
                counterparty_profile = {
                    'name': counterparty.name,
                    'aggressiveness_score': counterparty.aggressiveness_score,
                    'risk_profile': counterparty.risk_profile
                }
            except Counterparty.DoesNotExist:
                pass

        # Initialize generator
        generator = CounterProposalGenerator()

        # Analyze clause
        result = generator.analyze_clause_for_negotiation(
            clause_text=clause_text,
            clause_type=clause.clause_type or clause.clause_name,
            counterparty_profile=counterparty_profile
        )

        if not result['success']:
            return Response({
                'success': False,
                'error': result.get('error', 'Analysis failed')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.info(f"[NEGOTIATION-ANALYSIS] Analyzed clause {clause_id}, risk_score={result['risk_score']}")

        return Response(result, status=status.HTTP_200_OK)

    except Clause.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Clause {clause_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"[NEGOTIATION-ANALYSIS] Error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def batch_analyze_contract_for_negotiation(request, contract_id):
    """
    Analyze all clauses in a contract to identify negotiation priorities.

    POST /api/contracts/{contract_id}/analyze-for-negotiation

    Request body:
    {
        "counterparty_id": "uuid",  // Optional
        "min_risk_score": 0.6  // Only return clauses with risk >= this (default: 0.6)
    }

    Response:
    {
        "success": true,
        "contract_id": "uuid",
        "total_clauses": 25,
        "high_risk_clauses": 5,
        "negotiation_recommended": true,
        "priority_clauses": [
            {
                "clause_id": "uuid",
                "clause_name": "Indemnity",
                "risk_score": 0.85,
                "should_negotiate": true,
                "detected_risks": [...]
            }
        ],
        "summary": {
            "critical_issues": 5,
            "medium_issues": 8,
            "low_issues": 12
        }
    }
    """
    try:
        contract = get_object_or_404(Contract, id=contract_id)

        # Get request data
        counterparty_id = request.data.get('counterparty_id')
        min_risk_score = float(request.data.get('min_risk_score', 0.6))

        # Get counterparty profile
        counterparty_profile = None
        if counterparty_id:
            try:
                counterparty = Counterparty.objects.get(id=counterparty_id)
                counterparty_profile = {
                    'name': counterparty.name,
                    'aggressiveness_score': counterparty.aggressiveness_score,
                    'risk_profile': counterparty.risk_profile
                }
            except Counterparty.DoesNotExist:
                pass

        # Get all clauses
        clauses = Clause.objects.filter(contract=contract)

        # Analyze each clause
        generator = CounterProposalGenerator()
        priority_clauses = []
        critical_count = 0
        medium_count = 0
        low_count = 0

        for clause in clauses:
            clause_text = (
                clause.extracted_text or
                clause.context_sentences or
                clause.text_spans or
                ''
            )

            if not clause_text or len(clause_text.strip()) < 10:
                continue

            analysis = generator.analyze_clause_for_negotiation(
                clause_text=clause_text,
                clause_type=clause.clause_type or clause.clause_name,
                counterparty_profile=counterparty_profile
            )

            if not analysis['success']:
                continue

            risk_score = analysis['risk_score']

            # Categorize
            if risk_score >= 0.8:
                critical_count += 1
            elif risk_score >= 0.6:
                medium_count += 1
            else:
                low_count += 1

            # Add to priority list if above threshold
            if risk_score >= min_risk_score:
                priority_clauses.append({
                    'clause_id': clause.id,
                    'clause_name': clause.clause_name,
                    'clause_type': clause.clause_type or 'general',
                    'risk_score': risk_score,
                    'should_negotiate': analysis['should_negotiate'],
                    'detected_risks': analysis['detected_risks'],
                    'recommendation': analysis['recommendation']
                })

        # Sort by risk score descending
        priority_clauses.sort(key=lambda x: x['risk_score'], reverse=True)

        logger.info(
            f"[BATCH-NEGOTIATION-ANALYSIS] Contract {contract_id}: "
            f"{len(priority_clauses)} priority clauses identified"
        )

        return Response({
            'success': True,
            'contract_id': contract_id,
            'total_clauses': clauses.count(),
            'high_risk_clauses': critical_count,
            'negotiation_recommended': critical_count > 0 or medium_count > 3,
            'priority_clauses': priority_clauses,
            'summary': {
                'critical_issues': critical_count,
                'medium_issues': medium_count,
                'low_issues': low_count
            }
        }, status=status.HTTP_200_OK)

    except Contract.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Contract {contract_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"[BATCH-NEGOTIATION-ANALYSIS] Error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_counterparty_profile(request, counterparty_id):
    """
    Get counterparty negotiation profile.

    GET /api/counterparties/{counterparty_id}/profile

    Response:
    {
        "success": true,
        "counterparty": {
            "id": "uuid",
            "name": "Acme Corp",
            "industry": "Technology",
            "risk_profile": 0.65,
            "aggressiveness_score": 0.75,
            "negotiation_insights": {
                "typical_behavior": "Aggressive but willing to compromise",
                "acceptance_rate": 0.45,
                "avg_rounds": 3.2
            }
        }
    }
    """
    try:
        counterparty = get_object_or_404(Counterparty, id=counterparty_id)

        # Get negotiation history stats if available
        from negotiation.models import NegotiationHistory
        history = NegotiationHistory.objects.filter(counterparty=counterparty)

        total_negotiations = history.count()
        accepted_count = history.filter(accepted=True).count()
        acceptance_rate = accepted_count / total_negotiations if total_negotiations > 0 else 0.5

        avg_rounds = history.aggregate(avg=models.Avg('redline_rounds'))['avg'] or 2.0

        # Generate insights
        if counterparty.aggressiveness_score > 0.7:
            behavior = "Aggressive negotiator, expects multiple rounds"
        elif counterparty.aggressiveness_score > 0.5:
            behavior = "Moderately assertive, open to reasonable compromises"
        else:
            behavior = "Flexible negotiator, collaborative approach"

        return Response({
            'success': True,
            'counterparty': {
                'id': counterparty.id,
                'name': counterparty.name,
                'industry': counterparty.industry,
                'risk_profile': counterparty.risk_profile,
                'aggressiveness_score': counterparty.aggressiveness_score,
                'negotiation_insights': {
                    'typical_behavior': behavior,
                    'acceptance_rate': round(acceptance_rate, 2),
                    'avg_rounds': round(avg_rounds, 1),
                    'total_negotiations': total_negotiations
                }
            }
        }, status=status.HTTP_200_OK)

    except Counterparty.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Counterparty {counterparty_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"[COUNTERPARTY-PROFILE] Error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
