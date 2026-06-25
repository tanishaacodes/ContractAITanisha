"""
RAG (Retrieval-Augmented Generation) Layer for Self-Healing Clause Library
Uses BM25 for initial retrieval + BERT for semantic reranking
"""

from rank_bm25 import BM25Okapi
import numpy as np
from typing import List, Dict, Any
from .embeddings import get_embedding_service


class ClauseRAG:
    """
    Retrieval-Augmented Generation for clause similarity search
    Two-stage approach:
    1. BM25: Fast keyword-based retrieval (top-K candidates)
    2. BERT: Semantic reranking for precision
    """

    def __init__(self, clauses: List[Dict[str, Any]]):
        """
        Initialize RAG with clause corpus

        Args:
            clauses: List of dicts with 'id', 'text', and other metadata
        """
        self.clauses = clauses
        self.texts = [c['text'] for c in clauses]

        # Tokenize for BM25
        self.tokenized = [text.lower().split() for text in self.texts]

        # Build BM25 index
        print(f"[INFO] Building BM25 index for {len(self.texts)} clauses...")
        self.bm25 = BM25Okapi(self.tokenized)

        # Embedding service for reranking
        self.embedding_service = get_embedding_service()

        print(f"[INFO] RAG initialized with {len(clauses)} clauses")

    def retrieve_bm25(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Stage 1: BM25 keyword-based retrieval

        Args:
            query: Search query text
            top_k: Number of candidates to retrieve

        Returns:
            List of top-K clause dicts with BM25 scores
        """
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        # Get top-K indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        # Build results
        results = []
        for idx in top_indices:
            clause = self.clauses[idx].copy()
            clause['bm25_score'] = float(scores[idx])
            results.append(clause)

        return results

    def rerank_bert(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Stage 2: BERT semantic reranking

        Args:
            query: Search query text
            candidates: List of candidate clauses from BM25

        Returns:
            Reranked list of clauses with semantic scores
        """
        if not candidates:
            return []

        # Generate query embedding
        query_emb = self.embedding_service.embed_semantic(query)

        # Score each candidate
        for candidate in candidates:
            clause_emb = self.embedding_service.embed_semantic(candidate['text'])
            semantic_score = self.embedding_service.similarity(query_emb, clause_emb)
            candidate['semantic_score'] = float(semantic_score)

            # Hybrid score (combine BM25 + semantic)
            bm25_normalized = min(candidate.get('bm25_score', 0) / 10, 1.0)
            candidate['hybrid_score'] = 0.4 * bm25_normalized + 0.6 * semantic_score

        # Sort by hybrid score
        candidates.sort(key=lambda x: x['hybrid_score'], reverse=True)

        return candidates

    def retrieve(self, query: str, top_k: int = 5, rerank: bool = True) -> List[Dict[str, Any]]:
        """
        Full two-stage retrieval: BM25 + BERT reranking

        Args:
            query: Search query text
            top_k: Number of final results to return
            rerank: Whether to apply BERT reranking (default: True)

        Returns:
            Top-K most relevant clauses
        """
        # Stage 1: BM25 retrieval (get more candidates for reranking)
        candidates = self.retrieve_bm25(query, top_k=min(top_k * 3, 50))

        # Stage 2: BERT reranking (optional)
        if rerank and candidates:
            candidates = self.rerank_bert(query, candidates)

        # Return top-K
        return candidates[:top_k]

    def find_similar_clauses(self, clause_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find clauses similar to a given clause text

        Args:
            clause_text: The clause to find similar ones for
            top_k: Number of similar clauses to return

        Returns:
            List of similar clauses with scores
        """
        return self.retrieve(clause_text, top_k=top_k, rerank=True)

    def find_by_outcome(self, query: str, outcome_type: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find clauses with specific outcome types (executed, disputed, etc.)

        Args:
            query: Search query
            outcome_type: Filter by event type ('EXECUTED', 'DISPUTED', etc.)
            top_k: Number of results

        Returns:
            Filtered and ranked clauses
        """
        # Retrieve candidates
        candidates = self.retrieve(query, top_k=top_k * 2, rerank=True)

        # Filter by outcome type if available
        if 'outcome_type' in candidates[0]:
            candidates = [c for c in candidates if c.get('outcome_type') == outcome_type]

        return candidates[:top_k]

    def get_clause_peers(self, clause_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Get peer clauses (similar clauses in the same category)

        Args:
            clause_id: ID of the reference clause
            top_k: Number of peers to return

        Returns:
            List of peer clauses
        """
        # Find the reference clause
        reference = next((c for c in self.clauses if c.get('id') == clause_id), None)
        if not reference:
            return []

        # Find similar clauses
        similar = self.find_similar_clauses(reference['text'], top_k=top_k + 1)

        # Exclude self
        similar = [c for c in similar if c.get('id') != clause_id]

        return similar[:top_k]


def build_rag_from_queryset(queryset) -> ClauseRAG:
    """
    Build RAG from Django QuerySet of Clause or ClauseVersion objects

    Args:
        queryset: Django QuerySet

    Returns:
        Initialized ClauseRAG instance
    """
    clauses = []
    for obj in queryset:
        clause_dict = {
            'id': str(obj.id),
            'text': getattr(obj, 'extracted_text', '') or getattr(obj, 'modified_text', '') or '',
            'clause_name': getattr(obj, 'clause_name', '') or getattr(obj, 'clause.clause_name', ''),
        }

        # Add optional fields if available
        if hasattr(obj, 'risk_score'):
            clause_dict['risk_score'] = obj.risk_score
        if hasattr(obj, 'clause_type'):
            clause_dict['clause_type'] = obj.clause_type

        clauses.append(clause_dict)

    return ClauseRAG(clauses)
