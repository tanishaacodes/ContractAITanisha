"""
Test script to verify jurisdiction-specific rules work correctly.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
import django
django.setup()

from api.redline_engine import generate_suggested_clause

def test_jurisdiction_rules():
    print("\n" + "="*80)
    print("JURISDICTION-SPECIFIC RULES TEST")
    print("="*80)

    # Test clause
    test_clause = "Payment due immediately and party may terminate at will without notice."

    jurisdictions = ['Common Law', 'UAE', 'EU', 'US', 'UK']

    for jurisdiction in jurisdictions:
        print(f"\n{'='*60}")
        print(f"Jurisdiction: {jurisdiction}")
        print('='*60)
        print(f"Original: {test_clause}\n")

        # Generate suggestion with medium risk (50) to trigger fallback rules
        suggestion = generate_suggested_clause(
            clause_text=test_clause,
            risk_score=50,
            risk_type="PAYMENT",
            jurisdiction=jurisdiction
        )

        print(f"Suggested: {suggestion}")
        print(f"Changed: {'YES' if suggestion != test_clause else 'NO'}")

if __name__ == "__main__":
    print("\n" + "#"*80)
    print("# ContractAI - Jurisdiction Rules Test")
    print("# Testing fallback rules for different countries")
    print("#"*80)

    test_jurisdiction_rules()

    print("\n" + "#"*80)
    print("# Test Complete")
    print("#"*80 + "\n")
