"""
Neo4j Writer
============
Persists enriched contract documents, clauses, and entities
into the Neo4j graph database.

Graph schema written here:
  (:Document)-[:HAS_CLAUSE]->(:Clause)
  (:Clause)-[:MENTIONS_ENTITY]->(:Entity)
  (:Entity)-[:CO_OCCURS_WITH]->(:Entity)
  (:Clause)-[:HAS_TEMPORAL]->(:TemporalEntity)

Uses the existing contractai.neo4j_config.get_neo4j_driver() singleton.
"""

import uuid
import logging

logger = logging.getLogger(__name__)


def _get_driver():
    from contractai.neo4j_config import get_neo4j_driver
    return get_neo4j_driver()


# ─────────────────────────────────────────────────────────────────────────────
# Document + Clause persistence
# ─────────────────────────────────────────────────────────────────────────────

def write_contract(document_name: str, clauses: list) -> dict:
    """
    Write a full contract (document + enriched clauses + entities) to Neo4j.

    Args:
        document_name: Human-readable name / filename of the contract.
        clauses:       List of enriched clause dicts (output of enrichment.enrich_clauses).

    Returns:
        Summary dict with node/relationship counts.
    """
    driver = _get_driver()
    if driver is None:
        logger.warning("Neo4j unavailable — skipping graph persistence.")
        return {"status": "skipped", "reason": "neo4j_unavailable"}

    stats = {"document": 1, "clauses": 0, "entities": 0, "relationships": 0}

    with driver.session() as session:

        # ── Document node ──────────────────────────────────────────────────
        doc_id = _upsert_document(session, document_name)

        # ── Entity dedup cache (within this document) ──────────────────────
        entity_node_map: dict = {}  # canonical_name → neo4j node id

        for clause in clauses:
            clause_id = clause["id"]
            risk = clause.get("risk", {})
            flags = clause.get("flags", {})

            # ── Clause node ─────────────────────────────────────────────────
            # Serialize complex fields as JSON strings for Neo4j storage
            import json as _json
            session.run(
                """
                MERGE (cl:Clause {id: $id})
                SET cl.text             = $text,
                    cl.clause_number    = $clause_number,
                    cl.embedding        = $embedding,
                    cl.risk_level       = $risk_level,
                    cl.risk_score       = $risk_score,
                    cl.obligation       = $obligation,
                    cl.indemnity        = $indemnity,
                    cl.termination      = $termination,
                    cl.payment          = $payment,
                    cl.exclusivity      = $exclusivity,
                    cl.ip_clause        = $ip_clause,
                    cl.temporal_refs    = $temporal,
                    cl.obligations_svo  = $obligations_svo,
                    cl.monetary_values  = $monetary_values,
                    cl.regulatory_refs  = $regulatory_refs
                """,
                id=clause_id,
                text=clause.get("text", ""),
                clause_number=clause.get("clause_number"),
                embedding=clause.get("embedding", []),
                risk_level=risk.get("risk_level", "LOW"),
                risk_score=risk.get("score", 0.0),
                obligation=flags.get("obligation", False),
                indemnity=flags.get("indemnity", False),
                termination=flags.get("termination", False),
                payment=flags.get("payment", False),
                exclusivity=flags.get("exclusivity", False),
                ip_clause=flags.get("ip_clause", False),
                temporal=clause.get("temporal", []),
                obligations_svo=_json.dumps(clause.get("obligations_svo", [])),
                monetary_values=_json.dumps(clause.get("monetary_values", [])),
                regulatory_refs=clause.get("regulatory_refs", []),
            )
            stats["clauses"] += 1

            # ── Document → Clause ────────────────────────────────────────────
            session.run(
                """
                MATCH (d:Document {id: $doc_id})
                MATCH (cl:Clause   {id: $clause_id})
                MERGE (d)-[:HAS_CLAUSE]->(cl)
                """,
                doc_id=doc_id,
                clause_id=clause_id,
            )
            stats["relationships"] += 1

            # ── Entities ─────────────────────────────────────────────────────
            entity_ids_in_clause = []

            for ent in clause.get("entities", []):
                canonical = ent["name"]
                ent_type = ent["type"]
                key = (canonical.lower(), ent_type)

                if key not in entity_node_map:
                    ent_node_id = str(uuid.uuid4())
                    session.run(
                        """
                        MERGE (e:Entity {canonical_name: $canonical, type: $etype})
                        ON CREATE SET e.id = $eid
                        """,
                        canonical=canonical,
                        etype=ent_type,
                        eid=ent_node_id,
                    )
                    entity_node_map[key] = canonical
                    stats["entities"] += 1

                # Clause → Entity
                session.run(
                    """
                    MATCH (cl:Clause {id: $clause_id})
                    MATCH (e:Entity  {canonical_name: $canonical, type: $etype})
                    MERGE (cl)-[:MENTIONS_ENTITY]->(e)
                    """,
                    clause_id=clause_id,
                    canonical=canonical,
                    etype=ent_type,
                )
                stats["relationships"] += 1
                entity_ids_in_clause.append((canonical, ent_type))

            # ── Co-occurrence edges between entities in the same clause ───────
            for i in range(len(entity_ids_in_clause)):
                for j in range(i + 1, len(entity_ids_in_clause)):
                    a_name, a_type = entity_ids_in_clause[i]
                    b_name, b_type = entity_ids_in_clause[j]
                    session.run(
                        """
                        MATCH (a:Entity {canonical_name: $a_name, type: $a_type})
                        MATCH (b:Entity {canonical_name: $b_name, type: $b_type})
                        MERGE (a)-[:CO_OCCURS_WITH]->(b)
                        """,
                        a_name=a_name, a_type=a_type,
                        b_name=b_name, b_type=b_type,
                    )
                    stats["relationships"] += 1

    logger.info(
        f"[Neo4j] Contract '{document_name}' written — "
        f"{stats['clauses']} clauses, {stats['entities']} entities"
    )
    return {"status": "ok", **stats}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _upsert_document(session, document_name: str) -> str:
    """Create or update a Document node; return its id."""
    result = session.run(
        """
        MERGE (d:Document {name: $name})
        ON CREATE SET d.id = $new_id
        RETURN d.id AS doc_id
        """,
        name=document_name,
        new_id=str(uuid.uuid4()),
    )
    record = result.single()
    return record["doc_id"]
