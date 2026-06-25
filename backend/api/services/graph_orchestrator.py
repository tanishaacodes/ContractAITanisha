"""
Graph Orchestrator
==================
Central coordinator that builds all graph representations on contract upload.

Orchestrates:
1. NetworkX clause interaction graph
2. Risk propagation simulation
3. Negotiation priority ranking
4. Neo4j knowledge graph sync (using existing service)

This is the single entry point called during contract upload.
"""

import logging
from typing import Dict, List, Any
from .clause_graph import build_interaction_graph, get_graph_summary
from .risk_propagation import propagate_risk
from .graph_negotiation_advisor import generate_negotiation_advice

logger = logging.getLogger(__name__)


def build_all_graphs(contract, clauses: List[Any]) -> Dict[str, Any]:
    """
    Build all graph representations for a contract.

    This function is called automatically during contract upload.
    It orchestrates multiple graph-building services and returns
    metadata to be persisted in ContractGraphMeta model.

    Args:
        contract: Contract model instance
        clauses: List of Clause model instances

    Returns:
        Dict containing:
        - graph_summary: NetworkX graph nodes/edges
        - risk_timeline: Risk propagation simulation results
        - negotiation_advice: Prioritized negotiation recommendations
        - neo4j_synced: Whether Neo4j sync succeeded
    """
    logger.info(f"Building graphs for contract {contract.id}")

    result = {
        "graph_summary": {},
        "risk_timeline": {},
        "negotiation_advice": [],
        "neo4j_synced": False,
        "error": None
    }

    try:
        # Step 1: Build NetworkX clause interaction graph
        logger.info(f"Building NetworkX graph for {len(clauses)} clauses")
        nx_graph = build_interaction_graph(clauses)
        result["graph_summary"] = get_graph_summary(nx_graph)
        logger.info(f"NetworkX graph built: {nx_graph.number_of_nodes()} nodes, {nx_graph.number_of_edges()} edges")

        # Step 2: Run risk propagation simulation
        logger.info("Running risk propagation simulation")
        risk_propagation_data = propagate_risk(nx_graph)
        result["risk_timeline"] = risk_propagation_data
        logger.info(f"Risk propagation complete: {risk_propagation_data.get('propagation_steps', 0)} steps, "
                   f"total risk: {risk_propagation_data.get('total_risk', 0):.3f}")

        # Step 3: Generate negotiation advice
        logger.info("Generating negotiation advice")
        negotiation_advice = generate_negotiation_advice(nx_graph, risk_propagation_data)
        result["negotiation_advice"] = negotiation_advice

        high_priority_count = sum(1 for adv in negotiation_advice if adv.get('priority') == 'HIGH')
        logger.info(f"Negotiation advice generated: {len(negotiation_advice)} clauses analyzed, "
                   f"{high_priority_count} high-priority")

        # Step 4: Sync to Neo4j (optional, using existing service)
        try:
            from api.knowledge_graph_service import KnowledgeGraphService
            neo4j_service = KnowledgeGraphService()

            if neo4j_service.driver:
                sync_result = neo4j_service.sync_contract_to_graph(str(contract.id))
                result["neo4j_synced"] = sync_result.get('success', False)
                logger.info(f"Neo4j sync: {'successful' if result['neo4j_synced'] else 'failed'}")
            else:
                logger.info("Neo4j not available, skipping graph sync")
                result["neo4j_synced"] = False

        except Exception as neo4j_error:
            logger.warning(f"Neo4j sync failed (non-fatal): {neo4j_error}")
            result["neo4j_synced"] = False

    except Exception as e:
        logger.error(f"Error building graphs for contract {contract.id}: {e}", exc_info=True)
        result["error"] = str(e)
        # Return partial results even on error
        return result

    logger.info(f"All graphs built successfully for contract {contract.id}")
    return result


def rebuild_graphs_for_contract(contract_id: str) -> Dict[str, Any]:
    """
    Rebuild graphs for an existing contract (useful for re-analysis).

    Args:
        contract_id: Contract UUID

    Returns:
        Graph build results
    """
    from core.models import Contract, Clause

    try:
        contract = Contract.objects.get(id=contract_id)
        clauses = list(Clause.objects.filter(contract=contract, found=True))

        if not clauses:
            return {
                "error": "No clauses found for contract",
                "graph_summary": {},
                "risk_timeline": {},
                "negotiation_advice": []
            }

        return build_all_graphs(contract, clauses)

    except Contract.DoesNotExist:
        return {"error": f"Contract {contract_id} not found"}
    except Exception as e:
        logger.error(f"Error rebuilding graphs for contract {contract_id}: {e}")
        return {"error": str(e)}
