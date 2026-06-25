"""
Enterprise Risk & Profitability Intelligence Models
CFO-Grade Analytics for Contract Risk Management
"""
from django.db import models
from core.models import Contract, generate_uuid


class Supplier(models.Model):
    """Supplier entity for supply chain risk analysis"""
    TIER_CHOICES = [
        ('TIER_1', 'Tier 1 - Direct'),
        ('TIER_2', 'Tier 2 - Indirect'),
        ('TIER_3', 'Tier 3 - Sub-supplier'),
    ]

    RISK_LEVEL_CHOICES = [
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
        ('CRITICAL', 'Critical Risk'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    name = models.CharField(max_length=255)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    country = models.CharField(max_length=100)
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, db_column='riskLevel')
    risk_score = models.FloatField(default=0.0, db_column='riskScore', help_text='Risk score 0.0 - 1.0')

    # Financial metrics
    exposure_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, db_column='exposureAmount')

    # Supply chain attributes
    is_single_source = models.BooleanField(default=False, db_column='isSingleSource')
    dependency_score = models.FloatField(default=0.0, db_column='dependencyScore')

    # Geopolitical
    has_sanctions = models.BooleanField(default=False, db_column='hasSanctions')
    political_stability_index = models.FloatField(default=0.5, db_column='politicalStabilityIndex')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'enterprise_suppliers'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.tier})"


class Commodity(models.Model):
    """Commodity price tracking for volatility analysis"""
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True, null=True)

    # Pricing
    current_price = models.DecimalField(max_digits=18, decimal_places=2, db_column='currentPrice')
    currency = models.CharField(max_length=10, default='USD')
    unit = models.CharField(max_length=50, help_text='e.g., per ton, per barrel')

    # Volatility parameters for GBM
    volatility = models.FloatField(default=0.3, help_text='Annual volatility (sigma)')
    drift = models.FloatField(default=0.05, help_text='Expected drift (mu)')

    # Contract exposure
    total_exposure = models.DecimalField(max_digits=18, decimal_places=2, default=0, db_column='totalExposure')

    last_updated = models.DateTimeField(auto_now=True, db_column='lastUpdated')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'enterprise_commodities'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (${self.current_price}/{self.unit})"


class ContractSupplier(models.Model):
    """Many-to-many relationship between contracts and suppliers"""
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='contract_suppliers', db_column='contractId')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='supplier_contracts', db_column='supplierId')

    # Relationship attributes
    exposure_amount = models.DecimalField(max_digits=18, decimal_places=2, db_column='exposureAmount')
    dependency_level = models.CharField(max_length=20, choices=[
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ], db_column='dependencyLevel')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'enterprise_contract_suppliers'
        unique_together = ['contract', 'supplier']

    def __str__(self):
        return f"{self.contract.original_filename} - {self.supplier.name}"


class ContractCommodity(models.Model):
    """Many-to-many relationship between contracts and commodities"""
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='contract_commodities', db_column='contractId')
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE, related_name='commodity_contracts', db_column='commodityId')

    # Relationship attributes
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2, db_column='unitPrice')
    total_value = models.DecimalField(max_digits=18, decimal_places=2, db_column='totalValue')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'enterprise_contract_commodities'
        unique_together = ['contract', 'commodity']

    def __str__(self):
        return f"{self.contract.original_filename} - {self.commodity.name}"


class GeoPoliticalRisk(models.Model):
    """Geopolitical risk factors by country/region"""
    RISK_SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    country = models.CharField(max_length=100, unique=True)
    region = models.CharField(max_length=100)

    # Geographic coordinates for mapping
    latitude = models.FloatField()
    longitude = models.FloatField()

    # Risk metrics
    political_stability_score = models.FloatField(db_column='politicalStabilityScore', help_text='0.0 - 1.0')
    risk_severity = models.CharField(max_length=20, choices=RISK_SEVERITY_CHOICES, db_column='riskSeverity')

    # Sanctions & regulations
    has_active_sanctions = models.BooleanField(default=False, db_column='hasActiveSanctions')
    sanction_details = models.TextField(blank=True, null=True, db_column='sanctionDetails')

    # Economic indicators
    gdp_growth_rate = models.FloatField(null=True, blank=True, db_column='gdpGrowthRate')
    inflation_rate = models.FloatField(null=True, blank=True, db_column='inflationRate')
    currency_stability = models.FloatField(null=True, blank=True, db_column='currencyStability')

    # Contract exposure in this country
    total_exposure = models.DecimalField(max_digits=18, decimal_places=2, default=0, db_column='totalExposure')

    last_updated = models.DateTimeField(auto_now=True, db_column='lastUpdated')
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'enterprise_geopolitical_risks'
        ordering = ['country']

    def __str__(self):
        return f"{self.country} - {self.risk_severity} risk"


class MonteCarloSimulation(models.Model):
    """Stored Monte Carlo VaR simulation results"""
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='monte_carlo_simulations', db_column='contractId')

    # Simulation parameters
    iterations = models.IntegerField(default=30000)
    confidence_level = models.FloatField(default=0.95, db_column='confidenceLevel')

    # Results
    mean_exposure = models.DecimalField(max_digits=18, decimal_places=2, db_column='meanExposure')
    median_exposure = models.DecimalField(max_digits=18, decimal_places=2, db_column='medianExposure')
    std_dev = models.DecimalField(max_digits=18, decimal_places=2, db_column='stdDev')

    # VaR metrics
    var_90 = models.DecimalField(max_digits=18, decimal_places=2, db_column='var90')
    var_95 = models.DecimalField(max_digits=18, decimal_places=2, db_column='var95')
    var_99 = models.DecimalField(max_digits=18, decimal_places=2, db_column='var99')

    # CVaR (Conditional VaR / Expected Shortfall)
    cvar_95 = models.DecimalField(max_digits=18, decimal_places=2, db_column='cvar95')
    cvar_99 = models.DecimalField(max_digits=18, decimal_places=2, db_column='cvar99')

    # Min/Max
    min_exposure = models.DecimalField(max_digits=18, decimal_places=2, db_column='minExposure')
    max_exposure = models.DecimalField(max_digits=18, decimal_places=2, db_column='maxExposure')

    # Distribution data (JSON array)
    distribution_data = models.JSONField(db_column='distributionData', help_text='Histogram distribution data')
    convergence_data = models.JSONField(db_column='convergenceData', help_text='Convergence path data')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'enterprise_monte_carlo_simulations'
        ordering = ['-created_at']

    def __str__(self):
        return f"MonteCarlo {self.contract.original_filename} ({self.iterations} iterations)"


class SupplierDependency(models.Model):
    """Parent-child relationships between suppliers for multi-tier supply chain"""
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    parent_supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='sub_suppliers',
        db_column='parentSupplierId',
        help_text='The primary supplier (Tier 1 or 2)'
    )
    child_supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='parent_suppliers',
        db_column='childSupplierId',
        help_text='The sub-supplier (Tier 2 or 3)'
    )

    # Dependency metrics
    dependency_type = models.CharField(
        max_length=50,
        choices=[
            ('RAW_MATERIAL', 'Raw Material'),
            ('COMPONENT', 'Component'),
            ('LOGISTICS', 'Logistics'),
            ('SERVICE', 'Service'),
        ],
        default='COMPONENT',
        db_column='dependencyType'
    )
    criticality = models.FloatField(
        default=0.5,
        help_text='How critical this dependency is (0.0 = low, 1.0 = critical)'
    )
    lead_time_days = models.IntegerField(
        default=30,
        db_column='leadTimeDays',
        help_text='Lead time in days'
    )

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'enterprise_supplier_dependencies'
        unique_together = ['parent_supplier', 'child_supplier']

    def __str__(self):
        return f"{self.parent_supplier.name} → {self.child_supplier.name}"


class InsurancePolicy(models.Model):
    """Insurance policies that offset contract liabilities"""
    POLICY_TYPE_CHOICES = [
        ('GENERAL_LIABILITY', 'General Liability'),
        ('PROFESSIONAL_INDEMNITY', 'Professional Indemnity'),
        ('PRODUCT_LIABILITY', 'Product Liability'),
        ('CYBER_LIABILITY', 'Cyber Liability'),
        ('POLITICAL_RISK', 'Political Risk'),
        ('TRADE_CREDIT', 'Trade Credit'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('PENDING', 'Pending'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)
    policy_number = models.CharField(max_length=100, unique=True, db_column='policyNumber')
    policy_type = models.CharField(max_length=50, choices=POLICY_TYPE_CHOICES, db_column='policyType')

    # Relationships
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='insurance_policies',
        db_column='contractId',
        null=True,
        blank=True,
        help_text='Contract covered by this policy (optional)'
    )

    # Coverage details
    insurer_name = models.CharField(max_length=255, db_column='insurerName')
    coverage_amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        db_column='coverageAmount',
        help_text='Maximum coverage amount'
    )
    deductible = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        help_text='Deductible amount'
    )
    premium_annual = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        db_column='premiumAnnual',
        help_text='Annual premium cost'
    )

    # Policy period
    effective_date = models.DateField(db_column='effectiveDate')
    expiry_date = models.DateField(db_column='expiryDate')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    # Risk coverage
    covers_unlimited_liability = models.BooleanField(
        default=False,
        db_column='coversUnlimitedLiability',
        help_text='Whether this policy covers unlimited liability clauses'
    )
    covers_geo_political_risk = models.BooleanField(
        default=False,
        db_column='coversGeoPoliticalRisk'
    )
    covers_supply_chain_disruption = models.BooleanField(
        default=False,
        db_column='coversSupplyChainDisruption'
    )

    # Claims history
    total_claims_filed = models.IntegerField(default=0, db_column='totalClaimsFiled')
    total_claims_paid = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        db_column='totalClaimsPaid'
    )

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'enterprise_insurance_policies'
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.policy_number} - {self.insurer_name}"

    @property
    def is_active(self):
        """Check if policy is currently active"""
        from datetime import date
        today = date.today()
        return (
            self.status == 'ACTIVE' and
            self.effective_date <= today <= self.expiry_date
        )

    @property
    def net_coverage(self):
        """Calculate net coverage after deductible"""
        return self.coverage_amount - self.deductible
