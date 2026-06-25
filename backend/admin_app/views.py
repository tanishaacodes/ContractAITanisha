from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.models import User, Role
from core.serializers import UserSerializer, RoleSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users(request):
    """List all users (admin only)"""
    try:
        if request.user.role.name != 'Admin':
            return Response(
                {'message': 'Forbidden: Only admins can access this resource'},
                status=status.HTTP_403_FORBIDDEN
            )

        users = User.objects.all().order_by('-created_at')
        serializer = UserSerializer(users, many=True)
        return Response({
            'message': 'Users retrieved',
            'count': len(users),
            'users': serializer.data
        })

    except Exception as e:
        return Response(
            {'message': 'Failed to retrieve users', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user_role(request, user_id):
    """Update user role (admin only)"""
    try:
        if request.user.role.name != 'Admin':
            return Response(
                {'message': 'Forbidden: Only admins can access this resource'},
                status=status.HTTP_403_FORBIDDEN
            )

        user = User.objects.get(id=user_id)
        role_name = request.data.get('role')

        if not role_name:
            return Response(
                {'message': 'Role is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            return Response(
                {'message': 'Role not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        user.role = role
        user.save()

        return Response({
            'message': 'User role updated',
            'user': UserSerializer(user).data
        })

    except User.DoesNotExist:
        return Response(
            {'message': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'message': 'Failed to update user role', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_user_status(request, user_id):
    """Toggle user active status (admin only)"""
    try:
        if request.user.role.name != 'Admin':
            return Response(
                {'message': 'Forbidden: Only admins can access this resource'},
                status=status.HTTP_403_FORBIDDEN
            )

        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()

        return Response({
            'message': 'User status updated',
            'user': UserSerializer(user).data
        })

    except User.DoesNotExist:
        return Response(
            {'message': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'message': 'Failed to update user status', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def list_roles(request):
    """List all roles or create a new role (admin only for POST)"""
    if request.method == 'GET':
        try:
            roles = Role.objects.all().order_by('name')
            serializer = RoleSerializer(roles, many=True)
            return Response({
                'message': 'Roles retrieved',
                'count': len(roles),
                'roles': serializer.data
            })

        except Exception as e:
            return Response(
                {'message': 'Failed to retrieve roles', 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    elif request.method == 'POST':
        try:
            if request.user.role.name != 'Admin':
                return Response(
                    {'message': 'Forbidden: Only admins can create roles'},
                    status=status.HTTP_403_FORBIDDEN
                )

            data = request.data
            role_name = data.get('name')
            description = data.get('description', '')
            permissions = data.get('permissions', {})

            if not role_name:
                return Response(
                    {'message': 'Role name is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if Role.objects.filter(name=role_name).exists():
                return Response(
                    {'message': f'Role "{role_name}" already exists'},
                    status=status.HTTP_409_CONFLICT
                )

            role = Role.objects.create(
                name=role_name,
                description=description,
                permissions=permissions
            )

            serializer = RoleSerializer(role)
            return Response({
                'message': 'Role created successfully',
                'role': serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'message': 'Failed to create role', 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_role(request, role_id):
    """Delete a role (admin only)"""
    try:
        if request.user.role.name != 'Admin':
            return Response(
                {'message': 'Forbidden: Only admins can delete roles'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return Response(
                {'message': 'Role not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Prevent deletion of default roles
        default_roles = ['Admin', 'Legal Reviewer', 'Proc Reviewer', 'Viewer']
        if role.name in default_roles:
            return Response(
                {'message': f'Cannot delete default role: {role.name}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        role_name = role.name
        role.delete()

        return Response({
            'message': f'Role "{role_name}" deleted successfully'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'message': 'Failed to delete role', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    """Delete a user (admin only)"""
    try:
        if request.user.role.name != 'Admin':
            return Response(
                {'message': 'Forbidden: Only admins can delete users'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'message': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Prevent deletion of the current admin user
        if user.id == request.user.id:
            return Response(
                {'message': 'Cannot delete your own admin account'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_email = user.email
        user.delete()

        return Response({
            'message': f'User \"{user_email}\" deleted successfully'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'message': 'Failed to delete user', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
