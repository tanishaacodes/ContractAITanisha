"""
Neo4j Schema Setup
==================
Creates constraints and vector indexes required by the ingestion pipeline.

Run once via Django management command or directly:
    python manage.py shell -c "from ingestion.neo4j_schema import setup_schema; setup_schema()"

Neo4j 5.15+ required for vector index support.
"""

import logging

logger = logging.getLogger(__name__)

CONSTRAINTS = [
    # Unique document names
    """
    CREATE CONSTRAINT document_name_unique IF NOT EXISTS
    FOR (d:Document)
    REQUIRE d.name IS UNIQUE
    """,
    # Unique clause IDs
    """
    CREATE CONSTRAINT clause_id_unique IF NOT EXISTS
    FOR (c:Clause)
    REQUIRE c.id IS UNIQUE
    """,
    # Unique entity (canonical_name + type composite)
    """
    CREATE CONSTRAINT entity_unique IF NOT EXISTS
    FOR (e:Entity)
    REQUIRE (e.canonical_name, e.type) IS UNIQUE
    """,
]

INDEXES = [
    # Risk level property index for fast filtering
    """
    CREATE INDEX clause_risk_index IF NOT EXISTS
    FOR (c:Clause)
    ON (c.risk_level)
    """,
    # Legal flag indexes
    """
    CREATE INDEX clause_obligation_index IF NOT EXISTS
    FOR (c:Clause)
    ON (c.obligation)
    """,
    """
    CREATE INDEX clause_termination_index IF NOT EXISTS
    FOR (c:Clause)
    ON (c.termination)
    """,
]

VECTOR_INDEX = """
CREATE VECTOR INDEX clause_embedding_index IF NOT EXISTS
FOR (c:Clause)
ON (c.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 384,
    `vector.similarity_function`: 'cosine'
  }
}
"""


def setup_schema(force: bool = False) -> dict:
    """
    Create all Neo4j constraints and indexes.

    Args:
        force: If True, drop and recreate vector index.

    Returns:
        Dict summarising what was created / skipped.
    """
    from contractai.neo4j_config import get_neo4j_driver

    driver = get_neo4j_driver()
    if driver is None:
        return {"status": "skipped", "reason": "neo4j_unavailable"}

    results = {"constraints": [], "indexes": [], "vector_index": None}

    with driver.session() as session:

        for stmt in CONSTRAINTS:
            try:
                session.run(stmt)
                results["constraints"].append("ok")
                logger.info("[Schema] Constraint created/verified.")
            except Exception as e:
                results["constraints"].append(f"error: {e}")
                logger.warning(f"[Schema] Constraint error: {e}")

        for stmt in INDEXES:
            try:
                session.run(stmt)
                results["indexes"].append("ok")
                logger.info("[Schema] Index created/verified.")
            except Exception as e:
                results["indexes"].append(f"error: {e}")
                logger.warning(f"[Schema] Index error: {e}")

        # Vector index
        try:
            if force:
                session.run("DROP INDEX clause_embedding_index IF EXISTS")
            session.run(VECTOR_INDEX)
            results["vector_index"] = "ok"
            logger.info("[Schema] Vector index created/verified.")
        except Exception as e:
            results["vector_index"] = f"error: {e}"
            logger.warning(f"[Schema] Vector index error: {e}")

    return {"status": "done", **results}
