"""
Embeddings Engine
==================
Generates vector embeddings for contract text using:
  - sentence-transformers (all-MiniLM-L6-v2) as primary
  - Falls back to a simple TF-IDF-style hash embedding if transformers not available
"""

import logging
import hashlib
import math

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Lazy model loader
# ─────────────────────────────────────────────
_model = None
_model_name = "sentence-transformers/all-MiniLM-L6-v2"


def _get_model():
    global _model
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(_model_name, device='cpu')
        logger.info(f"Loaded embedding model: {_model_name}")
    except Exception as e:
        logger.warning(f"Could not load SentenceTransformer: {e}. Using fallback embedder.")
        _model = None
    return _model


# ─────────────────────────────────────────────
# Fallback: deterministic hash-based embedding (384-dim)
# ─────────────────────────────────────────────
def _hash_embed(text: str, dim: int = 384) -> list:
    """Deterministic pseudo-embedding via SHA-256 seeded values."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    # Expand digest to required dimensions
    values = []
    for i in range(dim):
        byte_val = digest[i % 32]
        # Map 0-255 → -1.0 to 1.0
        values.append((byte_val - 128) / 128.0)
    # L2-normalize
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [round(v / norm, 6) for v in values]


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────
def generate_embedding(text: str) -> dict:
    """
    Generate a vector embedding for the given text.

    Returns:
        {
            "embedding": [float, ...],   # 384-dim vector
            "dim": 384,
            "model": str,
            "method": "transformer" | "fallback"
        }
    """
    if not text or not text.strip():
        return {
            "embedding": [0.0] * 384,
            "dim": 384,
            "model": "none",
            "method": "zero",
        }

    model = _get_model()
    if model is not None:
        try:
            vector = model.encode(text, normalize_embeddings=True).tolist()
            return {
                "embedding": [round(v, 6) for v in vector],
                "dim": len(vector),
                "model": _model_name,
                "method": "transformer",
            }
        except Exception as e:
            logger.error(f"Transformer embedding failed: {e}")

    # Fallback
    return {
        "embedding": _hash_embed(text),
        "dim": 384,
        "model": "hash-fallback",
        "method": "fallback",
    }


def generate_batch_embeddings(texts: list) -> list:
    """
    Generate embeddings for a list of texts.

    Returns:
        List of embedding dicts (same structure as generate_embedding)
    """
    model = _get_model()
    if model is not None and texts:
        try:
            vectors = model.encode(texts, normalize_embeddings=True, batch_size=32).tolist()
            return [
                {
                    "embedding": [round(v, 6) for v in vec],
                    "dim": len(vec),
                    "model": _model_name,
                    "method": "transformer",
                }
                for vec in vectors
            ]
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")

    return [generate_embedding(t) for t in texts]


def cosine_similarity(vec_a: list, vec_b: list) -> float:
    """Compute cosine similarity between two equal-length vectors."""
    if len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a)) or 1.0
    norm_b = math.sqrt(sum(b * b for b in vec_b)) or 1.0
    return round(dot / (norm_a * norm_b), 6)


def is_transformer_available() -> bool:
    return _get_model() is not None
