"""
API Views for Bid Actions Management
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q

from apps.tenders.models import Tender
from .models import Department, ActionItem, RiskPropagation, DepartmentActionSummary
from .serializers import (
    DepartmentSerializer,
    ActionItemListSerializer,
    ActionItemDetailSerializer,
    RiskPropagationSerializer,
    DepartmentSummarySerializer,
    ActionItemStatusUpdateSerializer
)
from .services.action_generator import generate_actions_from_tender, regenerate_all_actions
from .services.risk_engine import (
    propagate_department_risks,
    create_risk_propagation_edges,
    calculate_action_delay_impact,
    get_critical_path_actions
)
from .services.readiness_calculator import (
    calculate_bid_readiness,
    calculate_department_summaries,
    update_cached_summaries,
    get_portfolio_readiness
)


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for departments
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def keywords(self, request):
        """Get department classification keywords"""
        from .services.department_classifier import get_department_keywords
        keywords = get_department_keywords()
        return Response(keywords)


class ActionItemViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for action items
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['list', 'by_tender']:
            return ActionItemListSerializer
        return ActionItemDetailSerializer

    def get_queryset(self):
        queryset = ActionItem.objects.select_related('department', 'tender')

        # Filter by tender
        tender_id = self.request.query_params.get('tender_id')
        if tender_id:
            queryset = queryset.filter(tender_id=tender_id)

        # Filter by department
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department__name=department)

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset

    @action(detail=False, methods=['get'], url_path='by-tender/(?P<tender_id>[^/.]+)')
    def by_tender(self, request, tender_id=None):
        """Get all action items for a specific tender"""
        actions = self.get_queryset().filter(tender_id=tender_id)
        serializer = self.get_serializer(actions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update status of a single action item"""
        action = self.get_object()
        new_status = request.data.get('status')

        if new_status not in dict(ActionItem.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        action.status = new_status
        action.save()

        serializer = self.get_serializer(action)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_update_status(self, request):
        """Update status for multiple action items"""
        serializer = ActionItemStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action_ids = serializer.validated_data['action_ids']
        new_status = serializer.validated_data['status']

        updated = ActionItem.objects.filter(id__in=action_ids).update(status=new_status)

        return Response({
            'updated': updated,
            'status': new_status
        })

    @action(detail=True, methods=['get'])
    def delay_prediction(self, request, pk=None):
        """Get delay prediction for an action item"""
        action = self.get_object()
        delay_days = calculate_action_delay_impact(action)

        return Response({
            'action_id': str(action.id),
            'predicted_delay_days': delay_days,
            'risk_score': action.risk_score,
            'complexity_score': action.complexity_score,
            'dependency_count': action.depends_on.count()
        })


class TenderActionsViewSet(viewsets.ViewSet):
    """
    Tender-specific action management endpoints
    """
    permission_classes = [IsAuthenticated]

    def get_tender(self, tender_id):
        """Helper to get tender"""
        return get_object_or_404(Tender, id=tender_id)

    @action(detail=False, methods=['post'], url_path='(?P<tender_id>[^/.]+)/generate')
    def generate_actions(self, request, tender_id=None):
        """Generate action items for a tender"""
        tender = self.get_tender(tender_id)

        actions = generate_actions_from_tender(tender)

        return Response({
            'tender_id': str(tender.id),
            'actions_created': len(actions),
            'message': f'Generated {len(actions)} action items'
        })

    @action(detail=False, methods=['post'], url_path='(?P<tender_id>[^/.]+)/regenerate')
    def regenerate_actions(self, request, tender_id=None):
        """Delete and regenerate all action items"""
        tender = self.get_tender(tender_id)

        count = regenerate_all_actions(tender)

        return Response({
            'tender_id': str(tender.id),
            'actions_created': count,
            'message': f'Regenerated {count} action items'
        })

    @action(detail=False, methods=['get'], url_path='(?P<tender_id>[^/.]+)/dashboard')
    def dashboard(self, request, tender_id=None):
        """Get comprehensive dashboard data for tender"""
        tender = self.get_tender(tender_id)

        # Readiness metrics
        readiness = calculate_bid_readiness(tender)

        # Department summaries
        dept_summaries = calculate_department_summaries(tender)

        # Actions summary
        actions = ActionItem.objects.filter(tender=tender)
        total_actions = actions.count()
        completed = actions.filter(status='Completed').count()
        critical_pending = actions.filter(
            priority='Critical',
            status__in=['Pending', 'In Progress', 'Blocked']
        ).count()

        # Total exposure
        from django.db.models import Sum
        total_exposure = actions.aggregate(Sum('financial_exposure'))['financial_exposure__sum'] or 0

        return Response({
            'tender_id': str(tender.id),
            'tender_title': tender.title,
            'readiness': readiness,
            'department_summaries': dept_summaries,
            'total_actions': total_actions,
            'completed_actions': completed,
            'critical_pending': critical_pending,
            'total_financial_exposure': float(total_exposure)
        })

    @action(detail=False, methods=['get'], url_path='(?P<tender_id>[^/.]+)/risk-propagation')
    def risk_propagation(self, request, tender_id=None):
        """Calculate risk propagation across departments"""
        tender = self.get_tender(tender_id)

        # Calculate propagated risks
        propagated_risks = propagate_department_risks(str(tender.id))

        # Create edges
        edges_created = create_risk_propagation_edges(str(tender.id))

        return Response({
            'tender_id': str(tender.id),
            'propagated_risks': propagated_risks,
            'risk_edges_created': edges_created
        })

    @action(detail=False, methods=['get'], url_path='(?P<tender_id>[^/.]+)/dependency-graph')
    def dependency_graph(self, request, tender_id=None):
        """Get dependency graph data for visualization"""
        tender = self.get_tender(tender_id)

        actions = ActionItem.objects.filter(tender=tender).select_related('department').prefetch_related('depends_on')

        nodes = []
        edges = []

        for action in actions:
            nodes.append({
                'id': str(action.id),
                'label': action.title[:40],
                'department': action.department.name,
                'risk_score': action.risk_score,
                'complexity_score': action.complexity_score,
                'status': action.status,
                'priority': action.priority
            })

            # Add dependency edges
            for dep in action.depends_on.all():
                edges.append({
                    'from': str(dep.id),
                    'to': str(action.id),
                    'type': 'dependency'
                })

        # Add risk propagation edges
        risk_edges = RiskPropagation.objects.filter(
            source_action__tender=tender
        ).select_related('source_action', 'target_action')

        for edge in risk_edges:
            edges.append({
                'from': str(edge.source_action.id),
                'to': str(edge.target_action.id),
                'type': 'risk_propagation',
                'weight': edge.propagation_weight
            })

        return Response({
            'nodes': nodes,
            'edges': edges
        })

    @action(detail=False, methods=['get'], url_path='(?P<tender_id>[^/.]+)/critical-path')
    def critical_path(self, request, tender_id=None):
        """Get actions on critical path"""
        tender = self.get_tender(tender_id)

        critical_actions = get_critical_path_actions(str(tender.id))

        serializer = ActionItemListSerializer(critical_actions, many=True)

        return Response({
            'tender_id': str(tender.id),
            'critical_path_count': len(critical_actions),
            'actions': serializer.data
        })


class PortfolioViewSet(viewsets.ViewSet):
    """
    Portfolio-wide analytics across multiple tenders
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get portfolio-wide dashboard"""
        tenders = Tender.objects.all()

        portfolio_data = get_portfolio_readiness(list(tenders))

        return Response(portfolio_data)

    @action(detail=False, methods=['get'])
    def department_heatmap(self, request):
        """Get department risk heatmap across portfolio"""
        from django.db.models import Avg, Count

        heatmap = ActionItem.objects.values(
            'department__name',
            'department__color_hex'
        ).annotate(
            avg_risk=Avg('risk_score'),
            total_actions=Count('id'),
            critical_count=Count('id', filter=Q(priority='Critical'))
        ).order_by('-avg_risk')

        return Response(list(heatmap))
