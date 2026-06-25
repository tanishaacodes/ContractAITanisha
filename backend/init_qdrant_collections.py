"""
Initialize Qdrant Collections for Negotiation Intelligence
Creates the required vector collections if they don't exist
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from ai.vectorstore import ensure_collections, get_qdrant_client, get_collection_info
from qdrant_client.http import models as qdrant_models


def check_qdrant_connection():
    """Check if Qdrant is accessible"""
    print("Checking Qdrant connection...")
    try:
        client = get_qdrant_client()
        collections = client.get_collections()
        print(f"  [OK] Connected to Qdrant")
        print(f"  Current collections: {len(collections.collections)}")
        return True
    except Exception as e:
        print(f"  [ERROR] Cannot connect to Qdrant: {e}")
        print("\n  To start Qdrant:")
        print("    docker run -p 6333:6333 qdrant/qdrant")
        print("  Or download from: https://qdrant.tech/documentation/quick-start/")
        return False


def create_collections():
    """Create negotiation intelligence collections"""
    print("\nCreating collections...")
    try:
        ensure_collections()
        print("  [OK] Collections created/verified")
        return True
    except Exception as e:
        print(f"  [ERROR] Error creating collections: {e}")
        return False


def verify_collections():
    """Verify collections are ready"""
    print("\nVerifying collections...")
    collections = ['negotiation_history', 'silent_risk_patterns']

    for collection_name in collections:
        try:
            info = get_collection_info(collection_name)
            print(f"\n  Collection: {collection_name}")
            print(f"    Status: Ready")
            print(f"    Vectors: {info.points_count}")
            print(f"    Vector size: {info.config.params.vectors.size}")
            print(f"    Distance: {info.config.params.vectors.distance}")
        except Exception as e:
            print(f"  [ERROR] Error checking {collection_name}: {e}")


def main():
    """Main execution"""
    print("=" * 60)
    print("QDRANT INITIALIZATION - NEGOTIATION INTELLIGENCE")
    print("=" * 60)

    # Step 1: Check connection
    if not check_qdrant_connection():
        return

    # Step 2: Create collections
    if not create_collections():
        return

    # Step 3: Verify
    verify_collections()

    print("\n" + "=" * 60)
    print("[SUCCESS] Qdrant collections initialized successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Run: python populate_negotiation_data.py")
    print("  2. Start Django: python manage.py runserver")
    print("  3. Access: http://localhost:5173/negotiation-intelligence")
    print("=" * 60)


if __name__ == '__main__':
    main()
