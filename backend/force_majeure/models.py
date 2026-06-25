"""
Force Majeure Intelligence Engine — Models
==========================================
DB conventions:
- PKs: CharField uuid (generate_uuid pattern)
- db_column camelCase
- No FK constraints to legacy tables (CharField IDs)
- Timestamps: auto_now_add for created, auto_now for updated
"""
import uuid
from django.db import models


def generate_uuid():
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# FM Prediction — core output of the Risk Predictor engine
# ---------------------------------------------------------------------------
class FMPrediction(models.Model):
    """
    Stores AI-generated Force Majeure risk prediction for a contract.
    Combines Bayesian network + Monte Carlo + Qwen explanation.
    """
    id = models.CharField(
        primary_key=True, max_length=36, default=generate_uuid, db_column='id'
    )
    contract_id = models.CharField(max_length=36, db_column='contractId', db_index=True)
    contract_title = models.CharField(max_length=512, blank=True, db_column='contractTitle')
    contract_text = models.TextField(blank=True, db_column='contractText')

    # Overall FM risk probability (0-1)
    fm_risk_score = models.FloatField(default=0.0, db_column='fmRiskScore')
    fm_invocation_probability = models.FloatField(default=0.0, db_column='fmInvocationProbability')
    project_delay_probability = models.FloatField(default=0.0, db_column='projectDelayProbability')
    cost_overrun_probability = models.FloatField(default=0.0, db_column='costOverrunProbability')
    contract_suspension_probability = models.FloatField(default=0.0, db_column='contractSuspensionProbability')
    contract_termination_probability = models.FloatField(default=0.0, db_column='contractTerminationProbability')

    # Per-event risk probabilities (JSON: {pandemic: 0.3, war: 0.12, flood: 0.08, ...})
    event_probabilities = models.JSONField(default=dict, db_column='eventProbabilities')

    # Financial exposure (Monte Carlo outputs)
    expected_loss_usd = models.FloatField(default=0.0, db_column='expectedLossUsd')
    worst_case_loss_usd = models.FloatField(default=0.0, db_column='worstCaseLossUsd')
    p50_loss_usd = models.FloatField(default=0.0, db_column='p50LossUsd')
    p95_loss_usd = models.FloatField(default=0.0, db_column='p95LossUsd')
    p99_loss_usd = models.FloatField(default=0.0, db_column='p99LossUsd')

    # Bayesian network layer outputs
    bayesian_nodes = models.JSONField(default=dict, db_column='bayesianNodes')
    top_risk_drivers = models.JSONField(default=list, db_column='topRiskDrivers')
    causal_chain = models.JSONField(default=list, db_column='causalChain')

    # Clause strength audit
    clause_strength_score = models.FloatField(default=0.0, db_column='clauseStrengthScore')
    missing_protections = models.JSONField(default=list, db_column='missingProtections')
    covered_events = models.JSONField(default=list, db_column='coveredEvents')

    # LLM explanation
    explanation = models.TextField(blank=True, db_column='explanation')
    mitigation_suggestions = models.JSONField(default=list, db_column='mitigationSuggestions')

    # Metadata
    contract_value = models.FloatField(default=0.0, db_column='contractValue')
    jurisdiction = models.CharField(max_length=128, blank=True, db_column='jurisdiction')
    industry = models.CharField(max_length=128, blank=True, db_column='industry')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'fm_prediction'
        ordering = ['-created_at']

    def __str__(self):
        return f"FM Prediction [{self.contract_id}] score={self.fm_risk_score:.2f}"


# ---------------------------------------------------------------------------
# FM Clause Audit — tracks per-contract clause audit results
# ---------------------------------------------------------------------------
class FMClauseAudit(models.Model):
    """
    Stores the Force Majeure clause audit result for a contract.
    Tracks which events are covered, which are missing, and strength score.
    """
    STATUS_CHOICES = [
        ('strong', 'Strong Clause'),
        ('weak', 'Weak Clause'),
        ('missing', 'Missing Clause'),
    ]

    id = models.CharField(
        primary_key=True, max_length=36, default=generate_uuid, db_column='id'
    )
    contract_id = models.CharField(max_length=36, db_column='contractId', db_index=True)
    contract_title = models.CharField(max_length=512, blank=True, db_column='contractTitle')

    # Raw FM clause text extracted from contract
    raw_clause_text = models.TextField(blank=True, db_column='rawClauseText')

    # Audit results
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='missing', db_column='status')
    strength_score = models.FloatField(default=0.0, db_column='strengthScore')  # 0-1

    # Event coverage (14 categories)
    covered_events = models.JSONField(default=list, db_column='coveredEvents')
    missing_events = models.JSONField(default=list, db_column='missingEvents')
    weak_events = models.JSONField(default=list, db_column='weakEvents')

    # Auto-corrected clause
    original_clause = models.TextField(blank=True, db_column='originalClause')
    corrected_clause = models.TextField(blank=True, db_column='correctedClause')
    correction_applied = models.BooleanField(default=False, db_column='correctionApplied')

    # Risk reduction from auto-correction
    risk_reduction_before = models.FloatField(default=0.0, db_column='riskReductionBefore')
    risk_reduction_after = models.FloatField(default=0.0, db_column='riskReductionAfter')

    # Benchmarks against FIDIC / NEC / ICC
    benchmark_fidic_score = models.FloatField(null=True, blank=True, db_column='benchmarkFidicScore')
    benchmark_nec_score = models.FloatField(null=True, blank=True, db_column='benchmarkNecScore')
    benchmark_icc_score = models.FloatField(null=True, blank=True, db_column='benchmarkIccScore')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'fm_clause_audit'
        ordering = ['-created_at']

    def __str__(self):
        return f"FM Audit [{self.contract_id}] status={self.status} score={self.strength_score:.2f}"


# ---------------------------------------------------------------------------
# FM Scenario — war / geopolitical / natural disaster scenario simulation
# ---------------------------------------------------------------------------
class FMScenario(models.Model):
    """
    A force majeure scenario simulation (Monte Carlo run).
    Represents one what-if simulation (e.g., 'War in Middle East supply route').
    """
    SCENARIO_TYPE_CHOICES = [
        ('war', 'War / Military Conflict'),
        ('pandemic', 'Pandemic / Epidemic'),
        ('natural_disaster', 'Natural Disaster'),
        ('supply_chain', 'Supply Chain Disruption'),
        ('sanctions', 'Trade Sanctions / Embargo'),
        ('cyber', 'Cyber Warfare'),
        ('energy_crisis', 'Energy Crisis'),
        ('political_coup', 'Political Coup'),
        ('custom', 'Custom Scenario'),
    ]

    id = models.CharField(
        primary_key=True, max_length=36, default=generate_uuid, db_column='id'
    )
    contract_id = models.CharField(max_length=36, blank=True, db_column='contractId', db_index=True)
    prediction_id = models.CharField(max_length=36, blank=True, db_column='predictionId')

    name = models.CharField(max_length=256, db_column='name')
    scenario_type = models.CharField(max_length=32, choices=SCENARIO_TYPE_CHOICES, default='custom', db_column='scenarioType')
    description = models.TextField(blank=True, db_column='description')

    # Input parameters for the scenario
    input_params = models.JSONField(default=dict, db_column='inputParams')
    # e.g. {"war_probability": 0.3, "port_shutdown_probability": 0.6, "sanctions": true}

    # Monte Carlo outputs
    iterations = models.IntegerField(default=5000, db_column='iterations')
    expected_loss_usd = models.FloatField(default=0.0, db_column='expectedLossUsd')
    p50_loss_usd = models.FloatField(default=0.0, db_column='p50LossUsd')
    p95_loss_usd = models.FloatField(default=0.0, db_column='p95LossUsd')
    p99_loss_usd = models.FloatField(default=0.0, db_column='p99LossUsd')
    delay_days_expected = models.FloatField(default=0.0, db_column='delayDaysExpected')
    delay_days_worst = models.FloatField(default=0.0, db_column='delayDaysWorstCase')

    # Bayesian inference output under this scenario
    fm_invocation_prob = models.FloatField(default=0.0, db_column='fmInvocationProb')
    project_delay_prob = models.FloatField(default=0.0, db_column='projectDelayProb')
    contract_termination_prob = models.FloatField(default=0.0, db_column='contractTerminationProb')

    # Loss breakdown by category
    loss_breakdown = models.JSONField(default=dict, db_column='lossBreakdown')
    # e.g. {"delay_penalties": 120000, "idle_labour": 45000, "commodity_shock": 90000, ...}

    # AI explanation
    explanation = models.TextField(blank=True, db_column='explanation')
    recommended_mitigations = models.JSONField(default=list, db_column='recommendedMitigations')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'fm_scenario'
        ordering = ['-created_at']

    def __str__(self):
        return f"FM Scenario [{self.name}] type={self.scenario_type}"


# ---------------------------------------------------------------------------
# FM War Risk — stores war/geopolitical risk analysis per contract
# ---------------------------------------------------------------------------
class FMWarRisk(models.Model):
    """
    War & geopolitical risk analysis for a contract.
    Tracks supply chain routes, war event probabilities, and exposure.
    """
    id = models.CharField(
        primary_key=True, max_length=36, default=generate_uuid, db_column='id'
    )
    contract_id = models.CharField(max_length=36, db_column='contractId', db_index=True)
    contract_title = models.CharField(max_length=512, blank=True, db_column='contractTitle')

    # Overall war risk score (0-1)
    war_risk_score = models.FloatField(default=0.0, db_column='warRiskScore')

    # Per-event war risk probabilities
    event_risks = models.JSONField(default=dict, db_column='eventRisks')
    # e.g. {"military_invasion": 0.08, "trade_sanctions": 0.35, "port_shutdown": 0.22, ...}

    # Supply chain route exposure
    supply_chain_routes = models.JSONField(default=list, db_column='supplyChainRoutes')
    disrupted_routes = models.JSONField(default=list, db_column='disruptedRoutes')

    # Financial exposure from war events
    war_loss_expected_usd = models.FloatField(default=0.0, db_column='warLossExpectedUsd')
    war_loss_worst_usd = models.FloatField(default=0.0, db_column='warLossWorstUsd')

    # Top threat list
    top_threats = models.JSONField(default=list, db_column='topThreats')

    # Geopolitical context
    project_location = models.CharField(max_length=256, blank=True, db_column='projectLocation')
    supplier_locations = models.JSONField(default=list, db_column='supplierLocations')
    shipping_routes = models.JSONField(default=list, db_column='shippingRoutes')

    # Mitigation recommendations
    war_mitigation_clauses = models.JSONField(default=list, db_column='warMitigationClauses')

    # AI explanation
    explanation = models.TextField(blank=True, db_column='explanation')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'fm_war_risk'
        ordering = ['-created_at']

    def __str__(self):
        return f"FM War Risk [{self.contract_id}] score={self.war_risk_score:.2f}"


# ---------------------------------------------------------------------------
# FM Global Alert — real-time radar alert for a detected global event
# ---------------------------------------------------------------------------
class FMGlobalAlert(models.Model):
    """
    A real-time Force Majeure radar alert triggered by a detected global event.
    Maps detected geopolitical/natural/supply chain event to affected contracts.
    """
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    EVENT_TYPE_CHOICES = [
        ('war', 'War / Military Conflict'),
        ('sanctions', 'Trade Sanctions'),
        ('pandemic', 'Pandemic'),
        ('earthquake', 'Earthquake'),
        ('flood', 'Flood'),
        ('hurricane', 'Hurricane'),
        ('port_closure', 'Port Closure'),
        ('airspace_closure', 'Airspace Closure'),
        ('energy_shortage', 'Energy Shortage'),
        ('cyber_attack', 'Cyber Attack'),
        ('political_coup', 'Political Coup'),
        ('supply_disruption', 'Supply Chain Disruption'),
    ]

    id = models.CharField(
        primary_key=True, max_length=36, default=generate_uuid, db_column='id'
    )

    event_type = models.CharField(max_length=32, choices=EVENT_TYPE_CHOICES, db_column='eventType')
    event_title = models.CharField(max_length=512, db_column='eventTitle')
    event_description = models.TextField(blank=True, db_column='eventDescription')
    event_location = models.CharField(max_length=256, blank=True, db_column='eventLocation')
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default='medium', db_column='severity')

    # Affected contracts
    affected_contract_ids = models.JSONField(default=list, db_column='affectedContractIds')
    affected_contracts_count = models.IntegerField(default=0, db_column='affectedContractsCount')

    # Financial exposure estimate
    total_portfolio_exposure_usd = models.FloatField(default=0.0, db_column='totalPortfolioExposureUsd')

    # Suggested actions
    suggested_actions = models.JSONField(default=list, db_column='suggestedActions')
    clause_updates_required = models.IntegerField(default=0, db_column='clauseUpdatesRequired')

    # Status
    is_active = models.BooleanField(default=True, db_column='isActive')
    is_resolved = models.BooleanField(default=False, db_column='isResolved')

    detected_at = models.DateTimeField(auto_now_add=True, db_column='detectedAt')
    resolved_at = models.DateTimeField(null=True, blank=True, db_column='resolvedAt')

    class Meta:
        db_table = 'fm_global_alert'
        ordering = ['-detected_at']

    def __str__(self):
        return f"FM Alert [{self.event_type}] severity={self.severity}"
