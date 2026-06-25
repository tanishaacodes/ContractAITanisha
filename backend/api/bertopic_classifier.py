from bertopic import BERTopic
import numpy as np
import os
import hashlib

# ============================
# LOAD TRAINED MODEL (ONCE)
# ============================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "bertopic_contracts"
)

# Try to load the model, but don't fail if it doesn't exist
try:
    topic_model = BERTopic.load(MODEL_PATH)
    MODEL_LOADED = True
    print(f"✅ BERTopic model loaded successfully from {MODEL_PATH}")
except Exception as e:
    print(f"⚠️ BERTopic model not found. Classification will use keyword-based fallback.")
    print(f"   To train the model, run: cd django_backend && python initialize_bertopic.py")
    topic_model = None
    MODEL_LOADED = False

# ============================
# LOAD EMBEDDING MODEL (ONCE)
# ============================
from sentence_transformers import SentenceTransformer

# Only load embedding model if BERTopic is loaded (to save memory)
if MODEL_LOADED:
    embedding_model = SentenceTransformer("all-mpnet-base-v2", device='cpu')
    print(f"✅ Embedding model loaded successfully")
else:
    embedding_model = None

# ============================
# CACHE FOR CONSISTENT RESULTS
# ============================
_classification_cache = {}
_embedding_cache = {}

# ============================
# STABLE CLASSIFICATION WITH CACHING
# ============================

def classify_with_bertopic(text: str):
    """
    Classify contract text using BERTopic.
    Uses caching to ensure consistent results for the same text.
    Falls back to keyword-based classification if model isn't loaded.
    """
    # Create cache key from text hash
    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()

    # Return cached result if available
    if text_hash in _classification_cache:
        return _classification_cache[text_hash]

    # If model not loaded, use keyword-based fallback
    if not MODEL_LOADED or topic_model is None:
        result = _fallback_classification(text)
        _classification_cache[text_hash] = result
        return result

    # Run classification
    topics, probs = topic_model.transform([text])

    topic_id = int(topics[0])

    if topic_id == -1:
        result = {
            "contractType": "Outlier / Unknown",
            "confidenceScore": 0,
            "topicId": -1
        }
    else:
        confidence = float(np.max(probs[0])) * 100 if probs is not None else 0

        topic_info = topic_model.get_topic_info()
        topic_name = topic_info.loc[
            topic_info.Topic == topic_id, "Name"
        ].values[0]

        result = {
            "contractType": topic_name,
            "confidenceScore": round(confidence, 2),
            "topicId": topic_id
        }

    # Cache the result
    _classification_cache[text_hash] = result

    return result


def _fallback_classification(text: str):
    """
    Simple keyword-based fallback classification when BERTopic model isn't available.
    """
    text_lower = text.lower()

    # Define contract type keywords
    patterns = {
        "Employment Agreement": ["employment", "employee", "employer", "salary", "compensation", "termination of employment"],
        "Service Agreement": ["services", "service provider", "deliverables", "scope of work", "project"],
        "Vendor Agreement": ["vendor", "supplier", "purchase", "goods", "materials"],
        "Non-Disclosure Agreement": ["confidential", "nda", "non-disclosure", "proprietary information", "confidentiality"],
        "Consulting Agreement": ["consultant", "consulting services", "advisory", "expertise"],
        "Master Service Agreement": ["master service", "msa", "framework agreement", "overarching"],
        "License Agreement": ["license", "licensor", "licensee", "intellectual property", "rights granted"],
        "Lease Agreement": ["lease", "lessor", "lessee", "premises", "rent", "tenant"],
        "Partnership Agreement": ["partner", "partnership", "profit sharing", "joint venture"],
        "Sales Agreement": ["sale", "buyer", "seller", "purchase price", "delivery"],
    }

    # Count keyword matches
    scores = {}
    for contract_type, keywords in patterns.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            scores[contract_type] = score

    if not scores:
        return {
            "contractType": "General Contract",
            "confidenceScore": 30,
            "topicId": -1
        }

    # Get best match
    best_type = max(scores, key=scores.get)
    max_score = scores[best_type]
    total_keywords = len(patterns[best_type])
    confidence = min(95, (max_score / total_keywords) * 100)

    return {
        "contractType": best_type,
        "confidenceScore": round(confidence, 2),
        "topicId": -1
    }


def get_embeddings(texts):
    """
    Get embeddings for texts with caching.
    Returns embeddings as numpy array.
    Falls back to None if embedding model isn't loaded.
    """
    if not MODEL_LOADED or embedding_model is None:
        return None

    embeddings = []
    texts_to_encode = []
    indices_to_encode = []

    for i, text in enumerate(texts):
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        if text_hash in _embedding_cache:
            embeddings.append(_embedding_cache[text_hash])
        else:
            texts_to_encode.append(text)
            indices_to_encode.append(i)
            embeddings.append(None)

    # Encode uncached texts
    if texts_to_encode:
        new_embeddings = embedding_model.encode(texts_to_encode, show_progress_bar=False)
        for idx, text in zip(indices_to_encode, texts_to_encode):
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            _embedding_cache[text_hash] = new_embeddings[indices_to_encode.index(idx)]
            embeddings[idx] = new_embeddings[indices_to_encode.index(idx)]

    return np.array(embeddings)
