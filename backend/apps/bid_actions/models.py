"""
Bid Actions Models - Enterprise Action Item Management
Supports multi-department bid orchestration with risk propagation
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Department(models.Model):
    """
    Departments involved in mega EPC projects
    Civil, Mechanical, Electrical, MEP, Legal, Finance, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    color_hex = models.CharField(max_length=7, default="#3b82f6")
    workload_weight = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bid_departments'
        ordering = ['name']

    def __str__(self):
        return self.name


class ActionItem(models.Model):
    """
    Individual action items generated from tender analysis
    Maps to specific departments with risk/complexity scores
    """

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Review', 'Review'),
        ('Completed', 'Completed'),
        ('Blocked', 'Blocked'),
    ]

    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]

    SOURCE_TYPE_CHOICES = [
        ('Clause', 'Tender Clause'),
        ('BOQ', 'Bill of Quantities'),
        ('Risk', 'Risk Analysis'),
        ('Negotiation', 'Negotiation Point'),
        ('Eligibility', 'Eligibility Criteria'),
        ('Auto-generated', 'Auto-generated'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tender = models.ForeignKey(
        'tenders.Tender',
        on_delete=models.CASCADE,
        related_name='action_items'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='action_items'
    )

    # Core fields
    title = models.CharField(max_length=255)
    description = models.TextField()

    # Source tracking
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPE_CHOICES)
    source_reference = models.CharField(max_length=255, blank=True)

    # Metadata
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    # Risk & Complexity
    risk_score = models.FloatField(default=0.0, help_text="0.0 to 1.0")
    complexity_score = models.FloatField(default=0.0, help_text="0.0 to 1.0")
    financial_exposure = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Financial impact in INR"
    )

    # Dependencies
    depends_on = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='blocks',
        blank=True
    )

    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_actions'
    )

    # Dates
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bid_action_items'
        ordering = ['-priority', '-risk_score', 'created_at']
        indexes = [
            models.Index(fields=['tender', 'department']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['risk_score']),
        ]

    def __str__(self):
        return f"{self.department.name}: {self.title}"

    def save(self, *args, **kwargs):
        # Auto-update completed_at when status changes to Completed
        if self.status == 'Completed' and not self.completed_at:
            from django.utils import timezone
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)


class RiskPropagation(models.Model):
    """
    Models risk cascade between action items
    If Civil foundation delays → Mechanical installation delays
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_action = models.ForeignKey(
        ActionItem,
        on_delete=models.CASCADE,
        related_name='propagates_to'
    )
    target_action = models.ForeignKey(
        ActionItem,
        on_delete=models.CASCADE,
        related_name='impacted_by'
    )
    propagation_weight = models.FloatField(
        default=0.5,
        help_text="Weight of risk propagation (0.0 to 1.0)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bid_risk_propagations'
        unique_together = [['source_action', 'target_action']]

    def __str__(self):
        return f"{self.source_action.title} → {self.target_action.title} ({self.propagation_weight})"


class DepartmentActionSummary(models.Model):
    """
    Aggregated statistics per department per tender
    Cached for performance
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tender = models.ForeignKey(
        'tenders.Tender',
        on_delete=models.CASCADE,
        related_name='dept_summaries'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='summaries'
    )

    total_actions = models.IntegerField(default=0)
    completed_actions = models.IntegerField(default=0)
    avg_risk_score = models.FloatField(default=0.0)
    total_financial_exposure = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    last_calculated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bid_dept_summaries'
        unique_together = [['tender', 'department']]

    def __str__(self):
        return f"{self.tender.title} - {self.department.name}"
