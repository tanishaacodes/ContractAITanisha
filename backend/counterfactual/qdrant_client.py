"""
Qdrant client for contract outcome similarity search.
Manages vector embeddings and retrieval for historical contract outcomes.
"""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from django.conf import settings
import logging
import uuid

logger = logging.getLogger(__name__)

# Initialize Qdrant client
try:
    qdrant = QdrantClient(url=settings.QDRANT_URL)
    logger.info(f"Connected to Qdrant at {settings.QDRANT_URL}")
except Exception as e:
    logger.warning(f"Could not connect to Qdrant: {e}")
    qdrant = None

# Collection name for contract outcomes
COLLECTION_NAME = "contract_outcomes"
VECTOR_SIZE = 384  # For sentence-transformers/all-MiniLM-L6-v2


def ensure_collection_exists():
    """
    Create the contract_outcomes collection if it doesn't exist.
    """
    if not qdrant:
        logger.warning("Qdrant client not initialized")
        return False

    try:
        collections = qdrant.get_collections().collections
        collection_exists = any(c.name == COLLECTION_NAME for c in collections)

        if not collection_exists:
            qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection: {COLLECTION_NAME}")
        return True
    except Exception as e:
        logger.error(f"Error ensuring collection exists: {e}")
        return False


def index_historical_outcome(outcome_data, embedding_vector):
    """
    Index a historical contract outcome in Qdrant.

    Args:
        outcome_data: Dictionary containing outcome information
        embedding_vector: List of floats representing the contract embedding

    Returns:
        str: Point ID in Qdrant
    """
    if not qdrant:
        logger.warning("Qdrant client not initialized")
        return None

    ensure_collection_exists()

    try:
        point_id = str(uuid.uuid4())

        point = PointStruct(
            id=point_id,
            vector=embedding_vector,
            payload={
                "contract_id": outcome_data.get("contract_id"),
                "contract_type": outcome_data.get("contract_type"),
                "industry": outcome_data.get("industry"),
                "dispute_occurred": outcome_data.get("dispute_occurred", False),
                "litigation_occurred": outcome_data.get("litigation_occurred", False),
                "renewal_success": outcome_data.get("renewal_success"),
                "revenue_impact": float(outcome_data.get("revenue_impact", 0)),
                "operational_delays_days": outcome_data.get("operational_delays_days"),
                "key_clauses": outcome_data.get("key_clauses", {}),
            }
        )

        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[point]
        )

        logger.info(f"Indexed outcome for contract {outcome_data.get('contract_id')}")
        return point_id

    except Exception as e:
        logger.error(f"Error indexing historical outcome: {e}")
        return None


def search_similar_outcomes(embedding_vector, limit=5, filters=None):
    """
    Search for similar historical contract outcomes.

    Args:
        embedding_vector: Query vector (list of floats)
        limit: Maximum number of results to return
        filters: Optional filters (dict) for contract_type, industry, etc.

    Returns:
        list: Similar outcomes with scores
    """
    if not qdrant:
        logger.warning("Qdrant client not initialized")
        return []

    ensure_collection_exists()

    try:
        # Build query filter if filters provided
        query_filter = None
        if filters:
            conditions = []
            if "contract_type" in filters:
                conditions.append(
                    FieldCondition(
                        key="contract_type",
                        match=MatchValue(value=filters["contract_type"])
                    )
                )
            if "industry" in filters:
                conditions.append(
                    FieldCondition(
                        key="industry",
                        match=MatchValue(value=filters["industry"])
                    )
                )
            if conditions:
                query_filter = Filter(must=conditions)

        # Perform similarity search
        search_result = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=embedding_vector,
            query_filter=query_filter,
            limit=limit
        )

        # Format results
        results = []
        for hit in search_result:
            results.append({
                "score": hit.score,
                "contract_id": hit.payload.get("contract_id"),
                "contract_type": hit.payload.get("contract_type"),
                "industry": hit.payload.get("industry"),
                "dispute_occurred": hit.payload.get("dispute_occurred"),
                "litigation_occurred": hit.payload.get("litigation_occurred"),
                "renewal_success": hit.payload.get("renewal_success"),
                "revenue_impact": hit.payload.get("revenue_impact"),
                "operational_delays_days": hit.payload.get("operational_delays_days"),
                "key_clauses": hit.payload.get("key_clauses", {}),
            })

        logger.info(f"Found {len(results)} similar outcomes")
        return results

    except Exception as e:
        logger.error(f"Error searching similar outcomes: {e}")
        return []


def delete_outcome(point_id):
    """
    Delete a historical outcome from Qdrant.

    Args:
        point_id: The ID of the point to delete

    Returns:
        bool: Success status
    """
    if not qdrant:
        logger.warning("Qdrant client not initialized")
        return False

    try:
        qdrant.delete(
            collection_name=COLLECTION_NAME,
            points_selector=[point_id]
        )
        logger.info(f"Deleted outcome {point_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting outcome: {e}")
        return False


def get_collection_stats():
    """
    Get statistics about the contract outcomes collection.

    Returns:
        dict: Collection statistics
    """
    if not qdrant:
        return {"error": "Qdrant client not initialized"}

    try:
        collection_info = qdrant.get_collection(collection_name=COLLECTION_NAME)
        return {
            "vectors_count": collection_info.vectors_count,
            "points_count": collection_info.points_count,
            "status": collection_info.status,
        }
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        return {"error": str(e)}
