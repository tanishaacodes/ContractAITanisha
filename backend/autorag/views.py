"""
AutoRAG API Views
==================
POST /api/autorag/ask/           — Natural language question over indexed contracts
POST /api/autorag/ask/entity/    — Query scoped to a specific entity
GET  /api/autorag/clauses/risk/  — Retrieve all HIGH/CRITICAL clauses
GET  /api/autorag/clauses/flags/ — Retrieve clauses by legal flag type
GET  /api/autorag/graph/         — Return Neo4j graph data (nodes + links) for visualisation
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from .orchestrator import answer_query, answer_entity_query
from .retriever import (
    retrieve_high_risk_clauses,
    retrieve_obligation_clauses,
    retrieve_indemnity_clauses,
    retrieve_termination_clauses,
    retrieve_payment_clauses,
    retrieve_temporal_clauses,
)

logger = logging.getLogger(__name__)


class AskView(APIView):
    """
    POST /api/autorag/ask/

    Body:
        {
            "query": "What are the termination conditions?",
            "document": "contract.pdf"   (optional — scope to one doc)
        }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        query = request.data.get("query", "").strip()
        if not query:
            return Response({"error": "'query' is required."}, status=status.HTTP_400_BAD_REQUEST)

        document_filter = request.data.get("document")

        try:
            result = answer_query(query, document_filter=document_filter)
            return Response(result)
        except Exception as e:
            logger.exception(f"[AutoRAG] ask/ error: {e}")
            return Response({"error": "AutoRAG pipeline error.", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AskEntityView(APIView):
    """
    POST /api/autorag/ask/entity/

    Body:
        {
            "query": "What obligations does Acme Corp have?",
            "entity": "Acme Corp"
        }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        query = request.data.get("query", "").strip()
        entity = request.data.get("entity", "").strip()

        if not query or not entity:
            return Response({"error": "'query' and 'entity' are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = answer_entity_query(query, entity)
            return Response(result)
        except Exception as e:
            logger.exception(f"[AutoRAG] ask/entity/ error: {e}")
            return Response({"error": "AutoRAG pipeline error.", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RiskClausesView(APIView):
    """GET /api/autorag/clauses/risk/ — Return HIGH + CRITICAL clauses."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        top_k = int(request.query_params.get("limit", 20))
        clauses = retrieve_high_risk_clauses(top_k=top_k)
        return Response({"count": len(clauses), "clauses": clauses})


class FlagClausesView(APIView):
    """
    GET /api/autorag/clauses/flags/?type=obligation

    Supported types: obligation, indemnity, termination, payment, temporal
    """
    permission_classes = [IsAuthenticated]

    _RETRIEVERS = {
        "obligation":  retrieve_obligation_clauses,
        "indemnity":   retrieve_indemnity_clauses,
        "termination": retrieve_termination_clauses,
        "payment":     retrieve_payment_clauses,
        "temporal":    retrieve_temporal_clauses,
    }

    def get(self, request):
        flag_type = request.query_params.get("type", "").lower()
        top_k = int(request.query_params.get("limit", 20))

        retriever_fn = self._RETRIEVERS.get(flag_type)
        if not retriever_fn:
            return Response(
                {"error": f"Unknown flag type '{flag_type}'. Supported: {list(self._RETRIEVERS.keys())}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        clauses = retriever_fn(top_k=top_k)
        return Response({"type": flag_type, "count": len(clauses), "clauses": clauses})


class GraphDataView(APIView):
    """
    GET /api/autorag/graph/?document=<optional name>

    Returns Neo4j graph data as nodes + links for force-directed visualisation.
    Falls back to memory store when Neo4j is unavailable.

    Node types: Document (cyan), Clause (violet), Entity (orange/green/blue by type)
    Link types: HAS_CLAUSE, MENTIONS_ENTITY, CO_OCCURS_WITH
    """
    permission_classes = [IsAuthenticated]

    _ENTITY_COLORS = {
        "ORG":    "#f97316",   # orange
        "PERSON": "#a78bfa",   # violet
        "GPE":    "#34d399",   # green
        "LAW":    "#60a5fa",   # blue
        "MONEY":  "#fbbf24",   # amber
        "DATE":   "#f472b6",   # pink
    }

    def get(self, request):
        document_filter = request.query_params.get("document")
        from contractai.neo4j_config import get_neo4j_driver
        from ingestion import memory_store

        driver = get_neo4j_driver()
        if driver:
            return Response(self._from_neo4j(driver, document_filter))
        # Fallback: build graph from memory store
        return Response(self._from_memory(memory_store, document_filter))

    # ── Neo4j path ─────────────────────────────────────────────────────────────
    def _from_neo4j(self, driver, document_filter):
        nodes, links = [], []
        node_ids = set()

        with driver.session() as session:
            # ── Documents ───────────────────────────────────────────────────────
            doc_query = (
                "MATCH (d:Document) WHERE $name IS NULL OR d.name = $name "
                "RETURN d.id AS id, d.name AS name ORDER BY d.name LIMIT 10"
            )
            docs = session.run(doc_query, name=document_filter).data()
            for d in docs:
                did = d["id"] or f"doc_{d['name']}"
                if did not in node_ids:
                    nodes.append({"id": did, "label": d["name"], "type": "Document", "color": "#22d3ee"})
                    node_ids.add(did)

            if not docs:
                return {"nodes": [], "links": [], "stats": {"documents": 0, "clauses": 0, "entities": 0}}

            doc_names = [d["name"] for d in docs]

            # ── Clauses ─────────────────────────────────────────────────────────
            clause_query = (
                "MATCH (d:Document)-[:HAS_CLAUSE]->(c:Clause) "
                "WHERE d.name IN $names "
                "RETURN d.id AS doc_id, d.name AS doc_name, "
                "c.id AS cid, c.clause_number AS num, c.risk_level AS risk, c.text AS text "
                "LIMIT 60"
            )
            clauses = session.run(clause_query, names=doc_names).data()
            for c in clauses:
                did = c["doc_id"] or f"doc_{c['doc_name']}"
                cid = c["cid"]
                if cid and cid not in node_ids:
                    risk = c["risk"] or "LOW"
                    color = {"CRITICAL": "#ef4444", "HIGH": "#f97316", "MEDIUM": "#eab308", "LOW": "#22c55e"}.get(risk, "#94a3b8")
                    label = f"§{c['num']}" if c["num"] else "Clause"
                    preview = (c["text"] or "")[:60]
                    nodes.append({"id": cid, "label": label, "type": "Clause", "color": color, "risk": risk, "preview": preview})
                    node_ids.add(cid)
                if did in node_ids and cid and cid in node_ids:
                    links.append({"source": did, "target": cid, "type": "HAS_CLAUSE"})

            # ── Entities ────────────────────────────────────────────────────────
            entity_query = (
                "MATCH (d:Document)-[:HAS_CLAUSE]->(c:Clause)-[:MENTIONS_ENTITY]->(e:Entity) "
                "WHERE d.name IN $names "
                "RETURN DISTINCT c.id AS cid, e.canonical_name AS name, e.type AS etype "
                "LIMIT 120"
            )
            entities = session.run(entity_query, names=doc_names).data()
            for e in entities:
                eid = f"ent_{e['name']}_{e['etype']}"
                cid = e["cid"]
                if eid not in node_ids:
                    color = self._ENTITY_COLORS.get(e["etype"], "#94a3b8")
                    nodes.append({"id": eid, "label": e["name"], "type": e["etype"] or "Entity", "color": color})
                    node_ids.add(eid)
                if cid and cid in node_ids:
                    links.append({"source": cid, "target": eid, "type": "MENTIONS_ENTITY"})

        stats = {
            "documents": sum(1 for n in nodes if n["type"] == "Document"),
            "clauses":   sum(1 for n in nodes if n["type"] == "Clause"),
            "entities":  sum(1 for n in nodes if n["type"] not in ("Document", "Clause")),
        }
        return {"nodes": nodes, "links": links, "stats": stats, "source": "neo4j"}

    # ── Memory store fallback ───────────────────────────────────────────────────
    def _from_memory(self, memory_store, document_filter):
        clauses = memory_store.get_all()
        if document_filter:
            clauses = [c for c in clauses if c.get("document_name") == document_filter]

        nodes, links = [], []
        node_ids = set()
        doc_map = {}   # doc_name → node id

        for c in clauses[:60]:
            doc_name = c.get("document_name", "Unknown")
            risk = c.get("risk", {}).get("risk_level", "LOW")
            cid = c.get("id") or c.get("clause_id")
            if not cid:
                continue

            # Document node
            if doc_name not in doc_map:
                did = f"doc_{doc_name}"
                doc_map[doc_name] = did
                nodes.append({"id": did, "label": doc_name, "type": "Document", "color": "#22d3ee"})
                node_ids.add(did)

            did = doc_map[doc_name]
            color = {"CRITICAL": "#ef4444", "HIGH": "#f97316", "MEDIUM": "#eab308", "LOW": "#22c55e"}.get(risk, "#94a3b8")
            num = c.get("clause_number")
            label = f"§{num}" if num else "Clause"
            preview = (c.get("text") or "")[:60]
            nodes.append({"id": cid, "label": label, "type": "Clause", "color": color, "risk": risk, "preview": preview})
            node_ids.add(cid)
            links.append({"source": did, "target": cid, "type": "HAS_CLAUSE"})

            for ent in c.get("entities", [])[:5]:
                eid = f"ent_{ent['name']}_{ent['type']}"
                if eid not in node_ids:
                    color = self._ENTITY_COLORS.get(ent["type"], "#94a3b8")
                    nodes.append({"id": eid, "label": ent["name"], "type": ent["type"], "color": color})
                    node_ids.add(eid)
                links.append({"source": cid, "target": eid, "type": "MENTIONS_ENTITY"})

        stats = {
            "documents": sum(1 for n in nodes if n["type"] == "Document"),
            "clauses":   sum(1 for n in nodes if n["type"] == "Clause"),
            "entities":  sum(1 for n in nodes if n["type"] not in ("Document", "Clause")),
        }
        return {"nodes": nodes, "links": links, "stats": stats, "source": "memory"}
