"""
Qdrant Vector Store Module
===========================
Integration with Qdrant vector database for semantic clause storage and retrieval.

This module provides functionality to:
- Store clause embeddings in Qdrant
- Search for similar clauses
- Manage collections
- Perform semantic retrieval
"""

import os
from typing import List, Dict, Optional, Tuple
import uuid
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchParams
)

logger = logging.getLogger(__name__)


class QdrantStore:
    """
    Wrapper for Qdrant vector database operations.
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        collection_name: str = "clauses",
        vector_size: int = 384
    ):
        """
        Initialize Qdrant store.

        Args:
            host (str): Qdrant server host (default: QDRANT_HOST env or localhost)
            port (int): Qdrant server port (default: QDRANT_PORT env or 6333)
            collection_name (str): Name of the collection to use (default: clauses)
            vector_size (int): Dimension of embedding vectors (default: 384 for MiniLM)
        """
        if host is None:
            host = os.getenv('QDRANT_HOST', 'localhost')
        if port is None:
            port = int(os.getenv('QDRANT_PORT', 6333))
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.vector_size = vector_size

        try:
            self.client = QdrantClient(host=host, port=port)
            logger.info(f"Connected to Qdrant at {host}:{port}")
            self._ensure_collection_exists()
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise

    def _ensure_collection_exists(self):
        """
        Ensure the collection exists, create if it doesn't.
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection '{self.collection_name}' created successfully")
            else:
                logger.info(f"Collection '{self.collection_name}' already exists")

        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise

    def store_single_clause(
        self,
        embedding: List[float],
        metadata: Dict,
        point_id: Optional[str] = None
    ) -> str:
        """
        Store a single clause embedding with metadata.

        Args:
            embedding (List[float]): The clause embedding vector
            metadata (Dict): Metadata about the clause (clause_text, clause_type, contract_id, etc.)
            point_id (Optional[str]): Custom ID for the point (generated if not provided)

        Returns:
            str: The point ID

        Example:
            >>> store = QdrantStore()
            >>> point_id = store.store_single_clause(
            ...     embedding=embedding_vector,
            ...     metadata={'clause_text': 'Payment shall...', 'clause_type': 'Payment'}
            ... )
        """
        if point_id is None:
            point_id = str(uuid.uuid4())

        try:
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=metadata
            )

            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )

            logger.debug(f"Stored clause with ID: {point_id}")
            return point_id

        except Exception as e:
            logger.error(f"Error storing clause: {e}")
            raise

    def store_embeddings(
        self,
        embeddings: List[List[float]],
        metadata_list: List[Dict],
        point_ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Store multiple clause embeddings in batch.

        Args:
            embeddings (List[List[float]]): List of embedding vectors
            metadata_list (List[Dict]): List of metadata dictionaries (one per embedding)
            point_ids (Optional[List[str]]): Custom IDs for points (generated if not provided)

        Returns:
            List[str]: List of point IDs

        Example:
            >>> store = QdrantStore()
            >>> ids = store.store_embeddings(
            ...     embeddings=[emb1, emb2, emb3],
            ...     metadata_list=[meta1, meta2, meta3]
            ... )
        """
        if len(embeddings) != len(metadata_list):
            raise ValueError("Number of embeddings must match number of metadata entries")

        # Generate IDs if not provided
        if point_ids is None:
            point_ids = [str(uuid.uuid4()) for _ in embeddings]

        try:
            points = [
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=metadata
                )
                for point_id, embedding, metadata in zip(point_ids, embeddings, metadata_list)
            ]

            # Upsert in batches of 100
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                logger.debug(f"Stored batch of {len(batch)} clauses")

            logger.info(f"Stored {len(points)} clauses successfully")
            return point_ids

        except Exception as e:
            logger.error(f"Error storing embeddings batch: {e}")
            raise

    def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Search for similar clauses using a query embedding.

        Args:
            query_embedding (List[float]): The query embedding vector
            limit (int): Maximum number of results to return (default: 10)
            filters (Optional[Dict]): Filter conditions (e.g., {'clause_type': 'Payment'})
            score_threshold (Optional[float]): Minimum similarity score (0-1)

        Returns:
            List[Dict]: List of search results with 'id', 'score', and 'payload'

        Example:
            >>> results = store.search_similar(
            ...     query_embedding=query_vector,
            ...     limit=5,
            ...     filters={'contract_id': 'abc-123'}
            ... )
            >>> results[0]['score']
            0.95
        """
        try:
            # Build filter if provided
            query_filter = None
            if filters:
                conditions = [
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                    for key, value in filters.items()
                ]
                query_filter = Filter(must=conditions) if conditions else None

            # Perform search using query_points (new Qdrant API)
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=limit,
                query_filter=query_filter,
                score_threshold=score_threshold,
                with_payload=True
            )

            # Format results
            results = [
                {
                    'id': str(hit.id),
                    'score': hit.score,
                    'payload': hit.payload
                }
                for hit in search_result.points
            ]

            logger.debug(f"Found {len(results)} similar clauses")
            return results

        except Exception as e:
            logger.error(f"Error searching for similar clauses: {e}")
            return []

    def search_by_text_query(
        self,
        query_text: str,
        embedder,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar clauses using text query (convenience method).

        Args:
            query_text (str): The query text to search for
            embedder: Embedder instance to convert text to vector
            limit (int): Maximum number of results
            filters (Optional[Dict]): Filter conditions

        Returns:
            List[Dict]: Search results

        Example:
            >>> from nlp.embedding import get_embedder
            >>> embedder = get_embedder()
            >>> results = store.search_by_text_query(
            ...     query_text="payment terms",
            ...     embedder=embedder,
            ...     limit=5
            ... )
        """
        try:
            # Convert text to embedding
            query_embedding = embedder.embed_single_clause(query_text)

            # Search using embedding
            return self.search_similar(
                query_embedding=query_embedding,
                limit=limit,
                filters=filters
            )

        except Exception as e:
            logger.error(f"Error in text query search: {e}")
            return []

    def get_clause_by_id(self, point_id: str) -> Optional[Dict]:
        """
        Retrieve a specific clause by its ID.

        Args:
            point_id (str): The point ID

        Returns:
            Optional[Dict]: Clause data with 'id', 'vector', 'payload', or None if not found
        """
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id],
                with_vectors=True,
                with_payload=True
            )

            if result:
                point = result[0]
                return {
                    'id': str(point.id),
                    'vector': point.vector,
                    'payload': point.payload
                }
            return None

        except Exception as e:
            logger.error(f"Error retrieving clause: {e}")
            return None

    def delete_clause(self, point_id: str) -> bool:
        """
        Delete a clause from the vector store.

        Args:
            point_id (str): The point ID to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[point_id]
            )
            logger.debug(f"Deleted clause with ID: {point_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting clause: {e}")
            return False

    def delete_by_filter(self, filters: Dict) -> int:
        """
        Delete clauses matching filter conditions.

        Args:
            filters (Dict): Filter conditions

        Returns:
            int: Number of deleted clauses
        """
        try:
            conditions = [
                FieldCondition(
                    key=key,
                    match=MatchValue(value=value)
                )
                for key, value in filters.items()
            ]

            if not conditions:
                return 0

            result = self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(must=conditions)
            )

            logger.info(f"Deleted clauses matching filter: {filters}")
            return 1  # Qdrant doesn't return count, assume success

        except Exception as e:
            logger.error(f"Error deleting by filter: {e}")
            return 0

    def get_collection_info(self) -> Dict:
        """
        Get information about the collection.

        Returns:
            Dict: Collection statistics and configuration
        """
        try:
            info = self.client.get_collection(collection_name=self.collection_name)
            return {
                'name': info.config.name if hasattr(info.config, 'name') else self.collection_name,
                'vector_size': info.config.params.vectors.size,
                'distance': str(info.config.params.vectors.distance),
                'points_count': info.points_count,
                'status': str(info.status)
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}

    def check_connection(self) -> bool:
        """
        Check if Qdrant server is accessible.

        Returns:
            bool: True if connected, False otherwise
        """
        try:
            self.client.get_collections()
            logger.info("Qdrant connection is healthy")
            return True
        except Exception as e:
            logger.error(f"Qdrant connection failed: {e}")
            return False


# Module-level singleton instance
_default_store = None


def get_qdrant_store(
    host: str = "localhost",
    port: int = 6333,
    collection_name: str = "clauses"
) -> QdrantStore:
    """
    Get or create the default Qdrant store instance (singleton pattern).

    Args:
        host (str): Qdrant server host
        port (int): Qdrant server port
        collection_name (str): Collection name

    Returns:
        QdrantStore: The store instance
    """
    global _default_store
    if _default_store is None:
        _default_store = QdrantStore(host, port, collection_name)
    return _default_store


def store_embeddings(
    embeddings: List[List[float]],
    metadata_list: List[Dict]
) -> List[str]:
    """
    Convenience function to store embeddings using the default store.

    Args:
        embeddings (List[List[float]]): Embedding vectors
        metadata_list (List[Dict]): Metadata for each embedding

    Returns:
        List[str]: Point IDs

    Example:
        >>> from vector.qdrant_store import store_embeddings
        >>> ids = store_embeddings(embeddings, metadata_list)
    """
    store = get_qdrant_store()
    return store.store_embeddings(embeddings, metadata_list)


def search_similar_clauses(
    query_embedding: List[float],
    limit: int = 10
) -> List[Dict]:
    """
    Convenience function to search similar clauses.

    Args:
        query_embedding (List[float]): Query vector
        limit (int): Max results

    Returns:
        List[Dict]: Search results
    """
    store = get_qdrant_store()
    return store.search_similar(query_embedding, limit)
