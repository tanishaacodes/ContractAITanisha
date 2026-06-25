"""
Ingestion API Views
====================
POST /api/ingestion/upload/     — Upload contract text or file path, index to Neo4j
POST /api/ingestion/schema/     — Set up Neo4j schema (admin only)
GET  /api/ingestion/status/     — Pipeline health check
"""

import os
import logging
import tempfile

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, JSONParser

from .document_reader import extract_text, extract_text_from_string
from .clause_extractor import extract_clauses
from .enrichment import enrich_clauses, clear_entity_store
from .neo4j_writer import write_contract
from .neo4j_schema import setup_schema
from . import memory_store

logger = logging.getLogger(__name__)


class ContractIngestionView(APIView):
    """
    POST /api/ingestion/upload/

    Accepts either:
      a) multipart file upload  (field: "file", optional: "name")
      b) JSON body              {"name": str, "text": str}

    Pipeline:
      text → clause extraction → enrichment → Neo4j persistence
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, JSONParser]

    def post(self, request):
        try:
            document_name, text = self._resolve_input(request)
        except ValueError as e:
            # Includes PDF extractor errors — surface the real reason
            return Response({"error": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as e:
            logger.error(f"Input extraction failed: {e}")
            return Response({"error": f"Failed to read document: {e}"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        if not text or len(text.strip()) < 30:
            return Response({
                "error": "No extractable text found in document.",
                "hint": "The PDF may be scanned/image-based. Please paste the contract text manually in the text field instead."
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # Run the pipeline
        try:
            clauses = extract_clauses(text)
            logger.info(f"[Ingestion] '{document_name}': {len(clauses)} clauses extracted")

            enriched = enrich_clauses(clauses)

            # Tag each clause with its document name for cross-doc retrieval
            for c in enriched:
                c["document_name"] = document_name

            # Always save to in-memory store (works without Neo4j)
            memory_store.save_clauses(enriched)
            logger.info(f"[MemoryStore] {len(enriched)} clauses saved. Total: {memory_store.count()}")

            # Also persist to Neo4j when available
            neo4j_result = write_contract(document_name, enriched)

            return Response({
                "status": "indexed",
                "document": document_name,
                "clauses_extracted": len(clauses),
                "neo4j": neo4j_result,
                "memory_store_total": memory_store.count(),
                "risk_summary": _build_risk_summary(enriched),
                "flag_summary": _build_flag_summary(enriched),
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.exception(f"[Ingestion] Pipeline error for '{document_name}': {e}")
            return Response({"error": "Internal pipeline error.", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _resolve_input(self, request):
        """Return (document_name, text) from either file upload or JSON body."""
        if request.FILES.get("file"):
            uploaded = request.FILES["file"]
            document_name = request.data.get("name") or uploaded.name
            ext = uploaded.name.rsplit(".", 1)[-1].lower()

            # Write to temp file for extraction
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                for chunk in uploaded.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name

            try:
                text = extract_text(tmp_path)
            finally:
                os.unlink(tmp_path)

            return document_name, text

        # JSON body
        document_name = request.data.get("name", "").strip()
        raw_text = request.data.get("text", "").strip()

        if not document_name:
            raise ValueError("'name' field is required.")
        if not raw_text:
            raise ValueError("'text' field is required when not uploading a file.")

        return document_name, extract_text_from_string(raw_text)


class SchemaSetupView(APIView):
    """
    POST /api/ingestion/schema/
    Creates Neo4j constraints and vector index (idempotent).
    Restricted to admin users.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"error": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)

        force = request.data.get("force", False)
        result = setup_schema(force=bool(force))
        return Response(result)


class IngestionStatusView(APIView):
    """GET /api/ingestion/status/ — Health check for the ingestion pipeline."""
    permission_classes = [AllowAny]

    def get(self, request):
        from contractai.neo4j_config import check_neo4j_available
        from embeddings.embedding_service import is_transformer_available

        return Response({
            "neo4j_connected": check_neo4j_available(),
            "embeddings_ready": is_transformer_available(),
        })


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_risk_summary(clauses: list) -> dict:
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for c in clauses:
        level = c.get("risk", {}).get("risk_level", "LOW")
        counts[level] = counts.get(level, 0) + 1
    return counts


def _build_flag_summary(clauses: list) -> dict:
    summary = {
        "obligation": 0, "indemnity": 0,
        "termination": 0, "payment": 0,
        "exclusivity": 0, "ip_clause": 0,
    }
    for c in clauses:
        for flag, triggered in c.get("flags", {}).items():
            if triggered:
                summary[flag] = summary.get(flag, 0) + 1
    return summary
