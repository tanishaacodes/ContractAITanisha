"""
Keep only the top 5 analyzed contracts and delete the rest
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract


def keep_only_five():
    """Keep only the 5 specified contracts"""
    print("\n" + "="*60)
    print("KEEP ONLY 5 ANALYZED CONTRACTS")
    print("="*60)

    # IDs of the top 5 analyzed contracts
    keep_ids = [
        '0e79f7e7',  # CYBER001 (1).docx
        'f1b73e79',  # DATAP005.docx
        '39d31441',  # DATAP006.docx
        '0e081477',  # tesy.pdf
        'aa586d6d',  # LOI Acknowledgement(1).pdf
    ]

    # Find contracts by partial ID match
    contracts_to_keep = []
    for partial_id in keep_ids:
        contract = Contract.objects.filter(id__startswith=partial_id).first()
        if contract:
            contracts_to_keep.append(contract)
            print(f"[KEEP] {contract.original_filename or contract.filename}")

    print(f"\n[INFO] Will keep {len(contracts_to_keep)} contracts")

    # Get all other contracts
    contracts_to_delete = Contract.objects.exclude(
        id__in=[c.id for c in contracts_to_keep]
    )

    delete_count = contracts_to_delete.count()
    print(f"[WARNING] Will delete {delete_count} contracts")
    print("\n[INFO] Proceeding with deletion...")

    # Delete
    deleted = contracts_to_delete.delete()
    print(f"\n[OK] Deleted {deleted[0]} contracts")

    # Also delete orphaned AlfrescoDocument records
    from core.models import AlfrescoDocument
    orphaned = AlfrescoDocument.objects.filter(contract__isnull=True)
    orphaned_count = orphaned.count()
    if orphaned_count > 0:
        orphaned.delete()
        print(f"[OK] Cleaned up {orphaned_count} orphaned Alfresco records")

    # Verify
    remaining = Contract.objects.count()
    print(f"\n[OK] Remaining contracts: {remaining}")

    print("\n[COMPLETE] Restoration finished!")
    print("="*60)
    print("\nYour 5 analyzed contracts:")
    for idx, contract in enumerate(contracts_to_keep, 1):
        print(f"  {idx}. {contract.original_filename or contract.filename}")
        print(f"     Type: {contract.contract_type}")
        print(f"     Uploaded: {contract.uploaded_at}")
    print("="*60)


if __name__ == '__main__':
    try:
        keep_only_five()
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
