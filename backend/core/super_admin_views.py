"""
Super Admin API Views for LLM Configuration Management

Security:
- All endpoints require Super Admin permission
- All changes are audit logged
- API keys are never exposed in responses

Author: ContractAI Platform
Version: 1.0.0
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from core.super_admin_models import (
    LLMProvider,
    LLMConfiguration,
    SuperAdminAuditLog,
    LLMUsageMetrics
)
from core.super_admin_serializers import (
    LLMProviderSerializer,
    LLMProviderListSerializer,
    LLMConfigurationSerializer,
    SuperAdminAuditLogSerializer,
    LLMUsageMetricsSerializer,
    ActivateProviderSerializer,
    MakeConfigCurrentSerializer,
    CurrentLLMConfigSerializer,
    LLMConfigTestSerializer
)
from core.super_admin_permissions import (
    IsSuperAdmin,
    IsSuperAdminOrReadOnly,
    IsAdminOrAbove,
    CanViewAuditLogs
)


# =========================
# LLM PROVIDER MANAGEMENT
# =========================

class LLMProviderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing LLM Providers.

    Permissions:
    - LIST/RETRIEVE: Admin or Super Admin
    - CREATE/UPDATE/DELETE: Super Admin only

    Endpoints:
    - GET /api/super-admin/llm-providers/  (List all providers)
    - GET /api/super-admin/llm-providers/{id}/  (Get provider details)
    - POST /api/super-admin/llm-providers/  (Create provider)
    - PUT/PATCH /api/super-admin/llm-providers/{id}/  (Update provider)
    - DELETE /api/super-admin/llm-providers/{id}/  (Delete provider)
    - POST /api/super-admin/llm-providers/{id}/activate/  (Activate provider)
    - POST /api/super-admin/llm-providers/{id}/deactivate/  (Deactivate provider)
    - GET /api/super-admin/llm-providers/active/  (Get active provider)
    """

    queryset = LLMProvider.objects.all()
    serializer_class = LLMProviderSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrReadOnly]

    def get_serializer_class(self):
        """Use lightweight serializer for list view"""
        if self.action == 'list':
            return LLMProviderListSerializer
        return LLMProviderSerializer

    def perform_create(self, serializer):
        """Create provider with audit logging"""
        provider = serializer.save(created_by=self.request.user)

        # Audit log
        SuperAdminAuditLog.log_action(
            user=self.request.user,
            action_type='LLM_PROVIDER_CREATED',
            resource_type='llm_provider',
            resource_id=provider.id,
            action_summary=f'Created LLM provider: {provider.display_name}',
            new_values={
                'name': provider.name,
                'display_name': provider.display_name,
                'provider_type': provider.provider_type,
                'is_active': provider.is_active,
                'is_available': provider.is_available
            },
            request=self.request
        )

    def perform_update(self, serializer):
        """Update provider with audit logging"""
        old_instance = self.get_object()
        old_values = {
            'name': old_instance.name,
            'display_name': old_instance.display_name,
            'provider_type': old_instance.provider_type,
            'is_active': old_instance.is_active,
            'is_available': old_instance.is_available
        }

        provider = serializer.save()

        new_values = {
            'name': provider.name,
            'display_name': provider.display_name,
            'provider_type': provider.provider_type,
            'is_active': provider.is_active,
            'is_available': provider.is_available
        }

        # Audit log
        SuperAdminAuditLog.log_action(
            user=self.request.user,
            action_type='LLM_PROVIDER_UPDATED',
            resource_type='llm_provider',
            resource_id=provider.id,
            action_summary=f'Updated LLM provider: {provider.display_name}',
            old_values=old_values,
            new_values=new_values,
            request=self.request
        )

    def perform_destroy(self, instance):
        """Delete provider with audit logging"""
        # Audit log before deletion
        SuperAdminAuditLog.log_action(
            user=self.request.user,
            action_type='LLM_PROVIDER_DELETED',
            resource_type='llm_provider',
            resource_id=instance.id,
            action_summary=f'Deleted LLM provider: {instance.display_name}',
            old_values={
                'name': instance.name,
                'display_name': instance.display_name,
                'provider_type': instance.provider_type
            },
            request=self.request
        )

        instance.delete()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminOrAbove])
    def active(self, request):
        """
        Get currently active provider.

        GET /api/super-admin/llm-providers/active/
        """
        active_provider = LLMProvider.get_active_provider()

        if not active_provider:
            return Response(
                {'message': 'No active LLM provider configured'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(active_provider)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdmin])
    def activate(self, request, pk=None):
        """
        Activate this provider (deactivates all others).

        POST /api/super-admin/llm-providers/{id}/activate/
        """
        provider = self.get_object()

        if not provider.is_available:
            return Response(
                {'message': 'Cannot activate an unavailable provider'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            provider.activate(request.user)

        serializer = self.get_serializer(provider)
        return Response({
            'message': f'Provider "{provider.display_name}" activated successfully',
            'provider': serializer.data
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdmin])
    def deactivate(self, request, pk=None):
        """
        Deactivate this provider.

        POST /api/super-admin/llm-providers/{id}/deactivate/
        """
        provider = self.get_object()

        if not provider.is_active:
            return Response(
                {'message': 'Provider is already inactive'},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_value = provider.is_active
        provider.is_active = False
        provider.save()

        # Audit log
        SuperAdminAuditLog.log_action(
            user=request.user,
            action_type='LLM_PROVIDER_DEACTIVATED',
            resource_type='llm_provider',
            resource_id=provider.id,
            action_summary=f'Deactivated LLM provider: {provider.display_name}',
            old_values={'is_active': old_value},
            new_values={'is_active': False},
            request=request
        )

        serializer = self.get_serializer(provider)
        return Response({
            'message': f'Provider "{provider.display_name}" deactivated successfully',
            'provider': serializer.data
        })


# =========================
# LLM CONFIGURATION MANAGEMENT
# =========================

class LLMConfigurationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing LLM Configurations.

    Permissions:
    - LIST/RETRIEVE: Admin or Super Admin
    - CREATE/UPDATE/DELETE: Super Admin only

    Endpoints:
    - GET /api/super-admin/llm-configs/  (List all configs)
    - GET /api/super-admin/llm-configs/{id}/  (Get config details)
    - POST /api/super-admin/llm-configs/  (Create config)
    - PUT/PATCH /api/super-admin/llm-configs/{id}/  (Update config)
    - DELETE /api/super-admin/llm-configs/{id}/  (Delete config)
    - POST /api/super-admin/llm-configs/{id}/make_current/  (Set as current)
    - GET /api/super-admin/llm-configs/current/  (Get current config)
    - POST /api/super-admin/llm-configs/{id}/test/  (Test config)
    """

    queryset = LLMConfiguration.objects.select_related('provider', 'created_by').all()
    serializer_class = LLMConfigurationSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrReadOnly]

    def get_queryset(self):
        """Filter by provider if specified"""
        queryset = super().get_queryset()
        provider_id = self.request.query_params.get('provider')

        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)

        return queryset

    def perform_create(self, serializer):
        """Create config with audit logging"""
        config = serializer.save(created_by=self.request.user)

        # Audit log
        SuperAdminAuditLog.log_action(
            user=self.request.user,
            action_type='LLM_CONFIG_CREATED',
            resource_type='llm_configuration',
            resource_id=config.id,
            action_summary=f'Created LLM config v{config.version} for {config.provider.display_name}',
            new_values={
                'provider': config.provider.display_name,
                'model_name': config.model_name,
                'temperature': str(config.temperature),
                'max_tokens': config.max_tokens,
                'version': config.version
            },
            request=self.request
        )

    def perform_update(self, serializer):
        """Update config with audit logging"""
        old_instance = self.get_object()
        old_values = {
            'model_name': old_instance.model_name,
            'temperature': str(old_instance.temperature),
            'max_tokens': old_instance.max_tokens,
            'is_current': old_instance.is_current
        }

        config = serializer.save()

        new_values = {
            'model_name': config.model_name,
            'temperature': str(config.temperature),
            'max_tokens': config.max_tokens,
            'is_current': config.is_current
        }

        # Audit log
        SuperAdminAuditLog.log_action(
            user=self.request.user,
            action_type='LLM_CONFIG_UPDATED',
            resource_type='llm_configuration',
            resource_id=config.id,
            action_summary=f'Updated LLM config v{config.version} for {config.provider.display_name}',
            old_values=old_values,
            new_values=new_values,
            request=self.request
        )

    def perform_destroy(self, instance):
        """Delete config with audit logging"""
        # Prevent deletion of current config
        if instance.is_current:
            raise ValidationError("Cannot delete the current active configuration")

        # Audit log before deletion
        SuperAdminAuditLog.log_action(
            user=self.request.user,
            action_type='LLM_CONFIG_DELETED',
            resource_type='llm_configuration',
            resource_id=instance.id,
            action_summary=f'Deleted LLM config v{instance.version} for {instance.provider.display_name}',
            old_values={
                'provider': instance.provider.display_name,
                'model_name': instance.model_name,
                'version': instance.version
            },
            request=self.request
        )

        instance.delete()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminOrAbove])
    def current(self, request):
        """
        Get currently active LLM configuration.

        GET /api/super-admin/llm-configs/current/

        This endpoint is used by application code to get runtime LLM settings.
        """
        config = LLMConfiguration.get_current_config()

        if not config:
            return Response(
                {'message': 'No active LLM configuration found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Return configuration with decrypted API key (for backend use)
        api_key = config.provider.get_api_key() if config.provider.requires_api_key else None

        response_data = {
            'provider': config.provider.name,
            'provider_display_name': config.provider.display_name,
            'provider_type': config.provider.provider_type,
            'model_name': config.model_name,
            'temperature': config.temperature,
            'max_tokens': config.max_tokens,
            'top_p': config.top_p,
            'frequency_penalty': config.frequency_penalty,
            'presence_penalty': config.presence_penalty,
            'custom_parameters': config.custom_parameters,
            'api_endpoint': config.api_endpoint,
            'api_key': api_key,  # Only returned for backend-to-backend calls
            'version': config.version
        }

        return Response(response_data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdmin])
    def make_current(self, request, pk=None):
        """
        Make this configuration the current active one.

        POST /api/super-admin/llm-configs/{id}/make_current/
        """
        config = self.get_object()

        # Ensure provider is active
        if not config.provider.is_active:
            return Response(
                {'message': 'Provider must be active to set configuration'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            config.make_current(request.user)

        serializer = self.get_serializer(config)
        return Response({
            'message': f'Configuration v{config.version} is now active',
            'configuration': serializer.data
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdmin])
    def test(self, request, pk=None):
        """
        Test LLM configuration with a simple prompt.

        POST /api/super-admin/llm-configs/{id}/test/
        Body: { "test_prompt": "Hello world" }

        Returns:
        - Success: LLM response
        - Failure: Error details
        """
        config = self.get_object()
        test_prompt = request.data.get(
            'test_prompt',
            "Hello, this is a test. Please respond with 'Configuration test successful.'"
        )

        try:
            # Import LLM client dynamically based on provider
            from core.llm_client import test_llm_config

            result = test_llm_config(config, test_prompt)

            # Audit log
            SuperAdminAuditLog.log_action(
                user=request.user,
                action_type='LLM_CONFIG_TESTED',
                resource_type='llm_configuration',
                resource_id=config.id,
                action_summary=f'Tested LLM config v{config.version} - Success',
                new_values={'test_result': 'success'},
                request=request
            )

            return Response({
                'message': 'Configuration test successful',
                'test_prompt': test_prompt,
                'response': result['response'],
                'latency_ms': result.get('latency_ms'),
                'tokens_used': result.get('tokens_used')
            })

        except Exception as e:
            # Audit log failure
            SuperAdminAuditLog.log_action(
                user=request.user,
                action_type='LLM_CONFIG_TESTED',
                resource_type='llm_configuration',
                resource_id=config.id,
                action_summary=f'Tested LLM config v{config.version} - Failed',
                new_values={'test_result': 'failure', 'error': str(e)},
                request=request
            )

            return Response(
                {
                    'message': 'Configuration test failed',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =========================
# AUDIT LOG VIEW
# =========================

class SuperAdminAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing Super Admin audit logs.

    Permissions:
    - Admin or Super Admin can view

    Endpoints:
    - GET /api/super-admin/audit-logs/  (List audit logs)
    - GET /api/super-admin/audit-logs/{id}/  (Get audit log details)

    Query params:
    - user: Filter by user ID
    - action_type: Filter by action type
    - resource_type: Filter by resource type
    - start_date: Filter by date range (ISO 8601)
    - end_date: Filter by date range (ISO 8601)
    """

    queryset = SuperAdminAuditLog.objects.select_related('user').all()
    serializer_class = SuperAdminAuditLogSerializer
    permission_classes = [IsAuthenticated, CanViewAuditLogs]

    def get_queryset(self):
        """Filter audit logs by query params"""
        queryset = super().get_queryset()

        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filter by action type
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)

        # Filter by resource type
        resource_type = self.request.query_params.get('resource_type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)

        return queryset


# =========================
# LLM USAGE METRICS VIEW
# =========================

class LLMUsageMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing LLM usage metrics.

    Permissions:
    - Super Admin only

    Endpoints:
    - GET /api/super-admin/llm-metrics/  (List usage metrics)
    - GET /api/super-admin/llm-metrics/summary/  (Get usage summary)
    """

    queryset = LLMUsageMetrics.objects.select_related('provider', 'configuration').all()
    serializer_class = LLMUsageMetricsSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get_queryset(self):
        """Filter metrics by query params"""
        queryset = super().get_queryset()

        # Filter by provider
        provider_id = self.request.query_params.get('provider')
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(period_start__gte=start_date)
        if end_date:
            queryset = queryset.filter(period_end__lte=end_date)

        return queryset

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get aggregated usage summary.

        GET /api/super-admin/llm-metrics/summary/

        Query params:
        - days: Number of days to look back (default: 30)
        """
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)

        metrics = LLMUsageMetrics.objects.filter(
            period_start__gte=start_date
        ).select_related('provider')

        # Aggregate by provider
        summary = {}
        for metric in metrics:
            provider_name = metric.provider.display_name
            if provider_name not in summary:
                summary[provider_name] = {
                    'total_requests': 0,
                    'total_input_tokens': 0,
                    'total_output_tokens': 0,
                    'total_cost': 0,
                    'total_errors': 0
                }

            summary[provider_name]['total_requests'] += metric.request_count
            summary[provider_name]['total_input_tokens'] += metric.total_input_tokens
            summary[provider_name]['total_output_tokens'] += metric.total_output_tokens
            summary[provider_name]['total_cost'] += float(metric.total_cost)
            summary[provider_name]['total_errors'] += metric.error_count

        return Response({
            'period_days': days,
            'start_date': start_date.isoformat(),
            'end_date': timezone.now().isoformat(),
            'summary_by_provider': summary
        })
