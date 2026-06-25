#!/usr/bin/env python3
"""Check contracts in database and Qdrant"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, User

print("\n" + "="*60)
print("CONTRACTS IN DATABASE")
print("="*60)

total_contracts = Contract.objects.count()
print(f"Total contracts in database: {total_contracts}")

if total_contracts > 0:
    # Show contracts by user
    for user in User.objects.all():
        user_contracts = Contract.objects.filter(user=user)
        if user_contracts.exists():
            print(f"\nUser: {user.email}")
            print(f"  Contracts: {user_contracts.count()}")
            for contract in user_contracts[:5]:
                print(f"    - {contract.original_filename} (ID: {contract.id})")
else:
    print("No contracts found in database!")

# Check Qdrant
print("\n" + "="*60)
print("CHECKING QDRANT VECTOR DATABASE")
print("="*60)

try:
    from qdrant_client import QdrantClient

    QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
    COLLECTION = os.environ.get("QDRANT_COLLECTION", "contracts")

    client = QdrantClient(url=QDRANT_URL)

    # Check if collection exists
    collections = client.get_collections()
    collection_names = [c.name for c in collections.collections]

    print(f"Qdrant URL: {QDRANT_URL}")
    print(f"Collections: {collection_names}")

    if COLLECTION in collection_names:
        # Get collection info
        collection_info = client.get_collection(COLLECTION)
        print(f"\nCollection '{COLLECTION}' exists!")
        print(f"  Total vectors: {collection_info.points_count}")
        print(f"  Vector size: {collection_info.config.params.vectors.size}")

        if collection_info.points_count == 0:
            print("\n⚠️  WARNING: Collection exists but has NO VECTORS!")
            print("Your contracts need to be ingested into Qdrant.")
    else:
        print(f"\n⚠️  Collection '{COLLECTION}' does NOT exist!")
        print("You need to create the collection and ingest contracts.")

except Exception as e:
    print(f"\n❌ Error connecting to Qdrant: {e}")
    print("Make sure Qdrant is running on localhost:6333")
    print("Run: docker run -p 6333:6333 qdrant/qdrant")

print("\n" + "="*60 + "\n")
