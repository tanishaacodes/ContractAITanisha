"""
Seed Script for Deviation & Safeguard Detection Features

This script populates the database with:
1. Gold-standard templates
2. Industry benchmarks
3. Expected obligations

Run: python seed_deviation_data.py
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import GoldStandardTemplate, IndustryBenchmark, ExpectedObligation
from api.embedding_service import EmbeddingService

embedding_service = EmbeddingService()


def seed_gold_standard_templates():
    """Seed gold-standard clause templates"""
    print("Seeding gold-standard templates...")

    templates = [
        {
            'template_name': 'Standard Liability Cap',
            'clause_category': 'LIABILITY',
            'approved_clause_text': 'Neither party\'s liability shall exceed the total amount paid under this agreement in the twelve (12) months preceding the claim, except for liability arising from fraud, willful misconduct, or breach of confidentiality.',
            'jurisdiction': 'New York',
            'safe_threshold': 0.90,
            'review_threshold': 0.75,
            'legal_notes': 'Protects against unlimited liability exposure while preserving accountability for intentional wrongdoing.'
        },
        {
            'template_name': 'Mutual Termination for Convenience',
            'clause_category': 'TERMINATION',
            'approved_clause_text': 'Either party may terminate this agreement for convenience upon thirty (30) days prior written notice to the other party.',
            'jurisdiction': None,
            'safe_threshold': 0.90,
            'review_threshold': 0.75,
            'legal_notes': 'Ensures both parties have equal right to exit the relationship, preventing vendor lock-in.'
        },
        {
            'template_name': 'Balanced Indemnification',
            'clause_category': 'INDEMNIFICATION',
            'approved_clause_text': 'Each party agrees to indemnify and hold harmless the other party from claims arising from its own negligence, willful misconduct, or breach of this agreement.',
            'jurisdiction': None,
            'safe_threshold': 0.88,
            'review_threshold': 0.73,
            'legal_notes': 'Mutual indemnification prevents one-sided risk allocation.'
        },
        {
            'template_name': 'IP Ownership Protection',
            'clause_category': 'IP_OWNERSHIP',
            'approved_clause_text': 'Each party retains all ownership rights to its pre-existing intellectual property. Any intellectual property created jointly shall be owned equally by both parties unless otherwise agreed in writing.',
            'jurisdiction': None,
            'safe_threshold': 0.90,
            'review_threshold': 0.75,
            'legal_notes': 'Protects your IP from automatic transfer to counterparty.'
        },
        {
            'template_name': 'Strong Confidentiality',
            'clause_category': 'CONFIDENTIALITY',
            'approved_clause_text': 'Both parties agree to maintain the confidentiality of all proprietary information disclosed under this agreement for a period of five (5) years following termination, using the same degree of care as for their own confidential information.',
            'jurisdiction': None,
            'safe_threshold': 0.90,
            'review_threshold': 0.75,
            'legal_notes': 'Ensures confidential information remains protected even after contract ends.'
        },
        {
            'template_name': 'SLA with Meaningful Penalties',
            'clause_category': 'SLA_PENALTIES',
            'approved_clause_text': 'Service provider shall maintain 99.9% uptime. For each hour of downtime beyond the SLA, customer shall receive a service credit equal to 5% of monthly fees, up to a maximum of 100% of monthly fees.',
            'jurisdiction': None,
            'safe_threshold': 0.85,
            'review_threshold': 0.70,
            'legal_notes': 'Incentivizes performance and provides customer recourse for service failures.'
        },
    ]

    for template_data in templates:
        # Generate embedding
        embedding = embedding_service.embed_text(template_data['approved_clause_text'])

        # Create or update template
        template, created = GoldStandardTemplate.objects.update_or_create(
            template_name=template_data['template_name'],
            defaults={
                **template_data,
                'embedding': embedding,
                'embedding_model': 'all-MiniLM-L6-v2',
                'is_active': True
            }
        )

        print(f"  {'Created' if created else 'Updated'}: {template.template_name}")

    print(f"[OK] Seeded {len(templates)} gold-standard templates\n")


def seed_industry_benchmarks():
    """Seed industry benchmark clauses"""
    print("Seeding industry benchmarks...")

    benchmarks = [
        {
            'benchmark_name': 'SaaS Liability Standard (IACCM)',
            'clause_category': 'LIABILITY',
            'benchmark_clause_text': 'Except for payment obligations and confidentiality breaches, neither party shall be liable for amounts exceeding fees paid in the twelve months prior to the claim.',
            'industry': 'SaaS',
            'adoption_rate': 85.5,
            'source': 'IACCM SaaS Benchmark Study 2024',
            'jurisdiction': None
        },
        {
            'benchmark_name': 'Standard Service Agreement Termination',
            'clause_category': 'TERMINATION',
            'benchmark_clause_text': 'Either party may terminate upon 30 days notice for convenience, or immediately for material breach that remains uncured for 15 days after written notice.',
            'industry': 'Professional Services',
            'adoption_rate': 78.2,
            'source': 'Industry Standard',
            'jurisdiction': None
        },
        {
            'benchmark_name': 'Tech Industry IP Clause',
            'clause_category': 'IP_OWNERSHIP',
            'benchmark_clause_text': 'Customer retains all rights to customer data and content. Service provider retains rights to the platform and any improvements. Work product created specifically for customer shall be owned by customer.',
            'industry': 'Technology',
            'adoption_rate': 82.1,
            'source': 'Tech Contract Standards',
            'jurisdiction': None
        },
    ]

    for benchmark_data in benchmarks:
        # Generate embedding
        embedding = embedding_service.embed_text(benchmark_data['benchmark_clause_text'])

        # Create or update benchmark
        benchmark, created = IndustryBenchmark.objects.update_or_create(
            benchmark_name=benchmark_data['benchmark_name'],
            defaults={
                **benchmark_data,
                'embedding': embedding,
                'embedding_model': 'all-MiniLM-L6-v2',
                'is_active': True
            }
        )

        print(f"  {'Created' if created else 'Updated'}: {benchmark.benchmark_name}")

    print(f"[OK] Seeded {len(benchmarks)} industry benchmarks\n")


def seed_expected_obligations():
    """Seed expected obligations for safeguard detection"""
    print("Seeding expected obligations...")

    obligations = [
        {
            'obligation_name': 'Termination for Convenience',
            'obligation_category': 'TERMINATION',
            'criticality': 'CRITICAL',
            'expected_clause_text': 'Either party may terminate this agreement for convenience upon written notice.',
            'presence_threshold': 0.70,
            'absence_risk_description': 'Contract lacks buyer-side termination rights—this exposes organization to vendor lock-in and prevents exit from unfavorable relationships.',
            'absence_risk_example': 'If vendor performance deteriorates or better alternatives emerge, you may be locked into the contract with no recourse.',
            'suggested_clause_text': 'Either party may terminate this agreement for convenience upon thirty (30) days prior written notice to the other party.',
            'contract_type': None,  # Applies to all contract types
            'party_protected': 'YOUR_COMPANY'
        },
        {
            'obligation_name': 'Limitation of Liability',
            'obligation_category': 'LIMITATION_LIABILITY',
            'criticality': 'CRITICAL',
            'expected_clause_text': 'Liability shall be limited to the amount paid under this agreement, excluding certain exceptions like fraud and willful misconduct.',
            'presence_threshold': 0.70,
            'absence_risk_description': 'Missing liability cap exposes organization to unlimited financial liability for contract breaches or service failures.',
            'absence_risk_example': 'Without a cap, a minor service failure could result in catastrophic financial damages far exceeding the contract value.',
            'suggested_clause_text': 'Neither party\'s total liability shall exceed the amount paid under this agreement in the twelve (12) months preceding the claim, except for liability arising from fraud, willful misconduct, or breach of confidentiality.',
            'contract_type': None,
            'party_protected': 'BOTH'
        },
        {
            'obligation_name': 'Mutual Indemnification',
            'obligation_category': 'INDEMNITY',
            'criticality': 'IMPORTANT',
            'expected_clause_text': 'Each party shall indemnify the other from claims arising from its own negligence or breach of the agreement.',
            'presence_threshold': 0.68,
            'absence_risk_description': 'Missing or one-sided indemnification creates unbalanced risk allocation, potentially exposing your organization to liability for the counterparty\'s actions.',
            'absence_risk_example': 'If vendor\'s negligence causes third-party claims, you may bear full liability without recourse.',
            'suggested_clause_text': 'Each party agrees to indemnify and hold harmless the other party from claims arising from its own negligence, willful misconduct, or breach of this agreement.',
            'contract_type': None,
            'party_protected': 'BOTH'
        },
        {
            'obligation_name': 'IP Ownership Protection',
            'obligation_category': 'IP_OWNERSHIP',
            'criticality': 'CRITICAL',
            'expected_clause_text': 'Customer retains ownership of customer data and content. Service provider retains ownership of the platform.',
            'presence_threshold': 0.70,
            'absence_risk_description': 'Unclear IP ownership can result in loss of proprietary data, work product, or innovations created during the contract.',
            'absence_risk_example': 'Custom software developed for you may become the vendor\'s property, limiting your ability to use or modify it.',
            'suggested_clause_text': 'Each party retains all ownership rights to its pre-existing intellectual property. Any intellectual property created jointly shall be owned equally by both parties unless otherwise agreed in writing.',
            'contract_type': None,
            'party_protected': 'YOUR_COMPANY'
        },
        {
            'obligation_name': 'Confidentiality Obligations',
            'obligation_category': 'CONFIDENTIALITY',
            'criticality': 'CRITICAL',
            'expected_clause_text': 'Both parties agree to maintain confidentiality of proprietary information disclosed under this agreement.',
            'presence_threshold': 0.72,
            'absence_risk_description': 'Missing confidentiality protection allows counterparty to freely disclose your sensitive business information, trade secrets, and proprietary data.',
            'absence_risk_example': 'Vendor could share your customer lists, pricing strategies, or technical specifications with competitors.',
            'suggested_clause_text': 'Both parties agree to maintain the confidentiality of all proprietary information disclosed under this agreement for a period of five (5) years following termination, using the same degree of care as for their own confidential information.',
            'contract_type': None,
            'party_protected': 'BOTH'
        },
        {
            'obligation_name': 'Data Protection & Privacy',
            'obligation_category': 'DATA_PROTECTION',
            'criticality': 'CRITICAL',
            'expected_clause_text': 'Service provider shall comply with applicable data protection laws and implement appropriate security measures to protect customer data.',
            'presence_threshold': 0.70,
            'absence_risk_description': 'Missing data protection obligations expose organization to regulatory violations (GDPR, CCPA), data breaches, and reputational damage.',
            'absence_risk_example': 'Vendor\'s inadequate data security could result in massive GDPR fines (up to 4% of annual revenue) and loss of customer trust.',
            'suggested_clause_text': 'Service provider shall comply with all applicable data protection laws and regulations, including GDPR and CCPA, and implement industry-standard security measures to protect customer data.',
            'contract_type': 'SaaS Agreement',
            'party_protected': 'YOUR_COMPANY'
        },
        {
            'obligation_name': 'SLA with Performance Penalties',
            'obligation_category': 'SLA_PENALTIES',
            'criticality': 'IMPORTANT',
            'expected_clause_text': 'Service provider shall maintain defined service levels with financial penalties for failures.',
            'presence_threshold': 0.65,
            'absence_risk_description': 'Missing SLA penalties remove financial incentive for vendor to maintain service quality, leaving you without recourse for poor performance.',
            'absence_risk_example': 'Vendor may deprioritize your service with frequent outages, knowing there are no financial consequences.',
            'suggested_clause_text': 'Service provider shall maintain 99.9% uptime. For each hour of downtime beyond the SLA, customer shall receive a service credit equal to 5% of monthly fees, up to a maximum of 100% of monthly fees.',
            'contract_type': 'SaaS Agreement',
            'party_protected': 'YOUR_COMPANY'
        },
        {
            'obligation_name': 'Audit Rights',
            'obligation_category': 'AUDIT_RIGHTS',
            'criticality': 'RECOMMENDED',
            'expected_clause_text': 'Customer shall have the right to audit service provider\'s compliance with the agreement.',
            'presence_threshold': 0.68,
            'absence_risk_description': 'Missing audit rights prevent verification of vendor compliance with contractual obligations, security standards, and data handling practices.',
            'absence_risk_example': 'Unable to verify if vendor is properly securing your data or complying with agreed-upon processes.',
            'suggested_clause_text': 'Customer shall have the right, upon reasonable notice, to audit service provider\'s compliance with this agreement, including security practices and data handling procedures.',
            'contract_type': None,
            'party_protected': 'YOUR_COMPANY'
        },
        {
            'obligation_name': 'Insurance Requirements',
            'obligation_category': 'INSURANCE',
            'criticality': 'IMPORTANT',
            'expected_clause_text': 'Service provider shall maintain appropriate insurance coverage including professional liability and cyber liability insurance.',
            'presence_threshold': 0.65,
            'absence_risk_description': 'Missing insurance requirements increase risk that vendor cannot cover damages from their errors or security breaches.',
            'absence_risk_example': 'If vendor causes data breach affecting millions of customers, they may lack financial capacity to cover damages.',
            'suggested_clause_text': 'Service provider shall maintain professional liability insurance of at least $2,000,000 and cyber liability insurance of at least $5,000,000, naming customer as additional insured.',
            'contract_type': 'SaaS Agreement',
            'party_protected': 'YOUR_COMPANY'
        },
    ]

    for obligation_data in obligations:
        # Generate embedding
        embedding = embedding_service.embed_text(obligation_data['expected_clause_text'])

        # Create or update obligation
        obligation, created = ExpectedObligation.objects.update_or_create(
            obligation_name=obligation_data['obligation_name'],
            defaults={
                **obligation_data,
                'embedding': embedding,
                'embedding_model': 'all-MiniLM-L6-v2',
                'is_active': True
            }
        )

        print(f"  {'Created' if created else 'Updated'}: {obligation.obligation_name} ({obligation.criticality})")

    print(f"[OK] Seeded {len(obligations)} expected obligations\n")


def main():
    print("=" * 80)
    print("SEEDING DEVIATION & SAFEGUARD DETECTION DATA")
    print("=" * 80)
    print()

    seed_gold_standard_templates()
    seed_industry_benchmarks()
    seed_expected_obligations()

    print("=" * 80)
    print("[OK] SEEDING COMPLETE!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Upload a contract: POST /api/contracts/upload")
    print("2. Extract clauses: POST /api/contracts/{id}/extract-clauses")
    print("3. Analyze deviations: POST /api/embedding/contracts/{id}/analyze-deviations")
    print("4. Detect safeguards: POST /api/embedding/contracts/{id}/detect-safeguards")
    print("5. View heatmap: GET /api/embedding/contracts/{id}/risk-heatmap")
    print()


if __name__ == '__main__':
    main()
