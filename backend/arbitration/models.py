"""
Arbitration Risk Intelligence - Database Models
=================================================
Enterprise models for $100M+ EPC contract arbitration analysis.

Models:
- ArbitrationAnalysis: Master analysis record with summary metrics
- ArbitrationClause: Individual clause with 8-dimensional risk vector
- TribunalSimulation: Arbitrator panel simulation results
- ArbitrationScenario: Scenario analysis (seat × tribunal × cost)
- HistoricalArbitrationCase: Training data for GNN dispute prediction
- ClauseRewrite: AI-generated clause improvements
"""

from django.db import models
from core.models import Contract, generate_uuid


class ArbitrationAnalysis(models.Model):
    """
    Master arbitration risk analysis for a contract.
    Stores summary metrics and links to detailed clause analysis.
    """
    RISK_LEVEL_CHOICES = [
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
        ('CRITICAL', 'Critical Risk'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='arbitration_analyses',
        db_column='contractId',
        help_text='Contract being analyzed'
    )

    # Summary metrics
    total_clauses = models.IntegerField(default=0, db_column='totalClauses')
    high_risk_clauses = models.IntegerField(default=0, db_column='highRiskClauses')
    medium_risk_clauses = models.IntegerField(default=0, db_column='mediumRiskClauses')
    low_risk_clauses = models.IntegerField(default=0, db_column='lowRiskClauses')

    # Risk scores
    avg_composite_risk = models.FloatField(default=0.0, db_column='avgCompositeRisk', help_text='Average composite risk score 0.0-1.0')
    dispute_probability = models.FloatField(default=0.0, db_column='disputeProbability', help_text='Probability of arbitration dispute')
    overall_risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='MEDIUM', db_column='overallRiskLevel')

    # Monte Carlo results
    expected_loss = models.DecimalField(max_digits=18, decimal_places=2, default=0, db_column='expectedLoss')
    median_loss = models.DecimalField(max_digits=18, decimal_places=2, default=0, db_column='medianLoss')
    p75_loss = models.DecimalField(max_digits=18, decimal_places=2, default=0, db_column='p75Loss')
    p90_loss = models.DecimalField(max_digits=18, decimal_places=2, default=0, db_column='p90Loss')
    worst_case_p95 = models.DecimalField(max_digits=18, decimal_places=2, default=0, db_column='worstCaseP95')
    var_99 = models.DecimalField(max_digits=18, decimal_places=2, default=0, db_column='var99')
    std_deviation = models.DecimalField(max_digits=18, decimal_places=2, default=0, db_column='stdDeviation')

    # Tribunal simulation results
    buyer_win_probability = models.FloatField(default=0.0, db_column='buyerWinProbability')
    supplier_win_probability = models.FloatField(default=0.0, db_column='supplierWinProbability')
    partial_award_probability = models.FloatField(default=0.0, db_column='partialAwardProbability')
    settlement_probability = models.FloatField(default=0.0, db_column='settlementProbability')
    expected_award = models.DecimalField(max_digits=18, decimal_places=2, default=0, db_column='expectedAward')

    # Exposure & settlement
    arbitration_exposure = models.DecimalField(max_digits=18, decimal_places=2, default=0, db_column='arbitrationExposure')
    legal_cost_estimate = models.DecimalField(max_digits=18, decimal_places=2, default=0, db_column='legalCostEstimate')
    total_exposure = models.DecimalField(max_digits=18, decimal_places=2, default=0, db_column='totalExposure')

    # Settlement recommendation
    settlement_offer = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True, db_column='settlementOffer')
    settlement_decision = models.CharField(max_length=50, blank=True, null=True, db_column='settlementDecision', help_text='SETTLE or PROCEED_TO_ARBITRATION')
    potential_saving = models.DecimalField(max_digits=18, decimal_places=2, default=0, db_column='potentialSaving')

    # Optimal configuration
    optimal_seat = models.CharField(max_length=50, blank=True, null=True, db_column='optimalSeat')
    optimal_tribunal = models.CharField(max_length=50, blank=True, null=True, db_column='optimalTribunal')
    optimal_cost_rule = models.CharField(max_length=50, blank=True, null=True, db_column='optimalCostRule')
    optimal_institution = models.CharField(max_length=50, blank=True, null=True, db_column='optimalInstitution')
    optimal_expected_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0, db_column='optimalExpectedCost')

    # GNN prediction results (when implemented)
    gnn_dispute_probability = models.FloatField(null=True, blank=True, db_column='gnnDisputeProbability', help_text='GNN model dispute prediction')
    gnn_confidence = models.FloatField(null=True, blank=True, db_column='gnnConfidence', help_text='GNN prediction confidence')

    # Metadata
    monte_carlo_runs = models.IntegerField(default=50000, db_column='monteCarloRuns')
    tribunal_runs = models.IntegerField(default=5000, db_column='tribunalRuns')
    analysis_version = models.CharField(max_length=20, default='1.0', db_column='analysisVersion')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'arbitration_analyses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contract', '-created_at']),
            models.Index(fields=['overall_risk_level']),
            models.Index(fields=['dispute_probability']),
        ]

    def __str__(self):
        return f"Arbitration Analysis for {self.contract.original_filename} ({self.created_at.date()})"

    @property
    def risk_level_display(self):
        """Human-readable risk level with emoji"""
        mapping = {
            'LOW': '🟢 Low Risk',
            'MEDIUM': '🟡 Medium Risk',
            'HIGH': '🟠 High Risk',
            'CRITICAL': '🔴 Critical Risk',
        }
        return mapping.get(self.overall_risk_level, self.overall_risk_level)


class ArbitrationClause(models.Model):
    """
    Individual arbitration clause with 8-dimensional risk vector.
    """
    RISK_LEVEL_CHOICES = [
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    analysis = models.ForeignKey(
        ArbitrationAnalysis,
        on_delete=models.CASCADE,
        related_name='clauses',
        db_column='analysisId'
    )

    # Clause content
    clause_index = models.IntegerField(db_column='clauseIndex', help_text='Order in contract')
    clause_text = models.TextField(db_column='clauseText')
    confidence = models.FloatField(default=0.0, help_text='Extraction confidence 0.0-1.0')
    pattern_hits = models.IntegerField(default=0, db_column='patternHits')

    # 8-dimensional risk vector
    jurisdiction_risk = models.FloatField(default=0.0, db_column='jurisdictionRisk')
    cost_exposure = models.FloatField(default=0.0, db_column='costExposure')
    institutional_risk = models.FloatField(default=0.0, db_column='institutionalRisk')
    tribunal_structure = models.FloatField(default=0.0, db_column='tribunalStructure')
    procedural_risk = models.FloatField(default=0.0, db_column='proceduralRisk')
    enforcement_risk = models.FloatField(default=0.0, db_column='enforcementRisk')
    delay_dispute_risk = models.FloatField(default=0.0, db_column='delayDisputeRisk')
    subcontractor_pass_through = models.FloatField(default=0.0, db_column='subcontractorPassThrough')
    composite_risk = models.FloatField(default=0.0, db_column='compositeRisk')

    # Classification
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='MEDIUM', db_column='riskLevel')

    # Semantic embeddings (LegalBERT - 768 dimensions stored as JSON)
    embedding = models.JSONField(null=True, blank=True, help_text='LegalBERT embedding vector')

    # Neo4j graph node ID (when synced)
    graph_node_id = models.CharField(max_length=50, null=True, blank=True, db_column='graphNodeId')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'arbitration_clauses'
        ordering = ['analysis', 'clause_index']
        indexes = [
            models.Index(fields=['analysis', 'clause_index']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['composite_risk']),
        ]

    def __str__(self):
        return f"Clause {self.clause_index} - {self.risk_level} ({self.composite_risk:.2f})"


class TribunalSimulation(models.Model):
    """
    Tribunal arbitrator panel simulation results.
    Stores detailed arbitrator composition and voting patterns.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    analysis = models.ForeignKey(
        ArbitrationAnalysis,
        on_delete=models.CASCADE,
        related_name='tribunal_simulations',
        db_column='analysisId'
    )

    # Simulation parameters
    runs = models.IntegerField(default=5000, help_text='Number of Monte Carlo tribunal simulations')

    # Input features
    clause_strength = models.FloatField(db_column='clauseStrength')
    precedent_score = models.FloatField(db_column='precedentScore')
    jurisdiction_score = models.FloatField(db_column='jurisdictionScore')
    claim_strength = models.FloatField(db_column='claimStrength')
    delay_evidence = models.FloatField(db_column='delayEvidence')

    # Outcome probabilities
    buyer_win_prob = models.FloatField(db_column='buyerWinProb')
    supplier_win_prob = models.FloatField(db_column='supplierWinProb')
    partial_award_prob = models.FloatField(db_column='partialAwardProb')
    settlement_prob = models.FloatField(db_column='settlementProb')

    # Award estimation
    expected_award = models.DecimalField(max_digits=18, decimal_places=2, db_column='expectedAward')
    avg_tribunal_score = models.FloatField(db_column='avgTribunalScore')
    score_std = models.FloatField(db_column='scoreStd', help_text='Standard deviation of tribunal scores')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'arbitration_tribunal_simulations'
        ordering = ['-created_at']

    def __str__(self):
        return f"Tribunal Sim ({self.runs} runs) - Buyer Win: {self.buyer_win_prob:.2%}"


class ArbitrationScenario(models.Model):
    """
    Individual arbitration scenario configuration.
    Stores seat × tribunal × cost_rule × institution combinations.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    analysis = models.ForeignKey(
        ArbitrationAnalysis,
        on_delete=models.CASCADE,
        related_name='scenarios',
        db_column='analysisId'
    )

    # Configuration
    seat = models.CharField(max_length=50, help_text='Arbitration seat (london, singapore, etc.)')
    tribunal_size = models.CharField(max_length=50, db_column='tribunalSize', help_text='single_arbitrator, three_member, etc.')
    cost_rule = models.CharField(max_length=50, db_column='costRule', help_text='equal_sharing, loser_pays, etc.')
    institution = models.CharField(max_length=50, help_text='ICC, LCIA, SIAC, etc.')

    # Results
    expected_cost = models.DecimalField(max_digits=18, decimal_places=2, db_column='expectedCost')
    total_exposure = models.DecimalField(max_digits=18, decimal_places=2, db_column='totalExposure')
    risk_index = models.FloatField(db_column='riskIndex', help_text='Composite risk multiplier')

    # Ranking
    is_optimal = models.BooleanField(default=False, db_column='isOptimal', help_text='Lowest cost configuration')
    is_worst = models.BooleanField(default=False, db_column='isWorst', help_text='Highest cost configuration')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'arbitration_scenarios'
        ordering = ['expected_cost']
        indexes = [
            models.Index(fields=['analysis', 'expected_cost']),
            models.Index(fields=['is_optimal']),
            models.Index(fields=['is_worst']),
        ]

    def __str__(self):
        return f"{self.seat.title()} / {self.tribunal_size} / {self.cost_rule} - ${self.expected_cost:,.0f}"


class HistoricalArbitrationCase(models.Model):
    """
    Historical arbitration cases for GNN training and outcome prediction.
    Stores real-world arbitration awards for machine learning.
    """
    OUTCOME_CHOICES = [
        ('BUYER_WIN', 'Buyer Win'),
        ('SUPPLIER_WIN', 'Supplier Win'),
        ('PARTIAL_AWARD', 'Partial Award'),
        ('SETTLEMENT', 'Settlement'),
        ('DISMISSED', 'Dismissed'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)

    # Case metadata
    case_number = models.CharField(max_length=100, unique=True, db_column='caseNumber')
    case_year = models.IntegerField(db_column='caseYear')
    institution = models.CharField(max_length=50, help_text='ICC, LCIA, SIAC, etc.')
    seat = models.CharField(max_length=100, help_text='Arbitration seat')
    governing_law = models.CharField(max_length=100, db_column='governingLaw')

    # Contract details
    contract_type = models.CharField(max_length=100, db_column='contractType', help_text='EPC, service, supply, etc.')
    contract_value = models.DecimalField(max_digits=18, decimal_places=2, db_column='contractValue')
    industry_sector = models.CharField(max_length=100, db_column='industrySector', blank=True, null=True)

    # Tribunal composition
    number_of_arbitrators = models.IntegerField(db_column='numberOfArbitrators', default=3)
    tribunal_composition = models.CharField(max_length=200, blank=True, null=True, db_column='tribunalComposition')

    # Dispute characteristics
    has_delay_claims = models.BooleanField(default=False, db_column='hasDelayClaims')
    has_liquidated_damages = models.BooleanField(default=False, db_column='hasLiquidatedDamages')
    has_cost_shifting = models.BooleanField(default=False, db_column='hasCostShifting')
    has_subcontractor_dispute = models.BooleanField(default=False, db_column='hasSubcontractorDispute')
    has_multi_party = models.BooleanField(default=False, db_column='hasMultiParty')

    # Risk scores (if known)
    jurisdiction_risk_score = models.FloatField(null=True, blank=True, db_column='jurisdictionRiskScore')
    enforcement_risk_score = models.FloatField(null=True, blank=True, db_column='enforcementRiskScore')
    procedural_complexity = models.FloatField(null=True, blank=True, db_column='proceduralComplexity')

    # Outcome
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES)
    award_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True, db_column='awardAmount')
    award_percentage = models.FloatField(null=True, blank=True, db_column='awardPercentage', help_text='Award as % of claim')
    arbitration_cost = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True, db_column='arbitrationCost')

    # Duration
    duration_months = models.IntegerField(null=True, blank=True, db_column='durationMonths')

    # Text data
    case_summary = models.TextField(blank=True, null=True, db_column='caseSummary')
    key_issues = models.JSONField(null=True, blank=True, db_column='keyIssues', help_text='List of key dispute issues')

    # Graph embeddings (for GNN training)
    graph_features = models.JSONField(null=True, blank=True, db_column='graphFeatures', help_text='Graph neural network features')
    clause_embedding = models.JSONField(null=True, blank=True, db_column='clauseEmbedding', help_text='Average clause embeddings')

    # Training metadata
    used_for_training = models.BooleanField(default=True, db_column='usedForTraining')
    data_source = models.CharField(max_length=200, blank=True, null=True, db_column='dataSource')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'historical_arbitration_cases'
        ordering = ['-case_year', 'case_number']
        indexes = [
            models.Index(fields=['institution', 'outcome']),
            models.Index(fields=['case_year']),
            models.Index(fields=['contract_type']),
            models.Index(fields=['used_for_training']),
        ]

    def __str__(self):
        return f"{self.case_number} ({self.case_year}) - {self.outcome}"


class ClauseRewrite(models.Model):
    """
    AI-generated clause improvements for buyer-favorable terms.
    Stores LLM-based clause rewrites with comparison metrics.
    """
    REWRITE_STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('IMPLEMENTED', 'Implemented'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    clause = models.ForeignKey(
        ArbitrationClause,
        on_delete=models.CASCADE,
        related_name='rewrites',
        db_column='clauseId'
    )

    # Original clause
    original_text = models.TextField(db_column='originalText')
    original_risk_score = models.FloatField(db_column='originalRiskScore')

    # Rewritten clause
    rewritten_text = models.TextField(db_column='rewrittenText')
    predicted_risk_score = models.FloatField(db_column='predictedRiskScore', help_text='Expected risk after rewrite')

    # Improvements
    risk_reduction = models.FloatField(db_column='riskReduction', help_text='Reduction in risk score')
    improvements = models.JSONField(help_text='List of specific improvements made')

    # Rewrite parameters
    rewrite_strategy = models.CharField(max_length=100, db_column='rewriteStrategy', help_text='buyer_favorable, balanced, supplier_favorable')
    llm_model = models.CharField(max_length=100, db_column='llmModel', default='qwen2.5:0.5b')
    temperature = models.FloatField(default=0.3, help_text='LLM temperature parameter')

    # Review status
    status = models.CharField(max_length=20, choices=REWRITE_STATUS_CHOICES, default='DRAFT')
    reviewed_by = models.CharField(max_length=255, blank=True, null=True, db_column='reviewedBy')
    review_notes = models.TextField(blank=True, null=True, db_column='reviewNotes')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'arbitration_clause_rewrites'
        ordering = ['-risk_reduction', '-created_at']
        indexes = [
            models.Index(fields=['clause', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['-risk_reduction']),
        ]

    def __str__(self):
        return f"Rewrite ({self.risk_reduction:.1%} reduction) - {self.status}"


class GNNPrediction(models.Model):
    """
    Graph Neural Network dispute prediction results.
    Stores GNN model predictions for arbitration outcome.
    """
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    analysis = models.ForeignKey(
        ArbitrationAnalysis,
        on_delete=models.CASCADE,
        related_name='gnn_predictions',
        db_column='analysisId'
    )

    # Model metadata
    model_version = models.CharField(max_length=50, db_column='modelVersion', help_text='GNN model version')
    model_checkpoint = models.CharField(max_length=255, db_column='modelCheckpoint', help_text='Path to model weights')

    # Predictions
    dispute_probability = models.FloatField(db_column='disputeProbability')
    buyer_win_probability = models.FloatField(db_column='buyerWinProbability')
    supplier_win_probability = models.FloatField(db_column='supplierWinProbability')
    partial_award_probability = models.FloatField(db_column='partialAwardProbability')
    settlement_probability = models.FloatField(db_column='settlementProbability')

    # Confidence metrics
    prediction_confidence = models.FloatField(db_column='predictionConfidence')
    model_certainty = models.FloatField(db_column='modelCertainty', help_text='Model confidence score')

    # Graph features used
    node_count = models.IntegerField(db_column='nodeCount')
    edge_count = models.IntegerField(db_column='edgeCount')
    avg_node_degree = models.FloatField(db_column='avgNodeDegree')
    graph_density = models.FloatField(db_column='graphDensity')

    # Explainability
    top_influential_clauses = models.JSONField(db_column='topInfluentialClauses', help_text='Most influential clause IDs')
    attention_weights = models.JSONField(null=True, blank=True, db_column='attentionWeights', help_text='GAT attention weights')

    # Performance
    inference_time_ms = models.FloatField(db_column='inferenceTimeMs', help_text='Prediction latency in milliseconds')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'arbitration_gnn_predictions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['analysis', '-created_at']),
            models.Index(fields=['model_version']),
        ]

    def __str__(self):
        return f"GNN Prediction (Dispute: {self.dispute_probability:.1%}, Confidence: {self.prediction_confidence:.1%})"
