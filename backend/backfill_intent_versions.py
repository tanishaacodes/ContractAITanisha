"""
Backfill script to link existing intent records to their contract versions.
Links all intents, obligations, and rights to version 1 of their respective contracts.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import ClauseIntent, IntentObligation, IntentRight, ContractVersion, Contract, User
from django.db import transaction

def create_missing_versions():
    """Create version 1 for contracts that don't have any versions"""
    from api.views import create_contract_version_snapshot

    contracts_without_versions = Contract.objects.filter(versions__isnull=True).distinct()
    created_count = 0

    for contract in contracts_without_versions:
        print(f"[CREATE] Creating version 1 for contract {contract.id} - {contract.filename}")
        try:
            # Use the contract's user, or find a system user
            user = contract.user
            create_contract_version_snapshot(contract, user, "Initial version (backfilled)")
            created_count += 1
        except Exception as e:
            print(f"[ERROR] Failed to create version for contract {contract.id}: {e}")

    print(f"\n[OK] Created {created_count} missing contract versions")
    return created_count

def backfill_clause_intents():
    """Link ClauseIntents to their contract versions"""
    clause_intents = ClauseIntent.objects.filter(contract_version__isnull=True).select_related('clause__contract')

    total = clause_intents.count()
    updated = 0
    errors = 0

    print(f"\n[INFO] Processing {total} ClauseIntents...")

    with transaction.atomic():
        for ci in clause_intents:
            try:
                contract = ci.clause.contract
                # Get version 1 for this contract
                version = ContractVersion.objects.filter(contract=contract, version_number=1).first()

                if version:
                    ci.contract_version = version
                    ci.save(update_fields=['contract_version'])
                    updated += 1

                    if updated % 50 == 0:
                        print(f"[OK] Linked {updated}/{total} ClauseIntents...")
                else:
                    print(f"[WARNING] No version 1 found for contract {contract.id}")
                    errors += 1

            except Exception as e:
                print(f"[ERROR] Failed to link ClauseIntent {ci.id}: {e}")
                errors += 1

    print(f"[OK] Linked {updated} ClauseIntents to their contract versions")
    if errors > 0:
        print(f"[WARNING] {errors} ClauseIntents could not be linked")

    return updated, errors

def backfill_intent_obligations():
    """Link IntentObligations to their contract versions"""
    obligations = IntentObligation.objects.filter(contract_version__isnull=True).select_related('clause__contract')

    total = obligations.count()
    updated = 0
    errors = 0

    print(f"\n[INFO] Processing {total} IntentObligations...")

    with transaction.atomic():
        for obl in obligations:
            try:
                contract = obl.clause.contract
                version = ContractVersion.objects.filter(contract=contract, version_number=1).first()

                if version:
                    obl.contract_version = version
                    obl.save(update_fields=['contract_version'])
                    updated += 1

                    if updated % 50 == 0:
                        print(f"[OK] Linked {updated}/{total} IntentObligations...")
                else:
                    print(f"[WARNING] No version 1 found for contract {contract.id}")
                    errors += 1

            except Exception as e:
                print(f"[ERROR] Failed to link IntentObligation {obl.id}: {e}")
                errors += 1

    print(f"[OK] Linked {updated} IntentObligations to their contract versions")
    if errors > 0:
        print(f"[WARNING] {errors} IntentObligations could not be linked")

    return updated, errors

def backfill_intent_rights():
    """Link IntentRights to their contract versions"""
    rights = IntentRight.objects.filter(contract_version__isnull=True).select_related('clause__contract')

    total = rights.count()
    updated = 0
    errors = 0

    print(f"\n[INFO] Processing {total} IntentRights...")

    with transaction.atomic():
        for right in rights:
            try:
                contract = right.clause.contract
                version = ContractVersion.objects.filter(contract=contract, version_number=1).first()

                if version:
                    right.contract_version = version
                    right.save(update_fields=['contract_version'])
                    updated += 1

                    if updated % 50 == 0:
                        print(f"[OK] Linked {updated}/{total} IntentRights...")
                else:
                    print(f"[WARNING] No version 1 found for contract {contract.id}")
                    errors += 1

            except Exception as e:
                print(f"[ERROR] Failed to link IntentRight {right.id}: {e}")
                errors += 1

    print(f"[OK] Linked {updated} IntentRights to their contract versions")
    if errors > 0:
        print(f"[WARNING] {errors} IntentRights could not be linked")

    return updated, errors

def verify_backfill():
    """Verify that all intent records are now linked to versions"""
    unlinked_intents = ClauseIntent.objects.filter(contract_version__isnull=True).count()
    unlinked_obligations = IntentObligation.objects.filter(contract_version__isnull=True).count()
    unlinked_rights = IntentRight.objects.filter(contract_version__isnull=True).count()

    print("\n" + "=" * 60)
    print("Backfill Verification")
    print("=" * 60)

    if unlinked_intents == 0 and unlinked_obligations == 0 and unlinked_rights == 0:
        print("[OK] All intent records successfully linked to versions!")
        print(f"  - ClauseIntents with version: {ClauseIntent.objects.filter(contract_version__isnull=False).count()}")
        print(f"  - IntentObligations with version: {IntentObligation.objects.filter(contract_version__isnull=False).count()}")
        print(f"  - IntentRights with version: {IntentRight.objects.filter(contract_version__isnull=False).count()}")
        return True
    else:
        print("[WARNING] Some records still unlinked:")
        if unlinked_intents > 0:
            print(f"  - ClauseIntents: {unlinked_intents}")
        if unlinked_obligations > 0:
            print(f"  - IntentObligations: {unlinked_obligations}")
        if unlinked_rights > 0:
            print(f"  - IntentRights: {unlinked_rights}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Intent Version Backfill Script")
    print("=" * 60)

    # Step 1: Create missing versions
    print("\nStep 1: Creating missing contract versions...")
    created = create_missing_versions()

    # Step 2: Backfill ClauseIntents
    print("\nStep 2: Backfilling ClauseIntents...")
    ci_updated, ci_errors = backfill_clause_intents()

    # Step 3: Backfill IntentObligations
    print("\nStep 3: Backfilling IntentObligations...")
    obl_updated, obl_errors = backfill_intent_obligations()

    # Step 4: Backfill IntentRights
    print("\nStep 4: Backfilling IntentRights...")
    right_updated, right_errors = backfill_intent_rights()

    # Step 5: Verify
    print("\nStep 5: Verifying backfill...")
    success = verify_backfill()

    # Summary
    print("\n" + "=" * 60)
    print("Backfill Summary")
    print("=" * 60)
    print(f"Contract versions created: {created}")
    print(f"ClauseIntents linked: {ci_updated}")
    print(f"IntentObligations linked: {obl_updated}")
    print(f"IntentRights linked: {right_updated}")
    print(f"Total records linked: {ci_updated + obl_updated + right_updated}")
    print(f"Total errors: {ci_errors + obl_errors + right_errors}")

    if success:
        print("\n[SUCCESS] Backfill completed successfully!")
    else:
        print("\n[WARNING] Backfill completed with warnings. Review output above.")

    print("=" * 60)
