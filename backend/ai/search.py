"""
Semantic Search Engine for Clauses
Uses cosine similarity with MiniLM embeddings
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .embedding import embed

def search_clauses(query: str, clause_embeddings: dict):
    """
    Search for similar clauses using semantic similarity

    Args:
        query: Search query string
        clause_embeddings: Dictionary mapping clause_id to embedding vector

    Returns:
        List of tuples (clause_id, similarity_score) sorted by relevance
    """
    query_vec = np.array(embed(query)).reshape(1, -1)

    scores = []
    for clause_id, emb in clause_embeddings.items():
        emb_vec = np.array(emb).reshape(1, -1)
        score = cosine_similarity(query_vec, emb_vec)[0][0]
        scores.append((clause_id, float(score)))

    # Sort by similarity score (highest first)
    return sorted(scores, key=lambda x: x[1], reverse=True)

def find_similar_clauses(target_embedding, all_embeddings: dict, top_k: int = 5):
    """
    Find most similar clauses to a target clause

    Args:
        target_embedding: Embedding vector of target clause
        all_embeddings: Dictionary of clause_id -> embedding
        top_k: Number of similar clauses to return

    Returns:
        List of (clause_id, similarity_score) tuples
    """
    target_vec = np.array(target_embedding).reshape(1, -1)

    scores = []
    for clause_id, emb in all_embeddings.items():
        emb_vec = np.array(emb).reshape(1, -1)
        score = cosine_similarity(target_vec, emb_vec)[0][0]
        scores.append((clause_id, float(score)))

    # Sort and return top K
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]
