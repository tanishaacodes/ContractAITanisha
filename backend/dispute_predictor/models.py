"""
Dispute Predictor Models
========================
Database models for storing dispute predictions, Bayesian risk assessments,
scenario simulations, and historical dispute outcomes.

DB conventions:
- PKs: CharField uuid (generate_uuid pattern)
- db_column camelCase
- No FK constraints to legacy tables (CharField IDs)
"""
import uuid
from django.db import models


def generate_uuid():
    return str(uuid.uuid4())


class DisputePrediction(models.Model):
    """
    Stores AI-generated dispute prediction for a contract.
    Combines Bayesian network + GNN + Qwen explanation.
    """
    id = models.CharField(
        primary_key=True, max_length=36, default=generate_uuid,
        db_column='id'
    )
    # Use CharField – no FK constraint to avoid MySQL 3780 collation issues
    contract_id = models.CharField(max_length=36, db_column='contractId', db_index=True)
    contract_title = models.CharField(max_length=512, blank=True, db_column='contractTitle')
    contract_text = models.TextField(blank=True, db_column='contractText')

    # Core probabilities (0–1)
    dispute_probability = models.FloatField(default=0.0, db_column='disputeProbability')
    arbitration_probability = models.FloatField(default=0.0, db_column='arbitrationProbability')
    litigation_probability = models.FloatField(default=0.0, db_column='litigationProbability')
    settlement_probability = models.FloatField(default=0.0, db_column='settlementProbability')

    # Financial exposure
    predicted_cost_usd = models.FloatField(default=0.0, db_column='predictedCostUsd')
    legal_cost_exposure_usd = models.FloatField(default=0.0, db_column='legalCostExposureUsd')

    # Risk scores (0–1)
    contract_risk_score = models.FloatField(default=0.0, db_column='contractRiskScore')
    financial_stress_score = models.FloatField(default=0.0, db_column='financialStressScore')
    operational_risk_score = models.FloatField(default=0.0, db_column='operationalRiskScore')
    geopolitical_risk_score = models.FloatField(default=0.0, db_column='geopoliticalRiskScore')

    # Bayesian network outputs
    bayesian_risk_nodes = models.JSONField(default=dict, db_column='bayesianRiskNodes')
    risk_propagation_path = models.JSONField(default=list, db_column='riskPropagationPath')
    top_risk_drivers = models.JSONField(default=list, db_column='topRiskDrivers')

    # GNN outputs
    gnn_dispute_score = models.FloatField(null=True, blank=True, db_column='gnnDisputeScore')
    gnn_confidence = models.FloatField(null=True, blank=True, db_column='gnnConfidence')

    # LLM explanation
    explanation = models.TextField(blank=True, db_column='explanation')
    mitigation_recommendations = models.JSONField(default=list, db_column='mitigationRecommendations')

    # Input risk signals used
    input_signals = models.JSONField(default=dict, db_column='inputSignals')

    # Metadata
    prediction_model_version = models.CharField(max_length=50, default='v1.0', db_column='predictionModelVersion')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'dispute_predictions'
        ordering = ['-created_at']

    def __str__(self):
        return f"DisputePrediction[{self.contract_id}] prob={self.dispute_probability:.2f}"


class DisputeScenario(models.Model):
    """
    Stores scenario simulation results (what-if analysis on risk drivers).
    """
    id = models.CharField(
        primary_key=True, max_length=36, default=generate_uuid,
        db_column='id'
    )
    prediction_id = models.CharField(max_length=36, db_column='predictionId', db_index=True)
    contract_id = models.CharField(max_length=36, db_column='contractId', db_index=True)

    scenario_name = models.CharField(max_length=255, db_column='scenarioName')
    scenario_description = models.TextField(blank=True, db_column='scenarioDescription')

    # Risk overrides applied in this scenario
    risk_overrides = models.JSONField(default=dict, db_column='riskOverrides')

    # Results
    dispute_probability = models.FloatField(default=0.0, db_column='disputeProbability')
    arbitration_probability = models.FloatField(default=0.0, db_column='arbitrationProbability')
    predicted_cost_usd = models.FloatField(default=0.0, db_column='predictedCostUsd')
    contract_risk_score = models.FloatField(default=0.0, db_column='contractRiskScore')

    # Delta vs base prediction
    dispute_probability_delta = models.FloatField(default=0.0, db_column='disputeProbabilityDelta')
    cost_delta = models.FloatField(default=0.0, db_column='costDelta')

    risk_nodes_snapshot = models.JSONField(default=dict, db_column='riskNodesSnapshot')
    propagation_path = models.JSONField(default=list, db_column='propagationPath')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'dispute_scenarios'
        ordering = ['-created_at']

    def __str__(self):
        return f"Scenario[{self.scenario_name}] prob={self.dispute_probability:.2f}"


class DisputeRiskNode(models.Model):
    """
    Stores the 60-node Bayesian risk graph structure for visualisation.
    Seeded once; updated via management command or API.
    """
    id = models.CharField(
        primary_key=True, max_length=36, default=generate_uuid,
        db_column='id'
    )
    node_id = models.CharField(max_length=100, unique=True, db_column='nodeId')
    label = models.CharField(max_length=255, db_column='label')
    cluster = models.CharField(max_length=100, db_column='cluster')  # geo/macro/supply/financial/operational/contract/legal
    layer = models.IntegerField(default=1, db_column='layer')  # 1–8
    base_probability = models.FloatField(default=0.1, db_column='baseProbability')
    description = models.TextField(blank=True, db_column='description')

    class Meta:
        db_table = 'dispute_risk_nodes'

    def __str__(self):
        return f"RiskNode[{self.node_id}]"


class DisputeRiskEdge(models.Model):
    """
    Directed edges in the Bayesian risk graph.
    """
    id = models.CharField(
        primary_key=True, max_length=36, default=generate_uuid,
        db_column='id'
    )
    source_node_id = models.CharField(max_length=100, db_column='sourceNodeId')
    target_node_id = models.CharField(max_length=100, db_column='targetNodeId')
    conditional_probability = models.FloatField(default=0.5, db_column='conditionalProbability')
    relation_type = models.CharField(max_length=100, blank=True, db_column='relationType')

    class Meta:
        db_table = 'dispute_risk_edges'
        unique_together = [('source_node_id', 'target_node_id')]

    def __str__(self):
        return f"Edge[{self.source_node_id} → {self.target_node_id}]"
