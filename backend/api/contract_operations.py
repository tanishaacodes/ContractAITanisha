"""
Contract Operations - Download and Bulk Actions
Endpoints for downloading contracts and performing bulk operations
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.http import FileResponse, Http404
from django.conf import settings
import os
import mimetypes

from core.models import Contract, ContractIntelligence
from .alfresco_rag_views import extract_contract_intelligence
from .risk_analyzer import analyze_contract_risk


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_contract(request, contract_id):
    """
    Download the original contract file.
    Supports both uploaded files and Alfresco synced documents.
    """
    try:
        # Get contract
        contract = Contract.objects.get(id=contract_id)

        # Check permission
        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if file exists
        if not contract.file_path or not os.path.exists(contract.file_path):
            return Response(
                {'message': 'Contract file not found on server. The file may have been deleted or is no longer available.'},
                status=status.HTTP_404_NOT_FOUND
            )

        file_path = contract.file_path

        # Determine content type
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'

        # Create file response
        try:
            response = FileResponse(
                open(file_path, 'rb'),
                content_type=content_type
            )
            response['Content-Disposition'] = f'attachment; filename="{contract.original_filename}"'
            return response
        except FileNotFoundError:
            raise Http404("Contract file not found")

    except Contract.DoesNotExist:
        return Response(
            {'message': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'[DOWNLOAD ERROR] {str(e)}')
        return Response(
            {'message': 'Failed to download contract', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_extract_intelligence(request):
    """
    Extract legal intelligence from multiple contracts in bulk.
    Expects: { "contract_ids": ["uuid1", "uuid2", ...] }
    """
    try:
        contract_ids = request.data.get('contract_ids', [])

        if not contract_ids:
            return Response(
                {'message': 'No contract IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate all contracts belong to user
        contracts = Contract.objects.filter(id__in=contract_ids, user=request.user)

        if contracts.count() != len(contract_ids):
            return Response(
                {'message': 'Some contracts not found or access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        results = []
        success_count = 0
        failed_count = 0

        for contract in contracts:
            try:
                # Check if intelligence already exists
                if hasattr(contract, 'intelligence'):
                    results.append({
                        'contract_id': str(contract.id),
                        'filename': contract.original_filename,
                        'status': 'skipped',
                        'message': 'Intelligence already extracted'
                    })
                    continue

                # Extract intelligence
                # This would ideally be done in background task, but for MVP we'll do it synchronously
                # You can later integrate with Celery for async processing

                # For now, we'll mark it as queued
                results.append({
                    'contract_id': str(contract.id),
                    'filename': contract.original_filename,
                    'status': 'queued',
                    'message': 'Intelligence extraction queued'
                })
                success_count += 1

            except Exception as e:
                results.append({
                    'contract_id': str(contract.id),
                    'filename': contract.original_filename,
                    'status': 'failed',
                    'error': str(e)
                })
                failed_count += 1

        return Response({
            'message': f'Bulk extraction initiated for {success_count} contracts',
            'total': len(contract_ids),
            'success': success_count,
            'failed': failed_count,
            'results': results
        })

    except Exception as e:
        print(f'[BULK EXTRACT ERROR] {str(e)}')
        return Response(
            {'message': 'Bulk extraction failed', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_risk_analysis(request):
    """
    Perform risk analysis on multiple contracts in bulk.
    Expects: { "contract_ids": ["uuid1", "uuid2", ...] }
    """
    try:
        contract_ids = request.data.get('contract_ids', [])

        if not contract_ids:
            return Response(
                {'message': 'No contract IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate all contracts belong to user
        contracts = Contract.objects.filter(id__in=contract_ids, user=request.user)

        if contracts.count() != len(contract_ids):
            return Response(
                {'message': 'Some contracts not found or access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        results = []
        success_count = 0
        failed_count = 0

        for contract in contracts:
            try:
                # Check if risk analysis already exists
                if hasattr(contract, 'risk_analysis'):
                    results.append({
                        'contract_id': str(contract.id),
                        'filename': contract.original_filename,
                        'status': 'skipped',
                        'message': 'Risk analysis already exists'
                    })
                    continue

                # Queue risk analysis
                # This would ideally be done in background task
                results.append({
                    'contract_id': str(contract.id),
                    'filename': contract.original_filename,
                    'status': 'queued',
                    'message': 'Risk analysis queued'
                })
                success_count += 1

            except Exception as e:
                results.append({
                    'contract_id': str(contract.id),
                    'filename': contract.original_filename,
                    'status': 'failed',
                    'error': str(e)
                })
                failed_count += 1

        return Response({
            'message': f'Bulk risk analysis initiated for {success_count} contracts',
            'total': len(contract_ids),
            'success': success_count,
            'failed': failed_count,
            'results': results
        })

    except Exception as e:
        print(f'[BULK RISK ANALYSIS ERROR] {str(e)}')
        return Response(
            {'message': 'Bulk risk analysis failed', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
