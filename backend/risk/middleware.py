"""
Audit logging middleware for tracking risk analysis operations
"""
import logging
import json
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from datetime import datetime

logger = logging.getLogger('audit')


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all risk-related API requests for audit trail
    """

    def process_request(self, request):
        """Store request start time"""
        request.audit_start_time = datetime.utcnow()
        return None

    def process_response(self, request, response):
        """Log the request/response for audit"""

        # Only log risk API endpoints
        if not request.path.startswith('/api/risk/'):
            return response

        # Skip health check endpoints from audit
        if '/health' in request.path:
            return response

        try:
            user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
            duration = None

            if hasattr(request, 'audit_start_time'):
                duration = (datetime.utcnow() - request.audit_start_time).total_seconds()

            # Build audit log entry
            audit_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'user': user.email if user else 'anonymous',
                'user_id': str(user.id) if user else None,
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_seconds': duration,
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
            }

            # Add request body for POST/PUT (excluding sensitive data)
            if request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    body = json.loads(request.body) if request.body else {}
                    # Remove sensitive fields
                    body.pop('password', None)
                    body.pop('token', None)
                    audit_entry['request_body'] = json.dumps(body)[:1000]  # Limit size
                except:
                    pass

            # Add response data for specific operations
            if response.status_code in [200, 201, 202]:
                try:
                    if hasattr(response, 'data'):
                        # Extract key information
                        if 'job_id' in response.data:
                            audit_entry['job_id'] = response.data['job_id']
                        if 'contract_id' in response.data:
                            audit_entry['contract_id'] = response.data['contract_id']
                except:
                    pass

            # Log to file
            logger.info(json.dumps(audit_entry))

            # Also store recent audit logs in cache for quick access
            self._store_in_cache(audit_entry)

        except Exception as e:
            logger.error(f"Audit logging error: {e}")

        return response

    def _get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _store_in_cache(self, audit_entry):
        """Store recent audit logs in Redis cache"""
        try:
            # Keep last 1000 audit entries in cache
            cache_key = 'audit_logs_recent'
            recent_logs = cache.get(cache_key, [])

            recent_logs.append(audit_entry)

            # Keep only last 1000
            if len(recent_logs) > 1000:
                recent_logs = recent_logs[-1000:]

            cache.set(cache_key, recent_logs, timeout=3600)  # 1 hour
        except Exception as e:
            logger.error(f"Error storing audit log in cache: {e}")
