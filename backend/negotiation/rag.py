"""
RAG Layer for Negotiation Co-Pilot
Uses BM25 for clause retrieval and similarity search
"""
from rank_bm25 import BM25Okapi
import logging
import numpy as np

logger = logging.getLogger(__name__)

class NegotiationRAG:
    """
    Retrieval-Augmented Generation for clause suggestions
    
    Uses BM25 for keyword-based retrieval and embeddings for semantic similarity
    """
    
    def __init__(self, clauses=None):
        """
        Initialize RAG with clause database
        
        Args:
            clauses: List of Clause objects or None to lazy-load
        """
        self.clauses = clauses
        self.bm25 = None
        self.tokenized_corpus = None
        self._initialized = False
    
    def initialize(self):
        """Lazy initialization of BM25 index"""
        if self._initialized:
            return
        
        if self.clauses is None:
            from core.models import Clause
            self.clauses = list(Clause.objects.all())
        
        if not self.clauses:
            logger.warning("No clauses available for RAG")
            return
        
        # Build BM25 index
        logger.info(f"Building BM25 index for {len(self.clauses)} clauses...")
        
        self.texts = []
        for clause in self.clauses:
            text = clause.extracted_text or clause.context_sentences or clause.clause_name or ''
            self.texts.append(text)
        
        # Tokenize
        self.tokenized_corpus = [text.lower().split() for text in self.texts]
        
        # Create BM25 index
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        
        self._initialized = True
        logger.info("BM25 index built successfully")
    
    def fetch_similar_clauses(self, query, top_k=5):
        """
        Fetch similar clauses using BM25
        
        Args:
            query: Search query text
            top_k: Number of results to return
        
        Returns:
            List of dicts with {id, name, text, score}
        """
        self.initialize()
        
        if not self._initialized:
            return []
        
        # Tokenize query
        query_tokens = query.lower().split()
        
        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include clauses with positive scores
                clause = self.clauses[idx]
                results.append({
                    'id': clause.id,
                    'name': clause.clause_name,
                    'text': self.texts[idx][:200] + '...' if len(self.texts[idx]) > 200 else self.texts[idx],
                    'score': float(scores[idx]),
                    'clause_type': clause.clause_type or 'general',
                    'risk_score': clause.risk_score or 0.5
                })
        
        return results
    
    def fetch_by_clause_type(self, clause_type, top_k=5):
        """
        Fetch clauses of a specific type
        
        Args:
            clause_type: Clause type to filter by
            top_k: Number of results to return
        
        Returns:
            List of matching clauses
        """
        self.initialize()
        
        if not self._initialized:
            return []
        
        matching = []
        for clause in self.clauses:
            if clause.clause_type == clause_type or clause.clause_name == clause_type:
                matching.append({
                    'id': clause.id,
                    'name': clause.clause_name,
                    'text': (clause.extracted_text or clause.context_sentences or '')[:200],
                    'clause_type': clause.clause_type,
                    'risk_score': clause.risk_score or 0.5
                })
        
        return matching[:top_k]
    
    def fetch_low_risk_alternatives(self, clause_type, top_k=3):
        """
        Fetch low-risk alternatives for a clause type
        
        Args:
            clause_type: Type of clause to find alternatives for
            top_k: Number of alternatives
        
        Returns:
            List of low-risk clause alternatives
        """
        self.initialize()
        
        if not self._initialized:
            return []
        
        # Get clauses of same type
        same_type = []
        for clause in self.clauses:
            if clause.clause_type == clause_type or clause.clause_name == clause_type:
                risk = clause.risk_score or 0.5
                if risk < 0.5:  # Low risk threshold
                    same_type.append({
                        'id': clause.id,
                        'name': clause.clause_name,
                        'text': (clause.extracted_text or clause.context_sentences or '')[:200],
                        'risk_score': risk,
                        'reason': f"Low risk ({risk:.0%}) alternative for {clause_type}"
                    })
        
        # Sort by risk score (lowest first)
        same_type.sort(key=lambda x: x['risk_score'])
        
        return same_type[:top_k]


# Global RAG instance (lazy-loaded)
_rag_instance = None


def get_rag():
    """Get or create global RAG instance"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = NegotiationRAG()
    return _rag_instance
