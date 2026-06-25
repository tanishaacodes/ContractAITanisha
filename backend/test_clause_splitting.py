"""
Test script to verify clause splitting works correctly.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
import django
django.setup()

from api.redline_engine import split_contract_into_clauses

# Sample contract similar to the one in the screenshot
test_contract = """
--- Page 1 ---

CONTRACT AGREEMENT

This agreement is made between Party A and Party B.

--- Page 2 ---

4
LETTER OF INTENT
Inclusions - As noted below:
- Supply & installation of conduits, tray, trunkings
- Any type of civil & builders works, electrical power points

Total Price: Dhs. 3,300,000 (Dirhams Three Million Three Hundred Thousand Only).
Delivered Duty Paid- Excluding VAT

Note: Present unit price based on LME 9000 USD/Ton which will be adjusted during confirmation of order.

5
PAYMENT TERMS
a) 25% of the total price from the date of delivery of materials to the site
b) 5% of the total price after successful testing & commissioning/ energization of busbar and accepted by the Engineer.

6
DELIVERY TERMS
- Delivery Location: To our project site in Dubai
- Delivery Period: No 12 weeks from the date of confirmation of order; actual delivery schedule will be provided along with the order, as per site progress.

7
WARRANTY
Performance Guarantee: A Performance (Security Cheque) for 10% of the total price shall be provided along with first invoice.
"""

def test_splitting():
    print("\n" + "="*80)
    print("CLAUSE SPLITTING TEST")
    print("="*80)

    clauses = split_contract_into_clauses(test_contract)

    print(f"\nTotal clauses found: {len(clauses)}\n")

    for i, clause in enumerate(clauses):
        print(f"\n{'='*60}")
        print(f"Clause {i+1}: {clause['name']} (Index: {clause['index']})")
        print('='*60)
        print(f"Text (first 200 chars):")
        print(clause['text'][:200] + "..." if len(clause['text']) > 200 else clause['text'])
        print(f"\nLength: {len(clause['text'])} characters")

    return clauses

if __name__ == "__main__":
    clauses = test_splitting()

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    if len(clauses) >= 4:
        print("[OK] Successfully split contract into multiple clauses")
        print(f"Found {len(clauses)} clauses")
    else:
        print(f"[WARN] Only found {len(clauses)} clauses, expected more")

    # Check for overly long clauses
    long_clauses = [c for c in clauses if len(c['text']) > 1500]
    if long_clauses:
        print(f"[WARN] Found {len(long_clauses)} clauses longer than 1500 characters")
    else:
        print("[OK] No overly long clauses")
