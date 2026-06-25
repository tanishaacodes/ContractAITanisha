"""
Qdrant Vector Store for Negotiation Intelligence
Handles storage and retrieval of negotiation patterns and clause interactions
"""
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Distance, VectorParams
from qdrant_client.http import models
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Collection names
NEGOTIATION_HISTORY_COLLECTION = "negotiation_history"
SILENT_RISK_PATTERNS_COLLECTION = "silent_risk_patterns"


def get_qdrant_client():
    """Get or create Qdrant client"""
    url = settings.QDRANT_URL
    return QdrantClient(url=url)


def ensure_collections():
    """Ensure required collections exist"""
    client = get_qdrant_client()

    collections = [
        (NEGOTIATION_HISTORY_COLLECTION, 384),  # MiniLM embedding size
        (SILENT_RISK_PATTERNS_COLLECTION, 384),
    ]

    for collection_name, vector_size in collections:
        try:
            client.get_collection(collection_name)
            logger.info(f"Collection {collection_name} already exists")
        except Exception:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection {collection_name}")


def store_negotiation_vector(vector, payload, idx):
    """
    Store a negotiation history vector in Qdrant

    Args:
        vector: Embedding vector
        payload: Metadata (counterparty, clause_type, accepted, etc.)
        idx: Unique ID
    """
    client = get_qdrant_client()

    client.upsert(
        collection_name=NEGOTIATION_HISTORY_COLLECTION,
        points=[
            PointStruct(
                id=idx,
                vector=vector,
                payload=payload
            )
        ]
    )


def store_negotiation_vectors_batch(vectors, payloads, start_idx):
    """
    Store multiple negotiation vectors in batch

    Args:
        vectors: List of embedding vectors
        payloads: List of metadata dicts
        start_idx: Starting ID for the batch
    """
    client = get_qdrant_client()

    points = [
        PointStruct(
            id=start_idx + i,
            vector=vector,
            payload=payload
        )
        for i, (vector, payload) in enumerate(zip(vectors, payloads))
    ]

    client.upsert(
        collection_name=NEGOTIATION_HISTORY_COLLECTION,
        points=points
    )


def search_similar_negotiations(vector, limit=20, clause_type_filter=None):
    """
    Search for similar negotiation patterns

    Args:
        vector: Query embedding vector
        limit: Number of results to return
        clause_type_filter: Optional filter by clause type

    Returns:
        List of search results with payload and score
    """
    client = get_qdrant_client()

    query_filter = None
    if clause_type_filter:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="clause_type",
                    match=models.MatchValue(value=clause_type_filter)
                )
            ]
        )

    results = client.query_points(
        collection_name=NEGOTIATION_HISTORY_COLLECTION,
        query=vector,
        limit=limit,
        query_filter=query_filter
    ).points

    return results


def store_risk_pattern(vector, payload, idx):
    """
    Store a silent risk pattern in Qdrant

    Args:
        vector: Clause-pair embedding vector
        payload: Metadata (clause_types, risk_type, impact_multiplier, etc.)
        idx: Unique ID
    """
    client = get_qdrant_client()

    client.upsert(
        collection_name=SILENT_RISK_PATTERNS_COLLECTION,
        points=[
            PointStruct(
                id=idx,
                vector=vector,
                payload=payload
            )
        ]
    )


def store_risk_patterns_batch(vectors, payloads, start_idx):
    """
    Store multiple risk patterns in batch

    Args:
        vectors: List of clause-pair embedding vectors
        payloads: List of metadata dicts
        start_idx: Starting ID for the batch
    """
    client = get_qdrant_client()

    points = [
        PointStruct(
            id=start_idx + i,
            vector=vector,
            payload=payload
        )
        for i, (vector, payload) in enumerate(zip(vectors, payloads))
    ]

    client.upsert(
        collection_name=SILENT_RISK_PATTERNS_COLLECTION,
        points=points
    )


def search_risk_patterns(vector, limit=5):
    """
    Search for matching silent risk patterns

    Args:
        vector: Clause-pair query embedding vector
        limit: Number of results to return

    Returns:
        List of search results with payload and score
    """
    client = get_qdrant_client()

    results = client.query_points(
        collection_name=SILENT_RISK_PATTERNS_COLLECTION,
        query=vector,
        limit=limit
    ).points

    return results


def delete_collection(collection_name):
    """Delete a collection (use with caution)"""
    client = get_qdrant_client()
    client.delete_collection(collection_name)
    logger.warning(f"Deleted collection {collection_name}")


def get_collection_info(collection_name):
    """Get information about a collection"""
    client = get_qdrant_client()
    return client.get_collection(collection_name)
