"""
Risk Intelligence API Views
============================
Production-grade endpoints for graph-based risk analysis.

Endpoints:
1. POST /api/risk-intelligence/monte-carlo - Monte Carlo exposure simulation
2. POST /api/risk-intelligence/var - Value at Risk calculation
3. POST /api/risk-intelligence/stress-test - Stress scenario testing
4. GET /api/risk-intelligence/risk-subgraph/<contract_id> - Risk graph visualization
5. POST /api/risk-intelligence/similar-clauses - BM25+BERT clause search
6. POST /api/risk-intelligence/propagate - Risk propagation analysis
7. POST /api/risk-intelligence/setup-graph - Initialize enhanced graph schema

Author: PrimeContractAI System
"""

import logging
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from core.models import Contract, Clause
from api.services.monte_carlo_exposure import MonteCarloExposureSimulator
from api.services.clause_graph import build_interaction_graph
from ai.graph.risk_graph_schema import get_risk_graph_schema
from ai.rag.bm25_bert_retriever import create_clause_retriever, search_similar_clauses

logger = logging.getLogger(__name__)


class MonteCarloExposureView(APIView):
    """
    Monte Carlo exposure simulation for contract.

    POST /api/risk-intelligence/monte-carlo
    Body: {
        "contract_id": "uuid",
        "iterations": 5000 (optional)
    }
    """

    def post(self, request):
        try:
            contract_id = request.data.get('contract_id')
            iterations = request.data.get('iterations', 5000)

            if not contract_id:
                return Response(
                    {"error": "contract_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get contract and clauses
            contract = get_object_or_404(Contract, id=contract_id)
            clauses = list(Clause.objects.filter(contract=contract))

            if not clauses:
                return Response(
                    {"error": "No clauses found for this contract"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Build graph
            graph = build_interaction_graph(clauses)

            # Get contract value - handle currency formatting
            contract_value_str = str(contract.contract_value or '10000000')
            # Remove currency symbols and commas
            contract_value_str = contract_value_str.replace('$', '').replace(',', '').replace('₹', '').strip()
            try:
                contract_value = float(contract_value_str)
            except ValueError:
                contract_value = 10000000  # Default 1 Cr if parsing fails

            # Run Monte Carlo simulation
            simulator = MonteCarloExposureSimulator(iterations=iterations)
            result = simulator.simulate(clauses, graph, contract_value)

            return Response({
                "success": True,
                "contract_id": contract_id,
                "contract_value": contract_value,
                "monte_carlo": result
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[RISK-API] Monte Carlo failed: {e}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ValueAtRiskView(APIView):
    """
    Calculate Value at Risk (VaR) for contract.

    POST /api/risk-intelligence/var
    Body: {
        "contract_id": "uuid",
        "confidence_level": 0.95 (optional)
    }
    """

    def post(self, request):
        try:
            contract_id = request.data.get('contract_id')
            confidence_level = float(request.data.get('confidence_level', 0.95))

            if not contract_id:
                return Response(
                    {"error": "contract_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get contract and clauses
            contract = get_object_or_404(Contract, id=contract_id)
            clauses = list(Clause.objects.filter(contract=contract))

            if not clauses:
                return Response(
                    {"error": "No clauses found for this contract"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Build graph
            graph = build_interaction_graph(clauses)

            # Get contract value - handle currency formatting
            contract_value_str = str(contract.contract_value or '10000000')
            contract_value_str = contract_value_str.replace('$', '').replace(',', '').replace('₹', '').strip()
            try:
                contract_value = float(contract_value_str)
            except ValueError:
                contract_value = 10000000

            # Calculate VaR
            simulator = MonteCarloExposureSimulator()
            result = simulator.calculate_var(
                clauses,
                graph,
                contract_value,
                confidence_level
            )

            return Response({
                "success": True,
                "contract_id": contract_id,
                "var": result
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[RISK-API] VaR calculation failed: {e}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StressTestView(APIView):
    """
    Run stress test scenarios.

    POST /api/risk-intelligence/stress-test
    Body: {
        "contract_id": "uuid"
    }
    """

    def post(self, request):
        try:
            contract_id = request.data.get('contract_id')

            if not contract_id:
                return Response(
                    {"error": "contract_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get contract and clauses
            contract = get_object_or_404(Contract, id=contract_id)
            clauses = list(Clause.objects.filter(contract=contract))

            if not clauses:
                return Response(
                    {"error": "No clauses found for this contract"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Build graph
            graph = build_interaction_graph(clauses)

            # Get contract value - handle currency formatting
            contract_value_str = str(contract.contract_value or '10000000')
            contract_value_str = contract_value_str.replace('$', '').replace(',', '').replace('₹', '').strip()
            try:
                contract_value = float(contract_value_str)
            except ValueError:
                contract_value = 10000000

            # Run stress test
            simulator = MonteCarloExposureSimulator()
            result = simulator.stress_test(clauses, graph, contract_value)

            return Response({
                "success": True,
                "contract_id": contract_id,
                "stress_test": result
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[RISK-API] Stress test failed: {e}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RiskSubgraphView(APIView):
    """
    Get risk subgraph for visualization.

    GET /api/risk-intelligence/risk-subgraph/<contract_id>
    """
    permission_classes = [AllowAny]  # Allow for debugging - remove in production

    def get(self, request, contract_id):
        try:
            # Verify contract exists
            contract = get_object_or_404(Contract, id=contract_id)

            # Get risk graph schema
            risk_graph = get_risk_graph_schema()

            if not risk_graph.connected:
                # Fallback: Generate graph from MySQL data
                logger.info(f"[RISK-API] Neo4j not available, using MySQL fallback for contract {contract_id}")

                clauses = list(Clause.objects.filter(contract=contract))
                logger.info(f"[RISK-API] Found {len(clauses)} clauses for contract {contract_id}")
                nodes = []
                edges = []

                # Create clause nodes (React Flow compatible format)
                import math
                for idx, clause in enumerate(clauses):
                    risk_score = clause.risk_score or 0.5
                    clause_type = clause.clause_type or clause.clause_name or "General"

                    # Calculate size based on risk score (40-100px)
                    node_size = 40 + (risk_score * 60)

                    # Position nodes in circular layout
                    angle = (2 * math.pi * idx) / max(len(clauses), 1)
                    radius = 300
                    x = radius * math.cos(angle) + 500
                    y = radius * math.sin(angle) + 400

                    # Color node by risk level
                    risk_level = clause.risk_level or ('HIGH' if risk_score >= 0.7 else 'MEDIUM' if risk_score >= 0.4 else 'LOW')
                    risk_color = '#F16667' if risk_level == 'HIGH' else '#f59e0b' if risk_level == 'MEDIUM' else '#10b981'
                    extracted = clause.extracted_text or ''
                    nodes.append({
                        "id": str(clause.id),
                        "data": {
                            "label": clause.clause_name or f"Clause {idx+1}",
                            "type": "Clause",
                            "risk_score": round(risk_score, 2),
                            "risk_level": risk_level,
                            "breach_probability": round(risk_score * 0.8, 2),
                            "category": clause_type,
                            "clause_text": extracted[:120] + "..." if len(extracted) > 120 else extracted,
                            "color": risk_color,
                            "size": int(node_size)
                        },
                        "position": {"x": x, "y": y},
                        "type": "neo4j"
                    })

                # Add contract central node
                contract_label = (contract.original_filename or
                                contract.filename or
                                f"Contract {str(contract_id)[:8]}")
                nodes.insert(0, {
                    "id": f"contract-{contract_id}",
                    "data": {
                        "label": contract_label,
                        "type": "Contract",
                        "size": 120,
                        "contract_type": contract.contract_type or "Unknown",
                        "status": contract.status or "active"
                    },
                    "position": {"x": 500, "y": 400},
                    "type": "neo4j"
                })

                # Connect all clauses to contract
                for clause in clauses:
                    edges.append({
                        "id": f"e-contract-{clause.id}",
                        "source": f"contract-{contract_id}",
                        "target": str(clause.id),
                        "label": "HAS_CLAUSE",
                        "color": "#68BC00",
                        "width": 2
                    })

                # Create edges between related clauses (same risk level or same clause type)
                for i, clause1 in enumerate(clauses):
                    for clause2 in clauses[i+1:]:
                        type1 = clause1.clause_type or clause1.clause_name
                        type2 = clause2.clause_type or clause2.clause_name
                        rl1 = clause1.risk_level or 'MEDIUM'
                        rl2 = clause2.risk_level or 'MEDIUM'
                        if type1 and type2 and type1 == type2:
                            edges.append({
                                "id": f"e-{clause1.id}-{clause2.id}",
                                "source": str(clause1.id),
                                "target": str(clause2.id),
                                "label": "SAME_TYPE",
                                "color": "#9063CD",
                                "width": 1,
                                "animated": False
                            })
                        elif rl1 == rl2 and rl1 == 'HIGH':
                            edges.append({
                                "id": f"e-risk-{clause1.id}-{clause2.id}",
                                "source": str(clause1.id),
                                "target": str(clause2.id),
                                "label": "AMPLIFIES",
                                "color": "#F16667",
                                "width": 1,
                                "animated": True
                            })

                logger.info(f"[RISK-API] Returning {len(nodes)} nodes and {len(edges)} edges")
                return Response({
                    "success": True,
                    "contract_id": str(contract_id),
                    "nodes": nodes,
                    "edges": edges,
                    "fallback_mode": True,
                    "message": "Using MySQL data (Neo4j unavailable)"
                }, status=status.HTTP_200_OK)

            # Fetch subgraph from Neo4j
            subgraph = risk_graph.get_risk_subgraph(contract_id)

            neo4j_nodes = subgraph.get("nodes", [])
            neo4j_edges = subgraph.get("edges", [])
            logger.info(f"[RISK-API] Subgraph nodes: {len(neo4j_nodes)}, edges: {len(neo4j_edges)}")

            # If Neo4j has no data for this contract, fall back to MySQL
            if not neo4j_nodes:
                logger.info(f"[RISK-API] Neo4j empty for contract {contract_id}, using MySQL fallback")
                clauses = list(Clause.objects.filter(contract=contract))
                import math as _math
                nodes = []
                edges = []
                for idx, clause in enumerate(clauses):
                    risk_score = clause.risk_score or 0.5
                    clause_type = clause.clause_type or clause.clause_name or "General"
                    node_size = 40 + (risk_score * 60)
                    angle = (2 * _math.pi * idx) / max(len(clauses), 1)
                    x = 300 * _math.cos(angle) + 500
                    y = 300 * _math.sin(angle) + 400
                    risk_level = clause.risk_level or ('HIGH' if risk_score >= 0.7 else 'MEDIUM' if risk_score >= 0.4 else 'LOW')
                    risk_color = '#F16667' if risk_level == 'HIGH' else '#f59e0b' if risk_level == 'MEDIUM' else '#10b981'
                    extracted = clause.extracted_text or ''
                    nodes.append({
                        "id": str(clause.id),
                        "data": {
                            "label": clause.clause_name or f"Clause {idx+1}",
                            "type": "Clause",
                            "risk_score": round(risk_score, 2),
                            "risk_level": risk_level,
                            "breach_probability": round(risk_score * 0.8, 2),
                            "category": clause_type,
                            "clause_text": extracted[:120] + "..." if len(extracted) > 120 else extracted,
                            "color": risk_color,
                            "size": int(node_size)
                        },
                        "position": {"x": x, "y": y},
                        "type": "neo4j"
                    })
                contract_label = contract.original_filename or contract.filename or f"Contract {str(contract_id)[:8]}"
                nodes.insert(0, {
                    "id": f"contract-{contract_id}",
                    "data": {
                        "label": contract_label,
                        "type": "Contract",
                        "size": 120,
                        "contract_type": contract.contract_type or "Unknown",
                        "status": contract.status or "active"
                    },
                    "position": {"x": 500, "y": 400},
                    "type": "neo4j"
                })
                for clause in clauses:
                    edges.append({
                        "id": f"e-contract-{clause.id}",
                        "source": f"contract-{contract_id}",
                        "target": str(clause.id),
                        "label": "HAS_CLAUSE",
                        "color": "#68BC00",
                        "width": 2,
                        "animated": False
                    })
                for i, clause1 in enumerate(clauses):
                    for clause2 in clauses[i+1:]:
                        type1 = clause1.clause_type or clause1.clause_name
                        type2 = clause2.clause_type or clause2.clause_name
                        rl1 = clause1.risk_level or 'MEDIUM'
                        rl2 = clause2.risk_level or 'MEDIUM'
                        if type1 and type2 and type1 == type2:
                            edges.append({"id": f"e-{clause1.id}-{clause2.id}", "source": str(clause1.id), "target": str(clause2.id), "label": "SAME_TYPE", "color": "#9063CD", "width": 1, "animated": False})
                        elif rl1 == rl2 == 'HIGH':
                            edges.append({"id": f"e-risk-{clause1.id}-{clause2.id}", "source": str(clause1.id), "target": str(clause2.id), "label": "AMPLIFIES", "color": "#F16667", "width": 1, "animated": True})
                logger.info(f"[RISK-API] MySQL fallback: {len(nodes)} nodes, {len(edges)} edges")
                return Response({
                    "success": True,
                    "contract_id": str(contract_id),
                    "nodes": nodes,
                    "edges": edges,
                    "fallback_mode": True,
                    "message": "Using MySQL data (contract not yet ingested in Neo4j)"
                }, status=status.HTTP_200_OK)

            # Transform Neo4j format to React Flow format
            import math

            # Convert nodes to React Flow format
            reactflow_nodes = []
            for idx, node in enumerate(neo4j_nodes):
                node_type = node.get('type', 'Unknown')
                risk_score = node.get('risk_score', node.get('base_multiplier', 0.5))
                node_size = 40 + (risk_score * 60)

                # Circular layout
                angle = (2 * math.pi * idx) / max(len(neo4j_nodes), 1)
                radius = 300
                x = radius * math.cos(angle) + 500
                y = radius * math.sin(angle) + 400

                reactflow_nodes.append({
                    "id": str(node['id']),
                    "data": {
                        "label": node.get('label', 'Unnamed'),
                        "type": node_type,
                        "size": int(node_size),
                        **{k: v for k, v in node.items() if k not in ['id', 'type', 'label']}
                    },
                    "position": {"x": x, "y": y},
                    "type": "neo4j"
                })

            # Add central contract node
            reactflow_nodes.insert(0, {
                "id": f"contract-{contract_id}",
                "data": {
                    "label": contract.original_filename or contract.filename or f"Contract {str(contract_id)[:8]}",
                    "type": "Contract",
                    "size": 120
                },
                "position": {"x": 500, "y": 400},
                "type": "neo4j"
            })

            # Build set of node IDs for validation
            node_ids = set(str(node['id']) for node in reactflow_nodes)

            # Convert edges to React Flow format with better colors
            reactflow_edges = []
            for edge in neo4j_edges:
                # Only create edge if both source and target nodes exist
                source_id = str(edge['source'])
                target_id = str(edge['target'])

                if source_id not in node_ids or target_id not in node_ids:
                    logger.warning(f"[RISK-API] Skipping edge {source_id}->{target_id}: missing node")
                    continue

                edge_type = edge.get('type', 'RELATES_TO')
                # Color coding: INTRODUCES = orange, IMPACTS = red, others = gray
                if edge_type == 'INTRODUCES':
                    color = '#F79767'  # Orange - clause introduces risk
                    width = 3
                    animated = True
                elif edge_type == 'IMPACTS':
                    color = '#F16667'  # Red - risk impacts another risk
                    width = 2
                    animated = True
                else:
                    color = '#8D99AE'  # Gray
                    width = 2
                    animated = False

                reactflow_edges.append({
                    "id": f"e-{source_id}-{target_id}",
                    "source": source_id,
                    "target": target_id,
                    "label": edge_type,
                    "color": color,
                    "width": width,
                    "animated": animated
                })

            # Add edges from contract to all clauses (green lines from center)
            for node in reactflow_nodes[1:]:  # Skip contract node itself
                if node['data']['type'] == 'Clause':
                    reactflow_edges.insert(0, {
                        "id": f"e-contract-{node['id']}",
                        "source": f"contract-{contract_id}",
                        "target": node['id'],
                        "label": "HAS_CLAUSE",
                        "color": "#68BC00",
                        "width": 2,
                        "animated": False
                    })

            logger.info(f"[RISK-API] Transformed to {len(reactflow_nodes)} React Flow nodes and {len(reactflow_edges)} edges")

            # Explicitly serialize to ensure proper JSON
            response_data = {
                "success": True,
                "contract_id": str(contract_id),
                "subgraph": {
                    "nodes": reactflow_nodes,
                    "edges": reactflow_edges,
                    "contract_id": str(contract_id)
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[RISK-API] Subgraph fetch failed: {e}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SimilarClausesView(APIView):
    """
    Find similar clauses using BM25 + BERT hybrid search.

    POST /api/risk-intelligence/similar-clauses
    Body: {
        "clause_id": "uuid",
        "top_k": 5 (optional)
    }
    OR
    Body: {
        "query_text": "search text",
        "contract_id": "uuid" (optional),
        "top_k": 5 (optional)
    }
    """

    def post(self, request):
        try:
            clause_id = request.data.get('clause_id')
            query_text = request.data.get('query_text')
            contract_id = request.data.get('contract_id')
            top_k = int(request.data.get('top_k', 5))

            if clause_id:
                # Find similar to a specific clause
                clause = get_object_or_404(Clause, id=clause_id)
                all_clauses = list(Clause.objects.all())

                results = search_similar_clauses(clause, all_clauses, top_k)

            elif query_text:
                # Search by text
                if contract_id:
                    clauses = list(Clause.objects.filter(contract_id=contract_id))
                else:
                    clauses = list(Clause.objects.all()[:1000])  # Limit for performance

                retriever = create_clause_retriever(clauses)
                results = retriever.search(query_text, top_k=top_k)

            else:
                return Response(
                    {"error": "Either clause_id or query_text is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response({
                "success": True,
                "results": results,
                "count": len(results)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[RISK-API] Similar clauses search failed: {e}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RiskPropagationView(APIView):
    """
    Analyze risk propagation through the contract graph.

    POST /api/risk-intelligence/propagate
    Body: {
        "contract_id": "uuid",
        "source_clause_id": "uuid" (optional)
    }
    """

    def post(self, request):
        try:
            contract_id = request.data.get('contract_id')
            source_clause_id = request.data.get('source_clause_id')

            if not contract_id:
                return Response(
                    {"error": "contract_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get contract and clauses
            contract = get_object_or_404(Contract, id=contract_id)
            clauses = list(Clause.objects.filter(contract=contract))

            if not clauses:
                return Response(
                    {"error": "No clauses found for this contract"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Build graph
            from api.services.risk_propagation import propagate_risk
            graph = build_interaction_graph(clauses)

            # Propagate risk
            propagated_scores = propagate_risk(
                graph,
                source_node=source_clause_id,
                iterations=5,
                damping=0.85
            )

            return Response({
                "success": True,
                "contract_id": contract_id,
                "source_clause_id": source_clause_id,
                "propagated_scores": propagated_scores
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[RISK-API] Risk propagation failed: {e}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SetupGraphSchemaView(APIView):
    """
    Initialize enhanced graph schema (one-time setup).

    POST /api/risk-intelligence/setup-graph
    Body: {
        "apply_schema": true (optional),
        "seed_risks": true (optional),
        "seed_jurisdictions": true (optional)
    }
    """

    def post(self, request):
        try:
            apply_schema = request.data.get('apply_schema', True)
            seed_risks = request.data.get('seed_risks', True)
            seed_jurisdictions = request.data.get('seed_jurisdictions', True)

            risk_graph = get_risk_graph_schema()

            if not risk_graph.connected:
                return Response({
                    "error": "Neo4j not available. Check connection settings.",
                    "success": False
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            results = {}

            # Apply schema
            if apply_schema:
                results['schema_applied'] = risk_graph.apply_schema()

            # Seed risks
            if seed_risks:
                results['risks_seeded'] = risk_graph.seed_risk_categories()

            # Seed jurisdictions
            if seed_jurisdictions:
                results['jurisdictions_seeded'] = risk_graph.seed_jurisdictions()

            return Response({
                "success": True,
                "results": results,
                "message": "Graph schema setup completed"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[RISK-API] Setup failed: {e}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CascadingRisksView(APIView):
    """
    Get cascading risk impacts using multi-hop IMPACTS traversal.

    GET /api/risk-intelligence/cascading-risks/<risk_id>
    Query params:
        - max_depth: Maximum traversal depth (1-5, default 3)
    """
    permission_classes = [AllowAny]

    def get(self, request, risk_id):
        try:
            max_depth = int(request.query_params.get('max_depth', 3))

            risk_graph = get_risk_graph_schema()

            if not risk_graph.connected:
                return Response({
                    "error": "Neo4j not available. Multi-hop traversal requires Neo4j.",
                    "success": False
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            # Get cascading risks
            result = risk_graph.get_cascading_risks(risk_id, max_depth=max_depth)

            return Response({
                "success": True,
                "risk_id": risk_id,
                "analysis": result
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[RISK-API] Cascading risk analysis failed: {e}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RiskBlastRadiusView(APIView):
    """
    Calculate blast radius for all risks in a contract using multi-hop analysis.

    GET /api/risk-intelligence/blast-radius/<contract_id>
    Query params:
        - max_hops: Maximum hops for impact analysis (1-5, default 3)
    """
    permission_classes = [AllowAny]

    def get(self, request, contract_id):
        try:
            max_hops = int(request.query_params.get('max_hops', 3))

            risk_graph = get_risk_graph_schema()

            if not risk_graph.connected:
                return Response({
                    "error": "Neo4j not available. Blast radius requires Neo4j.",
                    "success": False
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            # Calculate blast radius
            result = risk_graph.get_risk_blast_radius(contract_id, max_hops=max_hops)

            # Sort by blast radius
            result['risks'] = sorted(
                result.get('risks', []),
                key=lambda x: x.get('blast_radius', 0),
                reverse=True
            )

            return Response({
                "success": True,
                "contract_id": contract_id,
                "analysis": result
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[RISK-API] Blast radius calculation failed: {e}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MultiHopRiskGraphView(APIView):
    """
    Get risk subgraph with multi-hop IMPACTS traversal.

    GET /api/risk-intelligence/risk-subgraph-multihop/<contract_id>
    Query params:
        - max_hops: Maximum hops (1-3, default 2)
    """
    permission_classes = [AllowAny]

    def get(self, request, contract_id):
        try:
            max_hops = int(request.query_params.get('max_hops', 2))

            risk_graph = get_risk_graph_schema()

            if not risk_graph.connected:
                return Response({
                    "error": "Neo4j not available",
                    "success": False
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            # Fetch multi-hop subgraph
            subgraph = risk_graph.get_risk_subgraph(
                contract_id,
                include_multihop=True,
                max_hops=max_hops
            )

            # Get contract for label
            contract = get_object_or_404(Contract, id=contract_id)

            # Transform Neo4j format to React Flow format (same as regular endpoint)
            import math
            neo4j_nodes = subgraph.get("nodes", [])
            neo4j_edges = subgraph.get("edges", [])

            # Convert nodes to React Flow format
            reactflow_nodes = []
            for idx, node in enumerate(neo4j_nodes):
                node_type = node.get('type', 'Unknown')
                risk_score = node.get('risk_score', node.get('base_multiplier', 0.5))
                node_size = 40 + (risk_score * 60)

                # Circular layout
                angle = (2 * math.pi * idx) / max(len(neo4j_nodes), 1)
                radius = 300
                x = radius * math.cos(angle) + 500
                y = radius * math.sin(angle) + 400

                reactflow_nodes.append({
                    "id": str(node['id']),
                    "data": {
                        "label": node.get('label', 'Unnamed'),
                        "type": node_type,
                        "size": int(node_size),
                        **{k: v for k, v in node.items() if k not in ['id', 'type', 'label']}
                    },
                    "position": {"x": x, "y": y},
                    "type": "neo4j"
                })

            # Add central contract node
            reactflow_nodes.insert(0, {
                "id": f"contract-{contract_id}",
                "data": {
                    "label": contract.original_filename or contract.filename or f"Contract {str(contract_id)[:8]}",
                    "type": "Contract",
                    "size": 120
                },
                "position": {"x": 500, "y": 400},
                "type": "neo4j"
            })

            # Build set of node IDs for validation
            node_ids = set(str(node['id']) for node in reactflow_nodes)

            # Convert edges to React Flow format with better colors
            reactflow_edges = []
            multi_hop_count = 0
            for edge in neo4j_edges:
                # Only create edge if both source and target nodes exist
                source_id = str(edge['source'])
                target_id = str(edge['target'])

                if source_id not in node_ids or target_id not in node_ids:
                    logger.warning(f"[RISK-API] Skipping edge {source_id}->{target_id}: missing node")
                    continue

                edge_type = edge.get('type', 'RELATES_TO')
                is_multi_hop = edge.get('multi_hop', False)

                if is_multi_hop:
                    multi_hop_count += 1

                # Color coding
                if edge_type == 'INTRODUCES':
                    color = '#F79767'  # Orange
                    width = 3
                    animated = True
                elif edge_type == 'IMPACTS':
                    color = '#F16667'  # Red
                    width = 2 if not is_multi_hop else 3  # Thicker for multi-hop
                    animated = True
                else:
                    color = '#8D99AE'  # Gray
                    width = 2
                    animated = False

                reactflow_edges.append({
                    "id": f"e-{source_id}-{target_id}",
                    "source": source_id,
                    "target": target_id,
                    "label": edge_type + (" (multi-hop)" if is_multi_hop else ""),
                    "color": color,
                    "width": width,
                    "animated": animated
                })

            # Add edges from contract to all clauses
            for node in reactflow_nodes[1:]:
                if node['data']['type'] == 'Clause':
                    reactflow_edges.insert(0, {
                        "id": f"e-contract-{node['id']}",
                        "source": f"contract-{contract_id}",
                        "target": node['id'],
                        "label": "HAS_CLAUSE",
                        "color": "#68BC00",
                        "width": 2,
                        "animated": False
                    })

            return Response({
                "success": True,
                "contract_id": str(contract_id),
                "subgraph": {
                    "nodes": reactflow_nodes,
                    "edges": reactflow_edges,
                    "contract_id": str(contract_id)
                },
                "stats": {
                    "total_nodes": len(reactflow_nodes),
                    "total_edges": len(reactflow_edges),
                    "multi_hop_edges": multi_hop_count,
                    "max_hops": max_hops
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[RISK-API] Multi-hop subgraph failed: {e}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
