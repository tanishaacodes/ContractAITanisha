"""
Qdrant Vector Database Service
Handles clause embeddings for semantic similarity analysis
"""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from django.conf import settings
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None
import logging
import hashlib

logger = logging.getLogger(__name__)


class QdrantService:
    """
    Service class for Qdrant vector database operations.
    Manages clause embeddings for semantic similarity.
    """

    COLLECTION_NAME = "contract_clauses"
    VECTOR_SIZE = 384  # MiniLM-L6-v2 produces 384-dimensional vectors

    def __init__(self):
        """Initialize Qdrant client and embedding model"""
        # Parse Qdrant URL
        qdrant_url = settings.QDRANT_URL
        if qdrant_url.startswith("http://"):
            host = qdrant_url.replace("http://", "").split(":")[0]
            port = int(qdrant_url.split(":")[-1]) if ":" in qdrant_url.split("//")[1] else 6333
        else:
            host = "localhost"
            port = 6333

        self.client = QdrantClient(host=host, port=port)

        # Initialize embedding model (same as used in RAG)
        self.embedding_model = SentenceTransformer(settings.CONTRACTS_BERT_MODEL, device='cpu')

        logger.info(f"Qdrant service initialized: {host}:{port}")

        # Ensure collection exists
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.COLLECTION_NAME not in collection_names:
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=self.VECTOR_SIZE,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.COLLECTION_NAME}")
            else:
                logger.info(f"Qdrant collection already exists: {self.COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection: {e}")

    def _get_clause_hash(self, clause_text):
        """Generate SHA256 hash of clause text for deduplication"""
        return hashlib.sha256(clause_text.encode('utf-8')).hexdigest()

    def store_clause_embedding(self, clause_id, clause_text, metadata=None):
        """
        Store clause embedding in Qdrant.

        Args:
            clause_id: Clause UUID (from MySQL)
            clause_text: Clause text to embed
            metadata: Optional metadata dict (contract_id, category, etc.)

        Returns:
            Point ID in Qdrant
        """
        try:
            # Generate embedding
            vector = self.embedding_model.encode(clause_text).tolist()

            # Generate clause hash for deduplication
            clause_hash = self._get_clause_hash(clause_text)

            # Prepare metadata payload
            payload = {
                "clause_id": str(clause_id),
                "clause_hash": clause_hash,
                "clause_text": clause_text[:500],  # Store truncated text
                "type": "clause"
            }

            if metadata:
                payload.update(metadata)

            # Upsert point (uses clause_id as point_id)
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[
                    PointStruct(
                        id=clause_hash,  # Use hash as ID for deduplication
                        vector=vector,
                        payload=payload
                    )
                ]
            )

            logger.info(f"Stored clause embedding: {clause_id[:8]}")
            return clause_hash

        except Exception as e:
            logger.error(f"Error storing clause embedding: {e}")
            return None

    def find_similar_clauses(self, clause_text, limit=10, score_threshold=0.7):
        """
        Find semantically similar clauses.

        Args:
            clause_text: Clause text to search for
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0-1)

        Returns:
            List of similar clauses with scores
        """
        try:
            # Generate query embedding
            query_vector = self.embedding_model.encode(clause_text).tolist()

            # Search Qdrant
            search_results = self.client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )

            # Format results
            similar_clauses = []
            for result in search_results:
                similar_clauses.append({
                    "clause_id": result.payload.get("clause_id"),
                    "clause_hash": result.payload.get("clause_hash"),
                    "clause_text": result.payload.get("clause_text"),
                    "similarity_score": result.score,
                    "contract_id": result.payload.get("contract_id"),
                    "category": result.payload.get("category")
                })

            logger.info(f"Found {len(similar_clauses)} similar clauses")
            return similar_clauses

        except Exception as e:
            logger.error(f"Error finding similar clauses: {e}")
            return []

    def find_clauses_by_category(self, category, limit=100):
        """
        Find all clauses in a specific category.

        Args:
            category: Clause category (e.g., "Indemnity", "Liability")
            limit: Maximum number of results

        Returns:
            List of clauses in that category
        """
        try:
            search_results = self.client.scroll(
                collection_name=self.COLLECTION_NAME,
                scroll_filter={
                    "must": [
                        {
                            "key": "category",
                            "match": {"value": category}
                        }
                    ]
                },
                limit=limit
            )

            clauses = []
            for point in search_results[0]:
                clauses.append({
                    "clause_id": point.payload.get("clause_id"),
                    "clause_hash": point.payload.get("clause_hash"),
                    "clause_text": point.payload.get("clause_text"),
                    "category": point.payload.get("category"),
                    "contract_id": point.payload.get("contract_id")
                })

            logger.info(f"Found {len(clauses)} clauses in category: {category}")
            return clauses

        except Exception as e:
            logger.error(f"Error finding clauses by category: {e}")
            return []

    def detect_clause_clusters(self, min_cluster_size=5):
        """
        Detect clusters of similar clauses for risk correlation analysis.

        Args:
            min_cluster_size: Minimum cluster size to consider

        Returns:
            List of clause clusters
        """
        # This is a simplified version - in production, you'd use HDBSCAN or similar
        # For now, we'll group by similarity using a sliding window approach

        try:
            # Get all points
            all_points, _ = self.client.scroll(
                collection_name=self.COLLECTION_NAME,
                limit=1000  # Adjust based on your dataset size
            )

            logger.info(f"Analyzing {len(all_points)} clauses for clustering")

            # Simplified clustering: group by category for now
            # In production, use proper clustering algorithms
            clusters = {}
            for point in all_points:
                category = point.payload.get("category", "Unknown")
                if category not in clusters:
                    clusters[category] = []
                clusters[category].append({
                    "clause_id": point.payload.get("clause_id"),
                    "clause_hash": point.payload.get("clause_hash"),
                    "contract_id": point.payload.get("contract_id")
                })

            # Filter clusters by size
            significant_clusters = {
                k: v for k, v in clusters.items()
                if len(v) >= min_cluster_size
            }

            logger.info(f"Found {len(significant_clusters)} significant clause clusters")
            return significant_clusters

        except Exception as e:
            logger.error(f"Error detecting clause clusters: {e}")
            return {}

    def get_clause_by_hash(self, clause_hash):
        """
        Retrieve clause by its hash.

        Args:
            clause_hash: SHA256 hash of clause text

        Returns:
            Clause data or None
        """
        try:
            result = self.client.retrieve(
                collection_name=self.COLLECTION_NAME,
                ids=[clause_hash]
            )

            if result:
                point = result[0]
                return {
                    "clause_id": point.payload.get("clause_id"),
                    "clause_hash": point.payload.get("clause_hash"),
                    "clause_text": point.payload.get("clause_text"),
                    "category": point.payload.get("category"),
                    "contract_id": point.payload.get("contract_id")
                }
            return None

        except Exception as e:
            logger.error(f"Error retrieving clause by hash: {e}")
            return None

    def delete_clause(self, clause_hash):
        """Delete clause from Qdrant by hash"""
        try:
            self.client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=[clause_hash]
            )
            logger.info(f"Deleted clause from Qdrant: {clause_hash[:8]}")
            return True
        except Exception as e:
            logger.error(f"Error deleting clause: {e}")
            return False


# Singleton instance
_qdrant_service = None


def get_qdrant_service():
    """Get or create Qdrant service instance"""
    global _qdrant_service
    if _qdrant_service is None:
        _qdrant_service = QdrantService()
    return _qdrant_service
