"""
Simple cleanup - Delete all contracts directly
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.db import connection


def cleanup_all_contracts():
    """Delete all contracts using raw SQL to avoid cascade issues"""
    print("\n" + "="*60)
    print("CLEANUP ALL CONTRACTS")
    print("="*60)

    with connection.cursor() as cursor:
        # Count contracts
        cursor.execute("SELECT COUNT(*) FROM contracts")
        count = cursor.fetchone()[0]
        print(f"\n[INFO] Total contracts in database: {count}")

        if count == 0:
            print("\n[OK] Database is already clean!")
            print("="*60)
            return

        print(f"\n[INFO] Deleting all {count} contracts...")

        # Delete from all related tables first
        tables_to_clean = [
            'alfresco_documents',
            'vector_embeddings',
            'contract_intelligence',
            'contracts'
        ]

        for table in tables_to_clean:
            try:
                cursor.execute(f"DELETE FROM {table}")
                deleted = cursor.rowcount
                print(f"  [OK] Cleaned {table}: {deleted} rows deleted")
            except Exception as e:
                print(f"  [SKIP] {table}: {e}")

        # Verify
        cursor.execute("SELECT COUNT(*) FROM contracts")
        remaining = cursor.fetchone()[0]

        print(f"\n[OK] Contracts remaining: {remaining}")
        print("\n[COMPLETE] Cleanup finished!")
        print("="*60)
        print("\nNext steps:")
        print("  1. Go to http://localhost:5173/alfresco-sync")
        print("  2. Click 'Start Sync' button")
        print("  3. Wait for sync to complete")
        print("  4. Contracts will be imported with full intelligence extraction")
        print("="*60)


if __name__ == '__main__':
    try:
        cleanup_all_contracts()
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
