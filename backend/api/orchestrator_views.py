"""
Orchestrator Django Views
==========================
POST /api/analyze-contract/                          – run full pipeline (contract-first)
GET  /api/analyze-contract/<analysis_id>/            – retrieve stored result
GET  /api/analyze-contract/contract/<contract_id>/latest/  – latest result for a contract
GET  /api/analyze-contract/contract/<contract_id>/all/     – all results for a contract

Legacy (kept for backwards compatibility):
POST /api/ai-studio/full-analysis/
GET  /api/ai-studio/analysis-result/<id>/
"""

import io
import logging

from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from api.orchestrator import run_full_analysis, get_cached_result

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _extract_text_from_file(uploaded_file) -> str:
    """Extract raw text from an uploaded file (txt, md, or generic binary)."""
    name = (uploaded_file.name or "").lower()
    raw = uploaded_file.read()

    if name.endswith(".pdf"):
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(raw)) as pdf:
                return "\n\n".join(p.extract_text() or "" for p in pdf.pages)
        except ImportError:
            pass
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(raw))
            return "\n\n".join(
                reader.pages[i].extract_text() or "" for i in range(len(reader.pages))
            )
        except Exception:
            pass

    # Fallback: decode as UTF-8 (covers .txt, .md, .rst, raw text)
    try:
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""


def _persist_analysis(result: dict, input_source: str) -> None:
    """Write pipeline output to the database (fire-and-forget on error)."""
    try:
        from negotiation.models import (
            ContractAnalysisResult,
            AnalysisClause,
            AnalysisClauseRisk,
            AnalysisNegotiationResult,
        )
        import uuid

        def _gen():
            return str(uuid.uuid4())

        contract_fk = None
        contract_id_ref = result.get("contract_id")
        if contract_id_ref:
            try:
                from core.models import Contract
                contract_fk = Contract.objects.filter(id=contract_id_ref).first()
            except Exception:
                pass

        # Top-level record
        ar = ContractAnalysisResult.objects.create(
            id=_gen(),
            analysis_id=result["analysis_id"],
            contract=contract_fk,
            contract_id_ref=contract_id_ref,
            jurisdiction=result.get("jurisdiction", "india"),
            contract_value=result.get("cfo_result", {}).get("contract_value", 0),
            duration_months=12,
            final_score=result.get("final_score", 0),
            decision=result.get("decision", "RENEGOTIATE"),
            score_breakdown=result.get("score_breakdown", {}),
            risk_summary=result.get("risk_summary", {}),
            cfo_result=result.get("cfo_result", {}),
            recommendations=result.get("recommendations", []),
            pipeline_trace=result.get("pipeline_trace", []),
            total_duration_ms=result.get("total_duration_ms", 0),
            input_source=input_source,
            status=result.get("status", "complete"),
        )

        # Build a lookup from clause ref-id → AnalysisClause row
        clause_map: dict = {}
        for c in result.get("clauses", []):
            ac = AnalysisClause.objects.create(
                id=_gen(),
                analysis=ar,
                clause_ref_id=str(c.get("id", "")),
                title=str(c.get("title", ""))[:500],
                text=str(c.get("text", "")),
                clause_type=str(c.get("type", "general"))[:100],
            )
            clause_map[str(c.get("id", ""))] = ac

        for risk in result.get("legal_risks", []):
            AnalysisClauseRisk.objects.create(
                id=_gen(),
                analysis=ar,
                clause=clause_map.get(str(risk.get("clause_id", ""))),
                clause_ref_id=str(risk.get("clause_id", ""))[:100],
                clause_title=str(risk.get("clause_title", ""))[:500],
                risk_level=str(risk.get("risk_level", "MEDIUM"))[:20],
                compliance_status=str(risk.get("compliance_status", ""))[:100],
                confidence_score=float(risk.get("confidence_score", 0.5)),
                issues=risk.get("issues", []),
                explanation=str(risk.get("explanation", "")),
                suggested_clause=str(risk.get("suggested_clause", "")),
                rule_flags=risk.get("rule_flags", []),
            )

        for neg in result.get("negotiation_results", []):
            AnalysisNegotiationResult.objects.create(
                id=_gen(),
                analysis=ar,
                clause_ref_id=str(neg.get("clause_id", ""))[:100],
                clause_title=str(neg.get("clause_title", ""))[:500],
                original_risk=str(neg.get("original_risk", "MEDIUM"))[:20],
                final_clause=str(neg.get("final_clause", "")),
                best_clause=str(neg.get("best_clause", "")),
                final_score=float(neg.get("final_score", 0)),
                converged=bool(neg.get("converged", False)),
                rounds_completed=int(neg.get("rounds", 0)),
                score_trend=str(neg.get("score_trend", ""))[:50],
            )

        logger.info("Persisted analysis %s to DB (input_source=%s)", result["analysis_id"], input_source)
    except Exception as exc:
        logger.warning("DB persist failed (non-fatal): %s", exc)


def _result_from_db(analysis_id: str) -> dict | None:
    """Load a stored analysis from the DB and reconstruct the pipeline result dict."""
    try:
        from negotiation.models import ContractAnalysisResult
        ar = ContractAnalysisResult.objects.prefetch_related(
            "stored_clauses", "stored_clause_risks", "stored_negotiation_results"
        ).get(analysis_id=analysis_id)

        clauses = [
            {"id": c.clause_ref_id, "title": c.title, "text": c.text, "type": c.clause_type}
            for c in ar.stored_clauses.all()
        ]
        legal_risks = [
            {
                "clause_id":         r.clause_ref_id,
                "clause_title":      r.clause_title,
                "risk_level":        r.risk_level,
                "compliance_status": r.compliance_status,
                "confidence_score":  r.confidence_score,
                "issues":            r.issues,
                "explanation":       r.explanation,
                "suggested_clause":  r.suggested_clause,
                "rule_flags":        r.rule_flags,
            }
            for r in ar.stored_clause_risks.all()
        ]
        negotiation_results = [
            {
                "clause_id":    n.clause_ref_id,
                "clause_title": n.clause_title,
                "original_risk": n.original_risk,
                "final_clause": n.final_clause,
                "best_clause":  n.best_clause,
                "final_score":  n.final_score,
                "converged":    n.converged,
                "rounds":       n.rounds_completed,
                "score_trend":  n.score_trend,
            }
            for n in ar.stored_negotiation_results.all()
        ]
        return {
            "analysis_id":        ar.analysis_id,
            "contract_id":        ar.contract_id_ref,
            "jurisdiction":       ar.jurisdiction,
            "status":             ar.status,
            "clauses":            clauses,
            "legal_risks":        legal_risks,
            "cfo_result":         ar.cfo_result,
            "negotiation_results": negotiation_results,
            "score_breakdown":    ar.score_breakdown,
            "final_score":        ar.final_score,
            "decision":           ar.decision,
            "recommendations":    ar.recommendations,
            "risk_summary":       ar.risk_summary,
            "pipeline_trace":     ar.pipeline_trace,
            "total_duration_ms":  ar.total_duration_ms,
            "created_at":         ar.created_at.isoformat(),
            "input_source":       ar.input_source,
        }
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/analyze-contract/
# ──────────────────────────────────────────────────────────────────────────────

class AnalyzeContractView(APIView):
    """
    Primary contract analysis endpoint.

    Accepts (multipart/form-data OR application/json):
      contract_id     – UUID of an existing contract in the DB  ─┐ at least
      document        – uploaded file (.txt / .pdf / .md)       ─┘ one required
      raw_text        – fallback raw text (optional)
      jurisdiction    – "india" | "us" | "uk"  (default "india")
      contract_value  – numeric
      duration_months – integer
      clauses         – JSON list of {title, text} (optional override)
    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        data = request.data

        contract_id  = data.get("contract_id") or None
        raw_text     = data.get("raw_text") or None
        document     = request.FILES.get("document")

        # ── Validate: need contract_id, document, or raw_text ────────────────
        if not contract_id and not document and not raw_text:
            return Response(
                {"error": "Provide a contract_id, upload a document file, or paste raw_text."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Determine input_source ────────────────────────────────────────────
        if contract_id:
            input_source = "contract_id"
        elif document:
            input_source = "file_upload"
        else:
            input_source = "raw_text"

        # ── Extract text from uploaded file ───────────────────────────────────
        if document and not raw_text:
            raw_text = _extract_text_from_file(document)
            if not raw_text or not raw_text.strip():
                return Response(
                    {"error": "Could not extract text from uploaded file."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ── Parse numeric params ──────────────────────────────────────────────
        try:
            contract_value = float(data.get("contract_value", 100_000))
        except (TypeError, ValueError):
            contract_value = 100_000.0

        try:
            duration_months = int(data.get("duration_months", 12))
        except (TypeError, ValueError):
            duration_months = 12

        jurisdiction = str(data.get("jurisdiction", "india")).lower()
        if jurisdiction not in ("india", "us", "uk"):
            jurisdiction = "india"

        # ── Optional pre-supplied clause list ─────────────────────────────────
        raw_clauses = None
        clauses_input = data.get("clauses")
        if isinstance(clauses_input, list) and clauses_input:
            raw_clauses = [
                {
                    "id":    f"input-{i}",
                    "title": c.get("title") or f"Clause {i + 1}",
                    "text":  str(c.get("text", ""))[:800],
                    "type":  c.get("type", "general"),
                }
                for i, c in enumerate(clauses_input[:20])
                if c.get("text")
            ]

        logger.info(
            "analyze-contract: input_source=%s contract_id=%s jurisdiction=%s value=%.0f",
            input_source, contract_id, jurisdiction, contract_value,
        )

        try:
            result = run_full_analysis(
                contract_id     = contract_id,
                jurisdiction    = jurisdiction,
                contract_value  = contract_value,
                duration_months = duration_months,
                raw_clauses     = raw_clauses,
                raw_text        = raw_text,
            )
            # Persist to DB in the same request (fast enough; move to Celery if needed)
            _persist_analysis(result, input_source)
            return Response(result, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.exception("analyze-contract pipeline error: %s", exc)
            return Response(
                {"error": "Analysis pipeline failed.", "detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/analyze-contract/<analysis_id>/
# ──────────────────────────────────────────────────────────────────────────────

class AnalysisStoredResultView(APIView):
    """Retrieve a previously computed analysis — checks DB first, then in-memory cache."""
    permission_classes = [AllowAny]

    def get(self, request, analysis_id: str):
        # DB is source of truth
        result = _result_from_db(analysis_id)
        if result is None:
            # Fallback to in-memory cache (for very recent results not yet persisted)
            result = get_cached_result(analysis_id)
        if result is None:
            return Response(
                {"error": "Analysis result not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(result, status=status.HTTP_200_OK)


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/analyze-contract/contract/<contract_id>/latest/
# ──────────────────────────────────────────────────────────────────────────────

class ContractLatestAnalysisView(APIView):
    """Return the most recent analysis for a given contract_id (read by other modules)."""
    permission_classes = [AllowAny]

    def get(self, request, contract_id: str):
        try:
            from negotiation.models import ContractAnalysisResult
            ar = (
                ContractAnalysisResult.objects
                .filter(contract_id_ref=contract_id)
                .order_by("-created_at")
                .first()
            )
            if ar is None:
                return Response(
                    {"error": "No analysis found for this contract."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            result = _result_from_db(ar.analysis_id)
            if result is None:
                return Response({"error": "Could not reconstruct analysis."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("ContractLatestAnalysisView error: %s", exc)
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/analyze-contract/contract/<contract_id>/all/
# ──────────────────────────────────────────────────────────────────────────────

class ContractAllAnalysesView(APIView):
    """List all analyses for a contract (summary only, no clause detail)."""
    permission_classes = [AllowAny]

    def get(self, request, contract_id: str):
        try:
            from negotiation.models import ContractAnalysisResult
            qs = (
                ContractAnalysisResult.objects
                .filter(contract_id_ref=contract_id)
                .order_by("-created_at")
                .values(
                    "analysis_id", "final_score", "decision",
                    "jurisdiction", "input_source", "status", "created_at",
                )[:20]
            )
            return Response(list(qs), status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ──────────────────────────────────────────────────────────────────────────────
# Legacy endpoints (kept for backwards compatibility with existing frontend code)
# ──────────────────────────────────────────────────────────────────────────────

class FullAnalysisView(APIView):
    """
    POST /api/ai-studio/full-analysis/  (legacy – delegates to AnalyzeContractView)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data            = request.data
        contract_id     = data.get("contract_id") or None
        jurisdiction    = str(data.get("jurisdiction", "india")).lower()
        raw_text        = data.get("raw_text") or None

        try:
            contract_value  = float(data.get("contract_value", 100_000))
        except (TypeError, ValueError):
            contract_value  = 100_000.0

        try:
            duration_months = int(data.get("duration_months", 12))
        except (TypeError, ValueError):
            duration_months = 12

        raw_clauses = None
        clauses_input = data.get("clauses")
        if isinstance(clauses_input, list) and clauses_input:
            raw_clauses = [
                {
                    "id":    f"input-{i}",
                    "title": c.get("title") or f"Clause {i + 1}",
                    "text":  str(c.get("text", ""))[:800],
                    "type":  c.get("type", "general"),
                }
                for i, c in enumerate(clauses_input[:20])
                if c.get("text")
            ]

        if jurisdiction not in ("india", "us", "uk"):
            jurisdiction = "india"

        try:
            result = run_full_analysis(
                contract_id     = contract_id,
                jurisdiction    = jurisdiction,
                contract_value  = contract_value,
                duration_months = duration_months,
                raw_clauses     = raw_clauses,
                raw_text        = raw_text,
            )
            input_source = "contract_id" if contract_id else ("raw_text" if raw_text else "clauses")
            _persist_analysis(result, input_source)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("Orchestrator pipeline error: %s", exc)
            return Response(
                {"error": "Full analysis pipeline failed.", "detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AnalysisResultView(APIView):
    """
    GET /api/ai-studio/analysis-result/<analysis_id>/  (legacy)
    """
    permission_classes = [AllowAny]

    def get(self, request, analysis_id: str):
        result = _result_from_db(analysis_id) or get_cached_result(analysis_id)
        if result is None:
            return Response(
                {"error": "Analysis result not found or expired."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(result, status=status.HTTP_200_OK)
