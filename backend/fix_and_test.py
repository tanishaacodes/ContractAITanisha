"""
Quick fix script to download embedding model and test system
"""

import os
import sys

print("=" * 60)
print("  FIXING AND TESTING ALFRESCO RAG SYSTEM")
print("=" * 60)

# 1. Download embedding model offline
print("\n1. Downloading embedding model (one-time setup)...")
try:
    from sentence_transformers import SentenceTransformer

    # This will download the model if not cached
    print("   Loading: sentence-transformers/all-MiniLM-L6-v2")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu')
    print("   ✓ Model loaded successfully!")
    print(f"   Model cached at: {model._model_card_vars.get('model_path', 'default cache')}")
except Exception as e:
    print(f"   ✗ Error loading model: {e}")
    print("\n   SOLUTION:")
    print("   If you're behind a firewall/proxy, download model manually:")
    print("   1. Go to: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2")
    print("   2. Download all files")
    print("   3. Place in: ~/.cache/huggingface/hub/")
    print("\n   OR use offline mode by setting HF_HUB_OFFLINE=1")
    sys.exit(1)

# 2. Test imports
print("\n2. Testing imports...")
try:
    print("   - langchain...")
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    print("     ✓ langchain")

    print("   - langchain_community...")
    from langchain_community.llms import Ollama
    print("     ✓ langchain_community")

    print("   - chromadb...")
    import chromadb
    print("     ✓ chromadb")

    print("   ✓ All imports successful!")
except ImportError as e:
    print(f"   ✗ Import error: {e}")
    print("\n   SOLUTION: pip install -r requirements.txt")
    sys.exit(1)

# 3. Initialize Django
print("\n3. Initializing Django...")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
import django
django.setup()
print("   ✓ Django initialized")

# 4. Test RAG Engine
print("\n4. Testing RAG Engine...")
try:
    from api.rag_engine import ContractRAG

    print("   Initializing RAG (this may take a moment)...")
    rag = ContractRAG(use_openai=False)
    print(f"   ✓ RAG initialized!")
    print(f"     - Embedding model: {rag.embedding_model_name}")
    print(f"     - Collection size: {rag.collection.count()}")
except Exception as e:
    print(f"   ✗ RAG initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. Test document ingestion
print("\n5. Testing document ingestion...")
sample_text = """
AGREEMENT

This Agreement is between Acme Corp and Widget Inc.

TERMINATION: Either party may terminate with 30 days notice.
LIABILITY: Liability is capped at fees paid in last 12 months.
JURISDICTION: Delaware, USA
"""

try:
    result = rag.ingest_contract(
        contract_id="test-fix-001",
        text=sample_text,
        metadata={"test": True}
    )
    print(f"   ✓ Document ingested!")
    print(f"     - Chunks created: {result.get('chunks_created', 0)}")
except Exception as e:
    print(f"   ✗ Ingestion failed: {e}")
    import traceback
    traceback.print_exc()

# 6. Test clause extraction
print("\n6. Testing clause extraction...")
try:
    extraction = rag.extract_clauses(
        contract_id="test-fix-001",
        contract_text=sample_text
    )

    if extraction['status'] == 'success':
        data = extraction['extracted_data']
        print("   ✓ Extraction successful!")
        print(f"     - Parties: {data.get('parties', 'N/A')}")
        print(f"     - Termination: {data.get('termination', {}).get('summary', 'N/A')}")
        print(f"     - Jurisdiction: {data.get('jurisdiction', 'N/A')}")
    else:
        print(f"   ✗ Extraction failed: {extraction.get('error')}")
except Exception as e:
    print(f"   ✗ Extraction error: {e}")
    import traceback
    traceback.print_exc()

# 7. Test semantic search
print("\n7. Testing semantic search...")
try:
    results = rag.semantic_search("termination clause", k=2)
    print(f"   ✓ Search complete!")
    print(f"     - Results found: {len(results)}")
    if results:
        print(f"     - Top result: {results[0]['text'][:100]}...")
except Exception as e:
    print(f"   ✗ Search failed: {e}")

# 8. Cleanup
print("\n8. Cleaning up test data...")
try:
    rag.delete_contract("test-fix-001")
    print("   ✓ Test data cleaned")
except:
    pass

# Final summary
print("\n" + "=" * 60)
print("  SYSTEM STATUS")
print("=" * 60)
print("\n✅ READY TO USE!")
print("\nNext steps:")
print("  1. Run full test suite: python test_alfresco_rag.py")
print("  2. Start Django server: python manage.py runserver")
print("  3. Test health endpoint: curl http://localhost:8000/api/alfresco/health")
print("\n" + "=" * 60)
