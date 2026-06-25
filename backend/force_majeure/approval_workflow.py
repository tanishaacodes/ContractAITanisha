"""
Approval Workflow System for Force Majeure Clause Changes
Multi-level approval chain with audit trail and notifications
"""

import uuid
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Approval status enumeration"""
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    WITHDRAWN = 'withdrawn'
    EXPIRED = 'expired'


class ApprovalLevel(Enum):
    """Approval level enumeration"""
    L1_ANALYST = 'analyst'
    L2_MANAGER = 'manager'
    L3_DIRECTOR = 'director'
    L4_LEGAL = 'legal'
    L5_EXECUTIVE = 'executive'


@dataclass
class ApprovalStep:
    """Single approval step"""
    step_id: str
    level: ApprovalLevel
    approver_id: str
    approver_name: str
    approver_email: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    comments: str = ""
    decision_date: Optional[datetime] = None
    required: bool = True


@dataclass
class ApprovalRequest:
    """Approval request for clause change"""
    request_id: str
    contract_id: str
    contract_name: str
    change_type: str  # 'rewrite', 'optimize', 'generate'
    original_clause: str
    proposed_clause: str
    change_justification: str
    risk_reduction: float
    improvement_score: float
    requester_id: str
    requester_name: str
    created_at: datetime
    expires_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    approval_chain: List[ApprovalStep] = field(default_factory=list)
    audit_trail: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class ApprovalWorkflowEngine:
    """
    Approval Workflow Engine

    Features:
    - Multi-level approval chains
    - Configurable approval rules
    - Automatic routing
    - Audit trail tracking
    - Expiration handling
    - Notification integration
    """

    def __init__(self):
        self.requests: Dict[str, ApprovalRequest] = {}
        self.approval_rules = self._initialize_approval_rules()

    def _initialize_approval_rules(self) -> Dict:
        """Initialize approval rules based on change characteristics"""
        return {
            'low_risk': {
                'required_levels': [ApprovalLevel.L1_ANALYST, ApprovalLevel.L2_MANAGER],
                'expiration_days': 7,
                'description': 'Minor clause improvements'
            },
            'medium_risk': {
                'required_levels': [ApprovalLevel.L1_ANALYST, ApprovalLevel.L2_MANAGER, ApprovalLevel.L3_DIRECTOR],
                'expiration_days': 14,
                'description': 'Significant clause changes'
            },
            'high_risk': {
                'required_levels': [
                    ApprovalLevel.L1_ANALYST,
                    ApprovalLevel.L2_MANAGER,
                    ApprovalLevel.L3_DIRECTOR,
                    ApprovalLevel.L4_LEGAL
                ],
                'expiration_days': 21,
                'description': 'Major clause rewrites'
            },
            'critical': {
                'required_levels': [
                    ApprovalLevel.L1_ANALYST,
                    ApprovalLevel.L2_MANAGER,
                    ApprovalLevel.L3_DIRECTOR,
                    ApprovalLevel.L4_LEGAL,
                    ApprovalLevel.L5_EXECUTIVE
                ],
                'expiration_days': 30,
                'description': 'Critical contract modifications'
            }
        }

    def create_approval_request(
        self,
        contract_id: str,
        contract_name: str,
        change_type: str,
        original_clause: str,
        proposed_clause: str,
        change_justification: str,
        risk_reduction: float,
        improvement_score: float,
        requester_id: str,
        requester_name: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create new approval request

        Args:
            contract_id: Contract identifier
            contract_name: Contract name
            change_type: Type of change (rewrite, optimize, generate)
            original_clause: Original clause text
            proposed_clause: Proposed new clause text
            change_justification: Reason for change
            risk_reduction: Estimated risk reduction (0-1)
            improvement_score: Overall improvement score (0-1)
            requester_id: User ID of requester
            requester_name: Name of requester
            metadata: Additional metadata

        Returns:
            request_id: Unique approval request identifier
        """

        request_id = f"APR-{uuid.uuid4().hex[:12].upper()}"

        # Determine risk category and approval chain
        risk_category = self._determine_risk_category(
            change_type,
            risk_reduction,
            improvement_score,
            original_clause,
            proposed_clause
        )

        rules = self.approval_rules[risk_category]
        expiration_date = datetime.now() + timedelta(days=rules['expiration_days'])

        # Create approval request
        request = ApprovalRequest(
            request_id=request_id,
            contract_id=contract_id,
            contract_name=contract_name,
            change_type=change_type,
            original_clause=original_clause,
            proposed_clause=proposed_clause,
            change_justification=change_justification,
            risk_reduction=risk_reduction,
            improvement_score=improvement_score,
            requester_id=requester_id,
            requester_name=requester_name,
            created_at=datetime.now(),
            expires_at=expiration_date,
            metadata=metadata or {}
        )

        # Build approval chain
        request.approval_chain = self._build_approval_chain(
            rules['required_levels'],
            contract_id
        )

        # Add to audit trail
        self._add_audit_entry(
            request,
            'REQUEST_CREATED',
            requester_id,
            f"Approval request created for {change_type}"
        )

        # Store request
        self.requests[request_id] = request

        # Send notifications to first approver
        self._notify_next_approver(request)

        logger.info(f"Created approval request {request_id} for contract {contract_id}")

        return request_id

    def approve_step(
        self,
        request_id: str,
        approver_id: str,
        comments: Optional[str] = None
    ) -> Dict:
        """
        Approve current step in approval chain

        Args:
            request_id: Approval request ID
            approver_id: ID of approver
            comments: Optional comments

        Returns:
            Updated request status
        """

        if request_id not in self.requests:
            return {'error': f'Request {request_id} not found'}

        request = self.requests[request_id]

        # Check if request is expired
        if datetime.now() > request.expires_at:
            request.status = ApprovalStatus.EXPIRED
            return {'error': 'Request has expired'}

        # Find current pending step for this approver
        current_step = None
        for step in request.approval_chain:
            if step.approver_id == approver_id and step.status == ApprovalStatus.PENDING:
                current_step = step
                break

        if not current_step:
            return {'error': 'No pending approval found for this user'}

        # Approve step
        current_step.status = ApprovalStatus.APPROVED
        current_step.decision_date = datetime.now()
        current_step.comments = comments or ""

        # Add to audit trail
        self._add_audit_entry(
            request,
            'STEP_APPROVED',
            approver_id,
            f"Approved by {current_step.approver_name} ({current_step.level.value})"
        )

        # Check if all steps are approved
        if all(step.status == ApprovalStatus.APPROVED for step in request.approval_chain if step.required):
            request.status = ApprovalStatus.APPROVED
            self._add_audit_entry(
                request,
                'REQUEST_APPROVED',
                'system',
                'All approval steps completed'
            )
            # Notify requester
            self._notify_requester(request, 'approved')
        else:
            # Notify next approver
            self._notify_next_approver(request)

        logger.info(f"Approved step for request {request_id} by {approver_id}")

        return {
            'request_id': request_id,
            'step_status': 'approved',
            'overall_status': request.status.value,
            'next_approver': self._get_next_approver(request)
        }

    def reject_step(
        self,
        request_id: str,
        approver_id: str,
        reason: str
    ) -> Dict:
        """
        Reject approval request

        Args:
            request_id: Approval request ID
            approver_id: ID of approver
            reason: Reason for rejection

        Returns:
            Updated request status
        """

        if request_id not in self.requests:
            return {'error': f'Request {request_id} not found'}

        request = self.requests[request_id]

        # Find current step
        current_step = None
        for step in request.approval_chain:
            if step.approver_id == approver_id and step.status == ApprovalStatus.PENDING:
                current_step = step
                break

        if not current_step:
            return {'error': 'No pending approval found for this user'}

        # Reject step (rejects entire request)
        current_step.status = ApprovalStatus.REJECTED
        current_step.decision_date = datetime.now()
        current_step.comments = reason

        request.status = ApprovalStatus.REJECTED

        # Add to audit trail
        self._add_audit_entry(
            request,
            'REQUEST_REJECTED',
            approver_id,
            f"Rejected by {current_step.approver_name}: {reason}"
        )

        # Notify requester
        self._notify_requester(request, 'rejected')

        logger.info(f"Rejected request {request_id} by {approver_id}")

        return {
            'request_id': request_id,
            'status': 'rejected',
            'rejected_by': current_step.approver_name,
            'reason': reason
        }

    def withdraw_request(
        self,
        request_id: str,
        requester_id: str,
        reason: str
    ) -> Dict:
        """
        Withdraw approval request

        Args:
            request_id: Approval request ID
            requester_id: ID of requester
            reason: Reason for withdrawal

        Returns:
            Withdrawal confirmation
        """

        if request_id not in self.requests:
            return {'error': f'Request {request_id} not found'}

        request = self.requests[request_id]

        if request.requester_id != requester_id:
            return {'error': 'Only requester can withdraw request'}

        if request.status != ApprovalStatus.PENDING:
            return {'error': f'Cannot withdraw request with status {request.status.value}'}

        request.status = ApprovalStatus.WITHDRAWN

        self._add_audit_entry(
            request,
            'REQUEST_WITHDRAWN',
            requester_id,
            f"Withdrawn by requester: {reason}"
        )

        logger.info(f"Withdrawn request {request_id} by {requester_id}")

        return {
            'request_id': request_id,
            'status': 'withdrawn',
            'reason': reason
        }

    def get_request_status(self, request_id: str) -> Dict:
        """Get approval request status"""

        if request_id not in self.requests:
            return {'error': f'Request {request_id} not found'}

        request = self.requests[request_id]

        return {
            'request_id': request.request_id,
            'contract_id': request.contract_id,
            'contract_name': request.contract_name,
            'change_type': request.change_type,
            'status': request.status.value,
            'created_at': request.created_at.isoformat(),
            'expires_at': request.expires_at.isoformat(),
            'requester': request.requester_name,
            'risk_reduction': round(request.risk_reduction, 3),
            'improvement_score': round(request.improvement_score, 3),
            'approval_chain': [
                {
                    'level': step.level.value,
                    'approver': step.approver_name,
                    'status': step.status.value,
                    'comments': step.comments,
                    'decision_date': step.decision_date.isoformat() if step.decision_date else None
                }
                for step in request.approval_chain
            ],
            'audit_trail': request.audit_trail
        }

    def get_pending_approvals(self, approver_id: str) -> List[Dict]:
        """Get all pending approvals for an approver"""

        pending = []

        for request in self.requests.values():
            if request.status != ApprovalStatus.PENDING:
                continue

            # Check if expired
            if datetime.now() > request.expires_at:
                request.status = ApprovalStatus.EXPIRED
                continue

            # Find pending steps for this approver
            for step in request.approval_chain:
                if step.approver_id == approver_id and step.status == ApprovalStatus.PENDING:
                    pending.append({
                        'request_id': request.request_id,
                        'contract_id': request.contract_id,
                        'contract_name': request.contract_name,
                        'change_type': request.change_type,
                        'requester': request.requester_name,
                        'created_at': request.created_at.isoformat(),
                        'expires_at': request.expires_at.isoformat(),
                        'approval_level': step.level.value,
                        'risk_reduction': round(request.risk_reduction, 3),
                        'improvement_score': round(request.improvement_score, 3)
                    })
                    break

        return pending

    def _determine_risk_category(
        self,
        change_type: str,
        risk_reduction: float,
        improvement_score: float,
        original_clause: str,
        proposed_clause: str
    ) -> str:
        """Determine risk category for approval routing"""

        # Critical: Complete clause generation or major rewrites
        if change_type == 'generate' or len(original_clause) < 50:
            return 'critical'

        # High risk: Large improvement scores or high risk reduction
        if risk_reduction > 0.50 or improvement_score > 0.60:
            return 'high_risk'

        # Medium risk: Moderate changes
        if risk_reduction > 0.30 or improvement_score > 0.40:
            return 'medium_risk'

        # Low risk: Minor improvements
        return 'low_risk'

    def _build_approval_chain(
        self,
        required_levels: List[ApprovalLevel],
        contract_id: str
    ) -> List[ApprovalStep]:
        """Build approval chain based on required levels"""

        # In production, would look up actual approvers from database
        # For now, use placeholder approvers

        approver_mapping = {
            ApprovalLevel.L1_ANALYST: {
                'id': 'analyst001',
                'name': 'Contract Analyst',
                'email': 'analyst@company.com'
            },
            ApprovalLevel.L2_MANAGER: {
                'id': 'manager001',
                'name': 'Contract Manager',
                'email': 'manager@company.com'
            },
            ApprovalLevel.L3_DIRECTOR: {
                'id': 'director001',
                'name': 'Legal Director',
                'email': 'director@company.com'
            },
            ApprovalLevel.L4_LEGAL: {
                'id': 'legal001',
                'name': 'General Counsel',
                'email': 'legal@company.com'
            },
            ApprovalLevel.L5_EXECUTIVE: {
                'id': 'exec001',
                'name': 'Chief Executive',
                'email': 'exec@company.com'
            }
        }

        chain = []
        for level in required_levels:
            approver = approver_mapping[level]
            step = ApprovalStep(
                step_id=f"step_{uuid.uuid4().hex[:8]}",
                level=level,
                approver_id=approver['id'],
                approver_name=approver['name'],
                approver_email=approver['email']
            )
            chain.append(step)

        return chain

    def _add_audit_entry(
        self,
        request: ApprovalRequest,
        action: str,
        actor_id: str,
        description: str
    ):
        """Add entry to audit trail"""

        request.audit_trail.append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'actor_id': actor_id,
            'description': description
        })

    def _get_next_approver(self, request: ApprovalRequest) -> Optional[Dict]:
        """Get next pending approver"""

        for step in request.approval_chain:
            if step.status == ApprovalStatus.PENDING:
                return {
                    'approver_id': step.approver_id,
                    'approver_name': step.approver_name,
                    'level': step.level.value
                }

        return None

    def _notify_next_approver(self, request: ApprovalRequest):
        """Notify next approver in chain"""

        next_approver = self._get_next_approver(request)
        if next_approver:
            # In production, send email/notification
            logger.info(
                f"Notifying {next_approver['approver_name']} "
                f"for approval request {request.request_id}"
            )

    def _notify_requester(self, request: ApprovalRequest, outcome: str):
        """Notify requester of final outcome"""

        logger.info(
            f"Notifying requester {request.requester_name} "
            f"that request {request.request_id} was {outcome}"
        )


# Global instance
approval_workflow_engine = ApprovalWorkflowEngine()


# Convenience functions
def create_clause_approval_request(
    contract_id: str,
    contract_name: str,
    original_clause: str,
    proposed_clause: str,
    change_justification: str,
    risk_reduction: float,
    requester_id: str,
    requester_name: str
) -> str:
    """Create approval request for clause change"""
    return approval_workflow_engine.create_approval_request(
        contract_id,
        contract_name,
        'rewrite',
        original_clause,
        proposed_clause,
        change_justification,
        risk_reduction,
        0.5,  # Default improvement score
        requester_id,
        requester_name
    )


def get_my_pending_approvals(approver_id: str) -> List[Dict]:
    """Get pending approvals for user"""
    return approval_workflow_engine.get_pending_approvals(approver_id)
