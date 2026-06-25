"""
Vector Database Module for Contract AI
=======================================
Vector database integrations for semantic search and storage.
"""

from .qdrant_store import (
    QdrantStore,
    get_qdrant_store,
    store_embeddings,
    search_similar_clauses
)

__all__ = [
    'QdrantStore',
    'get_qdrant_store',
    'store_embeddings',
    'search_similar_clauses'
]
