"""
RAG (Retrieval-Augmented Generation) Module
============================================
Hybrid retrieval system combining lexical and semantic search.
"""

from .bm25_bert_retriever import (
    BM25BERTRetriever,
    create_clause_retriever,
    search_similar_clauses
)

__all__ = [
    'BM25BERTRetriever',
    'create_clause_retriever',
    'search_similar_clauses'
]
