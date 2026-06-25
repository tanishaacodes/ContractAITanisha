"""
Clause Addition & Rewriting API Views
======================================
API endpoints for adding new clauses and rewriting existing ones with AI.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
import networkx as nx

from core.models import Contract, Clause
from .services.clause_addition import ClauseAdditionService
from .services.clause_graph import build_interaction_graph

logger = logging.getLogger(__name__)


@api_view(['POST'])
def add_clause_to_contract(request, contract_id):
    """
    Add a new clause to a contract with automatic risk assessment.

    POST /api/contracts/{contract_id}/clauses/add

    Request body:
    {
        "clause_name": "Force Majeure",
        "clause_type": "force_majeure",
        "clause_text": "Neither party shall be liable...",
        "run_simulation": true  // Optional: run what-if simulation
    }

    Response:
    {
        "success": true,
        "clause_id": "uuid",
        "risk_score": 0.35,
        "risk_level": "LOW",
        "simulation": {
            "current_exposure": 1500000,
            "new_exposure": 1650000,
            "exposure_delta": 150000,
            "risk_increase_pct": 10.0
        }
    }
    """
    try:
        contract = get_object_or_404(Contract, id=contract_id)

        # Get request data
        clause_name = request.data.get('clause_name')
        clause_type = request.data.get('clause_type')
        clause_text = request.data.get('clause_text')
        run_simulation = request.data.get('run_simulation', False)

        # Validate inputs
        if not clause_name or not clause_type or not clause_text:
            return Response({
                'success': False,
                'error': 'Missing required fields: clause_name, clause_type, clause_text'
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(clause_text.strip()) < 10:
            return Response({
                'success': False,
                'error': 'Clause text is too short (minimum 10 characters)'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Initialize service
        service = ClauseAdditionService()

        # Assess risk
        assessment = service.add_clause_to_contract(
            clause_text=clause_text,
            clause_name=clause_name,
            clause_type=clause_type,
            contract_model=contract
        )

        if not assessment['success']:
            return Response({
                'success': False,
                'error': assessment.get('error', 'Failed to assess clause')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Create clause in database
        clause = Clause.objects.create(
            contract=contract,
            **assessment['clause_data']
        )

        logger.info(f"[CLAUSE-ADD] Created clause {clause.id} for contract {contract_id}")

        # Run what-if simulation if requested
        simulation_result = None
        if run_simulation:
            try:
                # Get existing clauses
                existing_clauses = Clause.objects.filter(contract=contract).exclude(id=clause.id)

                # Build graph
                graph = build_interaction_graph(existing_clauses)

                # Parse contract value
                from .services.exposure_engine import ExposureEngine
                exposure_engine = ExposureEngine()

                contract_value = 0
                if contract.contract_value and contract.contract_value not in ["Not set", "not set", ""]:
                    contract_value = exposure_engine.parse_contract_value(contract.contract_value)
                elif contract.total_liability and float(contract.total_liability) > 0:
                    contract_value = float(contract.total_liability)

                if contract_value > 0:
                    # Simulate impact
                    simulation_result = service.simulate_clause_addition_impact(
                        list(existing_clauses),
                        assessment['clause_data'],
                        graph,
                        contract_value
                    )

            except Exception as e:
                logger.error(f"[CLAUSE-ADD-SIMULATION] Error: {e}", exc_info=True)
                simulation_result = {
                    'success': False,
                    'error': str(e)
                }

        return Response({
            'success': True,
            'clause_id': clause.id,
            'clause_name': clause.clause_name,
            'clause_type': clause.clause_type,
            'risk_score': assessment['risk_score'],
            'risk_level': assessment['risk_level'],
            'risk_factors': assessment['risk_factors'],
            'simulation': simulation_result
        }, status=status.HTTP_201_CREATED)

    except Contract.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Contract {contract_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"[CLAUSE-ADD] Error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def simulate_clause_addition(request, contract_id):
    """
    Simulate adding a clause WITHOUT actually creating it.
    Useful for "preview" functionality.

    POST /api/contracts/{contract_id}/clauses/simulate-addition

    Request body:
    {
        "clause_name": "New Clause",
        "clause_type": "payment",
        "clause_text": "..."
    }

    Response:
    {
        "success": true,
        "risk_assessment": {...},
        "impact_analysis": {...}
    }
    """
    try:
        contract = get_object_or_404(Contract, id=contract_id)

        clause_name = request.data.get('clause_name')
        clause_type = request.data.get('clause_type')
        clause_text = request.data.get('clause_text')

        if not clause_name or not clause_type or not clause_text:
            return Response({
                'success': False,
                'error': 'Missing required fields'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Initialize service
        service = ClauseAdditionService()

        # Assess risk
        assessment = service.add_clause_to_contract(
            clause_text=clause_text,
            clause_name=clause_name,
            clause_type=clause_type,
            contract_model=contract
        )

        if not assessment['success']:
            return Response({
                'success': False,
                'error': assessment.get('error')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Get existing clauses and graph
        existing_clauses = Clause.objects.filter(contract=contract)
        graph = build_interaction_graph(existing_clauses)

        # Parse contract value
        from .services.exposure_engine import ExposureEngine
        exposure_engine = ExposureEngine()

        contract_value = 0
        if contract.contract_value and contract.contract_value not in ["Not set", "not set", ""]:
            contract_value = exposure_engine.parse_contract_value(contract.contract_value)
        elif contract.total_liability and float(contract.total_liability) > 0:
            contract_value = float(contract.total_liability)

        impact = None
        if contract_value > 0:
            # Simulate impact
            impact = service.simulate_clause_addition_impact(
                list(existing_clauses),
                assessment['clause_data'],
                graph,
                contract_value
            )

        return Response({
            'success': True,
            'risk_assessment': {
                'risk_score': assessment['risk_score'],
                'risk_level': assessment['risk_level'],
                'risk_factors': assessment['risk_factors']
            },
            'impact_analysis': impact
        }, status=status.HTTP_200_OK)

    except Contract.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Contract {contract_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"[CLAUSE-SIMULATE] Error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def delete_clause(request, clause_id):
    """
    Delete a clause from a contract.

    DELETE /api/clauses/{clause_id}

    Response:
    {
        "success": true,
        "message": "Clause deleted successfully"
    }
    """
    try:
        clause = get_object_or_404(Clause, id=clause_id)
        clause_name = clause.clause_name
        contract_id = clause.contract_id

        clause.delete()

        logger.info(f"[CLAUSE-DELETE] Deleted clause {clause_id} from contract {contract_id}")

        return Response({
            'success': True,
            'message': f'Clause "{clause_name}" deleted successfully'
        }, status=status.HTTP_200_OK)

    except Clause.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Clause {clause_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"[CLAUSE-DELETE] Error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def rewrite_clause_with_ai(request, clause_id):
    """
    Rewrite a clause using AI (OpenAI GPT-4 or Anthropic Claude).

    POST /api/clauses/{clause_id}/rewrite

    Request body:
    {
        "mode": "reduce_risk",  // reduce_risk, simplify, favor_client, favor_vendor, counter_proposal
        "custom_instructions": "Make it more favorable to us",  // Optional
        "provider": "openai",  // openai or anthropic (default: openai)
        "num_alternatives": 2  // Number of alternatives (1-3, default: 1)
    }

    Response:
    {
        "success": true,
        "original_text": "...",
        "mode": "reduce_risk",
        "alternatives": [
            {
                "text": "Rewritten clause...",
                "similarity_to_original": 0.75,
                "quality_score": 0.85,
                "changes": ["Added liability limitations", ...],
                "rank": 1
            }
        ],
        "best_alternative": {...}
    }
    """
    try:
        clause = get_object_or_404(Clause, id=clause_id)

        # Get request data
        mode = request.data.get('mode', 'reduce_risk')
        custom_instructions = request.data.get('custom_instructions')
        provider = request.data.get('provider', 'openai')
        num_alternatives = min(int(request.data.get('num_alternatives', 1)), 3)

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

        # Initialize rewriter
        from .services.ai_clause_rewriter import AIClauseRewriter

        rewriter = AIClauseRewriter(provider=provider)

        # Rewrite clause
        result = rewriter.rewrite_clause(
            clause_text=clause_text,
            rewrite_mode=mode,
            custom_instructions=custom_instructions,
            clause_type=clause.clause_type or clause.clause_name,
            num_alternatives=num_alternatives
        )

        if not result['success']:
            return Response({
                'success': False,
                'error': result.get('error', 'Rewrite failed')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.info(f"[CLAUSE-REWRITE] Rewrote clause {clause_id} in mode '{mode}'")

        return Response(result, status=status.HTTP_200_OK)

    except Clause.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Clause {clause_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"[CLAUSE-REWRITE] Error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def apply_clause_rewrite(request, clause_id):
    """
    Apply a rewritten version of a clause (update the clause in the database).

    POST /api/clauses/{clause_id}/apply-rewrite

    Request body:
    {
        "new_text": "The rewritten clause text...",
        "rewrite_reason": "Reduced risk by adding liability cap",
        "original_text": "Original clause text for version tracking"
    }

    Response:
    {
        "success": true,
        "clause_id": "uuid",
        "version_number": 2,
        "message": "Clause updated successfully"
    }
    """
    try:
        clause = get_object_or_404(Clause, id=clause_id)

        new_text = request.data.get('new_text')
        rewrite_reason = request.data.get('rewrite_reason', 'AI rewrite')
        original_text = request.data.get('original_text') or clause.extracted_text

        if not new_text or len(new_text.strip()) < 10:
            return Response({
                'success': False,
                'error': 'New text is required and must be at least 10 characters'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create version record
        from core.models import ClauseVersion, User

        # Get latest version number
        latest_version = ClauseVersion.objects.filter(clause=clause).order_by('-version_number').first()
        version_number = (latest_version.version_number + 1) if latest_version else 1

        # Get user from request (assume authenticated)
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None

        if user:
            ClauseVersion.objects.create(
                clause=clause,
                version_number=version_number,
                original_text=original_text or '',
                modified_text=new_text,
                change_description=rewrite_reason,
                modified_by=user
            )

        # Update clause
        clause.extracted_text = new_text
        clause.context_sentences = new_text
        clause.text_spans = new_text
        clause.save()

        logger.info(f"[CLAUSE-APPLY-REWRITE] Updated clause {clause_id} to version {version_number}")

        return Response({
            'success': True,
            'clause_id': clause_id,
            'version_number': version_number,
            'message': 'Clause updated successfully'
        }, status=status.HTTP_200_OK)

    except Clause.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Clause {clause_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"[CLAUSE-APPLY-REWRITE] Error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
