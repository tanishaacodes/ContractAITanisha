"""
Clause Extractor
================
Two-stage clause extraction pipeline:

Stage 1 — Structural: Detect numbered/named clauses using legal formatting patterns
  (1., 1.1, Section 3, Article IV, etc.)

Stage 2 — Semantic Fallback: Split on paragraph boundaries + cosine similarity
  Primary embeddings: Legal-BERT CLS tokens (nlpaueb/legal-bert-base-uncased)
  Fallback embeddings: MiniLM via existing embeddings.embedding_service

Legal-BERT is domain-trained on legal text so clause boundaries are more accurate.
Falls back gracefully to MiniLM if model unavailable or too slow.
"""

import re
import uuid
import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Legal-BERT lazy loader for semantic clause splitting
# ─────────────────────────────────────────────────────────────────────────────
_lb_tokenizer = None   # None = not attempted; False = tried and failed
_lb_model = None


def _get_legal_bert():
    """Return (tokenizer, model) tuple for Legal-BERT, or (None, None)."""
    global _lb_tokenizer, _lb_model
    if _lb_tokenizer is None:
        try:
            from transformers import AutoTokenizer, AutoModel
            _lb_tokenizer = AutoTokenizer.from_pretrained("nlpaueb/legal-bert-base-uncased")
            _lb_model = AutoModel.from_pretrained("nlpaueb/legal-bert-base-uncased", low_cpu_mem_usage=False)
            _lb_model.eval()
            logger.info("[ClauseExtractor] Legal-BERT loaded for semantic splitting.")
        except Exception as e:
            logger.warning(f"[ClauseExtractor] Legal-BERT unavailable ({e}). Using MiniLM.")
            _lb_tokenizer = False
            _lb_model = False
    return (_lb_tokenizer, _lb_model) if _lb_tokenizer else (None, None)


def _legal_bert_embedding(text: str):
    """Return CLS token embedding from Legal-BERT (384-dim list), or None on failure."""
    tokenizer, model = _get_legal_bert()
    if tokenizer is None:
        return None
    try:
        import torch
        inputs = tokenizer(
            text, return_tensors="pt", truncation=True, padding=True, max_length=512
        )
        with torch.no_grad():
            outputs = model(**inputs)
        # CLS token (position 0) encodes the full sentence meaning
        return outputs.last_hidden_state[:, 0, :].squeeze().tolist()
    except Exception as e:
        logger.warning(f"[ClauseExtractor] Legal-BERT embedding failed: {e}")
        return None

# Cosine similarity threshold — lower = more clauses, higher = fewer
SIMILARITY_THRESHOLD = 0.80


# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Structural extraction
# ─────────────────────────────────────────────────────────────────────────────

# Matches: 1. / 1.1 / 1.1.1 / Section 3 / Article IV / (a) / CLAUSE 2
_STRUCTURAL_PATTERN = re.compile(
    r"(?:^|\n)"
    r"(\d+(?:\.\d+)*|Section\s+\d+(?:\.\d+)*|Article\s+[IVXLCDM]+|Clause\s+\d+|\([a-z]\))"
    r"[\.\):]?\s+",
    re.IGNORECASE,
)


def _structural_split(text: str) -> list:
    """Return clause dicts if legal numbering patterns are found."""
    splits = _STRUCTURAL_PATTERN.split(text)

    clauses = []
    # splits = [pre, number, body, number, body, ...]
    # After re.split with one capture group the pattern is [pre, g1, suffix, g1, suffix, ...]
    # With our pattern we have 1 capture group so pattern is: [pre, cap, rest, cap, rest, ...]
    if len(splits) > 2:
        for i in range(1, len(splits) - 1, 2):
            clause_number = splits[i].strip()
            clause_text = splits[i + 1].strip() if i + 1 < len(splits) else ""
            if len(clause_text) > 30:
                clauses.append({
                    "id": str(uuid.uuid4()),
                    "clause_number": clause_number,
                    "text": clause_text,
                })

    return clauses


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Semantic split using MiniLM embeddings
# ─────────────────────────────────────────────────────────────────────────────

def _cosine_sim(vec_a: list, vec_b: list) -> float:
    """Pure-Python cosine similarity (avoids numpy dependency here)."""
    import math
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a)) or 1.0
    norm_b = math.sqrt(sum(b * b for b in vec_b)) or 1.0
    return dot / (norm_a * norm_b)


def _semantic_split(text: str) -> list:
    """
    Split contract text into clauses by detecting topic shifts via
    cosine similarity of adjacent paragraph embeddings.

    Primary: Legal-BERT CLS token embeddings (legal domain-specific).
    Fallback: MiniLM via existing embeddings.embedding_service.
    """
    paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 40]

    if len(paragraphs) <= 1:
        return [{
            "id": str(uuid.uuid4()),
            "clause_number": None,
            "text": text.strip(),
        }]

    # Determine which embedding source to use for this document
    first_emb = _legal_bert_embedding(paragraphs[0])
    if first_emb is not None:
        use_legal_bert = True
        logger.info("[ClauseExtractor] Semantic splitting using Legal-BERT embeddings.")
    else:
        use_legal_bert = False
        from embeddings.embedding_service import generate_embedding
        first_emb = generate_embedding(paragraphs[0])["embedding"]
        logger.info("[ClauseExtractor] Semantic splitting using MiniLM embeddings.")

    # Embed all paragraphs using chosen source
    embeddings = [first_emb]
    for p in paragraphs[1:]:
        if use_legal_bert:
            emb = _legal_bert_embedding(p)
            if emb is None:                      # unexpected mid-run failure
                use_legal_bert = False
                from embeddings.embedding_service import generate_embedding
                emb = generate_embedding(p)["embedding"]
        else:
            from embeddings.embedding_service import generate_embedding
            emb = generate_embedding(p)["embedding"]
        embeddings.append(emb)

    clauses = []
    current_text = paragraphs[0]
    clause_id = str(uuid.uuid4())

    for i in range(1, len(paragraphs)):
        sim = _cosine_sim(embeddings[i - 1], embeddings[i])
        if sim < SIMILARITY_THRESHOLD:
            clauses.append({
                "id": clause_id,
                "clause_number": None,
                "text": current_text,
            })
            clause_id = str(uuid.uuid4())
            current_text = paragraphs[i]
        else:
            current_text += "\n" + paragraphs[i]

    clauses.append({
        "id": clause_id,
        "clause_number": None,
        "text": current_text,
    })

    return clauses


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def extract_clauses(text: str) -> list:
    """
    Extract clauses from contract text.

    Tries structural detection first; falls back to semantic splitting.

    Returns:
        List of dicts: [{id, clause_number, text}, ...]
    """
    if not text or not text.strip():
        return []

    # Stage 1 — structural
    clauses = _structural_split(text)
    if clauses:
        logger.info(f"Structural extraction: {len(clauses)} clauses")
        return clauses

    # Stage 2 — semantic
    logger.info("No structural numbering detected. Using semantic splitting.")
    try:
        clauses = _semantic_split(text)
        logger.info(f"Semantic extraction: {len(clauses)} clauses")
        return clauses
    except Exception as e:
        logger.warning(f"Semantic split failed ({e}). Using paragraph fallback.")

    # Final fallback: split on double newlines
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 50]
    return [
        {"id": str(uuid.uuid4()), "clause_number": None, "text": p}
        for p in paragraphs
    ]
