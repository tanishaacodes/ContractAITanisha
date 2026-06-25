"""
Backfill script to create version 1 for all existing contracts
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, ContractVersion

print("=" * 60)
print("BACKFILL VERSION HISTORY FOR EXISTING CONTRACTS")
print("=" * 60)

# Get all contracts that don't have any versions
contracts = Contract.objects.all()
total_contracts = contracts.count()
backfilled = 0

print(f"\n[INFO] Found {total_contracts} total contracts")

for contract in contracts:
    # Check if this contract already has version 1
    existing_version = ContractVersion.objects.filter(contract=contract, version_number=1).first()

    if existing_version:
        print(f"[SKIP] Contract {contract.original_filename} already has version 1")
        continue

    # Create version 1 for this contract
    try:
        ContractVersion.objects.create(
            contract=contract,
            version_number=1,
            created_by=contract.user,
            change_description="Initial version (backfilled)",
            filename=contract.filename,
            original_filename=contract.original_filename,
            file_type=contract.file_type,
            file_path=contract.file_path,
            full_text=contract.full_text,
            contract_type=contract.contract_type,
            contract_value=contract.contract_value,
            party_name=contract.party_name,
            contract_duration=contract.contract_duration
        )
        backfilled += 1
        print(f"[OK] Created version 1 for: {contract.original_filename}")
    except Exception as e:
        print(f"[ERROR] Failed to create version for {contract.original_filename}: {e}")

print("\n" + "=" * 60)
print(f"COMPLETE: Backfilled {backfilled} contracts")
print("=" * 60)
