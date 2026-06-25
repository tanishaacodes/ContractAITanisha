"""
Trust Propagation API Views

RESTful endpoints for Neo4j trust propagation analysis.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ai.trust_engine.neo4j_trust_propagation import get_trust_propagation_service


class TrustImpactRadiusView(APIView):
    """
    Calculate trust impact radius for a clause.

    GET /api/clauses/<clause_id>/trust/impact/?depth=3
    """

    def get(self, request, clause_id):
        """Get trust impact radius"""
        try:
            max_depth = int(request.query_params.get('depth', 3))
            max_depth = min(max_depth, 5)  # Cap at 5 for performance

            service = get_trust_propagation_service()

            if not service.neo4j_available:
                return Response(
                    {"error": "Neo4j not available. Trust propagation requires Neo4j."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            results = service.propagate_trust_impact(clause_id, max_depth)

            return Response({
                "clause_id": clause_id,
                "max_depth": max_depth,
                "affected_count": len(results),
                "affected_clauses": results
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SilentKillerDetectionView(APIView):
    """
    Detect Silent Killer clauses via graph analysis.

    GET /api/trust/silent-killers/?min_trust=0.7&max_neighbor=0.4
    """

    def get(self, request):
        """Find silent killer clauses"""
        try:
            min_local_trust = float(request.query_params.get('min_trust', 0.7))
            max_neighbor_trust = float(request.query_params.get('max_neighbor', 0.4))

            service = get_trust_propagation_service()

            if not service.neo4j_available:
                return Response(
                    {"error": "Neo4j not available"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            results = service.find_silent_killers(min_local_trust, max_neighbor_trust)

            return Response({
                "silent_killers": results,
                "count": len(results),
                "criteria": {
                    "min_local_trust": min_local_trust,
                    "max_neighbor_trust": max_neighbor_trust
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class JurisdictionalTrustDriftView(APIView):
    """
    Analyze trust by jurisdiction.

    GET /api/trust/jurisdictional-drift/
    """

    def get(self, request):
        """Get jurisdictional trust analysis"""
        try:
            service = get_trust_propagation_service()

            if not service.neo4j_available:
                return Response(
                    {"error": "Neo4j not available"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            results = service.jurisdictional_trust_drift()

            return Response({
                "jurisdictions": results,
                "count": len(results)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CounterpartyTrustCollapseView(APIView):
    """
    Find counterparty-specific trust failures.

    GET /api/trust/counterparty-collapse/
    """

    def get(self, request):
        """Get counterparty trust collapse analysis"""
        try:
            service = get_trust_propagation_service()

            if not service.neo4j_available:
                return Response(
                    {"error": "Neo4j not available"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            results = service.counterparty_trust_collapse()

            return Response({
                "counterparty_types": results,
                "count": len(results)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TrustContagionSimulationView(APIView):
    """
    Simulate trust contagion if a clause fails.

    POST /api/clauses/<clause_id>/trust/simulate-failure/
    """

    def post(self, request, clause_id):
        """Simulate clause failure contagion"""
        try:
            service = get_trust_propagation_service()

            if not service.neo4j_available:
                return Response(
                    {"error": "Neo4j not available"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            simulation = service.trust_contagion_simulation(clause_id)

            return Response(simulation, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TrustRepairRecommendationView(APIView):
    """
    Get repair recommendations for low-trust clause.

    GET /api/clauses/<clause_id>/trust/repair-recommendations/
    """

    def get(self, request, clause_id):
        """Get trust repair recommendations"""
        try:
            service = get_trust_propagation_service()

            if not service.neo4j_available:
                return Response(
                    {"error": "Neo4j not available"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            recommendations = service.recommend_trust_repair(clause_id)

            return Response(recommendations, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SyncClauseTrustToGraphView(APIView):
    """
    Sync trust scores from ClauseHealthMetrics to Neo4j.

    POST /api/clauses/<clause_id>/trust/sync-to-graph/
    """

    def post(self, request, clause_id):
        """Sync trust scores to graph"""
        try:
            # Get trust data from request or fetch from database
            trust_score = request.data.get('trust_score')
            enforceability = request.data.get('enforceability')
            negotiability = request.data.get('negotiability')
            ambiguity = request.data.get('ambiguity')
            litigation_survival = request.data.get('litigation_survival')
            badge = request.data.get('badge')

            if not all([trust_score is not None, enforceability is not None,
                       negotiability is not None, ambiguity is not None,
                       litigation_survival is not None, badge]):
                return Response(
                    {"error": "Missing required trust fields"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            service = get_trust_propagation_service()

            if not service.neo4j_available:
                return Response(
                    {"error": "Neo4j not available"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            result = service.sync_clause_trust(
                clause_id,
                trust_score,
                enforceability,
                negotiability,
                ambiguity,
                litigation_survival,
                badge
            )

            return Response({
                "message": "Trust scores synced to graph",
                "clause_id": clause_id,
                "synced": len(result) > 0
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
