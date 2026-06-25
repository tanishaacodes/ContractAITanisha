"""
Populate standard template clauses for different contract types
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import TemplateClause

def populate_template_clauses():
    """Populate template clauses for all contract types"""

    # Define standard clauses for each contract type
    template_data = {
        'NDA': [
            {'clause_name': 'Confidentiality', 'importance': 'CRITICAL', 'description': 'Protection of confidential information'},
            {'clause_name': 'Non-Disclosure', 'importance': 'CRITICAL', 'description': 'Prohibition on disclosing confidential information'},
            {'clause_name': 'Termination', 'importance': 'IMPORTANT', 'description': 'Conditions for ending the agreement'},
            {'clause_name': 'Governing Law', 'importance': 'IMPORTANT', 'description': 'Jurisdiction and applicable law'},
            {'clause_name': 'Dispute Resolution', 'importance': 'IMPORTANT', 'description': 'Process for resolving disputes'},
            {'clause_name': 'Severability', 'importance': 'OPTIONAL', 'description': 'Invalidity of one provision doesn\'t affect others'},
            {'clause_name': 'Entire Agreement', 'importance': 'OPTIONAL', 'description': 'This agreement supersedes all prior agreements'},
        ],
        'Master Service Agreement': [
            {'clause_name': 'Payment Terms', 'importance': 'CRITICAL', 'description': 'Payment schedule and terms', 'risk_keywords': ['net 90', 'net 120', 'upon demand', 'no refund']},
            {'clause_name': 'Limitation of Liability', 'importance': 'CRITICAL', 'description': 'Limits on liability exposure', 'risk_keywords': ['unlimited liability', 'no cap', 'consequential damages']},
            {'clause_name': 'Indemnification', 'importance': 'CRITICAL', 'description': 'Agreement to compensate for losses', 'risk_keywords': ['indemnify client', 'hold harmless', 'defend']},
            {'clause_name': 'Termination', 'importance': 'CRITICAL', 'description': 'Conditions for ending the agreement', 'risk_keywords': ['terminate for convenience', 'immediate termination', 'no notice']},
            {'clause_name': 'Intellectual Property', 'importance': 'CRITICAL', 'description': 'IP ownership and rights', 'risk_keywords': ['work for hire', 'all rights', 'exclusive']},
            {'clause_name': 'Warranty', 'importance': 'IMPORTANT', 'description': 'Guarantees and representations', 'risk_keywords': ['no warranty', 'as-is', 'disclaimer']},
            {'clause_name': 'Confidentiality', 'importance': 'IMPORTANT', 'description': 'Protection of confidential information'},
            {'clause_name': 'Renewal', 'importance': 'IMPORTANT', 'description': 'Terms for renewing the agreement', 'risk_keywords': ['auto-renew', 'automatic renewal']},
            {'clause_name': 'Governing Law', 'importance': 'IMPORTANT', 'description': 'Jurisdiction and applicable law'},
            {'clause_name': 'Dispute Resolution', 'importance': 'IMPORTANT', 'description': 'Process for resolving disputes'},
            {'clause_name': 'Insurance', 'importance': 'IMPORTANT', 'description': 'Required insurance coverage', 'risk_keywords': ['maintain insurance', 'million coverage']},
        ],
        'Service Level Agreement': [
            {'clause_name': 'Payment Terms', 'importance': 'CRITICAL', 'description': 'Payment schedule and terms'},
            {'clause_name': 'Termination', 'importance': 'CRITICAL', 'description': 'Conditions for ending the agreement'},
            {'clause_name': 'Limitation of Liability', 'importance': 'CRITICAL', 'description': 'Limits on liability exposure'},
            {'clause_name': 'Indemnification', 'importance': 'IMPORTANT', 'description': 'Agreement to compensate for losses'},
            {'clause_name': 'Warranty', 'importance': 'IMPORTANT', 'description': 'Service level guarantees'},
            {'clause_name': 'Renewal', 'importance': 'IMPORTANT', 'description': 'Terms for renewing the agreement'},
            {'clause_name': 'Dispute Resolution', 'importance': 'IMPORTANT', 'description': 'Process for resolving disputes'},
        ],
        'Employment Agreement': [
            {'clause_name': 'Payment Terms', 'importance': 'CRITICAL', 'description': 'Compensation and benefits'},
            {'clause_name': 'Termination', 'importance': 'CRITICAL', 'description': 'Conditions for ending employment'},
            {'clause_name': 'Confidentiality', 'importance': 'CRITICAL', 'description': 'Protection of company information'},
            {'clause_name': 'Intellectual Property', 'importance': 'CRITICAL', 'description': 'IP rights for work created'},
            {'clause_name': 'Non-Disclosure', 'importance': 'IMPORTANT', 'description': 'Prohibition on disclosing confidential information'},
            {'clause_name': 'Governing Law', 'importance': 'IMPORTANT', 'description': 'Jurisdiction and applicable law'},
            {'clause_name': 'Entire Agreement', 'importance': 'OPTIONAL', 'description': 'This agreement supersedes all prior agreements'},
        ],
        'Consulting Agreement': [
            {'clause_name': 'Payment Terms', 'importance': 'CRITICAL', 'description': 'Fee structure and payment terms'},
            {'clause_name': 'Intellectual Property', 'importance': 'CRITICAL', 'description': 'IP ownership for work product'},
            {'clause_name': 'Confidentiality', 'importance': 'CRITICAL', 'description': 'Protection of confidential information'},
            {'clause_name': 'Termination', 'importance': 'IMPORTANT', 'description': 'Conditions for ending the engagement'},
            {'clause_name': 'Limitation of Liability', 'importance': 'IMPORTANT', 'description': 'Limits on liability exposure'},
            {'clause_name': 'Indemnification', 'importance': 'IMPORTANT', 'description': 'Agreement to compensate for losses'},
            {'clause_name': 'Dispute Resolution', 'importance': 'IMPORTANT', 'description': 'Process for resolving disputes'},
        ],
        'License Agreement': [
            {'clause_name': 'Payment Terms', 'importance': 'CRITICAL', 'description': 'License fees and payment terms'},
            {'clause_name': 'Intellectual Property', 'importance': 'CRITICAL', 'description': 'IP rights and license scope'},
            {'clause_name': 'Termination', 'importance': 'CRITICAL', 'description': 'Conditions for license termination'},
            {'clause_name': 'Warranty', 'importance': 'IMPORTANT', 'description': 'Guarantees about the licensed property'},
            {'clause_name': 'Limitation of Liability', 'importance': 'IMPORTANT', 'description': 'Limits on liability exposure'},
            {'clause_name': 'Renewal', 'importance': 'IMPORTANT', 'description': 'Terms for license renewal'},
            {'clause_name': 'Assignment', 'importance': 'IMPORTANT', 'description': 'Transfer of license rights'},
        ],
    }

    print("="*60)
    print("Populating Template Clauses")
    print("="*60)

    # Clear existing template clauses
    deleted_count = TemplateClause.objects.all().count()
    TemplateClause.objects.all().delete()
    print(f"\n[CLEANUP] Deleted {deleted_count} existing template clauses")

    total_created = 0

    # Create template clauses for each contract type
    for contract_type, clauses in template_data.items():
        print(f"\n[{contract_type}] Creating {len(clauses)} template clauses...")

        for clause_data in clauses:
            template = TemplateClause.objects.create(
                contract_type=contract_type,
                clause_name=clause_data['clause_name'],
                importance=clause_data['importance'],
                description=clause_data.get('description', ''),
                risk_keywords=clause_data.get('risk_keywords', [])
            )
            total_created += 1

            importance_icon = {
                'CRITICAL': '[!!!]',
                'IMPORTANT': '[ ! ]',
                'OPTIONAL': '[ - ]'
            }[template.importance]

            print(f"  {importance_icon} {template.clause_name}")

    print(f"\n{'='*60}")
    print(f"[SUCCESS] Created {total_created} template clauses for {len(template_data)} contract types")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    populate_template_clauses()
