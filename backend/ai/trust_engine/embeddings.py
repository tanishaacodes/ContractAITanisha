"""
Trust Engine - Behavioral Clause Clustering

Clusters clauses by outcomes, not text.
Uses MiniLM for behavioral similarity detection.
"""
from sentence_transformers import SentenceTransformer
import numpy as np

# Lazy-loaded to avoid startup memory exhaustion on Windows
_model = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
    return _model


def embed_behavior(texts):
    """
    Embed clause behaviors for clustering.

    Args:
        texts: List of clause texts or single text

    Returns:
        numpy array of embeddings (384-dimensional)
    """
    if isinstance(texts, str):
        texts = [texts]
    return _get_model().encode(texts)


def behavioral_similarity(embedding_a, embedding_b):
    """
    Calculate cosine similarity between two behavioral embeddings.

    Args:
        embedding_a: First embedding vector
        embedding_b: Second embedding vector

    Returns:
        float: Similarity score (0-1)
    """
    a = np.array(embedding_a)
    b = np.array(embedding_b)

    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def find_similar_clauses(target_embedding, clause_embeddings, top_k=5):
    """
    Find clauses with similar behavioral patterns.

    Args:
        target_embedding: Target clause embedding
        clause_embeddings: List of (clause_id, embedding) tuples
        top_k: Number of similar clauses to return

    Returns:
        List of (clause_id, similarity_score) tuples
    """
    similarities = []

    for clause_id, embedding in clause_embeddings:
        sim = behavioral_similarity(target_embedding, embedding)
        similarities.append((clause_id, sim))

    # Sort by similarity (descending) and return top_k
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]
