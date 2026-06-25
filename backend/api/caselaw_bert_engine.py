"""
CaseLaw-BERT Engine for Legal Document Embeddings
==================================================
Implements:
- Legal-BERT embeddings for case law and clauses
- FAISS vector index for fast similarity search
- Cross-encoder reranking for precision
- Hybrid search (BM25 + semantic)
- Jurisdiction-aware retrieval
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
import torch
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Import transformers
try:
    from transformers import AutoTokenizer, AutoModel
    from sentence_transformers import SentenceTransformer, CrossEncoder
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("transformers or sentence_transformers not available. Using fallback embeddings.")
    TRANSFORMERS_AVAILABLE = False

# Import FAISS
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    logger.warning("FAISS not available. Using numpy-based similarity search.")
    FAISS_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# CASE LAW BERT MODEL
# ═══════════════════════════════════════════════════════════════

@dataclass
class CaseDocument:
    """Case law document structure."""
    case_id: str
    title: str
    text: str
    jurisdiction: str
    year: int
    court: str
    outcome: str = ""
    tags: List[str] = None
    embedding: np.ndarray = None


@dataclass
class SearchResult:
    """Search result with relevance score."""
    case: CaseDocument
    score: float
    reranked_score: Optional[float] = None
    rank: int = 0


class CaseLawBERT:
    """
    CaseLaw-BERT model for generating legal document embeddings.
    Uses legal-bert-base-uncased or similar legal domain model.
    """

    def __init__(
        self,
        model_name: str = "nlpaueb/legal-bert-base-uncased",
        use_sentence_transformer: bool = True
    ):
        """
        Initialize CaseLaw-BERT model.

        Args:
            model_name: HuggingFace model name or path
            use_sentence_transformer: Use SentenceTransformer for easier embeddings
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Using fallback embeddings - install transformers for better results")
            self.model = None
            self.tokenizer = None
            return

        try:
            if use_sentence_transformer:
                # Use sentence-transformers for easier embedding generation
                self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu')
                self.tokenizer = None
                logger.info(f"Loaded SentenceTransformer model")
            else:
                # Use base transformers
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModel.from_pretrained(model_name, low_cpu_mem_usage=False)
                self.model.to(self.device)
                self.model.eval()
                logger.info(f"Loaded {model_name} on {self.device}")
        except Exception as e:
            logger.error(f"Error loading model: {e}. Using fallback.")
            self.model = None
            self.tokenizer = None

    def embed(self, text: str) -> np.ndarray:
        """
        Generate embedding for text.

        Args:
            text: Input text

        Returns:
            Embedding vector as numpy array
        """
        if self.model is None:
            # Fallback: simple hash-based embedding
            return self._fallback_embedding(text)

        if isinstance(self.model, SentenceTransformer):
            # SentenceTransformer path
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding

        # Base transformers path
        try:
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)

            # Mean pooling
            embeddings = outputs.last_hidden_state.mean(dim=1)
            return embeddings.squeeze().cpu().numpy()

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return self._fallback_embedding(text)

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of input texts
            batch_size: Batch size for processing

        Returns:
            Array of embeddings
        """
        if isinstance(self.model, SentenceTransformer):
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=True
            )
            return embeddings

        # Process in batches manually
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = [self.embed(text) for text in batch]
            all_embeddings.extend(batch_embeddings)

        return np.array(all_embeddings)

    def _fallback_embedding(self, text: str, dim: int = 384) -> np.ndarray:
        """Simple fallback embedding using text hash."""
        # Create deterministic embedding from text
        text_hash = hash(text.lower()[:1000])
        np.random.seed(abs(text_hash) % (2**32))
        embedding = np.random.randn(dim).astype(np.float32)
        # Normalize
        embedding = embedding / np.linalg.norm(embedding)
        return embedding


# ═══════════════════════════════════════════════════════════════
# FAISS VECTOR INDEX
# ═══════════════════════════════════════════════════════════════

class CaseLawIndex:
    """
    FAISS-based vector index for case law similarity search.
    Supports:
    - Fast approximate nearest neighbor search
    - Jurisdiction filtering
    - Metadata storage
    """

    def __init__(self, embedding_dim: int = 384):
        """
        Initialize FAISS index.

        Args:
            embedding_dim: Dimension of embeddings
        """
        self.embedding_dim = embedding_dim
        self.metadata: List[CaseDocument] = []

        if FAISS_AVAILABLE:
            # Use FAISS IndexFlatL2 for exact search
            # For large datasets, use IndexIVFFlat or IndexHNSWFlat
            self.index = faiss.IndexFlatL2(embedding_dim)
            logger.info(f"Initialized FAISS index with dimension {embedding_dim}")
        else:
            # Fallback: store embeddings in numpy array
            self.index = None
            self.embeddings = []
            logger.info("Using numpy-based similarity search (slower than FAISS)")

    def add_case(
        self,
        case: CaseDocument,
        embedding: np.ndarray
    ):
        """
        Add case document to index.

        Args:
            case: Case document metadata
            embedding: Embedding vector
        """
        # Store metadata
        self.metadata.append(case)

        # Add to index
        if FAISS_AVAILABLE and self.index is not None:
            # FAISS requires float32
            embedding_f32 = embedding.astype(np.float32).reshape(1, -1)
            self.index.add(embedding_f32)
        else:
            self.embeddings.append(embedding)

    def add_cases_batch(self, cases: List[CaseDocument], embeddings: np.ndarray):
        """
        Add multiple cases in batch.

        Args:
            cases: List of case documents
            embeddings: Array of embeddings (n_cases x embedding_dim)
        """
        for case in cases:
            self.metadata.append(case)

        if FAISS_AVAILABLE and self.index is not None:
            embeddings_f32 = embeddings.astype(np.float32)
            self.index.add(embeddings_f32)
        else:
            self.embeddings.extend(list(embeddings))

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        jurisdiction: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Search for similar cases.

        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            jurisdiction: Optional jurisdiction filter

        Returns:
            List of search results with scores
        """
        if FAISS_AVAILABLE and self.index is not None:
            # FAISS search
            query_f32 = query_embedding.astype(np.float32).reshape(1, -1)
            distances, indices = self.index.search(query_f32, k * 2)  # Get more for filtering

            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0 or idx >= len(self.metadata):
                    continue

                case = self.metadata[idx]

                # Apply jurisdiction filter
                if jurisdiction and case.jurisdiction != jurisdiction:
                    continue

                # Convert L2 distance to similarity score (0-1)
                score = 1.0 / (1.0 + dist)

                results.append(SearchResult(
                    case=case,
                    score=float(score),
                    rank=len(results) + 1
                ))

                if len(results) >= k:
                    break

        else:
            # Numpy-based search
            results = self._numpy_search(query_embedding, k, jurisdiction)

        return results

    def _numpy_search(
        self,
        query_embedding: np.ndarray,
        k: int,
        jurisdiction: Optional[str]
    ) -> List[SearchResult]:
        """Fallback numpy-based similarity search."""
        if not self.embeddings:
            return []

        # Compute cosine similarities
        embeddings_array = np.array(self.embeddings)
        query_norm = query_embedding / np.linalg.norm(query_embedding)

        similarities = []
        for idx, emb in enumerate(embeddings_array):
            case = self.metadata[idx]

            # Apply jurisdiction filter
            if jurisdiction and case.jurisdiction != jurisdiction:
                continue

            emb_norm = emb / np.linalg.norm(emb)
            similarity = float(np.dot(query_norm, emb_norm))
            similarities.append((similarity, idx))

        # Sort by similarity (descending)
        similarities.sort(reverse=True, key=lambda x: x[0])

        # Return top k
        results = []
        for rank, (score, idx) in enumerate(similarities[:k], 1):
            results.append(SearchResult(
                case=self.metadata[idx],
                score=score,
                rank=rank
            ))

        return results

    def save(self, filepath: str):
        """Save index and metadata to disk."""
        import pickle

        if FAISS_AVAILABLE and self.index is not None:
            faiss.write_index(self.index, f"{filepath}.faiss")

        with open(f"{filepath}.metadata.pkl", "wb") as f:
            pickle.dump({
                "metadata": self.metadata,
                "embeddings": self.embeddings if not FAISS_AVAILABLE else None,
                "embedding_dim": self.embedding_dim
            }, f)

        logger.info(f"Saved index to {filepath}")

    def load(self, filepath: str):
        """Load index and metadata from disk."""
        import pickle

        if FAISS_AVAILABLE:
            try:
                self.index = faiss.read_index(f"{filepath}.faiss")
                logger.info(f"Loaded FAISS index from {filepath}.faiss")
            except Exception as e:
                logger.warning(f"Could not load FAISS index: {e}")

        with open(f"{filepath}.metadata.pkl", "rb") as f:
            data = pickle.load(f)
            self.metadata = data["metadata"]
            self.embeddings = data.get("embeddings", [])
            self.embedding_dim = data["embedding_dim"]

        logger.info(f"Loaded metadata: {len(self.metadata)} cases")


# ═══════════════════════════════════════════════════════════════
# CROSS-ENCODER RERANKING
# ═══════════════════════════════════════════════════════════════

class CrossEncoderReranker:
    """
    Cross-encoder for reranking search results.
    Provides higher precision than bi-encoder (BERT) alone.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """Initialize cross-encoder model."""
        if not TRANSFORMERS_AVAILABLE:
            self.model = None
            return

        try:
            self.model = CrossEncoder(model_name)
            logger.info(f"Loaded cross-encoder: {model_name}")
        except Exception as e:
            logger.error(f"Error loading cross-encoder: {e}")
            self.model = None

    def rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        Rerank search results using cross-encoder.

        Args:
            query: Query text
            results: Initial search results
            top_k: Number of top results to return

        Returns:
            Reranked results
        """
        if self.model is None or not results:
            return results[:top_k]

        # Prepare pairs for cross-encoder
        pairs = [(query, result.case.text[:512]) for result in results]

        try:
            # Get cross-encoder scores
            scores = self.model.predict(pairs)

            # Update results with reranked scores
            for result, score in zip(results, scores):
                result.reranked_score = float(score)

            # Sort by reranked score
            results.sort(key=lambda x: x.reranked_score, reverse=True)

            # Update ranks
            for rank, result in enumerate(results, 1):
                result.rank = rank

            return results[:top_k]

        except Exception as e:
            logger.error(f"Error in reranking: {e}")
            return results[:top_k]


# ═══════════════════════════════════════════════════════════════
# HYBRID SEARCH (BM25 + BERT)
# ═══════════════════════════════════════════════════════════════

class BM25Searcher:
    """BM25 keyword-based search for hybrid retrieval."""

    def __init__(self):
        """Initialize BM25 searcher."""
        try:
            from rank_bm25 import BM25Okapi
            self.BM25Okapi = BM25Okapi
            self.available = True
        except ImportError:
            logger.warning("rank_bm25 not available. Install with: pip install rank-bm25")
            self.available = False

        self.corpus = []
        self.bm25 = None
        self.metadata = []

    def index_documents(self, cases: List[CaseDocument]):
        """Index documents for BM25 search."""
        if not self.available:
            return

        self.metadata = cases
        self.corpus = [case.text.lower().split() for case in cases]
        self.bm25 = self.BM25Okapi(self.corpus)
        logger.info(f"Indexed {len(cases)} cases for BM25 search")

    def search(self, query: str, k: int = 5) -> List[SearchResult]:
        """Search using BM25."""
        if not self.available or self.bm25 is None:
            return []

        query_tokens = query.lower().split()
        scores = self.bm25.get_scores(query_tokens)

        # Get top k indices
        top_indices = np.argsort(scores)[::-1][:k]

        results = []
        for rank, idx in enumerate(top_indices, 1):
            results.append(SearchResult(
                case=self.metadata[idx],
                score=float(scores[idx]),
                rank=rank
            ))

        return results


class HybridSearchEngine:
    """
    Hybrid search combining BM25 (keyword) and BERT (semantic).
    Provides best of both worlds: keyword precision + semantic understanding.
    """

    def __init__(
        self,
        bert_model: CaseLawBERT,
        vector_index: CaseLawIndex,
        use_reranking: bool = True
    ):
        """
        Initialize hybrid search engine.

        Args:
            bert_model: CaseLaw-BERT model
            vector_index: FAISS vector index
            use_reranking: Enable cross-encoder reranking
        """
        self.bert_model = bert_model
        self.vector_index = vector_index
        self.bm25_searcher = BM25Searcher()
        self.reranker = CrossEncoderReranker() if use_reranking else None

    def index_cases(self, cases: List[CaseDocument]):
        """Index cases for both BM25 and BERT search."""
        # Generate embeddings
        texts = [case.text for case in cases]
        embeddings = self.bert_model.embed_batch(texts)

        # Add to vector index
        self.vector_index.add_cases_batch(cases, embeddings)

        # Index for BM25
        self.bm25_searcher.index_documents(cases)

        logger.info(f"Indexed {len(cases)} cases for hybrid search")

    def search(
        self,
        query: str,
        k: int = 5,
        alpha: float = 0.5,
        jurisdiction: Optional[str] = None,
        use_reranking: bool = True
    ) -> List[SearchResult]:
        """
        Hybrid search with BM25 + BERT.

        Args:
            query: Search query
            k: Number of results
            alpha: Weight for BM25 (1-alpha for BERT). 0.5 = equal weight
            jurisdiction: Optional jurisdiction filter
            use_reranking: Apply cross-encoder reranking

        Returns:
            Hybrid search results
        """
        # BM25 search
        bm25_results = self.bm25_searcher.search(query, k * 2)

        # BERT semantic search
        query_embedding = self.bert_model.embed(query)
        bert_results = self.vector_index.search(query_embedding, k * 2, jurisdiction)

        # Combine results
        combined_scores = {}
        for result in bm25_results:
            case_id = result.case.case_id
            combined_scores[case_id] = {
                "case": result.case,
                "bm25_score": result.score,
                "bert_score": 0.0
            }

        for result in bert_results:
            case_id = result.case.case_id
            if case_id in combined_scores:
                combined_scores[case_id]["bert_score"] = result.score
            else:
                combined_scores[case_id] = {
                    "case": result.case,
                    "bm25_score": 0.0,
                    "bert_score": result.score
                }

        # Compute hybrid score
        hybrid_results = []
        for case_id, scores in combined_scores.items():
            hybrid_score = (
                alpha * scores["bm25_score"] +
                (1 - alpha) * scores["bert_score"]
            )
            hybrid_results.append(SearchResult(
                case=scores["case"],
                score=hybrid_score
            ))

        # Sort by hybrid score
        hybrid_results.sort(key=lambda x: x.score, reverse=True)

        # Take top k
        top_results = hybrid_results[:k * 2]  # Get more for reranking

        # Apply cross-encoder reranking
        if use_reranking and self.reranker:
            top_results = self.reranker.rerank(query, top_results, k)
        else:
            top_results = top_results[:k]

        return top_results


# ═══════════════════════════════════════════════════════════════
# SINGLETON INSTANCES
# ═══════════════════════════════════════════════════════════════

_bert_model_instance: Optional[CaseLawBERT] = None
_vector_index_instance: Optional[CaseLawIndex] = None
_hybrid_search_instance: Optional[HybridSearchEngine] = None


def get_caselaw_bert() -> CaseLawBERT:
    """Get singleton CaseLaw-BERT model."""
    global _bert_model_instance
    if _bert_model_instance is None:
        _bert_model_instance = CaseLawBERT()
    return _bert_model_instance


def get_vector_index() -> CaseLawIndex:
    """Get singleton vector index."""
    global _vector_index_instance
    if _vector_index_instance is None:
        _vector_index_instance = CaseLawIndex()
    return _vector_index_instance


def get_hybrid_search() -> HybridSearchEngine:
    """Get singleton hybrid search engine."""
    global _hybrid_search_instance
    if _hybrid_search_instance is None:
        bert_model = get_caselaw_bert()
        vector_index = get_vector_index()
        _hybrid_search_instance = HybridSearchEngine(bert_model, vector_index)
    return _hybrid_search_instance
