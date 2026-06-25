"""
Django Management Command: Initialize Default LLM Providers

Creates default LLM provider configurations:
- OpenAI GPT-4
- Claude Sonnet
- Google Gemini
- Ollama (local)

Usage:
    python manage.py init_llm_providers

Author: ContractAI Platform
Version: 1.0.0
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from core.super_admin_models import LLMProvider, LLMConfiguration
from core.models import User
import uuid


class Command(BaseCommand):
    help = 'Initialize default LLM provider configurations'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write(self.style.WARNING('INITIALIZING DEFAULT LLM PROVIDERS'))
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write('')

        # Get Super Admin user for created_by field
        super_admin = User.objects.filter(role__name='Super Admin').first()

        if not super_admin:
            self.stdout.write(self.style.ERROR('No Super Admin user found. Create one first.'))
            return

        providers_config = [
            {
                'name': 'openai_gpt4',
                'display_name': 'OpenAI GPT-4 Turbo',
                'provider_type': 'OPENAI',
                'config_schema': {
                    'required': ['api_key', 'model_name'],
                    'optional': ['organization_id', 'base_url']
                },
                'default_config': {
                    'model_name': 'gpt-4-turbo-preview',
                    'temperature': 0.7,
                    'max_tokens': 4096,
                    'top_p': 1.0
                },
                'requires_api_key': True,
                'priority': 1
            },
            {
                'name': 'claude_sonnet',
                'display_name': 'Claude 3.5 Sonnet',
                'provider_type': 'ANTHROPIC',
                'config_schema': {
                    'required': ['api_key', 'model_name'],
                    'optional': ['base_url']
                },
                'default_config': {
                    'model_name': 'claude-3-5-sonnet-20241022',
                    'temperature': 0.7,
                    'max_tokens': 4096
                },
                'requires_api_key': True,
                'priority': 2
            },
            {
                'name': 'gemini_pro',
                'display_name': 'Google Gemini Pro',
                'provider_type': 'GOOGLE',
                'config_schema': {
                    'required': ['api_key', 'model_name'],
                    'optional': []
                },
                'default_config': {
                    'model_name': 'gemini-pro',
                    'temperature': 0.7,
                    'max_tokens': 2048
                },
                'requires_api_key': True,
                'priority': 3
            },
            {
                'name': 'ollama_local',
                'display_name': 'Ollama (Local)',
                'provider_type': 'OLLAMA',
                'config_schema': {
                    'required': ['base_url', 'model_name'],
                    'optional': []
                },
                'default_config': {
                    'model_name': 'qwen2.5:0.5b',
                    'base_url': 'http://localhost:11434',
                    'temperature': 0.7,
                    'max_tokens': 2048
                },
                'requires_api_key': False,
                'priority': 4
            }
        ]

        with transaction.atomic():
            created_count = 0

            for config in providers_config:
                # Check if provider already exists
                if LLMProvider.objects.filter(name=config['name']).exists():
                    self.stdout.write(
                        self.style.NOTICE(f"Provider '{config['display_name']}' already exists, skipping...")
                    )
                    continue

                # Create provider
                provider = LLMProvider.objects.create(
                    id=str(uuid.uuid4()),
                    name=config['name'],
                    display_name=config['display_name'],
                    provider_type=config['provider_type'],
                    is_active=False,  # Not active by default
                    is_available=True,
                    config_schema=config['config_schema'],
                    default_config=config['default_config'],
                    requires_api_key=config['requires_api_key'],
                    priority=config['priority'],
                    created_by=super_admin
                )

                # Create default configuration
                default_conf = config['default_config']
                LLMConfiguration.objects.create(
                    id=str(uuid.uuid4()),
                    provider=provider,
                    model_name=default_conf['model_name'],
                    temperature=default_conf.get('temperature', 0.7),
                    max_tokens=default_conf.get('max_tokens', 4096),
                    top_p=1.0,
                    frequency_penalty=0.0,
                    presence_penalty=0.0,
                    custom_parameters={},
                    api_endpoint=default_conf.get('base_url'),
                    is_current=False,
                    version=1,
                    created_by=super_admin
                )

                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"[OK] Created provider: {config['display_name']}")
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'[OK] Initialized {created_count} LLM providers'))
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('Next steps:'))
        self.stdout.write('  1. Add API keys via Super Admin dashboard')
        self.stdout.write('  2. Activate desired provider')
        self.stdout.write('  3. Configure model parameters')
        self.stdout.write('')
