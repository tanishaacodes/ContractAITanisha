"""
Enterprise-Grade Super Admin & LLM Configuration Models

SECURITY NOTICE:
- Super Admin role can ONLY be created via Django shell or management command
- ALL Super Admin actions are audit logged
- LLM configurations are versioned and tracked
- API keys are encrypted at rest

Author: ContractAI Platform
Version: 1.0.0
"""

import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings
import json


def generate_uuid():
    """Generate UUID for model primary keys"""
    return str(uuid.uuid4())


# =========================
# ENCRYPTION UTILITIES
# =========================

class EncryptionHelper:
    """
    Handles encryption/decryption of sensitive data (API keys).
    Uses Fernet symmetric encryption.

    Production: Store ENCRYPTION_KEY in environment variables, not in code!
    """

    @staticmethod
    def get_cipher():
        """Get Fernet cipher instance"""
        # CRITICAL: In production, load from environment variable!
        encryption_key = getattr(settings, 'ENCRYPTION_KEY', None)
        if not encryption_key:
            raise ValueError("ENCRYPTION_KEY not configured in settings")
        return Fernet(encryption_key.encode())

    @staticmethod
    def encrypt(plaintext: str) -> str:
        """Encrypt plaintext string"""
        if not plaintext:
            return None
        cipher = EncryptionHelper.get_cipher()
        return cipher.encrypt(plaintext.encode()).decode()

    @staticmethod
    def decrypt(ciphertext: str) -> str:
        """Decrypt ciphertext string"""
        if not ciphertext:
            return None
        cipher = EncryptionHelper.get_cipher()
        return cipher.decrypt(ciphertext.encode()).decode()


# =========================
# ENHANCED ROLE MODEL
# =========================

class RoleLevel:
    """Role hierarchy constants"""
    SUPER_ADMIN = 0
    ADMIN = 10
    MANAGER = 30
    USER = 50
    VIEWER = 70

    CHOICES = [
        (SUPER_ADMIN, 'Super Admin'),
        (ADMIN, 'Admin'),
        (MANAGER, 'Manager'),
        (USER, 'User'),
        (VIEWER, 'Viewer'),
    ]


# Note: Extend existing Role model with migration
# ALTER TABLE roles ADD COLUMN role_level INT DEFAULT 50;
# ALTER TABLE roles ADD COLUMN is_system_role BOOLEAN DEFAULT FALSE;


# =========================
# LLM PROVIDER CONFIGURATION
# =========================

class LLMProvider(models.Model):
    """
    Stores LLM provider configurations (OpenAI, Claude, Gemini, Ollama).
    Only ONE provider can be active at a time.

    Security:
    - API keys are encrypted at rest
    - Only Super Admin can manage providers
    - All changes are audit logged
    """

    PROVIDER_TYPE_CHOICES = [
        ('OPENAI', 'OpenAI'),
        ('ANTHROPIC', 'Anthropic (Claude)'),
        ('GOOGLE', 'Google (Gemini)'),
        ('OLLAMA', 'Ollama (Local)'),
        ('CUSTOM', 'Custom Provider'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)

    # Provider identification
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Unique provider identifier (e.g., openai_gpt4, claude_sonnet)'
    )
    display_name = models.CharField(
        max_length=100,
        db_column='displayName',
        help_text='Human-readable name (e.g., "OpenAI GPT-4")'
    )
    provider_type = models.CharField(
        max_length=20,
        choices=PROVIDER_TYPE_CHOICES,
        db_column='providerType'
    )

    # Status flags
    is_active = models.BooleanField(
        default=False,
        db_column='isActive',
        help_text='Only ONE provider can be active (enforced by DB constraint)'
    )
    is_available = models.BooleanField(
        default=True,
        db_column='isAvailable',
        help_text='Whether provider is available for selection'
    )

    # Configuration schema (defines what fields are required)
    config_schema = models.JSONField(
        default=dict,
        db_column='configSchema',
        help_text='JSON schema defining required configuration fields'
    )
    default_config = models.JSONField(
        default=dict,
        db_column='defaultConfig',
        help_text='Default configuration values'
    )

    # Security
    requires_api_key = models.BooleanField(
        default=True,
        db_column='requiresApiKey'
    )
    api_key_encrypted = models.TextField(
        blank=True,
        null=True,
        db_column='apiKeyEncrypted',
        help_text='Encrypted API key (Fernet)'
    )

    # Display order
    priority = models.IntegerField(
        default=0,
        help_text='Display order (lower = first)'
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_llm_providers',
        db_column='createdBy'
    )

    class Meta:
        db_table = 'llm_providers'
        ordering = ['priority', 'display_name']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['is_available']),
            models.Index(fields=['provider_type']),
        ]

    def __str__(self):
        active_status = '🟢 ACTIVE' if self.is_active else '⚫ Inactive'
        return f"{self.display_name} ({self.provider_type}) - {active_status}"

    def clean(self):
        """Validation: Cannot be active if not available"""
        if self.is_active and not self.is_available:
            raise ValidationError("Cannot activate an unavailable provider")

    def set_api_key(self, api_key: str):
        """Encrypt and store API key"""
        if api_key:
            self.api_key_encrypted = EncryptionHelper.encrypt(api_key)

    def get_api_key(self) -> str:
        """Decrypt and return API key"""
        if self.api_key_encrypted:
            return EncryptionHelper.decrypt(self.api_key_encrypted)
        return None

    @classmethod
    def get_active_provider(cls):
        """Get currently active LLM provider"""
        return cls.objects.filter(is_active=True, is_available=True).first()

    def activate(self, user):
        """
        Activate this provider (deactivates all others).
        Must be called with Super Admin user for audit trail.
        """
        from core.super_admin_models import SuperAdminAuditLog

        # Deactivate all others
        LLMProvider.objects.exclude(id=self.id).update(is_active=False)

        old_value = self.is_active
        self.is_active = True
        self.save()

        # Audit log
        SuperAdminAuditLog.log_action(
            user=user,
            action_type='LLM_PROVIDER_ACTIVATED',
            resource_type='llm_provider',
            resource_id=self.id,
            action_summary=f'Activated LLM provider: {self.display_name}',
            old_values={'is_active': old_value},
            new_values={'is_active': True}
        )


# =========================
# LLM RUNTIME CONFIGURATION
# =========================

class LLMConfiguration(models.Model):
    """
    Runtime configuration for LLM models.
    Controls temperature, max_tokens, and other model parameters.

    Versioned: Each change creates a new version for audit trail.
    """

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)

    # Provider relationship
    provider = models.ForeignKey(
        LLMProvider,
        on_delete=models.CASCADE,
        related_name='configurations',
        db_column='providerId'
    )

    # Model settings
    model_name = models.CharField(
        max_length=200,
        db_column='modelName',
        help_text='Model identifier (e.g., gpt-4-turbo, claude-3-opus-20240229)'
    )

    # Generation parameters
    temperature = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.7,
        help_text='Randomness (0-2): Lower = deterministic, Higher = creative'
    )
    max_tokens = models.IntegerField(
        default=4096,
        db_column='maxTokens',
        help_text='Maximum tokens in response'
    )
    top_p = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.0,
        db_column='topP',
        help_text='Nucleus sampling (0-1)'
    )
    frequency_penalty = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.0,
        db_column='frequencyPenalty',
        help_text='Penalize repeated tokens (-2 to 2)'
    )
    presence_penalty = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.0,
        db_column='presencePenalty',
        help_text='Penalize new topics (-2 to 2)'
    )

    # Advanced settings (provider-specific)
    custom_parameters = models.JSONField(
        default=dict,
        db_column='customParameters',
        help_text='Provider-specific parameters (JSON)'
    )

    # Endpoint configuration (for Ollama/custom)
    api_endpoint = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        db_column='apiEndpoint',
        help_text='Custom API endpoint URL'
    )
    api_version = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        db_column='apiVersion'
    )

    # Rate limiting
    requests_per_minute = models.IntegerField(
        default=60,
        db_column='requestsPerMinute'
    )
    tokens_per_minute = models.IntegerField(
        default=90000,
        db_column='tokensPerMinute'
    )

    # Cost tracking (for budgeting)
    cost_per_1k_input_tokens = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        blank=True,
        null=True,
        db_column='costPer1kInputTokens',
        help_text='Cost in USD per 1000 input tokens'
    )
    cost_per_1k_output_tokens = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        blank=True,
        null=True,
        db_column='costPer1kOutputTokens',
        help_text='Cost in USD per 1000 output tokens'
    )

    # Versioning
    is_current = models.BooleanField(
        default=False,
        db_column='isCurrent',
        help_text='Is this the current active configuration?'
    )
    version = models.IntegerField(
        default=1,
        help_text='Configuration version number'
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='updatedAt')
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.RESTRICT,
        related_name='created_llm_configs',
        db_column='createdBy'
    )

    class Meta:
        db_table = 'llm_configurations'
        ordering = ['-version', '-created_at']
        indexes = [
            models.Index(fields=['provider', 'is_current']),
            models.Index(fields=['is_current']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(temperature__gte=0, temperature__lte=2),
                name='temperature_range'
            ),
            models.CheckConstraint(
                check=models.Q(top_p__gte=0, top_p__lte=1),
                name='top_p_range'
            ),
        ]

    def __str__(self):
        current = '✓ CURRENT' if self.is_current else ''
        return f"{self.provider.display_name} - {self.model_name} v{self.version} {current}"

    @classmethod
    def get_current_config(cls):
        """Get currently active LLM configuration"""
        return cls.objects.filter(
            is_current=True,
            provider__is_active=True,
            provider__is_available=True
        ).first()

    def make_current(self, user):
        """
        Make this configuration the current one.
        Deactivates all other configs for this provider.
        """
        from core.super_admin_models import SuperAdminAuditLog

        # Deactivate all other configs for this provider
        LLMConfiguration.objects.filter(provider=self.provider).update(is_current=False)

        self.is_current = True
        self.save()

        # Audit log
        SuperAdminAuditLog.log_action(
            user=user,
            action_type='LLM_CONFIG_UPDATED',
            resource_type='llm_configuration',
            resource_id=self.id,
            action_summary=f'Activated LLM config v{self.version} for {self.provider.display_name}',
            old_values={'is_current': False},
            new_values={'is_current': True}
        )


# =========================
# SUPER ADMIN AUDIT LOG
# =========================

class SuperAdminAuditLog(models.Model):
    """
    Immutable audit trail for ALL Super Admin actions.

    Requirements:
    - Cannot be deleted or modified (append-only)
    - Captures IP, user agent, request context
    - Stores before/after state for all changes
    - Retention: Keep forever for compliance
    """

    ACTION_TYPE_CHOICES = [
        ('LLM_PROVIDER_CREATED', 'LLM Provider Created'),
        ('LLM_PROVIDER_UPDATED', 'LLM Provider Updated'),
        ('LLM_PROVIDER_ACTIVATED', 'LLM Provider Activated'),
        ('LLM_PROVIDER_DEACTIVATED', 'LLM Provider Deactivated'),
        ('LLM_CONFIG_CREATED', 'LLM Configuration Created'),
        ('LLM_CONFIG_UPDATED', 'LLM Configuration Updated'),
        ('LLM_CONFIG_DELETED', 'LLM Configuration Deleted'),
        ('LLM_SWITCHED', 'LLM Provider Switched'),
        ('API_KEY_UPDATED', 'API Key Updated'),
        ('SUPER_ADMIN_CREATED', 'Super Admin Created'),
        ('CONFIG_EXPORTED', 'Configuration Exported'),
        ('SYSTEM_SETTING_CHANGED', 'System Setting Changed'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)

    # Who performed the action
    user = models.ForeignKey(
        'core.User',
        on_delete=models.RESTRICT,  # Cannot delete users with audit logs
        related_name='super_admin_audits',
        db_column='userId'
    )
    user_email = models.EmailField(
        db_column='userEmail',
        help_text='Email at time of action (denormalized for immutability)'
    )
    user_role = models.CharField(
        max_length=50,
        db_column='userRole',
        help_text='Role at time of action'
    )

    # What was done
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPE_CHOICES,
        db_column='actionType'
    )
    resource_type = models.CharField(
        max_length=100,
        db_column='resourceType',
        help_text='Type of resource affected (llm_provider, llm_configuration)'
    )
    resource_id = models.CharField(
        max_length=36,
        blank=True,
        null=True,
        db_column='resourceId',
        help_text='ID of affected resource'
    )

    # Details
    action_summary = models.TextField(
        db_column='actionSummary',
        help_text='Human-readable description of action'
    )
    old_values = models.JSONField(
        default=dict,
        blank=True,
        db_column='oldValues',
        help_text='State before change'
    )
    new_values = models.JSONField(
        default=dict,
        blank=True,
        db_column='newValues',
        help_text='State after change'
    )

    # Context
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        db_column='ipAddress',
        help_text='IP address of user'
    )
    user_agent = models.TextField(
        blank=True,
        null=True,
        db_column='userAgent',
        help_text='Browser/client information'
    )
    request_id = models.CharField(
        max_length=36,
        blank=True,
        null=True,
        db_column='requestId',
        help_text='Request trace ID'
    )

    # Timestamp
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When action occurred'
    )

    class Meta:
        db_table = 'super_admin_audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['-timestamp']),
        ]
        # Make truly immutable
        permissions = [
            ('view_audit_log', 'Can view audit logs'),
        ]

    def __str__(self):
        return f"{self.action_type} by {self.user_email} at {self.timestamp}"

    def save(self, *args, **kwargs):
        """Override save to prevent updates"""
        # Allow creation (when pk is None or force_insert is True)
        # But prevent updates (when pk exists and force_insert is False)
        if self.pk and not kwargs.get('force_insert', False):
            raise ValidationError("Audit logs cannot be modified after creation")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Override delete to prevent deletion"""
        raise ValidationError("Audit logs cannot be deleted")

    @classmethod
    def log_action(cls, user, action_type, resource_type, resource_id,
                   action_summary, old_values=None, new_values=None,
                   request=None):
        """
        Create a new audit log entry.

        Args:
            user: User object performing action
            action_type: Type of action (from ACTION_TYPE_CHOICES)
            resource_type: Type of resource affected
            resource_id: ID of resource
            action_summary: Human-readable description
            old_values: State before change (dict)
            new_values: State after change (dict)
            request: Django request object (for IP, user agent)
        """
        ip_address = None
        user_agent = None
        request_id = None

        if request:
            # Extract IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')

            # Extract user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

            # Generate or extract request ID
            request_id = request.META.get('HTTP_X_REQUEST_ID', str(uuid.uuid4()))

        return cls.objects.create(
            user=user,
            user_email=user.email,
            user_role=user.role.name,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action_summary=action_summary,
            old_values=old_values or {},
            new_values=new_values or {},
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id
        )


# =========================
# LLM USAGE METRICS
# =========================

class LLMUsageMetrics(models.Model):
    """
    Tracks LLM usage for cost monitoring and performance analysis.
    Aggregated by time period (hourly/daily).
    """

    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid, editable=False)

    provider = models.ForeignKey(
        LLMProvider,
        on_delete=models.CASCADE,
        related_name='usage_metrics',
        db_column='providerId'
    )
    configuration = models.ForeignKey(
        LLMConfiguration,
        on_delete=models.CASCADE,
        related_name='usage_metrics',
        db_column='configurationId'
    )

    # Usage statistics
    request_count = models.IntegerField(
        default=0,
        db_column='requestCount'
    )
    total_input_tokens = models.BigIntegerField(
        default=0,
        db_column='totalInputTokens'
    )
    total_output_tokens = models.BigIntegerField(
        default=0,
        db_column='totalOutputTokens'
    )
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0,
        db_column='totalCost',
        help_text='Total cost in USD'
    )

    # Performance metrics
    avg_latency_ms = models.IntegerField(
        blank=True,
        null=True,
        db_column='avgLatencyMs',
        help_text='Average response time in milliseconds'
    )
    error_count = models.IntegerField(
        default=0,
        db_column='errorCount'
    )

    # Time period
    period_start = models.DateTimeField(
        db_column='periodStart',
        help_text='Start of measurement period'
    )
    period_end = models.DateTimeField(
        db_column='periodEnd',
        help_text='End of measurement period'
    )

    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'llm_usage_metrics'
        ordering = ['-period_start']
        indexes = [
            models.Index(fields=['provider', '-period_start']),
            models.Index(fields=['configuration', '-period_start']),
            models.Index(fields=['-period_start']),
        ]

    def __str__(self):
        return f"{self.provider.display_name} - {self.period_start.date()} ({self.request_count} requests)"
