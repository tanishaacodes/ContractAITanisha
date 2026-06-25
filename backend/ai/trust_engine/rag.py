"""
Trust Engine - RAG (Retrieval-Augmented Generation)

BM25-based retrieval of similar clause outcomes for trust scoring.
Provides historical memory for trust predictions.
"""
from rank_bm25 import BM25Okapi


class TrustRAG:
    """
    RAG system for finding clauses with similar historical outcomes.
    Uses BM25 for fast keyword-based retrieval.
    """

    def __init__(self, clauses):
        """
        Initialize RAG with clause corpus.

        Args:
            clauses: QuerySet or list of Clause objects with .text attribute
        """
        self.clauses = list(clauses)
        self.texts = [c.clause_text if hasattr(c, 'clause_text') else str(c) for c in self.clauses]
        self.tokenized = [self._tokenize(text) for text in self.texts]

        # Initialize BM25
        if self.tokenized:
            self.bm25 = BM25Okapi(self.tokenized)
        else:
            self.bm25 = None

    def _tokenize(self, text):
        """Simple whitespace tokenization."""
        return text.lower().split()

    def similar_outcomes(self, query, top_k=5):
        """
        Find clauses with similar text and retrieve their outcomes.

        Args:
            query: Clause text to search for
            top_k: Number of similar clauses to return

        Returns:
            list: Similar clauses sorted by relevance
        """
        if not self.bm25 or not self.clauses:
            return []

        # Tokenize query
        query_tokens = self._tokenize(query)

        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)

        # Get top-k indices
        import numpy as np
        top_indices = np.argsort(scores)[::-1][:top_k]

        # Return clauses with scores
        results = []
        for idx in top_indices:
            if idx < len(self.clauses):
                results.append({
                    "clause": self.clauses[idx],
                    "score": float(scores[idx]),
                    "text": self.texts[idx]
                })

        return results

    def retrieve_trust_precedents(self, query, min_score=1.0):
        """
        Retrieve clauses with known trust scores for comparison.

        Args:
            query: Clause text
            min_score: Minimum BM25 score threshold

        Returns:
            list: Precedent clauses with trust data
        """
        results = self.similar_outcomes(query, top_k=10)

        # Filter by minimum score
        precedents = [r for r in results if r["score"] >= min_score]

        return precedents

    def aggregate_trust_from_similar(self, query, top_k=5):
        """
        Aggregate trust scores from similar clauses.

        Useful for estimating trust when a clause has no direct history.

        Args:
            query: Clause text
            top_k: Number of similar clauses to consider

        Returns:
            dict: Aggregated trust metrics
        """
        similar = self.similar_outcomes(query, top_k=top_k)

        if not similar:
            return {
                "estimated_trust": 0.5,
                "confidence": 0.0,
                "sample_size": 0
            }

        # Aggregate trust scores (assuming clauses have health_metrics)
        trust_scores = []
        for result in similar:
            clause = result["clause"]
            if hasattr(clause, 'health_metrics') and clause.health_metrics:
                # Use health_score as proxy for trust if trust_score not available
                score = getattr(clause.health_metrics, 'trust_score', None) or \
                        getattr(clause.health_metrics, 'health_score', 0.5)
                trust_scores.append(score)

        if not trust_scores:
            return {
                "estimated_trust": 0.5,
                "confidence": 0.0,
                "sample_size": 0
            }

        # Calculate weighted average (weight by BM25 score)
        import numpy as np
        weights = [r["score"] for r in similar if len(trust_scores) > 0]
        avg_trust = np.average(trust_scores, weights=weights[:len(trust_scores)])

        # Confidence based on sample size and score agreement
        confidence = min(1.0, len(trust_scores) / top_k)

        return {
            "estimated_trust": round(float(avg_trust), 3),
            "confidence": round(confidence, 3),
            "sample_size": len(trust_scores),
            "similar_clauses": [r["clause"].id if hasattr(r["clause"], 'id') else None for r in similar]
        }
