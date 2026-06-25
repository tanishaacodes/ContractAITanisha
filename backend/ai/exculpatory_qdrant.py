"""
Exculpatory Pattern Qdrant Integration
Manages vector storage and similarity search for exculpatory patterns
"""

import os
import logging
from typing import List, Dict, Any, Optional
from vector.qdrant_store import QdrantStore

logger = logging.getLogger(__name__)


class ExculpatoryPatternStore:
    """
    Specialized Qdrant store for exculpatory patterns.
    """

    def __init__(self, host: str = None, port: int = None):
        """
        Initialize pattern store.

        Args:
            host: Qdrant server host
            port: Qdrant server port
        """
        if host is None:
            host = os.getenv('QDRANT_HOST', 'localhost')
        if port is None:
            port = int(os.getenv('QDRANT_PORT', 6333))
        self.store = QdrantStore(
            host=host,
            port=port,
            collection_name="exculpatory_patterns",
            vector_size=384  # MiniLM embedding size
        )

    def index_patterns(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """
        Index exculpatory patterns in Qdrant.

        Args:
            patterns: List of pattern dictionaries with 'id', 'text', 'embedding', etc.

        Returns:
            List of point IDs
        """
        try:
            # Prepare embeddings and metadata
            embeddings = []
            metadata_list = []
            point_ids = []

            for pattern in patterns:
                if "vector_embedding" in pattern and pattern["vector_embedding"]:
                    embeddings.append(pattern["vector_embedding"])
                    point_ids.append(pattern["id"])

                    # Metadata without embedding
                    metadata = {
                        "pattern_id": pattern["pattern_id"],
                        "label": pattern["label"],
                        "text": pattern["text"],
                        "risk_category": pattern["risk_category"],
                        "controlled_by": pattern["controlled_by"],
                        "explanation": pattern["explanation"]
                    }
                    metadata_list.append(metadata)

            if embeddings:
                stored_ids = self.store.store_embeddings(
                    embeddings=embeddings,
                    metadata_list=metadata_list,
                    point_ids=point_ids
                )
                logger.info(f"Indexed {len(stored_ids)} exculpatory patterns")
                return stored_ids
            else:
                logger.warning("No patterns with embeddings to index")
                return []

        except Exception as e:
            logger.error(f"Error indexing patterns: {e}")
            raise

    def search_similar_patterns(
        self,
        clause_embedding: List[float],
        limit: int = 3,
        threshold: float = 0.65
    ) -> List[Dict[str, Any]]:
        """
        Search for similar exculpatory patterns.

        Args:
            clause_embedding: Embedding of the clause to check
            limit: Maximum number of results
            threshold: Minimum similarity threshold (0-1)

        Returns:
            List of matching patterns with similarity scores
        """
        try:
            results = self.store.search_similar(
                query_embedding=clause_embedding,
                limit=limit,
                score_threshold=threshold
            )

            # Format results
            matches = []
            for result in results:
                payload = result["payload"]
                matches.append({
                    "pattern_id": payload.get("pattern_id"),
                    "pattern": payload.get("label"),
                    "similarity": round(result["score"], 2),
                    "text": payload.get("text"),
                    "risk_category": payload.get("risk_category"),
                    "explanation": payload.get("explanation")
                })

            return matches

        except Exception as e:
            logger.error(f"Error searching patterns: {e}")
            return []

    def get_pattern_by_id(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific pattern by ID.

        Args:
            pattern_id: Pattern identifier

        Returns:
            Pattern dictionary or None
        """
        try:
            result = self.store.get_clause_by_id(pattern_id)
            if result:
                return {
                    "id": result["id"],
                    "embedding": result["vector"],
                    **result["payload"]
                }
            return None

        except Exception as e:
            logger.error(f"Error retrieving pattern: {e}")
            return None

    def check_collection_exists(self) -> bool:
        """
        Check if the exculpatory_patterns collection exists.

        Returns:
            True if exists, False otherwise
        """
        try:
            info = self.store.get_collection_info()
            return info.get("points_count", 0) >= 0
        except Exception:
            return False

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the pattern collection.

        Returns:
            Statistics dictionary
        """
        try:
            return self.store.get_collection_info()
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}


# Singleton instance
_pattern_store = None


def get_pattern_store(host: str = None, port: int = None) -> ExculpatoryPatternStore:
    """
    Get or create the pattern store instance (singleton).

    Args:
        host: Qdrant server host
        port: Qdrant server port

    Returns:
        ExculpatoryPatternStore instance
    """
    global _pattern_store
    if _pattern_store is None:
        _pattern_store = ExculpatoryPatternStore(host, port)
    return _pattern_store
