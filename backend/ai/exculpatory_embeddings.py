"""
Exculpatory Clause Embeddings
Generates MiniLM embeddings for clause similarity matching
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union

# Lazy-loaded to avoid startup memory exhaustion on Windows
_model = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
    return _model


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for a single text.

    Args:
        text: Input text to embed

    Returns:
        List of floats representing the embedding vector
    """
    embedding = _get_model().encode(text, convert_to_numpy=True)
    return embedding.tolist()


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in batch.

    Args:
        texts: List of input texts

    Returns:
        List of embedding vectors
    """
    embeddings = _get_model().encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings.tolist()


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First embedding vector
        vec2: Second embedding vector

    Returns:
        Similarity score between 0 and 1
    """
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)

    dot_product = np.dot(vec1_np, vec2_np)
    norm1 = np.linalg.norm(vec1_np)
    norm2 = np.linalg.norm(vec2_np)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    similarity = dot_product / (norm1 * norm2)
    return float(similarity)


def find_most_similar(query_embedding: List[float],
                     candidate_embeddings: List[List[float]],
                     top_k: int = 3,
                     threshold: float = 0.0) -> List[tuple]:
    """
    Find most similar embeddings to a query.

    Args:
        query_embedding: Query embedding vector
        candidate_embeddings: List of candidate embedding vectors
        top_k: Number of top results to return
        threshold: Minimum similarity threshold

    Returns:
        List of (index, similarity_score) tuples
    """
    similarities = []

    for idx, candidate in enumerate(candidate_embeddings):
        similarity = cosine_similarity(query_embedding, candidate)
        if similarity >= threshold:
            similarities.append((idx, similarity))

    # Sort by similarity (descending) and return top_k
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]
