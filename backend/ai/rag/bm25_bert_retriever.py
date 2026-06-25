"""
BM25 + BERT Hybrid RAG Retriever
==================================
Production-grade retrieval system combining lexical (BM25) and semantic (BERT) search.

Architecture:
1. BM25 (lexical) - Fast keyword matching for exact terms
2. BERT embeddings (semantic) - Captures meaning and context
3. Reciprocal Rank Fusion (RRF) - Combines both rankings

Use cases:
- Clause library search
- Similar clause retrieval
- Contract precedent lookup
- Risk pattern matching

Author: PrimeContractAI System
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import re
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

# Module-level singleton to avoid loading SentenceTransformer twice
# (second load triggers PyTorch meta tensor error on 2.x)
_EMBEDDER_CACHE: dict = {}


def _get_embedder(model_name: str):
    """Return cached SentenceTransformer instance, loading once per model name."""
    if model_name not in _EMBEDDER_CACHE:
        try:
            _EMBEDDER_CACHE[model_name] = SentenceTransformer(model_name, device="cpu")
            logger.info(f"[RAG] Loaded BERT model: {model_name}")
        except Exception as e:
            logger.error(f"[RAG] Failed to load BERT model: {e}")
            _EMBEDDER_CACHE[model_name] = None
    return _EMBEDDER_CACHE[model_name]


class BM25BERTRetriever:
    """
    Hybrid retriever combining BM25 (lexical) and BERT (semantic) search.

    Uses Reciprocal Rank Fusion (RRF) to merge results.
    """

    def __init__(
        self,
        documents: Optional[List[Dict[str, Any]]] = None,
        embedding_model: str = "all-MiniLM-L6-v2",
        bm25_weight: float = 0.5,
        bert_weight: float = 0.5
    ):
        """
        Args:
            documents: List of documents with 'text' and 'id' fields
            embedding_model: Sentence transformer model name
            bm25_weight: Weight for BM25 scores (0-1)
            bert_weight: Weight for BERT scores (0-1)
        """
        self.bm25_weight = bm25_weight
        self.bert_weight = bert_weight

        # Use cached singleton — prevents meta tensor error on second instantiation
        self.embedder = _get_embedder(embedding_model)

        # Initialize storage
        self.documents = []
        self.doc_embeddings = None
        self.bm25 = None

        # Index documents if provided
        if documents:
            self.index_documents(documents)

    def index_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Index documents for both BM25 and BERT retrieval.

        Args:
            documents: List of dicts with 'text', 'id', and optional metadata
        """
        if not documents:
            logger.warning("[RAG] No documents to index")
            return

        self.documents = documents

        # Extract text and IDs
        texts = [doc.get('text', '') for doc in documents]

        # Build BM25 index
        tokenized_texts = [self._tokenize(text) for text in texts]
        self.bm25 = BM25Okapi(tokenized_texts)
        logger.info(f"[RAG] Indexed {len(documents)} documents in BM25")

        # Build BERT embeddings
        if self.embedder:
            try:
                self.doc_embeddings = self.embedder.encode(
                    texts,
                    show_progress_bar=False,
                    convert_to_numpy=True
                )
                logger.info(f"[RAG] Generated {len(self.doc_embeddings)} BERT embeddings")
            except Exception as e:
                logger.error(f"[RAG] BERT embedding failed: {e}")
                self.doc_embeddings = None

    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search using BM25 + BERT with RRF fusion.

        Args:
            query: Search query string
            top_k: Number of results to return
            min_score: Minimum fusion score threshold

        Returns:
            List of results with scores and metadata
        """
        if not self.documents:
            logger.warning("[RAG] No documents indexed")
            return []

        # Get BM25 results
        bm25_results = self._bm25_search(query, top_k * 2)  # Retrieve more for fusion

        # Get BERT results
        bert_results = self._bert_search(query, top_k * 2) if self.embedder else []

        # Fuse results using Reciprocal Rank Fusion
        fused_results = self._reciprocal_rank_fusion(
            bm25_results,
            bert_results,
            top_k
        )

        # Filter by minimum score
        filtered_results = [
            r for r in fused_results
            if r['fusion_score'] >= min_score
        ]

        return filtered_results[:top_k]

    def _bm25_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """BM25 lexical search"""
        if not self.bm25:
            return []

        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(top_indices):
            if scores[idx] > 0:  # Only include positive scores
                results.append({
                    'doc_id': self.documents[idx].get('id', idx),
                    'document': self.documents[idx],
                    'bm25_score': float(scores[idx]),
                    'bm25_rank': rank + 1
                })

        return results

    def _bert_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """BERT semantic search"""
        if not self.embedder or self.doc_embeddings is None:
            return []

        try:
            # Embed query
            query_embedding = self.embedder.encode(
                query,
                convert_to_numpy=True
            )

            # Calculate cosine similarity
            similarities = np.dot(self.doc_embeddings, query_embedding) / (
                np.linalg.norm(self.doc_embeddings, axis=1) *
                np.linalg.norm(query_embedding)
            )

            # Get top-k indices
            top_indices = np.argsort(similarities)[::-1][:top_k]

            results = []
            for rank, idx in enumerate(top_indices):
                if similarities[idx] > 0:  # Only include positive similarities
                    results.append({
                        'doc_id': self.documents[idx].get('id', idx),
                        'document': self.documents[idx],
                        'bert_score': float(similarities[idx]),
                        'bert_rank': rank + 1
                    })

            return results

        except Exception as e:
            logger.error(f"[RAG] BERT search failed: {e}")
            return []

    def _reciprocal_rank_fusion(
        self,
        bm25_results: List[Dict[str, Any]],
        bert_results: List[Dict[str, Any]],
        top_k: int,
        k: int = 60  # RRF constant
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF) algorithm.

        RRF Score = Σ (1 / (k + rank)) for each retriever
        """
        # Build score dictionaries
        bm25_scores = {r['doc_id']: 1 / (k + r['bm25_rank']) for r in bm25_results}
        bert_scores = {r['doc_id']: 1 / (k + r['bert_rank']) for r in bert_results}

        # Combine all doc IDs
        all_doc_ids = set(bm25_scores.keys()) | set(bert_scores.keys())

        # Calculate fusion scores
        fusion_results = []
        doc_map = {r['doc_id']: r for r in bm25_results + bert_results}

        for doc_id in all_doc_ids:
            bm25_rrf = bm25_scores.get(doc_id, 0) * self.bm25_weight
            bert_rrf = bert_scores.get(doc_id, 0) * self.bert_weight

            fusion_score = bm25_rrf + bert_rrf

            # Get document data
            doc_data = doc_map.get(doc_id, {})

            fusion_results.append({
                'doc_id': doc_id,
                'document': doc_data.get('document', {}),
                'fusion_score': float(fusion_score),
                'bm25_score': doc_data.get('bm25_score', 0.0),
                'bert_score': doc_data.get('bert_score', 0.0),
                'retrieval_method': self._get_retrieval_method(
                    bm25_scores.get(doc_id, 0),
                    bert_scores.get(doc_id, 0)
                )
            })

        # Sort by fusion score
        fusion_results.sort(key=lambda x: x['fusion_score'], reverse=True)

        return fusion_results[:top_k]

    def _get_retrieval_method(self, bm25_score: float, bert_score: float) -> str:
        """Determine which retrieval method contributed most"""
        if bm25_score > 0 and bert_score > 0:
            return "hybrid"
        elif bm25_score > 0:
            return "lexical"
        elif bert_score > 0:
            return "semantic"
        else:
            return "unknown"

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25.

        Uses simple whitespace + lowercase + alphanumeric filtering.
        """
        # Lowercase and split
        text = text.lower()

        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)

        # Split and filter empty tokens
        tokens = [t for t in text.split() if t]

        return tokens

    def add_documents(self, new_documents: List[Dict[str, Any]]) -> None:
        """
        Add new documents to the index.

        Note: This requires full re-indexing. For large-scale updates,
        consider incremental indexing strategies.
        """
        self.documents.extend(new_documents)
        self.index_documents(self.documents)
        logger.info(f"[RAG] Added {len(new_documents)} documents, total: {len(self.documents)}")

    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document by ID"""
        for doc in self.documents:
            if doc.get('id') == doc_id:
                return doc
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get retriever statistics"""
        return {
            'total_documents': len(self.documents),
            'bm25_indexed': self.bm25 is not None,
            'bert_indexed': self.doc_embeddings is not None,
            'embedding_dim': self.doc_embeddings.shape[1] if self.doc_embeddings is not None else 0,
            'bm25_weight': self.bm25_weight,
            'bert_weight': self.bert_weight
        }


# Convenience functions
def create_clause_retriever(clauses: List[Any]) -> BM25BERTRetriever:
    """
    Create retriever from clause objects.

    Args:
        clauses: List of Clause model instances or dicts

    Returns:
        Configured BM25BERTRetriever
    """
    documents = []

    for clause in clauses:
        # Handle both model instances and dicts
        if hasattr(clause, 'id'):
            doc_id = clause.id
            text = (
                getattr(clause, 'extracted_text', '') or
                getattr(clause, 'context_sentences', '') or
                getattr(clause, 'text_spans', '') or
                ''
            )
            metadata = {
                'clause_name': getattr(clause, 'clause_name', ''),
                'clause_type': getattr(clause, 'clause_type', ''),
                'risk_score': getattr(clause, 'risk_score', 0.0),
                'contract_id': getattr(clause, 'contract_id', '')
            }
        else:
            doc_id = clause.get('id')
            text = (
                clause.get('extracted_text', '') or
                clause.get('context_sentences', '') or
                clause.get('text_spans', '') or
                ''
            )
            metadata = {
                'clause_name': clause.get('clause_name', ''),
                'clause_type': clause.get('clause_type', ''),
                'risk_score': clause.get('risk_score', 0.0),
                'contract_id': clause.get('contract_id', '')
            }

        documents.append({
            'id': doc_id,
            'text': text,
            **metadata
        })

    return BM25BERTRetriever(documents=documents)


def search_similar_clauses(
    query_clause: Any,
    all_clauses: List[Any],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Find clauses similar to a query clause.

    Args:
        query_clause: Clause to find similar clauses for
        all_clauses: All clauses to search through
        top_k: Number of similar clauses to return

    Returns:
        List of similar clauses with scores
    """
    retriever = create_clause_retriever(all_clauses)

    # Get query text
    if hasattr(query_clause, 'extracted_text'):
        query_text = query_clause.extracted_text or ''
    else:
        query_text = query_clause.get('extracted_text', '')

    # Search
    results = retriever.search(query_text, top_k=top_k + 1)  # +1 to exclude self

    # Filter out the query clause itself
    query_id = query_clause.id if hasattr(query_clause, 'id') else query_clause.get('id')
    filtered_results = [r for r in results if r['doc_id'] != query_id]

    return filtered_results[:top_k]
