"""
Seed compliance frameworks from JSON configuration into the database.

Usage:
  python manage.py shell < seed_compliance_frameworks.py

Or:
  python seed_compliance_frameworks.py
"""

import json
import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import ComplianceFramework, ComplianceRequirement


def seed_compliance_frameworks():
    """Load compliance frameworks from JSON and populate database"""

    json_path = os.path.join(os.path.dirname(__file__), 'compliance_frameworks.json')

    print(f"Loading compliance frameworks from: {json_path}")

    with open(json_path, 'r') as f:
        data = json.load(f)

    frameworks_created = 0
    frameworks_updated = 0
    requirements_created = 0
    requirements_updated = 0

    for framework_data in data['frameworks']:
        requirements_data = framework_data.pop('requirements', [])

        # Convert effective_date from string to datetime if provided
        if framework_data.get('effective_date'):
            try:
                framework_data['effective_date'] = datetime.strptime(
                    framework_data['effective_date'], '%Y-%m-%d'
                ).date()
            except (ValueError, TypeError):
                framework_data['effective_date'] = None

        # Create or update framework
        framework, created = ComplianceFramework.objects.update_or_create(
            code=framework_data['code'],
            defaults={
                'name': framework_data['name'],
                'description': framework_data['description'],
                'jurisdiction': framework_data.get('jurisdiction'),
                'effective_date': framework_data.get('effective_date'),
                'version': framework_data.get('version'),
                'is_active': framework_data.get('is_active', True),
                'priority': framework_data.get('priority', 1),
            }
        )

        if created:
            frameworks_created += 1
            status = '[OK] Created'
        else:
            frameworks_updated += 1
            status = '[UPDATED]'

        print(f"{status}: {framework.code} - {framework.name}")

        # Create or update requirements
        for req_data in requirements_data:
            requirement, req_created = ComplianceRequirement.objects.update_or_create(
                framework=framework,
                requirement_code=req_data['requirement_code'],
                defaults={
                    'requirement_name': req_data['requirement_name'],
                    'description': req_data['description'],
                    'requirement_type': req_data['requirement_type'],
                    'criticality': req_data['criticality'],
                    'detection_keywords': req_data.get('detection_keywords', []),
                    'risk_weight': req_data.get('risk_weight', 1.0),
                    'compliance_score_weight': req_data.get('compliance_score_weight', 1.0),
                    'legal_reference': req_data.get('legal_reference'),
                    'is_active': True,
                }
            )

            if req_created:
                requirements_created += 1
                req_status = '  [OK] Created'
            else:
                requirements_updated += 1
                req_status = '  [UPDATED]'

            print(f"{req_status}: {requirement.requirement_code}")

    # Print summary
    print("\n" + "="*60)
    print("SEEDING COMPLETE!")
    print("="*60)
    print(f"Frameworks created:    {frameworks_created}")
    print(f"Frameworks updated:    {frameworks_updated}")
    print(f"Requirements created:  {requirements_created}")
    print(f"Requirements updated:  {requirements_updated}")
    print(f"\nTotal frameworks:      {ComplianceFramework.objects.count()}")
    print(f"Total requirements:    {ComplianceRequirement.objects.count()}")
    print("="*60)


if __name__ == '__main__':
    seed_compliance_frameworks()
