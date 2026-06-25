"""
Django models for Fivetran-synced external data sources.
These models represent raw data synced from DocuSign, Salesforce, and SAP.
"""
from django.db import models
from django.utils import timezone
import uuid


# ========================================
# DOCUSIGN MODELS (Raw Fivetran Data)
# ========================================

class DocuSignEnvelope(models.Model):
    """
    Represents a DocuSign envelope (contract document package).
    Synced from Fivetran's DocuSign connector.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    envelope_id = models.CharField(max_length=100, unique=True, db_index=True)
    email_subject = models.CharField(max_length=500, null=True, blank=True)
    status = models.CharField(max_length=50)  # completed, sent, delivered, etc.
    sent_date_time = models.DateTimeField(null=True, blank=True)
    completed_date_time = models.DateTimeField(null=True, blank=True)
    created_date_time = models.DateTimeField(null=True, blank=True)

    # Metadata
    sender_email = models.EmailField(null=True, blank=True)
    source_system = models.CharField(max_length=50, default='DOCUSIGN')
    last_synced_at = models.DateTimeField(auto_now=True)
    fivetran_synced = models.BooleanField(default=True)
    processed = models.BooleanField(default=False)  # Has ETL processed this?

    class Meta:
        db_table = 'fivetran_docusign_envelopes'
        indexes = [
            models.Index(fields=['envelope_id']),
            models.Index(fields=['status']),
            models.Index(fields=['processed']),
        ]

    def __str__(self):
        return f"DocuSign Envelope: {self.envelope_id}"


class DocuSignDocument(models.Model):
    """
    Represents individual documents within a DocuSign envelope.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    envelope = models.ForeignKey(DocuSignEnvelope, on_delete=models.CASCADE, related_name='documents')
    document_id = models.CharField(max_length=100)
    document_name = models.CharField(max_length=500)
    document_base64 = models.TextField(null=True, blank=True)  # Base64 encoded document

    last_synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fivetran_docusign_documents'
        unique_together = [['envelope', 'document_id']]

    def __str__(self):
        return f"Document: {self.document_name}"


class DocuSignRecipient(models.Model):
    """
    Represents signers/recipients of a DocuSign envelope.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    envelope = models.ForeignKey(DocuSignEnvelope, on_delete=models.CASCADE, related_name='recipients')
    recipient_id = models.CharField(max_length=100)
    role_name = models.CharField(max_length=200)  # Signer, Carbon Copy, etc.
    email = models.EmailField()
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=50)  # signed, sent, delivered

    last_synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fivetran_docusign_recipients'
        unique_together = [['envelope', 'recipient_id']]

    def __str__(self):
        return f"{self.name} ({self.role_name})"


# ========================================
# SALESFORCE MODELS (Raw Fivetran Data)
# ========================================

class SalesforceAccount(models.Model):
    """
    Represents a Salesforce account (company/counterparty).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    salesforce_id = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=500)
    account_type = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=200, null=True, blank=True)
    website = models.URLField(null=True, blank=True)

    billing_street = models.CharField(max_length=500, null=True, blank=True)
    billing_city = models.CharField(max_length=200, null=True, blank=True)
    billing_state = models.CharField(max_length=100, null=True, blank=True)
    billing_country = models.CharField(max_length=100, null=True, blank=True)

    last_synced_at = models.DateTimeField(auto_now=True)
    fivetran_synced = models.BooleanField(default=True)

    class Meta:
        db_table = 'fivetran_salesforce_accounts'
        indexes = [
            models.Index(fields=['salesforce_id']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name


class SalesforceContract(models.Model):
    """
    Represents a Salesforce contract record.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    salesforce_id = models.CharField(max_length=100, unique=True, db_index=True)
    contract_number = models.CharField(max_length=200)
    account = models.ForeignKey(SalesforceAccount, on_delete=models.SET_NULL, null=True, related_name='contracts')

    status = models.CharField(max_length=100)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    contract_term = models.IntegerField(null=True, blank=True)  # in months

    owner_name = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    source_system = models.CharField(max_length=50, default='SALESFORCE')
    last_synced_at = models.DateTimeField(auto_now=True)
    fivetran_synced = models.BooleanField(default=True)
    processed = models.BooleanField(default=False)

    class Meta:
        db_table = 'fivetran_salesforce_contracts'
        indexes = [
            models.Index(fields=['salesforce_id']),
            models.Index(fields=['contract_number']),
            models.Index(fields=['processed']),
        ]

    def __str__(self):
        return f"Salesforce Contract: {self.contract_number}"


class SalesforceOpportunity(models.Model):
    """
    Represents a Salesforce opportunity (potential deal).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    salesforce_id = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=500)
    account = models.ForeignKey(SalesforceAccount, on_delete=models.SET_NULL, null=True, related_name='opportunities')

    stage_name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    close_date = models.DateField(null=True, blank=True)
    probability = models.IntegerField(null=True, blank=True)

    last_synced_at = models.DateTimeField(auto_now=True)
    fivetran_synced = models.BooleanField(default=True)

    class Meta:
        db_table = 'fivetran_salesforce_opportunities'
        indexes = [
            models.Index(fields=['salesforce_id']),
        ]

    def __str__(self):
        return self.name


# ========================================
# SAP MODELS (Raw Fivetran Data)
# ========================================

class SapEKKO(models.Model):
    """
    SAP EKKO table - Purchasing Document Header.
    Represents contract/purchase order headers.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ebeln = models.CharField(max_length=20, unique=True, db_index=True)  # Purchase Document Number
    bukrs = models.CharField(max_length=10, null=True, blank=True)  # Company Code
    bsart = models.CharField(max_length=10, null=True, blank=True)  # Document Type
    bstyp = models.CharField(max_length=1, null=True, blank=True)  # Document Category

    lifnr = models.CharField(max_length=20, null=True, blank=True)  # Vendor Number
    bedat = models.DateField(null=True, blank=True)  # Purchasing Document Date
    kdatb = models.DateField(null=True, blank=True)  # Start of Validity Period
    kdate = models.DateField(null=True, blank=True)  # End of Validity Period

    waers = models.CharField(max_length=5, null=True, blank=True)  # Currency

    source_system = models.CharField(max_length=50, default='SAP')
    last_synced_at = models.DateTimeField(auto_now=True)
    fivetran_synced = models.BooleanField(default=True)
    processed = models.BooleanField(default=False)

    class Meta:
        db_table = 'fivetran_sap_ekko'
        indexes = [
            models.Index(fields=['ebeln']),
            models.Index(fields=['lifnr']),
            models.Index(fields=['processed']),
        ]

    def __str__(self):
        return f"SAP PO: {self.ebeln}"


class SapEKPO(models.Model):
    """
    SAP EKPO table - Purchasing Document Line Items.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ebeln = models.CharField(max_length=20, db_index=True)  # Purchase Document Number
    ebelp = models.CharField(max_length=10)  # Item Number

    matnr = models.CharField(max_length=40, null=True, blank=True)  # Material Number
    txz01 = models.CharField(max_length=500, null=True, blank=True)  # Short Text
    menge = models.DecimalField(max_digits=18, decimal_places=3, null=True, blank=True)  # Quantity
    meins = models.CharField(max_length=10, null=True, blank=True)  # Unit of Measure
    netpr = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)  # Net Price
    netwr = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)  # Net Value

    last_synced_at = models.DateTimeField(auto_now=True)
    fivetran_synced = models.BooleanField(default=True)

    class Meta:
        db_table = 'fivetran_sap_ekpo'
        unique_together = [['ebeln', 'ebelp']]
        indexes = [
            models.Index(fields=['ebeln']),
        ]

    def __str__(self):
        return f"SAP PO Line: {self.ebeln}-{self.ebelp}"


class SapLFA1(models.Model):
    """
    SAP LFA1 table - Vendor Master.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lifnr = models.CharField(max_length=20, unique=True, db_index=True)  # Vendor Number
    name1 = models.CharField(max_length=200, null=True, blank=True)  # Name
    land1 = models.CharField(max_length=10, null=True, blank=True)  # Country Key
    ort01 = models.CharField(max_length=200, null=True, blank=True)  # City

    last_synced_at = models.DateTimeField(auto_now=True)
    fivetran_synced = models.BooleanField(default=True)

    class Meta:
        db_table = 'fivetran_sap_lfa1'
        indexes = [
            models.Index(fields=['lifnr']),
        ]

    def __str__(self):
        return f"{self.name1} ({self.lifnr})"


class SapCDPOS(models.Model):
    """
    SAP CDPOS table - Change Document Items (Field-level changes).
    Used for tracking contract amendments and drift.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    objectid = models.CharField(max_length=100, db_index=True)  # Changed Object ID
    tabname = models.CharField(max_length=50)  # Table Name
    fname = models.CharField(max_length=50)  # Field Name
    chngind = models.CharField(max_length=1)  # Change Type (U=Update, I=Insert, D=Delete)

    value_old = models.TextField(null=True, blank=True)
    value_new = models.TextField(null=True, blank=True)

    changedby = models.CharField(max_length=50, null=True, blank=True)
    changedat = models.DateField(null=True, blank=True)

    last_synced_at = models.DateTimeField(auto_now=True)
    fivetran_synced = models.BooleanField(default=True)

    class Meta:
        db_table = 'fivetran_sap_cdpos'
        indexes = [
            models.Index(fields=['objectid']),
            models.Index(fields=['tabname']),
        ]

    def __str__(self):
        return f"Change: {self.objectid} - {self.fname}"


# ========================================
# UNIFIED CANONICAL MODEL
# ========================================

class UnifiedContract(models.Model):
    """
    Canonical contract model that unifies data from all sources.
    This is the single source of truth for contract data.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Source tracking
    external_id = models.CharField(max_length=200, unique=True, db_index=True)
    source_system = models.CharField(max_length=50, choices=[
        ('DOCUSIGN', 'DocuSign'),
        ('SALESFORCE', 'Salesforce'),
        ('SAP', 'SAP'),
        ('MANUAL', 'Manual Upload'),
    ])

    # Core contract details
    contract_name = models.CharField(max_length=500, null=True, blank=True)
    contract_number = models.CharField(max_length=200, null=True, blank=True)
    counterparty = models.CharField(max_length=500)
    contract_type = models.CharField(max_length=100, null=True, blank=True)

    # Financial
    contract_value = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, null=True, blank=True)

    # Dates
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    execution_date = models.DateField(null=True, blank=True)

    # Status
    lifecycle_status = models.CharField(max_length=100)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ETL tracking
    etl_processed_at = models.DateTimeField(null=True, blank=True)
    qdrant_synced = models.BooleanField(default=False)
    qdrant_synced_at = models.DateTimeField(null=True, blank=True)

    # Link to ContractAI's native contract model (if applicable)
    native_contract_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)

    class Meta:
        db_table = 'unified_contracts'
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['source_system']),
            models.Index(fields=['counterparty']),
            models.Index(fields=['qdrant_synced']),
        ]

    def __str__(self):
        return f"{self.contract_name or self.contract_number} ({self.source_system})"
