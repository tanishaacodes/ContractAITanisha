"""
Clause Enrichment Pipeline
===========================
Enriches raw clause dicts with:
  - MiniLM vector embeddings        (via existing embeddings.embedding_service)
  - Risk level + signals             (via existing risk_engine.risk_service)
  - Legal semantic flags             (obligation / indemnity / termination / payment)
  - Temporal entity extraction       (regex + dateparser normalization to ISO dates)
  - Named entity extraction          (spaCy en_core_web_sm + regex fallback)
  - Cross-document entity linking    (embedding similarity within session)

All heavy models are loaded lazily to avoid import-time failures.
"""

import re
import logging
import math

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Lazy spaCy loader — graceful fallback to regex if model not installed
# ─────────────────────────────────────────────────────────────────────────────
_nlp = None          # None = not yet attempted; False = tried and failed


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
            logger.info("[Enrichment] spaCy en_core_web_sm loaded.")
        except Exception as e:
            logger.warning(f"[Enrichment] spaCy unavailable ({e}). Falling back to regex NER.")
            _nlp = False
    return _nlp if _nlp else None


# Lazy dateparser import — graceful fallback to raw string if not installed
try:
    import dateparser as _dateparser
    _DATEPARSER_AVAILABLE = True
except ImportError:
    _dateparser = None
    _DATEPARSER_AVAILABLE = False
    logger.warning("[Enrichment] dateparser not installed. Temporal strings won't be normalized.")

# ─────────────────────────────────────────────────────────────────────────────
# Legal-BERT NER lazy loader (nlpaueb/legal-bert-base-uncased)
# ─────────────────────────────────────────────────────────────────────────────
_legal_ner_pipeline = None   # None = not attempted; False = tried and failed


def _get_legal_ner():
    """Return HuggingFace NER pipeline backed by Legal-BERT, or None."""
    global _legal_ner_pipeline
    if _legal_ner_pipeline is None:
        try:
            from transformers import (
                pipeline,
                AutoTokenizer,
                AutoModelForTokenClassification,
            )
            tokenizer = AutoTokenizer.from_pretrained("nlpaueb/legal-bert-base-uncased")
            model = AutoModelForTokenClassification.from_pretrained(
                "nlpaueb/legal-bert-base-uncased"
            , low_cpu_mem_usage=False)
            _legal_ner_pipeline = pipeline(
                "ner",
                model=model,
                tokenizer=tokenizer,
                aggregation_strategy="simple",
            )
            logger.info("[Enrichment] Legal-BERT NER pipeline loaded.")
        except Exception as e:
            logger.warning(f"[Enrichment] Legal-BERT NER unavailable ({e}). spaCy+regex only.")
            _legal_ner_pipeline = False
    return _legal_ner_pipeline if _legal_ner_pipeline else None

# ─────────────────────────────────────────────────────────────────────────────
# Cross-document entity store (in-memory, per-process)
# Persists across requests in the same worker. Keyed by canonical entity name.
# ─────────────────────────────────────────────────────────────────────────────
_entity_store: dict = {}   # { canonical_name: embedding_vector }

ENTITY_SIM_THRESHOLD = 0.85


def _cosine_sim(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (norm_a * norm_b)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Embeddings
# ─────────────────────────────────────────────────────────────────────────────

def get_clause_embedding(text: str) -> list:
    """Return 384-dim MiniLM embedding using existing embedding_service."""
    from embeddings.embedding_service import generate_embedding
    result = generate_embedding(text)
    return result["embedding"]


# ─────────────────────────────────────────────────────────────────────────────
# 2. Risk classification
# ─────────────────────────────────────────────────────────────────────────────

def classify_risk(text: str) -> dict:
    """
    Use existing keyword-weighted risk engine.
    Returns: {risk_level, score, signals, protective_factors}
    """
    from risk_engine.risk_service import compute_clause_risk
    result = compute_clause_risk(text)
    return {
        "risk_level": result["level"],
        "score": result["score"],
        "signals": result["signals"],
        "protective_factors": result["protective_factors"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Legal semantic flags
# ─────────────────────────────────────────────────────────────────────────────

_OBLIGATION_RE  = re.compile(r"\b(shall|must|will|agrees to|is required to|undertakes)\b", re.I)
_INDEMNITY_RE   = re.compile(r"\b(indemnif|hold harmless|defend.*against)\b", re.I)
_TERMINATION_RE = re.compile(r"\b(terminat|cancell?ation|expire|expiry|rescind|void)\b", re.I)
_PAYMENT_RE     = re.compile(r"\b(payment|fee|invoice|reimburse|compensat|consideration|\$|USD|EUR|GBP)\b", re.I)
_EXCLUSIVITY_RE = re.compile(r"\b(exclusive|non.?compete|non.?solicit|restraint of trade)\b", re.I)
_IP_RE          = re.compile(r"\b(intellectual property|ip assignment|work for hire|proprietary|patent|copyright|trade secret)\b", re.I)


def detect_legal_flags(text: str) -> dict:
    return {
        "obligation":   bool(_OBLIGATION_RE.search(text)),
        "indemnity":    bool(_INDEMNITY_RE.search(text)),
        "termination":  bool(_TERMINATION_RE.search(text)),
        "payment":      bool(_PAYMENT_RE.search(text)),
        "exclusivity":  bool(_EXCLUSIVITY_RE.search(text)),
        "ip_clause":    bool(_IP_RE.search(text)),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. Temporal entity extraction (regex)
# ─────────────────────────────────────────────────────────────────────────────

_DATE_PATTERNS = [
    # ISO: 2024-01-15
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    # Long form: January 15, 2024 / 15th January 2024
    re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b",
        re.I,
    ),
    re.compile(
        r"\b\d{1,2}(?:st|nd|rd|th)?\s+"
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r",?\s+\d{4}\b",
        re.I,
    ),
    # Short: 01/15/2024 or 15-01-2024
    re.compile(r"\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b"),
    # Relative: within 30 days / 90-day period / 6 months
    re.compile(r"\b(?:within|after|before|no later than)\s+\d+\s+(?:day|month|year)s?\b", re.I),
    re.compile(r"\b\d+[- ](?:day|month|year)\s+(?:notice|period|term|window)\b", re.I),
]


def _normalise_date_str(raw: str) -> str:
    """Normalize a raw date string to ISO YYYY-MM-DD using dateparser, or return raw."""
    if not _DATEPARSER_AVAILABLE:
        return raw
    try:
        parsed = _dateparser.parse(
            raw,
            settings={"RETURN_AS_TIMEZONE_AWARE": False, "PREFER_DAY_OF_MONTH": "first"},
        )
        return parsed.strftime("%Y-%m-%d") if parsed else raw
    except Exception:
        return raw


def extract_temporal_entities(text: str) -> list:
    """
    Extract date/time expressions from contract text.
    Stage 1: Regex patterns (ISO dates, long-form, short-form, relative periods).
    Stage 2: spaCy DATE/TIME entities — catches natural-language expressions
             like "thirty days after execution" that regex cannot match.
    All calendar dates are normalized to ISO YYYY-MM-DD via dateparser.
    Returns: [str, ...] — backward-compatible list of strings.
    """
    found = []
    seen = set()

    # Stage 1: regex extraction
    for pattern in _DATE_PATTERNS:
        for match in pattern.finditer(text):
            raw = match.group(0).strip()
            if raw.lower() not in seen:
                seen.add(raw.lower())
                found.append(_normalise_date_str(raw))

    # Stage 2: spaCy DATE/TIME entities (augments regex, avoids duplicates)
    nlp = _get_nlp()
    if nlp:
        try:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ in ("DATE", "TIME"):
                    raw = ent.text.strip()
                    if raw.lower() not in seen:
                        seen.add(raw.lower())
                        found.append(_normalise_date_str(raw))
        except Exception as e:
            logger.warning(f"[Enrichment] spaCy temporal extraction failed: {e}")

    return found


# ─────────────────────────────────────────────────────────────────────────────
# 5. Named entity extraction (lightweight regex heuristics)
# ─────────────────────────────────────────────────────────────────────────────

_MONEY_RE  = re.compile(r"(?:USD|EUR|GBP|INR|AUD|CAD)?\s*\$?\d[\d,]*(?:\.\d+)?\s*(?:million|billion|thousand|k|M|B)?", re.I)
_ORG_HINTS = re.compile(
    r"\b([A-Z][A-Za-z0-9&\-\.\']+(?:\s+[A-Z][A-Za-z0-9&\-\.\']+)*)"
    r"\s*(?:Inc\.?|LLC|Ltd\.?|Corp\.?|GmbH|Pvt\.?|Pte\.?|PLC|LLP|Co\.?|Corporation|Limited)\b"
)
_PERSON_RE = re.compile(
    r"\b(Mr\.|Mrs\.|Ms\.|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
)


_SPACY_ENTITY_LABELS = {"ORG", "PERSON", "GPE", "MONEY", "LAW", "DATE", "NORP"}


def _regex_entities(text: str) -> list:
    """Lightweight regex NER — always runs as a supplement to spaCy."""
    entities = []
    seen = set()

    def _add(name: str, etype: str):
        key = (name.lower(), etype)
        if key not in seen and len(name) > 2:
            seen.add(key)
            entities.append({"name": name.strip(), "type": etype})

    for m in _ORG_HINTS.finditer(text):
        _add(m.group(0), "ORG")

    for m in _PERSON_RE.finditer(text):
        _add(f"{m.group(1)} {m.group(2)}", "PERSON")

    for m in _MONEY_RE.finditer(text):
        val = m.group(0).strip()
        if any(c.isdigit() for c in val):
            _add(val, "MONEY")

    return entities


def extract_entities(text: str) -> list:
    """
    Return [{name, type}, ...].
    Source 1: spaCy en_core_web_sm (ORG / PERSON / GPE / MONEY / LAW / DATE / NORP).
    Source 2: Legal-BERT NER pipeline (nlpaueb/legal-bert-base-uncased) — legal domain NER.
    Source 3: Regex heuristics — always runs as supplement for company suffixes + money.
    Deduplicates by (name.lower(), type).
    """
    entities = []

    # 1. spaCy NER — richer entity types (GPE, LAW, NORP, etc.)
    nlp = _get_nlp()
    if nlp:
        try:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ in _SPACY_ENTITY_LABELS:
                    entities.append({"name": ent.text.strip(), "type": ent.label_})
        except Exception as e:
            logger.warning(f"[Enrichment] spaCy NER failed: {e}")

    # 2. Legal-BERT NER — legal domain-specific entity recognition
    legal_ner = _get_legal_ner()
    if legal_ner:
        try:
            # BERT has a 512-token limit; truncate text if needed
            bert_ents = legal_ner(text[:1024])
            for ent in bert_ents:
                word = ent.get("word", "").strip().lstrip("##")
                label = ent.get("entity_group", ent.get("entity", "MISC"))
                if word and len(word) > 2:
                    entities.append({"name": word, "type": label})
        except Exception as e:
            logger.warning(f"[Enrichment] Legal-BERT NER failed: {e}")

    # 3. Regex supplement — always runs to catch company suffixes spaCy/BERT may miss
    entities.extend(_regex_entities(text))

    # Deduplicate by (name.lower(), type)
    seen = set()
    unique = []
    for e in entities:
        key = (e["name"].lower(), e["type"])
        if key not in seen and len(e["name"]) > 2:
            seen.add(key)
            unique.append(e)
    return unique


# ─────────────────────────────────────────────────────────────────────────────
# 6. SVO triple extraction (Subject-Verb-Object for obligations)
# ─────────────────────────────────────────────────────────────────────────────

_OBLIGATION_LEMMAS = {"shall", "must", "will", "agree", "undertake", "require", "warrant", "covenant"}


def extract_obligations_svo(text: str) -> list:
    """
    Extract Subject-Verb-Object triples for obligation sentences using spaCy
    dependency parsing.  Example: "Contractor shall pay $50,000 within 30 days."
    → {"subject": "Contractor", "verb": "shall pay", "object": "$50,000"}
    Returns: [{subject, verb, object}, ...]
    """
    nlp = _get_nlp()
    if not nlp:
        return []
    try:
        doc = nlp(text)
        triples = []
        for sent in doc.sents:
            for token in sent:
                if token.pos_ == "VERB" and token.lemma_.lower() in _OBLIGATION_LEMMAS:
                    subject, obj = None, None
                    # Check auxiliaries (shall, must) before the root verb
                    aux = " ".join(
                        c.text for c in token.children if c.dep_ == "aux"
                    )
                    verb_phrase = f"{aux} {token.text}".strip() if aux else token.text
                    for child in token.children:
                        if child.dep_ in ("nsubj", "nsubjpass"):
                            subject = child.text
                        elif child.dep_ in ("dobj", "attr", "pobj", "xcomp"):
                            obj = child.text
                    if subject:
                        triples.append({
                            "subject": subject,
                            "verb": verb_phrase,
                            "object": obj or "",
                        })
        return triples
    except Exception as e:
        logger.warning(f"[Enrichment] SVO extraction failed: {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# 7. Monetary value normalization
# ─────────────────────────────────────────────────────────────────────────────

_MONEY_NORMALIZE_RE = re.compile(
    r"(?P<currency>USD|EUR|GBP|INR|AUD|CAD|CHF|\$|€|£|¥)?\s*"
    r"(?P<amount>\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*"
    r"(?P<multiplier>million|billion|thousand|k|M|B)?",
    re.I,
)
_CURRENCY_SYMBOLS = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}
_MULTIPLIERS = {
    "billion": 1_000_000_000, "b": 1_000_000_000,
    "million": 1_000_000, "m": 1_000_000,
    "thousand": 1_000, "k": 1_000,
}


def normalize_monetary_values(text: str) -> list:
    """
    Extract and normalize monetary values found in clause text.
    Returns: [{"raw": str, "value": float, "currency": str}, ...]
    Example: "$5,000,000" → {"raw": "$5,000,000", "value": 5000000.0, "currency": "USD"}
    """
    results = []
    seen = set()
    for m in _MONEY_NORMALIZE_RE.finditer(text):
        amount_str = m.group("amount")
        if not amount_str or not any(c.isdigit() for c in amount_str):
            continue
        raw = m.group(0).strip()
        if not raw or raw.lower() in seen:
            continue
        try:
            value = float(amount_str.replace(",", ""))
        except ValueError:
            continue
        mult = (m.group("multiplier") or "").lower()
        value *= _MULTIPLIERS.get(mult, 1)
        currency_raw = (m.group("currency") or "").strip()
        currency = _CURRENCY_SYMBOLS.get(currency_raw, currency_raw.upper() if currency_raw else "USD")
        seen.add(raw.lower())
        results.append({"raw": raw, "value": value, "currency": currency})
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 8. Regulatory framework mapping
# ─────────────────────────────────────────────────────────────────────────────

_REGULATORY_KEYWORDS: dict = {
    "GDPR": [
        "personal data", "data subject", "controller", "processor",
        "data protection", "right to erasure", "right to access",
        "consent", "data breach", "gdpr", "dpa", "lawful basis",
    ],
    "HIPAA": [
        "protected health information", "phi", "covered entity",
        "business associate", "hipaa", "health information",
        "medical record", "patient data",
    ],
    "SOX": [
        "internal controls", "financial reporting", "material weakness",
        "audit committee", "sarbanes-oxley", "sox", "sec filing",
        "public company", "internal audit",
    ],
    "PCI-DSS": [
        "payment card", "cardholder data", "pci dss",
        "payment processing", "credit card data",
    ],
    "CCPA": [
        "california consumer privacy", "ccpa", "consumer rights",
        "personal information sale", "opt-out",
    ],
}


def map_regulatory_frameworks(text: str) -> list:
    """
    Identify regulatory frameworks referenced in clause text.
    Returns list of matched framework names, e.g. ["GDPR", "HIPAA"].
    """
    text_lower = text.lower()
    return [fw for fw, kws in _REGULATORY_KEYWORDS.items() if any(kw in text_lower for kw in kws)]


# ─────────────────────────────────────────────────────────────────────────────
# 9. Cross-document entity linking
# ─────────────────────────────────────────────────────────────────────────────

def link_entity(entity_name: str) -> str:
    """
    Return canonical entity name by checking embedding similarity
    against previously seen entities. Updates global store.
    """
    from embeddings.embedding_service import generate_embedding

    embedding = generate_embedding(entity_name)["embedding"]

    for canonical, stored_emb in _entity_store.items():
        sim = _cosine_sim(embedding, stored_emb)
        if sim > ENTITY_SIM_THRESHOLD:
            return canonical  # Link to existing canonical name

    _entity_store[entity_name] = embedding
    return entity_name


def clear_entity_store():
    """Clear the cross-document entity cache (call between unrelated ingestion batches)."""
    global _entity_store
    _entity_store = {}


# ─────────────────────────────────────────────────────────────────────────────
# 7. Full enrichment pipeline
# ─────────────────────────────────────────────────────────────────────────────

def enrich_clause(clause: dict) -> dict:
    """
    Enrich a single clause dict in-place.

    Input:  {id, clause_number, text}
    Output: adds embedding, risk, flags, temporal, entities
    """
    text = clause.get("text", "")

    try:
        clause["embedding"] = get_clause_embedding(text)
    except Exception as e:
        logger.warning(f"Embedding failed for clause {clause['id']}: {e}")
        clause["embedding"] = [0.0] * 384

    try:
        clause["risk"] = classify_risk(text)
    except Exception as e:
        logger.warning(f"Risk classification failed for clause {clause['id']}: {e}")
        clause["risk"] = {"risk_level": "LOW", "score": 0.0, "signals": [], "protective_factors": []}

    clause["flags"] = detect_legal_flags(text)
    clause["temporal"] = extract_temporal_entities(text)
    clause["obligations_svo"] = extract_obligations_svo(text)
    clause["monetary_values"] = normalize_monetary_values(text)
    clause["regulatory_refs"] = map_regulatory_frameworks(text)

    raw_entities = extract_entities(text)
    linked_entities = []
    for ent in raw_entities:
        try:
            canonical = link_entity(ent["name"])
            linked_entities.append({"name": canonical, "type": ent["type"]})
        except Exception:
            linked_entities.append(ent)

    clause["entities"] = linked_entities
    return clause


def enrich_clauses(clauses: list) -> list:
    """Enrich a list of clause dicts."""
    return [enrich_clause(c) for c in clauses]
