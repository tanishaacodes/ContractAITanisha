"""
Role-Based Approval Service

Handles:
- Approval workflow policies
- Task creation and validation
- Permission checks
- Workflow advancement
"""

from django.utils import timezone
from core.models import Contract, ApprovalTask, ApprovalAudit, User


# =========================
# APPROVAL FLOW POLICIES
# =========================

# Maps contract status to required approval roles
APPROVAL_FLOW = {
    'DRAFT': [],  # No approvals needed yet
    'LEGAL_REVIEW': ['LEGAL'],
    'BUSINESS_REVIEW': ['BUSINESS'],
    'COMPLIANCE_REVIEW': ['COMPLIANCE'],
    'FINAL_APPROVAL': ['ADMIN'],
    'APPROVED': [],  # No more approvals needed
    'REJECTED': [],
}

# Maps workflow stages to next stage upon approval
NEXT_STAGE = {
    'DRAFT': 'LEGAL_REVIEW',
    'LEGAL_REVIEW': 'BUSINESS_REVIEW',
    'BUSINESS_REVIEW': 'COMPLIANCE_REVIEW',
    'COMPLIANCE_REVIEW': 'FINAL_APPROVAL',
    'FINAL_APPROVAL': 'APPROVED',
}


# =========================
# CORE SERVICE FUNCTIONS
# =========================

def create_approval_tasks(contract):
    """
    Create approval tasks for the current contract status.

    Args:
        contract: Contract instance

    Returns:
        List of created ApprovalTask instances
    """
    roles = APPROVAL_FLOW.get(contract.status, [])
    tasks = []

    for role in roles:
        task = ApprovalTask.objects.create(
            contract=contract,
            role_required=role,
            workflow_stage=contract.status,
            status='PENDING'
        )
        tasks.append(task)

    return tasks


def user_can_approve(user, approval_task):
    """
    Check if user has permission to approve this task.

    Args:
        user: User instance
        approval_task: ApprovalTask instance

    Returns:
        Boolean indicating if user can approve
    """
    # Check if user's role matches the required role for this approval
    # The Role model has a 'name' field
    user_role_name = user.role.name.upper()
    required_role = approval_task.role_required.upper()

    # Direct match
    if user_role_name == required_role:
        return True

    # Admin can approve anything
    if user_role_name == 'ADMIN':
        return True

    return False


def approve_task(approval_task, user, comments='', request=None):
    """
    Approve a task and create audit trail.

    Args:
        approval_task: ApprovalTask instance
        user: User who is approving
        comments: Optional approval comments
        request: HTTP request object for audit metadata

    Returns:
        Tuple of (success: bool, message: str)
    """
    # Permission check
    if not user_can_approve(user, approval_task):
        return False, "You do not have permission to approve this task"

    # Status check
    if approval_task.status != 'PENDING':
        return False, f"Task is already {approval_task.status.lower()}"

    # Update task
    approval_task.status = 'APPROVED'
    approval_task.assigned_to = user
    approval_task.approved_at = timezone.now()
    approval_task.comments = comments
    approval_task.save()

    # Create audit trail
    create_audit_record(
        approval_task=approval_task,
        user=user,
        action='APPROVED',
        comments=comments,
        request=request
    )

    # Try to advance contract workflow
    advance_contract_if_ready(approval_task.contract)

    return True, "Approval recorded successfully"


def reject_task(approval_task, user, comments='', request=None):
    """
    Reject a task and create audit trail.

    Args:
        approval_task: ApprovalTask instance
        user: User who is rejecting
        comments: Rejection reason (required)
        request: HTTP request object for audit metadata

    Returns:
        Tuple of (success: bool, message: str)
    """
    # Permission check
    if not user_can_approve(user, approval_task):
        return False, "You do not have permission to reject this task"

    # Status check
    if approval_task.status != 'PENDING':
        return False, f"Task is already {approval_task.status.lower()}"

    # Rejection reason required
    if not comments:
        return False, "Rejection reason is required"

    # Update task
    approval_task.status = 'REJECTED'
    approval_task.assigned_to = user
    approval_task.approved_at = timezone.now()
    approval_task.comments = comments
    approval_task.save()

    # Create audit trail
    create_audit_record(
        approval_task=approval_task,
        user=user,
        action='REJECTED',
        comments=comments,
        request=request
    )

    # Reject the contract
    contract = approval_task.contract
    contract.status = 'REJECTED'
    contract.save()

    return True, "Rejection recorded successfully"


def advance_contract_if_ready(contract):
    """
    Advance contract to next stage if all approvals are complete.

    Args:
        contract: Contract instance

    Returns:
        Boolean indicating if contract was advanced
    """
    # Check if there are any pending approvals for current stage
    pending_tasks = ApprovalTask.objects.filter(
        contract=contract,
        workflow_stage=contract.status,
        status='PENDING'
    ).exists()

    if pending_tasks:
        # Still waiting for approvals
        return False

    # Check if any task was rejected
    rejected_tasks = ApprovalTask.objects.filter(
        contract=contract,
        workflow_stage=contract.status,
        status='REJECTED'
    ).exists()

    if rejected_tasks:
        # Contract was rejected, don't advance
        contract.status = 'REJECTED'
        contract.save()
        return False

    # All tasks approved, advance to next stage
    next_status = NEXT_STAGE.get(contract.status)

    if next_status:
        contract.status = next_status
        contract.save()

        # Create approval tasks for the new stage
        create_approval_tasks(contract)
        return True

    return False


def create_audit_record(approval_task, user, action, comments, request=None):
    """
    Create an immutable audit trail record.

    Args:
        approval_task: ApprovalTask instance
        user: User who performed action
        action: Action taken (APPROVED/REJECTED/REASSIGNED)
        comments: Action comments
        request: HTTP request for metadata
    """
    ip_address = None
    user_agent = None

    if request:
        # Extract IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        # Extract user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

    ApprovalAudit.objects.create(
        contract=approval_task.contract,
        approval_task=approval_task,
        user=user,
        user_role=user.role.name,
        action=action,
        comments=comments,
        ip_address=ip_address,
        user_agent=user_agent
    )


def get_pending_approvals_for_user(user):
    """
    Get all pending approval tasks that a user can approve.

    Args:
        user: User instance

    Returns:
        QuerySet of ApprovalTask instances
    """
    user_role_name = user.role.name.upper()

    # Get tasks matching user's role
    tasks = ApprovalTask.objects.filter(
        status='PENDING',
        role_required=user_role_name
    ).select_related('contract', 'contract__user')

    # If admin, get all pending tasks
    if user_role_name == 'ADMIN':
        tasks = ApprovalTask.objects.filter(
            status='PENDING'
        ).select_related('contract', 'contract__user')

    return tasks


def get_contract_approval_status(contract):
    """
    Get comprehensive approval status for a contract.

    Args:
        contract: Contract instance

    Returns:
        Dictionary with approval status information
    """
    tasks = ApprovalTask.objects.filter(contract=contract).order_by('created_at')

    total_tasks = tasks.count()
    approved_tasks = tasks.filter(status='APPROVED').count()
    rejected_tasks = tasks.filter(status='REJECTED').count()
    pending_tasks = tasks.filter(status='PENDING').count()

    return {
        'contract_status': contract.status,
        'total_tasks': total_tasks,
        'approved': approved_tasks,
        'rejected': rejected_tasks,
        'pending': pending_tasks,
        'is_complete': pending_tasks == 0 and rejected_tasks == 0,
        'is_rejected': contract.status == 'REJECTED' or rejected_tasks > 0,
        'tasks': tasks
    }


def initiate_approval_workflow(contract):
    """
    Initiate the approval workflow for a contract in DRAFT status.

    Args:
        contract: Contract instance

    Returns:
        Tuple of (success: bool, message: str)
    """
    if contract.status != 'DRAFT':
        return False, f"Contract must be in DRAFT status to initiate workflow. Current status: {contract.status}"

    # Move to first approval stage
    contract.status = 'LEGAL_REVIEW'
    contract.save()

    # Create initial approval tasks
    tasks = create_approval_tasks(contract)

    return True, f"Approval workflow initiated. Created {len(tasks)} approval task(s)."
