from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Tender(models.Model):
    """Main tender model storing core tender information"""

    # Basic Information
    title = models.CharField(max_length=500)
    reference_number = models.CharField(max_length=200, null=True, blank=True)

    # Financial Information
    estimated_value = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    bid_security = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    emd_amount = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True,
        help_text="Earnest Money Deposit"
    )

    # Timeline Information
    submission_deadline = models.DateTimeField(null=True, blank=True)
    technical_opening_date = models.DateTimeField(null=True, blank=True)
    financial_opening_date = models.DateTimeField(null=True, blank=True)
    completion_period_days = models.IntegerField(null=True, blank=True)

    # Document Information
    pdf_file = models.FileField(upload_to='tenders/', null=True, blank=True)
    pdf_url = models.URLField(null=True, blank=True)

    # Extracted Information
    summary = models.TextField(null=True, blank=True)
    scope_of_work = models.TextField(null=True, blank=True)

    # Status
    status = models.CharField(
        max_length=50,
        choices=[
            ('DRAFT', 'Draft'),
            ('ANALYZING', 'Analyzing'),
            ('ANALYZED', 'Analyzed'),
            ('BIDDING', 'Bidding'),
            ('SUBMITTED', 'Submitted'),
            ('WON', 'Won'),
            ('LOST', 'Lost'),
        ],
        default='DRAFT'
    )

    # Ownership
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tenders',
        db_column='uploadedById'
    )
    organization = models.CharField(max_length=300, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['uploaded_by']),
        ]

    def __str__(self):
        return f"{self.reference_number or 'TENDER'} - {self.title[:50]}"


class TenderSection(models.Model):
    """Hierarchical section model for parsed tender documents"""

    tender = models.ForeignKey(
        Tender,
        on_delete=models.CASCADE,
        related_name='sections'
    )

    section_number = models.CharField(max_length=50)
    title = models.TextField()

    # Hierarchical structure
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='subsections'
    )
    level = models.IntegerField(default=0)

    # Content
    content = models.TextField()

    # Vector embeddings reference
    vector_id = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['section_number']
        indexes = [
            models.Index(fields=['tender', 'section_number']),
        ]

    def __str__(self):
        return f"{self.section_number} - {self.title[:50]}"


class TenderWorkItem(models.Model):
    """BOQ / Work Items with category classification"""

    CATEGORY_CHOICES = [
        ('CIVIL', 'Civil Work'),
        ('MECHANICAL', 'Mechanical Work'),
        ('MEP', 'MEP Work'),
        ('ELECTRICAL', 'Electrical Work'),
        ('PLUMBING', 'Plumbing Work'),
        ('HVAC', 'HVAC Work'),
        ('OTHER', 'Other'),
    ]

    tender = models.ForeignKey(
        Tender,
        on_delete=models.CASCADE,
        related_name='work_items'
    )

    # Work Item Details
    item_code = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    # Quantity Information
    quantity = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=50, null=True, blank=True)

    # Cost Breakdown
    estimated_cost = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    base_material_cost = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    base_labor_cost = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    base_equipment_cost = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )

    # Cost Factors
    overhead_percentage = models.FloatField(default=10.0)
    risk_factor = models.FloatField(default=0.05)
    final_unit_cost = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['item_code']
        indexes = [
            models.Index(fields=['tender', 'category']),
        ]

    def __str__(self):
        return f"{self.item_code or 'ITEM'} - {self.description[:50]}"


class TenderEligibility(models.Model):
    """Eligibility criteria extracted from tender"""

    tender = models.OneToOneField(
        Tender,
        on_delete=models.CASCADE,
        related_name='eligibility'
    )

    # Financial Criteria
    min_turnover = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    turnover_multiplier = models.FloatField(
        null=True, blank=True,
        help_text="Turnover required as multiple of tender value"
    )
    min_net_worth = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )

    # Experience Criteria
    min_projects = models.IntegerField(null=True, blank=True)
    min_project_value = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    similar_work_required = models.BooleanField(default=False)

    # Other Requirements
    technical_criteria = models.JSONField(null=True, blank=True)
    other_requirements = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Eligibility for {self.tender.reference_number}"


class TenderRisk(models.Model):
    """Salient risks identified in tender"""

    CATEGORY_CHOICES = [
        ('UNLIMITED_LIABILITY', 'Unlimited Liability'),
        ('HIGH_LD', 'High Liquidated Damages'),
        ('ONE_SIDED_TERMINATION', 'One-Sided Termination'),
        ('PAYMENT_TERMS', 'Unfavorable Payment Terms'),
        ('PERFORMANCE_GUARANTEE', 'High Performance Guarantee'),
        ('WARRANTY_PERIOD', 'Extended Warranty Period'),
        ('FORCE_MAJEURE', 'Limited Force Majeure'),
        ('INDEMNITY', 'Broad Indemnity Clause'),
        ('DISPUTE_RESOLUTION', 'Unfavorable Dispute Resolution'),
        ('SCOPE_AMBIGUITY', 'Scope Ambiguity'),
        ('OTHER', 'Other Risk'),
    ]

    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    tender = models.ForeignKey(
        Tender,
        on_delete=models.CASCADE,
        related_name='risks'
    )

    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    description = models.TextField()
    clause_reference = models.CharField(max_length=200, null=True, blank=True)

    # Impact Assessment
    financial_exposure = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='MEDIUM'
    )
    severity_score = models.FloatField(default=0.5)

    # Mitigation
    mitigation_suggestion = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-severity_score', '-created_at']
        indexes = [
            models.Index(fields=['tender', '-severity_score']),
        ]

    def __str__(self):
        return f"{self.category} - {self.severity}"


class TenderConflict(models.Model):
    """Conflicting clauses identified in tender"""

    tender = models.ForeignKey(
        Tender,
        on_delete=models.CASCADE,
        related_name='conflicts'
    )

    clause_a = models.TextField()
    clause_a_reference = models.CharField(max_length=200, null=True, blank=True)

    clause_b = models.TextField()
    clause_b_reference = models.CharField(max_length=200, null=True, blank=True)

    contradiction_score = models.FloatField(default=0.0)
    explanation = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-contradiction_score', '-created_at']

    def __str__(self):
        return f"Conflict: {self.clause_a_reference} vs {self.clause_b_reference}"


class BidScenario(models.Model):
    """Bid pricing scenarios with win probability"""

    tender = models.ForeignKey(
        Tender,
        on_delete=models.CASCADE,
        related_name='bid_scenarios'
    )

    margin_percentage = models.FloatField()
    total_cost = models.DecimalField(max_digits=20, decimal_places=2)
    bid_price = models.DecimalField(max_digits=20, decimal_places=2)

    win_probability = models.FloatField()
    expected_profit = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )

    is_recommended = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-win_probability']
        indexes = [
            models.Index(fields=['tender', '-win_probability']),
        ]

    def __str__(self):
        return f"{self.margin_percentage}% margin - {self.win_probability}% win prob"


class TenderProposal(models.Model):
    """Generated proposal for tender"""

    tender = models.OneToOneField(
        Tender,
        on_delete=models.CASCADE,
        related_name='proposal'
    )

    # Proposal Sections
    technical_compliance = models.TextField(null=True, blank=True)
    construction_methodology = models.TextField(null=True, blank=True)
    resource_mobilization = models.TextField(null=True, blank=True)
    risk_mitigation = models.TextField(null=True, blank=True)
    commercial_positioning = models.TextField(null=True, blank=True)
    schedule_assurance = models.TextField(null=True, blank=True)
    value_engineering = models.TextField(null=True, blank=True)

    # Full Proposal
    full_proposal = models.TextField(null=True, blank=True)

    # Competitive Analysis
    competitor_analysis = models.JSONField(null=True, blank=True)
    competitive_advantage = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Proposal for {self.tender.reference_number}"


class TenderNegotiation(models.Model):
    """Tender negotiation tracking"""

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('PARTIAL', 'Partially Accepted'),
    ]

    tender = models.ForeignKey(
        Tender,
        on_delete=models.CASCADE,
        related_name='negotiations'
    )

    issue_type = models.CharField(max_length=100)
    original_clause = models.TextField()
    clause_reference = models.CharField(max_length=200, null=True, blank=True)

    counter_proposal = models.TextField()
    rationale = models.TextField(null=True, blank=True)

    negotiation_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OPEN'
    )

    # Simulation
    acceptance_probability = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.issue_type} - {self.negotiation_status}"


class PreBidQuestion(models.Model):
    """Pre-bid questions generated for clarification"""

    CATEGORY_CHOICES = [
        ('COMMERCIAL', 'Commercial'),
        ('TECHNICAL', 'Technical'),
        ('ELIGIBILITY', 'Eligibility'),
        ('RISK', 'Risk Allocation'),
        ('TIMELINE', 'Timeline'),
        ('SCOPE', 'Scope Clarification'),
        ('OTHER', 'Other'),
    ]

    tender = models.ForeignKey(
        Tender,
        on_delete=models.CASCADE,
        related_name='prebid_questions'
    )

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    question = models.TextField()
    rationale = models.TextField(null=True, blank=True)

    # Tracking
    is_submitted = models.BooleanField(default=False)
    response = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', '-created_at']

    def __str__(self):
        return f"{self.category} - {self.question[:50]}"


class CompanyProfile(models.Model):
    """Company profile for eligibility checks and proposal generation"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='company_profile',
        db_column='userId'
    )

    # Company Information
    company_name = models.CharField(max_length=300)
    registration_number = models.CharField(max_length=100, null=True, blank=True)

    # Financial Information
    annual_turnover = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    net_worth = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )

    # Experience
    years_in_business = models.IntegerField(null=True, blank=True)
    total_projects_completed = models.IntegerField(default=0)
    similar_projects_completed = models.IntegerField(default=0)

    # Performance
    past_win_rate = models.FloatField(default=0.0)
    average_project_margin = models.FloatField(default=0.0)

    # Capabilities
    technical_capabilities = models.JSONField(null=True, blank=True)
    certifications = models.JSONField(null=True, blank=True)
    key_equipment = models.JSONField(null=True, blank=True)
    key_personnel = models.JSONField(null=True, blank=True)

    # Strengths
    company_strengths = models.TextField(null=True, blank=True)
    competitive_advantages = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name


class TenderAmendment(models.Model):
    """Tracks amendment versions of a tender document"""

    tender = models.ForeignKey(
        Tender,
        on_delete=models.CASCADE,
        related_name='amendments'
    )

    version_number = models.IntegerField()
    amendment_note = models.TextField(null=True, blank=True)

    # Snapshot of key metrics before this amendment
    snapshot = models.JSONField(null=True, blank=True)

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tender_amendments',
        db_constraint=False,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number']
        indexes = [
            models.Index(fields=['tender', '-version_number']),
        ]

    def __str__(self):
        return f"Amendment v{self.version_number} – {self.tender.reference_number}"


# ─────────────────────────────────────────────────────────────────────────────
# BID MANAGEMENT MODELS
# ─────────────────────────────────────────────────────────────────────────────

class BidDepartment(models.Model):
    """Department reference for bid action orchestration"""
    DEPT_CHOICES = [
        ('Civil',       'Civil'),
        ('Mechanical',  'Mechanical'),
        ('Electrical',  'Electrical'),
        ('MEP',         'MEP'),
        ('Signaling',   'Signaling'),
        ('Planning',    'Planning'),
        ('Procurement', 'Procurement'),
        ('Finance',     'Finance'),
        ('Legal',       'Legal'),
        ('HSE',         'HSE'),
        ('QA/QC',       'QA/QC'),
    ]

    name = models.CharField(max_length=100, choices=DEPT_CHOICES, unique=True)
    workload_weight = models.FloatField(default=1.0)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'bid_department'
        ordering = ['name']

    def __str__(self):
        return self.name


class BidActionItem(models.Model):
    """
    Enterprise action items auto-generated from tender clauses, BOQ,
    and bill of services. Each item is assigned to a department.
    """

    STATUS_CHOICES = [
        ('Pending',     'Pending'),
        ('In Progress', 'In Progress'),
        ('Review',      'Review'),
        ('Completed',   'Completed'),
        ('Blocked',     'Blocked'),
    ]

    PRIORITY_CHOICES = [
        ('Low',      'Low'),
        ('Medium',   'Medium'),
        ('High',     'High'),
        ('Critical', 'Critical'),
    ]

    SOURCE_CHOICES = [
        ('BOQ',          'BOQ'),
        ('Risk',         'Risk'),
        ('Clause',       'Clause'),
        ('Negotiation',  'Negotiation'),
        ('Eligibility',  'Eligibility'),
        ('Static',       'Static'),
    ]

    tender = models.ForeignKey(
        Tender,
        on_delete=models.CASCADE,
        related_name='action_items',
        db_constraint=False,
    )
    department = models.ForeignKey(
        BidDepartment,
        on_delete=models.SET_NULL,
        null=True,
        related_name='action_items',
        db_constraint=False,
    )

    source_type    = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='Static')
    source_ref     = models.CharField(max_length=255, blank=True, null=True)
    title          = models.CharField(max_length=500)
    description    = models.TextField(blank=True, null=True)

    priority          = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    complexity_score  = models.FloatField(default=0.0)
    risk_score        = models.FloatField(default=0.0)
    financial_exposure = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    due_date   = models.DateTimeField(null=True, blank=True)

    # AI-generated flag
    ai_generated = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bid_action_item'
        ordering = ['-risk_score', 'priority', 'department']
        indexes = [
            models.Index(fields=['tender', 'status']),
            models.Index(fields=['tender', 'department']),
            models.Index(fields=['tender', 'priority']),
        ]

    def __str__(self):
        return f"[{self.department}] {self.title}"


class BidActionDependency(models.Model):
    """
    Directed dependency edge between action items.
    source must be completed before target can start.
    """
    source = models.ForeignKey(
        BidActionItem,
        on_delete=models.CASCADE,
        related_name='dependencies_as_source',
        db_constraint=False,
    )
    target = models.ForeignKey(
        BidActionItem,
        on_delete=models.CASCADE,
        related_name='dependencies_as_target',
        db_constraint=False,
    )
    dependency_weight = models.FloatField(default=0.5,
        help_text="Risk propagation weight 0-1")

    class Meta:
        db_table = 'bid_action_dependency'
        unique_together = [('source', 'target')]

    def __str__(self):
        return f"{self.source.title} → {self.target.title} ({self.dependency_weight})"


class BidDepartmentRiskPropagation(models.Model):
    """
    Stores the result of DFS cross-department risk cascade for a tender.
    One row per department per tender, updated each time propagation runs.
    """
    tender = models.ForeignKey(
        Tender,
        on_delete=models.CASCADE,
        related_name='risk_propagations',
        db_constraint=False,
    )
    department_name   = models.CharField(max_length=100)
    base_risk         = models.FloatField(default=0.0)
    propagated_risk   = models.FloatField(default=0.0)
    amplification     = models.FloatField(default=0.0,
        help_text="propagated_risk - base_risk")
    predicted_delay_days = models.IntegerField(default=0)
    task_count        = models.IntegerField(default=0)

    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bid_dept_risk_propagation'
        unique_together = [('tender', 'department_name')]
        ordering = ['-propagated_risk']

    def __str__(self):
        return (f"{self.tender_id} | {self.department_name}: "
                f"{self.base_risk:.0%} → {self.propagated_risk:.0%}")


class BidReadinessSnapshot(models.Model):
    """
    Periodic snapshot of bid readiness index for a tender.
    Enables trend tracking over time.
    """
    tender = models.ForeignKey(
        Tender,
        on_delete=models.CASCADE,
        related_name='readiness_snapshots',
        db_constraint=False,
    )
    readiness_index   = models.FloatField(default=0.0,
        help_text="Overall readiness 0-100")
    data_readiness    = models.FloatField(default=0.0,
        help_text="Data completeness score 0-100")
    task_completion   = models.FloatField(default=0.0,
        help_text="Action item completion 0-100")
    total_actions     = models.IntegerField(default=0)
    completed_actions = models.IntegerField(default=0)
    critical_pending  = models.IntegerField(default=0)
    total_exposure    = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bid_readiness_snapshot'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tender', '-created_at']),
        ]

    def __str__(self):
        return f"{self.tender_id} — {self.readiness_index:.1f}% ready @ {self.created_at:%Y-%m-%d}"


# ─────────────────────────────────────────────────────────────────────────────
# BOQ BID QUOTATION MODEL
# ─────────────────────────────────────────────────────────────────────────────

class BidBOQ(models.Model):
    """
    Contractor's quoted rates for tender BOQ items.
    Used for BOQ comparison and gap analysis.
    """
    tender_work_item = models.ForeignKey(
        TenderWorkItem,
        on_delete=models.CASCADE,
        related_name='bid_quotes',
        help_text="Reference to tender BOQ item"
    )
    tender = models.ForeignKey(
        Tender,
        on_delete=models.CASCADE,
        related_name='bid_boq_items',
        db_constraint=False,
    )

    # Quoted Rates
    quoted_rate = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Contractor's quoted unit rate"
    )
    quoted_total = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Quoted rate × quantity"
    )

    # Breakdown (optional)
    quoted_material_cost = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    quoted_labor_cost = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    quoted_equipment_cost = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )

    # Analysis
    gap_percentage = models.FloatField(
        default=0.0,
        help_text="% difference from tender estimate"
    )
    is_risky = models.BooleanField(
        default=False,
        help_text="Gap exceeds threshold (±15%)"
    )

    # Notes
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bid_boq'
        unique_together = [('tender', 'tender_work_item')]
        ordering = ['tender_work_item__item_code']

    def __str__(self):
        return f"Bid BOQ: {self.tender_work_item.item_code} @ ₹{self.quoted_rate}"


# ─────────────────────────────────────────────────────────────────────────────
# BUYER BID EVALUATION MODELS
# ─────────────────────────────────────────────────────────────────────────────

class Vendor(models.Model):
    """Vendor / bidder participating in a tender"""
    name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100, null=True, blank=True)
    financial_rating = models.FloatField(default=0.5,
        help_text="Financial stability score 0-1")
    past_performance_score = models.FloatField(default=0.5,
        help_text="Historical performance score 0-1")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'buyer_vendor'
        ordering = ['name']

    def __str__(self):
        return self.name


class VendorBid(models.Model):
    """One bid submission per vendor per round for a tender"""
    ROUND_CHOICES = [
        (1, 'Round 1 (Initial Bid)'),
        (2, 'Round 2'),
        (3, 'Round 3'),
        (4, 'BAFO (Best and Final Offer)'),
    ]

    tender = models.ForeignKey(
        Tender, on_delete=models.CASCADE,
        related_name='vendor_bids', db_constraint=False
    )
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE,
        related_name='bids', db_constraint=False
    )
    round_number = models.IntegerField(choices=ROUND_CHOICES, default=1)

    # Financials
    total_price = models.FloatField()
    technical_score = models.FloatField(default=0.0,
        help_text="Technical evaluation score 0-100")
    commercial_score = models.FloatField(default=0.0,
        help_text="Commercial score 0-100")
    legal_risk_score = models.FloatField(default=0.0,
        help_text="Legal deviation risk 0-1")
    delay_probability = models.FloatField(default=0.0,
        help_text="Predicted delay probability 0-1")
    deviation_score = models.FloatField(default=0.0,
        help_text="Overall clause deviation 0-1")

    submitted_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'buyer_vendor_bid'
        unique_together = [('tender', 'vendor', 'round_number')]
        ordering = ['vendor', 'round_number']

    def __str__(self):
        return f"{self.vendor.name} – R{self.round_number} – ₹{self.total_price:,.0f}"


class VendorClause(models.Model):
    """Clause submitted / deviated by a vendor in a bid"""
    CLAUSE_TYPE_CHOICES = [
        ('PAYMENT_TERMS',      'Payment Terms'),
        ('LIQUIDATED_DAMAGES', 'Liquidated Damages'),
        ('INDEMNITY',          'Indemnity'),
        ('LIABILITY',          'Liability Cap'),
        ('ARBITRATION',        'Arbitration'),
        ('TERMINATION',        'Termination'),
        ('FORCE_MAJEURE',      'Force Majeure'),
        ('WARRANTY',           'Warranty'),
        ('GOVERNING_LAW',      'Governing Law'),
        ('PERFORMANCE_BOND',   'Performance Bond'),
        ('OTHER',              'Other'),
    ]

    vendor_bid = models.ForeignKey(
        VendorBid, on_delete=models.CASCADE,
        related_name='clauses', db_constraint=False
    )
    clause_type = models.CharField(max_length=60, choices=CLAUSE_TYPE_CHOICES)
    clause_text = models.TextField()
    deviation_score = models.FloatField(default=0.0,
        help_text="Semantic deviation from tender baseline 0-1")
    risk_score = models.FloatField(default=0.0,
        help_text="Clause-level risk 0-1")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'buyer_vendor_clause'
        ordering = ['-deviation_score']

    def __str__(self):
        return f"{self.vendor_bid} – {self.clause_type}"


class TenderLegalMetadata(models.Model):
    """Structured legal clause metadata extracted from a tender"""
    CLAUSE_TYPE_CHOICES = VendorClause.CLAUSE_TYPE_CHOICES

    tender = models.ForeignKey(
        Tender, on_delete=models.CASCADE,
        related_name='legal_metadata', db_constraint=False
    )
    clause_type = models.CharField(max_length=60, choices=CLAUSE_TYPE_CHOICES)
    clause_title = models.CharField(max_length=255)
    clause_text = models.TextField()
    risk_weight = models.FloatField(default=0.5)
    financial_impact = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'buyer_tender_legal_metadata'
        ordering = ['-risk_weight']

    def __str__(self):
        return f"{self.tender_id} – {self.clause_type}"
