"""
Obligation Extraction API Views
================================
RESTful API endpoints for extracting and managing contract obligations.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.models import Contract, Clause, ContractObligation
from .services.obligation_extractor import ObligationExtractor

logger = logging.getLogger(__name__)


@api_view(['POST'])
def extract_obligations_from_contract(request, contract_id):
    """
    Extract obligations from all clauses in a contract.

    POST /api/contracts/{contract_id}/obligations/extract/

    Request body:
    {
        "reextract": false  // Optional: re-extract even if obligations exist
    }

    Response:
    {
        "success": true,
        "contract_id": "uuid",
        "obligations_extracted": 15,
        "obligations": [...]
    }
    """
    try:
        contract = get_object_or_404(Contract, id=contract_id)
        reextract = request.data.get('reextract', False)

        # Check if obligations already exist
        existing_count = ContractObligation.objects.filter(contract=contract).count()
        if existing_count > 0 and not reextract:
            return Response({
                'success': False,
                'error': f'Contract already has {existing_count} obligations. Use reextract=true to re-process.',
                'existing_obligations': existing_count
            }, status=status.HTTP_400_BAD_REQUEST)

        # Delete existing if re-extracting
        if reextract:
            deleted_count = ContractObligation.objects.filter(contract=contract).delete()[0]
            logger.info(f"[OBLIGATION-EXTRACT] Deleted {deleted_count} existing obligations for contract {contract_id}")

        # Extract obligations from all clauses
        extractor = ObligationExtractor()
        clauses = Clause.objects.filter(contract=contract)

        obligations_created = []
        total_extracted = 0

        for clause in clauses:
            # Get clause text
            clause_text = (
                clause.extracted_text or
                clause.context_sentences or
                clause.text_spans or
                ''
            )

            if not clause_text or len(clause_text.strip()) < 10:
                continue

            # Extract obligations
            extracted = extractor.extract_obligations(
                clause_text,
                clause_type=clause.clause_type or clause.clause_name
            )

            # Create database records
            for obligation_data in extracted:
                try:
                    obligation = ContractObligation.objects.create(
                        contract=contract,
                        title=obligation_data['title'],
                        description=obligation_data['description'],
                        full_text=obligation_data.get('full_text', ''),
                        category=obligation_data['category'],
                        responsible_party=obligation_data['responsible_party'],
                        priority=obligation_data['priority'],
                        due_date_text=obligation_data.get('due_date_text'),
                        clause_reference=f"{clause.clause_name}",
                        is_completed=False
                    )

                    obligations_created.append({
                        'id': obligation.id,
                        'title': obligation.title,
                        'category': obligation.category,
                        'priority': obligation.priority,
                        'responsible_party': obligation.responsible_party,
                        'confidence': obligation_data.get('confidence', 0.5)
                    })

                    total_extracted += 1

                except Exception as e:
                    logger.error(f"[OBLIGATION-EXTRACT] Failed to create obligation: {e}")
                    continue

        logger.info(f"[OBLIGATION-EXTRACT] Extracted {total_extracted} obligations from contract {contract_id}")

        return Response({
            'success': True,
            'contract_id': contract_id,
            'obligations_extracted': total_extracted,
            'clauses_processed': clauses.count(),
            'obligations': obligations_created
        }, status=status.HTTP_201_CREATED)

    except Contract.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Contract {contract_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"[OBLIGATION-EXTRACT] Error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def extract_obligations_from_clause(request, clause_id):
    """
    Extract obligations from a specific clause.

    POST /api/clauses/{clause_id}/obligations/extract/

    Response:
    {
        "success": true,
        "clause_id": "uuid",
        "obligations_extracted": 3,
        "obligations": [...]
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

        # Extract obligations
        extractor = ObligationExtractor()
        extracted = extractor.extract_obligations(
            clause_text,
            clause_type=clause.clause_type or clause.clause_name
        )

        # Create database records
        obligations_created = []
        for obligation_data in extracted:
            try:
                obligation = ContractObligation.objects.create(
                    contract=clause.contract,
                    title=obligation_data['title'],
                    description=obligation_data['description'],
                    full_text=obligation_data.get('full_text', ''),
                    category=obligation_data['category'],
                    responsible_party=obligation_data['responsible_party'],
                    priority=obligation_data['priority'],
                    due_date_text=obligation_data.get('due_date_text'),
                    clause_reference=f"{clause.clause_name}",
                    is_completed=False
                )

                obligations_created.append({
                    'id': obligation.id,
                    'title': obligation.title,
                    'category': obligation.category,
                    'priority': obligation.priority,
                    'responsible_party': obligation.responsible_party,
                    'confidence': obligation_data.get('confidence', 0.5)
                })

            except Exception as e:
                logger.error(f"[OBLIGATION-EXTRACT] Failed to create obligation: {e}")
                continue

        logger.info(f"[OBLIGATION-EXTRACT] Extracted {len(obligations_created)} obligations from clause {clause_id}")

        return Response({
            'success': True,
            'clause_id': clause_id,
            'obligations_extracted': len(obligations_created),
            'obligations': obligations_created
        }, status=status.HTTP_201_CREATED)

    except Clause.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Clause {clause_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"[OBLIGATION-EXTRACT] Error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def list_contract_obligations(request, contract_id):
    """
    List all obligations for a contract.

    GET /api/contracts/{contract_id}/obligations/

    Query params:
    - category: Filter by category (PAYMENT, DELIVERY, etc.)
    - priority: Filter by priority (HIGH, MEDIUM, LOW)
    - responsible_party: Filter by party
    - is_completed: Filter by completion status

    Response:
    {
        "success": true,
        "contract_id": "uuid",
        "total_obligations": 15,
        "obligations": [...]
    }
    """
    try:
        contract = get_object_or_404(Contract, id=contract_id)

        # Get query parameters
        category = request.query_params.get('category')
        priority = request.query_params.get('priority')
        responsible_party = request.query_params.get('responsible_party')
        is_completed = request.query_params.get('is_completed')

        # Build query
        obligations = ContractObligation.objects.filter(contract=contract)

        if category:
            obligations = obligations.filter(category=category.upper())
        if priority:
            obligations = obligations.filter(priority=priority.upper())
        if responsible_party:
            obligations = obligations.filter(responsible_party=responsible_party.upper())
        if is_completed is not None:
            obligations = obligations.filter(is_completed=is_completed.lower() == 'true')

        # Serialize
        obligations_data = []
        for obligation in obligations:
            obligations_data.append({
                'id': obligation.id,
                'title': obligation.title,
                'description': obligation.description,
                'category': obligation.category,
                'responsible_party': obligation.responsible_party,
                'priority': obligation.priority,
                'due_date_text': obligation.due_date_text,
                'clause_reference': obligation.clause_reference,
                'is_completed': obligation.is_completed,
                'completed_at': obligation.completed_at.isoformat() if obligation.completed_at else None,
                'created_at': obligation.created_at.isoformat()
            })

        return Response({
            'success': True,
            'contract_id': contract_id,
            'total_obligations': len(obligations_data),
            'obligations': obligations_data
        }, status=status.HTTP_200_OK)

    except Contract.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Contract {contract_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"[OBLIGATION-LIST] Error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
def mark_obligation_complete(request, obligation_id):
    """
    Mark an obligation as completed.

    PUT /api/obligations/{obligation_id}/complete/

    Request body:
    {
        "completion_notes": "Optional notes"
    }
    """
    try:
        obligation = get_object_or_404(ContractObligation, id=obligation_id)

        obligation.is_completed = True
        obligation.completed_at = timezone.now()
        obligation.completion_notes = request.data.get('completion_notes', '')
        obligation.save()

        return Response({
            'success': True,
            'obligation_id': obligation_id,
            'completed_at': obligation.completed_at.isoformat()
        }, status=status.HTTP_200_OK)

    except ContractObligation.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Obligation {obligation_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"[OBLIGATION-COMPLETE] Error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
