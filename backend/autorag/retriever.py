"""
AutoRAG Retriever
==================
Retrieves contract clauses from:
  1. Neo4j 5 vector index (when available)
  2. In-memory store fallback (always available — populated on each index)

All retrieval strategies return a unified list of clause dicts.
"""

import logging
from ingestion import memory_store

logger = logging.getLogger(__name__)

# Number of top clauses to retrieve per query
TOP_K = 8


# ─────────────────────────────────────────────────────────────────────────────
# Driver helper
# ─────────────────────────────────────────────────────────────────────────────

def _get_driver():
    from contractai.neo4j_config import get_neo4j_driver
    return get_neo4j_driver()


def _get_embedding(text: str) -> list:
    from embeddings.embedding_service import generate_embedding
    return generate_embedding(text)["embedding"]


# ─────────────────────────────────────────────────────────────────────────────
# 1. Vector similarity search
# ─────────────────────────────────────────────────────────────────────────────

def vector_search(query: str, top_k: int = TOP_K) -> list:
    """
    Find semantically similar clauses.
    Primary: Neo4j vector index.
    Fallback: in-memory keyword search.
    """
    driver = _get_driver()
    if driver is None:
        logger.info("[AutoRAG] Neo4j unavailable — using memory store text search.")
        return memory_store.text_search_normalised(query, top_k)


    query_emb = _get_embedding(query)

    with driver.session() as session:
        try:
            result = session.run(
                """
                CALL db.index.vector.queryNodes(
                    'clause_embedding_index',
                    $top_k,
                    $embedding
                )
                YIELD node, score
                OPTIONAL MATCH (d:Document)-[:HAS_CLAUSE]->(node)
                RETURN
                    node.id           AS clause_id,
                    node.text         AS text,
                    node.risk_level   AS risk_level,
                    node.risk_score   AS risk_score,
                    node.clause_number AS clause_number,
                    node.obligation   AS obligation,
                    node.indemnity    AS indemnity,
                    node.termination  AS termination,
                    node.payment      AS payment,
                    node.temporal_refs AS temporal_refs,
                    d.name            AS document,
                    score
                ORDER BY score DESC
                """,
                top_k=top_k,
                embedding=query_emb,
            )
            return [_row_to_clause(r) for r in result]

        except Exception as e:
            logger.warning(f"[AutoRAG] Vector search failed: {e}. Falling back to text search.")
            return _text_fallback_search(session, query, top_k)


def _text_fallback_search(session, query: str, top_k: int) -> list:
    """Full-text keyword fallback when vector index isn't ready."""
    keywords = " ".join(query.split()[:5])  # use first 5 words
    result = session.run(
        """
        MATCH (c:Clause)
        WHERE toLower(c.text) CONTAINS toLower($keyword)
        OPTIONAL MATCH (d:Document)-[:HAS_CLAUSE]->(c)
        RETURN
            c.id AS clause_id, c.text AS text,
            c.risk_level AS risk_level, c.risk_score AS risk_score,
            c.clause_number AS clause_number,
            c.obligation AS obligation, c.indemnity AS indemnity,
            c.termination AS termination, c.payment AS payment,
            c.temporal_refs AS temporal_refs,
            d.name AS document,
            1.0 AS score
        LIMIT $limit
        """,
        keyword=keywords,
        limit=top_k,
    )
    return [_row_to_clause(r) for r in result]


# ─────────────────────────────────────────────────────────────────────────────
# 2. Filtered graph queries
# ─────────────────────────────────────────────────────────────────────────────

def retrieve_high_risk_clauses(top_k: int = TOP_K) -> list:
    if _get_driver() is None:
        return memory_store.get_high_risk_normalised(top_k)
    return _flag_query("c.risk_level IN ['HIGH', 'CRITICAL']", top_k)


def retrieve_obligation_clauses(top_k: int = TOP_K) -> list:
    if _get_driver() is None:
        return memory_store.get_flag_normalised("obligation", top_k)
    return _flag_query("c.obligation = true", top_k)


def retrieve_indemnity_clauses(top_k: int = TOP_K) -> list:
    if _get_driver() is None:
        return memory_store.get_flag_normalised("indemnity", top_k)
    return _flag_query("c.indemnity = true", top_k)


def retrieve_termination_clauses(top_k: int = TOP_K) -> list:
    if _get_driver() is None:
        return memory_store.get_flag_normalised("termination", top_k)
    return _flag_query("c.termination = true", top_k)


def retrieve_payment_clauses(top_k: int = TOP_K) -> list:
    if _get_driver() is None:
        return memory_store.get_flag_normalised("payment", top_k)
    return _flag_query("c.payment = true", top_k)


def retrieve_temporal_clauses(top_k: int = TOP_K) -> list:
    if _get_driver() is None:
        return memory_store.get_temporal_normalised(top_k)
    return _flag_query("size(c.temporal_refs) > 0", top_k)


def _flag_query(where_clause: str, top_k: int) -> list:
    driver = _get_driver()
    if driver is None:
        return []

    with driver.session() as session:
        try:
            result = session.run(
                f"""
                MATCH (c:Clause)
                WHERE {where_clause}
                OPTIONAL MATCH (d:Document)-[:HAS_CLAUSE]->(c)
                RETURN
                    c.id AS clause_id, c.text AS text,
                    c.risk_level AS risk_level, c.risk_score AS risk_score,
                    c.clause_number AS clause_number,
                    c.obligation AS obligation, c.indemnity AS indemnity,
                    c.termination AS termination, c.payment AS payment,
                    c.temporal_refs AS temporal_refs,
                    d.name AS document,
                    coalesce(c.risk_score, 0.0) AS score
                ORDER BY score DESC
                LIMIT $limit
                """,
                limit=top_k,
            )
            return [_row_to_clause(r) for r in result]
        except Exception as e:
            logger.error(f"[AutoRAG] Flag query failed: {e}")
            return []


# ─────────────────────────────────────────────────────────────────────────────
# 3. Hybrid retrieval (vector + graph enrichment)
# ─────────────────────────────────────────────────────────────────────────────

def hybrid_retrieve(query: str, intent: str = "GENERAL", top_k: int = TOP_K) -> list:
    """
    Intent-aware hybrid retrieval.
    Combines vector similarity with graph-filtered clauses.
    """
    vector_results = vector_search(query, top_k=top_k)

    # Augment with graph-specific results for non-general intents
    extra = []
    if intent == "RISK":
        extra = retrieve_high_risk_clauses(top_k=top_k // 2)
    elif intent == "OBLIGATION":
        extra = retrieve_obligation_clauses(top_k=top_k // 2)
    elif intent == "TERMINATION":
        extra = retrieve_termination_clauses(top_k=top_k // 2)
    elif intent == "PAYMENT":
        extra = retrieve_payment_clauses(top_k=top_k // 2)
    elif intent == "TEMPORAL":
        extra = retrieve_temporal_clauses(top_k=top_k // 2)
    elif intent == "INDEMNITY":
        extra = retrieve_indemnity_clauses(top_k=top_k // 2)

    # Merge, deduplicate by clause_id
    seen_ids = set()
    merged = []
    for c in (vector_results + extra):
        cid = c.get("clause_id") or c.get("text", "")[:40]
        if cid not in seen_ids:
            seen_ids.add(cid)
            merged.append(c)

    return merged[:top_k]


# ─────────────────────────────────────────────────────────────────────────────
# 4. Entity-centric retrieval
# ─────────────────────────────────────────────────────────────────────────────

def retrieve_clauses_by_entity(entity_name: str, top_k: int = TOP_K) -> list:
    """Find all clauses that mention a specific entity (by canonical name)."""
    driver = _get_driver()
    if driver is None:
        return []

    with driver.session() as session:
        try:
            result = session.run(
                """
                MATCH (e:Entity {canonical_name: $name})<-[:MENTIONS_ENTITY]-(c:Clause)
                OPTIONAL MATCH (d:Document)-[:HAS_CLAUSE]->(c)
                RETURN
                    c.id AS clause_id, c.text AS text,
                    c.risk_level AS risk_level, c.risk_score AS risk_score,
                    c.clause_number AS clause_number,
                    c.obligation AS obligation, c.indemnity AS indemnity,
                    c.termination AS termination, c.payment AS payment,
                    c.temporal_refs AS temporal_refs,
                    d.name AS document,
                    1.0 AS score
                LIMIT $limit
                """,
                name=entity_name,
                limit=top_k,
            )
            return [_row_to_clause(r) for r in result]
        except Exception as e:
            logger.error(f"[AutoRAG] Entity query failed: {e}")
            return []


# ─────────────────────────────────────────────────────────────────────────────
# Row normaliser
# ─────────────────────────────────────────────────────────────────────────────

def _row_to_clause(record) -> dict:
    return {
        "clause_id":    record.get("clause_id"),
        "text":         record.get("text", ""),
        "risk_level":   record.get("risk_level", "LOW"),
        "risk_score":   record.get("risk_score", 0.0),
        "clause_number": record.get("clause_number"),
        "obligation":   record.get("obligation", False),
        "indemnity":    record.get("indemnity", False),
        "termination":  record.get("termination", False),
        "payment":      record.get("payment", False),
        "temporal_refs": record.get("temporal_refs", []),
        "document":     record.get("document"),
        "score":        record.get("score", 0.0),
    }
