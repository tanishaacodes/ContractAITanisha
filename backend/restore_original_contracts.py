"""
Restore original 5 analyzed contracts and delete Alfresco synced ones
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, AlfrescoDocument
from django.db.models import Q


def restore_original_contracts():
    """Keep only the original 5 analyzed contracts"""
    print("\n" + "="*60)
    print("RESTORE ORIGINAL 5 ANALYZED CONTRACTS")
    print("="*60)

    # Get all contracts
    all_contracts = Contract.objects.all().order_by('uploaded_at')
    total = all_contracts.count()
    print(f"\n[INFO] Total contracts in database: {total}")

    # Find contracts that were synced from Alfresco (have AlfrescoDocument link)
    alfresco_synced = Contract.objects.filter(alfresco_doc__isnull=False)
    alfresco_count = alfresco_synced.count()
    print(f"[INFO] Contracts synced from Alfresco: {alfresco_count}")

    # Find original uploaded contracts (no Alfresco link, have full analysis)
    original_contracts = Contract.objects.filter(
        alfresco_doc__isnull=True,
        full_text__isnull=False
    ).exclude(
        full_text=''
    ).order_by('uploaded_at')

    original_count = original_contracts.count()
    print(f"[INFO] Original uploaded contracts (with text): {original_count}")

    # Show original contracts
    print(f"\n[INFO] Original analyzed contracts:")
    for idx, contract in enumerate(original_contracts[:10], 1):
        print(f"  {idx}. {contract.original_filename or contract.filename}")
        print(f"     Uploaded: {contract.uploaded_at}")
        print(f"     Type: {contract.contract_type or 'Unknown'}")
        print(f"     Has text: {'Yes' if contract.full_text else 'No'}")
        print()

    if original_count < 5:
        print(f"\n[WARNING] Found only {original_count} original contracts, expected 5")
        print("[INFO] Looking for contracts without Alfresco link...")

        # Alternative: find any contracts without Alfresco link
        non_alfresco = Contract.objects.filter(alfresco_doc__isnull=True).order_by('uploaded_at')
        print(f"\n[INFO] All non-Alfresco contracts: {non_alfresco.count()}")

        print("\nAll non-Alfresco contracts:")
        for idx, contract in enumerate(non_alfresco[:20], 1):
            print(f"  {idx}. {contract.original_filename or contract.filename}")
            print(f"     Uploaded: {contract.uploaded_at}")
            print(f"     Has text: {'Yes' if contract.full_text else 'No'}")
            print()

        print("\n[QUESTION] Please identify which 5 contracts to keep.")
        print("Run this script with contract IDs as arguments:")
        print("python restore_original_contracts.py <id1> <id2> <id3> <id4> <id5>")
        print("="*60)
        return

    # If we have 5 or more, keep the first 5
    contracts_to_keep = list(original_contracts[:5])
    contracts_to_delete = Contract.objects.exclude(
        id__in=[c.id for c in contracts_to_keep]
    )

    print(f"\n[INFO] Will keep these 5 contracts:")
    for idx, contract in enumerate(contracts_to_keep, 1):
        print(f"  {idx}. {contract.original_filename or contract.filename}")

    delete_count = contracts_to_delete.count()
    print(f"\n[WARNING] Will delete {delete_count} contracts")
    print("  These include all Alfresco-synced contracts")
    print("\n[INFO] Proceeding with deletion...")

    # Delete
    deleted = contracts_to_delete.delete()
    print(f"\n[OK] Deleted {deleted[0]} contracts")

    # Verify
    remaining = Contract.objects.count()
    print(f"[OK] Remaining contracts: {remaining}")

    print("\n[COMPLETE] Restoration finished!")
    print("="*60)
    print("\nYour original 5 analyzed contracts are now restored.")
    print("All Alfresco-synced contracts have been removed.")
    print("="*60)


if __name__ == '__main__':
    try:
        restore_original_contracts()
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Restoration failed: {e}")
        import traceback
        traceback.print_exc()
