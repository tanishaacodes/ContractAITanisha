"""
Management command to seed departments
Usage: python manage.py seed_departments
"""
from django.core.management.base import BaseCommand
from apps.bid_actions.models import Department


class Command(BaseCommand):
    help = 'Seeds department data for bid management'

    def handle(self, *args, **options):
        departments = [
            {
                'name': 'Civil',
                'code': 'CIV',
                'description': 'Civil engineering, foundation, structural works',
                'color_hex': '#3b82f6',
                'workload_weight': 1.5
            },
            {
                'name': 'Mechanical',
                'code': 'MECH',
                'description': 'HVAC, elevators, mechanical equipment',
                'color_hex': '#f97316',
                'workload_weight': 1.2
            },
            {
                'name': 'Electrical',
                'code': 'ELEC',
                'description': 'Power distribution, cabling, electrical systems',
                'color_hex': '#eab308',
                'workload_weight': 1.3
            },
            {
                'name': 'MEP',
                'code': 'MEP',
                'description': 'MEP coordination, fire fighting, plumbing',
                'color_hex': '#06b6d4',
                'workload_weight': 1.1
            },
            {
                'name': 'Signaling',
                'code': 'SIG',
                'description': 'Signaling, telecom, train control systems',
                'color_hex': '#ec4899',
                'workload_weight': 1.2
            },
            {
                'name': 'Planning',
                'code': 'PLN',
                'description': 'Project planning, scheduling, Primavera P6',
                'color_hex': '#a855f7',
                'workload_weight': 0.8
            },
            {
                'name': 'Procurement',
                'code': 'PROC',
                'description': 'Procurement, vendor management, material sourcing',
                'color_hex': '#6366f1',
                'workload_weight': 1.0
            },
            {
                'name': 'Finance',
                'code': 'FIN',
                'description': 'Financial analysis, costing, bank guarantees',
                'color_hex': '#22c55e',
                'workload_weight': 0.7
            },
            {
                'name': 'Legal',
                'code': 'LEG',
                'description': 'Contract review, legal compliance, arbitration',
                'color_hex': '#ef4444',
                'workload_weight': 0.9
            },
            {
                'name': 'HSE',
                'code': 'HSE',
                'description': 'Health, safety, environment compliance',
                'color_hex': '#f43f5e',
                'workload_weight': 0.6
            },
            {
                'name': 'QA/QC',
                'code': 'QA',
                'description': 'Quality assurance, inspection, testing',
                'color_hex': '#14b8a6',
                'workload_weight': 0.8
            },
        ]

        created_count = 0
        updated_count = 0

        for dept_data in departments:
            dept, created = Department.objects.update_or_create(
                name=dept_data['name'],
                defaults={
                    'code': dept_data['code'],
                    'description': dept_data['description'],
                    'color_hex': dept_data['color_hex'],
                    'workload_weight': dept_data['workload_weight']
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created department: {dept.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated department: {dept.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSeeding complete! Created: {created_count}, Updated: {updated_count}'
            )
        )
