"""
Fivetran Integration API Views.
Only users with fivetran_access permission (or SuperAdmin) can access these endpoints.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import require_fivetran_access
from .fivetran_service import FivetranService
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_fivetran_access
def fivetran_status(request):
    """
    Get Fivetran connector status.
    GET /api/integrations/fivetran/status/

    Requires: fivetran_access permission or SuperAdmin role
    """
    try:
        fivetran = FivetranService()
        status_data = fivetran.get_connection_status()
        connectors = fivetran.get_connectors()

        return Response({
            'status': status_data.get('status'),
            'lastSync': status_data.get('lastSync'),
            'totalConnectors': status_data.get('totalConnectors', len(connectors)),
            'activeConnectors': status_data.get('activeConnectors', 0),
            'message': status_data.get('message'),
            'connectors': connectors[:3]  # Return first 3 for summary
        })
    except Exception as e:
        logger.error(f"Failed to get Fivetran status: {str(e)}")
        return Response({
            'error': 'Failed to fetch Fivetran status',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_fivetran_access
def fivetran_sync(request):
    """
    Trigger manual Fivetran sync.
    POST /api/integrations/fivetran/sync/

    Requires: fivetran_access permission or SuperAdmin role

    Body:
    {
        "connectorId": "docusign_connector"
    }
    """
    connector_id = request.data.get('connectorId')

    if not connector_id:
        return Response({
            'error': 'connectorId is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        fivetran = FivetranService()
        result = fivetran.trigger_sync(connector_id)

        if result.get('success'):
            return Response({
                'message': result.get('message', f'Sync triggered for connector: {connector_id}'),
                'status': 'pending',
                'estimatedCompletionTime': '2-5 minutes'
            })
        else:
            return Response({
                'error': 'Failed to trigger sync',
                'details': result.get('message')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        logger.error(f"Failed to trigger sync: {str(e)}")
        return Response({
            'error': 'Failed to trigger sync',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_fivetran_access
def fivetran_connectors(request):
    """
    List all available Fivetran connectors.
    GET /api/integrations/fivetran/connectors/

    Requires: fivetran_access permission or SuperAdmin role
    """
    try:
        fivetran = FivetranService()
        connectors = fivetran.get_connectors()

        return Response({
            'connectors': connectors,
            'total': len(connectors)
        })

    except Exception as e:
        logger.error(f"Failed to fetch connectors: {str(e)}")
        return Response({
            'error': 'Failed to fetch connectors',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_fivetran_access
def fivetran_webhook(request):
    """
    Webhook endpoint for Fivetran to notify sync completion.
    POST /api/integrations/fivetran/webhook/

    Requires: fivetran_access permission or SuperAdmin role

    This endpoint receives notifications from Fivetran when a sync completes.
    """
    import json

    try:
        payload = json.loads(request.body) if isinstance(request.body, bytes) else request.data

        if payload.get('event') == 'sync_success':
            schema = payload.get('schema')
            connector_id = payload.get('connector_id')

            # Trigger downstream processing
            from .tasks import process_fivetran_sync
            task_result = process_fivetran_sync.delay(schema, connector_id)

            logger.info(f"Triggered Fivetran processing task {task_result.id} for schema: {schema}")

            return Response({
                'status': 'ok',
                'message': f'Webhook received and processing started for schema: {schema}',
                'task_id': task_result.id
            })

        return Response({
            'status': 'ok',
            'message': 'Webhook received'
        })

    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
