"""
Extended Models for MCTS, Multi-Agent, and Legal Precedents
============================================================
"""
import uuid
from django.db import models


def generate_uuid():
    return str(uuid.uuid4())


class NegotiationState(models.Model):
    """
    Stores individual states in the MCTS negotiation tree.
    Each state represents a contract configuration during negotiation.
    """
    id = models.CharField(
        primary_key=True, max_length=36, default=generate_uuid,
        db_column='id'
    )
    contract_id = models.CharField(max_length=36, db_column='contractId', db_index=True)
    parent_state_id = models.CharField(
        max_length=36, null=True, blank=True, db_column='parentStateId', db_index=True
    )
    level = models.IntegerField(default=0, db_column='level')

    # Contract parameters at this state
    state_data = models.JSONField(
        db_column='stateData',
        help_text='Contract parameters: price, delivery_days, liability_cap, payment_terms, etc.'
    )

    # MCTS metrics
    score = models.FloatField(default=0.0, db_column='score')
    dispute_probability = models.FloatField(default=0.0, db_column='disputeProbability')
    commercial_value = models.FloatField(default=0.0, db_column='commercialValue')
    visits = models.IntegerField(default=0, db_column='visits')
    is_optimal = models.BooleanField(default=False, db_column='isOptimal')

    # Action that led to this state
    action_taken = models.CharField(
        max_length=255, null=True, blank=True, db_column='actionTaken'
    )

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'negotiation_states'
        indexes = [
            models.Index(fields=['contract_id', 'level']),
            models.Index(fields=['parent_state_id']),
        ]

    def __str__(self):
        return f"State[{self.id[:8]}] Level {self.level} Score {self.score}"


class AgentDecision(models.Model):
    """
    Tracks decisions made by each autonomous agent in multi-agent negotiation.
    """
    AGENT_CHOICES = [
        ('buyer', 'Buyer Agent'),
        ('supplier', 'Supplier Agent'),
        ('regulator', 'Regulator Agent'),
        ('risk', 'Risk Agent'),
        ('finance', 'Finance Agent'),
    ]

    id = models.CharField(
        primary_key=True, max_length=36, default=generate_uuid,
        db_column='id'
    )
    simulation_id = models.CharField(max_length=36, db_column='simulationId', db_index=True)
    agent_type = models.CharField(
        max_length=50, choices=AGENT_CHOICES, db_column='agentType'
    )
    action = models.CharField(max_length=255, db_column='action')
    clause_affected = models.CharField(max_length=100, db_column='clauseAffected')

    # Before/after values
    value_change = models.JSONField(
        db_column='valueChange',
        help_text='{"before": value, "after": value}'
    )

    rationale = models.TextField(null=True, blank=True, db_column='rationale')
    approved = models.BooleanField(default=True, db_column='approved')

    # Impact metrics
    impact = models.JSONField(
        null=True, blank=True, db_column='impact',
        help_text='{"dispute_change": float, "cost_change": float}'
    )

    timestamp = models.DateTimeField(auto_now_add=True, db_column='timestamp')

    class Meta:
        db_table = 'agent_decisions'
        indexes = [
            models.Index(fields=['simulation_id', 'agent_type']),
        ]

    def __str__(self):
        return f"{self.agent_type}: {self.action}"


class ContractEvent(models.Model):
    """
    Lifecycle events for Contract Digital Twin simulation.
    """
    EVENT_CHOICES = [
        ('signed', 'Contract Signed'),
        ('supplier_delay', 'Supplier Delay'),
        ('cost_escalation', 'Cost Escalation'),
        ('scope_change', 'Scope Change'),
        ('renegotiation', 'Renegotiation'),
        ('dispute_triggered', 'Dispute Triggered'),
        ('arbitration', 'Arbitration Initiated'),
        ('settlement', 'Settlement Reached'),
    ]

    id = models.CharField(
        primary_key=True, max_length=36, default=generate_uuid,
        db_column='id'
    )
    contract_id = models.CharField(max_length=36, db_column='contractId', db_index=True)
    event_type = models.CharField(
        max_length=100, choices=EVENT_CHOICES, db_column='eventType'
    )
    event_time = models.DateTimeField(db_column='eventTime')

    impact_data = models.JSONField(
        null=True, blank=True, db_column='impactData',
        help_text='Event-specific impact metrics'
    )
    risk_change = models.FloatField(default=0.0, db_column='riskChange')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'contract_events'
        ordering = ['event_time']
        indexes = [
            models.Index(fields=['contract_id', 'event_time']),
        ]

    def __str__(self):
        return f"{self.event_type} @ {self.event_time}"


class LegalPrecedent(models.Model):
    """
    Historical arbitration/litigation cases for precedent-based prediction.
    """
    OUTCOME_CHOICES = [
        ('claimant_win', 'Claimant Win'),
        ('respondent_win', 'Respondent Win'),
        ('partial_award', 'Partial Award'),
        ('settlement', 'Settlement'),
        ('dismissed', 'Dismissed'),
    ]

    id = models.CharField(
        primary_key=True, max_length=36, default=generate_uuid,
        db_column='id'
    )
    case_id = models.CharField(max_length=100, unique=True, db_column='caseId')
    case_name = models.CharField(max_length=255, db_column='caseName')

    # Jurisdiction & venue
    jurisdiction = models.CharField(max_length=100, db_column='jurisdiction')
    arbitration_seat = models.CharField(
        max_length=100, null=True, blank=True, db_column='arbitrationSeat'
    )
    tribunal_composition = models.CharField(
        max_length=255, null=True, blank=True, db_column='tribunalComposition'
    )

    # Case details
    dispute_type = models.CharField(max_length=100, db_column='disputeType')
    contract_type = models.CharField(max_length=100, db_column='contractType')
    contract_value = models.FloatField(null=True, blank=True, db_column='contractValue')
    claim_amount = models.FloatField(null=True, blank=True, db_column='claimAmount')
    award_amount = models.FloatField(null=True, blank=True, db_column='awardAmount')

    # Outcome
    outcome = models.CharField(max_length=50, choices=OUTCOME_CHOICES, db_column='outcome')
    decision_date = models.DateField(db_column='decisionDate')
    duration_days = models.IntegerField(null=True, blank=True, db_column='durationDays')
    legal_costs = models.FloatField(null=True, blank=True, db_column='legalCosts')

    # Key issues & embeddings
    key_issues = models.JSONField(null=True, blank=True, db_column='keyIssues')
    clause_embeddings = models.JSONField(
        null=True, blank=True, db_column='clauseEmbeddings',
        help_text='768-dim LegalBERT embeddings for similarity matching'
    )

    summary = models.TextField(null=True, blank=True, db_column='summary')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'legal_precedents'
        indexes = [
            models.Index(fields=['jurisdiction', 'dispute_type']),
            models.Index(fields=['contract_type', 'outcome']),
        ]

    def __str__(self):
        return f"{self.case_id}: {self.case_name}"


class RLTrainingLog(models.Model):
    """
    Logs RL training episodes for contract risk optimization.
    """
    id = models.CharField(
        primary_key=True, max_length=36, default=generate_uuid,
        db_column='id'
    )
    episode = models.IntegerField(db_column='episode', db_index=True)
    state = models.JSONField(db_column='state')
    action = models.JSONField(db_column='action')
    reward = models.FloatField(db_column='reward')
    next_state = models.JSONField(db_column='nextState')
    done = models.BooleanField(default=False, db_column='done')

    # Training metrics
    loss = models.FloatField(null=True, blank=True, db_column='loss')
    epsilon = models.FloatField(null=True, blank=True, db_column='epsilon')

    timestamp = models.DateTimeField(auto_now_add=True, db_column='timestamp')

    class Meta:
        db_table = 'rl_training_logs'
        indexes = [
            models.Index(fields=['episode']),
        ]

    def __str__(self):
        return f"Episode {self.episode}: Reward {self.reward}"
