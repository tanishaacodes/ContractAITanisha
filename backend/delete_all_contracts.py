"""
Django script to delete ALL contracts from the system
Run with: python delete_all_contracts.py --force
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract

print("=" * 60)
print("DELETE ALL CONTRACTS")
print("=" * 60)

# Check for --force flag
force_delete = '--force' in sys.argv

try:
    # Get all contracts
    print(f"\n[1] Finding all contracts...")
    total = Contract.objects.count()
    print(f"[INFO] Found {total} contracts in database")

    if total == 0:
        print("[INFO] No contracts to delete.")
    else:
        # Show sample contracts
        print(f"\n[2] Sample contracts (showing first 10):")
        for i, contract in enumerate(Contract.objects.all()[:10], 1):
            print(f"  {i}. {contract.original_filename} (User: {contract.user.email})")
        if total > 10:
            print(f"  ... and {total - 10} more")

        # Confirm deletion
        if force_delete:
            print(f"\n[INFO] Force flag detected. Proceeding with deletion...")
            proceed = True
        else:
            print(f"\n[WARNING] This will delete ALL {total} contracts and related data!")
            confirm = input("Type 'DELETE ALL' to confirm: ")
            proceed = confirm == 'DELETE ALL'

        if proceed:
            # Delete all contracts (CASCADE will handle related records)
            print(f"\n[3] Deleting {total} contracts...")
            deleted_count, details = Contract.objects.all().delete()

            print("\n" + "=" * 60)
            print("DELETION SUMMARY")
            print("=" * 60)
            print(f"Total database records deleted: {deleted_count}")
            print("\nBreakdown by model:")
            for model, count in details.items():
                print(f"  - {model}: {count}")
            print("=" * 60)

            # Delete uploaded files
            uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
            if os.path.exists(uploads_dir):
                print(f"\n[4] Cleaning uploads directory...")
                files = [f for f in os.listdir(uploads_dir) if os.path.isfile(os.path.join(uploads_dir, f))]
                file_count = len(files)

                if file_count > 0:
                    for filename in files:
                        file_path = os.path.join(uploads_dir, filename)
                        os.remove(file_path)
                    print(f"[SUCCESS] Deleted {file_count} uploaded files")
                else:
                    print("[INFO] No uploaded files to delete")

            print("\n[SUCCESS] All contracts have been deleted!")
        else:
            print("[CANCELLED] Deletion cancelled. No changes made.")

except Exception as e:
    print(f"[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
