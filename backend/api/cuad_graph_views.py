"""
CUAD Graph Views
================
REST API endpoints for the CUAD Graph-Based Contract Intelligence System.

Original Endpoints:
  POST /api/cuad-graph/ingest/<contract_id>/   — Ingest contract into Neo4j
  GET  /api/cuad-graph/compare/                — Compare two contracts (diff graph)
  GET  /api/cuad-graph/pagerank/<contract_id>/ — Clause influence via PageRank
  POST /api/cuad-graph/similarity/             — Contract structural similarity
  POST /api/cuad-graph/gnn-score/              — GNN risk/stability score

New Endpoints (all 11 features):
  POST /api/cuad-graph/rag-analyze/            — GraphRAG + Qwen analysis of one contract
  POST /api/cuad-graph/rag-compare/            — GraphRAG + Qwen comparison of two contracts
  POST /api/cuad-graph/rag-negotiate/          — AI negotiation recommendations
  POST /api/cuad-graph/gnn-train/              — Train GNN (200-epoch loop)
  POST /api/cuad-graph/build-similar/          — Persist SIMILAR edges in Neo4j
  POST /api/cuad-graph/ingest-cuad-json/       — Bulk CUAD JSON ingestion
  GET  /api/cuad-graph/gds-pagerank/<id>/      — Native Neo4j GDS PageRank
  POST /api/cuad-graph/gds-similarity/         — Native Neo4j GDS NodeSimilarity
  POST /api/cuad-graph/amendment/              — Track amendment (temporal graph)
  GET  /api/cuad-graph/amendments/<id>/        — Get amendment history
"""

import logging

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.parsers import JSONParser

from .services.cuad_graph_service import CUADGraphService
from .services.cuad_graph_rag import CUADGraphRAG

logger = logging.getLogger(__name__)


def _service() -> CUADGraphService:
    """Return a fresh service instance (stateless)."""
    return CUADGraphService()


# ─────────────────────────────────────────────────────────────────────────────
# 1. Ingest Contract into Neo4j
# ─────────────────────────────────────────────────────────────────────────────

class IngestContractGraphView(APIView):
    """
    POST /api/cuad-graph/ingest/<contract_id>/

    Builds a full CUAD-style Neo4j graph from an existing MySQL contract.
    Node types: Contract, Clause, ClauseType, Party, Jurisdiction, Obligation, Risk, Industry
    """

    def post(self, request, contract_id):
        try:
            svc = _service()
            result = svc.ingest_contract_graph(str(contract_id))

            if "error" in result:
                return Response(
                    {"error": result["error"]},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[CUAD-INGEST] Error: {e}", exc_info=True)
            return Response(
                {"error": "Failed to ingest contract graph", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Compare Two Contracts — Differential Graph
# ─────────────────────────────────────────────────────────────────────────────

class CompareContractGraphView(APIView):
    """
    GET /api/cuad-graph/compare/?c1=<uuid>&c2=<uuid>&risk_weight=1.0&obligation_weight=1.0

    Returns a React Flow compatible diff graph with color-coded nodes:
      - Green  (#68BC00) = same clause type, similar risk
      - Yellow (#FFD86E) = same clause type, risk differs ≥ 0.15
      - Red    (#F16667) = clause only in contract1 (missing from contract2)
      - Blue   (#4C8EDA) = clause only in contract2 (new vs contract1)

    Also returns weighted scores and diff summary.
    """

    def get(self, request):
        c1_id = request.query_params.get("c1")
        c2_id = request.query_params.get("c2")

        if not c1_id or not c2_id:
            return Response(
                {"error": "Both c1 and c2 contract IDs are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if c1_id == c2_id:
            return Response(
                {"error": "c1 and c2 must be different contracts"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            risk_weight = float(request.query_params.get("risk_weight", 1.0))
            obligation_weight = float(request.query_params.get("obligation_weight", 1.0))
        except (ValueError, TypeError):
            risk_weight = 1.0
            obligation_weight = 1.0

        # Clamp weights
        risk_weight = max(0.0, min(5.0, risk_weight))
        obligation_weight = max(0.0, min(5.0, obligation_weight))

        try:
            svc = _service()
            result = svc.compare_contracts_graph(c1_id, c2_id, risk_weight, obligation_weight)

            if "error" in result:
                return Response(
                    {"error": result["error"]},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[CUAD-COMPARE] Error: {e}", exc_info=True)
            return Response(
                {"error": "Failed to compare contracts", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ─────────────────────────────────────────────────────────────────────────────
# 3. PageRank — Clause Influence Scores
# ─────────────────────────────────────────────────────────────────────────────

class GDSPageRankView(APIView):
    """
    GET /api/cuad-graph/pagerank/<contract_id>/

    Returns PageRank-based influence scores for all clauses in a contract.
    Higher score = clause is more central/influential in the risk network.
    """

    def get(self, request, contract_id):
        try:
            svc = _service()
            result = svc.get_gds_pagerank(str(contract_id))

            if "error" in result and not result.get("pagerank"):
                return Response(result, status=status.HTTP_404_NOT_FOUND)

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[CUAD-PAGERANK] Error: {e}", exc_info=True)
            return Response(
                {"error": "Failed to compute PageRank", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Similarity — Structural Contract Similarity
# ─────────────────────────────────────────────────────────────────────────────

class GDSSimilarityView(APIView):
    """
    POST /api/cuad-graph/similarity/

    Body: { "contract1_id": "<uuid>", "contract2_id": "<uuid>" }

    Returns Jaccard + cosine hybrid similarity score (0–1) between two contracts,
    plus clause type overlap analysis.
    """

    def post(self, request):
        c1_id = request.data.get("contract1_id")
        c2_id = request.data.get("contract2_id")

        if not c1_id or not c2_id:
            return Response(
                {"error": "contract1_id and contract2_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            svc = _service()
            result = svc.get_gds_similarity(str(c1_id), str(c2_id))
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[CUAD-SIMILARITY] Error: {e}", exc_info=True)
            return Response(
                {"error": "Failed to compute similarity", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ─────────────────────────────────────────────────────────────────────────────
# 5. GNN Scoring — Risk + Stability Score
# ─────────────────────────────────────────────────────────────────────────────

class GNNScoringView(APIView):
    """
    POST /api/cuad-graph/gnn-score/

    Body: { "contract_id": "<uuid>" }

    Returns:
      - risk_score (0–100): Higher = more risky
      - stability_score (0–100): Higher = more stable
      - top_risky_clauses: Top 5 highest-risk clauses from GNN
      - method: "pytorch_geometric_gcn" | "rule_based_pagerank_fallback"

    Uses PyTorch Geometric GCN. Falls back to weighted rule-based scoring
    if PyTorch is unavailable or graph is too small.
    """

    def post(self, request):
        contract_id = request.data.get("contract_id")

        if not contract_id:
            return Response(
                {"error": "contract_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            svc = _service()
            result = svc.get_gnn_score(str(contract_id))

            if "error" in result:
                return Response(result, status=status.HTTP_404_NOT_FOUND)

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[CUAD-GNN] Error: {e}", exc_info=True)
            return Response(
                {"error": "Failed to compute GNN score", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ─────────────────────────────────────────────────────────────────────────────
# 6. GraphRAG — AI Analysis of Single Contract
# ─────────────────────────────────────────────────────────────────────────────

class RAGAnalyzeView(APIView):
    """
    POST /api/cuad-graph/rag-analyze/
    Body: { "contract_id": "<uuid>" }

    Returns Qwen 2.5 + Neo4j graph powered risk analysis:
      - risk narrative, red flags, compliance insights, recommendation
    """

    def post(self, request):
        contract_id = request.data.get("contract_id")
        if not contract_id:
            return Response({"error": "contract_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            rag = CUADGraphRAG()
            result = rag.analyze_contract(str(contract_id))
            if "error" in result:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"[CUAD-RAG-ANALYZE] Error: {e}", exc_info=True)
            return Response({"error": "GraphRAG analysis failed", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────────────────────────────────
# 7. GraphRAG — AI Comparison of Two Contracts
# ─────────────────────────────────────────────────────────────────────────────

class RAGCompareView(APIView):
    """
    POST /api/cuad-graph/rag-compare/
    Body: {
        "contract1_id": "<uuid>",
        "contract2_id": "<uuid>",
        "diff_summary": { ... }  # optional, from compare endpoint
    }
    """

    def post(self, request):
        c1_id = request.data.get("contract1_id")
        c2_id = request.data.get("contract2_id")
        if not c1_id or not c2_id:
            return Response({"error": "contract1_id and contract2_id are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            rag = CUADGraphRAG()
            diff_summary = request.data.get("diff_summary")
            result = rag.compare_contracts(str(c1_id), str(c2_id), diff_summary=diff_summary)
            if "error" in result:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"[CUAD-RAG-COMPARE] Error: {e}", exc_info=True)
            return Response({"error": "GraphRAG comparison failed", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────────────────────────────────
# 8. GraphRAG — AI Negotiation Recommendations
# ─────────────────────────────────────────────────────────────────────────────

class RAGNegotiateView(APIView):
    """
    POST /api/cuad-graph/rag-negotiate/
    Body: {
        "contract_id": "<uuid>",
        "negotiation_goals": "reduce liability, shorten notice periods",
        "diff_context": { ... }  # optional graph diff result
    }
    """

    def post(self, request):
        contract_id = request.data.get("contract_id")
        if not contract_id:
            return Response({"error": "contract_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            rag = CUADGraphRAG()
            goals = request.data.get("negotiation_goals", "")
            diff_ctx = request.data.get("diff_context")
            result = rag.get_negotiation_recommendations(
                str(contract_id), negotiation_goals=goals, diff_context=diff_ctx
            )
            if "error" in result:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"[CUAD-RAG-NEGOTIATE] Error: {e}", exc_info=True)
            return Response({"error": "Negotiation RAG failed", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────────────────────────────────
# 9. GNN Training (200-epoch loop)
# ─────────────────────────────────────────────────────────────────────────────

class MultiContractCompareView(APIView):
    """
    POST /api/cuad-graph/compare-multi/

    Body: {
        "contract_ids": ["<uuid1>", "<uuid2>", "<uuid3>"],   # 2–5 contracts
        "risk_weight": 1.0,
        "obligation_weight": 1.0
    }

    Returns a React Flow portfolio graph showing clause coverage across all contracts.
    Clause coverage status:
      - universal (#68BC00 green)  — present in ALL contracts
      - common    (#FFD86E yellow) — present in majority
      - partial   (#F97316 orange) — present in minority
      - unique    (#4C8EDA blue)   — present in only 1 contract
    """

    def post(self, request):
        contract_ids = request.data.get("contract_ids")
        if not contract_ids or not isinstance(contract_ids, list):
            return Response(
                {"error": "contract_ids array (2–5 items) is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if len(contract_ids) < 2 or len(contract_ids) > 5:
            return Response(
                {"error": "Provide between 2 and 5 contract IDs"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            risk_weight = float(request.data.get("risk_weight", 1.0))
            obligation_weight = float(request.data.get("obligation_weight", 1.0))
        except (ValueError, TypeError):
            risk_weight = 1.0
            obligation_weight = 1.0

        risk_weight = max(0.0, min(5.0, risk_weight))
        obligation_weight = max(0.0, min(5.0, obligation_weight))

        try:
            svc = _service()
            result = svc.compare_multi_contracts_graph(
                [str(cid) for cid in contract_ids],
                risk_weight=risk_weight,
                obligation_weight=obligation_weight,
            )
            if "error" in result:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[CUAD-MULTI-COMPARE] Error: {e}", exc_info=True)
            return Response(
                {"error": "Multi-contract comparison failed", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GNNTrainView(APIView):
    """
    POST /api/cuad-graph/gnn-train/
    Body: { "contract_id": "<uuid>", "epochs": 200, "lr": 0.01 }
    """

    def post(self, request):
        contract_id = request.data.get("contract_id")
        if not contract_id:
            return Response({"error": "contract_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            epochs = int(request.data.get("epochs", 200))
            lr = float(request.data.get("lr", 0.01))
            epochs = max(10, min(500, epochs))  # clamp 10-500
            svc = _service()
            result = svc.train_gnn(str(contract_id), epochs=epochs, lr=lr)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"[CUAD-GNN-TRAIN] Error: {e}", exc_info=True)
            return Response({"error": "GNN training failed", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────────────────────────────────
# 10. Build Persisted SIMILAR Edges in Neo4j
# ─────────────────────────────────────────────────────────────────────────────

class BuildSimilarEdgesView(APIView):
    """
    POST /api/cuad-graph/build-similar/
    Body: { "threshold": 0.70 }  # similarity cutoff (0-1)

    Builds SIMILAR relationships between clauses across all contracts.
    Uses MiniLM embeddings or falls back to risk-vector cosine.
    """

    def post(self, request):
        try:
            threshold = float(request.data.get("threshold", 0.70))
            threshold = max(0.3, min(0.99, threshold))
            svc = _service()
            result = svc.build_similarity_edges(threshold=threshold)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"[CUAD-SIMILAR] Error: {e}", exc_info=True)
            return Response({"error": "Build similarity edges failed", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────────────────────────────────
# 11. Bulk CUAD JSON Ingestion
# ─────────────────────────────────────────────────────────────────────────────

class IngestCUADJsonView(APIView):
    """
    POST /api/cuad-graph/ingest-cuad-json/
    Body: {
        "contracts": [ { CUAD-format contract objects } ],
        "source": "cuad_dataset"
    }

    Bulk ingests CUAD JSON dataset into Neo4j with all 13 node types.
    """

    def post(self, request):
        contracts = request.data.get("contracts")
        if not contracts or not isinstance(contracts, list):
            return Response({"error": "contracts array is required"}, status=status.HTTP_400_BAD_REQUEST)
        if len(contracts) > 100:
            return Response({"error": "Maximum 100 contracts per batch"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            source = request.data.get("source", "cuad_dataset")
            svc = _service()
            result = svc.ingest_cuad_json(contracts, source=source)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"[CUAD-JSON-INGEST] Error: {e}", exc_info=True)
            return Response({"error": "CUAD JSON ingestion failed", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────────────────────────────────
# 12. GDS Native PageRank
# ─────────────────────────────────────────────────────────────────────────────

class GDSNativePageRankView(APIView):
    """
    GET /api/cuad-graph/gds-pagerank/<contract_id>/

    Runs native Neo4j GDS PageRank algorithm.
    Falls back to NetworkX if GDS plugin unavailable.
    """

    def get(self, request, contract_id):
        try:
            svc = _service()
            result = svc.gds_pagerank(str(contract_id))
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"[CUAD-GDS-PR] Error: {e}", exc_info=True)
            return Response({"error": "GDS PageRank failed", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────────────────────────────────
# 13. GDS Native NodeSimilarity
# ─────────────────────────────────────────────────────────────────────────────

class GDSNativeSimilarityView(APIView):
    """
    POST /api/cuad-graph/gds-similarity/
    Body: { "contract1_id": "<uuid>", "contract2_id": "<uuid>" }

    Runs native Neo4j GDS NodeSimilarity.
    Falls back to Jaccard+cosine hybrid.
    """

    def post(self, request):
        c1_id = request.data.get("contract1_id")
        c2_id = request.data.get("contract2_id")
        if not c1_id or not c2_id:
            return Response({"error": "contract1_id and contract2_id are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            svc = _service()
            result = svc.gds_node_similarity(str(c1_id), str(c2_id))
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"[CUAD-GDS-SIM] Error: {e}", exc_info=True)
            return Response({"error": "GDS Node Similarity failed", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────────────────────────────────
# 14. Temporal Graph — Track Amendment
# ─────────────────────────────────────────────────────────────────────────────

class TrackAmendmentView(APIView):
    """
    POST /api/cuad-graph/amendment/
    Body: {
        "contract_id": "<uuid>",
        "description": "Rate increase + liability cap amendment",
        "affected_clause_types": ["Payment Terms", "Limitation of Liability"],
        "date": "2024-03-15"
    }
    """

    def post(self, request):
        contract_id = request.data.get("contract_id")
        description = request.data.get("description", "")
        if not contract_id or not description:
            return Response({"error": "contract_id and description are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            affected = request.data.get("affected_clause_types", [])
            date = request.data.get("date", "")
            svc = _service()
            result = svc.track_amendment(str(contract_id), description, affected_clause_types=affected, amendment_date=date)
            if "error" in result:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"[CUAD-TEMPORAL] Error: {e}", exc_info=True)
            return Response({"error": "Amendment tracking failed", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AmendmentHistoryView(APIView):
    """
    GET /api/cuad-graph/amendments/<contract_id>/
    Returns full amendment timeline for a contract.
    """

    def get(self, request, contract_id):
        try:
            svc = _service()
            result = svc.get_amendment_history(str(contract_id))
            if "error" in result:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"[CUAD-TEMPORAL-HIST] Error: {e}", exc_info=True)
            return Response({"error": "Amendment history failed", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
