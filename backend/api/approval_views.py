"""
Role-Based Approval API Views

Provides REST API endpoints for:
- Viewing pending approvals
- Approving/rejecting tasks
- Viewing approval history
- Contract approval timeline
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q

from core.models import Contract, ApprovalTask, ApprovalAudit, User
from api.approval_service import (
    initiate_approval_workflow,
    approve_task,
    reject_task,
    get_pending_approvals_for_user,
    get_contract_approval_status,
    user_can_approve
)
from core.authentication import JWTAuthentication


# Custom permission decorator
def jwt_authenticated(view_func):
    """Decorator to apply JWT authentication"""
    def wrapped_view(request, *args, **kwargs):
        auth = JWTAuthentication()
        try:
            user, _ = auth.authenticate(request)
            if not user:
                return Response(
                    {'message': 'Authentication required'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            request.user = user
            return view_func(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {'message': 'Invalid token', 'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
    return wrapped_view


# =========================
# APPROVAL TASK ENDPOINTS
# =========================

@api_view(['POST'])
@jwt_authenticated
def initiate_workflow(request, contract_id):
    """
    Initiate approval workflow for a contract in DRAFT status.

    POST /api/approvals/contracts/{contract_id}/initiate
    """
    try:
        contract = get_object_or_404(Contract, id=contract_id)

        # Check if user owns the contract or is admin
        if contract.user != request.user and request.user.role.name.upper() != 'ADMIN':
            return Response(
                {'message': 'You do not have permission to initiate workflow for this contract'},
                status=status.HTTP_403_FORBIDDEN
            )

        success, message = initiate_approval_workflow(contract)

        if success:
            return Response({
                'message': message,
                'contract_status': contract.status
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response(
            {'message': 'Failed to initiate workflow', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_authenticated
def get_approval_inbox(request):
    """
    Get all pending approval tasks for the current user.

    GET /api/approvals/inbox
    """
    try:
        tasks = get_pending_approvals_for_user(request.user)

        tasks_data = []
        for task in tasks:
            tasks_data.append({
                'id': task.id,
                'contract_id': task.contract.id,
                'contract_name': task.contract.original_filename,
                'contract_type': task.contract.contract_type,
                'role_required': task.role_required,
                'workflow_stage': task.workflow_stage,
                'status': task.status,
                'created_at': task.created_at.isoformat(),
                'contract_owner': {
                    'email': task.contract.user.email,
                    'name': f"{task.contract.user.first_name} {task.contract.user.last_name}".strip()
                }
            })

        return Response({
            'tasks': tasks_data,
            'count': len(tasks_data)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'message': 'Failed to fetch approval inbox', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@jwt_authenticated
def approve_approval_task(request, task_id):
    """
    Approve a specific approval task.

    POST /api/approvals/tasks/{task_id}/approve
    Body: { "comments": "Optional approval comments" }
    """
    try:
        task = get_object_or_404(ApprovalTask, id=task_id)
        comments = request.data.get('comments', '')

        success, message = approve_task(
            approval_task=task,
            user=request.user,
            comments=comments,
            request=request
        )

        if success:
            return Response({
                'message': message,
                'task_status': task.status,
                'contract_status': task.contract.status
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': message
            }, status=status.HTTP_403_FORBIDDEN)

    except Exception as e:
        return Response(
            {'message': 'Failed to approve task', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@jwt_authenticated
def reject_approval_task(request, task_id):
    """
    Reject a specific approval task.

    POST /api/approvals/tasks/{task_id}/reject
    Body: { "comments": "Rejection reason (required)" }
    """
    try:
        task = get_object_or_404(ApprovalTask, id=task_id)
        comments = request.data.get('comments', '')

        if not comments:
            return Response({
                'message': 'Rejection reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        success, message = reject_task(
            approval_task=task,
            user=request.user,
            comments=comments,
            request=request
        )

        if success:
            return Response({
                'message': message,
                'task_status': task.status,
                'contract_status': task.contract.status
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': message
            }, status=status.HTTP_403_FORBIDDEN)

    except Exception as e:
        return Response(
            {'message': 'Failed to reject task', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =========================
# CONTRACT APPROVAL STATUS
# =========================

@api_view(['GET'])
@jwt_authenticated
def get_contract_approvals(request, contract_id):
    """
    Get approval status and timeline for a specific contract.

    GET /api/approvals/contracts/{contract_id}
    """
    try:
        contract = get_object_or_404(Contract, id=contract_id)

        # Get approval status
        approval_status = get_contract_approval_status(contract)

        # Format tasks
        tasks_data = []
        for task in approval_status['tasks']:
            task_data = {
                'id': task.id,
                'role_required': task.role_required,
                'workflow_stage': task.workflow_stage,
                'status': task.status,
                'created_at': task.created_at.isoformat(),
                'approved_at': task.approved_at.isoformat() if task.approved_at else None,
                'comments': task.comments,
                'assigned_to': None
            }

            if task.assigned_to:
                task_data['assigned_to'] = {
                    'email': task.assigned_to.email,
                    'name': f"{task.assigned_to.first_name} {task.assigned_to.last_name}".strip(),
                    'role': task.assigned_to.role.name
                }

            tasks_data.append(task_data)

        return Response({
            'contract': {
                'id': contract.id,
                'name': contract.original_filename,
                'status': contract.status
            },
            'approval_status': {
                'total_tasks': approval_status['total_tasks'],
                'approved': approval_status['approved'],
                'rejected': approval_status['rejected'],
                'pending': approval_status['pending'],
                'is_complete': approval_status['is_complete'],
                'is_rejected': approval_status['is_rejected']
            },
            'tasks': tasks_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'message': 'Failed to fetch contract approvals', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_authenticated
def get_approval_timeline(request, contract_id):
    """
    Get full approval timeline including audit trail.

    GET /api/approvals/contracts/{contract_id}/timeline
    """
    try:
        contract = get_object_or_404(Contract, id=contract_id)

        # Get all audit records
        audits = ApprovalAudit.objects.filter(
            contract=contract
        ).select_related('user', 'approval_task').order_by('-timestamp')

        timeline_data = []
        for audit in audits:
            timeline_data.append({
                'id': audit.id,
                'action': audit.action,
                'timestamp': audit.timestamp.isoformat(),
                'user': {
                    'email': audit.user.email if audit.user else 'Unknown',
                    'name': f"{audit.user.first_name} {audit.user.last_name}".strip() if audit.user else 'Unknown',
                    'role': audit.user_role
                },
                'task': {
                    'id': audit.approval_task.id,
                    'role_required': audit.approval_task.role_required,
                    'workflow_stage': audit.approval_task.workflow_stage
                },
                'comments': audit.comments,
                'metadata': {
                    'ip_address': audit.ip_address,
                    'user_agent': audit.user_agent
                }
            })

        return Response({
            'contract': {
                'id': contract.id,
                'name': contract.original_filename,
                'status': contract.status
            },
            'timeline': timeline_data,
            'count': len(timeline_data)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'message': 'Failed to fetch approval timeline', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =========================
# APPROVAL ANALYTICS
# =========================

@api_view(['GET'])
@jwt_authenticated
def get_approval_stats(request):
    """
    Get approval statistics for the current user.

    GET /api/approvals/stats
    """
    try:
        user = request.user

        # Count tasks by status
        total_pending = ApprovalTask.objects.filter(
            role_required=user.role.name.upper(),
            status='PENDING'
        ).count()

        total_approved = ApprovalAudit.objects.filter(
            user=user,
            action='APPROVED'
        ).count()

        total_rejected = ApprovalAudit.objects.filter(
            user=user,
            action='REJECTED'
        ).count()

        # Recent activity
        recent_actions = ApprovalAudit.objects.filter(
            user=user
        ).select_related('contract', 'approval_task').order_by('-timestamp')[:10]

        recent_data = []
        for audit in recent_actions:
            recent_data.append({
                'action': audit.action,
                'timestamp': audit.timestamp.isoformat(),
                'contract_name': audit.contract.original_filename,
                'role': audit.user_role
            })

        return Response({
            'stats': {
                'pending': total_pending,
                'approved': total_approved,
                'rejected': total_rejected,
                'total_actions': total_approved + total_rejected
            },
            'recent_activity': recent_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'message': 'Failed to fetch approval stats', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
