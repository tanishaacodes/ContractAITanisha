"""
Integrated Arbitration Intelligence Service
============================================
Orchestrates all arbitration analysis components:
- Database persistence (models)
- LegalBERT embeddings
- Neo4j graph storage
- GNN dispute prediction
- Clause rewriting

This service coordinates the full analysis pipeline with persistence.
"""

import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal

from django.db import transaction

from core.models import Contract
from arbitration.models import (
    ArbitrationAnalysis,
    ArbitrationClause,
    TribunalSimulation,
    ArbitrationScenario,
    ClauseRewrite,
    GNNPrediction,
)
from api.arbitration_risk_service import (
    run_full_arbitration_analysis,
    extract_arbitration_clauses,
    compute_clause_risk,
    classify_risk_level,
)
from arbitration.legalbert_service import (
    generate_clause_embeddings_batch,
    discover_semantic_relationships,
    get_legalbert_service,
)
from arbitration.neo4j_graph_service import get_neo4j_graph_service
from arbitration.gnn_model import get_gnn_inference_service
from arbitration.clause_rewrite_service import get_clause_rewrite_service

logger = logging.getLogger(__name__)


class IntegratedArbitrationService:
    """
    Unified service for arbitration intelligence with full persistence.
    """

    def __init__(self):
        self.legalbert = get_legalbert_service()
        self.neo4j = get_neo4j_graph_service()
        self.gnn = get_gnn_inference_service()
        self.rewriter = get_clause_rewrite_service()

    def run_full_analysis_with_persistence(
        self,
        contract: Contract,
        contract_text: str,
        contract_value: float,
        settlement_offer: Optional[float] = None,
        monte_carlo_runs: int = 50000,
        tribunal_runs: int = 5000,
        enable_gnn: bool = True,
        enable_neo4j: bool = True,
        enable_clause_rewrite: bool = True,
    ) -> Dict[str, Any]:
        """
        Run complete arbitration analysis and persist all results.

        Args:
            contract: Contract model instance
            contract_text: Raw contract text
            contract_value: Contract value in USD
            settlement_offer: Optional settlement amount
            monte_carlo_runs: MC simulation iterations
            tribunal_runs: Tribunal simulation iterations
            enable_gnn: Whether to run GNN prediction
            enable_neo4j: Whether to persist to Neo4j
            enable_clause_rewrite: Whether to generate rewrites

        Returns:
            Complete analysis results with DB IDs
        """
        try:
            with transaction.atomic():
                # ═══════════════════════════════════════════════════
                # STEP 1: Run Core Analysis
                # ═══════════════════════════════════════════════════
                logger.info(f"Running arbitration analysis for contract {contract.id}")

                core_result = run_full_arbitration_analysis(
                    contract_text=contract_text,
                    contract_value=contract_value,
                    settlement_offer=settlement_offer,
                    monte_carlo_runs=monte_carlo_runs,
                    tribunal_runs=tribunal_runs,
                )

                # ═══════════════════════════════════════════════════
                # STEP 2: Create ArbitrationAnalysis Record
                # ═══════════════════════════════════════════════════
                summary = core_result["summary"]
                mc = core_result["monte_carlo"]
                tribunal = core_result["tribunal"]
                exposure = core_result["exposure"]
                settlement_rec = core_result.get("settlement")
                negotiation = core_result["negotiation"]

                # Determine overall risk level
                avg_risk = summary["avg_composite_risk"]
                if avg_risk >= 0.60:
                    risk_level = "CRITICAL"
                elif avg_risk >= 0.45:
                    risk_level = "HIGH"
                elif avg_risk >= 0.25:
                    risk_level = "MEDIUM"
                else:
                    risk_level = "LOW"

                analysis = ArbitrationAnalysis.objects.create(
                    contract=contract,
                    total_clauses=summary["total_clauses"],
                    high_risk_clauses=summary["high_risk_clauses"],
                    medium_risk_clauses=summary["medium_risk_clauses"],
                    low_risk_clauses=summary["low_risk_clauses"],
                    avg_composite_risk=avg_risk,
                    dispute_probability=summary["dispute_probability"],
                    overall_risk_level=risk_level,
                    # Monte Carlo
                    expected_loss=Decimal(str(mc["expected_loss"])),
                    median_loss=Decimal(str(mc["median_loss"])),
                    p75_loss=Decimal(str(mc.get("p75_loss", 0))),
                    p90_loss=Decimal(str(mc.get("p90_loss", 0))),
                    worst_case_p95=Decimal(str(mc["worst_case_p95"])),
                    var_99=Decimal(str(mc["var_99"])),
                    std_deviation=Decimal(str(mc["std_deviation"])),
                    monte_carlo_runs=mc["runs"],
                    # Tribunal
                    buyer_win_probability=tribunal["probabilities"]["buyer_win"],
                    supplier_win_probability=tribunal["probabilities"]["supplier_win"],
                    partial_award_probability=tribunal["probabilities"]["partial_award"],
                    settlement_probability=tribunal["probabilities"]["settlement"],
                    expected_award=Decimal(str(tribunal["expected_award"])),
                    tribunal_runs=tribunal["runs"],
                    # Exposure
                    arbitration_exposure=Decimal(str(exposure["arbitration_exposure"])),
                    legal_cost_estimate=Decimal(str(exposure["legal_cost_estimate"])),
                    total_exposure=Decimal(str(exposure["total_exposure"])),
                    # Settlement
                    settlement_offer=Decimal(str(settlement_offer)) if settlement_offer else None,
                    settlement_decision=settlement_rec["decision"] if settlement_rec else None,
                    potential_saving=Decimal(str(settlement_rec.get("potential_saving", 0))) if settlement_rec else Decimal("0"),
                    # Optimal config
                    optimal_seat=negotiation["optimal_configuration"]["seat"],
                    optimal_tribunal=negotiation["optimal_configuration"]["tribunal"],
                    optimal_cost_rule=negotiation["optimal_configuration"]["cost_rule"],
                    optimal_institution=negotiation["optimal_configuration"]["institution"],
                    optimal_expected_cost=Decimal(str(negotiation["optimal_configuration"]["expected_cost"])),
                )

                logger.info(f"Created ArbitrationAnalysis {analysis.id}")

                # ═══════════════════════════════════════════════════
                # STEP 3: Generate LegalBERT Embeddings
                # ═══════════════════════════════════════════════════
                clauses_data = core_result["clauses"]
                clause_texts = [cl["text"] for cl in clauses_data]

                logger.info("Generating LegalBERT embeddings...")
                embeddings = generate_clause_embeddings_batch(clause_texts)

                # ═══════════════════════════════════════════════════
                # STEP 4: Create ArbitrationClause Records
                # ═══════════════════════════════════════════════════
                clause_objects = []

                for i, clause_dict in enumerate(clauses_data):
                    risk_vector = clause_dict["risk_vector"]

                    clause_obj = ArbitrationClause.objects.create(
                        analysis=analysis,
                        clause_index=i,
                        clause_text=clause_dict["text"],
                        confidence=clause_dict["confidence"],
                        pattern_hits=clause_dict["pattern_hits"],
                        # Risk vector
                        jurisdiction_risk=risk_vector.get("jurisdiction_risk", 0.0),
                        cost_exposure=risk_vector.get("cost_exposure", 0.0),
                        institutional_risk=risk_vector.get("institutional_risk", 0.0),
                        tribunal_structure=risk_vector.get("tribunal_structure", 0.0),
                        procedural_risk=risk_vector.get("procedural_risk", 0.0),
                        enforcement_risk=risk_vector.get("enforcement_risk", 0.0),
                        delay_dispute_risk=risk_vector.get("delay_dispute_risk", 0.0),
                        subcontractor_pass_through=risk_vector.get("subcontractor_pass_through", 0.0),
                        composite_risk=risk_vector.get("composite", 0.0),
                        risk_level=clause_dict["risk_level"],
                        # Embedding
                        embedding=embeddings[i],
                    )

                    clause_objects.append(clause_obj)

                logger.info(f"Created {len(clause_objects)} ArbitrationClause records")

                # ═══════════════════════════════════════════════════
                # STEP 5: Create TribunalSimulation Record
                # ═══════════════════════════════════════════════════
                # Tribunal features from core analysis
                # (These are fixed in the current implementation, but could be dynamic)
                tribunal_features = {
                    "clause_strength": 0.62,
                    "precedent_score": 0.60,
                    "jurisdiction_score": 0.58,
                    "claim_strength": 0.60,
                    "delay_evidence": 0.65,
                }

                TribunalSimulation.objects.create(
                    analysis=analysis,
                    runs=tribunal["runs"],
                    clause_strength=tribunal_features["clause_strength"],
                    precedent_score=tribunal_features["precedent_score"],
                    jurisdiction_score=tribunal_features["jurisdiction_score"],
                    claim_strength=tribunal_features["claim_strength"],
                    delay_evidence=tribunal_features["delay_evidence"],
                    buyer_win_prob=tribunal["probabilities"]["buyer_win"],
                    supplier_win_prob=tribunal["probabilities"]["supplier_win"],
                    partial_award_prob=tribunal["probabilities"]["partial_award"],
                    settlement_prob=tribunal["probabilities"]["settlement"],
                    expected_award=Decimal(str(tribunal["expected_award"])),
                    avg_tribunal_score=tribunal["avg_tribunal_score"],
                    score_std=tribunal["score_std"],
                )

                # ═══════════════════════════════════════════════════
                # STEP 6: Create ArbitrationScenario Records
                # ═══════════════════════════════════════════════════
                optimal_scenarios = core_result["scenarios"]["optimal"]
                worst_scenarios = core_result["scenarios"]["worst"]

                for scenario in optimal_scenarios:
                    ArbitrationScenario.objects.create(
                        analysis=analysis,
                        seat=scenario["seat"],
                        tribunal_size=scenario["tribunal"],
                        cost_rule=scenario["cost_rule"],
                        institution=scenario["institution"],
                        expected_cost=Decimal(str(scenario["expected_cost"])),
                        total_exposure=Decimal(str(scenario["total_exposure"])),
                        risk_index=scenario["risk_index"],
                        is_optimal=True,
                        is_worst=False,
                    )

                for scenario in worst_scenarios:
                    ArbitrationScenario.objects.create(
                        analysis=analysis,
                        seat=scenario["seat"],
                        tribunal_size=scenario["tribunal"],
                        cost_rule=scenario["cost_rule"],
                        institution=scenario["institution"],
                        expected_cost=Decimal(str(scenario["expected_cost"])),
                        total_exposure=Decimal(str(scenario["total_exposure"])),
                        risk_index=scenario["risk_index"],
                        is_optimal=False,
                        is_worst=True,
                    )

                # ═══════════════════════════════════════════════════
                # STEP 7: Neo4j Graph Storage
                # ═══════════════════════════════════════════════════
                if enable_neo4j and self.neo4j.is_available():
                    logger.info("Storing graph in Neo4j...")

                    # Create contract node
                    self.neo4j.create_contract_node(
                        contract_id=str(contract.id),
                        contract_name=contract.original_filename,
                        analysis_data={
                            "total_clauses": analysis.total_clauses,
                            "high_risk_clauses": analysis.high_risk_clauses,
                            "avg_composite_risk": analysis.avg_composite_risk,
                            "dispute_probability": analysis.dispute_probability,
                            "expected_loss": float(analysis.expected_loss),
                        },
                    )

                    # Create clause nodes
                    clause_dicts = [
                        {
                            "id": str(cl.id),
                            "clause_index": cl.clause_index,
                            "clause_text": cl.clause_text,
                            "composite_risk": cl.composite_risk,
                            "jurisdiction_risk": cl.jurisdiction_risk,
                            "cost_exposure": cl.cost_exposure,
                            "institutional_risk": cl.institutional_risk,
                            "tribunal_structure": cl.tribunal_structure,
                            "procedural_risk": cl.procedural_risk,
                            "enforcement_risk": cl.enforcement_risk,
                            "delay_dispute_risk": cl.delay_dispute_risk,
                            "subcontractor_pass_through": cl.subcontractor_pass_through,
                            "risk_level": cl.risk_level,
                        }
                        for cl in clause_objects
                    ]

                    self.neo4j.create_clause_nodes(str(contract.id), clause_dicts)

                    # Discover semantic relationships
                    if self.legalbert.is_available():
                        clause_emb_data = [
                            {"id": str(cl.id), "text": cl.clause_text, "embedding": cl.embedding}
                            for cl in clause_objects
                            if cl.embedding
                        ]

                        relationships = discover_semantic_relationships(clause_emb_data, similarity_threshold=0.70)
                        self.neo4j.create_clause_relationships(relationships)

                # ═══════════════════════════════════════════════════
                # STEP 8: GNN Prediction
                # ═══════════════════════════════════════════════════
                if enable_gnn:
                    logger.info("Running GNN prediction...")
                    if not self.gnn.is_available():
                        logger.info("GNN model not available, using heuristic predictions")

                    # Build graph for GNN
                    node_features = [
                        [
                            cl.jurisdiction_risk,
                            cl.cost_exposure,
                            cl.institutional_risk,
                            cl.tribunal_structure,
                            cl.procedural_risk,
                            cl.enforcement_risk,
                            cl.delay_dispute_risk,
                            cl.subcontractor_pass_through,
                        ]
                        for cl in clause_objects
                    ]

                    # Simple sequential edges for now
                    edges = [[i, i + 1] for i in range(len(clause_objects) - 1)]

                    gnn_result = self.gnn.predict(node_features, edges)

                    # Prepare influential clauses data
                    # Sort by composite risk (high risk = more influential)
                    sorted_clauses = sorted(clause_objects, key=lambda c: c.composite_risk, reverse=True)
                    influential_clauses = [
                        {
                            "id": str(cl.id),
                            "text": cl.clause_text[:200] + "..." if len(cl.clause_text) > 200 else cl.clause_text,
                            "risk_level": cl.risk_level,
                            "influence_score": cl.composite_risk,  # Use risk as influence proxy
                        }
                        for cl in sorted_clauses[:5]
                    ]

                    # Store GNN prediction
                    GNNPrediction.objects.create(
                        analysis=analysis,
                        model_version="v1.0-heuristic" if not self.gnn.is_available() else "v1.0",
                        model_checkpoint="heuristic" if not self.gnn.is_available() else "models/arbitration_gnn/best_model.pt",
                        dispute_probability=gnn_result["dispute_probability"],
                        buyer_win_probability=gnn_result["buyer_win_probability"],
                        supplier_win_probability=gnn_result["supplier_win_probability"],
                        partial_award_probability=gnn_result["partial_award_probability"],
                        settlement_probability=gnn_result["settlement_probability"],
                        prediction_confidence=gnn_result["confidence"],
                        model_certainty=gnn_result["confidence"],
                        node_count=len(clause_objects),
                        edge_count=len(edges),
                        avg_node_degree=2.0 if len(edges) > 0 else 0.0,
                        graph_density=len(edges) / max((len(clause_objects) * (len(clause_objects) - 1) / 2), 1),
                        top_influential_clauses=influential_clauses,
                        inference_time_ms=50.0,  # Placeholder
                    )

                    # Update analysis with GNN predictions
                    analysis.gnn_dispute_probability = gnn_result["dispute_probability"]
                    analysis.gnn_confidence = gnn_result["confidence"]
                    analysis.save()

                # ═══════════════════════════════════════════════════
                # STEP 9: Clause Rewrites (High-Risk Only)
                # ═══════════════════════════════════════════════════
                if enable_clause_rewrite and self.rewriter.is_available():
                    logger.info("Generating clause rewrites for high-risk clauses...")

                    high_risk_clauses = [cl for cl in clause_objects if cl.risk_level == "HIGH"]

                    for clause in high_risk_clauses[:5]:  # Limit to top 5 to avoid excessive API calls
                        try:
                            rewrite_result = self.rewriter.rewrite_clause(
                                clause_text=clause.clause_text,
                                strategy="buyer_favorable",
                                contract_value=contract_value,
                            )

                            # Estimate risk reduction (simplified)
                            risk_reduction = max(0.0, clause.composite_risk - clause.composite_risk * 0.60)

                            ClauseRewrite.objects.create(
                                clause=clause,
                                original_text=rewrite_result["original"],
                                original_risk_score=clause.composite_risk,
                                rewritten_text=rewrite_result["rewritten"],
                                predicted_risk_score=clause.composite_risk * 0.60,  # Assume 40% reduction
                                risk_reduction=risk_reduction,
                                improvements=rewrite_result["improvements"],
                                rewrite_strategy=rewrite_result["strategy"],
                                llm_model=rewrite_result["model"],
                                temperature=rewrite_result.get("temperature", 0.3),
                                status="DRAFT",
                            )

                        except Exception as e:
                            logger.error(f"Clause rewrite failed for {clause.id}: {e}")

                # ═══════════════════════════════════════════════════
                # STEP 10: Prepare Response
                # ═══════════════════════════════════════════════════
                response = {
                    **core_result,
                    "analysis_id": str(analysis.id),
                    "persistence": {
                        "database": True,
                        "neo4j": enable_neo4j and self.neo4j.is_available(),
                        "gnn": enable_gnn and self.gnn.is_available(),
                        "legalbert": self.legalbert.is_available(),
                        "clause_rewrites": enable_clause_rewrite and self.rewriter.is_available(),
                    },
                    "clause_count": len(clause_objects),
                    "high_risk_rewrites_generated": len([cl for cl in clause_objects if cl.risk_level == "HIGH"]),
                }

                logger.info(f"Arbitration analysis completed successfully: {analysis.id}")

                return response

        except Exception as e:
            logger.exception("Arbitration analysis failed")
            raise e


# Global singleton
_integrated_service = None


def get_integrated_arbitration_service() -> IntegratedArbitrationService:
    """Get or create the global integrated service."""
    global _integrated_service
    if _integrated_service is None:
        _integrated_service = IntegratedArbitrationService()
    return _integrated_service
