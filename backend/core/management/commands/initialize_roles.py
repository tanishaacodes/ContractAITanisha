from django.core.management.base import BaseCommand
from core.models import Role


class Command(BaseCommand):
    help = 'Initialize default roles for the application'

    def handle(self, *args, **options):
        default_roles = [
            {
                'name': 'SuperAdmin',
                'description': 'Super administrator with user management and connector permissions',
                'permissions': {
                    'manage_users': True,
                    'assign_connectors': True,
                    'system_settings': True
                }
            },
            {
                'name': 'Admin',
                'description': 'Full system access'
            },
            {
                'name': 'Legal Reviewer',
                'description': 'Can review and comment on contracts'
            },
            {
                'name': 'Proc Reviewer',
                'description': 'Can review and approve procurement contracts'
            },
            {
                'name': 'Viewer',
                'description': 'Read-only access to contracts'
            },
        ]

        for role_data in default_roles:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'description': role_data['description'],
                    'permissions': role_data.get('permissions', {})
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created role: {role.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Role already exists: {role.name}')
                )

        self.stdout.write(self.style.SUCCESS('All default roles initialized'))
