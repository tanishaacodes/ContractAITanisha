import uuid
from django.db import models
import bcrypt


def generate_uuid():
    """Generate UUID for model primary keys"""
    return str(uuid.uuid4())


class Role(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    permissions = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'roles'
        ordering = ['name']

    def __str__(self):
        return self.name


class PricingPlan(models.Model):
    """
    Pricing plans for subscription tiers.
    Defines contract limits and feature access for each plan.
    """
    PLAN_TYPE_CHOICES = [
        ('FREE', 'Free'),
        ('STANDARD', 'Standard'),
        ('PROFESSIONAL', 'Professional'),
        ('ENTERPRISE', 'Enterprise'),
        ('ON_PREMISE', 'On-Premise'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text='Plan name (e.g., Free, Standard, Professional)')
    display_name = models.CharField(max_length=100, db_column='displayName', help_text='Display name for UI')
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, unique=True, db_column='planType')

    # Pricing
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0, db_column='priceMonthly', help_text='Monthly price in USD')

    # Limits
    contract_limit = models.IntegerField(db_column='contractLimit', help_text='Maximum contracts allowed (-1 for unlimited)')

    # Features (JSON)
    features = models.JSONField(default=list, help_text='List of features included in this plan')
    feature_flags = models.JSONField(default=dict, db_column='featureFlags', help_text='Feature toggles: {"analyse_risks": true, "analyse_intents": false, ...}')

    # Plan metadata
    description = models.TextField(blank=True, null=True, help_text='Plan description for display')
    is_active = models.BooleanField(default=True, db_column='isActive', help_text='Whether this plan is available for selection')
    is_contact_sales = models.BooleanField(default=False, db_column='isContactSales', help_text='Whether this requires contacting sales')
    sort_order = models.IntegerField(default=0, db_column='sortOrder', help_text='Display order (lower = first)')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'pricing_plans'
        ordering = ['sort_order', 'price_monthly']

    def __str__(self):
        return f"{self.display_name} (${self.price_monthly}/mo)"


class User(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    first_name = models.CharField(max_length=100, blank=True, null=True, db_column='firstName')
    last_name = models.CharField(max_length=100, blank=True, null=True, db_column='lastName')
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='users', db_column='roleId')
    current_plan = models.ForeignKey(PricingPlan, on_delete=models.PROTECT, related_name='users', db_column='currentPlanId', null=True, blank=True)
    total_contracts_uploaded = models.IntegerField(default=0, db_column='totalContractsUploaded', help_text='Lifetime count of contracts uploaded (never decreases)')
    is_active = models.BooleanField(default=True, db_column='isActive')
    last_login = models.DateTimeField(blank=True, null=True, db_column='lastLogin')

    # Connector Permissions (Only SuperAdmin can assign these)
    fivetran_access = models.BooleanField(default=False, db_column='fivetranAccess', help_text='User has access to Fivetran connector features')
    kafka_access = models.BooleanField(default=False, db_column='kafkaAccess', help_text='User has access to Kafka connector features')
    sap_access = models.BooleanField(default=False, db_column='sapAccess', help_text='User has access to SAP S/4HANA integration features')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    # Required for Django authentication system
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # email is already the USERNAME_FIELD, so it's not needed here

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return self.email

    def set_password(self, raw_password):
        """Hash and set password using bcrypt"""
        salt = bcrypt.gensalt(rounds=10)
        self.password = bcrypt.hashpw(raw_password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, raw_password):
        """Verify password against bcrypt hash"""
        return bcrypt.checkpw(raw_password.encode('utf-8'), self.password.encode('utf-8'))

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def save(self, *args, **kwargs):
        """Hash password before saving if it's not already hashed"""
        if self.password and not self.password.startswith('$2'):
            self.set_password(self.password)
        super().save(*args, **kwargs)


class Contract(models.Model):
    """📌 UPDATED: Added contract_value, party_name, contract_duration, jurisdiction, payment_terms, liability_level, has_arbitration"""

    LIABILITY_CHOICES = [
        ('LOW', 'Low Liability'),
        ('MEDIUM', 'Medium Liability'),
        ('HIGH', 'High Liability'),
    ]

    # ✅ UPDATED: Enhanced workflow stages for role-based approvals
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('LEGAL_REVIEW', 'Legal Review'),
        ('BUSINESS_REVIEW', 'Business Review'),
        ('COMPLIANCE_REVIEW', 'Compliance Review'),
        ('FINAL_APPROVAL', 'Final Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contracts', db_column='userId')
    assigned_by = models.CharField(max_length=36, null=True, blank=True, db_column='assignedBy', help_text='ID of user who assigned this contract')

    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255, db_column='originalFilename')
    file_type = models.CharField(max_length=50, db_column='fileType')
    file_path = models.TextField(db_column='filePath')

    full_text = models.TextField(blank=True, null=True, db_column='fullText')
    contract_type = models.CharField(max_length=100, blank=True, null=True, db_column='contractType')

    # NOT displayed in UI anymore but kept for backend compatibility
    confidence_score = models.FloatField(blank=True, null=True, db_column='confidenceScore')

    # ✅ FUSION CLASSIFICATION RESULTS (BERTopic + Contracts-BERT)
    bert_topics = models.JSONField(blank=True, null=True, db_column='bertTopics', help_text='BERTopic classification results')
    bert_intents = models.JSONField(blank=True, null=True, db_column='bertIntents', help_text='Contracts-BERT intent distribution')
    fused_scores = models.JSONField(blank=True, null=True, db_column='fusedScores', help_text='All contract type scores from fusion')

    ocr_performed = models.BooleanField(default=False, db_column='ocrPerformed')

    # ✅ NEW FIELDS YOU REQUESTED
    contract_value = models.CharField(max_length=100, null=True, blank=True, db_column='contractValue')
   # OLD (kept for backward compatibility)
    party_name = models.CharField(max_length=255, null=True, blank=True, db_column='partyName')
    contract_duration = models.CharField(max_length=100, null=True, blank=True, db_column='contractDuration')

# ✅ NEW FIELDS (THIS IS WHAT UI NEEDS)
    party_a = models.CharField(max_length=255, null=True, blank=True, db_column='partyA')
    party_b = models.CharField(max_length=255, null=True, blank=True, db_column='partyB')

    # Contract Intelligence Maps fields
    business_unit = models.CharField(max_length=100, null=True, blank=True)
    version = models.IntegerField(default=1)
    version_date = models.DateTimeField(null=True, blank=True)
    total_liability = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    start_date = models.DateField(null=True, blank=True, db_column='startDate')
    end_date = models.DateField(null=True, blank=True, db_column='endDate')

    # ✅ NEW SEARCHABLE FIELDS FOR CONTRACT SEARCH
    jurisdiction = models.CharField(max_length=200, null=True, blank=True, help_text='Contract jurisdiction (e.g., Dubai, USA, UK)')
    payment_terms = models.CharField(max_length=500, null=True, blank=True, db_column='paymentTerms', help_text='Payment terms (e.g., NET 30, Upon delivery)')
    liability_level = models.CharField(max_length=20, choices=LIABILITY_CHOICES, null=True, blank=True, db_column='liabilityLevel', help_text='Liability level classification')
    has_arbitration = models.BooleanField(default=False, db_column='hasArbitration', help_text='Whether contract includes arbitration clause')
    project_location = models.CharField(max_length=300, null=True, blank=True, db_column='projectLocation', help_text='Project site/location where work is performed')
    supplier_locations = models.TextField(null=True, blank=True, db_column='supplierLocations', help_text='Comma-separated list of supplier countries/locations')

    # ✅ CONTRACT WORKFLOW STATUS
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', help_text='Contract workflow status')

    # ✅ COUNTERPARTY LINKAGE FOR PORTFOLIO RISK ANALYSIS
    counterparty = models.ForeignKey(
        'negotiation.Counterparty',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contracts',
        db_column='counterpartyId',
        help_text='Linked counterparty for portfolio-level risk analysis'
    )

    uploaded_at = models.DateTimeField(auto_now_add=True, db_column='uploadedAt')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'contracts'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', '-uploaded_at']),
        ]

    def __str__(self):
        return f"{self.original_filename} ({self.user.email})"

    def can_transition_to(self, new_status):
        """
        Validate if contract can transition to the new status.

        ✅ UPDATED Transition Rules for Role-Based Approvals:
        - DRAFT → LEGAL_REVIEW
        - LEGAL_REVIEW → BUSINESS_REVIEW, REJECTED
        - BUSINESS_REVIEW → COMPLIANCE_REVIEW, REJECTED
        - COMPLIANCE_REVIEW → FINAL_APPROVAL, REJECTED
        - FINAL_APPROVAL → APPROVED, REJECTED
        - APPROVED/REJECTED → (no transitions allowed)
        """
        ALLOWED_TRANSITIONS = {
            'DRAFT': ['LEGAL_REVIEW'],
            'LEGAL_REVIEW': ['BUSINESS_REVIEW', 'REJECTED'],
            'BUSINESS_REVIEW': ['COMPLIANCE_REVIEW', 'REJECTED'],
            'COMPLIANCE_REVIEW': ['FINAL_APPROVAL', 'REJECTED'],
            'FINAL_APPROVAL': ['APPROVED', 'REJECTED'],
            'APPROVED': [],
            'REJECTED': [],
        }

        return new_status in ALLOWED_TRANSITIONS.get(self.status, [])


class Clause(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='clauses', db_column='contractId')
    clause_name = models.CharField(max_length=150, db_column='clauseName')
    found = models.BooleanField(default=False)
    confidence = models.FloatField(blank=True, null=True)
    match_count = models.IntegerField(blank=True, null=True, db_column='matchCount')
    text_spans = models.TextField(blank=True, null=True, db_column='textSpans')
    context_sentences = models.TextField(blank=True, null=True, db_column='contextSentences')
    extracted_text = models.TextField(blank=True, null=True, db_column='extractedText')

    # Clause Library Integration Fields
    clause_type = models.CharField(max_length=255, blank=True, null=True, db_column='clauseType',
                                   help_text='AI-generated clause category (e.g., Payment Terms, Liability)')
    clause_label = models.CharField(max_length=255, blank=True, null=True, db_column='clauseLabel',
                                    help_text='Cluster label for grouped similar clauses')
    embedding_id = models.CharField(max_length=255, blank=True, null=True, db_column='embeddingId',
                                    help_text='Reference ID for vector embedding in Qdrant')

    # Enhanced Clause Library Fields (from PDF requirements)
    sentence_type = models.CharField(
        max_length=50, blank=True, null=True, db_column='sentenceType',
        choices=[
            ('HEADING', 'Heading'),
            ('DEFINITION', 'Definition'),
            ('OBLIGATION', 'Obligation'),
            ('RISK', 'Risk'),
            ('RIGHT', 'Right'),
        ],
        help_text='Sentence classification: Heading, Definition, Obligation, Risk, or Right'
    )
    party = models.CharField(
        max_length=50, blank=True, null=True, db_column='party',
        choices=[
            ('CONTRACTOR', 'Contractor'),
            ('EMPLOYER', 'Employer'),
            ('SHARED', 'Shared'),
        ],
        help_text='Party attribution: Contractor, Employer, or Shared'
    )
    cluster_id = models.IntegerField(
        blank=True, null=True, db_column='clusterId',
        help_text='Numeric cluster ID from KMeans clustering'
    )
    financial_impact = models.FloatField(
        blank=True, null=True, db_column='financialImpact',
        help_text='Calculated financial impact in currency (risk_score × ₹100,000)'
    )
    keywords = models.JSONField(
        default=dict, blank=True, db_column='keywords',
        help_text='Risk keywords detected and their weights (e.g., {"liability": 5, "penalty": 4})'
    )

    # Risk Analysis Fields
    risk_score = models.FloatField(
        blank=True, null=True, db_column='riskScore',
        help_text='Enriched risk score from ClauseRiskEnricher (0-1)'
    )
    risk_level = models.CharField(
        max_length=20, blank=True, null=True, db_column='riskLevel',
        choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')],
        help_text='Risk severity classification'
    )
    risk_factors = models.JSONField(
        default=dict, blank=True, db_column='riskFactors',
        help_text='Detailed risk factors from enrichment'
    )
    likelihood_score = models.FloatField(
        blank=True, null=True, db_column='likelihoodScore',
        help_text='Probability of risk occurrence (1-5)'
    )
    impact_score = models.FloatField(
        blank=True, null=True, db_column='impactScore',
        help_text='Severity of risk impact (1-5)'
    )
    enriched_at = models.DateTimeField(
        blank=True, null=True, db_column='enrichedAt',
        help_text='When risk enrichment was performed'
    )

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'clauses'
        ordering = ['-confidence']
        indexes = [
            models.Index(fields=['contract', 'clause_name']),
            models.Index(fields=['contract']),
            models.Index(fields=['clause_type']),
            models.Index(fields=['embedding_id']),
            models.Index(fields=['risk_level', '-risk_score']),
            models.Index(fields=['likelihood_score', 'impact_score']),
            models.Index(fields=['clause_type', 'risk_level']),
            # New indexes for enhanced clause library
            models.Index(fields=['sentence_type', 'party'], name='clause_sent_party_idx'),
            models.Index(fields=['cluster_id'], name='clause_cluster_idx'),
        ]

    def __str__(self):
        return f"{self.clause_name} ({self.contract.original_filename})"


class ClauseVersion(models.Model):
    """Track version history of clause edits"""
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    clause = models.ForeignKey(Clause, on_delete=models.CASCADE, related_name='versions', db_column='clauseId')
    version_number = models.IntegerField(db_column='versionNumber', help_text='Sequential version number')
    original_text = models.TextField(db_column='originalText', help_text='Text before this edit')
    modified_text = models.TextField(db_column='modifiedText', help_text='Text after this edit')
    change_description = models.TextField(blank=True, null=True, db_column='changeDescription',
                                          help_text='User explanation of what was changed')

    # Risk scores after modification
    new_risk_score = models.FloatField(blank=True, null=True, db_column='newRiskScore')
    new_risk_level = models.CharField(max_length=20, blank=True, null=True, db_column='newRiskLevel')
    new_likelihood_score = models.FloatField(blank=True, null=True, db_column='newLikelihoodScore')
    new_impact_score = models.FloatField(blank=True, null=True, db_column='newImpactScore')

    modified_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='clause_edits', db_column='modifiedBy')
    modified_at = models.DateTimeField(auto_now_add=True, db_column='modifiedAt')

    # Approval workflow
    approved_by_id = models.CharField(max_length=36, blank=True, null=True, db_column='approvedBy',
                                      help_text='User ID who approved this change')
    approved_at = models.DateTimeField(null=True, blank=True, db_column='approvedAt')

    class Meta:
        db_table = 'clause_versions'
        ordering = ['-version_number']
        unique_together = [['clause', 'version_number']]
        indexes = [
            models.Index(fields=['clause', '-version_number']),
            models.Index(fields=['modified_by', '-modified_at']),
        ]

    def __str__(self):
        return f"{self.clause.clause_name} v{self.version_number}"


class TemplateClause(models.Model):
    IMPORTANCE_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('IMPORTANT', 'Important'),
        ('OPTIONAL', 'Optional'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract_type = models.CharField(max_length=100, db_column='contractType')
    clause_name = models.CharField(max_length=150, db_column='clauseName')
    importance = models.CharField(max_length=20, choices=IMPORTANCE_CHOICES, default='IMPORTANT')
    description = models.TextField(blank=True, null=True)
    standard_language = models.TextField(blank=True, null=True, db_column='standardLanguage')
    risk_keywords = models.JSONField(default=list, blank=True, db_column='riskKeywords')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'template_clauses'
        unique_together = ['contract_type', 'clause_name']
        ordering = ['contract_type', 'importance', 'clause_name']

    def __str__(self):
        return f"{self.contract_type} - {self.clause_name} ({self.importance})"


class ContractRiskAnalysis(models.Model):
    RISK_LEVEL_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.OneToOneField(Contract, on_delete=models.CASCADE, related_name='risk_analysis', db_column='contractId')
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, db_column='riskLevel')
    risk_score = models.IntegerField(default=0, db_column='riskScore')
    total_deviations = models.IntegerField(default=0, db_column='totalDeviations')
    critical_issues = models.IntegerField(default=0, db_column='criticalIssues')
    medium_issues = models.IntegerField(default=0, db_column='mediumIssues')
    low_issues = models.IntegerField(default=0, db_column='lowIssues')
    analysis_summary = models.TextField(blank=True, null=True, db_column='analysisSummary')
    executive_summary = models.TextField(blank=True, null=True, db_column='executiveSummary')
    summary_generated_at = models.DateTimeField(blank=True, null=True, db_column='summaryGeneratedAt')
    # New risk scoring model fields
    category_breakdown = models.JSONField(default=dict, blank=True, null=True, db_column='categoryBreakdown')
    detailed_breakdown = models.JSONField(default=dict, blank=True, null=True, db_column='detailedBreakdown')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'contract_risk_analysis'

    def __str__(self):
        return f"{self.contract.original_filename} - {self.risk_level}"


class ClauseDeviation(models.Model):
    SEVERITY_CHOICES = [
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]

    DEVIATION_TYPE_CHOICES = [
        ('MISSING', 'Missing Clause'),
        ('UNFAVORABLE', 'Unfavorable Terms'),
        ('WEAK', 'Weak Protection'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('ACCEPTED', 'Suggestion Accepted'),
        ('REJECTED', 'Suggestion Rejected'),
        ('MODIFIED', 'Manually Modified'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    risk_analysis = models.ForeignKey(ContractRiskAnalysis, on_delete=models.CASCADE, related_name='deviations', db_column='riskAnalysisId')
    clause_name = models.CharField(max_length=150, db_column='clauseName')
    deviation_type = models.CharField(max_length=20, choices=DEVIATION_TYPE_CHOICES, db_column='deviationType')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField()
    recommendation = models.TextField(blank=True, null=True)

    # Fields for tracking accepted suggestions
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    suggested_text = models.TextField(blank=True, null=True, db_column='suggestedText')
    accepted_text = models.TextField(blank=True, null=True, db_column='acceptedText')
    accepted_at = models.DateTimeField(null=True, blank=True, db_column='acceptedAt')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'clause_deviations'
        ordering = ['-severity', 'clause_name']

    def __str__(self):
        return f"{self.clause_name} - {self.severity} ({self.deviation_type})"


class ContractVersion(models.Model):
    """Store historical versions of contracts for version tracking"""
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='versions', db_column='contractId')

    # Version metadata
    version_number = models.IntegerField(db_column='versionNumber')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='contract_versions', db_column='createdBy')
    change_description = models.TextField(blank=True, null=True, db_column='changeDescription')

    # Snapshot of contract data at this version
    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255, db_column='originalFilename')
    file_type = models.CharField(max_length=50, db_column='fileType')
    file_path = models.TextField(db_column='filePath')
    full_text = models.TextField(blank=True, null=True, db_column='fullText')
    contract_type = models.CharField(max_length=100, blank=True, null=True, db_column='contractType')
    contract_value = models.CharField(max_length=100, null=True, blank=True, db_column='contractValue')
    party_name = models.CharField(max_length=255, null=True, blank=True, db_column='partyName')
    contract_duration = models.CharField(max_length=100, null=True, blank=True, db_column='contractDuration')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'contract_versions'
        ordering = ['-version_number']
        unique_together = ['contract', 'version_number']
        indexes = [
            models.Index(fields=['contract', '-version_number']),
        ]

    def __str__(self):
        return f"{self.contract.original_filename} - v{self.version_number}"


class ContractObligation(models.Model):
    CATEGORY_CHOICES = [
        ('PAYMENT', 'Payment'),
        ('DELIVERY', 'Delivery'),
        ('COMPLIANCE', 'Compliance'),
        ('REPORTING', 'Reporting'),
        ('NOTICE', 'Notice'),
        ('TERMINATION', 'Termination'),
        ('OTHER', 'Other'),
    ]

    PARTY_CHOICES = [
        ('YOUR_COMPANY', 'Your Company'),
        ('COUNTERPARTY', 'Counterparty'),
        ('BOTH', 'Both Parties'),
    ]

    PRIORITY_CHOICES = [
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='obligations', db_column='contractId')
    title = models.CharField(max_length=500)
    description = models.TextField()
    full_text = models.TextField(blank=True, null=True, db_column='fullText')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    responsible_party = models.CharField(max_length=50, choices=PARTY_CHOICES, db_column='responsibleParty')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    due_date_text = models.CharField(max_length=200, blank=True, null=True, db_column='dueDateText')
    clause_reference = models.CharField(max_length=200, blank=True, null=True, db_column='clauseReference')
    is_completed = models.BooleanField(default=False, db_column='isCompleted')
    completed_at = models.DateTimeField(blank=True, null=True, db_column='completedAt')
    completion_notes = models.TextField(blank=True, null=True, db_column='completionNotes')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now_add=True, db_column='updatedAt')

    class Meta:
        db_table = 'contract_obligations'
        ordering = ['-priority', 'responsible_party', 'category']

    def __str__(self):
        return f"{self.title} ({self.responsible_party})"


# =========================
# INTENT MINING MODELS
# =========================

class Intent(models.Model):
    """
    Stores discovered legal intents across all contracts.
    Intents are auto-discovered and normalized (e.g., "Payment Obligation", "Termination Rights")
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    name = models.CharField(max_length=200, unique=True, help_text='Canonical intent name')
    description = models.TextField(help_text='What this intent means in legal context')
    confidence = models.FloatField(default=0.0, help_text='Overall confidence score for this intent')
    occurrence_count = models.IntegerField(default=0, db_column='occurrenceCount', help_text='Number of clauses with this intent')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'intents'
        ordering = ['-occurrence_count', 'name']

    def __str__(self):
        return f"{self.name} ({self.occurrence_count} occurrences)"


class ClauseIntent(models.Model):
    """
    Links clauses to their discovered intents with confidence scores.
    Each clause can have multiple intents with different confidence levels.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    clause = models.ForeignKey(Clause, on_delete=models.CASCADE, related_name='clause_intents')
    intent = models.ForeignKey(Intent, on_delete=models.CASCADE, related_name='clause_intents')
    contract_version = models.ForeignKey(
        'ContractVersion',
        on_delete=models.CASCADE,
        related_name='clause_intents',
        db_column='contractVersionId',
        null=True,
        blank=True,
        help_text='Contract version this intent was discovered in'
    )
    confidence = models.FloatField(help_text='Confidence score for this intent assignment (0-1)')
    is_primary = models.BooleanField(default=False, db_column='isPrimary', help_text='Is this the primary intent for the clause')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'clause_intents'
        unique_together = ['clause', 'intent']
        ordering = ['-confidence']
        indexes = [
            models.Index(fields=['clause', '-confidence']),
            models.Index(fields=['intent']),
            models.Index(fields=['contract_version', '-confidence'], name='clauseintent_version_conf_idx'),
        ]

    def __str__(self):
        return f"{self.clause.clause_name} -> {self.intent.name} ({self.confidence:.2f})"


class IntentObligation(models.Model):
    """
    Obligations extracted from clauses, linked to intents.
    More refined than ContractObligation - intent-aware.
    """
    PARTY_CHOICES = [
        ('YOUR_COMPANY', 'Your Company'),
        ('COUNTERPARTY', 'Counterparty'),
        ('BOTH', 'Both Parties'),
    ]

    PRIORITY_CHOICES = [
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    clause = models.ForeignKey(Clause, on_delete=models.CASCADE, related_name='intent_obligations')
    intent = models.ForeignKey(Intent, on_delete=models.CASCADE, related_name='obligations')
    contract_version = models.ForeignKey(
        'ContractVersion',
        on_delete=models.CASCADE,
        related_name='intent_obligations',
        db_column='contractVersionId',
        null=True,
        blank=True,
        help_text='Contract version this obligation was extracted from'
    )
    party = models.CharField(max_length=50, choices=PARTY_CHOICES)
    action = models.TextField(help_text='What must be done')
    condition = models.TextField(blank=True, null=True, help_text='Under what conditions')
    deadline = models.CharField(max_length=200, blank=True, null=True, help_text='When it must be done')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    risk_score = models.FloatField(default=0.0, db_column='riskScore', help_text='Risk score for this obligation (0-1)')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'intent_obligations'
        ordering = ['-risk_score', '-priority', 'party']
        indexes = [
            models.Index(fields=['clause']),
            models.Index(fields=['intent']),
            models.Index(fields=['-risk_score']),
            models.Index(fields=['contract_version', '-risk_score'], name='intentobl_version_risk_idx'),
        ]

    def __str__(self):
        return f"{self.party}: {self.action[:50]}..."


class IntentRight(models.Model):
    """
    Rights extracted from clauses, linked to intents.
    Represents what parties are entitled to do.
    """
    PARTY_CHOICES = [
        ('YOUR_COMPANY', 'Your Company'),
        ('COUNTERPARTY', 'Counterparty'),
        ('BOTH', 'Both Parties'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    clause = models.ForeignKey(Clause, on_delete=models.CASCADE, related_name='intent_rights')
    intent = models.ForeignKey(Intent, on_delete=models.CASCADE, related_name='rights')
    contract_version = models.ForeignKey(
        'ContractVersion',
        on_delete=models.CASCADE,
        related_name='intent_rights',
        db_column='contractVersionId',
        null=True,
        blank=True,
        help_text='Contract version this right was extracted from'
    )
    party = models.CharField(max_length=50, choices=PARTY_CHOICES)
    entitlement = models.TextField(help_text='What the party may do')
    trigger = models.TextField(blank=True, null=True, help_text='What triggers this right')
    risk_score = models.FloatField(default=0.0, db_column='riskScore', help_text='Risk score for this right (0-1)')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'intent_rights'
        ordering = ['-risk_score', 'party']
        indexes = [
            models.Index(fields=['clause']),
            models.Index(fields=['intent']),
            models.Index(fields=['-risk_score']),
            models.Index(fields=['contract_version', '-risk_score'], name='intentright_version_risk_idx'),
        ]

    def __str__(self):
        return f"{self.party}: {self.entitlement[:50]}..."


class ComplianceFramework(models.Model):
    """
    Master table for compliance frameworks (GDPR, SOX, HIPAA, GST).
    Each framework represents a regulatory standard.
    """
    FRAMEWORK_CHOICES = [
        ('GDPR', 'General Data Protection Regulation'),
        ('SOX', 'Sarbanes-Oxley Act'),
        ('HIPAA', 'Health Insurance Portability and Accountability Act'),
        ('GST', 'Goods and Services Tax / Tax Laws'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    code = models.CharField(max_length=20, unique=True, choices=FRAMEWORK_CHOICES, help_text='Framework code (GDPR, SOX, HIPAA, GST)')
    name = models.CharField(max_length=200, help_text='Full framework name')
    description = models.TextField(help_text='What this framework regulates')
    jurisdiction = models.CharField(max_length=100, blank=True, null=True, help_text='Primary jurisdiction (e.g., EU, USA, Global)')
    effective_date = models.DateField(blank=True, null=True, db_column='effectiveDate', help_text='Date framework came into effect')
    version = models.CharField(max_length=50, blank=True, null=True, help_text='Framework version/year')
    is_active = models.BooleanField(default=True, db_column='isActive', help_text='Whether to check this framework')
    priority = models.IntegerField(default=1, help_text='Priority order for checking (1=highest)')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'compliance_frameworks'
        ordering = ['priority', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class ComplianceRequirement(models.Model):
    """
    Specific requirements within each compliance framework.
    E.g., GDPR Article 6 (Lawful basis), GDPR Article 17 (Right to erasure).
    """
    CRITICALITY_CHOICES = [
        ('CRITICAL', 'Critical - Legal mandate'),
        ('HIGH', 'High - Strong requirement'),
        ('MEDIUM', 'Medium - Standard requirement'),
        ('LOW', 'Low - Best practice'),
    ]

    REQUIREMENT_TYPE_CHOICES = [
        ('DATA_PROTECTION', 'Data Protection'),
        ('FINANCIAL_CONTROLS', 'Financial Controls'),
        ('HEALTH_DATA', 'Health Data Privacy'),
        ('TAX_COMPLIANCE', 'Tax Compliance'),
        ('CONSENT', 'Consent Requirements'),
        ('SECURITY', 'Security Measures'),
        ('RETENTION', 'Data Retention'),
        ('BREACH_NOTIFICATION', 'Breach Notification'),
        ('AUDIT', 'Audit Requirements'),
        ('REPORTING', 'Reporting Obligations'),
        ('OTHER', 'Other'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    framework = models.ForeignKey(ComplianceFramework, on_delete=models.CASCADE, related_name='requirements', db_column='frameworkId')

    requirement_code = models.CharField(max_length=100, db_column='requirementCode', help_text='Official code (e.g., GDPR Art. 6, SOX Section 404)')
    requirement_name = models.CharField(max_length=300, db_column='requirementName', help_text='Short requirement name')
    description = models.TextField(help_text='Full description of what must be done')

    requirement_type = models.CharField(max_length=50, choices=REQUIREMENT_TYPE_CHOICES, db_column='requirementType', help_text='Category of requirement')
    criticality = models.CharField(max_length=20, choices=CRITICALITY_CHOICES, help_text='How critical is compliance with this requirement')

    detection_keywords = models.JSONField(default=list, db_column='detectionKeywords', help_text='Keywords that suggest this requirement applies')

    risk_weight = models.FloatField(default=1.0, db_column='riskWeight', help_text='Multiplier for risk calculations (0.1-2.0)')
    compliance_score_weight = models.FloatField(default=1.0, db_column='complianceScoreWeight', help_text='Weight in overall compliance score')

    legal_reference = models.TextField(blank=True, null=True, db_column='legalReference', help_text='Link to official documentation')

    is_active = models.BooleanField(default=True, db_column='isActive')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'compliance_requirements'
        unique_together = ['framework', 'requirement_code']
        ordering = ['-criticality', 'requirement_code']
        indexes = [
            models.Index(fields=['framework', 'is_active']),
            models.Index(fields=['requirement_type']),
        ]

    def __str__(self):
        return f"{self.framework.code} - {self.requirement_code}: {self.requirement_name}"


class IntentComplianceMapping(models.Model):
    """
    Links discovered intents to compliance requirements.
    Automatically detected by LLM with confidence scoring.
    """
    COMPLIANCE_STATUS_CHOICES = [
        ('COMPLIANT', 'Fully Compliant'),
        ('PARTIAL', 'Partially Compliant'),
        ('NON_COMPLIANT', 'Non-Compliant'),
        ('NOT_APPLICABLE', 'Not Applicable'),
        ('NEEDS_REVIEW', 'Needs Manual Review'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)

    intent = models.ForeignKey(Intent, on_delete=models.CASCADE, related_name='compliance_mappings', db_column='intentId')
    requirement = models.ForeignKey(ComplianceRequirement, on_delete=models.CASCADE, related_name='intent_mappings', db_column='requirementId')
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='compliance_mappings', db_column='contractId', help_text='Contract this mapping applies to')

    relevance_score = models.FloatField(db_column='relevanceScore', help_text='LLM confidence that requirement applies (0-1)')
    compliance_status = models.CharField(max_length=20, choices=COMPLIANCE_STATUS_CHOICES, db_column='complianceStatus', help_text='Whether intent meets the requirement')

    analysis_summary = models.TextField(db_column='analysisSummary', help_text='LLM explanation of why this applies')
    gap_description = models.TextField(blank=True, null=True, db_column='gapDescription', help_text='What is missing or non-compliant')
    recommendation = models.TextField(blank=True, null=True, help_text='How to achieve compliance')

    risk_score = models.FloatField(default=0.0, db_column='riskScore', help_text='Risk score for this non-compliance (0-1)')

    detected_at = models.DateTimeField(auto_now_add=True, db_column='detectedAt')
    last_reviewed_at = models.DateTimeField(blank=True, null=True, db_column='lastReviewedAt')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='compliance_reviews', db_column='reviewedBy')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'intent_compliance_mappings'
        unique_together = ['intent', 'requirement', 'contract']
        ordering = ['-risk_score', '-relevance_score']
        indexes = [
            models.Index(fields=['contract', 'compliance_status']),
            models.Index(fields=['intent', 'relevance_score']),
            models.Index(fields=['requirement']),
            models.Index(fields=['-risk_score']),
        ]

    def __str__(self):
        return f"{self.intent.name} -> {self.requirement.requirement_code} ({self.compliance_status})"


class ContractComplianceAnalysis(models.Model):
    """
    Aggregate compliance analysis for entire contract.
    Stores overall compliance scores and coverage metrics.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.OneToOneField(Contract, on_delete=models.CASCADE, related_name='compliance_analysis', db_column='contractId')

    overall_compliance_score = models.FloatField(default=0.0, db_column='overallComplianceScore', help_text='Weighted compliance score (0-100)')
    total_requirements_checked = models.IntegerField(default=0, db_column='totalRequirementsChecked')
    compliant_count = models.IntegerField(default=0, db_column='compliantCount')
    partial_count = models.IntegerField(default=0, db_column='partialCount')
    non_compliant_count = models.IntegerField(default=0, db_column='nonCompliantCount')

    framework_scores = models.JSONField(default=dict, db_column='frameworkScores', help_text='{"GDPR": {"score": 75.5, "coverage": 80}, ...}')

    compliance_risk_score = models.FloatField(default=0.0, db_column='complianceRiskScore', help_text='Risk score from non-compliance (0-1)')
    critical_violations = models.IntegerField(default=0, db_column='criticalViolations', help_text='Count of critical compliance failures')
    high_violations = models.IntegerField(default=0, db_column='highViolations')
    medium_violations = models.IntegerField(default=0, db_column='mediumViolations')
    low_violations = models.IntegerField(default=0, db_column='lowViolations')

    executive_summary = models.TextField(blank=True, null=True, db_column='executiveSummary', help_text='LLM-generated compliance summary')

    analysis_completed_at = models.DateTimeField(db_column='analysisCompletedAt')
    analysis_duration_seconds = models.FloatField(default=0.0, db_column='analysisDurationSeconds')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'contract_compliance_analysis'
        ordering = ['-analysis_completed_at']

    def __str__(self):
        return f"Compliance Analysis: {self.contract.original_filename} (Score: {self.overall_compliance_score:.1f})"


class ClauseRewriteSuggestion(models.Model):
    """
    AI-generated suggestions for rewriting contract clauses.
    Used by the Negotiation Agent to help users negotiate better terms.
    """
    CATEGORY_CHOICES = [
        ('RISK_REDUCTION', 'Risk Reduction'),
        ('CLARITY_IMPROVEMENT', 'Clarity Improvement'),
        ('FAVORABLE_TERMS', 'More Favorable Terms'),
        ('COMPLIANCE', 'Compliance Enhancement'),
        ('MUTUAL_BENEFIT', 'Mutual Benefit'),
        ('STANDARD_PRACTICE', 'Industry Standard Practice'),
    ]

    PRIORITY_CHOICES = [
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('MODIFIED', 'Modified and Accepted'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    clause = models.ForeignKey(Clause, on_delete=models.CASCADE, related_name='rewrite_suggestions', db_column='clauseId')
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='rewrite_suggestions', db_column='contractId')

    original_text = models.TextField(db_column='originalText', help_text='Original clause text')
    suggested_text = models.TextField(db_column='suggestedText', help_text='Suggested rewrite')
    rationale = models.TextField(help_text='Why this change is recommended')

    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    impact_analysis = models.TextField(blank=True, null=True, db_column='impactAnalysis', help_text='Analysis of how this change affects the contract')
    negotiation_tips = models.TextField(blank=True, null=True, db_column='negotiationTips', help_text='Tips for negotiating this change')

    confidence_score = models.FloatField(default=0.5, db_column='confidenceScore', help_text='AI confidence in suggestion (0-1)')

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='clause_suggestions', db_column='createdBy')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_suggestions', db_column='reviewedBy')
    reviewed_at = models.DateTimeField(blank=True, null=True, db_column='reviewedAt')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'clause_rewrite_suggestions'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['contract', 'status']),
            models.Index(fields=['clause']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Suggestion for {self.clause.clause_name} ({self.category}) - {self.status}"


# =========================
# ROLE-BASED APPROVAL SYSTEM
# =========================

class ApprovalTask(models.Model):
    """
    Represents an approval task that must be completed before contract can progress.
    Enforces role-based authorization - only users with required role can approve.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    # Role types that can be assigned approval tasks
    ROLE_CHOICES = [
        ('LEGAL', 'Legal Reviewer'),
        ('BUSINESS', 'Business Owner'),
        ('COMPLIANCE', 'Compliance Officer'),
        ('ADMIN', 'Administrator'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='approval_tasks', db_column='contractId')

    # Role required for this approval (not specific user)
    role_required = models.CharField(max_length=50, choices=ROLE_CHOICES, db_column='roleRequired', help_text='Role needed to approve')

    # User who completed the approval (assigned when approved/rejected)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approval_tasks_assigned', db_column='assignedTo')

    # Approval status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # Approval comments/reasoning
    comments = models.TextField(blank=True, null=True, help_text='Approver comments or rejection reason')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    approved_at = models.DateTimeField(null=True, blank=True, db_column='approvedAt')

    # Workflow stage this approval belongs to
    workflow_stage = models.CharField(max_length=30, db_column='workflowStage', help_text='Contract stage when task was created')

    class Meta:
        db_table = 'approval_tasks'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['contract', 'status']),
            models.Index(fields=['role_required', 'status']),
            models.Index(fields=['assigned_to', 'status']),
        ]

    def __str__(self):
        return f"{self.role_required} approval for {self.contract.original_filename} - {self.status}"


class ApprovalAudit(models.Model):
    """
    Immutable audit trail for all approval actions.
    Legally required for compliance and court-defensible records.
    """
    ACTION_CHOICES = [
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('REASSIGNED', 'Reassigned'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='approval_audits', db_column='contractId')
    approval_task = models.ForeignKey(ApprovalTask, on_delete=models.CASCADE, related_name='audits', db_column='approvalTaskId')

    # Who performed the action
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approval_audits', db_column='userId')

    # What role they had at the time
    user_role = models.CharField(max_length=50, db_column='userRole', help_text='Role of user at time of action')

    # What they did
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    # Why they did it
    comments = models.TextField(help_text='Audit trail comments')

    # When it happened
    timestamp = models.DateTimeField(auto_now_add=True, help_text='When action was performed')

    # System metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_column='ipAddress', help_text='IP address of approver')
    user_agent = models.CharField(max_length=500, null=True, blank=True, db_column='userAgent', help_text='Browser/client info')

    class Meta:
        db_table = 'approval_audits'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['contract', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['approval_task']),
        ]

    def __str__(self):
        return f"{self.action} by {self.user.email if self.user else 'Unknown'} at {self.timestamp}"


# =========================
# ALFRESCO INTEGRATION & RAG MODELS
# =========================

class AlfrescoDocument(models.Model):
    """
    Stores metadata for documents synced from Alfresco.
    Links Alfresco documents to our Contract model.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)

    # Alfresco specific fields
    alfresco_node_id = models.CharField(max_length=255, unique=True, db_column='alfrescoNodeId', help_text='Alfresco node ID')
    alfresco_folder_id = models.CharField(max_length=255, db_column='alfrescoFolderId', help_text='Parent folder ID in Alfresco')
    alfresco_name = models.CharField(max_length=500, db_column='alfrescoName', help_text='Original name in Alfresco')
    alfresco_content_type = models.CharField(max_length=100, db_column='alfrescoContentType', help_text='MIME type from Alfresco')
    alfresco_properties = models.JSONField(default=dict, db_column='alfrescoProperties', help_text='Metadata from Alfresco')
    alfresco_version = models.CharField(max_length=50, blank=True, null=True, db_column='alfrescoVersion', help_text='Document version in Alfresco')

    # Link to our contract system
    contract = models.OneToOneField(Contract, on_delete=models.CASCADE, related_name='alfresco_doc', db_column='contractId', null=True, blank=True, to_field='id')

    # Sync status
    last_synced_at = models.DateTimeField(db_column='lastSyncedAt', help_text='When document was last synced')
    sync_status = models.CharField(max_length=20, default='SYNCED', db_column='syncStatus',
                                   choices=[('SYNCED', 'Synced'), ('FAILED', 'Failed'), ('PENDING', 'Pending')])
    sync_error = models.TextField(blank=True, null=True, db_column='syncError', help_text='Error message if sync failed')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'alfresco_documents'
        ordering = ['-last_synced_at']
        indexes = [
            models.Index(fields=['alfresco_node_id']),
            models.Index(fields=['alfresco_folder_id']),
            models.Index(fields=['sync_status']),
        ]

    def __str__(self):
        return f"{self.alfresco_name} (Alfresco: {self.alfresco_node_id})"


class ContractIntelligence(models.Model):
    """
    Stores AI-extracted legal intelligence from contracts using RAG.
    This is the JSON output from the legal extraction prompt template.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.OneToOneField(Contract, on_delete=models.CASCADE, related_name='intelligence', db_column='contractId', to_field='id')

    # Extracted legal data (from RAG prompt template)
    parties = models.TextField(blank=True, null=True, help_text='Entities entering the agreement')
    termination_summary = models.TextField(blank=True, null=True, db_column='terminationSummary', help_text='How contract can be ended')
    termination_notice_period = models.CharField(max_length=200, blank=True, null=True, db_column='terminationNoticePeriod', help_text='Required notice period for termination')
    liability_summary = models.TextField(blank=True, null=True, db_column='liabilitySummary', help_text='Liability limitations and caps')
    jurisdiction = models.CharField(max_length=200, blank=True, null=True, help_text='Governing law jurisdiction')
    confidentiality_duration = models.CharField(max_length=200, blank=True, null=True, db_column='confidentialityDuration', help_text='Confidentiality obligations duration')

    # RAG metadata
    extraction_confidence = models.FloatField(default=0.0, db_column='extractionConfidence', help_text='Overall extraction quality (0-1)')
    vector_db_chunks = models.IntegerField(default=0, db_column='vectorDbChunks', help_text='Number of chunks in vector DB')
    relevant_chunks_used = models.IntegerField(default=0, db_column='relevantChunksUsed', help_text='Chunks used for extraction')

    # Raw extraction data
    raw_extraction_data = models.JSONField(default=dict, db_column='rawExtractionData', help_text='Full JSON from LLM extraction')

    extracted_at = models.DateTimeField(auto_now_add=True, db_column='extractedAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'contract_intelligence'
        ordering = ['-extracted_at']

    def __str__(self):
        return f"Intelligence: {self.contract.original_filename}"


class VectorEmbedding(models.Model):
    """
    Tracks document chunks stored in ChromaDB/Vector Database.
    Links back to contract for management and auditing.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='embeddings', db_column='contractId', to_field='id')

    # Vector DB metadata
    embedding_id = models.CharField(max_length=255, unique=True, db_column='embeddingId', help_text='ID in vector database (ChromaDB)')
    chunk_index = models.IntegerField(db_column='chunkIndex', help_text='Order of chunk in document')
    chunk_text = models.TextField(db_column='chunkText', help_text='Original text of this chunk')
    chunk_start_char = models.IntegerField(db_column='chunkStartChar', help_text='Start position in full text')
    chunk_end_char = models.IntegerField(db_column='chunkEndChar', help_text='End position in full text')

    # Semantic metadata
    chunk_type = models.CharField(max_length=50, blank=True, null=True, db_column='chunkType',
                                   help_text='Type of content (clause, obligation, etc.)')
    embedding_model = models.CharField(max_length=100, default='sentence-transformers', db_column='embeddingModel',
                                      help_text='Model used for embedding')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'vector_embeddings'
        ordering = ['contract', 'chunk_index']
        indexes = [
            models.Index(fields=['contract', 'chunk_index']),
            models.Index(fields=['embedding_id']),
        ]

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.contract.original_filename}"


# =========================
# AGENTIC AI ANALYSIS RESULTS
# =========================

class AnalysisResult(models.Model):
    """
    Stores AI-generated insights from the Agentic AI system.
    This table captures results from all 5 agent tools:
    1. Risk Scoring
    2. Contract Classification
    3. Clause Extraction
    4. Executive Summary
    5. Intent Mining
    """

    RISK_LEVEL_CHOICES = [
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
        ('CRITICAL', 'Critical Risk'),
    ]

    id = models.AutoField(primary_key=True)
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='analysis_results',
        db_column='contractId',
        help_text='Contract this analysis belongs to'
    )

    # Feature 1: Executive Summary
    executive_summary = models.TextField(
        blank=True,
        null=True,
        db_column='executiveSummary',
        help_text='AI-generated high-level summary for executives'
    )

    # Feature 2: Risk Scoring (Searchable/Filterable)
    risk_score = models.IntegerField(
        blank=True,
        null=True,
        db_column='riskScore',
        help_text='Overall risk score 0-100'
    )
    risk_level = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=RISK_LEVEL_CHOICES,
        db_column='riskLevel',
        help_text='Risk classification'
    )
    risk_flags = models.JSONField(
        default=list,
        blank=True,
        db_column='riskFlags',
        help_text='List of specific risk factors identified'
    )

    # Feature 3: Clause Extraction (Flexible JSON)
    extracted_clauses = models.JSONField(
        default=dict,
        blank=True,
        db_column='extractedClauses',
        help_text='Extracted provisions: {"liability": "...", "payment": "..."}'
    )

    # Feature 4: Intent Mining & Classification (JSON Metadata)
    agent_metadata = models.JSONField(
        default=dict,
        blank=True,
        db_column='agentMetadata',
        help_text='Agent metadata: {"primary_intent": "...", "confidence": 0.98}'
    )
    primary_intent = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        db_column='primaryIntent',
        help_text='Main business intent (extracted for search)'
    )
    intent_confidence = models.FloatField(
        blank=True,
        null=True,
        db_column='intentConfidence',
        help_text='Confidence score for intent classification (0-1)'
    )

    # Feature 5: Compliance Check
    is_compliant = models.BooleanField(
        default=True,
        db_column='isCompliant',
        help_text='Overall compliance status'
    )
    compliance_issues = models.JSONField(
        default=list,
        blank=True,
        db_column='complianceIssues',
        help_text='List of compliance violations found'
    )

    # Agent Execution Metadata
    agent_version = models.CharField(
        max_length=50,
        default='1.0',
        db_column='agentVersion',
        help_text='Version of agent that performed analysis'
    )
    tools_used = models.JSONField(
        default=list,
        blank=True,
        db_column='toolsUsed',
        help_text='List of MCP tools used in this analysis'
    )
    execution_time_seconds = models.FloatField(
        blank=True,
        null=True,
        db_column='executionTimeSeconds',
        help_text='Time taken for agent to complete analysis'
    )

    # Timestamps
    analyzed_at = models.DateTimeField(
        auto_now_add=True,
        db_column='analyzedAt',
        help_text='When this analysis was performed'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_column='updatedAt',
        help_text='When this analysis was last updated'
    )

    class Meta:
        db_table = 'analysis_results'
        ordering = ['-analyzed_at']
        indexes = [
            models.Index(fields=['contract']),
            models.Index(fields=['risk_score']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['primary_intent']),
            models.Index(fields=['-analyzed_at']),
        ]

    def __str__(self):
        return f"Analysis for {self.contract.original_filename} (Risk: {self.risk_level or 'N/A'})"


# =========================
# PAYMENT & SUBSCRIPTION MODELS
# =========================

class PaymentTransaction(models.Model):
    """
    Stores all payment transactions for subscriptions.
    Tracks payments from both Stripe and PayPal.
    """
    PAYMENT_METHOD_CHOICES = [
        ('STRIPE', 'Stripe'),
        ('PAYPAL', 'PayPal'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments', db_column='userId')
    plan = models.ForeignKey(PricingPlan, on_delete=models.PROTECT, related_name='payments', db_column='planId')

    # Payment details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, db_column='paymentMethod')
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text='Payment amount in USD')
    currency = models.CharField(max_length=3, default='USD', help_text='Currency code (USD, EUR, etc.)')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # Gateway-specific IDs
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True, db_column='stripePaymentIntentId', help_text='Stripe Payment Intent ID')
    paypal_order_id = models.CharField(max_length=255, blank=True, null=True, db_column='paypalOrderId', help_text='PayPal Order ID')
    gateway_response = models.JSONField(default=dict, blank=True, db_column='gatewayResponse', help_text='Full response from payment gateway')

    # Transaction metadata
    description = models.TextField(blank=True, null=True, help_text='Payment description')
    failure_reason = models.TextField(blank=True, null=True, db_column='failureReason', help_text='Reason for payment failure')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    completed_at = models.DateTimeField(blank=True, null=True, db_column='completedAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'payment_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['stripe_payment_intent_id']),
            models.Index(fields=['paypal_order_id']),
        ]

    def __str__(self):
        return f"{self.payment_method} - ${self.amount} ({self.status})"


class Subscription(models.Model):
    """
    Tracks user subscriptions and billing cycles.
    Links users to their current and past subscriptions.
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('PAST_DUE', 'Past Due'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
        ('TRIALING', 'Trialing'),
    ]

    BILLING_CYCLE_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('YEARLY', 'Yearly'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions', db_column='userId')
    plan = models.ForeignKey(PricingPlan, on_delete=models.PROTECT, related_name='subscriptions', db_column='planId')

    # Subscription details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default='MONTHLY', db_column='billingCycle')

    # Gateway subscription IDs (for recurring payments)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True, db_column='stripeSubscriptionId', help_text='Stripe Subscription ID')
    paypal_subscription_id = models.CharField(max_length=255, blank=True, null=True, db_column='paypalSubscriptionId', help_text='PayPal Subscription ID')

    # Dates
    start_date = models.DateTimeField(db_column='startDate', help_text='When subscription started')
    current_period_start = models.DateTimeField(db_column='currentPeriodStart', help_text='Current billing period start')
    current_period_end = models.DateTimeField(db_column='currentPeriodEnd', help_text='Current billing period end')
    cancelled_at = models.DateTimeField(blank=True, null=True, db_column='cancelledAt', help_text='When subscription was cancelled')
    ended_at = models.DateTimeField(blank=True, null=True, db_column='endedAt', help_text='When subscription ended')

    # Trial
    trial_start = models.DateTimeField(blank=True, null=True, db_column='trialStart')
    trial_end = models.DateTimeField(blank=True, null=True, db_column='trialEnd')

    # Auto-renewal
    auto_renew = models.BooleanField(default=True, db_column='autoRenew', help_text='Whether subscription auto-renews')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['plan']),
            models.Index(fields=['status', 'current_period_end']),
            models.Index(fields=['stripe_subscription_id']),
            models.Index(fields=['paypal_subscription_id']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.plan.display_name} ({self.status})"


# =========================
# CONTRACT REDLINING MODELS
# =========================

class RedlineSession(models.Model):
    """
    Tracks a redlining session for a contract.
    Stores all clause analysis and changes made during the session.
    """
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('EXPORTED', 'Exported'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='redline_sessions', db_column='contractId')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='redline_sessions', db_column='userId')

    # Session metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    jurisdiction = models.CharField(max_length=100, default='Common Law', help_text='Legal jurisdiction for analysis')

    # Analysis summary
    total_clauses_analyzed = models.IntegerField(default=0, db_column='totalClausesAnalyzed')
    high_risk_count = models.IntegerField(default=0, db_column='highRiskCount')
    medium_risk_count = models.IntegerField(default=0, db_column='mediumRiskCount')
    low_risk_count = models.IntegerField(default=0, db_column='lowRiskCount')
    changes_accepted = models.IntegerField(default=0, db_column='changesAccepted')
    changes_rejected = models.IntegerField(default=0, db_column='changesRejected')

    # Export tracking
    docx_exported_at = models.DateTimeField(null=True, blank=True, db_column='docxExportedAt')
    pdf_exported_at = models.DateTimeField(null=True, blank=True, db_column='pdfExportedAt')
    exported_file_path = models.TextField(blank=True, null=True, db_column='exportedFilePath')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')
    completed_at = models.DateTimeField(null=True, blank=True, db_column='completedAt')

    class Meta:
        db_table = 'redline_sessions'
        managed = False  # Table created via raw SQL migration
        ordering = ['-created_at']

    def __str__(self):
        return f"Redline Session: {self.contract.original_filename} ({self.status})"


class RedlineChange(models.Model):
    """
    Individual clause change in a redlining session.
    Stores original text, suggested text, risk analysis, and legal explainability.
    """
    RISK_TYPE_CHOICES = [
        ('FINANCIAL', 'Financial Risk'),
        ('LIABILITY', 'Liability Risk'),
        ('TERMINATION', 'Termination Risk'),
        ('IP', 'Intellectual Property Risk'),
        ('CONFIDENTIALITY', 'Confidentiality Risk'),
        ('GOVERNING_LAW', 'Governing Law Risk'),
        ('INDEMNITY', 'Indemnification Risk'),
        ('FORCE_MAJEURE', 'Force Majeure Risk'),
        ('DATA_PRIVACY', 'Data Privacy Risk'),
        ('COMPLIANCE', 'Compliance Risk'),
        ('OTHER', 'Other Risk'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('MODIFIED', 'Modified'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    session = models.ForeignKey(RedlineSession, on_delete=models.CASCADE, related_name='changes', db_column='sessionId')
    clause = models.ForeignKey(Clause, on_delete=models.SET_NULL, null=True, blank=True, related_name='redline_changes', db_column='clauseId')

    # Clause identification
    clause_name = models.CharField(max_length=255, db_column='clauseName')
    clause_index = models.IntegerField(default=0, db_column='clauseIndex', help_text='Order in the document')

    # Original and suggested text
    original_text = models.TextField(db_column='originalText')
    suggested_text = models.TextField(db_column='suggestedText')
    accepted_text = models.TextField(blank=True, null=True, db_column='acceptedText', help_text='Final text after user edits')

    # Redline diff (unified diff format)
    redline_diff = models.TextField(blank=True, null=True, db_column='redlineDiff')

    # Risk analysis
    risk_type = models.CharField(max_length=30, choices=RISK_TYPE_CHOICES, db_column='riskType')
    risk_score = models.IntegerField(default=0, db_column='riskScore', help_text='Risk score 0-100')
    risk_explanation = models.TextField(db_column='riskExplanation', help_text='Commercial risk explanation')

    # Legal explainability (court-safe)
    legal_doctrine = models.CharField(max_length=255, blank=True, null=True, db_column='legalDoctrine',
                                      help_text='Legal doctrine violated (e.g., Unconscionability)')
    court_reasoning = models.TextField(blank=True, null=True, db_column='courtReasoning',
                                       help_text='Why courts typically reject this clause')
    litigation_risk = models.CharField(max_length=100, blank=True, null=True, db_column='litigationRisk',
                                       help_text='Probability of judicial modification')
    judicial_treatment = models.TextField(blank=True, null=True, db_column='judicialTreatment',
                                          help_text='How courts usually interpret this clause')

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reviewed_redlines', db_column='reviewedBy')
    reviewed_at = models.DateTimeField(null=True, blank=True, db_column='reviewedAt')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'redline_changes'
        managed = False  # Table created via raw SQL migration
        ordering = ['clause_index', '-risk_score']

    def __str__(self):
        return f"{self.clause_name} - {self.risk_type} ({self.risk_score}/100)"


# =========================
# EMBEDDING-FIRST AI MODELS
# =========================
# These models support the non-LLM, embedding-based contract analysis
# Using sentence-transformers/all-MiniLM-L6-v2 (384-dimensional embeddings)

class RiskPlaybook(models.Model):
    """
    Library of known risky clause patterns with pre-computed embeddings.
    Used for deterministic risk scoring: Risk = Similarity × Severity Weight

    Example entries:
    - "Unlimited liability clause" (severity: 0.9)
    - "One-sided termination rights" (severity: 0.7)
    - "Broad indemnification language" (severity: 0.8)
    """
    RISK_CATEGORY_CHOICES = [
        ('LIABILITY', 'Liability Risk'),
        ('TERMINATION', 'Termination Risk'),
        ('INDEMNIFICATION', 'Indemnification Risk'),
        ('IP_OWNERSHIP', 'IP Ownership Risk'),
        ('CONFIDENTIALITY', 'Confidentiality Risk'),
        ('PAYMENT', 'Payment Risk'),
        ('GOVERNING_LAW', 'Governing Law Risk'),
        ('FORCE_MAJEURE', 'Force Majeure Risk'),
        ('DATA_PRIVACY', 'Data Privacy Risk'),
        ('NON_COMPETE', 'Non-Compete Risk'),
        ('LIMITATION_OF_DAMAGES', 'Limitation of Damages'),
        ('ASSIGNMENT', 'Assignment Risk'),
        ('RENEWAL', 'Auto-Renewal Risk'),
        ('DISPUTE_RESOLUTION', 'Dispute Resolution Risk'),
        ('OTHER', 'Other Risk'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)

    # Risk identification
    risk_type = models.CharField(max_length=50, choices=RISK_CATEGORY_CHOICES, db_column='riskType',
                                 help_text='Category of risk this pattern represents')
    risk_name = models.CharField(max_length=255, db_column='riskName',
                                 help_text='Short name for this risk pattern')
    risk_description = models.TextField(db_column='riskDescription',
                                        help_text='Full description of the risky pattern')

    # Example risky clause text (used for embedding generation)
    example_clause_text = models.TextField(db_column='exampleClauseText',
                                           help_text='Example text of a clause exhibiting this risk')

    # Severity and scoring
    severity_weight = models.FloatField(default=0.5, db_column='severityWeight',
                                        help_text='Severity multiplier (0.0-1.0) for risk scoring')

    # Pre-computed embedding (384 dimensions for all-MiniLM-L6-v2)
    embedding = models.JSONField(default=list, blank=True,
                                 help_text='Pre-computed 384-dim embedding vector as JSON array')
    embedding_model = models.CharField(max_length=100, default='all-MiniLM-L6-v2', db_column='embeddingModel',
                                       help_text='Model used to generate embedding')

    # Similarity threshold for matching
    similarity_threshold = models.FloatField(default=0.7, db_column='similarityThreshold',
                                             help_text='Minimum cosine similarity to trigger this risk')

    # Legal context
    jurisdiction = models.CharField(max_length=100, blank=True, null=True,
                                    help_text='Jurisdiction where this risk is most relevant')
    legal_reference = models.TextField(blank=True, null=True, db_column='legalReference',
                                       help_text='Legal precedent or regulation reference')
    court_treatment = models.TextField(blank=True, null=True, db_column='courtTreatment',
                                       help_text='How courts typically treat this clause type')

    # Metadata
    is_active = models.BooleanField(default=True, db_column='isActive',
                                    help_text='Whether this risk pattern is actively checked')
    created_by_id = models.CharField(max_length=36, null=True, blank=True, db_column='createdBy',
                                     help_text='ID of user who created this playbook')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'risk_playbooks'
        ordering = ['-severity_weight', 'risk_type']
        indexes = [
            models.Index(fields=['risk_type', 'is_active']),
            models.Index(fields=['-severity_weight']),
            models.Index(fields=['jurisdiction']),
        ]

    def __str__(self):
        return f"{self.risk_name} ({self.risk_type}) - Severity: {self.severity_weight}"


class IntentTemplate(models.Model):
    """
    Library of legal intent patterns with pre-computed embeddings.
    Used for deterministic intent detection via cosine similarity.

    Example intents:
    - "Shift liability to counterparty"
    - "Exclude consequential damages"
    - "Lock-in termination rights"
    - "Transfer IP ownership"
    """
    INTENT_CATEGORY_CHOICES = [
        ('LIABILITY_SHIFT', 'Liability Shifting'),
        ('DAMAGE_EXCLUSION', 'Damage Exclusion'),
        ('TERMINATION_CONTROL', 'Termination Control'),
        ('IP_TRANSFER', 'IP Transfer'),
        ('PAYMENT_CONTROL', 'Payment Control'),
        ('CONFIDENTIALITY_OBLIGATION', 'Confidentiality Obligation'),
        ('NON_COMPETE', 'Non-Compete Restriction'),
        ('INDEMNIFICATION', 'Indemnification Obligation'),
        ('DISPUTE_RESOLUTION', 'Dispute Resolution'),
        ('RENEWAL_CONTROL', 'Renewal/Extension Control'),
        ('ASSIGNMENT_RESTRICTION', 'Assignment Restriction'),
        ('GOVERNING_LAW', 'Governing Law Selection'),
        ('COMPLIANCE_REQUIREMENT', 'Compliance Requirement'),
        ('DATA_HANDLING', 'Data Handling Obligation'),
        ('OTHER', 'Other Intent'),
    ]

    PARTY_IMPACT_CHOICES = [
        ('FAVOR_YOU', 'Favors Your Company'),
        ('FAVOR_COUNTERPARTY', 'Favors Counterparty'),
        ('NEUTRAL', 'Neutral/Balanced'),
        ('MUTUAL', 'Mutual Obligation'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)

    # Intent identification
    intent_name = models.CharField(max_length=255, unique=True, db_column='intentName',
                                   help_text='Canonical name for this intent')
    intent_category = models.CharField(max_length=50, choices=INTENT_CATEGORY_CHOICES, db_column='intentCategory',
                                       help_text='Category of legal intent')
    intent_description = models.TextField(db_column='intentDescription',
                                          help_text='What this intent aims to achieve legally')

    # Example clause text (used for embedding generation)
    example_clause_text = models.TextField(db_column='exampleClauseText',
                                           help_text='Example clause text that exhibits this intent')

    # Party impact analysis
    party_impact = models.CharField(max_length=30, choices=PARTY_IMPACT_CHOICES, db_column='partyImpact',
                                    help_text='Which party does this intent favor')
    risk_level = models.CharField(max_length=20, default='MEDIUM', db_column='riskLevel',
                                  choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')],
                                  help_text='Inherent risk level of this intent')

    # Pre-computed embedding (384 dimensions for all-MiniLM-L6-v2)
    embedding = models.JSONField(default=list, blank=True,
                                 help_text='Pre-computed 384-dim embedding vector as JSON array')
    embedding_model = models.CharField(max_length=100, default='all-MiniLM-L6-v2', db_column='embeddingModel',
                                       help_text='Model used to generate embedding')

    # Similarity threshold for matching
    similarity_threshold = models.FloatField(default=0.65, db_column='similarityThreshold',
                                             help_text='Minimum cosine similarity to detect this intent')

    # Legal guidance
    negotiation_guidance = models.TextField(blank=True, null=True, db_column='negotiationGuidance',
                                            help_text='How to negotiate when this intent is detected')
    risk_mitigation = models.TextField(blank=True, null=True, db_column='riskMitigation',
                                       help_text='How to mitigate risks from this intent')

    # Metadata
    is_active = models.BooleanField(default=True, db_column='isActive',
                                    help_text='Whether this intent is actively detected')
    created_by_id = models.CharField(max_length=36, null=True, blank=True, db_column='createdBy',
                                     help_text='ID of user who created this template')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'intent_templates'
        ordering = ['intent_category', 'intent_name']
        indexes = [
            models.Index(fields=['intent_category', 'is_active']),
            models.Index(fields=['party_impact']),
            models.Index(fields=['risk_level']),
        ]

    def __str__(self):
        return f"{self.intent_name} ({self.intent_category}) - {self.party_impact}"


class ApprovedClause(models.Model):
    """
    Library of pre-approved, legally-vetted clause alternatives.
    Used for deterministic redlining: Match intent → Lookup approved clause → Generate diff

    Zero hallucination - only outputs from this approved library.
    """
    CLAUSE_TYPE_CHOICES = [
        ('LIABILITY', 'Liability Clause'),
        ('INDEMNIFICATION', 'Indemnification Clause'),
        ('TERMINATION', 'Termination Clause'),
        ('CONFIDENTIALITY', 'Confidentiality Clause'),
        ('IP_OWNERSHIP', 'IP Ownership Clause'),
        ('PAYMENT', 'Payment Terms'),
        ('GOVERNING_LAW', 'Governing Law'),
        ('DISPUTE_RESOLUTION', 'Dispute Resolution'),
        ('FORCE_MAJEURE', 'Force Majeure'),
        ('DATA_PROTECTION', 'Data Protection'),
        ('NON_COMPETE', 'Non-Compete'),
        ('ASSIGNMENT', 'Assignment'),
        ('RENEWAL', 'Renewal Terms'),
        ('WARRANTY', 'Warranty'),
        ('LIMITATION_OF_DAMAGES', 'Limitation of Damages'),
        ('OTHER', 'Other'),
    ]

    PROTECTION_LEVEL_CHOICES = [
        ('MAXIMUM', 'Maximum Protection'),
        ('BALANCED', 'Balanced/Market Standard'),
        ('MINIMUM', 'Minimum Acceptable'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)

    # Clause identification
    clause_type = models.CharField(max_length=50, choices=CLAUSE_TYPE_CHOICES, db_column='clauseType',
                                   help_text='Type of clause')
    clause_name = models.CharField(max_length=255, db_column='clauseName',
                                   help_text='Descriptive name for this approved clause')

    # Intent mapping (links to IntentTemplate for redlining)
    intent_name = models.CharField(max_length=255, db_column='intentName',
                                   help_text='Intent this clause addresses (matches IntentTemplate.intent_name)')
    intent_template_id = models.CharField(max_length=36, null=True, blank=True, db_column='intentTemplateId',
                                          help_text='Optional ID of IntentTemplate for direct lookup')

    # The approved clause text
    clause_text = models.TextField(db_column='clauseText',
                                   help_text='The approved, legally-vetted clause text')

    # Protection and context
    protection_level = models.CharField(max_length=20, choices=PROTECTION_LEVEL_CHOICES, db_column='protectionLevel',
                                        help_text='Level of protection this clause provides')

    # Jurisdiction and applicability
    jurisdiction = models.CharField(max_length=100, default='Common Law',
                                    help_text='Jurisdiction this clause is designed for')
    contract_types = models.JSONField(default=list, db_column='contractTypes',
                                      help_text='Contract types this clause applies to (e.g., ["NDA", "SLA", "MSA"])')

    # Pre-computed embedding for similarity matching
    embedding = models.JSONField(default=list, blank=True,
                                 help_text='Pre-computed 384-dim embedding for similarity search')
    embedding_model = models.CharField(max_length=100, default='all-MiniLM-L6-v2', db_column='embeddingModel',
                                       help_text='Model used to generate embedding')

    # Legal metadata
    legal_notes = models.TextField(blank=True, null=True, db_column='legalNotes',
                                   help_text='Legal team notes on this clause')
    last_reviewed_by_id = models.CharField(max_length=36, null=True, blank=True, db_column='lastReviewedBy',
                                           help_text='ID of user who last reviewed this clause')
    last_reviewed_at = models.DateTimeField(blank=True, null=True, db_column='lastReviewedAt')

    # Metadata
    is_active = models.BooleanField(default=True, db_column='isActive',
                                    help_text='Whether this clause is available for suggestions')
    version = models.IntegerField(default=1, help_text='Version number of this approved clause')
    created_by_id = models.CharField(max_length=36, null=True, blank=True, db_column='createdBy',
                                     help_text='ID of user who created this clause')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'approved_clauses'
        ordering = ['clause_type', 'protection_level', 'clause_name']
        indexes = [
            models.Index(fields=['clause_type', 'is_active']),
            models.Index(fields=['intent_name']),
            models.Index(fields=['jurisdiction']),
            models.Index(fields=['protection_level']),
        ]

    def __str__(self):
        return f"{self.clause_name} ({self.clause_type}) - {self.protection_level}"


class ClauseEmbedding(models.Model):
    """
    Stores pre-computed embeddings for contract clauses.
    Used for fast similarity search without external vector DB dependency.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    clause_id = models.CharField(max_length=36, unique=True, db_column='clauseId',
                                 help_text='Clause ID this embedding belongs to')

    # The embedding vector
    embedding = models.JSONField(default=list, help_text='384-dim embedding vector as JSON array')
    embedding_model = models.CharField(max_length=100, default='all-MiniLM-L6-v2', db_column='embeddingModel')

    # Text that was embedded (for verification)
    embedded_text_hash = models.CharField(max_length=64, db_column='embeddedTextHash',
                                          help_text='SHA256 hash of embedded text for change detection')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'clause_embeddings'
        indexes = [
            models.Index(fields=['clause_id']),
        ]

    def __str__(self):
        return f"Embedding for clause {self.clause_id}"


class ContractRiskHistory(models.Model):
    """
    Stores historical risk scores for contracts across versions.
    Enables time-series analysis and risk drift detection.
    """
    id = models.AutoField(primary_key=True)
    contract_id = models.CharField(max_length=36, db_column='contractId', help_text='Contract ID (UUID)')
    version = models.IntegerField(db_column='version', help_text='Contract version number')
    overall_risk = models.FloatField(db_column='overallRisk', help_text='Overall risk score (0-100)')
    ip_risk = models.FloatField(db_column='ipRisk', default=0, help_text='IP risk score (0-100)')
    liability_risk = models.FloatField(db_column='liabilityRisk', default=0, help_text='Liability risk score (0-100)')
    geography_risk = models.FloatField(db_column='geographyRisk', default=0, help_text='Geography risk score (0-100)')
    recorded_at = models.DateTimeField(auto_now_add=True, db_column='recordedAt')

    class Meta:
        db_table = 'contract_risk_history'
        ordering = ['contract_id', 'version']
        indexes = [
            models.Index(fields=['contract_id', 'version']),
        ]

    def __str__(self):
        return f"Risk history for contract {self.contract_id} v{self.version}"


class GoldStandardTemplate(models.Model):
    """
    Gold-standard pre-approved clause templates.
    Used as safe baselines for deviation detection.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    template_name = models.CharField(max_length=255, db_column='templateName')
    clause_category = models.CharField(max_length=50, db_column='clauseCategory', db_index=True)
    approved_clause_text = models.TextField(db_column='approvedClauseText')

    # Embedding for similarity matching
    embedding = models.JSONField(default=list)
    embedding_model = models.CharField(max_length=100, db_column='embeddingModel')

    # Risk thresholds
    safe_threshold = models.FloatField(db_column='safeThreshold', help_text='Similarity threshold for safe clauses')
    review_threshold = models.FloatField(db_column='reviewThreshold', help_text='Similarity threshold requiring review')

    # Metadata
    jurisdiction = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    legal_notes = models.TextField(null=True, blank=True, db_column='legalNotes')
    is_active = models.BooleanField(default=True, db_column='isActive')
    created_by = models.CharField(max_length=36, null=True, blank=True, db_column='createdBy')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'gold_standard_templates'
        indexes = [
            models.Index(fields=['clause_category', 'is_active']),
            models.Index(fields=['jurisdiction']),
        ]

    def __str__(self):
        return f"{self.template_name} ({self.clause_category})"


class IndustryBenchmark(models.Model):
    """
    Industry benchmark clauses from market analysis.
    Represents common/typical clauses in the industry.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    benchmark_name = models.CharField(max_length=255, db_column='benchmarkName')
    clause_category = models.CharField(max_length=50, db_column='clauseCategory', db_index=True)
    industry = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    benchmark_clause_text = models.TextField(db_column='benchmarkClauseText')

    # Embedding for similarity matching
    embedding = models.JSONField(default=list)
    embedding_model = models.CharField(max_length=100, db_column='embeddingModel')

    # Adoption metrics
    adoption_rate = models.FloatField(db_column='adoptionRate', help_text='How common this clause is (0-1)')
    source = models.CharField(max_length=255, null=True, blank=True, help_text='Source of benchmark data')

    # Metadata
    jurisdiction = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    is_active = models.BooleanField(default=True, db_column='isActive')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'industry_benchmarks'
        indexes = [
            models.Index(fields=['clause_category', 'industry']),
            models.Index(fields=['jurisdiction']),
        ]

    def __str__(self):
        return f"{self.benchmark_name} ({self.industry or 'General'})"


class ClauseDeviationScore(models.Model):
    """
    Stores deviation scores for clauses compared against templates and benchmarks.
    Used for clause risk assessment and negotiation intelligence.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    clause_id = models.CharField(max_length=36, unique=True, db_column='clauseId')
    contract_id = models.CharField(max_length=36, db_column='contractId', db_index=True)

    # Similarity scores (0-1, higher = more similar)
    gold_standard_similarity = models.FloatField(null=True, blank=True, db_column='goldStandardSimilarity')
    industry_benchmark_similarity = models.FloatField(null=True, blank=True, db_column='industryBenchmarkSimilarity')
    past_accepted_similarity = models.FloatField(null=True, blank=True, db_column='pastAcceptedSimilarity')

    # Risk assessment
    overall_risk_level = models.CharField(max_length=20, db_column='overallRiskLevel', db_index=True,
                                         help_text='LOW, MEDIUM, HIGH')
    overall_deviation_score = models.FloatField(db_column='overallDeviationScore',
                                                help_text='Combined deviation score (0-1)')
    risk_type = models.CharField(max_length=100, null=True, blank=True, db_column='riskType')

    # Suggestions
    suggested_replacement_text = models.TextField(null=True, blank=True, db_column='suggestedReplacementText')
    suggested_from_template_id = models.CharField(max_length=36, null=True, blank=True,
                                                  db_column='suggestedFromTemplateId')
    explanation = models.TextField(null=True, blank=True, help_text='Why this clause deviates')
    court_precedent = models.TextField(null=True, blank=True, db_column='courtPrecedent')

    # References to matched templates/benchmarks
    gold_standard_id = models.CharField(max_length=36, null=True, blank=True,
                                       db_column='goldStandardId', db_index=True)
    industry_benchmark_id = models.CharField(max_length=36, null=True, blank=True,
                                            db_column='industryBenchmarkId', db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'clause_deviation_scores'
        indexes = [
            models.Index(fields=['contract_id']),
            models.Index(fields=['overall_risk_level']),
            models.Index(fields=['gold_standard_id']),
            models.Index(fields=['industry_benchmark_id']),
        ]

    def __str__(self):
        return f"Deviation score for clause {self.clause_id} - {self.overall_risk_level}"


class ExpectedObligation(models.Model):
    """
    Expected obligations/safeguards that contracts should contain.
    Used to detect missing or weak protective clauses.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    obligation_name = models.CharField(max_length=255, db_column='obligationName')
    obligation_category = models.CharField(max_length=50, db_column='obligationCategory', db_index=True)
    criticality = models.CharField(max_length=20, db_column='criticality', db_index=True,
                                   help_text='CRITICAL, HIGH, MEDIUM, LOW')

    # Expected clause characteristics
    expected_clause_text = models.TextField(db_column='expectedClauseText',
                                           help_text='Example text of what we expect to see')

    # Embedding for semantic matching
    embedding = models.JSONField(default=list)
    embedding_model = models.CharField(max_length=100, db_column='embeddingModel')
    presence_threshold = models.FloatField(db_column='presenceThreshold',
                                          help_text='Similarity threshold to consider obligation present')

    # Risk information
    absence_risk_description = models.TextField(db_column='absenceRiskDescription',
                                               help_text='What risk occurs if this is missing')
    absence_risk_example = models.TextField(null=True, blank=True, db_column='absenceRiskExample')
    suggested_clause_text = models.TextField(null=True, blank=True, db_column='suggestedClauseText')

    # Applicability filters
    contract_type = models.CharField(max_length=100, null=True, blank=True, db_column='contractType', db_index=True)
    party_protected = models.CharField(max_length=50, null=True, blank=True, db_column='partyProtected')
    jurisdiction = models.CharField(max_length=100, null=True, blank=True)

    is_active = models.BooleanField(default=True, db_column='isActive')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'expected_obligations'
        indexes = [
            models.Index(fields=['obligation_category', 'criticality']),
            models.Index(fields=['contract_type']),
        ]

    def __str__(self):
        return f"{self.obligation_name} ({self.criticality})"


class MissingSafeguardDetection(models.Model):
    """
    Records detected missing or weak safeguards in contracts.
    Links to expected obligations that were not found.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract_id = models.CharField(max_length=36, db_column='contractId', db_index=True)
    expected_obligation_id = models.CharField(max_length=36, db_column='expectedObligationId', db_index=True)

    # Detection status
    status = models.CharField(max_length=20, db_column='status', db_index=True,
                             help_text='MISSING, WEAK, PRESENT')
    confidence = models.FloatField(help_text='Confidence in this detection (0-1)')

    # Best match found (if any)
    matched_clause_id = models.CharField(max_length=36, null=True, blank=True, db_column='matchedClauseId')
    matched_similarity = models.FloatField(null=True, blank=True, db_column='matchedSimilarity')

    # AI-generated insights
    ai_insight = models.TextField(db_column='aiInsight', help_text='AI explanation of the detection')
    risk_explanation = models.TextField(db_column='riskExplanation')
    suggested_action = models.TextField(db_column='suggestedAction')
    suggested_clause_text = models.TextField(null=True, blank=True, db_column='suggestedClauseText')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'missing_safeguard_detections'
        indexes = [
            models.Index(fields=['contract_id', 'status']),
            models.Index(fields=['expected_obligation_id']),
        ]

    def __str__(self):
        return f"Safeguard detection for contract {self.contract_id} - {self.status}"


class ContractGraphMeta(models.Model):
    """
    Graph Analysis Metadata
    ========================
    Stores pre-computed graph analysis results for fast dashboard loading.

    Created automatically on contract upload.
    Contains:
    - NetworkX graph summary (nodes/edges)
    - Risk propagation timeline
    - Negotiation priority rankings
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,
        related_name='graph_meta',
        db_column='contractId'
    )

    # NetworkX graph summary (nodes, edges, metrics)
    graph_summary = models.JSONField(
        db_column='graphSummary',
        help_text='NetworkX graph structure (nodes/edges/metrics)'
    )

    # Risk propagation simulation results
    risk_timeline = models.JSONField(
        db_column='riskTimeline',
        help_text='Risk propagation timeline with steps and hotspots'
    )

    # Negotiation priority advice
    negotiation_advice = models.JSONField(
        db_column='negotiationAdvice',
        help_text='Prioritized negotiation recommendations'
    )

    # Neo4j sync status
    neo4j_synced = models.BooleanField(
        default=False,
        db_column='neo4jSynced',
        help_text='Whether contract was synced to Neo4j knowledge graph'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'contract_graph_meta'
        indexes = [
            models.Index(fields=['contract_id']),
        ]

    def __str__(self):
        return f"Graph metadata for contract {self.contract_id}"


# =========================
# PLAYBOOK AUTOMATION
# =========================

class LegalPlaybook(models.Model):
    """
    Company's legal playbook – the authoritative set of approved standard
    and fallback clause texts per clause type and jurisdiction.

    Similarity comparison is done via the pre-computed 384-dim embedding
    of standard_clause, using the same MiniLM singleton as the rest of the
    embedding pipeline.
    """
    CLAUSE_TYPE_CHOICES = [
        ('LIABILITY', 'Liability'),
        ('TERMINATION', 'Termination'),
        ('INDEMNIFICATION', 'Indemnification'),
        ('IP_OWNERSHIP', 'IP Ownership'),
        ('CONFIDENTIALITY', 'Confidentiality'),
        ('PAYMENT', 'Payment'),
        ('GOVERNING_LAW', 'Governing Law'),
        ('FORCE_MAJEURE', 'Force Majeure'),
        ('DATA_PRIVACY', 'Data Privacy'),
        ('NON_COMPETE', 'Non-Compete'),
        ('LIMITATION_OF_DAMAGES', 'Limitation of Damages'),
        ('ASSIGNMENT', 'Assignment'),
        ('RENEWAL', 'Renewal'),
        ('DISPUTE_RESOLUTION', 'Dispute Resolution'),
        ('OTHER', 'Other'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)

    clause_type = models.CharField(max_length=50, choices=CLAUSE_TYPE_CHOICES, db_column='clauseType')
    jurisdiction = models.CharField(max_length=100, default='global')

    # The "gold" language – what every incoming clause should look like
    standard_clause = models.TextField(db_column='standardClause')

    # Approved fallback – used when Qwen rewrites a non-standard clause
    fallback_clause = models.TextField(db_column='fallbackClause')

    # Pre-computed embedding of standard_clause (384-dim JSON array)
    embedding = models.JSONField(default=list, blank=True)
    embedding_model = models.CharField(max_length=100, default='all-MiniLM-L6-v2', db_column='embeddingModel')

    # Cosine-similarity threshold below which a clause is flagged non-standard
    similarity_threshold = models.FloatField(default=0.85, db_column='similarityThreshold')

    # If True, a violation auto-triggers a negotiation session
    mandatory = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'legal_playbooks'
        ordering = ['clause_type', 'jurisdiction']
        indexes = [
            models.Index(fields=['clause_type', 'jurisdiction']),
            models.Index(fields=['mandatory']),
        ]

    def __str__(self):
        return f"{self.clause_type} – {self.jurisdiction} (threshold {self.similarity_threshold})"


class ClausePlaybookResult(models.Model):
    """
    Per-clause evaluation result produced by run_playbook_check().
    Stores the similarity score, standard/non-standard verdict, and – when
    non-standard – the Qwen-generated fallback suggestion.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)

    clause_id = models.CharField(max_length=36, db_column='clauseId')
    playbook_id = models.CharField(max_length=36, db_column='playbookId')

    similarity_score = models.FloatField(db_column='similarityScore')
    is_standard = models.BooleanField(db_column='isStandard')

    # Qwen-generated rewrite (null when clause is already standard)
    suggested_text = models.TextField(blank=True, null=True, db_column='suggestedText')

    # True once the user has clicked "Accept Fallback"
    fallback_accepted = models.BooleanField(default=False, db_column='fallbackAccepted')
    accepted_at = models.DateTimeField(blank=True, null=True, db_column='acceptedAt')

    evaluated_at = models.DateTimeField(auto_now_add=True, db_column='evaluatedAt')

    class Meta:
        db_table = 'clause_playbook_results'
        ordering = ['-evaluated_at']
        indexes = [
            models.Index(fields=['clause_id', 'playbook_id']),
            models.Index(fields=['is_standard']),
        ]

    def __str__(self):
        status = "standard" if self.is_standard else "non-standard"
        return f"Clause {self.clause_id} vs Playbook {self.playbook_id} – {status}"


class PlaybookDriftSnapshot(models.Model):
    """
    Daily aggregate snapshot of how much incoming contract language deviates
    from each playbook entry.  Populated by capture_playbook_drift() (cron /
    Celery).  Powers the drift trend chart on the frontend.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)

    clause_type = models.CharField(max_length=50, db_column='clauseType')
    jurisdiction = models.CharField(max_length=100)

    avg_similarity = models.FloatField(db_column='avgSimilarity')
    non_standard_rate = models.FloatField(db_column='nonStandardRate')

    snapshot_date = models.DateField(auto_now_add=True, db_column='snapshotDate')

    class Meta:
        db_table = 'playbook_drift_snapshots'
        ordering = ['-snapshot_date']
        indexes = [
            models.Index(fields=['clause_type', 'jurisdiction', '-snapshot_date']),
        ]

    def __str__(self):
        return f"{self.clause_type}/{self.jurisdiction} – {self.snapshot_date}"


class PlaybookUpdateSuggestion(models.Model):
    """
    When sustained drift is detected for a clause type the system creates one
    of these suggestions proposing a new standard_clause text.  A legal
    reviewer must approve or reject before any playbook entry changes.
    """
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)

    clause_type = models.CharField(max_length=50, db_column='clauseType')
    jurisdiction = models.CharField(max_length=100)

    reason = models.TextField()
    suggested_standard = models.TextField(db_column='suggestedStandard')

    avg_similarity = models.FloatField(db_column='avgSimilarity')
    non_standard_rate = models.FloatField(db_column='nonStandardRate')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'playbook_update_suggestions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'clause_type']),
        ]

    def __str__(self):
        return f"[{self.status}] {self.clause_type}/{self.jurisdiction}"


class SystemSettings(models.Model):
    """
    System-wide settings stored in database for persistence across server restarts.
    Uses singleton pattern - only one row should exist.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)

    # Active embedding model key ('minilm' or 'bert-large-uncased')
    active_embedding_model = models.CharField(
        max_length=50,
        default='minilm',
        db_column='activeEmbeddingModel',
        help_text='Currently active embedding model key'
    )

    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'system_settings'
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'

    def __str__(self):
        return f"System Settings (Embedding Model: {self.active_embedding_model})"

    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance"""
        settings, created = cls.objects.get_or_create(
            id='system-settings-singleton',
            defaults={'active_embedding_model': 'minilm'}
        )
        return settings

    @classmethod
    def get_active_embedding_model(cls):
        """Get the currently active embedding model key"""
        return cls.get_settings().active_embedding_model

    @classmethod
    def set_active_embedding_model(cls, model_key: str):
        """Set the active embedding model key"""
        settings = cls.get_settings()
        settings.active_embedding_model = model_key
        settings.save(update_fields=['active_embedding_model', 'updated_at'])
        return settings


# ============================================================
# SELF-HEALING CLAUSE LIBRARY MODELS
# ============================================================

class ClauseEvent(models.Model):
    """
    Track real-world outcomes of clause usage (executed contracts, disputes, renewals).
    This is the core intelligence for self-healing clauses.
    """
    EVENT_TYPE_CHOICES = [
        ('EXECUTED', 'Contract Executed'),
        ('DISPUTED', 'Clause Disputed'),
        ('RENEWED', 'Contract Renewed'),
        ('LITIGATED', 'Legal Litigation'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    clause_version = models.ForeignKey(
        ClauseVersion,
        on_delete=models.CASCADE,
        related_name='events',
        db_column='clauseVersionId'
    )
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='clause_events',
        db_column='contractId',
        null=True,
        blank=True
    )
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, db_column='eventType')
    outcome_score = models.FloatField(
        db_column='outcomeScore',
        help_text='Positive outcome = 1.0, Negative outcome = 0.0, Neutral = 0.5'
    )

    # Additional context
    description = models.TextField(blank=True, null=True, help_text='Details about the event')
    jurisdiction = models.CharField(max_length=100, blank=True, null=True, help_text='Where the event occurred')
    counterparty_type = models.CharField(max_length=100, blank=True, null=True, db_column='counterpartyType')
    settlement_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        db_column='settlementAmount',
        help_text='Settlement cost if disputed/litigated'
    )

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'clause_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['clause_version', '-created_at']),
            models.Index(fields=['event_type', 'outcome_score']),
            models.Index(fields=['contract', 'event_type']),
        ]

    def __str__(self):
        return f"{self.event_type} - Score: {self.outcome_score}"


class ClauseHealthMetrics(models.Model):
    """
    Computed health metrics for each clause version.
    These metrics drive auto-promotion and retirement decisions.
    """
    STATUS_CHOICES = [
        ('ALIVE', 'Alive - Healthy & Active'),
        ('WEAK', 'Weak - Needs Attention'),
        ('RETIRED', 'Retired - No Longer Used'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    clause = models.OneToOneField(
        Clause,
        on_delete=models.CASCADE,
        related_name='health_metrics',
        db_column='clauseId'
    )

    # Health Score Components
    usage_count = models.IntegerField(default=0, db_column='usageCount', help_text='Number of times used')
    success_rate = models.FloatField(default=0.0, db_column='successRate', help_text='Success rate (0-1)')
    enforceability_score = models.FloatField(
        default=0.5,
        db_column='enforceabilityScore',
        help_text='Court enforceability (0-1)'
    )
    negotiation_score = models.FloatField(
        default=0.5,
        db_column='negotiationScore',
        help_text='Ease of negotiation (0-1)'
    )

    # Trust Score Components (Feature #9: Clause Trust Score)
    trust_score = models.FloatField(
        default=0.5,
        db_column='trustScore',
        help_text='Clause Trust Score (CTS) - outcome-based trust (0-1)',
        blank=True,
        null=True
    )
    trust_level = models.CharField(
        max_length=20,
        db_column='trustLevel',
        help_text='Trust level: EXCELLENT, GOOD, FAIR, POOR, CRITICAL',
        blank=True,
        null=True
    )
    trust_badge = models.CharField(
        max_length=30,
        db_column='trustBadge',
        help_text='Trust badge: COURT_PROVEN, DEAL_MAKER, NEGOTIATION_FRAGILE, etc.',
        blank=True,
        null=True
    )
    ambiguity_score = models.FloatField(
        default=0.5,
        db_column='ambiguityScore',
        help_text='Legal ambiguity score (0-1, higher = more ambiguous)',
        blank=True,
        null=True
    )
    litigation_survival_score = models.FloatField(
        default=0.9,
        db_column='litigationSurvivalScore',
        help_text='Litigation survival score (0-1)',
        blank=True,
        null=True
    )

    # Composite Health Score
    health_score = models.FloatField(
        default=0.5,
        db_column='healthScore',
        help_text='Overall health (0-1)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ALIVE',
        help_text='Current health status'
    )

    # Auto-Promotion Tracking
    is_promoted = models.BooleanField(default=False, db_column='isPromoted')
    promoted_at = models.DateTimeField(blank=True, null=True, db_column='promotedAt')
    promotion_reason = models.TextField(blank=True, null=True, db_column='promotionReason')

    last_calculated = models.DateTimeField(auto_now=True, db_column='lastCalculated')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'clause_health_metrics'
        ordering = ['-health_score']
        indexes = [
            models.Index(fields=['-health_score', 'status']),
            models.Index(fields=['status', '-success_rate']),
        ]

    def __str__(self):
        return f"{self.clause.clause_name} - Health: {self.health_score:.2f} ({self.status})"


# ============================================================
# LIVE CLAUSE CO-PILOT (NEGOTIATION MODE) - FEATURE 3
# ============================================================

class NegotiationSession(models.Model):
    """
    Tracks active contract negotiation sessions.
    Supports real-time clause negotiation with AI co-pilot assistance.
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    PARTY_ROLE_CHOICES = [
        ('BUYER', 'Buyer'),
        ('SELLER', 'Seller'),
        ('SERVICE_PROVIDER', 'Service Provider'),
        ('CLIENT', 'Client'),
        ('OTHER', 'Other'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='negotiation_sessions',
        db_column='contractId',
        help_text='Contract being negotiated'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_negotiations',
        db_column='createdBy',
        help_text='User who started the negotiation'
    )

    # Session metadata
    session_name = models.CharField(
        max_length=255,
        db_column='sessionName',
        help_text='Descriptive name for this negotiation'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        help_text='Current session status'
    )
    our_party_role = models.CharField(
        max_length=50,
        choices=PARTY_ROLE_CHOICES,
        db_column='ourPartyRole',
        help_text='Our role in this negotiation (buyer, seller, etc.)'
    )
    counterparty_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_column='counterpartyName',
        help_text='Name of the other party'
    )

    # AI Co-Pilot Settings
    enable_suggestions = models.BooleanField(
        default=True,
        db_column='enableSuggestions',
        help_text='Enable AI clause suggestions'
    )
    risk_tolerance = models.CharField(
        max_length=20,
        choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')],
        default='MEDIUM',
        db_column='riskTolerance',
        help_text='Risk tolerance for suggestions'
    )

    # Negotiation objectives
    objectives = models.JSONField(
        default=list,
        help_text='List of negotiation objectives (e.g., ["Reduce liability cap", "Add termination rights"])'
    )
    must_have_clauses = models.JSONField(
        default=list,
        db_column='mustHaveClauses',
        help_text='Clause IDs that are non-negotiable'
    )
    nice_to_have_clauses = models.JSONField(
        default=list,
        db_column='niceToHaveClauses',
        help_text='Clause IDs that are preferred but negotiable'
    )

    # Session timeline
    started_at = models.DateTimeField(auto_now_add=True, db_column='startedAt')
    completed_at = models.DateTimeField(blank=True, null=True, db_column='completedAt')
    last_activity_at = models.DateTimeField(auto_now=True, db_column='lastActivityAt')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'negotiation_sessions'
        ordering = ['-last_activity_at']
        indexes = [
            models.Index(fields=['contract', '-started_at']),
            models.Index(fields=['status', '-last_activity_at']),
            models.Index(fields=['created_by', '-started_at']),
        ]

    def __str__(self):
        return f"{self.session_name} ({self.status})"


class NegotiationMessage(models.Model):
    """
    Chat messages in a negotiation session.
    Supports both user messages and AI co-pilot responses.
    """
    MESSAGE_TYPE_CHOICES = [
        ('USER', 'User Message'),
        ('AI', 'AI Co-Pilot'),
        ('SYSTEM', 'System Notification'),
        ('SUGGESTION', 'Clause Suggestion'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    session = models.ForeignKey(
        NegotiationSession,
        on_delete=models.CASCADE,
        related_name='messages',
        db_column='sessionId'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='negotiation_messages',
        db_column='senderId',
        blank=True,
        null=True,
        help_text='User who sent the message (null for AI/system)'
    )

    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        db_column='messageType',
        help_text='Type of message'
    )
    content = models.TextField(help_text='Message content')

    # Optional clause reference
    related_clause = models.ForeignKey(
        Clause,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='negotiation_messages',
        db_column='relatedClauseId',
        help_text='Clause being discussed'
    )

    # AI response metadata
    ai_confidence = models.FloatField(
        blank=True,
        null=True,
        db_column='aiConfidence',
        help_text='AI confidence in suggestion (0-1)'
    )
    reasoning = models.TextField(
        blank=True,
        null=True,
        help_text='AI reasoning behind suggestion'
    )

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'negotiation_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['message_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.message_type} in {self.session.session_name}"


class NegotiationClauseSuggestion(models.Model):
    """
    AI-generated clause suggestions during negotiation.
    Provides alternative language, risk analysis, and precedent data.
    """
    SUGGESTION_TYPE_CHOICES = [
        ('ALTERNATIVE', 'Alternative Language'),
        ('STRENGTHEN', 'Strengthen Position'),
        ('COMPROMISE', 'Compromise Option'),
        ('FALLBACK', 'Fallback Position'),
        ('PRECEDENT', 'Based on Precedent'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('MODIFIED', 'Modified and Accepted'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    session = models.ForeignKey(
        NegotiationSession,
        on_delete=models.CASCADE,
        related_name='suggestions',
        db_column='sessionId'
    )
    clause = models.ForeignKey(
        Clause,
        on_delete=models.CASCADE,
        related_name='negotiation_suggestions',
        db_column='clauseId',
        help_text='Clause being negotiated'
    )

    suggestion_type = models.CharField(
        max_length=20,
        choices=SUGGESTION_TYPE_CHOICES,
        db_column='suggestionType'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    # Original and suggested text
    original_text = models.TextField(db_column='originalText')
    suggested_text = models.TextField(db_column='suggestedText')

    # AI analysis
    risk_impact = models.CharField(
        max_length=20,
        choices=[('REDUCES_RISK', 'Reduces Risk'), ('NEUTRAL', 'Neutral'), ('INCREASES_RISK', 'Increases Risk')],
        db_column='riskImpact',
        help_text='Expected risk impact'
    )
    risk_score_delta = models.FloatField(
        db_column='riskScoreDelta',
        help_text='Change in risk score (-1 to +1)'
    )
    rationale = models.TextField(help_text='AI explanation of the suggestion')

    # Precedent data
    similar_clauses_count = models.IntegerField(
        default=0,
        db_column='similarClausesCount',
        help_text='Number of similar clauses in database'
    )
    avg_outcome_score = models.FloatField(
        blank=True,
        null=True,
        db_column='avgOutcomeScore',
        help_text='Average outcome score from precedents'
    )
    precedent_data = models.JSONField(
        default=dict,
        db_column='precedentData',
        help_text='Detailed precedent information'
    )

    # User action
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='reviewed_negotiation_suggestions',
        db_column='reviewedBy'
    )
    reviewed_at = models.DateTimeField(blank=True, null=True, db_column='reviewedAt')
    review_notes = models.TextField(blank=True, null=True, db_column='reviewNotes')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'negotiation_clause_suggestions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session', '-created_at']),
            models.Index(fields=['clause', 'status']),
            models.Index(fields=['status', 'suggestion_type']),
        ]

    def __str__(self):
        return f"{self.suggestion_type} for {self.clause.clause_name} ({self.status})"


class NegotiationPosition(models.Model):
    """
    Tracks each party's position on specific clauses during negotiation.
    Shows evolution of positions over time.
    """
    POSITION_STATUS_CHOICES = [
        ('PROPOSED', 'Proposed'),
        ('COUNTERED', 'Countered'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('STALLED', 'Stalled'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    session = models.ForeignKey(
        NegotiationSession,
        on_delete=models.CASCADE,
        related_name='positions',
        db_column='sessionId'
    )
    clause = models.ForeignKey(
        Clause,
        on_delete=models.CASCADE,
        related_name='negotiation_positions',
        db_column='clauseId'
    )

    # Position details
    iteration = models.IntegerField(
        default=1,
        help_text='Position version number (increments with counteroffers)'
    )
    position_status = models.CharField(
        max_length=20,
        choices=POSITION_STATUS_CHOICES,
        db_column='positionStatus'
    )

    # Our position
    our_text = models.TextField(db_column='ourText', help_text='Our proposed clause text')
    our_priority = models.CharField(
        max_length=20,
        choices=[('MUST_HAVE', 'Must Have'), ('IMPORTANT', 'Important'), ('NICE_TO_HAVE', 'Nice to Have')],
        db_column='ourPriority'
    )
    our_justification = models.TextField(blank=True, null=True, db_column='ourJustification')

    # Their position
    their_text = models.TextField(
        blank=True,
        null=True,
        db_column='theirText',
        help_text='Counterparty proposed text'
    )
    their_feedback = models.TextField(
        blank=True,
        null=True,
        db_column='theirFeedback',
        help_text='Counterparty comments'
    )

    # AI analysis of positions
    gap_analysis = models.JSONField(
        default=dict,
        db_column='gapAnalysis',
        help_text='AI analysis of differences between positions'
    )
    compromise_suggestions = models.JSONField(
        default=list,
        db_column='compromiseSuggestions',
        help_text='AI-generated compromise options'
    )

    # Timeline
    proposed_at = models.DateTimeField(auto_now_add=True, db_column='proposedAt')
    responded_at = models.DateTimeField(blank=True, null=True, db_column='respondedAt')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'negotiation_positions'
        ordering = ['clause', '-iteration']
        indexes = [
            models.Index(fields=['session', 'clause', '-iteration']),
            models.Index(fields=['position_status', '-proposed_at']),
        ]

    def __str__(self):
        return f"{self.clause.clause_name} - Iteration {self.iteration} ({self.position_status})"


# ─────────────────────────────────────────────
# Contract Links (Dependency Graph)
# ─────────────────────────────────────────────
class ContractLink(models.Model):
    """
    Directed dependency edge between two contracts.
    Represents relationships like parent-child, amendment, addendum, or reference.
    """
    LINK_TYPE_CHOICES = [
        ('amendment', 'Amendment'),
        ('addendum', 'Addendum'),
        ('parent_child', 'Parent-Child'),
        ('reference', 'Reference'),
        ('renewal', 'Renewal'),
        ('supersedes', 'Supersedes'),
    ]

    source_contract_id = models.CharField(
        max_length=36,
        db_column='sourceContractId',
        db_index=True,
    )
    target_contract_id = models.CharField(
        max_length=36,
        db_column='targetContractId',
        db_index=True,
    )
    link_type = models.CharField(
        max_length=50,
        choices=LINK_TYPE_CHOICES,
        default='reference',
        db_column='linkType',
        db_index=True,
    )
    description = models.TextField(blank=True, null=True, db_column='description')
    strength = models.FloatField(
        default=1.0,
        help_text='Edge weight (0.0–1.0) for graph algorithms',
        db_column='strength',
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    created_by_id = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        db_column='createdBy',
    )

    class Meta:
        db_table = 'contract_links'
        managed = False  # Table was created via raw SQL migration
        unique_together = [('source_contract_id', 'target_contract_id', 'link_type')]

    def __str__(self):
        return f"{self.source_contract_id} → {self.target_contract_id} ({self.link_type})"


class ClauseCategory(models.Model):
    """
    Dynamic taxonomy node for the Advanced Clause Library.
    Grows automatically as new clause types are discovered.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
        db_constraint=False,
        db_column='parentId',
    )
    clause_count = models.IntegerField(default=0, db_column='clauseCount')
    is_standard = models.BooleanField(default=False, db_column='isStandard')
    embedding_vector = models.JSONField(default=list, blank=True, db_column='embeddingVector')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'clause_categories'
        ordering = ['name']

    def __str__(self):
        return self.name
