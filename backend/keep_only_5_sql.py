"""
Keep only the top 5 analyzed contracts using raw SQL
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.db import connection
from core.models import Contract


def keep_only_five_sql():
    """Keep only the 5 specified contracts using SQL"""
    print("\n" + "="*60)
    print("KEEP ONLY 5 ANALYZED CONTRACTS (SQL)")
    print("="*60)

    # IDs of the top 5 analyzed contracts
    keep_ids = [
        '0e79f7e7',  # CYBER001 (1).docx
        'f1b73e79',  # DATAP005.docx
        '39d31441',  # DATAP006.docx
        '0e081477',  # tesy.pdf
        'aa586d6d',  # LOI Acknowledgement(1).pdf
    ]

    # Find full UUIDs
    full_ids = []
    for partial_id in keep_ids:
        contract = Contract.objects.filter(id__startswith=partial_id).first()
        if contract:
            full_ids.append(str(contract.id))
            print(f"[KEEP] {contract.original_filename or contract.filename}")

    print(f"\n[INFO] Will keep {len(full_ids)} contracts")

    if len(full_ids) != 5:
        print("[ERROR] Could not find all 5 contracts!")
        return

    # Delete using raw SQL in correct order
    with connection.cursor() as cursor:
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM contracts")
        before_count = cursor.fetchone()[0]
        print(f"[INFO] Contracts before deletion: {before_count}")

        # Prepare the NOT IN clause
        ids_str = "', '".join(full_ids)
        not_in_clause = f"('{ids_str}')"

        print(f"\n[INFO] Deleting contracts not in: {not_in_clause}")

        # Delete from related tables first
        tables = [
            'alfresco_documents',
            'vector_embeddings',
            'contract_intelligence',
        ]

        for table in tables:
            try:
                sql = f"DELETE FROM {table} WHERE contractId NOT IN {not_in_clause}"
                cursor.execute(sql)
                deleted = cursor.rowcount
                print(f"  [OK] Deleted {deleted} rows from {table}")
            except Exception as e:
                print(f"  [SKIP] {table}: {e}")

        # Finally delete contracts
        try:
            sql = f"DELETE FROM contracts WHERE id NOT IN {not_in_clause}"
            cursor.execute(sql)
            deleted = cursor.rowcount
            print(f"  [OK] Deleted {deleted} contracts")
        except Exception as e:
            print(f"  [ERROR] Failed to delete contracts: {e}")
            return

        # Get count after deletion
        cursor.execute("SELECT COUNT(*) FROM contracts")
        after_count = cursor.fetchone()[0]

        print(f"\n[OK] Contracts after deletion: {after_count}")

    print("\n[COMPLETE] Restoration finished!")
    print("="*60)
    print("\nYour 5 analyzed contracts:")

    remaining = Contract.objects.all().order_by('uploaded_at')
    for idx, contract in enumerate(remaining, 1):
        print(f"  {idx}. {contract.original_filename or contract.filename}")
        print(f"     Type: {contract.contract_type}")
        print(f"     Uploaded: {contract.uploaded_at}")

    print("="*60)


if __name__ == '__main__':
    try:
        keep_only_five_sql()
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
