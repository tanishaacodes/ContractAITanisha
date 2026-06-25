"""
Test Script for Alfresco Integration & RAG System

Tests:
1. Alfresco connection
2. RAG engine initialization
3. Document ingestion
4. Clause extraction
5. Semantic search
6. End-to-end workflow
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from api.alfresco_service import AlfrescoExtractor
from api.rag_engine import ContractRAG
from core.models import Contract, ContractIntelligence, VectorEmbedding, AlfrescoDocument
from django.contrib.auth import get_user_model
import json

User = get_user_model()


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def test_alfresco_connection():
    """Test 1: Alfresco Connection"""
    print_header("TEST 1: Alfresco Connection")

    try:
        extractor = AlfrescoExtractor()
        health = extractor.health_check()

        print(f"Status: {health['status']}")
        print(f"Method: {health['method']}")
        print(f"Message: {health['message']}")

        if health['status'] == 'healthy':
            print("✓ Alfresco connection successful!")
            return True
        else:
            print("✗ Alfresco connection failed!")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_rag_initialization():
    """Test 2: RAG Engine Initialization"""
    print_header("TEST 2: RAG Engine Initialization")

    try:
        # Test with Ollama (local)
        print("\nInitializing RAG with Ollama...")
        rag_ollama = ContractRAG(use_openai=False)
        print("✓ Ollama RAG initialized successfully!")
        print(f"  Embedding model: {rag_ollama.embedding_model_name}")
        print(f"  Vector DB collection size: {rag_ollama.collection.count()}")

        # Test with OpenAI (if configured)
        if os.getenv('OPENAI_API_KEY'):
            print("\nInitializing RAG with OpenAI...")
            rag_openai = ContractRAG(use_openai=True)
            print("✓ OpenAI RAG initialized successfully!")
        else:
            print("\n⚠ OpenAI API key not configured, skipping OpenAI test")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_document_ingestion():
    """Test 3: Document Ingestion"""
    print_header("TEST 3: Document Ingestion to Vector DB")

    sample_contract = """
    AGREEMENT

    This Agreement is made between Acme Corporation ("Party A") and Widget Industries ("Party B").

    1. TERMINATION
    Either party may terminate this Agreement by providing thirty (30) days written notice to the other party.

    2. LIABILITY
    The total liability of either party under this Agreement shall not exceed the total fees paid in the preceding twelve (12) months.

    3. GOVERNING LAW
    This Agreement shall be governed by the laws of the State of Delaware, USA.

    4. CONFIDENTIALITY
    All confidential information must be kept confidential for a period of five (5) years from the date of disclosure.

    5. PAYMENT TERMS
    Payment is due NET 30 days upon receipt of invoice.
    """

    try:
        rag = ContractRAG(use_openai=False)

        print("\nIngesting sample contract...")
        result = rag.ingest_contract(
            contract_id="test-contract-001",
            text=sample_contract,
            metadata={
                "filename": "test_contract.txt",
                "test": True
            }
        )

        print(f"Status: {result['status']}")
        print(f"Chunks created: {result.get('chunks_created', 0)}")

        if result['status'] == 'success':
            print("✓ Document ingested successfully!")
            return True
        else:
            print("✗ Document ingestion failed!")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_clause_extraction():
    """Test 4: Legal Clause Extraction"""
    print_header("TEST 4: Legal Clause Extraction")

    sample_contract = """
    AGREEMENT

    This Agreement is made between Acme Corporation ("Party A") and Widget Industries ("Party B").

    1. TERMINATION
    Either party may terminate this Agreement by providing thirty (30) days written notice to the other party.

    2. LIABILITY
    The total liability of either party under this Agreement shall not exceed the total fees paid in the preceding twelve (12) months.

    3. GOVERNING LAW
    This Agreement shall be governed by the laws of the State of Delaware, USA.

    4. CONFIDENTIALITY
    All confidential information must be kept confidential for a period of five (5) years from the date of disclosure.

    5. PAYMENT TERMS
    Payment is due NET 30 days upon receipt of invoice.
    """

    try:
        rag = ContractRAG(use_openai=False)

        print("\nExtracting clauses from sample contract...")
        result = rag.extract_clauses(
            contract_id="test-contract-001",
            contract_text=sample_contract
        )

        print(f"\nStatus: {result['status']}")

        if result['status'] == 'success':
            extracted = result['extracted_data']
            print("\nExtracted Intelligence:")
            print(f"  Parties: {extracted.get('parties', 'N/A')}")
            print(f"  Termination: {extracted.get('termination', {}).get('summary', 'N/A')}")
            print(f"  Liability: {extracted.get('liability', 'N/A')}")
            print(f"  Jurisdiction: {extracted.get('jurisdiction', 'N/A')}")
            print(f"  Confidentiality: {extracted.get('confidentiality_duration', 'N/A')}")
            print(f"  Payment Terms: {extracted.get('payment_terms', 'N/A')}")

            print("\n✓ Clause extraction successful!")
            return True
        else:
            print(f"✗ Clause extraction failed: {result.get('error')}")
            if 'raw_response' in result:
                print(f"\nRaw response: {result['raw_response'][:500]}")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_semantic_search():
    """Test 5: Semantic Search"""
    print_header("TEST 5: Semantic Search")

    try:
        rag = ContractRAG(use_openai=False)

        # Search for termination clauses
        print("\nSearching for: 'termination clauses and notice period'")
        results = rag.semantic_search(
            query="termination clauses and notice period",
            k=3
        )

        print(f"\nFound {len(results)} results:")
        for idx, result in enumerate(results, 1):
            print(f"\n{idx}. Relevance: {1 - result['distance']:.2f}")
            print(f"   Text: {result['text'][:150]}...")
            print(f"   Contract: {result['metadata'].get('contract_id', 'N/A')}")

        if results:
            print("\n✓ Semantic search successful!")
            return True
        else:
            print("\n⚠ No results found (may need to ingest documents first)")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_qa():
    """Test 6: RAG Q&A"""
    print_header("TEST 6: RAG Question Answering")

    try:
        rag = ContractRAG(use_openai=False)

        question = "What is the notice period for termination?"
        print(f"\nQuestion: {question}")
        print("Generating answer...")

        answer = rag.query_contracts(user_query=question)

        print(f"\nAnswer: {answer}")

        if answer and not answer.startswith("Error"):
            print("\n✓ RAG Q&A successful!")
            return True
        else:
            print("\n✗ RAG Q&A failed!")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_models():
    """Test 7: Database Models"""
    print_header("TEST 7: Database Models")

    try:
        # Count existing records
        alfresco_count = AlfrescoDocument.objects.count()
        intelligence_count = ContractIntelligence.objects.count()
        embedding_count = VectorEmbedding.objects.count()

        print(f"\nDatabase Statistics:")
        print(f"  AlfrescoDocuments: {alfresco_count}")
        print(f"  ContractIntelligence: {intelligence_count}")
        print(f"  VectorEmbeddings: {embedding_count}")

        print("\n✓ Database models accessible!")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_test_data():
    """Cleanup Test Data"""
    print_header("CLEANUP: Removing Test Data")

    try:
        rag = ContractRAG(use_openai=False)

        # Delete test contract from vector DB
        deleted = rag.delete_contract("test-contract-001")

        if deleted:
            print("✓ Test data cleaned up successfully!")
        else:
            print("⚠ No test data found to clean up")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "ALFRESCO & RAG SYSTEM TEST SUITE" + " "*16 + "║")
    print("╚" + "="*58 + "╝")

    tests = [
        ("Alfresco Connection", test_alfresco_connection),
        ("RAG Initialization", test_rag_initialization),
        ("Document Ingestion", test_document_ingestion),
        ("Clause Extraction", test_clause_extraction),
        ("Semantic Search", test_semantic_search),
        ("RAG Q&A", test_rag_qa),
        ("Database Models", test_database_models),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ CRITICAL ERROR in {name}: {e}")
            results.append((name, False))

    # Cleanup
    cleanup_test_data()

    # Summary
    print_header("TEST SUMMARY")
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print(f"\nResults: {passed_count}/{total_count} tests passed\n")

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status} - {name}")

    print("\n" + "="*60 + "\n")

    if passed_count == total_count:
        print("🎉 All tests passed! System is ready to use.")
        return 0
    else:
        print(f"⚠ {total_count - passed_count} test(s) failed. Review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
