"""
Self-Healing Clause Library API Views
RESTful endpoints for clause health monitoring and auto-promotion
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta

from core.models import (
    Clause, ClauseVersion, ClauseEvent, ClauseHealthMetrics
)
from ai.self_healing.promoter import get_promoter
from ai.self_healing.scorer import get_health_scorer
from ai.self_healing.rag import build_rag_from_queryset


class ClauseHealthView(APIView):
    """
    Get health metrics for all clauses or a specific clause
    GET /api/clauses/health/
    GET /api/clauses/health/{clause_id}/
    """

    def get(self, request, clause_id=None):
        try:
            if clause_id:
                # Single clause health
                try:
                    clause = Clause.objects.get(id=clause_id)
                except Clause.DoesNotExist:
                    return Response(
                        {'error': 'Clause not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # Get or compute health metrics
                try:
                    metrics = ClauseHealthMetrics.objects.get(clause=clause)
                    data = {
                        'clause_id': str(clause.id),
                        'clause_name': clause.clause_name,
                        'health_score': metrics.health_score,
                        'status': metrics.status,
                        'success_rate': metrics.success_rate,
                        'enforceability_score': metrics.enforceability_score,
                        'negotiation_score': metrics.negotiation_score,
                        'usage_count': metrics.usage_count,
                        'is_promoted': metrics.is_promoted,
                        'promoted_at': metrics.promoted_at,
                        'last_calculated': metrics.last_calculated
                    }
                except ClauseHealthMetrics.DoesNotExist:
                    # Compute on-the-fly
                    versions = ClauseVersion.objects.filter(clause=clause)
                    if versions.exists():
                        latest_version = versions.first()
                        events = ClauseEvent.objects.filter(clause_version=latest_version)

                        scorer = get_health_scorer()
                        computed_metrics = scorer.compute_health(list(events), usage_count=events.count())

                        data = {
                            'clause_id': str(clause.id),
                            'clause_name': clause.clause_name,
                            **computed_metrics,
                            'status': scorer.determine_status(computed_metrics['health_score']),
                            'is_promoted': False,
                            'note': 'Computed on-the-fly (not persisted)'
                        }
                    else:
                        return Response(
                            {'error': 'No versions found for this clause'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                return Response(data)

            else:
                # All clauses health
                all_metrics = ClauseHealthMetrics.objects.select_related('clause').all()

                data = []
                for metrics in all_metrics:
                    data.append({
                        'clause_id': str(metrics.clause.id),
                        'clause_code': metrics.clause.clause_name,
                        'status': metrics.status,
                        'health_score': metrics.health_score,
                        'success_rate': metrics.success_rate,
                        'usage_count': metrics.usage_count,
                        'is_promoted': metrics.is_promoted
                    })

                return Response({
                    'total': len(data),
                    'clauses': data
                })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClausePromotionView(APIView):
    """
    Auto-promote best-performing clause versions
    POST /api/clauses/promote/{clause_id}/
    POST /api/clauses/promote/batch/
    """

    def post(self, request, clause_id=None):
        try:
            promoter = get_promoter()
            dry_run = request.data.get('dry_run', False)

            if clause_id:
                # Single clause promotion
                result = promoter.auto_promote_clause(clause_id, dry_run=dry_run)
                return Response(result)
            else:
                # Batch promotion
                clause_ids = request.data.get('clause_ids', None)
                result = promoter.batch_promote_clauses(clause_ids=clause_ids, dry_run=dry_run)
                return Response(result)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClauseRetirementView(APIView):
    """
    Auto-retire weak clauses
    POST /api/clauses/retire/
    """

    def post(self, request):
        try:
            promoter = get_promoter()
            dry_run = request.data.get('dry_run', False)
            min_health_score = request.data.get('min_health_score', 0.45)

            result = promoter.auto_retire_weak_clauses(
                min_health_score=min_health_score,
                dry_run=dry_run
            )

            return Response(result)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClauseAnalysisView(APIView):
    """
    Analyze clause family (all versions)
    GET /api/clauses/analyze/{clause_id}/
    """

    def get(self, request, clause_id):
        try:
            promoter = get_promoter()
            analysis = promoter.analyze_clause_family(clause_id)

            return Response(analysis)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClauseHealthReportView(APIView):
    """
    Get overall health report for all clauses
    GET /api/clauses/health/report/
    """

    def get(self, request):
        try:
            promoter = get_promoter()
            report = promoter.health_report()

            return Response(report)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClauseEventView(APIView):
    """
    Create and retrieve clause events
    POST /api/clauses/events/
    GET /api/clauses/events/{clause_version_id}/
    """

    def post(self, request):
        """Create a new clause event"""
        try:
            clause_version_id = request.data.get('clause_version_id')
            event_type = request.data.get('event_type')
            outcome_score = request.data.get('outcome_score')
            description = request.data.get('description', '')
            jurisdiction = request.data.get('jurisdiction', '')
            counterparty_type = request.data.get('counterparty_type', '')
            contract_id = request.data.get('contract_id', None)

            # Validate required fields
            if not all([clause_version_id, event_type, outcome_score is not None]):
                return Response(
                    {'error': 'clause_version_id, event_type, and outcome_score are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get clause version
            try:
                clause_version = ClauseVersion.objects.get(id=clause_version_id)
            except ClauseVersion.DoesNotExist:
                return Response(
                    {'error': 'Clause version not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Create event
            event = ClauseEvent.objects.create(
                clause_version=clause_version,
                event_type=event_type,
                outcome_score=float(outcome_score),
                description=description,
                jurisdiction=jurisdiction,
                counterparty_type=counterparty_type,
                contract_id=contract_id
            )

            # Recompute health metrics
            self._update_health_metrics(clause_version.clause)

            return Response({
                'id': str(event.id),
                'clause_version_id': str(event.clause_version.id),
                'event_type': event.event_type,
                'outcome_score': event.outcome_score,
                'created_at': event.created_at
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request, clause_version_id=None):
        """Get events for a clause version"""
        try:
            if clause_version_id:
                events = ClauseEvent.objects.filter(clause_version_id=clause_version_id)
            else:
                events = ClauseEvent.objects.all()[:100]  # Limit to recent 100

            data = [{
                'id': str(e.id),
                'clause_version_id': str(e.clause_version.id),
                'event_type': e.event_type,
                'outcome_score': e.outcome_score,
                'description': e.description,
                'jurisdiction': e.jurisdiction,
                'created_at': e.created_at
            } for e in events]

            return Response({'total': len(data), 'events': data})

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _update_health_metrics(self, clause):
        """Helper to update health metrics after new event"""
        try:
            versions = ClauseVersion.objects.filter(clause=clause)
            if not versions.exists():
                return

            latest_version = versions.first()
            events = ClauseEvent.objects.filter(clause_version=latest_version)

            scorer = get_health_scorer()
            metrics_data = scorer.compute_health(list(events), usage_count=events.count())

            # Update or create metrics
            metrics, created = ClauseHealthMetrics.objects.get_or_create(
                clause=clause,
                defaults=metrics_data
            )

            if not created:
                for key, value in metrics_data.items():
                    setattr(metrics, key, value)
                metrics.status = scorer.determine_status(metrics_data['health_score'])
                metrics.save()

        except Exception as e:
            print(f"[ERROR] Failed to update health metrics: {e}")


class ClauseSimilarityView(APIView):
    """
    Find similar clauses using RAG
    POST /api/clauses/similar/
    """

    def post(self, request):
        try:
            query_text = request.data.get('text', '')
            top_k = request.data.get('top_k', 5)

            if not query_text:
                return Response(
                    {'error': 'text parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Build RAG from all clauses
            clauses = Clause.objects.filter(extracted_text__isnull=False).exclude(extracted_text='')
            rag = build_rag_from_queryset(clauses)

            # Find similar clauses
            similar = rag.find_similar_clauses(query_text, top_k=top_k)

            return Response({
                'query': query_text[:100],
                'top_k': top_k,
                'results': similar
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
