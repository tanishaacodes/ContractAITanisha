"""
Embeddings Service for Self-Healing Clause Library
Combines MiniLM (semantic) and Legal-BERT (legal context)
"""

import numpy as np
from functools import lru_cache

try:
    import torch
    from sentence_transformers import SentenceTransformer
    from transformers import AutoTokenizer, AutoModel
    _ML_AVAILABLE = True
except Exception:
    torch = None
    SentenceTransformer = None
    AutoTokenizer = None
    AutoModel = None
    _ML_AVAILABLE = False


class ClauseEmbeddingService:
    """
    Dual embedding service for clauses:
    - MiniLM: Fast, general semantic understanding
    - Legal-BERT: Legal domain-specific understanding
    """

    def __init__(self):
        self._minilm = None
        self._legal_tokenizer = None
        self._legal_model = None

    @property
    def minilm(self):
        """Lazy load MiniLM model"""
        if self._minilm is None:
            print("[INFO] Loading MiniLM model...")
            self._minilm = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
        return self._minilm

    @property
    def legal_tokenizer(self):
        """Lazy load Legal-BERT tokenizer"""
        if self._legal_tokenizer is None:
            print("[INFO] Loading Legal-BERT tokenizer...")
            self._legal_tokenizer = AutoTokenizer.from_pretrained("nlpaueb/legal-bert-base-uncased")
        return self._legal_tokenizer

    @property
    def legal_model(self):
        """Lazy load Legal-BERT model"""
        if self._legal_model is None:
            print("[INFO] Loading Legal-BERT model...")
            self._legal_model = AutoModel.from_pretrained("nlpaueb/legal-bert-base-uncased", low_cpu_mem_usage=False)
            self._legal_model.eval()  # Set to evaluation mode
        return self._legal_model

    def embed_semantic(self, text: str) -> np.ndarray:
        """
        Generate semantic embedding using MiniLM
        Fast and good for similarity search

        Args:
            text: Clause text to embed

        Returns:
            numpy array of shape (384,)
        """
        return self.minilm.encode(text, convert_to_numpy=True)

    def embed_legal(self, text: str) -> np.ndarray:
        """
        Generate legal-domain embedding using Legal-BERT
        Better for legal nuance and terminology

        Args:
            text: Clause text to embed

        Returns:
            numpy array of shape (768,)
        """
        # Tokenize
        inputs = self.legal_tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )

        # Generate embeddings
        with torch.no_grad():
            outputs = self.legal_model(**inputs)
            # Use mean pooling over token embeddings
            embeddings = outputs.last_hidden_state.mean(dim=1)

        return embeddings.cpu().numpy().flatten()

    def embed_clause(self, text: str) -> dict:
        """
        Generate both semantic and legal embeddings

        Args:
            text: Clause text to embed

        Returns:
            dict with 'semantic' and 'legal' numpy arrays
        """
        return {
            'semantic': self.embed_semantic(text),
            'legal': self.embed_legal(text)
        }

    def similarity(self, embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            embedding_a: First embedding vector
            embedding_b: Second embedding vector

        Returns:
            Similarity score (0-1)
        """
        dot_product = np.dot(embedding_a, embedding_b)
        norm_a = np.linalg.norm(embedding_a)
        norm_b = np.linalg.norm(embedding_b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))

    def semantic_similarity(self, text_a: str, text_b: str) -> float:
        """
        Calculate semantic similarity between two texts

        Args:
            text_a: First clause text
            text_b: Second clause text

        Returns:
            Similarity score (0-1)
        """
        emb_a = self.embed_semantic(text_a)
        emb_b = self.embed_semantic(text_b)
        return self.similarity(emb_a, emb_b)

    def legal_similarity(self, text_a: str, text_b: str) -> float:
        """
        Calculate legal domain similarity between two texts

        Args:
            text_a: First clause text
            text_b: Second clause text

        Returns:
            Similarity score (0-1)
        """
        emb_a = self.embed_legal(text_a)
        emb_b = self.embed_legal(text_b)
        return self.similarity(emb_a, emb_b)

    def hybrid_similarity(self, text_a: str, text_b: str, semantic_weight: float = 0.6) -> float:
        """
        Calculate weighted hybrid similarity (semantic + legal)

        Args:
            text_a: First clause text
            text_b: Second clause text
            semantic_weight: Weight for semantic similarity (0-1)

        Returns:
            Weighted similarity score (0-1)
        """
        semantic_sim = self.semantic_similarity(text_a, text_b)
        legal_sim = self.legal_similarity(text_a, text_b)

        legal_weight = 1.0 - semantic_weight
        return semantic_weight * semantic_sim + legal_weight * legal_sim


# Singleton instance
_embedding_service = None


def get_embedding_service() -> ClauseEmbeddingService:
    """Get or create the singleton embedding service"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = ClauseEmbeddingService()
    return _embedding_service
