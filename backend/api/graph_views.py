"""
Neo4j Clause Evolution Graph API Views
Provides endpoints for clause lineage and evolution tracking
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from core.models import Clause, ClauseVersion
from ai.graph_sync import get_graph_sync
from ai.graph_driver import get_neo4j_driver


class ClauseEvolutionView(APIView):
    """
    Get clause evolution path
    GET /api/graph/evolution/{clause_id}/
    """
    permission_classes = [AllowAny]

    def get(self, request, clause_id):
        try:
            clause = Clause.objects.get(id=clause_id)
        except Clause.DoesNotExist:
            return Response(
                {'error': 'Clause not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        graph_sync = get_graph_sync()
        evolution_data = graph_sync.get_clause_evolution_path(clause_id)

        # Format for frontend
        nodes = []
        links = []

        for item in evolution_data:
            v = item.get('v', {})
            node_data = {
                'id': v.get('id'),
                'version': v.get('version_number'),
                'risk_score': v.get('risk_score', 0.5),
                'text_preview': v.get('text', '')[:100]
            }
            nodes.append(node_data)

        return Response({
            'clause_id': str(clause_id),
            'clause_name': clause.clause_name,
            'nodes': nodes,
            'links': links
        })


class ClauseBestVersionView(APIView):
    """
    Get best performing version of a clause
    GET /api/graph/best-version/{clause_id}/
    """
    permission_classes = [AllowAny]

    def get(self, request, clause_id):
        try:
            clause = Clause.objects.get(id=clause_id)
        except Clause.DoesNotExist:
            return Response(
                {'error': 'Clause not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        graph_sync = get_graph_sync()
        best_version = graph_sync.get_best_performing_version(clause_id)

        if not best_version:
            return Response({
                'message': 'No version data available in graph'
            })

        v = best_version.get('v', {})

        return Response({
            'clause_id': str(clause_id),
            'best_version': {
                'id': v.get('id'),
                'version_number': v.get('version_number'),
                'avg_outcome': best_version.get('avg_outcome'),
                'event_count': best_version.get('event_count')
            }
        })


class GraphSyncView(APIView):
    """
    Sync clause data to Neo4j
    POST /api/graph/sync/
    POST /api/graph/sync/{clause_id}/
    """
    permission_classes = [AllowAny]

    def post(self, request, clause_id=None):
        graph_sync = get_graph_sync()

        if clause_id:
            # Sync single clause
            try:
                clause = Clause.objects.get(id=clause_id)
                graph_sync.sync_clause_family(clause)

                return Response({
                    'message': f'Synced clause {clause.clause_name} to graph',
                    'clause_id': str(clause_id)
                })

            except Clause.DoesNotExist:
                return Response(
                    {'error': 'Clause not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        else:
            # Sync all clauses
            clauses = Clause.objects.all()[:20]  # Limit for demo
            synced_count = 0

            for clause in clauses:
                try:
                    graph_sync.sync_clause_family(clause)
                    synced_count += 1
                except Exception as e:
                    print(f"[ERROR] Failed to sync clause {clause.id}: {e}")

            return Response({
                'message': f'Synced {synced_count} clauses to graph',
                'total_clauses': clauses.count()
            })


class GraphInitializeView(APIView):
    """
    Initialize Neo4j schema
    POST /api/graph/initialize/
    """
    permission_classes = [AllowAny]  # Allow setup without auth

    def post(self, request):
        driver = get_neo4j_driver()

        if not driver.driver:
            return Response({
                'error': 'Neo4j is not connected. Please configure NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD environment variables.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        driver.initialize_schema()

        return Response({
            'message': 'Neo4j schema initialized successfully',
            'uri': driver.uri
        })


class GraphStatusView(APIView):
    """
    Check Neo4j connection status
    GET /api/graph/status/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        driver = get_neo4j_driver()

        if not driver.driver:
            return Response({
                'connected': False,
                'message': 'Neo4j is not connected',
                'config_needed': {
                    'NEO4J_URI': 'bolt://localhost:7687',
                    'NEO4J_USER': 'neo4j',
                    'NEO4J_PASSWORD': 'your_password'
                }
            })

        # Try to run a simple query
        result = driver.run_query("RETURN 1 as test")

        if result:
            # Get graph stats
            stats_query = """
            MATCH (c:Clause) WITH count(c) as clauses
            MATCH (v:ClauseVersion) WITH clauses, count(v) as versions
            MATCH (e:Event) WITH clauses, versions, count(e) as events
            RETURN clauses, versions, events
            """

            stats = driver.run_query(stats_query)
            graph_stats = stats[0] if stats else {'clauses': 0, 'versions': 0, 'events': 0}

            return Response({
                'connected': True,
                'uri': driver.uri,
                'stats': graph_stats
            })

        return Response({
            'connected': False,
            'message': 'Neo4j connection test failed'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
