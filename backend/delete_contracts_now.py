import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract

# Contracts to keep - updated keywords to match actual filenames
KEEP_KEYWORDS = [
    'High_Risk_Construction',
    'SOFTWARE_DEVELOPMENT',
    'MANUFACTURING',
    'EXCLUSIVE_DISTRIBUTION',
    'COMMERCIAL_LEASE'
]

all_contracts = Contract.objects.all()
print(f"Total contracts: {all_contracts.count()}")

# Separate contracts
to_keep = []
to_delete = []

for contract in all_contracts:
    name = contract.filename or contract.title or str(contract.id)
    should_keep = any(kw in name for kw in KEEP_KEYWORDS)

    if should_keep:
        to_keep.append((contract.id, name))
    else:
        to_delete.append((contract.id, name))

print(f"\nKeeping {len(to_keep)} contracts:")
for cid, name in to_keep:
    print(f"  KEEP: {name}")

print(f"\nDeleting {len(to_delete)} contracts:")
for cid, name in to_delete:
    print(f"  DELETE: {name}")

if to_delete:
    deleted_ids = [cid for cid, _ in to_delete]
    deleted_count = Contract.objects.filter(id__in=deleted_ids).delete()[0]
    print(f"\nSuccessfully deleted {deleted_count} contracts!")
    print(f"Remaining: {Contract.objects.count()} contracts")
else:
    print("\nNo contracts to delete!")
