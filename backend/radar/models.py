from django.db import models


class ContractExposure(models.Model):
    """Stores computed exposure for a contract against a market signal."""

    contract_id = models.CharField(max_length=36, db_index=True)
    exposure_type = models.CharField(max_length=50)
    signal_name = models.CharField(max_length=255)
    sensitivity_factor = models.FloatField(default=0.0)
    estimated_impact = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_protected = models.BooleanField(default=False)
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-computed_at']
        indexes = [models.Index(fields=['contract_id', 'exposure_type'])]

    def __str__(self):
        return f"{self.contract_id} | {self.exposure_type} | ₹{self.estimated_impact}"


class StrategicAlert(models.Model):
    """Stores generated strategic alerts for contracts."""

    ALERT_TYPES = [
        ('strategic_opportunity', 'Strategic Opportunity'),
        ('cost_risk', 'Cost Risk'),
        ('renegotiation_opportunity', 'Renegotiation Opportunity'),
        ('hedging_required', 'Hedging Required'),
    ]

    contract_id = models.CharField(max_length=36, db_index=True)
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    exposure_type = models.CharField(max_length=50, blank=True)
    message = models.TextField()
    estimated_value = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_actioned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['contract_id', 'alert_type'])]

    def __str__(self):
        return f"[{self.alert_type}] {self.contract_id} — ₹{self.estimated_value}"
