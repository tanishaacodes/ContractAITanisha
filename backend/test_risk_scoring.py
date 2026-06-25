"""
Test script for the new Risk Scoring Model
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from api.risk_scoring_model import risk_scoring_algorithm, generate_risk_summary, get_top_risk_categories

# Sample contract text with various risk keywords
SAMPLE_CONTRACT_TEXT = """
VENDOR AGREEMENT

This Vendor Agreement ("Agreement") is entered into as of January 1, 2024.

1. PAYMENT TERMS
Payment shall be made net 90 days after receipt of invoice. The Client reserves the right to
withhold payment for any disputed amounts. All payments are subject to offset rights.

2. LIABILITY
The Vendor shall be liable for unlimited liability including consequential damages, indirect damages,
and loss of profit. There is no liability cap on the Vendor's obligations. The Vendor shall
indemnify and hold harmless the Client against all third party claims arising from this Agreement.

3. TERMINATION
This Agreement shall automatically renew for successive one-year terms unless terminated.
Early termination fee of $50,000 applies. The Client may terminate for convenience with 180 days notice.
Post-termination obligations survive indefinitely.

4. INTELLECTUAL PROPERTY
All work for hire and IP assignment shall vest in the Client. The Vendor grants a perpetual license
and waives all moral rights. The Client shall have exclusive license to all derivative works.

5. CONFIDENTIALITY
The Vendor acknowledges that confidential information may be disclosed to third parties and affiliates.
Limited confidentiality applies with exceptions to confidentiality for permitted disclosure.

6. DATA PRIVACY
This Agreement involves processing of personal data, PII, and sensitive data. Cross-border transfer
of data is permitted. The Vendor is the data processor and must comply with GDPR and data breach
notification requirements.

7. GOVERNING LAW
This Agreement shall be governed by the laws of foreign jurisdiction. Exclusive jurisdiction
shall be in offshore courts. The parties agree to binding arbitration with a sole arbitrator
and waive the right to jury trial.

8. FORCE MAJEURE
Force majeure events exclude pandemic and government action. Payment obligations survive any
force majeure event.

9. INSURANCE
The Vendor shall maintain minimum insurance coverage of $1,000,000. Coverage exclusions apply
and the policy includes high deductibles. The Client shall be an additional insured.

10. AUDIT RIGHTS
The Client shall have unlimited audit rights with frequent audits permitted. Third party audits
may be conducted at any time. The Vendor shall bear all audit costs and provide access to records.

11. PENALTIES
Liquidated damages and performance penalties apply without cap. Daily penalties accrue for
late delivery with cumulative penalties. Penalty escalation applies for repeated breaches.

12. ASSIGNMENT
Assignment is prohibited without consent. Change of control triggers automatic termination.
No assignment rights are granted to the Vendor.

13. NON-COMPETE
The Vendor agrees to exclusivity and non-compete obligations for a period of 5 years across
all geographic markets. Customer restriction and employee restriction apply.

14. PRICING
The Client reserves the right to unilateral price changes and price escalation. Variable pricing
applies with no price lock. Index linked pricing adjusts automatically based on market conditions.

15. SERVICE LEVELS
Services are provided on a best efforts only basis. No SLA applies and performance standards are
non-binding. Remedy limitation applies to all service failures.
"""

def test_risk_scoring():
    """Test the risk scoring algorithm"""
    print("=" * 80)
    print("TESTING NEW RISK SCORING MODEL")
    print("=" * 80)
    print()

    # Run risk scoring
    print("Analyzing sample contract...")
    result = risk_scoring_algorithm(SAMPLE_CONTRACT_TEXT)

    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    print(f"Total Risk Score: {result['total_risk_score']}/100")
    print(f"Risk Level: {result['risk_level']}")
    print()

    # Show top risk categories
    print("=" * 80)
    print("TOP 10 RISK CATEGORIES (Sorted by Score)")
    print("=" * 80)
    top_risks = get_top_risk_categories(result['category_breakdown'], top_n=10)

    for i, (category, score) in enumerate(top_risks, 1):
        print(f"{i:2}. {category:40} {score:.1f}/5")

    print()
    print("=" * 80)
    print("DETAILED BREAKDOWN (Categories with Keywords Found)")
    print("=" * 80)
    print()

    # Show detailed breakdown for categories with scores > 0
    for category, details in sorted(result['detailed_breakdown'].items(),
                                   key=lambda x: x[1]['score'],
                                   reverse=True):
        if details['score'] > 0:
            print(f"{details['display_name']}")
            print(f"  Score: {details['score']:.2f}/5")
            print(f"  Keywords Found: {details['keyword_hits']}")
            if details['found_keywords']:
                keywords_display = ', '.join(details['found_keywords'][:5])
                remaining = len(details['found_keywords']) - 5
                if remaining > 0:
                    keywords_display += f" (+{remaining} more)"
                print(f"  Examples: {keywords_display}")
            print()

    # Generate summary
    print("=" * 80)
    print("RISK SUMMARY")
    print("=" * 80)
    print()
    summary = generate_risk_summary(result)
    print(summary)

    print()
    print("=" * 80)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == '__main__':
    test_risk_scoring()
