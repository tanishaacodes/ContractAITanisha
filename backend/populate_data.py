"""
Populate test data for Contract Intelligence Maps
Run with: python manage.py shell < populate_data.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract
from django.db.models import Q
import random

# Get all contracts that need updating
contracts = Contract.objects.filter(
    Q(business_unit__isnull=True) | Q(business_unit='') | Q(total_liability=0) | Q(total_liability__isnull=True)
)

print(f"Found {contracts.count()} contracts to update")

# Business units to assign
business_units = ['EPC', 'Oil & Gas', 'Defense', 'IT Services', 'Manufacturing']

# Update each contract
updated_count = 0
for idx, contract in enumerate(contracts):
    # Assign business unit in round-robin fashion
    bu = business_units[idx % len(business_units)]

    # Generate random values
    total_liability = random.uniform(100000, 2100000)

    # Set contract value if empty
    if not contract.contract_value or contract.contract_value == '':
        contract.contract_value = str(int(random.uniform(500000, 5500000)))

    # Update fields
    contract.business_unit = bu
    contract.version = 1
    contract.total_liability = total_liability
    contract.save()

    updated_count += 1
    if updated_count % 10 == 0:
        print(f"Updated {updated_count} contracts...")

print(f"\n✅ Successfully updated {updated_count} contracts!")

# Show summary by business unit
print("\nBusiness Unit Summary:")
for bu in business_units:
    count = Contract.objects.filter(business_unit=bu).count()
    avg_liability = Contract.objects.filter(business_unit=bu).aggregate(
        avg=django.db.models.Avg('total_liability')
    )['avg']
    print(f"  {bu}: {count} contracts, Avg Liability: ${avg_liability:,.2f}" if avg_liability else f"  {bu}: {count} contracts")

# Show sample data
print("\nSample contracts:")
samples = Contract.objects.filter(business_unit__isnull=False)[:5]
for contract in samples:
    print(f"  ID: {contract.id[:8]}... | {contract.business_unit} | Value: ${contract.contract_value} | Liability: ${contract.total_liability:,.2f}")

print("\n🚀 Data is ready! Refresh your browser at /contract-maps")
