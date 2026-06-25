"""
Action Item Embedding Service
==============================
Indexes bid action items to Qdrant vector database for semantic search.

Features:
  - Auto-embedding on action creation
  - Semantic search across actions
  - Similar action recommendations
  - Historical action patterns
"""

import os
import logging
import uuid
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "bid_action_items"

# Lazy imports
_qdrant_client = None
_embedding_model = None


# ─────────────────────────────────────────────────────────────────────────────
# Initialization
# ─────────────────────────────────────────────────────────────────────────────

def get_qdrant_client():
    """Lazy-load Qdrant client."""
    global _qdrant_client
    if _qdrant_client is None:
        try:
            from qdrant_client import QdrantClient
            _qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
            logger.info(f"[ActionEmbeddings] Connected to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
        except Exception as e:
            logger.warning(f"[ActionEmbeddings] Qdrant unavailable: {e}")
            _qdrant_client = None
    return _qdrant_client


def get_embedding_model():
    """Lazy-load sentence transformer model."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            _embedding_model = SentenceTransformer(model_name, device='cpu')
            logger.info(f"[ActionEmbeddings] Loaded model: {model_name}")
        except Exception as e:
            logger.warning(f"[ActionEmbeddings] Model loading failed: {e}")
            _embedding_model = None
    return _embedding_model


def init_collection():
    """
    Initialize Qdrant collection for action items.
    Creates collection if it doesn't exist.
    """
    client = get_qdrant_client()
    if not client:
        return False

    try:
        from qdrant_client.models import Distance, VectorParams

        # Check if collection exists
        collections = client.get_collections().collections
        if any(c.name == COLLECTION_NAME for c in collections):
            logger.info(f"[ActionEmbeddings] Collection '{COLLECTION_NAME}' already exists")
            return True

        # Create collection (384 dimensions for all-MiniLM-L6-v2)
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

        logger.info(f"[ActionEmbeddings] Created collection '{COLLECTION_NAME}'")
        return True

    except Exception as e:
        logger.exception(f"[ActionEmbeddings] Collection init failed: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Embedding Operations
# ─────────────────────────────────────────────────────────────────────────────

def embed_action_item(action_item) -> bool:
    """
    Embed a single BidActionItem to Qdrant.

    Args:
        action_item: BidActionItem instance

    Returns:
        True if successful, False otherwise
    """
    client = get_qdrant_client()
    model = get_embedding_model()

    if not client or not model:
        logger.warning("[ActionEmbeddings] Embedding unavailable, skipping")
        return False

    try:
        # Construct text for embedding
        text = f"""
        Title: {action_item.title}
        Description: {action_item.description or ''}
        Department: {action_item.department.name if action_item.department else 'Unknown'}
        Priority: {action_item.priority}
        Source: {action_item.source_type}
        """

        # Generate embedding
        vector = model.encode(text).tolist()

        # Prepare metadata
        payload = {
            'action_id': action_item.id,
            'tender_id': action_item.tender_id,
            'title': action_item.title,
            'description': action_item.description or '',
            'department': action_item.department.name if action_item.department else 'Unknown',
            'priority': action_item.priority,
            'status': action_item.status,
            'source_type': action_item.source_type,
            'source_ref': action_item.source_ref or '',
            'risk_score': action_item.risk_score,
            'complexity_score': action_item.complexity_score,
            'financial_exposure': float(action_item.financial_exposure),
            'created_at': action_item.created_at.isoformat(),
        }

        # Upsert to Qdrant
        from qdrant_client.models import PointStruct

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(
                id=str(action_item.id),
                vector=vector,
                payload=payload
            )]
        )

        logger.debug(f"[ActionEmbeddings] Embedded action {action_item.id}")
        return True

    except Exception as e:
        logger.exception(f"[ActionEmbeddings] Embedding failed for action {action_item.id}: {e}")
        return False


def embed_all_actions(tender_id: Optional[int] = None) -> int:
    """
    Bulk embed all action items (or for specific tender).

    Args:
        tender_id: Optional tender ID to filter

    Returns:
        Number of actions embedded
    """
    from tenders.models import BidActionItem

    if not init_collection():
        logger.error("[ActionEmbeddings] Cannot initialize collection")
        return 0

    if tender_id:
        actions = BidActionItem.objects.filter(tender_id=tender_id).select_related('department')
    else:
        actions = BidActionItem.objects.all().select_related('department')

    count = 0
    for action in actions:
        if embed_action_item(action):
            count += 1

    logger.info(f"[ActionEmbeddings] Embedded {count} / {actions.count()} actions")
    return count


# ─────────────────────────────────────────────────────────────────────────────
# Search Operations
# ─────────────────────────────────────────────────────────────────────────────

def search_similar_actions(
    query: str,
    tender_id: Optional[int] = None,
    department: Optional[str] = None,
    limit: int = 5
) -> List[Dict]:
    """
    Semantic search for similar action items.

    Args:
        query: Search query text
        tender_id: Optional filter by tender
        department: Optional filter by department
        limit: Number of results

    Returns:
        List of matching actions with scores
    """
    client = get_qdrant_client()
    model = get_embedding_model()

    if not client or not model:
        return []

    try:
        # Generate query embedding
        vector = model.encode(query).tolist()

        # Build filter
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        filter_conditions = []
        if tender_id:
            filter_conditions.append(
                FieldCondition(key="tender_id", match=MatchValue(value=tender_id))
            )
        if department:
            filter_conditions.append(
                FieldCondition(key="department", match=MatchValue(value=department))
            )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Search
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            query_filter=search_filter,
            limit=limit,
        )

        # Format results
        matches = []
        for hit in results:
            matches.append({
                'action_id': hit.payload['action_id'],
                'title': hit.payload['title'],
                'description': hit.payload['description'],
                'department': hit.payload['department'],
                'priority': hit.payload['priority'],
                'status': hit.payload['status'],
                'risk_score': hit.payload['risk_score'],
                'similarity_score': hit.score,
            })

        return matches

    except Exception as e:
        logger.exception(f"[ActionEmbeddings] Search failed: {e}")
        return []


def find_similar_historical_actions(
    action_item,
    limit: int = 5
) -> List[Dict]:
    """
    Find historically similar actions (from other tenders).

    Args:
        action_item: Current BidActionItem
        limit: Number of results

    Returns:
        List of similar actions from other tenders
    """
    query = f"{action_item.title} {action_item.description or ''}"

    # Exclude current tender
    results = search_similar_actions(query, limit=limit * 2)

    # Filter out same tender
    filtered = [r for r in results if r['action_id'] != action_item.id]

    return filtered[:limit]


def recommend_actions_for_tender(
    tender_id: int,
    context: str = "",
    limit: int = 10
) -> List[Dict]:
    """
    Recommend action items based on tender context.
    Useful for suggesting common tasks for new tenders.

    Args:
        tender_id: Tender ID (to exclude existing actions)
        context: Tender title/description
        limit: Number of recommendations

    Returns:
        List of recommended actions
    """
    from tenders.models import BidActionItem

    # Get existing actions for this tender
    existing = set(
        BidActionItem.objects
        .filter(tender_id=tender_id)
        .values_list('title', flat=True)
    )

    # Search for similar actions from other tenders
    results = search_similar_actions(context, limit=limit * 3)

    # Filter out duplicates
    recommendations = []
    for result in results:
        if result['title'] not in existing:
            recommendations.append(result)

        if len(recommendations) >= limit:
            break

    return recommendations


# ─────────────────────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────────────────────

def check_embedding_health() -> Dict[str, bool]:
    """
    Check if embedding system is operational.

    Returns:
        {"qdrant": bool, "model": bool, "collection": bool}
    """
    status = {
        "qdrant": False,
        "model": False,
        "collection": False,
    }

    client = get_qdrant_client()
    model = get_embedding_model()

    status["qdrant"] = client is not None
    status["model"] = model is not None

    if client:
        try:
            collections = client.get_collections().collections
            status["collection"] = any(c.name == COLLECTION_NAME for c in collections)
        except:
            pass

    return status
