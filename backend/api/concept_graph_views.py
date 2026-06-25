"""
Concept Correlation Graph API Views
=====================================
REST endpoints for the Contract Concept Risk Topology Engine.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .services.concept_correlation_service import ConceptCorrelationService, CONTRACT_ARCHETYPES, CONCEPTS

logger = logging.getLogger(__name__)

# Singleton service instance (stateless, safe to share)
_service = None


def _get_service() -> ConceptCorrelationService:
    global _service
    if _service is None:
        _service = ConceptCorrelationService()
    return _service


class ConceptGraphAllView(APIView):
    """
    GET /api/concept-graph/all/
    Returns all 5 archetype graphs + global graph in one payload.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = _get_service()
            data = service.get_all_archetype_graphs()
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"ConceptGraphAllView error: {e}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConceptGraphByTypeView(APIView):
    """
    GET /api/concept-graph/<contract_type>/
    Returns the concept correlation graph for a specific contract archetype.
    contract_type: MSA | SaaS | NDA | Employment | EPC | ALL
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, contract_type: str):
        try:
            service = _get_service()
            if contract_type == "ALL":
                data = service.get_full_correlation_graph()
            else:
                data = service.get_archetype_graph(contract_type)
            return Response(data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"ConceptGraphByTypeView error: {e}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConceptCorrelationMatrixView(APIView):
    """
    GET /api/concept-graph/matrix/
    Returns the raw Pearson correlation matrix (CONCEPTS × CONCEPTS).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = _get_service()
            data = service.get_correlation_matrix()
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"ConceptCorrelationMatrixView error: {e}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConceptSummaryView(APIView):
    """
    GET /api/concept-graph/summary/
    Returns per-concept strength breakdown across all archetypes.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = _get_service()
            data = service.get_concept_summary()
            # Also attach archetype metadata
            data["archetypes"] = list(CONTRACT_ARCHETYPES.keys())
            data["total_concepts"] = len(CONCEPTS)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"ConceptSummaryView error: {e}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# NEW: Real Contract Data Extraction Endpoints (Phase 2)
# ============================================================================

class ContractConceptGraphView(APIView):
    """
    GET /api/concept-graph/contract/<contract_id>/
    Returns concept correlation graph extracted from a specific contract's clauses.

    Uses real clause data to extract concept strengths and builds a graph
    showing which legal concepts are present in the contract.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, contract_id: str):
        try:
            service = _get_service()
            data = service.get_contract_concept_graph(contract_id)
            return Response(data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"ContractConceptGraphView error: {e}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContractConceptComparisonView(APIView):
    """
    POST /api/concept-graph/compare/
    Compare concept profiles between two contracts.

    Request body:
    {
        "contract_id_1": "uuid",
        "contract_id_2": "uuid"
    }

    Returns:
    - Concept strength differences
    - Major increases/decreases
    - Percent changes
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            contract_id_1 = request.data.get("contract_id_1")
            contract_id_2 = request.data.get("contract_id_2")

            if not contract_id_1 or not contract_id_2:
                return Response(
                    {"error": "Both contract_id_1 and contract_id_2 required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            service = _get_service()
            data = service.compare_contract_concepts(contract_id_1, contract_id_2)
            return Response(data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"ContractConceptComparisonView error: {e}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# NEW: Advanced Analytics Endpoints (Phase 3)
# ============================================================================

class ConceptCentralityView(APIView):
    """
    GET /api/concept-graph/analytics/centrality/
    Compute centrality metrics for concept graph.

    Metrics:
    - Degree centrality (number of connections)
    - Betweenness centrality (bridge between clusters)
    - Eigenvector centrality (influence)

    Query params:
    - contract_id: Specific contract UUID (takes priority if provided)
    - contract_type: Archetype type (MSA/SaaS/NDA/Employment/EPC/ALL), default=ALL
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = _get_service()

            # Check if querying specific contract or archetype
            contract_id = request.query_params.get("contract_id")

            if contract_id:
                # Use contract-specific centrality
                data = service.compute_contract_centrality(contract_id)
            else:
                # Use archetype centrality
                contract_type = request.query_params.get("contract_type", "ALL")
                data = service.compute_concept_centrality(contract_type)

            return Response(data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"ConceptCentralityView error: {e}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConceptCommunitiesView(APIView):
    """
    GET /api/concept-graph/analytics/communities/?contract_type=MSA
    Detect concept communities using Louvain algorithm.

    Returns clusters of related concepts (e.g., Risk & Liability Cluster,
    IP & Data Protection Cluster).

    Query params:
    - contract_type: Optional (MSA/SaaS/NDA/Employment/EPC/ALL), default=ALL
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            contract_type = request.query_params.get("contract_type", "ALL")
            service = _get_service()
            data = service.detect_concept_communities(contract_type)
            return Response(data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"ConceptCommunitiesView error: {e}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# NEW: Temporal Tracking Endpoint (Phase 4 - Optional)
# ============================================================================

class ConceptEvolutionView(APIView):
    """
    GET /api/concept-graph/analytics/evolution/<contract_id>/
    Track concept strength changes across contract versions.

    Requires ClauseVersion model to be populated.
    Returns time-series data showing concept evolution over time.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, contract_id: str):
        try:
            service = _get_service()
            data = service.track_concept_evolution(contract_id)
            return Response(data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"ConceptEvolutionView error: {e}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
