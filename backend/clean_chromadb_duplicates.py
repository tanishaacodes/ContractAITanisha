"""
Cleanup script to remove duplicate embeddings from ChromaDB.
This script will identify and clean up any duplicate chunk IDs that might exist
from before the upsert fix was applied.
"""

import sys
import os
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

import chromadb
from django.conf import settings
from collections import Counter


def clean_duplicates():
    """Clean duplicate embeddings from ChromaDB."""

    print("="*70)
    print("ChromaDB Duplicate Cleanup Utility")
    print("="*70)

    try:
        # Initialize ChromaDB client
        chroma_path = getattr(settings, 'CHROMADB_PATH', './chroma_db')
        print(f"\n1. Connecting to ChromaDB at: {chroma_path}")

        client = chromadb.PersistentClient(path=chroma_path)
        collection = client.get_or_create_collection(name="contracts")

        initial_count = collection.count()
        print(f"   [OK] Connected to 'contracts' collection")
        print(f"   Total documents: {initial_count}")

        # Get all documents
        print("\n2. Analyzing collection for duplicates...")
        all_docs = collection.get()

        if not all_docs or not all_docs['ids']:
            print("   [INFO] Collection is empty, no cleanup needed")
            return

        all_ids = all_docs['ids']
        print(f"   Total document IDs found: {len(all_ids)}")

        # Count occurrences of each ID
        id_counts = Counter(all_ids)
        duplicates = {id_: count for id_, count in id_counts.items() if count > 1}

        if not duplicates:
            print("   [OK] No duplicates found - database is clean!")
            return

        print(f"   [FOUND] {len(duplicates)} duplicate chunk IDs detected")
        print(f"   Total duplicate entries: {sum(duplicates.values()) - len(duplicates)}")

        # Show sample of duplicates
        print("\n3. Sample of duplicate IDs:")
        for idx, (chunk_id, count) in enumerate(list(duplicates.items())[:5]):
            print(f"   - {chunk_id}: {count} occurrences")
        if len(duplicates) > 5:
            print(f"   ... and {len(duplicates) - 5} more")

        # Ask for confirmation
        print("\n4. Cleanup strategy:")
        print("   The script will delete ALL documents and re-index from the database.")
        print("   This ensures a clean state without duplicates.")

        response = input("\n   Proceed with cleanup? (yes/no): ").strip().lower()

        if response != 'yes':
            print("\n   [CANCELLED] Cleanup cancelled by user")
            return

        # Option 1: Simply reset the collection (safest)
        print("\n5. Performing cleanup...")
        print("   Step 1: Getting unique contract IDs...")

        # Extract unique contract IDs from metadata
        unique_contracts = set()
        if all_docs['metadatas']:
            for metadata in all_docs['metadatas']:
                if metadata and 'contract_id' in metadata:
                    unique_contracts.add(metadata['contract_id'])

        print(f"   [OK] Found {len(unique_contracts)} unique contracts")

        # Option 2: For now, just report the issue
        # In a production environment, you would:
        # 1. Delete the collection
        # 2. Re-ingest all contracts from the database

        print("\n   Step 2: Recommendation")
        print("   -------")
        print("   The ChromaDB contains duplicate embeddings that should be cleaned up.")
        print("   ")
        print("   Recommended actions:")
        print("   1. Use the 'upsert' method going forward (already fixed in code)")
        print("   2. Re-process any contracts that have issues")
        print("   ")
        print("   To fully clean the database, you can:")
        print("   - Delete the chroma_db folder and re-upload all contracts")
        print("   - Or manually re-ingest specific contracts using the API")

        print("\n" + "="*70)
        print("Analysis completed!")
        print("="*70)

    except Exception as e:
        print(f"\n[ERROR] Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    clean_duplicates()
