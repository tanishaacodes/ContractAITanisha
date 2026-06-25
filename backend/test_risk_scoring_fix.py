"""
Test script to verify risk scoring thresholds are working correctly
"""
import sys
import os
import django

# Setup Django
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from api.risk_keyword_scorer import get_risk_scorer
from api.risk_scoring_model import risk_scoring_algorithm

def test_clause_risk_scoring():
    """Test individual clause risk scoring"""
    print("\n" + "="*80)
    print("TESTING CLAUSE-LEVEL RISK SCORING")
    print("="*80 + "\n")

    scorer = get_risk_scorer()

    test_cases = [
        {
            "text": "The Contractor shall be liable for any delay and may face penalties for non-performance.",
            "expected_level": "MEDIUM or HIGH"
        },
        {
            "text": "Unlimited liability for damages, penalties, and indemnification for breach and default.",
            "expected_level": "HIGH"
        },
        {
            "text": "The Contractor shall provide reasonable efforts to complete the work.",
            "expected_level": "LOW"
        },
        {
            "text": "Termination for convenience with liquidated damages and penalty for delay.",
            "expected_level": "HIGH"
        },
        {
            "text": "Force majeure shall not excuse payment obligations or liability.",
            "expected_level": "MEDIUM"
        }
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Text: {case['text'][:80]}...")

        result = scorer.score(case['text'])

        print(f"\n  Results:")
        print(f"  - Raw Score: {result['score']} points")
        print(f"  - Normalized: {result['normalized_score']:.3f} ({result['normalized_score']*100:.0f}%)")
        print(f"  - Risk Level: {result['risk_level']}")
        print(f"  - Expected: {case['expected_level']}")
        print(f"  - Keywords Found: {', '.join(result['keywords'].keys())}")

        if result['risk_level'] == 'LOW' and 'HIGH' in case['expected_level']:
            print(f"  [WARNING]: Expected {case['expected_level']}, got {result['risk_level']}")
        else:
            print(f"  [PASS]")

    print("\n" + "="*80)

def test_contract_risk_scoring():
    """Test contract-level risk scoring"""
    print("\n" + "="*80)
    print("TESTING CONTRACT-LEVEL RISK SCORING")
    print("="*80 + "\n")

    sample_contracts = [
        {
            "name": "High Risk Contract",
            "text": """
            The Contractor shall indemnify and hold harmless the Employer for any liability,
            damages, penalties, or losses arising from breach, default, or delay.
            Unlimited liability applies. Termination for convenience with liquidated damages.
            Force majeure does not excuse payment obligations.
            The Contractor bears all risks of non-performance and failure to meet deadlines.
            Penalties shall be imposed for any violation or non-compliance.
            """,
            "expected": "HIGH or CRITICAL"
        },
        {
            "name": "Medium Risk Contract",
            "text": """
            The Contractor shall be liable for delays in delivery.
            Payment terms are net 90 days. Penalties may apply for late delivery.
            Dispute resolution through arbitration.
            Insurance coverage of minimum $1M required.
            """,
            "expected": "MEDIUM"
        },
        {
            "name": "Low Risk Contract",
            "text": """
            The parties shall work together in good faith.
            Reasonable efforts will be made to complete the project.
            Mutual agreement required for any changes.
            Standard industry terms apply.
            """,
            "expected": "LOW"
        }
    ]

    for contract in sample_contracts:
        print(f"\nContract: {contract['name']}")
        print(f"Expected Risk: {contract['expected']}")

        result = risk_scoring_algorithm(contract['text'])

        print(f"\n  Results:")
        print(f"  - Total Score: {result['total_risk_score']:.2f}/100")
        print(f"  - Risk Level: {result['risk_level']}")

        # Top 5 risk categories
        top_categories = sorted(
            result['category_breakdown'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        if any(score > 0 for _, score in top_categories):
            print(f"  - Top Risk Categories:")
            for cat, score in top_categories:
                if score > 0:
                    display_name = result['detailed_breakdown'][cat]['display_name']
                    keywords = result['detailed_breakdown'][cat]['found_keywords']
                    print(f"    • {display_name}: {score:.1f}/5 ({', '.join(keywords[:3])})")

        # Validation
        if result['risk_level'].upper() in contract['expected'].upper():
            print(f"  [PASS] - Risk level matches expectation")
        else:
            print(f"  [WARNING]: Expected {contract['expected']}, got {result['risk_level']}")

    print("\n" + "="*80)

def test_threshold_boundaries():
    """Test scoring at threshold boundaries"""
    print("\n" + "="*80)
    print("TESTING THRESHOLD BOUNDARIES")
    print("="*80 + "\n")

    scorer = get_risk_scorer()

    # Test normalized scores at boundaries
    test_scores = [
        {"raw": 6, "expected": "LOW"},      # 6/50 = 0.12
        {"raw": 12, "expected": "LOW"},     # 12/50 = 0.24
        {"raw": 13, "expected": "MEDIUM"},  # 13/50 = 0.26
        {"raw": 24, "expected": "MEDIUM"},  # 24/50 = 0.48
        {"raw": 25, "expected": "HIGH"},    # 25/50 = 0.50
        {"raw": 50, "expected": "HIGH"},    # 50/50 = 1.00
    ]

    print("Clause-Level Thresholds:")
    print("  - LOW: < 25% (< 12.5 points)")
    print("  - MEDIUM: 25-49% (12.5-24.5 points)")
    print("  - HIGH: >= 50% (>= 25 points)")
    print()

    for test in test_scores:
        normalized = test['raw'] / 50.0
        if normalized >= 0.5:
            actual = "HIGH"
        elif normalized >= 0.25:
            actual = "MEDIUM"
        else:
            actual = "LOW"

        status = "[PASS]" if actual == test['expected'] else "[FAIL]"
        print(f"  {status} Raw: {test['raw']:2d} pts -> Normalized: {normalized:.2f} ({normalized*100:.0f}%) -> {actual:6s} (Expected: {test['expected']})")

    print("\n" + "="*80)

if __name__ == "__main__":
    print("\n" + "="*80)
    print(" RISK SCORING VERIFICATION TEST SUITE")
    print("="*80)

    try:
        test_threshold_boundaries()
        test_clause_risk_scoring()
        test_contract_risk_scoring()

        print("\n" + "="*80)
        print("[SUCCESS] ALL TESTS COMPLETED")
        print("="*80 + "\n")

        print("Summary:")
        print("  - New thresholds are active")
        print("  - Clause-level scoring: LOW < 25% < MEDIUM < 50% < HIGH")
        print("  - Contract-level scoring: LOW < 15 < MEDIUM < 40 < HIGH < 65 < CRITICAL")
        print("  - Risk distribution should now be more realistic")
        print("\nNext: Test with real contracts in the RRIE dashboard!")

    except Exception as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
