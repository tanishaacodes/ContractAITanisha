"""
SuperAdmin API Views for User Management and Connector Permissions.
Only SuperAdmin users can access these endpoints.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.models import User, Role
from core.serializers import (
    UserCreateSerializer,
    UserManagementSerializer,
    UserUpdateSerializer,
    RoleSerializer
)
from core.permissions import require_superadmin


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_superadmin
def list_users(request):
    """
    List all users in the system (SuperAdmin only).
    GET /api/superadmin/users/
    """
    users = User.objects.all().select_related('role').order_by('-created_at')

    # Optional filters
    role_name = request.query_params.get('role')
    fivetran_access = request.query_params.get('fivetranAccess')
    kafka_access = request.query_params.get('kafkaAccess')
    is_active = request.query_params.get('isActive')

    if role_name:
        users = users.filter(role__name=role_name)
    if fivetran_access is not None:
        users = users.filter(fivetran_access=fivetran_access.lower() == 'true')
    if kafka_access is not None:
        users = users.filter(kafka_access=kafka_access.lower() == 'true')
    if is_active is not None:
        users = users.filter(is_active=is_active.lower() == 'true')

    serializer = UserManagementSerializer(users, many=True)
    return Response({'users': serializer.data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_superadmin
def create_user(request):
    """
    Create a new user with connector permissions (SuperAdmin only).
    POST /api/superadmin/users/

    Body:
    {
        "email": "user@example.com",
        "password": "password123",
        "firstName": "John",
        "lastName": "Doe",
        "roleId": "role-uuid",
        "fivetranAccess": true,
        "kafkaAccess": false
    }
    """
    serializer = UserCreateSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()
        response_serializer = UserManagementSerializer(user)
        return Response({
            'message': 'User created successfully',
            'user': response_serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response({
        'error': 'Validation failed',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_superadmin
def get_user(request, user_id):
    """
    Get specific user details (SuperAdmin only).
    GET /api/superadmin/users/<user_id>/
    """
    try:
        user = User.objects.select_related('role').get(id=user_id)
        serializer = UserManagementSerializer(user)
        return Response({'user': serializer.data})
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@require_superadmin
def update_user(request, user_id):
    """
    Update user connector permissions and details (SuperAdmin only).
    PUT/PATCH /api/superadmin/users/<user_id>/

    Body:
    {
        "firstName": "John",
        "lastName": "Doe",
        "roleId": "role-uuid",
        "fivetranAccess": true,
        "kafkaAccess": true,
        "isActive": true
    }
    """
    try:
        user = User.objects.get(id=user_id)

        # Prevent self-deactivation
        if user.id == request.user.id and 'isActive' in request.data:
            if not request.data.get('isActive'):
                return Response({
                    'error': 'You cannot deactivate your own account'
                }, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserUpdateSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            updated_user = serializer.save()
            response_serializer = UserManagementSerializer(updated_user)
            return Response({
                'message': 'User updated successfully',
                'user': response_serializer.data
            })

        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@require_superadmin
def delete_user(request, user_id):
    """
    Delete a user (SuperAdmin only).
    DELETE /api/superadmin/users/<user_id>/
    """
    try:
        user = User.objects.get(id=user_id)

        # Prevent self-deletion
        if user.id == request.user.id:
            return Response({
                'error': 'You cannot delete your own account'
            }, status=status.HTTP_400_BAD_REQUEST)

        user.delete()
        return Response({
            'message': 'User deleted successfully'
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_superadmin
def toggle_user_status(request, user_id):
    """
    Toggle user active/inactive status (SuperAdmin only).
    POST /api/superadmin/users/<user_id>/toggle-status/
    """
    try:
        user = User.objects.get(id=user_id)

        # Prevent self-deactivation
        if user.id == request.user.id:
            return Response({
                'error': 'You cannot deactivate your own account'
            }, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = not user.is_active
        user.save()

        serializer = UserManagementSerializer(user)
        return Response({
            'message': f'User {"activated" if user.is_active else "deactivated"} successfully',
            'user': serializer.data
        })

    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_superadmin
def update_connector_permissions(request, user_id):
    """
    Update user's connector permissions only (SuperAdmin only).
    POST /api/superadmin/users/<user_id>/connector-permissions/

    Body:
    {
        "fivetranAccess": true,
        "kafkaAccess": false
    }
    """
    try:
        user = User.objects.get(id=user_id)

        fivetran_access = request.data.get('fivetranAccess')
        kafka_access = request.data.get('kafkaAccess')

        if fivetran_access is not None:
            user.fivetran_access = fivetran_access
        if kafka_access is not None:
            user.kafka_access = kafka_access

        user.save()

        serializer = UserManagementSerializer(user)
        return Response({
            'message': 'Connector permissions updated successfully',
            'user': serializer.data
        })

    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_superadmin
def list_roles(request):
    """
    List all available roles (SuperAdmin only).
    GET /api/superadmin/roles/
    """
    roles = Role.objects.all().order_by('name')
    serializer = RoleSerializer(roles, many=True)
    return Response({'roles': serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_superadmin
def get_user_stats(request):
    """
    Get user statistics dashboard data (SuperAdmin only).
    GET /api/superadmin/stats/
    """
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()

    fivetran_users = User.objects.filter(fivetran_access=True).count()
    kafka_users = User.objects.filter(kafka_access=True).count()

    # Users by role
    users_by_role = {}
    roles = Role.objects.all()
    for role in roles:
        users_by_role[role.name] = User.objects.filter(role=role).count()

    return Response({
        'stats': {
            'totalUsers': total_users,
            'activeUsers': active_users,
            'inactiveUsers': inactive_users,
            'fivetranUsers': fivetran_users,
            'kafkaUsers': kafka_users,
            'usersByRole': users_by_role
        }
    })
