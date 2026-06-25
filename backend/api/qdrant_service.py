"""
Qdrant Vector Database Service
Handles storage and retrieval of clause embeddings
"""

import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http import models
import uuid
import logging
import numpy as np

logger = logging.getLogger(__name__)


class QdrantService:
    """
    Service for managing clause embeddings in Qdrant vector database
    """

    def __init__(self, host=None, port=None):
        """
        Initialize Qdrant client

        Args:
            host: Qdrant server host
            port: Qdrant server port
        """
        if host is None:
            host = os.getenv('QDRANT_HOST', 'localhost')
        if port is None:
            port = int(os.getenv('QDRANT_PORT', 6333))
        try:
            self.client = QdrantClient(host=host, port=port)
            self.collection_name = "contract_clauses"
            self._ensure_collection_exists()
            logger.info(f"Connected to Qdrant at {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            logger.warning("Qdrant features will be disabled")
            self.client = None

    def _ensure_collection_exists(self):
        """
        Ensure the clauses collection exists, create if not
        """
        if not self.client:
            return

        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]

            if self.collection_name not in collection_names:
                # Create collection with appropriate vector size
                # MiniLM-L6-v2 produces 384-dimensional vectors
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection {self.collection_name} already exists")

        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")
            raise

    def store_clause_embedding(self, clause_id, contract_id, clause_text,
                               clause_name, embedding, metadata=None):
        """
        Store a single clause embedding in Qdrant

        Args:
            clause_id: Database ID of the clause
            contract_id: Database ID of the contract
            clause_text: Full text of the clause
            clause_name: Name/type of the clause
            embedding: Numpy array or list of embedding values
            metadata: Additional metadata dictionary

        Returns:
            Qdrant point ID (UUID string)
        """
        if not self.client:
            logger.warning("Qdrant client not available")
            return None

        try:
            # Generate unique Qdrant point ID
            point_id = str(uuid.uuid4())

            # Prepare payload (convert UUIDs to strings for JSON serialization)
            payload = {
                'clause_id': str(clause_id),
                'contract_id': str(contract_id),
                'clause_text': clause_text[:500],  # Truncate for storage
                'clause_name': clause_name,
                'full_text_length': len(clause_text),
            }

            # Add additional metadata
            if metadata:
                payload.update(metadata)

            # Convert embedding to list if numpy array
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()

            # Create point
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )

            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )

            logger.info(f"Stored clause embedding: {clause_id} -> {point_id}")
            return point_id

        except Exception as e:
            logger.error(f"Failed to store clause embedding: {e}")
            return None

    def store_clause_embeddings_batch(self, clauses_data):
        """
        Store multiple clause embeddings in batch

        Args:
            clauses_data: List of dictionaries with keys:
                         - clause_id, contract_id, clause_text, clause_name, embedding, metadata

        Returns:
            List of Qdrant point IDs
        """
        if not self.client:
            logger.warning("Qdrant client not available")
            return []

        try:
            points = []
            point_ids = []

            for clause_data in clauses_data:
                point_id = str(uuid.uuid4())
                point_ids.append(point_id)

                # Prepare payload (convert UUIDs to strings for JSON serialization)
                payload = {
                    'clause_id': str(clause_data['clause_id']),
                    'contract_id': str(clause_data['contract_id']),
                    'clause_text': clause_data['clause_text'][:500],
                    'clause_name': clause_data['clause_name'],
                    'full_text_length': len(clause_data['clause_text']),
                }

                # Add metadata if present
                if 'metadata' in clause_data and clause_data['metadata']:
                    payload.update(clause_data['metadata'])

                # Convert embedding
                embedding = clause_data['embedding']
                if isinstance(embedding, np.ndarray):
                    embedding = embedding.tolist()

                # Create point
                points.append(PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                ))

            # Batch upsert
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            logger.info(f"Stored {len(points)} clause embeddings in batch")
            return point_ids

        except Exception as e:
            logger.error(f"Failed to store clause embeddings batch: {e}")
            return []

    def search_similar_clauses(self, query_embedding, limit=10,
                               contract_id=None, clause_type=None):
        """
        Search for similar clauses using vector similarity

        Args:
            query_embedding: Query vector (numpy array or list)
            limit: Maximum number of results
            contract_id: Filter by contract ID (optional)
            clause_type: Filter by clause type (optional)

        Returns:
            List of similar clause results with scores
        """
        if not self.client:
            logger.warning("Qdrant client not available")
            return []

        try:
            # Convert embedding to list if numpy array
            if isinstance(query_embedding, np.ndarray):
                query_embedding = query_embedding.tolist()

            # Build filter if needed
            must_conditions = []
            if contract_id:
                must_conditions.append(
                    models.FieldCondition(
                        key="contract_id",
                        match=models.MatchValue(value=contract_id)
                    )
                )
            if clause_type:
                must_conditions.append(
                    models.FieldCondition(
                        key="clause_name",
                        match=models.MatchValue(value=clause_type)
                    )
                )

            query_filter = models.Filter(must=must_conditions) if must_conditions else None

            # Search — supports both old (.search) and new (.query_points) Qdrant client APIs
            try:
                search_results = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_embedding,
                    query_filter=query_filter,
                    limit=limit,
                ).points
            except AttributeError:
                search_results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    query_filter=query_filter,
                    limit=limit,
                )

            # Format results
            results = []
            for hit in search_results:
                results.append({
                    'point_id': hit.id,
                    'score': hit.score,
                    'clause_id': hit.payload.get('clause_id'),
                    'contract_id': hit.payload.get('contract_id'),
                    'clause_name': hit.payload.get('clause_name'),
                    'clause_text': hit.payload.get('clause_text'),
                })

            logger.info(f"Found {len(results)} similar clauses")
            return results

        except Exception as e:
            logger.error(f"Failed to search similar clauses: {e}")
            return []

    def delete_contract_clauses(self, contract_id):
        """
        Delete all clause embeddings for a contract

        Args:
            contract_id: Contract database ID

        Returns:
            Success boolean
        """
        if not self.client:
            return False

        try:
            # Delete points matching contract_id
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="contract_id",
                                match=models.MatchValue(value=contract_id)
                            )
                        ]
                    )
                )
            )

            logger.info(f"Deleted clauses for contract: {contract_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete contract clauses: {e}")
            return False

    def get_collection_stats(self):
        """
        Get statistics about the clause collection

        Returns:
            Dictionary with collection statistics
        """
        if not self.client:
            return {}

        try:
            collection_info = self.client.get_collection(self.collection_name)

            return {
                'total_points': collection_info.points_count,
                'vector_size': collection_info.config.params.vectors.size,
                'distance_metric': collection_info.config.params.vectors.distance.value,
            }

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}


# Singleton instance
_qdrant_service = None


def get_qdrant_service():
    """Get or create singleton QdrantService instance"""
    global _qdrant_service
    if _qdrant_service is None:
        _qdrant_service = QdrantService()
    return _qdrant_service
