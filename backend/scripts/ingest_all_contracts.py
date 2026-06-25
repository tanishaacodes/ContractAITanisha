#!/usr/bin/env python
"""
Migration script to ingest all existing contracts into Qdrant vector store
for unified RAG chat functionality.

Usage:
    python scripts/ingest_all_contracts.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contract_ai.settings')
django.setup()

from core.models import Contract
from qdrant_client import QdrantClient, models as qmodels
from sentence_transformers import SentenceTransformer

# Configuration
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.environ.get("QDRANT_COLLECTION", "contracts")
EMBED_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500  # words per chunk

# Initialize clients
embedder = SentenceTransformer(EMBED_MODEL, device='cpu')
VECTOR_DIM = embedder.get_sentence_embedding_dimension()
client = QdrantClient(url=QDRANT_URL)


def chunk_text(text, chunk_size=CHUNK_SIZE):
    """Split text into chunks of approximately chunk_size words"""
    if not text:
        return []
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]


def ensure_collection_exists():
    """Create Qdrant collection if it doesn't exist"""
    try:
        client.get_collection(COLLECTION_NAME)
        print(f"✓ Collection '{COLLECTION_NAME}' already exists")
    except:
        print(f"Creating collection '{COLLECTION_NAME}'...")
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=qmodels.VectorParams(
                size=VECTOR_DIM,
                distance=qmodels.Distance.COSINE
            )
        )
        print(f"✓ Collection '{COLLECTION_NAME}' created successfully")


def ingest_contracts():
    """Ingest all contracts from database into Qdrant"""
    print("\n" + "="*60)
    print("CONTRACT INGESTION MIGRATION")
    print("="*60)

    # Ensure collection exists
    ensure_collection_exists()

    # Fetch all contracts
    contracts = Contract.objects.filter(full_text__isnull=False).exclude(full_text='')
    total_contracts = contracts.count()

    if total_contracts == 0:
        print("\nNo contracts found with extracted text.")
        return

    print(f"\n Found {total_contracts} contract(s) with text to ingest")
    print(f" Embedding model: {EMBED_MODEL}")
    print(f" Chunk size: {CHUNK_SIZE} words")
    print(f" Target collection: {COLLECTION_NAME}")
    print()

    points = []
    point_id = 1
    total_chunks = 0

    for idx, contract in enumerate(contracts, 1):
        print(f"[{idx}/{total_contracts}] Processing: {contract.original_filename}")

        # Extract text
        text = contract.full_text
        if not text or len(text.strip()) < 10:
            print(f"  ⚠ Skipping - insufficient text")
            continue

        # Chunk text
        chunks = chunk_text(text)
        print(f"  → Split into {len(chunks)} chunk(s)")

        # Create embeddings and points
        for chunk_idx, chunk in enumerate(chunks):
            try:
                # Generate embedding
                emb = embedder.encode(chunk).tolist()

                # Create point with metadata
                point = qmodels.PointStruct(
                    id=point_id,
                    vector=emb,
                    payload={
                        "contract_id": str(contract.id),
                        "user_id": str(contract.user.id),
                        "filename": contract.original_filename,
                        "chunk_index": chunk_idx,
                        "text": chunk,
                    }
                )
                points.append(point)
                point_id += 1
                total_chunks += 1

            except Exception as e:
                print(f"  ✗ Error processing chunk {chunk_idx}: {str(e)}")

        print(f"  ✓ Added {len(chunks)} chunk(s) to batch")

        # Batch upsert every 100 points to avoid memory issues
        if len(points) >= 100:
            print(f"\n  Upserting batch of {len(points)} points...")
            client.upsert(collection_name=COLLECTION_NAME, points=points)
            points = []

    # Upsert remaining points
    if points:
        print(f"\n  Upserting final batch of {len(points)} points...")
        client.upsert(collection_name=COLLECTION_NAME, points=points)

    print("\n" + "="*60)
    print("✓ MIGRATION COMPLETE")
    print("="*60)
    print(f"Total contracts processed: {total_contracts}")
    print(f"Total chunks created: {total_chunks}")
    print(f"Collection: {COLLECTION_NAME}")
    print()


if __name__ == "__main__":
    try:
        ingest_contracts()
    except KeyboardInterrupt:
        print("\n\n⚠ Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
