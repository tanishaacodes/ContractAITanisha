"""
Check for contracts with no clauses
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, Clause

contracts = Contract.objects.all()
empty_contracts = []

for c in contracts:
    clause_count = Clause.objects.filter(contract_id=c.id).count()
    if clause_count == 0:
        empty_contracts.append(c.filename)

print(f"Total contracts: {contracts.count()}")
print(f"Contracts without clauses: {len(empty_contracts)}")

if empty_contracts:
    print("\nContracts with no clauses:")
    for filename in empty_contracts[:10]:  # Show first 10
        print(f"  - {filename}")
    if len(empty_contracts) > 10:
        print(f"  ... and {len(empty_contracts) - 10} more")
