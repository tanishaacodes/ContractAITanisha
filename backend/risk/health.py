"""
Health check views for monitoring system status
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
def health_check(request):
    """
    Basic health check endpoint
    GET /api/risk/health
    """
    return Response({
        "status": "healthy",
        "service": "risk-analysis",
        "version": "2.0.0"
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def health_check_detailed(request):
    """
    Detailed health check with dependency status
    GET /api/risk/health/detailed
    """
    health_status = {
        "status": "healthy",
        "timestamp": None,
        "services": {}
    }

    # Check MySQL database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status["services"]["mysql"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["mysql"] = {
            "status": "unhealthy",
            "message": str(e)
        }
        logger.error(f"MySQL health check failed: {e}")

    # Check Redis cache
    try:
        cache.set('health_check', 'ok', timeout=10)
        value = cache.get('health_check')
        if value == 'ok':
            health_status["services"]["redis"] = {
                "status": "healthy",
                "message": "Cache connection successful"
            }
        else:
            raise Exception("Cache value mismatch")
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "message": str(e)
        }
        logger.error(f"Redis health check failed: {e}")

    # Check Neo4j
    try:
        from .services.neo4j import get_neo4j_service
        neo4j_service = get_neo4j_service()

        # Simple connectivity test
        result = neo4j_service.execute_query("RETURN 1 AS test")
        if result:
            health_status["services"]["neo4j"] = {
                "status": "healthy",
                "message": "Graph database connection successful"
            }
        else:
            raise Exception("No response from Neo4j")
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["neo4j"] = {
            "status": "unhealthy",
            "message": str(e)
        }
        logger.error(f"Neo4j health check failed: {e}")

    # Check Qdrant
    try:
        from .services.qdrant_service import QdrantService
        qdrant = QdrantService()

        # Try to get collection info
        collections = qdrant.client.get_collections()
        health_status["services"]["qdrant"] = {
            "status": "healthy",
            "message": f"Vector database connected, {len(collections.collections)} collections"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["qdrant"] = {
            "status": "unhealthy",
            "message": str(e)
        }
        logger.error(f"Qdrant health check failed: {e}")

    # Check Celery
    try:
        from celery.app.control import Control
        from contractai.celery import app as celery_app

        control = Control(celery_app)
        stats = control.inspect().stats()

        if stats:
            worker_count = len(stats.keys())
            health_status["services"]["celery"] = {
                "status": "healthy",
                "message": f"{worker_count} worker(s) active"
            }
        else:
            raise Exception("No Celery workers responding")
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["celery"] = {
            "status": "unhealthy",
            "message": str(e)
        }
        logger.error(f"Celery health check failed: {e}")

    # Determine overall HTTP status
    http_status = status.HTTP_200_OK
    if health_status["status"] == "degraded":
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    elif health_status["status"] == "unhealthy":
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    from datetime import datetime
    health_status["timestamp"] = datetime.utcnow().isoformat()

    return Response(health_status, status=http_status)


@api_view(['GET'])
def readiness_check(request):
    """
    Kubernetes-style readiness probe
    GET /api/risk/health/ready
    """
    try:
        # Quick database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return Response({
            "ready": True
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return Response({
            "ready": False,
            "error": str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
def liveness_check(request):
    """
    Kubernetes-style liveness probe
    GET /api/risk/health/live
    """
    return Response({
        "alive": True
    }, status=status.HTTP_200_OK)
