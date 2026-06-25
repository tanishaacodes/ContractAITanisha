"""
Serializers for Super Admin LLM Configuration Management

Author: ContractAI Platform
Version: 1.0.0
"""

from rest_framework import serializers
from core.super_admin_models import (
    LLMProvider,
    LLMConfiguration,
    SuperAdminAuditLog,
    LLMUsageMetrics
)


class LLMProviderSerializer(serializers.ModelSerializer):
    """
    Serializer for LLM Provider.

    Security:
    - API key is never returned in responses (write-only)
    - Only Super Admin can create/update
    """

    api_key = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text='API key for provider (encrypted at rest)'
    )

    # Computed field
    has_api_key = serializers.SerializerMethodField()

    class Meta:
        model = LLMProvider
        fields = [
            'id',
            'name',
            'display_name',
            'provider_type',
            'is_active',
            'is_available',
            'config_schema',
            'default_config',
            'requires_api_key',
            'api_key',  # write-only
            'has_api_key',  # read-only computed
            'priority',
            'created_at',
            'updated_at',
            'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'has_api_key']

    def get_has_api_key(self, obj):
        """Check if API key exists (without exposing it)"""
        return bool(obj.api_key_encrypted)

    def create(self, validated_data):
        """Handle API key encryption on create"""
        api_key = validated_data.pop('api_key', None)

        provider = LLMProvider.objects.create(**validated_data)

        if api_key:
            provider.set_api_key(api_key)
            provider.save()

        return provider

    def update(self, instance, validated_data):
        """Handle API key encryption on update"""
        api_key = validated_data.pop('api_key', None)

        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update API key if provided
        if api_key:
            instance.set_api_key(api_key)

        instance.save()
        return instance


class LLMProviderListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing providers.
    Used in dropdowns and list views.
    """

    has_api_key = serializers.SerializerMethodField()

    class Meta:
        model = LLMProvider
        fields = [
            'id',
            'name',
            'display_name',
            'provider_type',
            'is_active',
            'is_available',
            'has_api_key',
            'priority'
        ]

    def get_has_api_key(self, obj):
        return bool(obj.api_key_encrypted)


class LLMConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for LLM Configuration.

    Includes provider details for convenience.
    """

    provider_name = serializers.CharField(source='provider.display_name', read_only=True)
    provider_type = serializers.CharField(source='provider.provider_type', read_only=True)

    class Meta:
        model = LLMConfiguration
        fields = [
            'id',
            'provider',
            'provider_name',
            'provider_type',
            'model_name',
            'temperature',
            'max_tokens',
            'top_p',
            'frequency_penalty',
            'presence_penalty',
            'custom_parameters',
            'api_endpoint',
            'api_version',
            'requests_per_minute',
            'tokens_per_minute',
            'cost_per_1k_input_tokens',
            'cost_per_1k_output_tokens',
            'is_current',
            'version',
            'created_at',
            'updated_at',
            'created_by'
        ]
        read_only_fields = ['id', 'version', 'created_at', 'updated_at', 'created_by']

    def validate_temperature(self, value):
        """Validate temperature is in valid range"""
        if not (0 <= value <= 2):
            raise serializers.ValidationError("Temperature must be between 0 and 2")
        return value

    def validate_top_p(self, value):
        """Validate top_p is in valid range"""
        if not (0 <= value <= 1):
            raise serializers.ValidationError("Top-p must be between 0 and 1")
        return value

    def validate_frequency_penalty(self, value):
        """Validate frequency_penalty is in valid range"""
        if not (-2 <= value <= 2):
            raise serializers.ValidationError("Frequency penalty must be between -2 and 2")
        return value

    def validate_presence_penalty(self, value):
        """Validate presence_penalty is in valid range"""
        if not (-2 <= value <= 2):
            raise serializers.ValidationError("Presence penalty must be between -2 and 2")
        return value

    def create(self, validated_data):
        """Auto-increment version for same provider"""
        provider = validated_data['provider']

        # Get latest version for this provider
        latest = LLMConfiguration.objects.filter(provider=provider).order_by('-version').first()
        next_version = (latest.version + 1) if latest else 1

        validated_data['version'] = next_version
        return super().create(validated_data)


class SuperAdminAuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for Super Admin Audit Logs.

    Read-only: Audit logs cannot be modified or deleted.
    """

    user_email = serializers.EmailField(read_only=True)
    user_role = serializers.CharField(read_only=True)

    class Meta:
        model = SuperAdminAuditLog
        fields = [
            'id',
            'user',
            'user_email',
            'user_role',
            'action_type',
            'resource_type',
            'resource_id',
            'action_summary',
            'old_values',
            'new_values',
            'ip_address',
            'user_agent',
            'request_id',
            'timestamp'
        ]
        read_only_fields = '__all__'  # Everything is read-only


class LLMUsageMetricsSerializer(serializers.ModelSerializer):
    """
    Serializer for LLM Usage Metrics.

    Used for cost tracking and analytics.
    """

    provider_name = serializers.CharField(source='provider.display_name', read_only=True)
    configuration_version = serializers.IntegerField(source='configuration.version', read_only=True)

    class Meta:
        model = LLMUsageMetrics
        fields = [
            'id',
            'provider',
            'provider_name',
            'configuration',
            'configuration_version',
            'request_count',
            'total_input_tokens',
            'total_output_tokens',
            'total_cost',
            'avg_latency_ms',
            'error_count',
            'period_start',
            'period_end',
            'created_at'
        ]
        read_only_fields = '__all__'


# =========================
# REQUEST/RESPONSE SERIALIZERS
# =========================

class ActivateProviderSerializer(serializers.Serializer):
    """Request serializer for activating LLM provider"""
    provider_id = serializers.CharField(required=True)


class MakeConfigCurrentSerializer(serializers.Serializer):
    """Request serializer for making config current"""
    config_id = serializers.CharField(required=True)


class CurrentLLMConfigSerializer(serializers.Serializer):
    """
    Response serializer for current active LLM configuration.

    Used by application code to get runtime LLM settings.
    """

    provider = serializers.CharField(help_text='Provider type (openai, claude, etc.)')
    provider_display_name = serializers.CharField()
    model_name = serializers.CharField()
    temperature = serializers.DecimalField(max_digits=3, decimal_places=2)
    max_tokens = serializers.IntegerField()
    top_p = serializers.DecimalField(max_digits=3, decimal_places=2)
    frequency_penalty = serializers.DecimalField(max_digits=3, decimal_places=2)
    presence_penalty = serializers.DecimalField(max_digits=3, decimal_places=2)
    custom_parameters = serializers.JSONField()
    api_endpoint = serializers.CharField(allow_null=True)
    api_key = serializers.CharField(
        write_only=True,
        required=False,
        help_text='Decrypted API key (only for backend use)'
    )


class LLMConfigTestSerializer(serializers.Serializer):
    """
    Request serializer for testing LLM configuration.

    Allows Super Admin to test a config before activating.
    """

    config_id = serializers.CharField(required=True)
    test_prompt = serializers.CharField(
        required=False,
        default="Hello, this is a test. Please respond with 'Configuration test successful.'",
        max_length=500
    )
