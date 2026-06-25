import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, Clause

# Get all contracts
contracts = Contract.objects.all()

print(f"\n{'='*80}")
print(f"TOTAL CONTRACTS: {contracts.count()}")
print(f"{'='*80}\n")

for contract in contracts[:3]:  # Show only first 3 for brevity
    print(f"\nContract: {contract.original_filename}")
    clauses = Clause.objects.filter(contract=contract, found=True)
    print(f"Clauses found: {clauses.count()}")

    if clauses.exists():
        for clause in clauses:
            print(f"  - {clause.clause_name}")
    else:
        print("  WARNING: NO CLAUSES EXTRACTED!")
    print("-" * 80)

print("\n" + "="*80)
print("SUMMARY: All unique clause types in database")
print("="*80)
all_clause_types = Clause.objects.filter(found=True).values_list('clause_name', flat=True).distinct().order_by('clause_name')
for clause_type in all_clause_types:
    count = Clause.objects.filter(clause_name=clause_type, found=True).count()
    print(f"  {clause_type}: {count} occurrences")
