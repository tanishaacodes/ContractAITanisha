"""
Django Management Command: Create Super Admin

CRITICAL SECURITY:
- This is the ONLY way to create Super Admin accounts
- Cannot be called via API
- Requires direct server access
- All creations are audit logged

Usage:
    python manage.py create_superadmin --email admin@company.com --password SecurePass123!

Author: ContractAI Platform
Version: 1.0.0
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import User, Role
from core.super_admin_models import SuperAdminAuditLog, RoleLevel
import getpass
import uuid


class Command(BaseCommand):
    help = 'Create a Super Admin user (ONLY method to create Super Admin)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email address for Super Admin'
        )
        parser.add_argument(
            '--password',
            type=str,
            required=False,
            help='Password for Super Admin (prompted if not provided)'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            required=False,
            default='',
            help='First name (optional)'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            required=False,
            default='',
            help='Last name (optional)'
        )
        parser.add_argument(
            '--skip-confirmation',
            action='store_true',
            help='Skip confirmation prompt (use with caution)'
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options.get('password')
        first_name = options.get('first_name', '')
        last_name = options.get('last_name', '')
        skip_confirmation = options.get('skip_confirmation', False)

        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write(self.style.WARNING('SUPER ADMIN CREATION'))
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write('')

        # Validate email
        if User.objects.filter(email=email).exists():
            raise CommandError(f'User with email {email} already exists')

        # Get or create Super Admin role
        super_admin_role = self._get_or_create_super_admin_role()

        # Get password if not provided
        if not password:
            self.stdout.write(self.style.NOTICE('Password not provided. You will be prompted.'))
            password = getpass.getpass('Enter password: ')
            password_confirm = getpass.getpass('Confirm password: ')

            if password != password_confirm:
                raise CommandError('Passwords do not match')

        # Validate password strength
        self._validate_password(password)

        # Show summary
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('Super Admin Details:'))
        self.stdout.write(f'  Email: {email}')
        self.stdout.write(f'  First Name: {first_name or "(not provided)"}')
        self.stdout.write(f'  Last Name: {last_name or "(not provided)"}')
        self.stdout.write(f'  Role: {super_admin_role.name} (Level: {getattr(super_admin_role, "role_level", 0)})')
        self.stdout.write('')

        # Confirmation
        if not skip_confirmation:
            confirmation = input('Create this Super Admin? [y/N]: ')
            if confirmation.lower() != 'y':
                self.stdout.write(self.style.ERROR('Aborted.'))
                return

        # Create Super Admin
        try:
            with transaction.atomic():
                user = User.objects.create(
                    id=str(uuid.uuid4()),
                    email=email,
                    password=password,  # Will be hashed by User.save()
                    first_name=first_name,
                    last_name=last_name,
                    role=super_admin_role,
                    is_active=True
                )

                # Create audit log
                # Note: We create a "system" user for audit trail since this is CLI
                audit_log = SuperAdminAuditLog.objects.create(
                    user=user,  # Log against itself (bootstrap case)
                    user_email=email,
                    user_role='SYSTEM',
                    action_type='SUPER_ADMIN_CREATED',
                    resource_type='user',
                    resource_id=user.id,
                    action_summary=f'Super Admin created via management command: {email}',
                    new_values={
                        'email': email,
                        'role': super_admin_role.name,
                        'created_via': 'management_command'
                    }
                )

                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('✓ Super Admin created successfully!'))
                self.stdout.write('')
                self.stdout.write(self.style.NOTICE('Details:'))
                self.stdout.write(f'  User ID: {user.id}')
                self.stdout.write(f'  Email: {user.email}')
                self.stdout.write(f'  Role: {user.role.name}')
                self.stdout.write(f'  Audit Log ID: {audit_log.id}')
                self.stdout.write('')
                self.stdout.write(self.style.WARNING('IMPORTANT:'))
                self.stdout.write('  1. Store these credentials securely')
                self.stdout.write('  2. Change password on first login')
                self.stdout.write('  3. Enable 2FA if available')
                self.stdout.write('  4. All actions will be audit logged')
                self.stdout.write('')

        except Exception as e:
            raise CommandError(f'Failed to create Super Admin: {str(e)}')

    def _get_or_create_super_admin_role(self):
        """
        Get or create Super Admin role.

        Ensures role_level = 0 and is_system_role = True
        """
        try:
            # Try to get existing Super Admin role
            role = Role.objects.get(name='Super Admin')

            # Update role_level if not set (migration case)
            if hasattr(role, 'role_level'):
                if role.role_level != RoleLevel.SUPER_ADMIN:
                    role.role_level = RoleLevel.SUPER_ADMIN
                    role.save()

            if hasattr(role, 'is_system_role'):
                if not role.is_system_role:
                    role.is_system_role = True
                    role.save()

            return role

        except Role.DoesNotExist:
            # Create Super Admin role
            self.stdout.write(self.style.NOTICE('Super Admin role not found. Creating...'))

            role_data = {
                'id': str(uuid.uuid4()),
                'name': 'Super Admin',
                'description': 'Platform Super Administrator with full system access',
                'permissions': {
                    'system_config': True,
                    'llm_management': True,
                    'user_management': True,
                    'all_contracts': True,
                    'audit_logs': True
                }
            }

            # Add new fields if they exist (after migration)
            if hasattr(Role, 'role_level'):
                role_data['role_level'] = RoleLevel.SUPER_ADMIN

            if hasattr(Role, 'is_system_role'):
                role_data['is_system_role'] = True

            role = Role.objects.create(**role_data)

            self.stdout.write(self.style.SUCCESS('✓ Super Admin role created'))
            return role

    def _validate_password(self, password):
        """
        Validate password strength.

        Requirements:
        - At least 12 characters
        - Contains uppercase and lowercase
        - Contains numbers
        - Contains special characters
        """
        if len(password) < 12:
            raise CommandError('Password must be at least 12 characters long')

        if not any(c.isupper() for c in password):
            raise CommandError('Password must contain at least one uppercase letter')

        if not any(c.islower() for c in password):
            raise CommandError('Password must contain at least one lowercase letter')

        if not any(c.isdigit() for c in password):
            raise CommandError('Password must contain at least one number')

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            raise CommandError('Password must contain at least one special character')

        self.stdout.write(self.style.SUCCESS('✓ Password meets security requirements'))
