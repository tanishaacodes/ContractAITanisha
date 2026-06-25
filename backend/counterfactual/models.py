from django.db import models
from core.models import User


class CounterfactualScenario(models.Model):
    """
    Stores counterfactual simulation scenarios and their outcomes.
    Tracks what-if analysis for contract clauses.
    """
    contract_id = models.CharField(max_length=64, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='counterfactual_scenarios')

    # Original and modified clauses
    original_clause = models.TextField(help_text="Original contract clause")
    modified_clause = models.TextField(help_text="Modified/counterfactual clause")

    # Simulation results
    simulated_outcome = models.JSONField(
        help_text="Predicted outcomes including business, legal, and operational impacts"
    )

    # Risk metrics
    confidence_score = models.FloatField(
        help_text="Confidence level of the simulation (0.0 to 1.0)"
    )
    risk_delta = models.FloatField(
        null=True,
        blank=True,
        help_text="Change in risk level compared to original (-1.0 to 1.0)"
    )

    # Outcome categories
    business_impact = models.JSONField(
        null=True,
        blank=True,
        help_text="Revenue, pricing, and financial impacts"
    )
    legal_impact = models.JSONField(
        null=True,
        blank=True,
        help_text="Litigation, compliance, and regulatory impacts"
    )
    operational_impact = models.JSONField(
        null=True,
        blank=True,
        help_text="Delays, resource allocation, and process impacts"
    )

    # Metadata
    scenario_type = models.CharField(
        max_length=64,
        default='clause_modification',
        help_text="Type of counterfactual scenario"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'counterfactual_scenarios'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contract_id', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"Scenario {self.id} for Contract {self.contract_id}"


class HistoricalOutcome(models.Model):
    """
    Stores historical contract outcomes for similarity matching.
    Used to ground counterfactual predictions in real-world data.
    """
    contract_id = models.CharField(max_length=64, unique=True, db_index=True)

    # Contract metadata
    contract_type = models.CharField(max_length=128)
    industry = models.CharField(max_length=128, null=True, blank=True)
    contract_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Actual outcomes
    dispute_occurred = models.BooleanField(default=False)
    dispute_details = models.TextField(null=True, blank=True)
    revenue_impact = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    litigation_occurred = models.BooleanField(default=False)
    renewal_success = models.BooleanField(null=True, blank=True)
    operational_delays_days = models.IntegerField(null=True, blank=True)

    # Key clauses (for similarity matching)
    key_clauses = models.JSONField(
        help_text="Structured representation of key contract clauses"
    )

    # Vector embedding for similarity search
    embedding_id = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Reference to vector embedding in Qdrant"
    )

    # Timestamps
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    outcome_recorded_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'historical_outcomes'
        ordering = ['-outcome_recorded_date']
        indexes = [
            models.Index(fields=['contract_type', 'industry']),
            models.Index(fields=['dispute_occurred', 'litigation_occurred']),
        ]

    def __str__(self):
        return f"Outcome for Contract {self.contract_id}"
