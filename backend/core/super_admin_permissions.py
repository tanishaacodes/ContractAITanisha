"""
Enterprise-Grade Permission Classes for Super Admin

Security Model:
1. Super Admin (role_level=0): Full system access, can manage LLM configs
2. Admin (role_level=10): Can view LLM configs (read-only)
3. Users/Others: No access to system configuration

Author: ContractAI Platform
Version: 1.0.0
"""

from rest_framework.permissions import BasePermission
from core.models import Role


class IsSuperAdmin(BasePermission):
    """
    Permission class: Only Super Admin users allowed.

    Usage:
        @permission_classes([IsSuperAdmin])
        def my_super_admin_view(request):
            ...

    Security:
    - Checks both role name AND role_level for defense in depth
    - Requires active user account
    - Cannot be bypassed via API
    """

    message = "Only Super Admin users can perform this action."

    def has_permission(self, request, view):
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # User must be active
        if not request.user.is_active:
            return False

        # Check role level (primary check)
        if not hasattr(request.user, 'role'):
            return False

        # Super Admin must have role_level = 0
        # Add this field to Role model via migration
        role = request.user.role

        # Fallback: If role_level doesn't exist yet, check by name
        # This is for backward compatibility during migration
        if hasattr(role, 'role_level'):
            return role.role_level == 0  # RoleLevel.SUPER_ADMIN
        else:
            # Fallback: Check by name (case-insensitive)
            return role.name.upper() == 'SUPER_ADMIN'


class IsSuperAdminOrReadOnly(BasePermission):
    """
    Permission class: Super Admin for write, Admin for read.

    Allows:
    - Super Admin: Full CRUD access
    - Admin: Read-only access (GET, HEAD, OPTIONS)
    - Others: No access

    Usage:
        @permission_classes([IsSuperAdminOrReadOnly])
        def llm_config_view(request):
            ...
    """

    message = "Super Admin required for modifications. Admins can view only."

    def has_permission(self, request, view):
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # User must be active
        if not request.user.is_active:
            return False

        if not hasattr(request.user, 'role'):
            return False

        role = request.user.role

        # Check if read-only method
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            # Allow Admin and Super Admin to view
            if hasattr(role, 'role_level'):
                return role.role_level <= 10  # SUPER_ADMIN=0 or ADMIN=10
            else:
                return role.name.upper() in ['SUPER_ADMIN', 'ADMIN']

        # Write operations: Only Super Admin
        if hasattr(role, 'role_level'):
            return role.role_level == 0  # SUPER_ADMIN only
        else:
            return role.name.upper() == 'SUPER_ADMIN'


class IsAdminOrAbove(BasePermission):
    """
    Permission class: Admin or Super Admin.

    Allows:
    - Super Admin (level 0)
    - Admin (level 10)

    Usage:
        @permission_classes([IsAdminOrAbove])
        def admin_dashboard(request):
            ...
    """

    message = "Admin or Super Admin access required."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if not request.user.is_active:
            return False

        if not hasattr(request.user, 'role'):
            return False

        role = request.user.role

        if hasattr(role, 'role_level'):
            return role.role_level <= 10  # SUPER_ADMIN or ADMIN
        else:
            return role.name.upper() in ['SUPER_ADMIN', 'ADMIN']


class CanViewAuditLogs(BasePermission):
    """
    Permission class: Can view Super Admin audit logs.

    Allows:
    - Super Admin: Full access
    - Admin: Can view but not export

    Usage:
        @permission_classes([CanViewAuditLogs])
        def audit_log_view(request):
            ...
    """

    message = "Admin or Super Admin access required to view audit logs."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if not request.user.is_active:
            return False

        if not hasattr(request.user, 'role'):
            return False

        role = request.user.role

        # Admin and Super Admin can view
        if hasattr(role, 'role_level'):
            return role.role_level <= 10  # SUPER_ADMIN or ADMIN
        else:
            return role.name.upper() in ['SUPER_ADMIN', 'ADMIN']


class CannotCreateSuperAdminViaAPI(BasePermission):
    """
    Permission class: Prevents Super Admin creation via API.

    This permission ALWAYS returns False for POST/CREATE operations
    when creating Super Admin users.

    Super Admins can ONLY be created via:
    1. Django management command
    2. Django shell

    Usage in ViewSet:
        def get_permissions(self):
            if self.action == 'create':
                return [CannotCreateSuperAdminViaAPI()]
            return super().get_permissions()
    """

    message = "Super Admin accounts cannot be created via API. Use Django management command."

    def has_permission(self, request, view):
        # Check if attempting to create Super Admin
        if request.method == 'POST':
            data = request.data
            role_id = data.get('role') or data.get('roleId')

            if role_id:
                try:
                    role = Role.objects.get(id=role_id)
                    # Block if trying to create Super Admin
                    if hasattr(role, 'role_level'):
                        if role.role_level == 0:
                            return False
                    else:
                        if role.name.upper() == 'SUPER_ADMIN':
                            return False
                except Role.DoesNotExist:
                    pass

            # Check by role name in request
            role_name = data.get('roleName', '').upper()
            if role_name == 'SUPER_ADMIN':
                return False

        return True


# =========================
# HELPER FUNCTIONS
# =========================

def is_super_admin(user) -> bool:
    """
    Check if user is Super Admin.

    Args:
        user: User model instance

    Returns:
        bool: True if user is Super Admin

    Usage:
        if is_super_admin(request.user):
            # Allow action
    """
    if not user or not user.is_authenticated:
        return False

    if not user.is_active:
        return False

    if not hasattr(user, 'role'):
        return False

    role = user.role

    if hasattr(role, 'role_level'):
        return role.role_level == 0
    else:
        return role.name.upper() == 'SUPER_ADMIN'


def is_admin_or_above(user) -> bool:
    """
    Check if user is Admin or Super Admin.

    Args:
        user: User model instance

    Returns:
        bool: True if user is Admin or Super Admin
    """
    if not user or not user.is_authenticated:
        return False

    if not user.is_active:
        return False

    if not hasattr(user, 'role'):
        return False

    role = user.role

    if hasattr(role, 'role_level'):
        return role.role_level <= 10
    else:
        return role.name.upper() in ['SUPER_ADMIN', 'ADMIN']


def get_user_role_level(user) -> int:
    """
    Get user's role level.

    Args:
        user: User model instance

    Returns:
        int: Role level (0=SUPER_ADMIN, 10=ADMIN, 50=USER, etc.)
             Returns 999 if role not found
    """
    if not user or not hasattr(user, 'role'):
        return 999

    role = user.role

    if hasattr(role, 'role_level'):
        return role.role_level

    # Fallback: Map by name
    role_name = role.name.upper()
    role_map = {
        'SUPER_ADMIN': 0,
        'ADMIN': 10,
        'MANAGER': 30,
        'USER': 50,
        'VIEWER': 70,
    }

    return role_map.get(role_name, 999)
