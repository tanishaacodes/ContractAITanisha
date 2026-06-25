"""
Embedding Service for ContractAI
Supports two embedding backends, switchable at runtime via Settings UI:

  minilm             – sentence-transformers/all-MiniLM-L6-v2   (384-dim)
  bert-large-uncased – bert-large-uncased via HuggingFace        (768-dim)

Active model is driven by Django settings.EMBEDDING_MODEL_KEY.
Call  EmbeddingService.switch_model(key)  to hot-swap without a restart.
"""

import numpy as np
import hashlib
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def _get_model_options():
    from django.conf import settings
    return settings.EMBEDDING_MODEL_OPTIONS


def _get_active_key():
    """Get active embedding model key from database (persistent across restarts)"""
    from django.conf import settings

    # First check runtime override (for backward compatibility)
    if hasattr(settings, '_EMBEDDING_MODEL_KEY_OVERRIDE'):
        return settings._EMBEDDING_MODEL_KEY_OVERRIDE

    # Read from database for persistence
    try:
        from core.models import SystemSettings
        return SystemSettings.get_active_embedding_model()
    except Exception:
        # Fallback to settings if DB not available (during migrations, etc.)
        return settings.EMBEDDING_MODEL_KEY


def _set_active_key(key):
    """Set active embedding model key in database (persists across restarts)"""
    from django.conf import settings

    # Save to database for persistence
    try:
        from core.models import SystemSettings
        SystemSettings.set_active_embedding_model(key)
    except Exception as e:
        logger.warning(f"Could not save to database, using runtime override: {e}")
        # Fallback to runtime override
        settings._EMBEDDING_MODEL_KEY_OVERRIDE = key


class EmbeddingService:
    """
    Singleton embedding service.  Both models stay in memory once loaded —
    switching is instant (just flips which one encode routes to).
    """

    _instance = None
    _current_key = None
    # _cache: { key: { 'model': ..., 'tokenizer': ... | None } }
    _cache: Dict[str, dict] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ---------------------------------------------------------- lifecycle
    def _ensure_loaded(self):
        """Make sure the active model key is set and its weights are in _cache."""
        desired_key = _get_active_key()
        if desired_key not in self._cache:
            self._load_model(desired_key)
        self._current_key = desired_key

    def _load_model(self, key: str):
        """Load model weights into _cache[key].  No-op if already cached."""
        if key in self._cache:
            return

        options = _get_model_options()
        if key not in options:
            raise ValueError(f"Unknown embedding model key '{key}'. Valid: {list(options)}")

        cfg = options[key]
        logger.info("Loading embedding model: %s (%s)", cfg['label'], cfg['model_id'])

        if cfg['loader'] == 'sentence_transformers':
            from sentence_transformers import SentenceTransformer
            self._cache[key] = {
                'model': SentenceTransformer(cfg['model_id'], device='cpu'),
                'tokenizer': None,
            }

        elif cfg['loader'] == 'transformers':
            from transformers import BertTokenizer, BertModel
            model = BertModel.from_pretrained(cfg['model_id'], low_cpu_mem_usage=False)
            model.eval()
            self._cache[key] = {
                'model': model,
                'tokenizer': BertTokenizer.from_pretrained(cfg['model_id']),
            }

        logger.info("Embedding model loaded & cached: %s  dim=%d", cfg['label'], cfg['dimensions'])

    # ---------------------------------------------------------- public API
    @classmethod
    def switch_model(cls, key: str):
        """Switch the active model.  Loads into cache on first use; instant after that."""
        _set_active_key(key)
        instance = cls()
        instance._load_model(key)          # no-op if already cached
        instance._current_key = key

    @property
    def current_key(self) -> str:
        self._ensure_loaded()
        return self._current_key

    @property
    def dimensions(self) -> int:
        self._ensure_loaded()
        return _get_model_options()[self._current_key]['dimensions']

    @property
    def active_model_name(self) -> str:
        """Return the DB-friendly name for the currently active model."""
        self._ensure_loaded()
        model_id = _get_model_options()[self._current_key]['model_id']
        # Strip HuggingFace org prefix (e.g., 'sentence-transformers/all-MiniLM-L6-v2' -> 'all-MiniLM-L6-v2')
        return model_id.split('/')[-1] if '/' in model_id else model_id

    # ----------------------------------------------------------- raw encode
    def _active_entry(self) -> dict:
        """Return the cached { model, tokenizer } for the current key."""
        return self._cache[self._current_key]

    def _encode_single(self, text: str) -> np.ndarray:
        cfg = _get_model_options()[self._current_key]
        entry = self._active_entry()
        if cfg['loader'] == 'sentence_transformers':
            return entry['model'].encode(text, convert_to_numpy=True)
        # BERT-large: mean-pool last hidden state
        import torch
        inputs = entry['tokenizer'](text, return_tensors='pt', truncation=True, max_length=512)
        with torch.no_grad():
            outputs = entry['model'](**inputs)
        return outputs.last_hidden_state.squeeze(0).mean(dim=0).numpy()

    def _encode_batch(self, texts: List[str]) -> np.ndarray:
        cfg = _get_model_options()[self._current_key]
        entry = self._active_entry()
        if cfg['loader'] == 'sentence_transformers':
            return entry['model'].encode(texts, convert_to_numpy=True)
        # BERT-large: batched tokenise → mean-pool with attention mask
        import torch
        inputs = entry['tokenizer'](texts, return_tensors='pt', padding=True,
                                    truncation=True, max_length=512)
        with torch.no_grad():
            outputs = entry['model'](**inputs)
        mask = inputs['attention_mask'].unsqueeze(-1)
        hidden = outputs.last_hidden_state * mask
        return (hidden.sum(dim=1) / mask.sum(dim=1)).numpy()

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text using the active model."""
        self._ensure_loaded()
        dim = self.dimensions
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * dim
        try:
            return self._encode_single(text).tolist()
        except Exception as e:
            logger.error("Error generating embedding: %s", e)
            return [0.0] * dim

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using the active model."""
        self._ensure_loaded()
        if not texts:
            return []
        dim = self.dimensions
        valid_texts = [t if t and t.strip() else " " for t in texts]
        try:
            return [emb.tolist() for emb in self._encode_batch(valid_texts)]
        except Exception as e:
            logger.error("Error generating batch embeddings: %s", e)
            return [[0.0] * dim for _ in texts]

    @staticmethod
    def cosine_similarity(embedding_a: List[float], embedding_b: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding_a: First embedding vector
            embedding_b: Second embedding vector

        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        try:
            a = np.array(embedding_a)
            b = np.array(embedding_b)

            # Handle zero vectors
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)

            if norm_a == 0 or norm_b == 0:
                return 0.0

            similarity = np.dot(a, b) / (norm_a * norm_b)

            # Ensure result is in [0, 1] range (numerical stability)
            return float(max(0.0, min(1.0, similarity)))
        except Exception as e:
            logger.error(f"Error computing cosine similarity: {e}")
            return 0.0

    @staticmethod
    def compute_text_hash(text: str) -> str:
        """
        Generate SHA256 hash of text for change detection.

        Args:
            text: Text to hash

        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def find_most_similar(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[Tuple[str, List[float]]],
        top_k: int = 5,
        min_threshold: float = 0.0
    ) -> List[Tuple[str, float]]:
        """
        Find most similar embeddings from a list of candidates.

        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of (id, embedding) tuples
            top_k: Number of top results to return
            min_threshold: Minimum similarity threshold

        Returns:
            List of (id, similarity_score) tuples, sorted by descending similarity
        """
        results = []

        for candidate_id, candidate_embedding in candidate_embeddings:
            similarity = self.cosine_similarity(query_embedding, candidate_embedding)

            if similarity >= min_threshold:
                results.append((candidate_id, similarity))

        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def compute_risk_score(
        self,
        clause_embedding: List[float],
        risk_playbooks: List[Dict]
    ) -> Tuple[Optional[Dict], float]:
        """
        Compute risk score for a clause using similarity to risk playbooks.

        Formula: Risk Score = max(Similarity × Severity Weight) across all playbooks

        Args:
            clause_embedding: Clause embedding vector
            risk_playbooks: List of risk playbook dicts with 'embedding', 'severity_weight', etc.

        Returns:
            Tuple of (matched_playbook_dict, risk_score)
        """
        if not risk_playbooks:
            return None, 0.0

        max_risk_score = 0.0
        matched_playbook = None

        for playbook in risk_playbooks:
            similarity = self.cosine_similarity(clause_embedding, playbook['embedding'])

            # Check if similarity meets threshold
            if similarity >= playbook.get('similarity_threshold', 0.7):
                risk_score = similarity * playbook['severity_weight']

                if risk_score > max_risk_score:
                    max_risk_score = risk_score
                    matched_playbook = {
                        **playbook,
                        'similarity': similarity,
                        'risk_score': risk_score
                    }

        return matched_playbook, max_risk_score

    def detect_intent(
        self,
        clause_embedding: List[float],
        intent_templates: List[Dict]
    ) -> Tuple[Optional[Dict], float]:
        """
        Detect legal intent of a clause using similarity to intent templates.

        Args:
            clause_embedding: Clause embedding vector
            intent_templates: List of intent template dicts with 'embedding', etc.

        Returns:
            Tuple of (matched_intent_dict, confidence_score)
        """
        if not intent_templates:
            return None, 0.0

        best_match = None
        best_score = 0.0

        for template in intent_templates:
            similarity = self.cosine_similarity(clause_embedding, template['embedding'])

            # Check if similarity meets threshold
            if similarity >= template.get('similarity_threshold', 0.65):
                if similarity > best_score:
                    best_score = similarity
                    best_match = {
                        **template,
                        'confidence': similarity
                    }

        return best_match, best_score

    def find_approved_clause(
        self,
        clause_embedding: List[float],
        approved_clauses: List[Dict],
        intent_name: Optional[str] = None,
        clause_type: Optional[str] = None,
        protection_level: str = 'BALANCED'
    ) -> Optional[Dict]:
        """
        Find the best approved clause replacement.

        Args:
            clause_embedding: Original clause embedding
            approved_clauses: List of approved clause dicts
            intent_name: Optional intent name to filter by
            clause_type: Optional clause type to filter by
            protection_level: Preferred protection level (MAXIMUM, BALANCED, MINIMUM)

        Returns:
            Best matching approved clause dict or None
        """
        if not approved_clauses:
            return None

        # Filter by intent and clause type if provided
        filtered_clauses = approved_clauses

        if intent_name:
            filtered_clauses = [c for c in filtered_clauses if c.get('intent_name') == intent_name]

        if clause_type:
            filtered_clauses = [c for c in filtered_clauses if c.get('clause_type') == clause_type]

        if not filtered_clauses:
            filtered_clauses = approved_clauses  # Fallback to all

        # Prefer matching protection level
        protection_matches = [c for c in filtered_clauses if c.get('protection_level') == protection_level]

        if not protection_matches:
            protection_matches = filtered_clauses

        # Find highest similarity
        best_match = None
        best_similarity = 0.0

        for approved_clause in protection_matches:
            similarity = self.cosine_similarity(clause_embedding, approved_clause['embedding'])

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    **approved_clause,
                    'similarity': similarity
                }

        return best_match if best_similarity > 0.5 else None


# Global singleton instance
embedding_service = EmbeddingService()
