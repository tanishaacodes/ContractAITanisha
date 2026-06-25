"""
In-Memory Clause Store
=======================
Thread-safe fallback store that holds enriched clauses in RAM when
Neo4j is unavailable. Persists within a single Django worker process.

Capacity: last 500 clauses across all documents (FIFO eviction).
Text search: BM25Okapi ranking (falls back to naive substring if rank_bm25 unavailable).
"""

import threading
from collections import OrderedDict

_lock  = threading.Lock()
_store: OrderedDict = OrderedDict()   # clause_id → clause dict
_CAPACITY = 500

# ─────────────────────────────────────────────────────────────────────────────
# BM25 index — rebuilt lazily whenever the store changes
# ─────────────────────────────────────────────────────────────────────────────
try:
    from rank_bm25 import BM25Okapi as _BM25Okapi
    _BM25_AVAILABLE = True
except ImportError:
    _BM25Okapi = None
    _BM25_AVAILABLE = False

_bm25 = None         # BM25Okapi instance (rebuilt on demand)
_bm25_dirty = True   # True → needs rebuild before next search


def _rebuild_bm25():
    """Rebuild BM25 index from current store. Must be called while holding _lock."""
    global _bm25, _bm25_dirty
    if not _BM25_AVAILABLE:
        _bm25_dirty = False
        return
    clauses = list(_store.values())
    tokenized = [(c.get("text") or "").lower().split() for c in clauses]
    _bm25 = _BM25Okapi(tokenized) if tokenized else None
    _bm25_dirty = False


def save_clauses(clauses: list) -> int:
    """
    Store a list of enriched clause dicts.
    Returns number of clauses stored.
    """
    global _bm25_dirty
    with _lock:
        for clause in clauses:
            cid = clause.get("id") or clause.get("clause_id")
            if not cid:
                continue
            # Evict oldest if over capacity
            if len(_store) >= _CAPACITY and cid not in _store:
                _store.popitem(last=False)
            _store[cid] = clause
        _bm25_dirty = True   # mark BM25 for rebuild on next search
    return len(clauses)


def get_all() -> list:
    """Return all stored clauses (newest last)."""
    with _lock:
        return list(_store.values())


def search_by_flag(flag: str, limit: int = 20) -> list:
    """
    Return clauses where flags[flag] is True.
    flag: obligation | indemnity | termination | payment | exclusivity | ip_clause
    """
    with _lock:
        results = [
            c for c in _store.values()
            if c.get("flags", {}).get(flag)
        ]
    # Sort by risk score descending
    results.sort(key=lambda c: c.get("risk", {}).get("score", 0), reverse=True)
    return results[:limit]


def search_high_risk(limit: int = 20) -> list:
    """Return HIGH and CRITICAL clauses sorted by risk score."""
    with _lock:
        results = [
            c for c in _store.values()
            if c.get("risk", {}).get("risk_level") in ("HIGH", "CRITICAL")
        ]
    results.sort(key=lambda c: c.get("risk", {}).get("score", 0), reverse=True)
    return results[:limit]


def search_temporal(limit: int = 20) -> list:
    """Return clauses that have temporal references."""
    with _lock:
        results = [c for c in _store.values() if c.get("temporal")]
    return results[:limit]


def simple_text_search(query: str, limit: int = 8) -> list:
    """
    BM25-ranked full-text search over clause text.
    Falls back to naive keyword scoring if rank_bm25 is unavailable.
    Used when Neo4j vector search is unavailable.
    """
    global _bm25_dirty
    tokens = query.lower().split()
    if not tokens:
        return []

    with _lock:
        if not _store:
            return []

        if _BM25_AVAILABLE:
            # Rebuild index if store has changed since last search
            if _bm25_dirty or _bm25 is None:
                _rebuild_bm25()

            if _bm25 is None:
                return []

            clauses = list(_store.values())
            scores = _bm25.get_scores(tokens)
            ranked = sorted(
                ((scores[i], clauses[i]) for i in range(len(clauses)) if scores[i] > 0),
                key=lambda x: x[0],
                reverse=True,
            )
            return [c for _, c in ranked[:limit]]

        # Naive fallback when rank_bm25 not installed
        keywords = [w for w in tokens if len(w) > 3]
        scored = []
        for clause in _store.values():
            text = (clause.get("text") or "").lower()
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scored.append((score, clause))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:limit]]


def count() -> int:
    with _lock:
        return len(_store)


def clear() -> None:
    global _bm25, _bm25_dirty
    with _lock:
        _store.clear()
        _bm25 = None
        _bm25_dirty = True


def _normalise(clause: dict) -> dict:
    """Convert enriched clause dict to the retriever's standard format."""
    risk = clause.get("risk", {})
    flags = clause.get("flags", {})
    return {
        "clause_id":       clause.get("id") or clause.get("clause_id"),
        "text":            clause.get("text", ""),
        "text_preview":    clause.get("text", "")[:200],
        "risk_level":      risk.get("risk_level", "LOW"),
        "risk_score":      risk.get("score", 0.0),
        "clause_number":   clause.get("clause_number"),
        "obligation":      flags.get("obligation", False),
        "indemnity":       flags.get("indemnity", False),
        "termination":     flags.get("termination", False),
        "payment":         flags.get("payment", False),
        "temporal_refs":   clause.get("temporal", []),
        "document":        clause.get("document_name"),
        "score":           risk.get("score", 0.0),
        # Enterprise intelligence fields
        "obligations_svo": clause.get("obligations_svo", []),
        "monetary_values": clause.get("monetary_values", []),
        "regulatory_refs": clause.get("regulatory_refs", []),
    }


def get_high_risk_normalised(limit: int = 20) -> list:
    return [_normalise(c) for c in search_high_risk(limit)]


def get_flag_normalised(flag: str, limit: int = 20) -> list:
    return [_normalise(c) for c in search_by_flag(flag, limit)]


def get_temporal_normalised(limit: int = 20) -> list:
    return [_normalise(c) for c in search_temporal(limit)]


def text_search_normalised(query: str, limit: int = 8) -> list:
    return [_normalise(c) for c in simple_text_search(query, limit)]
