"""
Clean up contracts imported via import_from_alfresco.py
Removes contracts that don't have AlfrescoDocument entries so they can be re-synced properly
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, AlfrescoDocument


def cleanup_imported_contracts():
    """Remove contracts without AlfrescoDocument entries"""
    print("\n" + "="*60)
    print("CLEANUP IMPORTED CONTRACTS")
    print("="*60)

    # Find all contracts
    print("\n[1/3] Analyzing contracts...")
    all_contracts = Contract.objects.all()
    total_count = all_contracts.count()
    print(f"  [INFO] Total contracts in database: {total_count}")

    # Find contracts WITH Alfresco links (we keep these)
    contracts_with_alfresco = Contract.objects.filter(
        alfresco_doc__isnull=False
    ).distinct()
    linked_count = contracts_with_alfresco.count()
    print(f"  [INFO] Contracts linked to Alfresco: {linked_count}")

    # Find contracts WITHOUT Alfresco links (imported via script)
    contracts_without_alfresco = Contract.objects.filter(
        alfresco_doc__isnull=True
    )
    unlinked_count = contracts_without_alfresco.count()
    print(f"  [INFO] Contracts without Alfresco link: {unlinked_count}")

    if unlinked_count == 0:
        print("\n[OK] No cleanup needed! All contracts are properly linked.")
        print("="*60)
        return

    # Show sample of contracts to be deleted
    print("\n[2/3] Contracts to be removed (sample):")
    sample = contracts_without_alfresco[:5]
    for contract in sample:
        print(f"  - {contract.original_filename or contract.filename} (ID: {str(contract.id)[:8]}...)")

    if unlinked_count > 5:
        print(f"  ... and {unlinked_count - 5} more")

    # Confirm deletion
    print(f"\n[WARNING] This will delete {unlinked_count} contracts!")
    print("  These contracts were imported via import_from_alfresco.py")
    print("  After deletion, you can re-sync from Alfresco frontend with full intelligence extraction")
    print("\n  [INFO] Auto-proceeding with cleanup...")

    # Delete unlinked contracts
    print("\n[3/3] Deleting unlinked contracts...")
    deleted_count, _ = contracts_without_alfresco.delete()

    # Verify
    remaining = Contract.objects.count()

    print(f"  [OK] Deleted {deleted_count} contracts")
    print(f"  [OK] Remaining contracts: {remaining}")

    print("\n[COMPLETE] Cleanup finished!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Go to http://localhost:5173/alfresco-sync")
    print("  2. Click 'Start Sync' button")
    print("  3. Wait for sync to complete (will show progress)")
    print("  4. Contracts will be imported with:")
    print("     - Full text extraction")
    print("     - Vector embeddings")
    print("     - Legal intelligence (parties, clauses, etc.)")
    print("     - Proper Alfresco linking")
    print("="*60)


if __name__ == '__main__':
    try:
        cleanup_imported_contracts()
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
