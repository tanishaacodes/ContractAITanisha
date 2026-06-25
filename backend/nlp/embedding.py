"""
Clause Embedding Module
========================
Generates semantic embeddings for contract clauses using BERT models.

This module uses sentence-transformers to create dense vector representations
of clause text for semantic search and similarity analysis.
"""

from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class ClauseEmbedder:
    """
    BERT-based clause embedding generator.

    Uses sentence-transformers models to create semantic embeddings of contract clauses.
    Embeddings can be used for clustering, similarity search, and semantic retrieval.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the clause embedder with a pre-trained model.

        Args:
            model_name (str): Name of the sentence-transformers model to use.
                            Default: "all-MiniLM-L6-v2" (fast, good quality, 384 dimensions)
                            Alternatives:
                            - "all-mpnet-base-v2" (best quality, 768 dimensions, slower)
                            - "paraphrase-MiniLM-L3-v2" (fastest, 384 dimensions)
                            - "multi-qa-MiniLM-L6-cos-v1" (optimized for Q&A)
        """
        try:
            logger.info(f"Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name, device='cpu')
            self.model_name = model_name
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dimension}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def embed_single_clause(self, clause_text: str) -> List[float]:
        """
        Generate embedding for a single clause.

        Args:
            clause_text (str): The clause text to embed

        Returns:
            List[float]: Vector embedding of the clause

        Example:
            >>> embedder = ClauseEmbedder()
            >>> embedding = embedder.embed_single_clause("Payment shall be made within 30 days")
            >>> len(embedding)
            384
        """
        if not clause_text or not isinstance(clause_text, str):
            logger.warning("Empty or invalid clause text provided")
            return [0.0] * self.embedding_dimension

        try:
            # Normalize whitespace
            clause_text = " ".join(clause_text.split())

            # Generate embedding
            embedding = self.model.encode(clause_text, convert_to_numpy=True)

            # Convert to list for JSON serialization
            return embedding.tolist()

        except Exception as e:
            logger.error(f"Error embedding clause: {e}")
            return [0.0] * self.embedding_dimension

    def embed_clauses(self, clauses: List[str], batch_size: int = 32, show_progress: bool = False) -> List[List[float]]:
        """
        Generate embeddings for multiple clauses efficiently in batches.

        Args:
            clauses (List[str]): List of clause texts to embed
            batch_size (int): Number of clauses to process in each batch (default: 32)
            show_progress (bool): Whether to show progress bar (default: False)

        Returns:
            List[List[float]]: List of vector embeddings

        Example:
            >>> embedder = ClauseEmbedder()
            >>> clauses = ["Clause 1 text", "Clause 2 text", "Clause 3 text"]
            >>> embeddings = embedder.embed_clauses(clauses)
            >>> len(embeddings)
            3
        """
        if not clauses:
            logger.warning("Empty clauses list provided")
            return []

        try:
            # Normalize all clauses
            normalized_clauses = [" ".join(c.split()) if c else "" for c in clauses]

            # Generate embeddings in batches
            embeddings = self.model.encode(
                normalized_clauses,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )

            # Convert to list of lists for JSON serialization
            return [emb.tolist() for emb in embeddings]

        except Exception as e:
            logger.error(f"Error embedding clauses batch: {e}")
            # Return zero vectors as fallback
            return [[0.0] * self.embedding_dimension for _ in clauses]

    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1 (List[float]): First embedding vector
            embedding2 (List[float]): Second embedding vector

        Returns:
            float: Cosine similarity score between -1 and 1 (1 = identical, 0 = orthogonal, -1 = opposite)

        Example:
            >>> embedder = ClauseEmbedder()
            >>> emb1 = embedder.embed_single_clause("Payment terms")
            >>> emb2 = embedder.embed_single_clause("Invoice payment")
            >>> similarity = embedder.compute_similarity(emb1, emb2)
            >>> similarity > 0.5  # Should be similar
            True
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            # Cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return float(similarity)

        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return 0.0

    def find_most_similar(self, query_embedding: List[float],
                         candidate_embeddings: List[List[float]],
                         top_k: int = 5) -> List[tuple]:
        """
        Find the most similar clauses to a query clause.

        Args:
            query_embedding (List[float]): Embedding of the query clause
            candidate_embeddings (List[List[float]]): Embeddings of candidate clauses
            top_k (int): Number of top similar clauses to return

        Returns:
            List[tuple]: List of (index, similarity_score) tuples, sorted by similarity (descending)

        Example:
            >>> embedder = ClauseEmbedder()
            >>> query_emb = embedder.embed_single_clause("Payment terms")
            >>> candidates = embedder.embed_clauses(["Invoice payment", "Termination", "Liability"])
            >>> similar = embedder.find_most_similar(query_emb, candidates, top_k=2)
            >>> similar[0][0]  # Index of most similar
            0
        """
        try:
            similarities = []
            for idx, candidate_emb in enumerate(candidate_embeddings):
                similarity = self.compute_similarity(query_embedding, candidate_emb)
                similarities.append((idx, similarity))

            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)

            # Return top_k results
            return similarities[:top_k]

        except Exception as e:
            logger.error(f"Error finding similar clauses: {e}")
            return []


# Module-level singleton instance for convenience
_default_embedder = None


def get_embedder(model_name: str = "all-MiniLM-L6-v2") -> ClauseEmbedder:
    """
    Get or create the default embedder instance (singleton pattern).

    Args:
        model_name (str): Model name to use if creating new instance

    Returns:
        ClauseEmbedder: The embedder instance
    """
    global _default_embedder
    if _default_embedder is None:
        _default_embedder = ClauseEmbedder(model_name)
    return _default_embedder


def embed_clauses(clauses: List[str]) -> List[List[float]]:
    """
    Convenience function to embed clauses using the default embedder.

    Args:
        clauses (List[str]): List of clause texts

    Returns:
        List[List[float]]: List of embeddings

    Example:
        >>> from nlp.embedding import embed_clauses
        >>> embeddings = embed_clauses(["Clause 1", "Clause 2"])
        >>> len(embeddings)
        2
    """
    embedder = get_embedder()
    return embedder.embed_clauses(clauses)
