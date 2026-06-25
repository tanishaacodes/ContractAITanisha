"""
Seed script to populate pricing plans in the database.
Run this script to create the 5 pricing plans for the Contract AI product.
"""
import os
import django
import sys

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import PricingPlan

def seed_pricing_plans():
    """Create 5 pricing plans with features and limits"""

    plans_data = [
        {
            'name': 'Free',
            'display_name': 'Free Plan',
            'plan_type': 'FREE',
            'price_monthly': 0.00,
            'contract_limit': 5,
            'description': 'Perfect for trying out Contract AI',
            'is_contact_sales': False,
            'sort_order': 1,
            'features': [
                'Analyse Risks',
                'Clauses Library',
                '5 Contracts'
            ],
            'feature_flags': {
                'analyse_risks': True,
                'clauses_library': True,
                'analyse_intents': False,
                'contract_clustering': False,
                'comprehensive_risk_management': False
            }
        },
        {
            'name': 'Standard',
            'display_name': 'Standard Plan',
            'plan_type': 'STANDARD',
            'price_monthly': 10.00,
            'contract_limit': 30,
            'description': 'Great for small teams and growing businesses',
            'is_contact_sales': False,
            'sort_order': 2,
            'features': [
                'Everything in Free Plan',
                'Analyse Risks',
                'Clauses Library',
                '30 Contracts'
            ],
            'feature_flags': {
                'analyse_risks': True,
                'clauses_library': True,
                'analyse_intents': False,
                'contract_clustering': False,
                'comprehensive_risk_management': False
            }
        },
        {
            'name': 'Professional',
            'display_name': 'Professional Plan',
            'plan_type': 'PROFESSIONAL',
            'price_monthly': 30.00,
            'contract_limit': 120,
            'description': 'Advanced features for legal teams',
            'is_contact_sales': False,
            'sort_order': 3,
            'features': [
                'Everything in Standard Plan',
                'Analyse Intents',
                'Contract Clustering',
                'Comprehensive Risk Management',
                '120 Contracts'
            ],
            'feature_flags': {
                'analyse_risks': True,
                'clauses_library': True,
                'analyse_intents': True,
                'contract_clustering': True,
                'comprehensive_risk_management': True
            }
        },
        {
            'name': 'Enterprise',
            'display_name': 'Enterprise Plan',
            'plan_type': 'ENTERPRISE',
            'price_monthly': 0.00,  # Custom pricing
            'contract_limit': -1,  # Unlimited
            'description': 'Unlimited contracts with dedicated support',
            'is_contact_sales': True,
            'sort_order': 4,
            'features': [
                'Everything in Professional Plan',
                'Unlimited Contracts',
                'Dedicated Account Manager',
                'Priority Support',
                'Custom Integrations'
            ],
            'feature_flags': {
                'analyse_risks': True,
                'clauses_library': True,
                'analyse_intents': True,
                'contract_clustering': True,
                'comprehensive_risk_management': True,
                'priority_support': True,
                'custom_integrations': True
            }
        },
        {
            'name': 'On-Premise',
            'display_name': 'On-Premise',
            'plan_type': 'ON_PREMISE',
            'price_monthly': 0.00,  # Custom pricing
            'contract_limit': -1,  # Unlimited
            'description': 'Full deployment with DMS and SAP integration',
            'is_contact_sales': True,
            'sort_order': 5,
            'features': [
                'Everything in Enterprise Plan',
                'DMS Integration',
                'SAP Integration',
                'On-Premise Deployment',
                'Full Data Control',
                'Custom SLA'
            ],
            'feature_flags': {
                'analyse_risks': True,
                'clauses_library': True,
                'analyse_intents': True,
                'contract_clustering': True,
                'comprehensive_risk_management': True,
                'priority_support': True,
                'custom_integrations': True,
                'dms_integration': True,
                'sap_integration': True,
                'on_premise': True
            }
        }
    ]

    print("Seeding pricing plans...")

    for plan_data in plans_data:
        plan, created = PricingPlan.objects.update_or_create(
            plan_type=plan_data['plan_type'],
            defaults=plan_data
        )

        if created:
            print(f"Created: {plan.display_name} (${plan.price_monthly}/mo)")
        else:
            print(f"Updated: {plan.display_name} (${plan.price_monthly}/mo)")

    print(f"\nSuccessfully seeded {len(plans_data)} pricing plans!")

    # Print summary
    print("\nPricing Plans Summary:")
    print("-" * 60)
    for plan in PricingPlan.objects.all():
        limit = "Unlimited" if plan.contract_limit == -1 else f"{plan.contract_limit} contracts"
        price = "Custom" if plan.is_contact_sales else f"${plan.price_monthly}/mo"
        print(f"{plan.display_name:20} | {price:15} | {limit}")
    print("-" * 60)

if __name__ == '__main__':
    seed_pricing_plans()
