"""
Risk Models for Cross-Contract Risk & Exposure Analysis
Links to existing Contract and Clause models, adds Neo4j integration
"""
from django.db import models
from core.models import Contract, Clause


class Party(models.Model):
    """
    Represents vendors or customers in the risk network.
    Stored in both MySQL (for queries) and Neo4j (for relationships).
    """
    PARTY_TYPE_CHOICES = [
        ('VENDOR', 'Vendor'),
        ('CUSTOMER', 'Customer'),
        ('PARTNER', 'Partner'),
    ]

    name = models.CharField(max_length=255, unique=True, help_text='Party name (vendor/customer)')
    party_type = models.CharField(max_length=20, choices=PARTY_TYPE_CHOICES, db_column='partyType')
    country = models.CharField(max_length=100, blank=True, null=True, help_text='Country of operation')

    # Neo4j sync
    neo4j_node_id = models.CharField(max_length=100, blank=True, null=True, db_column='neo4jNodeId',
                                      help_text='Node ID in Neo4j graph')
    last_synced_at = models.DateTimeField(blank=True, null=True, db_column='lastSyncedAt')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'parties'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['party_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.party_type})"


class PartyPartition(models.Model):
    """
    Partition nodes to avoid vendor supernodes in Neo4j.
    Groups contracts by vendor + time period (e.g., VendorABC_2025).
    """
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='partitions', db_column='partyId')
    partition_key = models.CharField(max_length=100, unique=True, db_column='partitionKey',
                                     help_text='Partition identifier (e.g., VendorABC_2025)')
    year = models.IntegerField(help_text='Year of partition')
    region = models.CharField(max_length=100, blank=True, null=True, help_text='Region filter (APAC, EMEA, US)')

    # Neo4j sync
    neo4j_node_id = models.CharField(max_length=100, blank=True, null=True, db_column='neo4jNodeId')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'party_partitions'
        ordering = ['-year', 'party']
        indexes = [
            models.Index(fields=['party', 'year']),
            models.Index(fields=['partition_key']),
        ]

    def __str__(self):
        return f"{self.partition_key}"


class RiskNode(models.Model):
    """
    Explicit risk modeling for Neo4j graph.
    Represents identified risks that can be linked to clauses/contracts.
    """
    RISK_TYPE_CHOICES = [
        ('LEGAL', 'Legal Risk'),
        ('FINANCIAL', 'Financial Risk'),
        ('REGULATORY', 'Regulatory Risk'),
        ('OPERATIONAL', 'Operational Risk'),
    ]

    risk_type = models.CharField(max_length=20, choices=RISK_TYPE_CHOICES, db_column='riskType')
    description = models.TextField(help_text='Risk description')
    severity = models.FloatField(default=0.0, help_text='Risk severity score (0-1)')

    # Neo4j sync
    neo4j_node_id = models.CharField(max_length=100, blank=True, null=True, db_column='neo4jNodeId')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'risk_nodes'
        ordering = ['-severity', 'risk_type']
        indexes = [
            models.Index(fields=['risk_type']),
            models.Index(fields=['-severity']),
        ]

    def __str__(self):
        return f"{self.risk_type} - {self.description[:50]}"


class ContractRisk(models.Model):
    """
    Links contracts to their computed risk scores.
    Used for Neo4j relationship properties and aggregations.
    """
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='contract_risks', db_column='contractId')
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='contract_risks',
                              null=True, blank=True, db_column='partyId')

    # Risk metrics
    overall_risk_score = models.FloatField(default=0.0, db_column='overallRiskScore',
                                           help_text='Computed overall risk (0-1)')
    region = models.CharField(max_length=100, blank=True, null=True, help_text='Contract region')
    business_unit = models.CharField(max_length=100, blank=True, null=True, db_column='businessUnit',
                                     help_text='Business unit owning contract')

    # Neo4j sync
    neo4j_relationship_id = models.CharField(max_length=100, blank=True, null=True, db_column='neo4jRelationshipId')
    last_synced_at = models.DateTimeField(blank=True, null=True, db_column='lastSyncedAt')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'contract_risks'
        ordering = ['-overall_risk_score']
        indexes = [
            models.Index(fields=['contract']),
            models.Index(fields=['party']),
            models.Index(fields=['region']),
            models.Index(fields=['-overall_risk_score']),
        ]

    def __str__(self):
        return f"Risk for {self.contract.original_filename}: {self.overall_risk_score:.2f}"


class ClauseRisk(models.Model):
    """
    Stores risk scores for individual clauses.
    Links clauses to risk nodes and tracks embeddings in Qdrant.
    """
    clause = models.OneToOneField(Clause, on_delete=models.CASCADE, related_name='clause_risk', db_column='clauseId')
    risk_node = models.ForeignKey(RiskNode, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='clause_risks', db_column='riskNodeId')

    # LLM-computed risk from Qwen 7B
    local_risk_score = models.FloatField(default=0.0, db_column='localRiskScore',
                                         help_text='Clause-specific risk score (0-1)')
    was_negotiated = models.BooleanField(default=False, db_column='wasNegotiated',
                                         help_text='Whether clause was negotiated')

    # Qdrant vector embedding
    qdrant_point_id = models.CharField(max_length=100, blank=True, null=True, db_column='qdrantPointId',
                                       help_text='Point ID in Qdrant vector DB')
    embedding_synced_at = models.DateTimeField(blank=True, null=True, db_column='embeddingSyncedAt')

    # Neo4j sync
    neo4j_relationship_id = models.CharField(max_length=100, blank=True, null=True, db_column='neo4jRelationshipId')
    last_synced_at = models.DateTimeField(blank=True, null=True, db_column='lastSyncedAt')

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'clause_risks'
        ordering = ['-local_risk_score']
        indexes = [
            models.Index(fields=['clause']),
            models.Index(fields=['risk_node']),
            models.Index(fields=['-local_risk_score']),
        ]

    def __str__(self):
        return f"Clause Risk: {self.clause.clause_name} - {self.local_risk_score:.2f}"


class CrossContractCorrelation(models.Model):
    """
    Tracks AI-detected correlations between contracts.
    Used for risk propagation analysis in Neo4j.
    """
    contract_a = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='correlations_as_a', db_column='contractAId')
    contract_b = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='correlations_as_b', db_column='contractBId')

    correlation_strength = models.FloatField(db_column='correlationStrength',
                                             help_text='Strength of correlation (0-1)')
    correlation_reason = models.TextField(db_column='correlationReason',
                                          help_text='Why these contracts are correlated')

    # Factors for correlation
    same_vendor = models.BooleanField(default=False, db_column='sameVendor')
    same_jurisdiction = models.BooleanField(default=False, db_column='sameJurisdiction')
    similar_clauses = models.BooleanField(default=False, db_column='similarClauses')

    # Neo4j sync
    neo4j_relationship_id = models.CharField(max_length=100, blank=True, null=True, db_column='neo4jRelationshipId')

    detected_at = models.DateTimeField(auto_now_add=True, db_column='detectedAt')

    class Meta:
        db_table = 'cross_contract_correlations'
        unique_together = ['contract_a', 'contract_b']
        ordering = ['-correlation_strength']
        indexes = [
            models.Index(fields=['contract_a', '-correlation_strength']),
            models.Index(fields=['contract_b', '-correlation_strength']),
        ]

    def __str__(self):
        return f"Correlation: {self.contract_a.id[:8]} <-> {self.contract_b.id[:8]} ({self.correlation_strength:.2f})"


class VendorExposure(models.Model):
    """
    Aggregated vendor exposure metrics.
    Pre-computed for dashboard performance.
    """
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='exposures', db_column='partyId')

    total_exposure = models.FloatField(default=0.0, db_column='totalExposure',
                                       help_text='Total risk exposure from all contracts')
    contract_count = models.IntegerField(default=0, db_column='contractCount',
                                         help_text='Number of contracts with this vendor')
    average_risk = models.FloatField(default=0.0, db_column='averageRisk',
                                     help_text='Average risk score across contracts')

    # Regional breakdown
    exposure_by_region = models.JSONField(default=dict, db_column='exposureByRegion',
                                          help_text='{"APAC": 0.82, "EMEA": 0.46, ...}')

    computed_at = models.DateTimeField(auto_now=True, db_column='computedAt',
                                       help_text='When exposure was last calculated')

    class Meta:
        db_table = 'vendor_exposures'
        ordering = ['-total_exposure']
        indexes = [
            models.Index(fields=['party']),
            models.Index(fields=['-total_exposure']),
        ]

    def __str__(self):
        return f"Exposure for {self.party.name}: {self.total_exposure:.2f}"
