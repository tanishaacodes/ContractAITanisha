import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract
from api.views import extract_contract_metadata

print("=" * 80)
print("UPDATING CONTRACT DATES")
print("=" * 80)

contracts = Contract.objects.all()
total = contracts.count()
updated = 0

for i, contract in enumerate(contracts, 1):
    print(f"\n[{i}/{total}] Processing: {contract.original_filename}")

    if not contract.full_text:
        print("  [SKIP] No text available")
        continue

    # Extract metadata
    metadata = extract_contract_metadata(contract.full_text)

    if metadata:
        # Update contract fields
        changed = False

        if metadata.get('start_date') and not contract.start_date:
            contract.start_date = metadata['start_date']
            print(f"  [+] Start date: {metadata['start_date']}")
            changed = True

        if metadata.get('end_date') and not contract.end_date:
            contract.end_date = metadata['end_date']
            print(f"  [+] End date: {metadata['end_date']}")
            changed = True

        if metadata.get('party_a') and not contract.party_a:
            contract.party_a = metadata['party_a']
            print(f"  [+] Party A: {metadata['party_a']}")
            changed = True

        if metadata.get('party_b') and not contract.party_b:
            contract.party_b = metadata['party_b']
            print(f"  [+] Party B: {metadata['party_b']}")
            changed = True

        if changed:
            # Update party_name
            if contract.party_a and contract.party_b:
                contract.party_name = f"{contract.party_a} vs {contract.party_b}"
            else:
                contract.party_name = contract.party_a or contract.party_b

            # Update contract_duration
            if contract.start_date and contract.end_date:
                contract.contract_duration = f"{contract.start_date} to {contract.end_date}"

            contract.save()
            updated += 1
            print(f"  [OK] Contract updated!")
        else:
            print(f"  [INFO] No new data extracted")
    else:
        print(f"  [WARN] No metadata extracted")

print("\n" + "=" * 80)
print(f"COMPLETE: Updated {updated} out of {total} contracts")
print("=" * 80)
