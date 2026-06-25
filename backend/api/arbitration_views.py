"""
Arbitration Risk Intelligence API Views
=========================================
Enterprise endpoints for $100M+ EPC contract arbitration analysis.

Endpoints:
1. POST /api/arbitration/analyze              — Full analysis pipeline
2. POST /api/arbitration/monte-carlo          — Standalone Monte Carlo
3. POST /api/arbitration/scenarios            — Scenario engine
4. POST /api/arbitration/tribunal             — Tribunal simulation
5. POST /api/arbitration/exposure             — Exposure + settlement
6. POST /api/arbitration/optimize             — Clause config optimizer
7. POST /api/arbitration/strategies           — Legal strategy evaluator
8. GET  /api/arbitration/knowledge-graph/<id> — Graph for contract
9. GET  /api/arbitration/canonical-graph      — Canonical 32-node graph
10. POST /api/arbitration/extract-clauses     — Clause extraction only

Author: PrimeContractAI System
"""

import logging
import os
import tempfile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from core.models import Contract, Clause, User
from api.arbitration_risk_service import (
    run_full_arbitration_analysis,
    extract_arbitration_clauses,
    compute_clause_risk,
    classify_risk_level,
    run_monte_carlo,
    get_top_scenarios,
    simulate_tribunal,
    compute_arbitration_exposure,
    settlement_recommendation,
    optimize_clause_configuration,
    evaluate_strategies,
    build_arbitration_knowledge_graph,
    compute_pagerank_influence,
    CANONICAL_CLAUSE_NODES,
    CANONICAL_EDGES,
)

logger = logging.getLogger(__name__)


def _get_contract_text(contract: Contract) -> str:
    """Assemble clause texts from DB for a contract."""
    clauses = list(Clause.objects.filter(contract=contract).order_by("id"))
    parts = []
    for cl in clauses:
        text = getattr(cl, "clause_text", "") or getattr(cl, "text", "") or ""
        if text:
            parts.append(text)
    return "\n\n".join(parts)


# ─────────────────────────────────────────────
# 1. FULL ANALYSIS
# ─────────────────────────────────────────────

class ArbitrationFullAnalysisView(APIView):
    """
    POST /api/arbitration/analyze

    Body:
    {
        "contract_id":       "uuid",          // optional — use existing contract
        "contract_text":     "...",           // optional — raw text override
        "contract_value":    150000000,
        "settlement_offer":  8000000,         // optional
        "monte_carlo_runs":  50000,           // optional, default 50000
        "tribunal_runs":     5000             // optional, default 5000
    }
    """

    def post(self, request):
        try:
            data = request.data
            contract_value   = float(data.get("contract_value", 100_000_000))
            settlement_offer = float(data["settlement_offer"]) if "settlement_offer" in data else None
            mc_runs          = int(data.get("monte_carlo_runs", 50000))
            tribunal_runs    = int(data.get("tribunal_runs", 5000))

            # Clamp runs to reasonable limits
            mc_runs       = min(max(mc_runs, 1000), 100_000)
            tribunal_runs = min(max(tribunal_runs, 500), 10_000)

            # Get contract text
            contract_text = data.get("contract_text", "")
            if not contract_text and data.get("contract_id"):
                contract = get_object_or_404(Contract, id=data["contract_id"])
                contract_text = _get_contract_text(contract)

            if not contract_text:
                contract_text = "Standard EPC contract with arbitration, dispute resolution, governing law, seat of arbitration, liquidated damages, delay damages, cost allocation clauses."

            # Get or create contract object for persistence
            contract = None
            if data.get("contract_id"):
                contract = get_object_or_404(Contract, id=data["contract_id"])
            else:
                # Create a temporary contract to enable full persistence
                from django.utils import timezone
                import uuid as uuid_lib

                temp_id = str(uuid_lib.uuid4())
                default_user = User.objects.first()

                if not default_user:
                    logger.error("No users in database - cannot create temporary contract")
                    raise ValueError("No users available for temporary contract creation")

                contract = Contract.objects.create(
                    id=temp_id,
                    user=default_user,
                    filename=f"temp_analysis_{temp_id[:8]}.txt",
                    original_filename=f"Analysis {temp_id[:8]}",
                    file_type="txt",
                    file_path=f"/tmp/analysis_{temp_id}.txt",
                    full_text=contract_text[:500] if contract_text else "Temporary analysis",
                    uploaded_at=timezone.now(),
                )
                logger.info(f"Created temporary contract for analysis: {contract.id}")

            # Always use integrated service for full persistence
            try:
                from arbitration.integrated_service import get_integrated_arbitration_service

                integrated_service = get_integrated_arbitration_service()
                result = integrated_service.run_full_analysis_with_persistence(
                    contract=contract,
                    contract_text=contract_text,
                    contract_value=contract_value,
                    settlement_offer=settlement_offer,
                    monte_carlo_runs=mc_runs,
                    tribunal_runs=tribunal_runs,
                    enable_gnn=True,
                    enable_neo4j=False,  # Disable Neo4j for temp contracts
                    enable_clause_rewrite=True,  # Enable AI-powered clause rewriting
                )

                logger.info(f"✓ Analysis completed with ID: {result.get('analysis_id')}")
                return Response(result, status=status.HTTP_200_OK)

            except Exception as e:
                logger.exception(f"Integrated service failed: {e}")
                # Delete temp contract if analysis failed
                if not data.get("contract_id") and contract:
                    contract.delete()
                raise

        except Exception as e:
            logger.exception("Arbitration full analysis failed")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────
# 2. MONTE CARLO ONLY
# ─────────────────────────────────────────────

class ArbitrationMonteCarloView(APIView):
    """
    POST /api/arbitration/monte-carlo

    Body:
    {
        "contract_id":    "uuid",     // optional
        "contract_value": 150000000,
        "runs":           50000
    }
    """

    def post(self, request):
        try:
            data           = request.data
            contract_value = float(data.get("contract_value", 100_000_000))
            runs           = int(data.get("runs", 50000))
            runs           = min(max(runs, 1000), 100_000)

            # Fetch clause risk scores if contract_id given
            risk_scores = []
            if data.get("contract_id"):
                contract = get_object_or_404(Contract, id=data["contract_id"])
                text = _get_contract_text(contract)
                clauses = extract_arbitration_clauses(text)
                risk_scores = [compute_clause_risk(cl["text"]) for cl in clauses]

            result = run_monte_carlo(contract_value, risk_scores, runs=runs)
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Monte Carlo failed")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────
# 3. SCENARIO ENGINE
# ─────────────────────────────────────────────

class ArbitrationScenariosView(APIView):
    """
    POST /api/arbitration/scenarios

    Body: { "contract_value": 150000000, "top_n": 10 }
    """

    def post(self, request):
        try:
            contract_value = float(request.data.get("contract_value", 100_000_000))
            top_n          = int(request.data.get("top_n", 10))
            result         = get_top_scenarios(contract_value, top_n=top_n)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Scenario engine failed")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────
# 4. TRIBUNAL SIMULATION
# ─────────────────────────────────────────────

class ArbitrationTribunalView(APIView):
    """
    POST /api/arbitration/tribunal

    Body:
    {
        "features": {
            "clause_strength":    0.7,
            "precedent_score":    0.6,
            "jurisdiction_score": 0.5,
            "claim_strength":     0.65,
            "delay_evidence":     0.7
        },
        "contract_value": 150000000,
        "runs": 5000
    }
    """

    def post(self, request):
        try:
            data  = request.data
            runs  = int(data.get("runs", 5000))
            runs  = min(max(runs, 500), 10_000)

            features = data.get("features", {
                "clause_strength":    0.65,
                "precedent_score":    0.55,
                "jurisdiction_score": 0.50,
                "claim_strength":     0.60,
                "delay_evidence":     0.55,
            })
            features["contract_value"] = float(data.get("contract_value", 100_000_000))

            result = simulate_tribunal(features, runs=runs)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Tribunal simulation failed")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────
# 5. EXPOSURE & SETTLEMENT
# ─────────────────────────────────────────────

class ArbitrationExposureView(APIView):
    """
    POST /api/arbitration/exposure

    Body:
    {
        "contract_value":      150000000,
        "dispute_probability": 0.62,
        "tribunal_result":     { ... },   // from /tribunal
        "settlement_offer":    8000000    // optional
    }
    """

    def post(self, request):
        try:
            data              = request.data
            contract_value    = float(data.get("contract_value", 100_000_000))
            dispute_prob      = float(data.get("dispute_probability", 0.55))
            tribunal_result   = data.get("tribunal_result", {
                "probabilities": {"buyer_win": 0.4, "supplier_win": 0.25,
                                  "partial_award": 0.20, "settlement": 0.15}
            })
            settlement_offer  = data.get("settlement_offer")

            exposure = compute_arbitration_exposure(contract_value, dispute_prob, tribunal_result)

            result = {"exposure": exposure}
            if settlement_offer is not None:
                result["settlement"] = settlement_recommendation(
                    exposure, float(settlement_offer)
                )

            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Exposure calculation failed")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────
# 6. NEGOTIATION OPTIMIZER
# ─────────────────────────────────────────────

class ArbitrationOptimizerView(APIView):
    """
    POST /api/arbitration/optimize

    Body: { "contract_value": 150000000 }
    """

    def post(self, request):
        try:
            contract_value = float(request.data.get("contract_value", 100_000_000))
            result = optimize_clause_configuration(contract_value)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Optimizer failed")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────
# 7. LEGAL STRATEGY EVALUATOR
# ─────────────────────────────────────────────

class ArbitrationStrategiesView(APIView):
    """
    POST /api/arbitration/strategies

    Body:
    {
        "features": { ... },
        "contract_value": 150000000,
        "runs": 2000
    }
    """

    def post(self, request):
        try:
            data  = request.data
            runs  = int(data.get("runs", 2000))
            runs  = min(max(runs, 200), 5000)

            features = data.get("features", {
                "clause_strength":    0.65,
                "precedent_score":    0.55,
                "jurisdiction_score": 0.50,
                "claim_strength":     0.60,
                "delay_evidence":     0.55,
            })
            features["contract_value"] = float(data.get("contract_value", 100_000_000))

            result = evaluate_strategies(features, runs=runs)
            return Response({"strategies": result}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Strategy evaluation failed")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────
# 8. KNOWLEDGE GRAPH FOR EXISTING CONTRACT
# ─────────────────────────────────────────────

class ArbitrationKnowledgeGraphView(APIView):
    """
    GET /api/arbitration/knowledge-graph/<contract_id>/
    """

    def get(self, request, contract_id):
        try:
            contract     = get_object_or_404(Contract, id=contract_id)
            text         = _get_contract_text(contract)
            clauses      = extract_arbitration_clauses(text)
            risk_scores  = [compute_clause_risk(cl["text"]) for cl in clauses]
            graph        = build_arbitration_knowledge_graph(clauses, risk_scores)
            influence    = compute_pagerank_influence(risk_scores)

            return Response({
                "contract_id":     str(contract_id),
                "graph":           graph,
                "influence_scores": influence,
                "clause_count":    len(clauses),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Knowledge graph build failed")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────
# 9. CANONICAL GRAPH (static 32-node reference)
# ─────────────────────────────────────────────

class ArbitrationCanonicalGraphView(APIView):
    """
    GET /api/arbitration/canonical-graph/
    Returns the canonical 32-node arbitration knowledge graph
    with default risk scores (no contract required).
    """

    def get(self, request):
        try:
            # Query actual graph data from Neo4j
            from arbitration.neo4j_graph_service import get_neo4j_graph_service

            neo4j_service = get_neo4j_graph_service()
            graph = neo4j_service.get_full_arbitration_graph()

            # Fallback to hardcoded canonical graph if Neo4j fails
            if not graph or not graph.get("nodes"):
                logger.warning("Neo4j graph empty, using fallback canonical graph")
                graph = build_arbitration_knowledge_graph([], [])

            return Response({
                "graph":       graph,
                "node_count":  len(graph.get("nodes", [])),
                "edge_count":  len(graph.get("edges", [])),
                "description": "Live arbitration knowledge graph from Neo4j database",
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Canonical graph failed")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────
# 10. CLAUSE EXTRACTION ONLY
# ─────────────────────────────────────────────

class ArbitrationClauseExtractView(APIView):
    """
    POST /api/arbitration/extract-clauses

    Body: { "contract_text": "...", "contract_id": "uuid" }
    """

    def post(self, request):
        try:
            text = request.data.get("contract_text", "")
            if not text and request.data.get("contract_id"):
                contract = get_object_or_404(Contract, id=request.data["contract_id"])
                text = _get_contract_text(contract)

            clauses     = extract_arbitration_clauses(text)
            risk_scores = [compute_clause_risk(cl["text"]) for cl in clauses]

            for i, cl in enumerate(clauses):
                cl["risk_vector"] = risk_scores[i]
                cl["risk_level"]  = classify_risk_level(risk_scores[i]["composite"])

            high   = sum(1 for cl in clauses if cl["risk_level"] == "HIGH")
            medium = sum(1 for cl in clauses if cl["risk_level"] == "MEDIUM")
            low    = sum(1 for cl in clauses if cl["risk_level"] == "LOW")

            return Response({
                "clauses":       clauses,
                "total":         len(clauses),
                "high_risk":     high,
                "medium_risk":   medium,
                "low_risk":      low,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Clause extraction failed")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────
# 11. DEDICATED FILE TEXT EXTRACTION (no DB save)
# ─────────────────────────────────────────────

class ArbitrationExtractTextView(APIView):
    """
    POST /api/arbitration/extract-text

    Accepts a PDF or DOCX file upload.
    Extracts full text WITHOUT saving to database.
    Returns the raw text for use in arbitration analysis.

    Body: multipart/form-data with 'file' field
    """

    def post(self, request):
        try:
            if "file" not in request.FILES:
                return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

            file = request.FILES["file"]
            ext = os.path.splitext(file.name)[1].lower()

            allowed = [".pdf", ".docx", ".txt"]
            if ext not in allowed:
                return Response(
                    {"error": f"Unsupported file type '{ext}'. Allowed: PDF, DOCX, TXT"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Handle TXT directly (extract_text_from_file doesn't support .txt)
            if ext == ".txt":
                raw = b""
                for chunk in file.chunks():
                    raw += chunk
                extracted_text = raw.decode("utf-8", errors="replace")
                extraction_error = ""
            else:
                # Write to temp file so extract_text_from_file can read it
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    for chunk in file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                try:
                    from api.utils import extract_text_from_file
                    result = extract_text_from_file(tmp_path, ext)
                finally:
                    # Always clean up temp file
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass

                # extract_text_from_file returns a dict {text, pages, ocr_performed, ...}
                if isinstance(result, dict):
                    extracted_text = result.get("text", "") or ""
                    extraction_error = result.get("error", "")
                else:
                    extracted_text = str(result) if result else ""
                    extraction_error = ""

            if not extracted_text or not extracted_text.strip():
                msg = extraction_error or "Could not extract text from file. The file may be scanned/image-only."
                return Response(
                    {"error": msg},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            return Response({
                "text":       extracted_text,
                "characters": len(extracted_text),
                "filename":   file.name,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Text extraction failed")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────
# NEW ENDPOINTS FOR ENHANCED FEATURES
# ─────────────────────────────────────────────

class GetArbitrationAnalysisView(APIView):
    """
    GET /api/arbitration/analysis/<analysis_id>/

    Returns full analysis with all clauses and embeddings
    """

    def get(self, request, analysis_id):
        try:
            from arbitration.models import ArbitrationAnalysis, ArbitrationClause

            analysis = get_object_or_404(ArbitrationAnalysis, id=analysis_id)
            clauses = ArbitrationClause.objects.filter(analysis_id=analysis_id).order_by('clause_index')

            clause_data = []
            for clause in clauses:
                clause_data.append({
                    'id': str(clause.id),
                    'clause_index': clause.clause_index,
                    'clause_text': clause.clause_text,
                    'confidence': clause.confidence,
                    'pattern_hits': clause.pattern_hits,
                    'risk_vector': {
                        'jurisdiction_risk': clause.jurisdiction_risk,
                        'cost_exposure': clause.cost_exposure,
                        'institutional_risk': clause.institutional_risk,
                        'tribunal_structure': clause.tribunal_structure,
                        'procedural_risk': clause.procedural_risk,
                        'enforcement_risk': clause.enforcement_risk,
                        'delay_dispute_risk': clause.delay_dispute_risk,
                        'subcontractor_pass_through': clause.subcontractor_pass_through,
                    },
                    'composite_risk': clause.composite_risk,
                    'risk_level': clause.risk_level,
                    'embedding': clause.embedding,
                    'graph_node_id': clause.graph_node_id,
                })

            return Response({
                'analysis_id': str(analysis.id),
                'contract_id': str(analysis.contract_id),
                'total_clauses': analysis.total_clauses,
                'overall_risk_level': analysis.overall_risk_level,
                'dispute_probability': analysis.dispute_probability,
                'clauses': clause_data,
            })

        except Exception as e:
            logger.exception("Failed to get analysis")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetClauseRewritesView(APIView):
    """
    GET /api/arbitration/rewrites/<analysis_id>/

    Returns AI-generated clause rewrites for an analysis
    """

    def get(self, request, analysis_id):
        try:
            from arbitration.models import ClauseRewrite, ArbitrationClause

            rewrites = ClauseRewrite.objects.filter(
                clause__analysis_id=analysis_id
            ).select_related('clause').order_by('-risk_reduction')

            rewrite_data = []
            for rewrite in rewrites:
                rewrite_data.append({
                    'id': str(rewrite.id),
                    'clause_id': str(rewrite.clause_id),
                    'original_text': rewrite.original_text,
                    'original_risk_score': rewrite.original_risk_score,
                    'rewritten_text': rewrite.rewritten_text,
                    'predicted_risk_score': rewrite.predicted_risk_score,
                    'risk_reduction': rewrite.risk_reduction,
                    'improvements': rewrite.improvements,
                    'rewrite_strategy': rewrite.rewrite_strategy,
                    'llm_model': rewrite.llm_model,
                    'status': rewrite.status,
                    'created_at': rewrite.created_at.isoformat(),
                })

            return Response({'rewrites': rewrite_data})

        except Exception as e:
            logger.exception("Failed to get clause rewrites")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetGNNPredictionView(APIView):
    """
    GET /api/arbitration/gnn-prediction/<analysis_id>/

    Returns Graph Neural Network prediction for an analysis
    """

    def get(self, request, analysis_id):
        try:
            from arbitration.models import GNNPrediction

            prediction = GNNPrediction.objects.filter(
                analysis_id=analysis_id
            ).order_by('-created_at').first()

            if not prediction:
                return Response({
                    'error': 'No GNN prediction found for this analysis',
                    'fallback': True,
                    'model_available': False
                }, status=status.HTTP_200_OK)

            return Response({
                'model_version': prediction.model_version,
                'model_checkpoint': prediction.model_checkpoint,
                'dispute_probability': prediction.dispute_probability,
                'buyer_win_probability': prediction.buyer_win_probability,
                'supplier_win_probability': prediction.supplier_win_probability,
                'partial_award_probability': prediction.partial_award_probability,
                'settlement_probability': prediction.settlement_probability,
                'prediction_confidence': prediction.prediction_confidence,
                'model_certainty': prediction.model_certainty,
                'node_count': prediction.node_count,
                'edge_count': prediction.edge_count,
                'avg_node_degree': prediction.avg_node_degree,
                'graph_density': prediction.graph_density,
                'top_influential_clauses': prediction.top_influential_clauses,
                'inference_time_ms': prediction.inference_time_ms,
            })

        except Exception as e:
            logger.exception("Failed to get GNN prediction")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FindSimilarClausesView(APIView):
    """
    POST /api/arbitration/similar-clauses/

    Find semantically similar clauses using embeddings

    Body:
    {
        "clause_id": "uuid",
        "min_similarity": 0.7
    }
    """

    def post(self, request):
        try:
            from arbitration.models import ArbitrationClause
            from arbitration.legalbert_service import get_legalbert_service
            import numpy as np
            from difflib import SequenceMatcher

            clause_id = request.data.get('clause_id')
            min_similarity = float(request.data.get('min_similarity', 0.7))
            max_results = int(request.data.get('max_results', 10))

            target_clause = get_object_or_404(ArbitrationClause, id=clause_id)

            if not target_clause.embedding:
                return Response({
                    'error': 'Clause does not have an embedding'
                }, status=status.HTTP_400_BAD_REQUEST)

            target_embedding = np.array(target_clause.embedding)
            target_text = target_clause.clause_text.lower().strip()

            # Get all other clauses with embeddings, excluding:
            # 1. The same clause
            # 2. Clauses from the same analysis (to avoid duplicates from same contract)
            other_clauses = ArbitrationClause.objects.exclude(id=clause_id).exclude(
                analysis_id=target_clause.analysis_id
            ).filter(
                embedding__isnull=False
            )

            service = get_legalbert_service()
            similar_clauses = []
            seen_texts = set()  # Track similar texts to avoid near-duplicates

            def text_similarity(text1, text2):
                """Calculate text similarity ratio (0-1)"""
                return SequenceMatcher(None, text1.lower().strip(), text2.lower().strip()).ratio()

            for clause in other_clauses:
                if clause.embedding:
                    clause_text = clause.clause_text.lower().strip()

                    # Skip if text is too similar to target (likely same clause from different analysis)
                    text_sim = text_similarity(target_text, clause_text)
                    if text_sim > 0.9:  # 90% text similarity = likely duplicate
                        continue

                    # Skip if text is too similar to already-seen clauses (ensure diversity)
                    is_duplicate = False
                    for seen_text in seen_texts:
                        if text_similarity(clause_text, seen_text) > 0.85:  # 85% similarity threshold
                            is_duplicate = True
                            break

                    if is_duplicate:
                        continue

                    # Calculate embedding similarity
                    clause_embedding = np.array(clause.embedding)
                    similarity = service.compute_similarity(target_embedding, clause_embedding)

                    if similarity >= min_similarity:
                        similar_clauses.append({
                            'clause_id': str(clause.id),
                            'text': clause.clause_text,
                            'similarity': float(similarity),
                            'risk_level': clause.risk_level,
                            'composite_risk': clause.composite_risk,
                            'contract_name': clause.analysis.contract.original_filename if clause.analysis and clause.analysis.contract else 'Unknown',
                            'analysis_id': str(clause.analysis_id) if clause.analysis_id else None,
                        })

                        # Add to seen texts to ensure diversity
                        seen_texts.add(clause_text)

            # Sort by similarity descending
            similar_clauses.sort(key=lambda x: x['similarity'], reverse=True)

            return Response({
                'similar_clauses': similar_clauses[:max_results],
                'total_found': len(similar_clauses),
                'filtered_duplicates': True,
            })

        except Exception as e:
            logger.exception("Failed to find similar clauses")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetNeo4jGraphView(APIView):
    """
    GET /api/arbitration/neo4j-graph/<contract_id>/

    Get Neo4j graph data for visualization
    """

    def get(self, request, contract_id):
        try:
            from arbitration.neo4j_graph_service import get_neo4j_graph_service

            neo4j = get_neo4j_graph_service()
            graph_data = neo4j.get_contract_graph(contract_id)

            return Response(graph_data)

        except Exception as e:
            logger.exception("Failed to get Neo4j graph")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RewriteClauseView(APIView):
    """
    POST /api/arbitration/rewrite-clause/

    Generate AI-powered clause rewrite

    Body:
    {
        "clause_id": "uuid",
        "strategy": "buyer_favorable"  // or "balanced", "supplier_favorable"
    }
    """

    def post(self, request):
        try:
            from arbitration.models import ArbitrationClause
            from arbitration.clause_rewrite_service import get_clause_rewrite_service

            clause_id = request.data.get('clause_id')
            strategy = request.data.get('strategy', 'buyer_favorable')

            clause = get_object_or_404(ArbitrationClause, id=clause_id)

            # Estimate contract value from analysis
            contract_value = 150_000_000  # Default
            if clause.analysis and clause.analysis.contract:
                # Try to parse from contract if available
                contract_value = 150_000_000  # Could parse from contract data

            rewrite_service = get_clause_rewrite_service()
            result = rewrite_service.rewrite_clause(
                clause_text=clause.clause_text,
                strategy=strategy,
                contract_value=contract_value
            )

            return Response({
                'original': result.get('original'),
                'rewritten': result.get('rewritten'),
                'improvements': result.get('improvements'),
                'strategy': result.get('strategy'),
                'model': result.get('model'),
            })

        except Exception as e:
            logger.exception("Failed to rewrite clause")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
