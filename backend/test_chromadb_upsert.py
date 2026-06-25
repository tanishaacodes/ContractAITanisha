"""
Test script to verify ChromaDB upsert functionality.
This ensures that re-uploading contracts doesn't cause duplicate ID errors.
"""

import sys
import os
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from api.rag_engine import ContractRAG


def test_upsert():
    """Test that we can upsert the same contract multiple times without errors."""

    print("="*60)
    print("Testing ChromaDB Upsert Functionality")
    print("="*60)

    # Initialize RAG engine
    print("\n1. Initializing RAG engine...")
    rag = ContractRAG(use_openai=False)
    print("   [OK] RAG engine initialized")

    # Test contract data
    test_contract_id = "test_contract_upsert_001"
    test_text = """
    SERVICE AGREEMENT

    This Service Agreement ("Agreement") is entered into on January 1, 2024,
    between Company A ("Client") and Company B ("Service Provider").

    1. SERVICES
    The Service Provider agrees to provide consulting services to the Client.

    2. PAYMENT TERMS
    Payment shall be made within 30 days of invoice date.
    The total fee is $10,000 USD.

    3. TERMINATION
    Either party may terminate this agreement with 30 days written notice.

    4. CONFIDENTIALITY
    All information shared shall remain confidential.
    """

    # First ingestion
    print(f"\n2. First ingestion of contract {test_contract_id}...")
    result1 = rag.ingest_contract(
        contract_id=test_contract_id,
        text=test_text,
        metadata={"version": "1", "test": True}
    )
    print(f"   [OK] First ingestion: {result1['chunks_created']} chunks created")
    print(f"   Status: {result1['status']}")

    # Get stats after first ingestion
    stats1 = rag.get_contract_stats(test_contract_id)
    print(f"   Chunks in DB: {stats1['chunk_count']}")

    # Second ingestion (should upsert, not error)
    print(f"\n3. Second ingestion of same contract (testing upsert)...")
    result2 = rag.ingest_contract(
        contract_id=test_contract_id,
        text=test_text,
        metadata={"version": "2", "test": True}
    )
    print(f"   [OK] Second ingestion: {result2['chunks_created']} chunks created")
    print(f"   Status: {result2['status']}")

    # Get stats after second ingestion
    stats2 = rag.get_contract_stats(test_contract_id)
    print(f"   Chunks in DB: {stats2['chunk_count']}")

    # Verify no duplicates were created
    if stats1['chunk_count'] == stats2['chunk_count']:
        print("\n   [SUCCESS] Upsert working correctly - no duplicates created!")
    else:
        print(f"\n   [WARNING] Chunk count changed from {stats1['chunk_count']} to {stats2['chunk_count']}")

    # Third ingestion with modified text
    modified_text = test_text + "\n\n5. GOVERNING LAW\nThis agreement is governed by the laws of California."
    print(f"\n4. Third ingestion with modified text...")
    result3 = rag.ingest_contract(
        contract_id=test_contract_id,
        text=modified_text,
        metadata={"version": "3", "test": True}
    )
    print(f"   [OK] Third ingestion: {result3['chunks_created']} chunks created")
    print(f"   Status: {result3['status']}")

    stats3 = rag.get_contract_stats(test_contract_id)
    print(f"   Chunks in DB: {stats3['chunk_count']}")

    # Test semantic search
    print(f"\n5. Testing semantic search...")
    results = rag.semantic_search(
        query="payment terms",
        contract_id=test_contract_id,
        k=3
    )
    print(f"   [OK] Found {len(results)} relevant chunks")
    if results:
        print(f"   Top result preview: {results[0]['text'][:100]}...")

    # Cleanup
    print(f"\n6. Cleaning up test data...")
    deleted = rag.delete_contract(test_contract_id)
    if deleted:
        print(f"   [OK] Test contract deleted")

    print("\n" + "="*60)
    print("Test completed successfully!")
    print("="*60)


if __name__ == "__main__":
    try:
        test_upsert()
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
