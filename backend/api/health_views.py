"""
Health check endpoints for microservices monitoring.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Main health check endpoint.
    GET /health/

    Returns 200 if service is healthy, 503 if unhealthy.
    """
    health_status = {
        'status': 'healthy',
        'service': 'contractai-backend',
        'checks': {}
    }

    all_healthy = True

    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
        all_healthy = False

    # Check Redis/Cache
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status['checks']['cache'] = 'healthy'
        else:
            health_status['checks']['cache'] = 'unhealthy: cache read failed'
            all_healthy = False
    except Exception as e:
        health_status['checks']['cache'] = f'unhealthy: {str(e)}'
        all_healthy = False

    # Check Kafka (optional - don't fail if Kafka is down)
    try:
        from integrations.kafka.producer import get_producer
        producer = get_producer()
        health_status['checks']['kafka'] = 'healthy'
    except Exception as e:
        health_status['checks']['kafka'] = f'degraded: {str(e)}'
        # Don't mark as unhealthy - Kafka is optional

    if not all_healthy:
        health_status['status'] = 'unhealthy'
        return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return Response(health_status, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness check - is the service ready to accept traffic?
    GET /health/ready/
    """
    try:
        # Check if we can connect to database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return Response({
            'status': 'ready',
            'service': 'contractai-backend'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'status': 'not_ready',
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_check(request):
    """
    Liveness check - is the service alive?
    GET /health/live/
    """
    return Response({
        'status': 'alive',
        'service': 'contractai-backend'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def startup_check(request):
    """
    Startup check - has the service completed startup?
    GET /health/startup/
    """
    checks = {}

    # Check database migrations
    try:
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            checks['migrations'] = 'pending'
            startup_complete = False
        else:
            checks['migrations'] = 'complete'
            startup_complete = True
    except Exception as e:
        checks['migrations'] = f'error: {str(e)}'
        startup_complete = False

    if startup_complete:
        return Response({
            'status': 'started',
            'checks': checks
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'status': 'starting',
            'checks': checks
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
