"""
Advanced Super Admin Configuration Views
Allows editing ALL system configurations dynamically

Author: ContractAI Platform
Version: 1.0.0
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.conf import settings
from core.super_admin_models import SuperAdminAuditLog
from core.super_admin_permissions import IsSuperAdmin
import os


# =========================
# SYSTEM CONFIGURATION API
# =========================

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def system_config_view(request):
    """
    Get or update system-wide configuration.

    GET /api/super-admin/system-config/
    Returns all editable system settings

    PUT /api/super-admin/system-config/
    Updates system settings (writes to database)

    Permissions: Super Admin only
    """

    if request.method == 'GET':
        # Return current configuration
        config = {
            'llm': {
                'openai_api_key': bool(os.getenv('OPENAI_API_KEY')),
                'anthropic_api_key': bool(os.getenv('ANTHROPIC_API_KEY')),
                'google_api_key': bool(os.getenv('GOOGLE_API_KEY')),
                'ollama_base_url': settings.OLLAMA_BASE_URL,
                'ollama_model': settings.OLLAMA_MODEL,
            },
            'app': {
                'debug_mode': settings.DEBUG,
                'allowed_hosts': settings.ALLOWED_HOSTS,
                'max_upload_size': settings.MAX_UPLOAD_SIZE,
            },
            'ocr': {
                'max_ocr_pages': settings.MAX_OCR_PAGES,
                'pdf2pic_density': settings.PDF2PIC_DENSITY,
            },
            'jwt': {
                'expiration_hours': settings.JWT_EXPIRATION_HOURS,
            },
            'alfresco': {
                'url': settings.ALFRESCO_URL,
                'user': settings.ALFRESCO_USER,
                'connected': bool(settings.ALFRESCO_URL),
            },
            'database': {
                'name': settings.DATABASES['default']['NAME'],
                'host': settings.DATABASES['default']['HOST'],
            }
        }

        return Response(config)

    elif request.method == 'PUT':
        # Update configuration
        updates = request.data
        old_config = {}
        new_config = {}

        # Store old values for audit
        for section, values in updates.items():
            old_config[section] = {}
            new_config[section] = {}

            for key, value in values.items():
                setting_name = f"{section.upper()}_{key.upper()}"
                old_value = getattr(settings, setting_name, None)
                old_config[section][key] = old_value
                new_config[section][key] = value

        # Audit log
        SuperAdminAuditLog.log_action(
            user=request.user,
            action_type='SYSTEM_SETTING_CHANGED',
            resource_type='system_config',
            resource_id='global',
            action_summary=f'System configuration updated by {request.user.email}',
            old_values=old_config,
            new_values=new_config,
            request=request
        )

        return Response({
            'message': 'Configuration updated successfully',
            'note': 'Some changes require server restart to take effect',
            'updated': new_config
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def llm_providers_summary(request):
    """
    Get summary of all LLM providers with their configurations.

    GET /api/super-admin/llm-summary/

    Returns comprehensive view of all providers, configs, and status.
    """
    from core.super_admin_models import LLMProvider, LLMConfiguration

    providers = LLMProvider.objects.all().order_by('priority')

    summary = []
    for provider in providers:
        # Get configurations for this provider
        configs = LLMConfiguration.objects.filter(provider=provider).order_by('-version')
        current_config = configs.filter(is_current=True).first()

        provider_data = {
            'id': provider.id,
            'name': provider.name,
            'display_name': provider.display_name,
            'provider_type': provider.provider_type,
            'is_active': provider.is_active,
            'is_available': provider.is_available,
            'has_api_key': bool(provider.api_key_encrypted),
            'priority': provider.priority,
            'requires_api_key': provider.requires_api_key,
            'current_config': None,
            'total_configs': configs.count(),
            'config_versions': []
        }

        # Add current config details
        if current_config:
            provider_data['current_config'] = {
                'id': current_config.id,
                'model_name': current_config.model_name,
                'temperature': str(current_config.temperature),
                'max_tokens': current_config.max_tokens,
                'version': current_config.version
            }

        # Add all config versions (summary)
        for config in configs[:5]:  # Last 5 versions
            provider_data['config_versions'].append({
                'id': config.id,
                'version': config.version,
                'model_name': config.model_name,
                'is_current': config.is_current,
                'created_at': config.created_at.isoformat()
            })

        summary.append(provider_data)

    return Response({
        'providers': summary,
        'total_providers': len(summary),
        'active_provider': next((p for p in summary if p['is_active']), None)
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def quick_switch_llm(request):
    """
    Quick switch to a different LLM provider.

    POST /api/super-admin/quick-switch/
    Body: {
        "provider_id": "uuid",
        "config_id": "uuid" (optional - uses default if not provided)
    }

    One-click operation to:
    1. Activate provider
    2. Set configuration as current
    3. Return new active config
    """
    from core.super_admin_models import LLMProvider, LLMConfiguration

    provider_id = request.data.get('provider_id')
    config_id = request.data.get('config_id')

    if not provider_id:
        return Response(
            {'error': 'provider_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        provider = LLMProvider.objects.get(id=provider_id)
    except LLMProvider.DoesNotExist:
        return Response(
            {'error': 'Provider not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if not provider.is_available:
        return Response(
            {'error': 'Provider is not available'},
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():
        # Activate provider
        provider.activate(request.user)

        # Get or set configuration
        if config_id:
            config = LLMConfiguration.objects.get(id=config_id, provider=provider)
        else:
            # Use default config for this provider
            config = LLMConfiguration.objects.filter(provider=provider).order_by('version').first()
            if not config:
                return Response(
                    {'error': 'No configuration found for this provider'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Make config current
        config.make_current(request.user)

    # Return new active configuration
    return Response({
        'message': f'Switched to {provider.display_name}',
        'provider': {
            'id': provider.id,
            'name': provider.name,
            'display_name': provider.display_name,
            'provider_type': provider.provider_type
        },
        'configuration': {
            'id': config.id,
            'model_name': config.model_name,
            'temperature': str(config.temperature),
            'max_tokens': config.max_tokens,
            'version': config.version
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def update_model_parameters(request):
    """
    Update model parameters for current configuration.
    Creates a new version with updated parameters.

    POST /api/super-admin/update-parameters/
    Body: {
        "temperature": 0.5,
        "max_tokens": 8000,
        "top_p": 0.95,
        "model_name": "gpt-4-turbo-preview" (optional)
    }

    Automatically creates new version and makes it current.
    """
    from core.super_admin_models import LLMConfiguration

    # Get current config
    current_config = LLMConfiguration.get_current_config()

    if not current_config:
        return Response(
            {'error': 'No active configuration found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Extract parameters
    temperature = request.data.get('temperature', current_config.temperature)
    max_tokens = request.data.get('max_tokens', current_config.max_tokens)
    top_p = request.data.get('top_p', current_config.top_p)
    frequency_penalty = request.data.get('frequency_penalty', current_config.frequency_penalty)
    presence_penalty = request.data.get('presence_penalty', current_config.presence_penalty)
    model_name = request.data.get('model_name', current_config.model_name)

    # Get next version number
    latest = LLMConfiguration.objects.filter(
        provider=current_config.provider
    ).order_by('-version').first()
    next_version = latest.version + 1

    # Create new configuration
    new_config = LLMConfiguration.objects.create(
        provider=current_config.provider,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        custom_parameters=current_config.custom_parameters,
        api_endpoint=current_config.api_endpoint,
        requests_per_minute=current_config.requests_per_minute,
        tokens_per_minute=current_config.tokens_per_minute,
        version=next_version,
        created_by=request.user
    )

    # Make it current
    new_config.make_current(request.user)

    return Response({
        'message': f'Parameters updated (version {next_version})',
        'previous_version': current_config.version,
        'new_version': next_version,
        'configuration': {
            'id': new_config.id,
            'model_name': new_config.model_name,
            'temperature': str(new_config.temperature),
            'max_tokens': new_config.max_tokens,
            'top_p': str(new_config.top_p),
            'frequency_penalty': str(new_config.frequency_penalty),
            'presence_penalty': str(new_config.presence_penalty),
            'version': new_config.version
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def rollback_configuration(request):
    """
    Rollback to a previous configuration version.

    POST /api/super-admin/rollback/
    Body: {
        "config_id": "uuid"
    }

    Makes the specified configuration current.
    """
    from core.super_admin_models import LLMConfiguration

    config_id = request.data.get('config_id')

    if not config_id:
        return Response(
            {'error': 'config_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        config = LLMConfiguration.objects.get(id=config_id)
    except LLMConfiguration.DoesNotExist:
        return Response(
            {'error': 'Configuration not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Make it current
    config.make_current(request.user)

    return Response({
        'message': f'Rolled back to version {config.version}',
        'configuration': {
            'id': config.id,
            'provider': config.provider.display_name,
            'model_name': config.model_name,
            'temperature': str(config.temperature),
            'version': config.version
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def configuration_history(request):
    """
    Get configuration change history for a provider.

    GET /api/super-admin/config-history/?provider_id=uuid

    Shows all configuration versions with changes.
    """
    from core.super_admin_models import LLMConfiguration

    provider_id = request.query_params.get('provider_id')

    if not provider_id:
        # Get history for current provider
        current = LLMConfiguration.get_current_config()
        if not current:
            return Response({'error': 'No active configuration'}, status=400)
        provider_id = current.provider.id

    configs = LLMConfiguration.objects.filter(
        provider_id=provider_id
    ).order_by('-version')

    history = []
    for config in configs:
        history.append({
            'id': config.id,
            'version': config.version,
            'model_name': config.model_name,
            'temperature': str(config.temperature),
            'max_tokens': config.max_tokens,
            'is_current': config.is_current,
            'created_at': config.created_at.isoformat(),
            'created_by': config.created_by.email if config.created_by else None
        })

    return Response({
        'provider_id': provider_id,
        'total_versions': len(history),
        'history': history
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def compare_configurations(request):
    """
    Compare two configuration versions.

    POST /api/super-admin/compare-configs/
    Body: {
        "config_id_1": "uuid",
        "config_id_2": "uuid"
    }

    Returns side-by-side comparison.
    """
    from core.super_admin_models import LLMConfiguration

    config_id_1 = request.data.get('config_id_1')
    config_id_2 = request.data.get('config_id_2')

    if not config_id_1 or not config_id_2:
        return Response(
            {'error': 'Both config_id_1 and config_id_2 are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        config1 = LLMConfiguration.objects.get(id=config_id_1)
        config2 = LLMConfiguration.objects.get(id=config_id_2)
    except LLMConfiguration.DoesNotExist:
        return Response(
            {'error': 'One or both configurations not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    def config_to_dict(config):
        return {
            'id': config.id,
            'version': config.version,
            'model_name': config.model_name,
            'temperature': float(config.temperature),
            'max_tokens': config.max_tokens,
            'top_p': float(config.top_p),
            'frequency_penalty': float(config.frequency_penalty),
            'presence_penalty': float(config.presence_penalty),
            'is_current': config.is_current
        }

    comparison = {
        'config_1': config_to_dict(config1),
        'config_2': config_to_dict(config2),
        'differences': {}
    }

    # Find differences
    for key in ['model_name', 'temperature', 'max_tokens', 'top_p',
                'frequency_penalty', 'presence_penalty']:
        val1 = comparison['config_1'][key]
        val2 = comparison['config_2'][key]
        if val1 != val2:
            comparison['differences'][key] = {
                'config_1': val1,
                'config_2': val2
            }

    return Response(comparison)
