import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract
from api.risk_scoring_model import risk_scoring_algorithm

# Get the LOI contract
contract = Contract.objects.get(id='60696462-71bc-4390-9d70-c49677864b0c')

print("=" * 80)
print("LOI CONTRACT RISK SCORING DEBUG")
print("=" * 80)
print(f"Contract: {contract.original_filename}")
print(f"Text length: {len(contract.full_text)} characters")
print()

# Run risk scoring
result = risk_scoring_algorithm(contract.full_text)

print(f"Total Risk Score: {result['total_risk_score']}/100")
print(f"Risk Level: {result['risk_level']}")
print()

print("CATEGORIES WITH SCORES > 0:")
print("-" * 80)
for category, score in result['category_breakdown'].items():
    if score > 0:
        details = result['detailed_breakdown'][category]
        print(f"\n{details['display_name']}: {score}/5")
        print(f"  Keywords found: {details['found_keywords']}")
        print(f"  Total keyword hits: {details['keyword_hits']}")

print("\n" + "=" * 80)

# Sample some text to see what we're working with
print("\nSAMPLE TEXT (first 1000 chars):")
print("-" * 80)
print(contract.full_text[:1000])
print("\n" + "=" * 80)
