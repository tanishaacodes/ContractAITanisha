"""
Audit log API endpoints
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_audit_logs(request):
    """
    Get recent audit logs (admin only)
    GET /api/risk/audit/logs
    Query params:
        - limit: number of logs to return (default 100, max 1000)
        - user: filter by user email
        - method: filter by HTTP method
    """
    try:
        limit = min(int(request.query_params.get('limit', 100)), 1000)
        user_filter = request.query_params.get('user')
        method_filter = request.query_params.get('method')

        # Get from cache
        recent_logs = cache.get('audit_logs_recent', [])

        # Apply filters
        filtered_logs = recent_logs

        if user_filter:
            filtered_logs = [log for log in filtered_logs if log.get('user') == user_filter]

        if method_filter:
            filtered_logs = [log for log in filtered_logs if log.get('method') == method_filter]

        # Apply limit
        filtered_logs = filtered_logs[-limit:]

        # Reverse to show most recent first
        filtered_logs.reverse()

        return Response({
            "success": True,
            "data": {
                "logs": filtered_logs,
                "total": len(filtered_logs),
                "source": "cache"
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error retrieving audit logs: {e}")
        return Response({
            "success": False,
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_audit_stats(request):
    """
    Get audit statistics
    GET /api/risk/audit/stats
    """
    try:
        recent_logs = cache.get('audit_logs_recent', [])

        # Calculate stats
        total_requests = len(recent_logs)

        users = set(log.get('user') for log in recent_logs if log.get('user'))
        unique_users = len(users)

        methods = {}
        status_codes = {}
        endpoints = {}

        for log in recent_logs:
            # Count methods
            method = log.get('method', 'UNKNOWN')
            methods[method] = methods.get(method, 0) + 1

            # Count status codes
            code = log.get('status_code', 0)
            status_codes[str(code)] = status_codes.get(str(code), 0) + 1

            # Count endpoints
            path = log.get('path', 'UNKNOWN')
            endpoints[path] = endpoints.get(path, 0) + 1

        # Get top endpoints
        top_endpoints = sorted(endpoints.items(), key=lambda x: x[1], reverse=True)[:10]

        # Calculate average duration
        durations = [log.get('duration_seconds', 0) for log in recent_logs if log.get('duration_seconds')]
        avg_duration = sum(durations) / len(durations) if durations else 0

        stats = {
            "total_requests": total_requests,
            "unique_users": unique_users,
            "methods": methods,
            "status_codes": status_codes,
            "top_endpoints": [{"path": path, "count": count} for path, count in top_endpoints],
            "average_duration_seconds": round(avg_duration, 3),
            "time_window": "Last 1 hour (cached)"
        }

        return Response({
            "success": True,
            "data": stats
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error calculating audit stats: {e}")
        return Response({
            "success": False,
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def clear_audit_cache(request):
    """
    Clear cached audit logs (admin only)
    POST /api/risk/audit/clear
    """
    try:
        cache.delete('audit_logs_recent')

        return Response({
            "success": True,
            "message": "Audit log cache cleared"
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error clearing audit cache: {e}")
        return Response({
            "success": False,
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
