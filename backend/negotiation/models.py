import uuid
from django.db import models
from core.models import User, Contract


def generate_uuid():
    """Generate UUID for model primary keys"""
    return str(uuid.uuid4())


class Counterparty(models.Model):
    """
    Represents a counterparty (vendor, partner, client) in negotiations.
    Tracks their negotiation behavior and risk profile.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    name = models.CharField(max_length=255, unique=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    risk_profile = models.FloatField(
        default=0.5,
        help_text='Overall risk profile score (0=low, 1=high)'
    )
    aggressiveness_score = models.FloatField(
        default=0.5,
        help_text='How aggressive in negotiations (0=flexible, 1=aggressive)'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'counterparties'
        verbose_name_plural = 'counterparties'
        ordering = ['name']

    def __str__(self):
        return self.name


class NegotiationHistory(models.Model):
    """
    Historical record of clause-level negotiation outcomes.
    This is the training data for prediction models.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    counterparty = models.ForeignKey(
        Counterparty,
        on_delete=models.CASCADE,
        related_name='negotiation_history',
        db_column='counterpartyId'
    )
    clause_type = models.CharField(
        max_length=100,
        db_column='clauseType',
        help_text='Type of clause (e.g., IP Ownership, Termination)'
    )
    clause_text = models.TextField(
        db_column='clauseText',
        help_text='Original clause text'
    )
    deviation_score = models.FloatField(
        default=0.0,
        db_column='deviationScore',
        help_text='How much it deviates from standard (0-1)'
    )
    accepted = models.BooleanField(
        default=False,
        help_text='Whether the clause was accepted without major changes'
    )
    redline_rounds = models.IntegerField(
        default=0,
        db_column='redlineRounds',
        help_text='Number of negotiation rounds'
    )
    stalled = models.BooleanField(
        default=False,
        help_text='Whether negotiation stalled on this clause'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'negotiation_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['counterparty', 'clause_type']),
            models.Index(fields=['accepted']),
            models.Index(fields=['stalled']),
        ]

    def __str__(self):
        return f"{self.counterparty.name} - {self.clause_type}"


class CounterpartyBehaviorSnapshot(models.Model):
    """
    Periodic snapshot of counterparty behavior metrics.
    Used for trend analysis and dashboard visualization.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    counterparty = models.ForeignKey(
        Counterparty,
        on_delete=models.CASCADE,
        related_name='behavior_snapshots',
        db_column='counterpartyId'
    )
    avg_acceptance_rate = models.FloatField(
        db_column='avgAcceptanceRate',
        help_text='Average clause acceptance rate'
    )
    avg_redline_rounds = models.FloatField(
        db_column='avgRedlineRounds',
        help_text='Average number of redline rounds'
    )
    stall_rate = models.FloatField(
        db_column='stallRate',
        help_text='Percentage of clauses that stalled'
    )
    aggressiveness_score = models.FloatField(
        db_column='aggressivenessScore',
        help_text='Calculated aggressiveness (1 - acceptance_rate)'
    )
    elasticity_score = models.FloatField(
        db_column='elasticityScore',
        help_text='Flexibility after redlines (acceptance / redlines)'
    )
    snapshot_date = models.DateField(
        auto_now_add=True,
        db_column='snapshotDate'
    )

    class Meta:
        db_table = 'counterparty_behavior_snapshots'
        ordering = ['-snapshot_date']
        indexes = [
            models.Index(fields=['counterparty', 'snapshot_date']),
        ]

    def __str__(self):
        return f"{self.counterparty.name} - {self.snapshot_date}"


class ContractNegotiation(models.Model):
    """
    Represents a multi-clause contract negotiation simulation or actual negotiation.
    """
    STATUS_CHOICES = [
        ('SIMULATED', 'Simulated'),
        ('IN_PROGRESS', 'In Progress'),
        ('SIGNED', 'Signed'),
        ('STALLED', 'Stalled'),
        ('ABANDONED', 'Abandoned'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.ForeignKey(
        'core.Contract',
        on_delete=models.CASCADE,
        related_name='negotiations',
        db_column='contractId',
        null=True,
        blank=True
    )
    counterparty = models.ForeignKey(
        Counterparty,
        on_delete=models.CASCADE,
        related_name='negotiations',
        db_column='counterpartyId'
    )
    contract_name = models.CharField(
        max_length=255,
        db_column='contractName',
        help_text='Name or reference of the contract'
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='SIMULATED'
    )
    total_rounds = models.IntegerField(
        default=0,
        db_column='totalRounds',
        help_text='Total number of negotiation rounds'
    )
    stall_probability = models.FloatField(
        default=0.0,
        db_column='stallProbability',
        help_text='Overall probability of negotiation stalling'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'contract_negotiations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['counterparty', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.contract_name} - {self.counterparty.name}"


class NegotiationClauseState(models.Model):
    """
    Represents the state of a single clause within a negotiation.
    Tracks round-by-round progression.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    negotiation = models.ForeignKey(
        ContractNegotiation,
        on_delete=models.CASCADE,
        related_name='clause_states',
        db_column='negotiationId'
    )
    clause_type = models.CharField(
        max_length=100,
        db_column='clauseType',
        help_text='Type of clause'
    )
    proposed_text = models.TextField(
        db_column='proposedText',
        help_text='Proposed clause text'
    )
    accepted = models.BooleanField(
        default=False,
        help_text='Whether this clause has been accepted'
    )
    round_number = models.IntegerField(
        default=0,
        db_column='roundNumber',
        help_text='Negotiation round when this state was recorded'
    )
    acceptance_probability = models.FloatField(
        default=0.0,
        db_column='acceptanceProbability',
        help_text='Predicted probability of acceptance'
    )
    stall_risk = models.FloatField(
        default=0.0,
        db_column='stallRisk',
        help_text='Risk of negotiation stalling on this clause'
    )
    expected_redlines = models.IntegerField(
        default=0,
        db_column='expectedRedlines',
        help_text='Expected number of redline rounds'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'negotiation_clause_states'
        ordering = ['round_number', 'clause_type']
        indexes = [
            models.Index(fields=['negotiation', 'round_number']),
            models.Index(fields=['accepted']),
        ]

    def __str__(self):
        return f"{self.negotiation.contract_name} - {self.clause_type} - Round {self.round_number}"


class SilentRisk(models.Model):
    """
    Represents an emergent risk detected through cross-clause analysis.
    These are risks that don't exist in individual clauses but emerge from interactions.
    """
    RISK_TYPE_CHOICES = [
        ('CROSS_CLAUSE_CONFLICT', 'Cross-Clause Conflict'),
        ('LATENT_FINANCIAL_TRIGGER', 'Latent Financial Trigger'),
        ('DELAYED_LIABILITY', 'Delayed Liability Explosion'),
        ('HIDDEN_COST_ESCALATION', 'Hidden Cost Escalation'),
        ('NON_RECOVERABLE_SPEND', 'Non-Recoverable Spend'),
        ('LONG_TAIL_LIABILITY', 'Long-Tail Liability'),
        ('TERMINATION_PAYMENT_MISMATCH', 'Termination-Payment Mismatch'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.ForeignKey(
        'core.Contract',
        on_delete=models.CASCADE,
        related_name='silent_risks',
        db_column='contractId'
    )
    risk_type = models.CharField(
        max_length=100,
        choices=RISK_TYPE_CHOICES,
        db_column='riskType',
        help_text='Type of emergent risk'
    )
    description = models.TextField(
        help_text='Human-readable description of the risk'
    )
    clause_pair = models.JSONField(
        default=list,
        db_column='clausePair',
        help_text='Array of clause types involved [clauseA, clauseB]'
    )
    financial_exposure = models.FloatField(
        db_column='financialExposure',
        help_text='Estimated financial exposure in contract currency'
    )
    confidence = models.FloatField(
        default=0.0,
        help_text='Confidence score of the detection (0-1)'
    )
    severity = models.CharField(
        max_length=20,
        choices=[
            ('LOW', 'Low'),
            ('MEDIUM', 'Medium'),
            ('HIGH', 'High'),
            ('CRITICAL', 'Critical'),
        ],
        default='MEDIUM'
    )
    detected_at = models.DateTimeField(auto_now_add=True, db_column='detectedAt')

    class Meta:
        db_table = 'silent_risks'
        ordering = ['-severity', '-financial_exposure']
        indexes = [
            models.Index(fields=['contract', 'risk_type']),
            models.Index(fields=['severity']),
            models.Index(fields=['confidence']),
        ]

    def __str__(self):
        return f"{self.contract} - {self.risk_type}"


class SilentRiskHeatmapCache(models.Model):
    """
    Caches the heatmap visualization data for a contract.
    Stores the entire heatmap matrix for fast retrieval.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.OneToOneField(
        'core.Contract',
        on_delete=models.CASCADE,
        related_name='heatmap_cache',
        db_column='contractId',
        help_text='Contract this heatmap belongs to'
    )
    clauses = models.JSONField(
        default=list,
        help_text='List of clause names for the heatmap axes'
    )
    matrix = models.JSONField(
        default=dict,
        help_text='Matrix of risks indexed by "ClauseA|ClauseB"'
    )
    total_risks = models.IntegerField(
        default=0,
        db_column='totalRisks',
        help_text='Total number of risks detected'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'silent_risk_heatmap_cache'
        indexes = [
            models.Index(fields=['contract']),
            models.Index(fields=['updated_at']),
        ]

    def __str__(self):
        return f"Heatmap for {self.contract} - {self.total_risks} risks"


class NegotiationSimulationCache(models.Model):
    """
    Caches negotiation simulation results for a contract-counterparty pair.
    Stores the entire simulation outcome for fast retrieval.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.ForeignKey(
        'core.Contract',
        on_delete=models.CASCADE,
        related_name='simulation_cache',
        db_column='contractId',
        help_text='Contract this simulation belongs to'
    )
    counterparty_name = models.CharField(
        max_length=255,
        db_column='counterpartyName',
        help_text='Name of the counterparty'
    )
    simulation_result = models.JSONField(
        default=dict,
        db_column='simulationResult',
        help_text='Complete simulation result data'
    )
    strategy = models.JSONField(
        default=dict,
        help_text='Recommended negotiation strategy'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'negotiation_simulation_cache'
        unique_together = [['contract', 'counterparty_name']]
        indexes = [
            models.Index(fields=['contract', 'counterparty_name']),
            models.Index(fields=['updated_at']),
        ]

    def __str__(self):
        return f"Simulation for {self.contract} vs {self.counterparty_name}"


class ClauseInteractionPattern(models.Model):
    """
    Stores known patterns of dangerous clause interactions.
    Used as training data for silent risk detection.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    clause_types = models.JSONField(
        db_column='clauseTypes',
        help_text='Array of clause types that interact [clauseA, clauseB]'
    )
    risk_type = models.CharField(
        max_length=100,
        db_column='riskType',
        help_text='Type of risk this pattern creates'
    )
    pattern_description = models.TextField(
        db_column='patternDescription',
        help_text='Description of the dangerous pattern'
    )
    impact_multiplier = models.FloatField(
        default=0.3,
        db_column='impactMultiplier',
        help_text='Multiplier for financial impact calculation'
    )
    vector_embedding = models.JSONField(
        null=True,
        blank=True,
        db_column='vectorEmbedding',
        help_text='Embedding vector for similarity search'
    )
    is_active = models.BooleanField(
        default=True,
        db_column='isActive',
        help_text='Whether this pattern is actively used for detection'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'clause_interaction_patterns'
        ordering = ['-impact_multiplier']

    def __str__(self):
        return f"{' + '.join(self.clause_types)} -> {self.risk_type}"


class NegotiationPrediction(models.Model):
    """
    Stores predictions for negotiation outcomes.
    Used for tracking prediction accuracy over time.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.ForeignKey(
        'core.Contract',
        on_delete=models.CASCADE,
        related_name='negotiation_predictions',
        db_column='contractId',
        null=True,
        blank=True
    )
    counterparty = models.ForeignKey(
        Counterparty,
        on_delete=models.CASCADE,
        related_name='predictions',
        db_column='counterpartyId'
    )
    clause_type = models.CharField(
        max_length=100,
        db_column='clauseType'
    )
    clause_text = models.TextField(db_column='clauseText')
    acceptance_probability = models.FloatField(db_column='acceptanceProbability')
    expected_redlines = models.IntegerField(db_column='expectedRedlines')
    stall_risk = models.FloatField(db_column='stallRisk')
    actual_accepted = models.BooleanField(
        null=True,
        blank=True,
        db_column='actualAccepted',
        help_text='Actual outcome (for validation)'
    )
    actual_redlines = models.IntegerField(
        null=True,
        blank=True,
        db_column='actualRedlines',
        help_text='Actual redline rounds'
    )
    prediction_date = models.DateTimeField(auto_now_add=True, db_column='predictionDate')

    class Meta:
        db_table = 'negotiation_predictions'
        ordering = ['-prediction_date']
        indexes = [
            models.Index(fields=['counterparty', 'clause_type']),
            models.Index(fields=['prediction_date']),
        ]

    def __str__(self):
        return f"{self.counterparty.name} - {self.clause_type} - {self.acceptance_probability:.0%}"


class ExculpatoryPattern(models.Model):
    """
    Stores known exculpatory clause patterns for construction contracts.
    Used for semantic matching and risk detection.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    pattern_id = models.CharField(
        max_length=20,
        unique=True,
        db_column='patternId',
        help_text='Pattern identifier (e.g., EXP_01)'
    )
    label = models.CharField(
        max_length=255,
        help_text='Human-readable pattern label'
    )
    text = models.TextField(
        help_text='Example text of this pattern'
    )
    risk_category = models.CharField(
        max_length=100,
        db_column='riskCategory',
        help_text='Category of risk (SITE_CONDITIONS, DELAY, etc.)'
    )
    controlled_by = models.CharField(
        max_length=50,
        db_column='controlledBy',
        help_text='Who controls this risk (employer, contractor, both, neither)'
    )
    explanation = models.TextField(
        help_text='Explanation of why this pattern is exculpatory'
    )
    vector_embedding = models.JSONField(
        null=True,
        blank=True,
        db_column='vectorEmbedding',
        help_text='MiniLM embedding vector for similarity search'
    )
    is_active = models.BooleanField(
        default=True,
        db_column='isActive',
        help_text='Whether this pattern is actively used'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'exculpatory_patterns'
        ordering = ['pattern_id']

    def __str__(self):
        return f"{self.pattern_id} - {self.label}"


class ExculpatoryAnalysis(models.Model):
    """
    Stores cached exculpatory clause analysis results for a contract.
    Contains aggregate statistics and recommendations.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.OneToOneField(
        'core.Contract',
        on_delete=models.CASCADE,
        related_name='exculpatory_analysis',
        db_column='contractId'
    )
    total_clauses = models.IntegerField(
        default=0,
        db_column='totalClauses',
        help_text='Total number of clauses analyzed'
    )
    analyzed_clauses = models.IntegerField(
        default=0,
        db_column='analyzedClauses',
        help_text='Number of clauses processed'
    )
    high_risk_count = models.IntegerField(
        default=0,
        db_column='highRiskCount',
        help_text='Number of high-risk clauses'
    )
    medium_risk_count = models.IntegerField(
        default=0,
        db_column='mediumRiskCount',
        help_text='Number of medium-risk clauses'
    )
    low_risk_count = models.IntegerField(
        default=0,
        db_column='lowRiskCount',
        help_text='Number of low-risk clauses'
    )
    imbalanced_count = models.IntegerField(
        default=0,
        db_column='imbalancedCount',
        help_text='Number of clauses with risk allocation imbalance'
    )
    category_breakdown = models.JSONField(
        default=dict,
        db_column='categoryBreakdown',
        help_text='Risk count by category {SITE_CONDITIONS: 3, DELAY: 2, ...}'
    )
    recommendation = models.JSONField(
        default=dict,
        help_text='Overall recommendation {decision: "HIGH_RISK", message: "..."}'
    )
    analyzed_at = models.DateTimeField(auto_now_add=True, db_column='analyzedAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'exculpatory_analysis'
        indexes = [
            models.Index(fields=['contract']),
            models.Index(fields=['analyzed_at']),
        ]

    def __str__(self):
        return f"Exculpatory Analysis for {self.contract} - {self.high_risk_count} high risk"


class ExculpatoryClause(models.Model):
    """
    Stores individual clause analysis results.
    Links clauses to their risk scores and pattern matches.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    analysis = models.ForeignKey(
        ExculpatoryAnalysis,
        on_delete=models.CASCADE,
        related_name='clauses',
        db_column='analysisId'
    )
    clause_name = models.CharField(
        max_length=255,
        db_column='clauseName',
        help_text='Name or identifier of the clause'
    )
    text = models.TextField(
        help_text='Full clause text'
    )
    risk_score = models.FloatField(
        db_column='riskScore',
        help_text='Overall risk score (0.0-1.0)'
    )
    is_exculpatory = models.BooleanField(
        db_column='isExculpatory',
        help_text='Whether clause is classified as exculpatory'
    )
    risk_category = models.CharField(
        max_length=100,
        db_column='riskCategory',
        help_text='Primary risk category'
    )
    controlled_by = models.CharField(
        max_length=50,
        db_column='controlledBy',
        help_text='Who controls this risk'
    )
    bearer = models.CharField(
        max_length=50,
        help_text='Who bears the risk'
    )
    is_imbalanced = models.BooleanField(
        db_column='isImbalanced',
        help_text='Whether risk allocation is imbalanced'
    )
    imbalance_explanation = models.TextField(
        blank=True,
        db_column='imbalanceExplanation',
        help_text='Explanation of the imbalance'
    )
    pattern_matches = models.JSONField(
        default=list,
        db_column='patternMatches',
        help_text='Array of matched patterns [{pattern: "...", similarity: 0.85}]'
    )
    suggestions = models.JSONField(
        default=list,
        help_text='Array of mitigation suggestions for this clause'
    )
    vector_embedding = models.JSONField(
        null=True,
        blank=True,
        db_column='vectorEmbedding',
        help_text='Clause embedding for similarity search'
    )
    # Enhanced fields from Prof. Murali's research
    imbalance_severity = models.CharField(
        max_length=20,
        default='LOW',
        db_column='imbalanceSeverity',
        help_text='FIDIC-based imbalance severity: EXTREME, HIGH, MODERATE, LOW, BALANCED'
    )
    imbalance_score = models.FloatField(
        default=0.0,
        db_column='imbalanceScore',
        help_text='Quantitative imbalance score (0.0-1.0) based on FIDIC principles'
    )
    financial_exposure = models.JSONField(
        default=dict,
        db_column='financialExposure',
        help_text='Financial exposure estimates {maximum_exposure, likely_exposure, minimum_exposure}'
    )
    proper_allocation_advice = models.TextField(
        blank=True,
        db_column='properAllocationAdvice',
        help_text='FIDIC-based advice on proper risk allocation for this category'
    )
    impact_chain_data = models.JSONField(
        null=True,
        blank=True,
        db_column='impactChainData',
        help_text='Complete impact chain: why → impact → suggestion'
    )
    deal_breaker = models.BooleanField(
        default=False,
        db_column='dealBreaker',
        help_text='Whether this risk is severe enough to be a deal breaker'
    )
    probability = models.CharField(
        max_length=20,
        default='MEDIUM',
        help_text='Probability of risk materializing: HIGH, MEDIUM, LOW'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'exculpatory_clauses'
        ordering = ['-risk_score']
        indexes = [
            models.Index(fields=['analysis', 'risk_score']),
            models.Index(fields=['is_exculpatory']),
            models.Index(fields=['is_imbalanced']),
            models.Index(fields=['deal_breaker']),
        ]

    def __str__(self):
        return f"{self.clause_name} - Risk: {self.risk_score:.2f}"


# ─── AI Studio: Advanced Multi-Agent Negotiation Engine Models ────────
# Note: class names are prefixed with "Engine" to avoid collisions with
# the existing NegotiationSession / NegotiationMessage in core.models.

class EngineNegotiationSession(models.Model):
    """
    Stores the full state of one advanced negotiation engine session,
    including round-by-round scores and clause evolution history.
    """
    session_id = models.CharField(
        max_length=36, primary_key=True, default=generate_uuid, editable=False
    )
    contract_id = models.CharField(
        max_length=36, null=True, blank=True, db_column='contractId'
    )
    original_clause = models.TextField(db_column='originalClause')
    final_clause    = models.TextField(blank=True, db_column='finalClause')
    best_clause     = models.TextField(blank=True, db_column='bestClause')

    rounds_requested = models.IntegerField(default=3, db_column='roundsRequested')
    rounds_completed = models.IntegerField(default=0, db_column='roundsCompleted')

    converged         = models.BooleanField(default=False)
    convergence_round = models.IntegerField(null=True, blank=True, db_column='convergenceRound')
    best_round        = models.IntegerField(default=1, db_column='bestRound')
    final_score       = models.FloatField(default=0.0, db_column='finalScore')
    score_trend       = models.CharField(max_length=20, default='stable', db_column='scoreTrend')

    # JSON blobs – stored in the DB for persistence; also available in-response
    round_scores            = models.JSONField(default=list, db_column='roundScores')
    clause_history          = models.JSONField(default=list, db_column='clauseHistory')
    agent_strategy_weights  = models.JSONField(default=dict, db_column='agentStrategyWeights')
    reasoning               = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'engine_negotiation_sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contract_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['final_score']),
        ]

    def __str__(self):
        return f"Session {self.session_id[:8]}… score={self.final_score:.2f}"


class EngineNegotiationMessage(models.Model):
    """
    Individual agent message within an EngineNegotiationSession.
    One row per agent per round.
    """
    message_id = models.CharField(
        max_length=36, primary_key=True, default=generate_uuid, editable=False,
        db_column='messageId'
    )
    session = models.ForeignKey(
        EngineNegotiationSession,
        on_delete=models.CASCADE,
        related_name='messages',
        db_column='sessionId'
    )
    round_number    = models.IntegerField(db_column='roundNumber')
    agent_name      = models.CharField(max_length=50, db_column='agentName')
    agent_color     = models.CharField(max_length=30, db_column='agentColor')
    proposed_clause = models.TextField(db_column='proposedClause')
    justification   = models.TextField(blank=True)
    risk_impact     = models.FloatField(default=0.30, db_column='riskImpact')
    financial_impact = models.FloatField(default=0.00, db_column='financialImpact')
    compliance_score = models.FloatField(default=0.60, db_column='complianceScore')
    round_score     = models.FloatField(default=0.00, db_column='roundScore')
    timestamp       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'engine_negotiation_messages'
        ordering = ['round_number', 'agent_name']
        indexes = [
            models.Index(fields=['session', 'round_number']),
            models.Index(fields=['agent_name']),
        ]

    def __str__(self):
        return f"[R{self.round_number}] {self.agent_name} → {self.session_id}"


class EngineNegotiationOutcome(models.Model):
    """
    Records the real-world outcome of a deal that originated from a session.
    This feeds the RL strategy-weight update.
    """
    OUTCOME_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
        ('PARTIAL', 'Partial Success'),
        ('ONGOING', 'Ongoing'),
    ]

    session = models.OneToOneField(
        EngineNegotiationSession,
        on_delete=models.CASCADE,
        related_name='outcome',
        db_column='sessionId'
    )
    deal_outcome    = models.CharField(
        max_length=20, choices=OUTCOME_CHOICES, default='ONGOING',
        db_column='dealOutcome'
    )
    profit_margin   = models.FloatField(default=0.0, db_column='profitMargin')
    delay_days      = models.IntegerField(default=0, db_column='delayDays')
    dispute_count   = models.IntegerField(default=0, db_column='disputeCount')

    updated_strategy_weights = models.JSONField(
        default=dict, db_column='updatedStrategyWeights',
        help_text='Agent weights after RL update'
    )
    rl_feedback_processed = models.BooleanField(
        default=False, db_column='rlFeedbackProcessed'
    )
    evaluated_at = models.DateTimeField(auto_now_add=True, db_column='evaluatedAt')

    class Meta:
        db_table = 'engine_negotiation_outcomes'
        ordering = ['-evaluated_at']
        indexes = [
            models.Index(fields=['deal_outcome']),
            models.Index(fields=['evaluated_at']),
        ]

    def __str__(self):
        return f"Outcome({self.deal_outcome}) for session {self.session.session_id}"


# ──────────────────────────────────────────────────────────────────────────────
# Contract Analysis Pipeline Storage
# Stores the full output of the Contract Intelligence Orchestrator so that
# every other module (Benchmarking, Volatility, Risk vs Margin, etc.) can
# read from a single source of truth instead of re-running the pipeline.
# ──────────────────────────────────────────────────────────────────────────────

class ContractAnalysisResult(models.Model):
    """Top-level record for one full pipeline run."""
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    analysis_id = models.CharField(max_length=36, unique=True, db_column='analysisId')
    # Optional FK to a core Contract – null when input was raw text / file upload
    contract = models.ForeignKey(
        'core.Contract', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orchestrator_analyses', db_column='contractId',
    )
    contract_id_ref = models.CharField(max_length=36, null=True, blank=True, db_column='contractIdRef')
    jurisdiction = models.CharField(max_length=10, default='india')
    contract_value = models.FloatField(default=0, db_column='contractValue')
    duration_months = models.IntegerField(default=12, db_column='durationMonths')

    # Scores
    final_score = models.FloatField(default=0, db_column='finalScore')
    decision = models.CharField(max_length=20, default='RENEGOTIATE')

    # JSON blobs – each module queries what it needs
    score_breakdown = models.JSONField(default=dict, db_column='scoreBreakdown')
    risk_summary = models.JSONField(default=dict, db_column='riskSummary')
    cfo_result = models.JSONField(default=dict, db_column='cfoResult')
    recommendations = models.JSONField(default=list)
    pipeline_trace = models.JSONField(default=list, db_column='pipelineTrace')
    total_duration_ms = models.FloatField(default=0, db_column='totalDurationMs')

    # Input source: 'contract_id' | 'file_upload' | 'raw_text'
    input_source = models.CharField(max_length=20, default='raw_text', db_column='inputSource')
    status = models.CharField(max_length=20, default='complete')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'contract_analysis_results'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contract_id_ref']),
            models.Index(fields=['decision']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Analysis {self.analysis_id[:8]} · {self.decision} · {self.final_score:.1f}"


class AnalysisClause(models.Model):
    """Clause extracted during a pipeline run."""
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    analysis = models.ForeignKey(
        ContractAnalysisResult, on_delete=models.CASCADE, related_name='stored_clauses',
    )
    clause_ref_id = models.CharField(max_length=100, db_column='clauseRefId')
    title = models.CharField(max_length=500)
    text = models.TextField()
    clause_type = models.CharField(max_length=100, default='general', db_column='clauseType')

    class Meta:
        db_table = 'analysis_clauses'
        indexes = [models.Index(fields=['analysis'])]

    def __str__(self):
        return f"{self.title} ({self.analysis.analysis_id[:8]})"


class AnalysisClauseRisk(models.Model):
    """Legal risk assessment for one clause in a pipeline run."""
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    analysis = models.ForeignKey(
        ContractAnalysisResult, on_delete=models.CASCADE, related_name='stored_clause_risks',
    )
    clause = models.ForeignKey(
        AnalysisClause, on_delete=models.SET_NULL, null=True, blank=True, related_name='risks',
    )
    clause_ref_id = models.CharField(max_length=100, db_column='clauseRefId')
    clause_title = models.CharField(max_length=500, db_column='clauseTitle')
    risk_level = models.CharField(max_length=20, db_column='riskLevel')  # CRITICAL | HIGH | MEDIUM | LOW
    compliance_status = models.CharField(max_length=100, blank=True, db_column='complianceStatus')
    confidence_score = models.FloatField(default=0.5, db_column='confidenceScore')
    issues = models.JSONField(default=list)
    explanation = models.TextField(blank=True)
    suggested_clause = models.TextField(blank=True, db_column='suggestedClause')
    rule_flags = models.JSONField(default=list, db_column='ruleFlags')

    class Meta:
        db_table = 'analysis_clause_risks'
        indexes = [
            models.Index(fields=['analysis', 'risk_level']),
        ]

    def __str__(self):
        return f"{self.clause_title} – {self.risk_level}"


class AnalysisNegotiationResult(models.Model):
    """Multi-agent negotiation result for one clause in a pipeline run."""
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    analysis = models.ForeignKey(
        ContractAnalysisResult, on_delete=models.CASCADE, related_name='stored_negotiation_results',
    )
    clause_ref_id = models.CharField(max_length=100, db_column='clauseRefId')
    clause_title = models.CharField(max_length=500, db_column='clauseTitle')
    original_risk = models.CharField(max_length=20, db_column='originalRisk')
    final_clause = models.TextField(blank=True, db_column='finalClause')
    best_clause = models.TextField(blank=True, db_column='bestClause')
    final_score = models.FloatField(default=0, db_column='finalScore')
    converged = models.BooleanField(default=False)
    rounds_completed = models.IntegerField(default=0, db_column='roundsCompleted')
    score_trend = models.CharField(max_length=50, blank=True, db_column='scoreTrend')

    class Meta:
        db_table = 'analysis_negotiation_results'
        indexes = [models.Index(fields=['analysis'])]

    def __str__(self):
        return f"Negotiation({self.clause_title}) – score {self.final_score:.2f}"
