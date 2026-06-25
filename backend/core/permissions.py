"""
Permission decorators and classes for role-based access control.
Only SuperAdmin users can manage users and assign connector permissions.
"""
from functools import wraps
from rest_framework import status
from rest_framework.response import Response


def require_superadmin(view_func):
    """
    Decorator to require SuperAdmin role for a view.
    Returns 403 Forbidden if user is not a SuperAdmin.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated
        if not hasattr(request, 'user') or not request.user:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Check if user has SuperAdmin role
        if request.user.role.name != 'SuperAdmin':
            return Response(
                {'error': 'Forbidden: Only SuperAdmin can perform this action'},
                status=status.HTTP_403_FORBIDDEN
            )

        return view_func(request, *args, **kwargs)

    return wrapper


def require_fivetran_access(view_func):
    """
    Decorator to require Fivetran access permission.
    Returns 403 Forbidden if user doesn't have fivetran_access.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated
        if not hasattr(request, 'user') or not request.user:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # SuperAdmin always has access
        if request.user.role.name == 'SuperAdmin':
            return view_func(request, *args, **kwargs)

        # Check if user has Fivetran access
        if not request.user.fivetran_access:
            return Response(
                {'error': 'Forbidden: You do not have Fivetran connector access'},
                status=status.HTTP_403_FORBIDDEN
            )

        return view_func(request, *args, **kwargs)

    return wrapper


def require_kafka_access(view_func):
    """
    Decorator to require Kafka access permission.
    Returns 403 Forbidden if user doesn't have kafka_access.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated
        if not hasattr(request, 'user') or not request.user:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # SuperAdmin always has access
        if request.user.role.name == 'SuperAdmin':
            return view_func(request, *args, **kwargs)

        # Check if user has Kafka access
        if not request.user.kafka_access:
            return Response(
                {'error': 'Forbidden: You do not have Kafka connector access'},
                status=status.HTTP_403_FORBIDDEN
            )

        return view_func(request, *args, **kwargs)

    return wrapper


class IsSuperAdmin:
    """
    DRF Permission class to check if user is a SuperAdmin.
    Usage: permission_classes = [IsSuperAdmin]
    """

    def has_permission(self, request, view):
        return (
            request.user
            and hasattr(request.user, 'role')
            and request.user.role.name == 'SuperAdmin'
        )


class HasFivetranAccess:
    """
    DRF Permission class to check if user has Fivetran access.
    Usage: permission_classes = [HasFivetranAccess]
    """

    def has_permission(self, request, view):
        # SuperAdmin always has access
        if request.user and hasattr(request.user, 'role') and request.user.role.name == 'SuperAdmin':
            return True

        # Check fivetran_access flag
        return request.user and hasattr(request.user, 'fivetran_access') and request.user.fivetran_access


class HasKafkaAccess:
    """
    DRF Permission class to check if user has Kafka access.
    Usage: permission_classes = [HasKafkaAccess]
    """

    def has_permission(self, request, view):
        # SuperAdmin always has access
        if request.user and hasattr(request.user, 'role') and request.user.role.name == 'SuperAdmin':
            return True

        # Check kafka_access flag
        return request.user and hasattr(request.user, 'kafka_access') and request.user.kafka_access


# ===== PrimeContractAI RBAC Extensions =====

class UserRole:
    """User roles for PrimeContractAI"""
    ADMIN = 'admin'
    EXECUTIVE = 'executive'
    ANALYST = 'analyst'
    VIEWER = 'viewer'

    CHOICES = [
        (ADMIN, 'Administrator'),
        (EXECUTIVE, 'Executive'),
        (ANALYST, 'Analyst'),
        (VIEWER, 'Viewer'),
    ]


# Permission matrix
PRIME_PERMISSIONS = {
    UserRole.ADMIN: {
        'view_prime_dashboard': True,
        'use_ai_features': True,
        'view_profitability': True,
        'run_simulations': True,
        'export_reports': True,
        'manage_contracts': True,
    },
    UserRole.EXECUTIVE: {
        'view_prime_dashboard': True,
        'use_ai_features': True,
        'view_profitability': True,
        'run_simulations': True,
        'export_reports': True,
        'manage_contracts': False,
    },
    UserRole.ANALYST: {
        'view_prime_dashboard': True,
        'use_ai_features': True,
        'view_profitability': True,
        'run_simulations': True,
        'export_reports': True,
        'manage_contracts': True,
    },
    UserRole.VIEWER: {
        'view_prime_dashboard': True,
        'use_ai_features': False,
        'view_profitability': False,
        'run_simulations': False,
        'export_reports': False,
        'manage_contracts': False,
    },
}


def has_prime_permission(user, permission_name):
    """Check if user has Prime dashboard permission"""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    user_role = getattr(user, 'role', UserRole.VIEWER)
    return PRIME_PERMISSIONS.get(user_role, {}).get(permission_name, False)


def require_prime_permission(permission_name):
    """Decorator for Prime permission checks"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not has_prime_permission(request.user, permission_name):
                return Response(
                    {'error': 'Permission denied', 'detail': f'Requires {permission_name}'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
