"""
LegalBERT Semantic Embeddings Service
=======================================
Generates dense vector embeddings for arbitration clauses using LegalBERT.
Enables semantic similarity search and improved clause relationship discovery.

Model: nlpaueb/legal-bert-base-uncased (768 dimensions)
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
import torch

try:
    from transformers import AutoModel, AutoTokenizer
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)


class LegalBERTEmbeddingService:
    """
    Singleton service for generating LegalBERT embeddings.
    Loads model once and reuses for all clause embedding operations.
    """

    _instance = None
    _model = None
    _tokenizer = None
    _device = None
    _load_attempted = False  # Prevent infinite retry on failure

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize LegalBERT model (lazy loading, one attempt only)."""
        if not _TRANSFORMERS_AVAILABLE:
            logger.warning("transformers library not available. LegalBERT embeddings disabled.")
            return

        # Only attempt load once — don't retry on every request if it failed
        if self._load_attempted:
            return
        self._load_attempted = True

        try:
            logger.info("Loading LegalBERT model: nlpaueb/legal-bert-base-uncased")
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self._tokenizer = AutoTokenizer.from_pretrained("nlpaueb/legal-bert-base-uncased")
            self._model = AutoModel.from_pretrained(
                "nlpaueb/legal-bert-base-uncased",
                low_cpu_mem_usage=False,
            )
            self._model.to(self._device)
            self._model.eval()
            logger.info(f"LegalBERT loaded successfully on device: {self._device}")
        except Exception as e:
            logger.error(f"Failed to load LegalBERT: {e}. Running without LegalBERT (fallback active).")
            self._model = None
            self._tokenizer = None

    def is_available(self) -> bool:
        """Check if LegalBERT model is loaded and available."""
        return self._model is not None and self._tokenizer is not None

    def generate_embedding(self, text: str, max_length: int = 512) -> Optional[np.ndarray]:
        """
        Generate 768-dimensional LegalBERT embedding for a single text.

        Args:
            text: Input text (clause or contract segment)
            max_length: Maximum token length (default 512)

        Returns:
            numpy array of shape (768,) or None if model unavailable
        """
        if not self.is_available():
            return None

        try:
            # Tokenize
            inputs = self._tokenizer(
                text,
                return_tensors="pt",
                max_length=max_length,
                truncation=True,
                padding=True,
            )
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            # Generate embeddings (no gradient computation)
            with torch.no_grad():
                outputs = self._model(**inputs)

            # Use [CLS] token embedding (first token)
            # Alternative: mean pooling of all tokens
            cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze()

            # Convert to numpy
            embedding = cls_embedding.cpu().numpy()

            return embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None

    def generate_embeddings_batch(
        self, texts: List[str], max_length: int = 512, batch_size: int = 16
    ) -> List[Optional[np.ndarray]]:
        """
        Generate embeddings for multiple texts in batches (more efficient).

        Args:
            texts: List of input texts
            max_length: Maximum token length
            batch_size: Number of texts to process per batch

        Returns:
            List of numpy arrays (768,) or None for each text
        """
        if not self.is_available():
            return [None] * len(texts)

        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]

            try:
                # Tokenize batch
                inputs = self._tokenizer(
                    batch_texts,
                    return_tensors="pt",
                    max_length=max_length,
                    truncation=True,
                    padding=True,
                )
                inputs = {k: v.to(self._device) for k, v in inputs.items()}

                # Generate embeddings
                with torch.no_grad():
                    outputs = self._model(**inputs)

                # Extract [CLS] embeddings
                batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()

                embeddings.extend(list(batch_embeddings))

            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")
                embeddings.extend([None] * len(batch_texts))

        return embeddings

    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector (768,)
            embedding2: Second embedding vector (768,)

        Returns:
            Cosine similarity score 0.0-1.0
        """
        if embedding1 is None or embedding2 is None:
            return 0.0

        try:
            # Cosine similarity
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)

            # Clamp to [0, 1] range
            return float(max(0.0, min(1.0, similarity)))

        except Exception as e:
            logger.error(f"Similarity computation failed: {e}")
            return 0.0

    def find_similar_clauses(
        self,
        query_embedding: np.ndarray,
        clause_embeddings: List[Tuple[int, np.ndarray]],
        top_k: int = 5,
        min_similarity: float = 0.65,
    ) -> List[Dict]:
        """
        Find most similar clauses to a query embedding.

        Args:
            query_embedding: Query vector (768,)
            clause_embeddings: List of (clause_id, embedding) tuples
            top_k: Number of top results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of dicts with {clause_id, similarity}
        """
        if query_embedding is None:
            return []

        similarities = []

        for clause_id, clause_emb in clause_embeddings:
            if clause_emb is None:
                continue

            sim = self.compute_similarity(query_embedding, clause_emb)

            if sim >= min_similarity:
                similarities.append({"clause_id": clause_id, "similarity": round(sim, 4)})

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x["similarity"], reverse=True)

        return similarities[:top_k]


# Global singleton instance
_legalbert_service = None


def get_legalbert_service() -> LegalBERTEmbeddingService:
    """Get or create the global LegalBERT service instance."""
    global _legalbert_service
    if _legalbert_service is None:
        _legalbert_service = LegalBERTEmbeddingService()
    return _legalbert_service


# Convenience functions

def generate_clause_embedding(clause_text: str) -> Optional[List[float]]:
    """
    Generate embedding for a clause and return as Python list (for JSON storage).

    Args:
        clause_text: Clause text

    Returns:
        List of 768 float values or None
    """
    service = get_legalbert_service()
    embedding = service.generate_embedding(clause_text)

    if embedding is not None:
        return embedding.tolist()

    return None


def generate_clause_embeddings_batch(clause_texts: List[str]) -> List[Optional[List[float]]]:
    """
    Generate embeddings for multiple clauses.

    Args:
        clause_texts: List of clause texts

    Returns:
        List of embedding lists (768,) or None for each clause
    """
    service = get_legalbert_service()
    embeddings = service.generate_embeddings_batch(clause_texts)

    return [emb.tolist() if emb is not None else None for emb in embeddings]


def find_semantic_duplicates(
    clauses: List[Dict],
    similarity_threshold: float = 0.85,
) -> List[Tuple[int, int, float]]:
    """
    Find semantically duplicate clauses based on LegalBERT embeddings.

    Args:
        clauses: List of dicts with {id, text, embedding}
        similarity_threshold: Minimum similarity to consider duplicate

    Returns:
        List of (clause1_id, clause2_id, similarity) tuples
    """
    service = get_legalbert_service()
    duplicates = []

    for i in range(len(clauses)):
        for j in range(i + 1, len(clauses)):
            emb1 = clauses[i].get("embedding")
            emb2 = clauses[j].get("embedding")

            if emb1 is None or emb2 is None:
                continue

            # Convert from list to numpy if needed
            if isinstance(emb1, list):
                emb1 = np.array(emb1)
            if isinstance(emb2, list):
                emb2 = np.array(emb2)

            sim = service.compute_similarity(emb1, emb2)

            if sim >= similarity_threshold:
                duplicates.append((clauses[i]["id"], clauses[j]["id"], round(sim, 4)))

    return duplicates


def discover_semantic_relationships(
    clauses: List[Dict], similarity_threshold: float = 0.70
) -> List[Dict]:
    """
    Discover semantic relationships between clauses using LegalBERT.
    Complements regex-based pattern matching with semantic similarity.

    Args:
        clauses: List of dicts with {id, text, embedding}
        similarity_threshold: Minimum similarity for relationship

    Returns:
        List of relationship dicts {from_id, to_id, type, weight}
    """
    service = get_legalbert_service()
    relationships = []

    for i in range(len(clauses)):
        for j in range(i + 1, len(clauses)):
            emb1 = clauses[i].get("embedding")
            emb2 = clauses[j].get("embedding")

            if emb1 is None or emb2 is None:
                continue

            if isinstance(emb1, list):
                emb1 = np.array(emb1)
            if isinstance(emb2, list):
                emb2 = np.array(emb2)

            sim = service.compute_similarity(emb1, emb2)

            if sim >= similarity_threshold:
                # Classify relationship type based on similarity strength
                if sim >= 0.90:
                    rel_type = "SEMANTICALLY_EQUIVALENT"
                elif sim >= 0.80:
                    rel_type = "STRONGLY_RELATED"
                elif sim >= 0.70:
                    rel_type = "RELATED_TO"
                else:
                    rel_type = "WEAKLY_RELATED"

                relationships.append({
                    "from_id": clauses[i]["id"],
                    "to_id": clauses[j]["id"],
                    "type": rel_type,
                    "weight": round(sim, 4),
                })

    return relationships
