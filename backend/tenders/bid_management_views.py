"""
Bid Management API Views
========================
Endpoints:
  POST   /api/tenders/{id}/bid/generate-actions/       → generate action items
  GET    /api/tenders/{id}/bid/actions/                 → list action items
  PATCH  /api/tenders/{id}/bid/actions/{item_id}/       → update action status
  GET    /api/tenders/{id}/bid/readiness/               → readiness index + steps
  POST   /api/tenders/{id}/bid/propagate-risk/          → run DFS cascade + persist
  GET    /api/tenders/{id}/bid/risk-cascade/            → get stored propagation results
  GET    /api/tenders/{id}/bid/dependency-graph/        → get nodes + edges
  GET    /api/tenders/{id}/bid/dashboard/               → executive dashboard summary
  GET    /api/tenders/bid/portfolio/                    → cross-tender portfolio stats
  GET    /api/tenders/{id}/bid/readiness-trend/         → historical snapshots
  POST   /api/tenders/{id}/bid/snapshot-readiness/      → manually save snapshot
"""

import logging

from django.db.models import Avg, Count, Sum, Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as http_status

from tenders.models import (
    Tender, BidActionItem, BidDepartment,
    BidDepartmentRiskPropagation, BidReadinessSnapshot,
)
from tenders.services.action_generator import generate_action_items, seed_departments
from tenders.services.propagation_engine import propagate_and_store, get_dependency_graph
from tenders.services.readiness_engine import (
    calculate_readiness, snapshot_readiness, get_readiness_trend,
)

logger = logging.getLogger(__name__)


def _get_tender(tender_id, user):
    """Helper: fetch tender owned by requesting user."""
    return get_object_or_404(Tender, id=tender_id, uploaded_by=user)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Generate Action Items
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_actions(request, tender_id):
    """
    POST /api/tenders/{id}/bid/generate-actions/
    Body (optional): { "regenerate": true }
    Generates BidActionItem rows from existing tender data.
    """
    tender     = _get_tender(tender_id, request.user)
    regenerate = request.data.get('regenerate', False)

    try:
        seed_departments()
        count = generate_action_items(tender, regenerate=regenerate)
        return Response({
            'message': f'Generated {count} action items',
            'count':   count,
        })
    except Exception as e:
        logger.exception(f"[BidMgmt] Action generation failed for tender {tender_id}")
        return Response(
            {'error': str(e)},
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ─────────────────────────────────────────────────────────────────────────────
# 2. List Action Items
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_actions(request, tender_id):
    """
    GET /api/tenders/{id}/bid/actions/
    Query params: department, priority, status, search
    """
    tender = _get_tender(tender_id, request.user)
    qs     = BidActionItem.objects.filter(tender=tender).select_related('department')

    dept     = request.query_params.get('department')
    priority = request.query_params.get('priority')
    stat     = request.query_params.get('status')
    search   = request.query_params.get('search')

    if dept:
        qs = qs.filter(department__name=dept)
    if priority:
        qs = qs.filter(priority=priority)
    if stat:
        qs = qs.filter(status=stat)
    if search:
        qs = qs.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    data = [
        {
            'id':                 item.id,
            'department':         item.department.name if item.department else 'Unknown',
            'source_type':        item.source_type,
            'source_ref':         item.source_ref,
            'title':              item.title,
            'description':        item.description,
            'priority':           item.priority,
            'status':             item.status,
            'risk_score':         item.risk_score,
            'complexity_score':   item.complexity_score,
            'financial_exposure': float(item.financial_exposure),
            'ai_generated':       item.ai_generated,
            'created_at':         item.created_at.isoformat(),
            'updated_at':         item.updated_at.isoformat(),
        }
        for item in qs
    ]

    # Summary counts
    summary = qs.values('status').annotate(count=Count('id'))

    return Response({
        'count':   len(data),
        'items':   data,
        'summary': {row['status']: row['count'] for row in summary},
    })


# ─────────────────────────────────────────────────────────────────────────────
# 3. Update Action Item Status
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_action(request, tender_id, item_id):
    """
    PATCH /api/tenders/{id}/bid/actions/{item_id}/
    Body: { "status": "Completed" }  (or priority, due_date)
    """
    tender = _get_tender(tender_id, request.user)
    item   = get_object_or_404(BidActionItem, id=item_id, tender=tender)

    allowed_fields = {'status', 'priority', 'due_date', 'description'}
    for field in allowed_fields:
        if field in request.data:
            setattr(item, field, request.data[field])
    item.save()

    return Response({
        'id':       item.id,
        'status':   item.status,
        'priority': item.priority,
        'message':  'Updated',
    })


# ─────────────────────────────────────────────────────────────────────────────
# 4. Bid Readiness Index
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_readiness(request, tender_id):
    """GET /api/tenders/{id}/bid/readiness/"""
    tender = _get_tender(tender_id, request.user)
    report = calculate_readiness(tender)
    # Convert Decimal to float for JSON
    report['total_exposure'] = float(report['total_exposure'])
    return Response(report)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Run Risk Propagation
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_propagation(request, tender_id):
    """POST /api/tenders/{id}/bid/propagate-risk/"""
    tender = _get_tender(tender_id, request.user)

    if not BidActionItem.objects.filter(tender=tender).exists():
        return Response(
            {'error': 'No action items found. Run generate-actions first.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    results = propagate_and_store(tender)
    return Response({
        'message':      f'Propagation complete: {len(results)} departments',
        'departments':  results,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 6. Get Stored Risk Cascade Results
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_risk_cascade(request, tender_id):
    """GET /api/tenders/{id}/bid/risk-cascade/"""
    tender = _get_tender(tender_id, request.user)
    rows   = BidDepartmentRiskPropagation.objects.filter(tender=tender)

    data = [
        {
            'department':          r.department_name,
            'base_risk':           r.base_risk,
            'propagated_risk':     r.propagated_risk,
            'amplification':       r.amplification,
            'predicted_delay_days': r.predicted_delay_days,
            'task_count':          r.task_count,
            'computed_at':         r.computed_at.isoformat(),
        }
        for r in rows
    ]
    return Response({'departments': data, 'count': len(data)})


# ─────────────────────────────────────────────────────────────────────────────
# 7. Dependency Graph
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dependency_graph(request, tender_id):
    """GET /api/tenders/{id}/bid/dependency-graph/"""
    tender = _get_tender(tender_id, request.user)
    graph  = get_dependency_graph(tender)
    return Response(graph)


# ─────────────────────────────────────────────────────────────────────────────
# 8. Executive Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def executive_dashboard(request, tender_id):
    """
    GET /api/tenders/{id}/bid/dashboard/
    Full summary: readiness + dept breakdown + risk cascade + KPIs
    """
    tender = _get_tender(tender_id, request.user)

    # Readiness
    readiness = calculate_readiness(tender)
    readiness['total_exposure'] = float(readiness['total_exposure'])

    # Department breakdown
    dept_summary = list(
        BidActionItem.objects
        .filter(tender=tender)
        .values('department__name')
        .annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='Completed')),
            avg_risk=Avg('risk_score'),
            exposure=Sum('financial_exposure'),
        )
        .order_by('-avg_risk')
    )
    for row in dept_summary:
        row['exposure']  = float(row['exposure'] or 0)
        row['avg_risk']  = round(row['avg_risk'] or 0, 4)
        row['completion_pct'] = (
            round(row['completed'] / row['total'] * 100, 1)
            if row['total'] > 0 else 0
        )

    # Risk cascade (already stored or empty)
    cascade_rows = BidDepartmentRiskPropagation.objects.filter(tender=tender)
    cascade = [
        {
            'department':          r.department_name,
            'base_risk':           r.base_risk,
            'propagated_risk':     r.propagated_risk,
            'amplification':       r.amplification,
            'predicted_delay_days': r.predicted_delay_days,
            'task_count':          r.task_count,
        }
        for r in cascade_rows
    ]

    # Status counts
    status_counts = dict(
        BidActionItem.objects
        .filter(tender=tender)
        .values_list('status')
        .annotate(c=Count('id'))
    )

    return Response({
        'tender_id':         tender_id,
        'tender_title':      tender.title,
        'tender_status':     tender.status,
        'estimated_value':   float(tender.estimated_value or 0),
        'readiness':         readiness,
        'department_summary': dept_summary,
        'risk_cascade':      cascade,
        'status_counts':     status_counts,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 9. Portfolio Dashboard (all tenders for user)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def portfolio_dashboard(request):
    """
    GET /api/tenders/bid/portfolio/
    Cross-tender portfolio intelligence for the requesting user.
    """
    tenders = Tender.objects.filter(uploaded_by=request.user)

    portfolio = []
    for t in tenders:
        readiness = calculate_readiness(t)
        dept_risk = (
            BidActionItem.objects
            .filter(tender=t)
            .aggregate(avg=Avg('risk_score'), total_exp=Sum('financial_exposure'))
        )
        portfolio.append({
            'tender_id':        t.id,
            'tender_title':     t.title,
            'reference_number': t.reference_number,
            'status':           t.status,
            'estimated_value':  float(t.estimated_value or 0),
            'readiness_index':  readiness['readiness_index'],
            'total_actions':    readiness['total_actions'],
            'completed_actions': readiness['completed_actions'],
            'critical_pending': readiness['critical_pending'],
            'avg_risk':         round(dept_risk['avg'] or 0, 4),
            'total_exposure':   float(dept_risk['total_exp'] or 0),
        })

    # Portfolio aggregates
    total_value    = sum(p['estimated_value'] for p in portfolio)
    total_exposure = sum(p['total_exposure'] for p in portfolio)
    avg_readiness  = (
        sum(p['readiness_index'] for p in portfolio) / len(portfolio)
        if portfolio else 0
    )
    avg_risk = (
        sum(p['avg_risk'] for p in portfolio) / len(portfolio)
        if portfolio else 0
    )

    return Response({
        'total_tenders':    len(portfolio),
        'total_value':      total_value,
        'total_exposure':   total_exposure,
        'avg_readiness':    round(avg_readiness, 1),
        'avg_risk':         round(avg_risk, 4),
        'tenders':          portfolio,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 10. Readiness Trend
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def readiness_trend(request, tender_id):
    """GET /api/tenders/{id}/bid/readiness-trend/"""
    tender = _get_tender(tender_id, request.user)
    limit  = int(request.query_params.get('limit', 10))
    trend  = get_readiness_trend(tender, limit=limit)
    return Response({'trend': trend})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_readiness_snapshot(request, tender_id):
    """POST /api/tenders/{id}/bid/snapshot-readiness/"""
    tender = _get_tender(tender_id, request.user)
    snap   = snapshot_readiness(tender)
    return Response({
        'message':       'Snapshot saved',
        'readiness_index': snap.readiness_index,
        'created_at':    snap.created_at.isoformat(),
    })


# ─────────────────────────────────────────────────────────────────────────────
# 11. Department List
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_departments(request):
    """GET /api/tenders/bid/departments/"""
    seed_departments()
    depts = BidDepartment.objects.all().values('id', 'name', 'workload_weight')
    return Response({'departments': list(depts)})


# ─────────────────────────────────────────────────────────────────────────────
# 12. Delay Prediction
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def predict_delays(request, tender_id):
    """
    GET /api/tenders/{id}/bid/predict-delays/
    Predict delay days for all departments using ML model
    """
    tender = _get_tender(tender_id, request.user)

    from tenders.services.delay_model import predict_delays_for_tender

    predictions = predict_delays_for_tender(tender.id)

    results = [
        {'department': dept, 'predicted_delay_days': days}
        for dept, days in predictions.items()
    ]

    return Response({
        'tender_id': tender_id,
        'predictions': results,
        'total_predicted_delay': sum(predictions.values()),
    })


# ─────────────────────────────────────────────────────────────────────────────
# 13. Win Probability
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_win_probability(request, tender_id):
    """
    POST /api/tenders/{id}/bid/win-probability/
    Body: { "bid_margin": 12.5, "market_avg_margin": 10.0 }
    """
    tender = _get_tender(tender_id, request.user)

    # Get company profile
    from tenders.models import CompanyProfile
    try:
        company_profile = CompanyProfile.objects.get(user=request.user)
    except CompanyProfile.DoesNotExist:
        return Response(
            {'error': 'Company profile not found. Please complete your profile first.'},
            status=http_status.HTTP_400_BAD_REQUEST
        )

    bid_margin = request.data.get('bid_margin', 15.0)
    market_avg_margin = request.data.get('market_avg_margin', 12.0)

    from tenders.services.win_model import calculate_win_probability_for_tender

    win_prob = calculate_win_probability_for_tender(
        tender=tender,
        company_profile=company_profile,
        bid_margin=float(bid_margin),
        market_avg_margin=float(market_avg_margin),
    )

    return Response({
        'tender_id': tender_id,
        'win_probability': round(win_prob, 4),
        'win_percentage': round(win_prob * 100, 2),
        'bid_margin': bid_margin,
        'market_avg_margin': market_avg_margin,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 14. BOQ Comparison
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def compare_boq(request, tender_id):
    """
    GET /api/tenders/{id}/bid/boq-comparison/
    Full BOQ gap analysis
    """
    tender = _get_tender(tender_id, request.user)

    from tenders.services.boq_comparison import compare_all_boq_items

    comparison = compare_all_boq_items(tender)

    return Response(comparison)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auto_populate_boq(request, tender_id):
    """
    POST /api/tenders/{id}/bid/boq-auto-populate/
    Body: { "margin_percentage": 10.0 }
    """
    tender = _get_tender(tender_id, request.user)
    margin = float(request.data.get('margin_percentage', 10.0))

    from tenders.services.boq_comparison import auto_populate_bid_boq

    count = auto_populate_bid_boq(tender, margin_percentage=margin)

    return Response({
        'message': f'Auto-populated {count} BOQ items',
        'items_created': count,
        'margin_applied': margin,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recalculate_boq_gaps(request, tender_id):
    """
    POST /api/tenders/{id}/bid/boq-recalculate/
    Recalculate all gap percentages
    """
    tender = _get_tender(tender_id, request.user)

    from tenders.services.boq_comparison import recalculate_gaps

    count = recalculate_gaps(tender)

    return Response({
        'message': f'Recalculated gaps for {count} items',
        'items_updated': count,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 15. Heatmap & Analytics
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_heatmap(request, tender_id):
    """
    GET /api/tenders/{id}/bid/heatmap/
    Department × Priority heatmap data
    """
    tender = _get_tender(tender_id, request.user)

    actions = BidActionItem.objects.filter(tender=tender)

    # Build matrix: department × priority
    heatmap = {}
    priorities = ['Low', 'Medium', 'High', 'Critical']
    departments = BidDepartment.objects.all().values_list('name', flat=True)

    for dept in departments:
        heatmap[dept] = {}
        for priority in priorities:
            count = actions.filter(department__name=dept, priority=priority).count()
            heatmap[dept][priority] = count

    return Response({
        'tender_id': tender_id,
        'heatmap': heatmap,
        'departments': list(departments),
        'priorities': priorities,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_analytics(request, tender_id):
    """
    GET /api/tenders/{id}/bid/analytics/
    Advanced analytics: trends, bottlenecks, critical path
    """
    tender = _get_tender(tender_id, request.user)

    actions = BidActionItem.objects.filter(tender=tender)

    # Priority distribution
    priority_dist = dict(
        actions.values_list('priority').annotate(c=Count('id'))
    )

    # Status distribution
    status_dist = dict(
        actions.values_list('status').annotate(c=Count('id'))
    )

    # Department workload
    dept_workload = list(
        actions.values('department__name')
        .annotate(
            count=Count('id'),
            avg_risk=Avg('risk_score'),
            total_exposure=Sum('financial_exposure')
        )
        .order_by('-count')
    )

    # Critical path (simplified: highest risk + blocked status)
    critical_items = list(
        actions.filter(
            Q(priority='Critical') | Q(status='Blocked') | Q(risk_score__gt=0.7)
        )
        .values('id', 'title', 'department__name', 'priority', 'status', 'risk_score')
        [:10]
    )

    return Response({
        'tender_id': tender_id,
        'priority_distribution': priority_dist,
        'status_distribution': status_dist,
        'department_workload': dept_workload,
        'critical_path_items': critical_items,
        'total_actions': actions.count(),
    })
