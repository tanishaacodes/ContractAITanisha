from django.db import models
from core.models import User


class ContractDrift(models.Model):
    """
    Tracks detected drift between contract terms and actual business behavior.
    """
    # Core identifiers
    contract_id = models.CharField(max_length=64, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contract_drifts')

    # Drift classification
    drift_type = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Type of drift: scope_creep, implied_amendment, waiver, etc."
    )

    # Behavior analysis
    contract_terms = models.TextField(help_text="Original contract terms")
    detected_behavior = models.TextField(help_text="Observed behavior that deviates from contract")

    behavior_context = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional context from CRM, support tickets, emails, etc."
    )

    # Risk assessment
    legal_risk = models.TextField(help_text="Detailed legal risk analysis")
    business_impact = models.TextField(
        null=True,
        blank=True,
        help_text="Impact on revenue, obligations, precedent"
    )

    # Severity and status
    severity = models.IntegerField(
        default=5,
        help_text="Severity rating from 1 (low) to 10 (critical)"
    )

    status = models.CharField(
        max_length=32,
        default='detected',
        choices=[
            ('detected', 'Detected'),
            ('acknowledged', 'Acknowledged'),
            ('remediation_planned', 'Remediation Planned'),
            ('remediation_in_progress', 'Remediation In Progress'),
            ('resolved', 'Resolved'),
            ('accepted', 'Accepted as New Norm'),
        ],
        db_index=True
    )

    # Legal doctrines implicated
    legal_doctrines = models.JSONField(
        default=list,
        help_text="List of legal doctrines: waiver, estoppel, course of dealing, etc."
    )

    # Remediation
    remediation_recommendations = models.TextField(
        null=True,
        blank=True,
        help_text="Recommended actions to address the drift"
    )

    remediation_taken = models.TextField(
        null=True,
        blank=True,
        help_text="Actions actually taken to remediate"
    )

    # Timestamps
    detected_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Analytics
    drift_duration_days = models.IntegerField(
        null=True,
        blank=True,
        help_text="How long the drift has been occurring"
    )

    frequency_count = models.IntegerField(
        default=1,
        help_text="Number of times this drift pattern has occurred"
    )

    class Meta:
        db_table = 'contract_drift'
        ordering = ['-severity', '-detected_at']
        indexes = [
            models.Index(fields=['contract_id', '-detected_at']),
            models.Index(fields=['user', 'status', '-detected_at']),
            models.Index(fields=['severity', 'status']),
            models.Index(fields=['drift_type']),
        ]

    def __str__(self):
        return f"Drift {self.id} - {self.drift_type} (Severity: {self.severity})"


class DriftAlert(models.Model):
    """
    Automated alerts for critical drift detection.
    """
    drift = models.ForeignKey(ContractDrift, on_delete=models.CASCADE, related_name='alerts')

    alert_type = models.CharField(
        max_length=32,
        choices=[
            ('critical_severity', 'Critical Severity'),
            ('legal_risk', 'Legal Risk'),
            ('revenue_impact', 'Revenue Impact'),
            ('compliance_issue', 'Compliance Issue'),
        ]
    )

    alert_message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'drift_alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['drift', 'is_read']),
        ]

    def __str__(self):
        return f"Alert {self.id} - {self.alert_type}"


class BehaviorLog(models.Model):
    """
    Logs individual instances of behavior that contribute to drift detection.
    """
    contract_id = models.CharField(max_length=64, db_index=True)
    drift = models.ForeignKey(
        ContractDrift,
        on_delete=models.CASCADE,
        related_name='behavior_logs',
        null=True,
        blank=True
    )

    # Source of behavior data
    data_source = models.CharField(
        max_length=64,
        choices=[
            ('crm', 'CRM System'),
            ('billing', 'Billing System'),
            ('support', 'Support Tickets'),
            ('email', 'Email Communications'),
            ('slack', 'Slack Messages'),
            ('manual', 'Manual Entry'),
        ]
    )

    # Behavior details
    behavior_description = models.TextField()
    behavior_date = models.DateField()

    # Related entities
    related_user_id = models.CharField(max_length=128, null=True, blank=True)
    related_ticket_id = models.CharField(max_length=128, null=True, blank=True)

    # Metadata
    raw_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Raw data from the source system"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'behavior_logs'
        ordering = ['-behavior_date']
        indexes = [
            models.Index(fields=['contract_id', '-behavior_date']),
            models.Index(fields=['data_source', '-behavior_date']),
        ]

    def __str__(self):
        return f"Behavior Log {self.id} - {self.data_source} on {self.behavior_date}"
