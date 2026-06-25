"""
Buyer Bid Evaluation Dashboard Views
Endpoints for competitive positioning, winner recommendation, collusion, etc.
"""
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Tender, Vendor, VendorBid, VendorClause
from .buyer_engines import (
    compute_competitive_metrics,
    get_vendor_evolution,
    recommend_winner,
    detect_price_collusion,
    detect_clause_collusion,
    build_comparison_grid,
    compute_legal_risk,
    seed_mock_bids,
)


# ─────────────────────────────────────────────────────────────────────────────
# VENDOR CRUD
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def vendor_list_create(request):
    """List all vendors or create a new one."""
    if request.method == 'GET':
        vendors = Vendor.objects.all().values(
            'id', 'name', 'registration_number',
            'financial_rating', 'past_performance_score', 'created_at'
        )
        return Response(list(vendors))

    data = request.data
    vendor = Vendor.objects.create(
        name=data['name'],
        registration_number=data.get('registration_number', ''),
        financial_rating=float(data.get('financial_rating', 0.5)),
        past_performance_score=float(data.get('past_performance_score', 0.5)),
    )
    return Response({
        'id': vendor.id, 'name': vendor.name,
        'financial_rating': vendor.financial_rating,
        'past_performance_score': vendor.past_performance_score,
    }, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────────────────────────
# VENDOR BID CRUD
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def vendor_bid_list_create(request, tender_id):
    """List bids for a tender, or submit a new vendor bid."""
    try:
        tender = Tender.objects.get(id=tender_id)
    except Tender.DoesNotExist:
        return Response({'error': 'Tender not found'}, status=404)

    if request.method == 'GET':
        bids = (VendorBid.objects
                .filter(tender=tender)
                .select_related('vendor')
                .values(
                    'id', 'vendor__id', 'vendor__name',
                    'round_number', 'total_price',
                    'technical_score', 'commercial_score',
                    'legal_risk_score', 'delay_probability',
                    'deviation_score', 'submitted_at', 'notes',
                ))
        return Response(list(bids))

    data = request.data
    try:
        vendor = Vendor.objects.get(id=data['vendor_id'])
    except Vendor.DoesNotExist:
        return Response({'error': 'Vendor not found'}, status=404)

    bid, created = VendorBid.objects.get_or_create(
        tender=tender,
        vendor=vendor,
        round_number=int(data.get('round_number', 1)),
        defaults={
            'total_price'      : float(data['total_price']),
            'technical_score'  : float(data.get('technical_score', 0)),
            'commercial_score' : float(data.get('commercial_score', 0)),
            'legal_risk_score' : float(data.get('legal_risk_score', 0)),
            'delay_probability': float(data.get('delay_probability', 0)),
            'deviation_score'  : float(data.get('deviation_score', 0)),
            'notes'            : data.get('notes', ''),
        }
    )
    if not created:
        # Update existing
        for field in ['total_price', 'technical_score', 'commercial_score',
                      'legal_risk_score', 'delay_probability', 'deviation_score', 'notes']:
            if field in data:
                setattr(bid, field, float(data[field]) if field != 'notes' else data[field])
        bid.save()

    return Response({'id': bid.id, 'created': created}, status=201 if created else 200)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def vendor_bid_delete(request, tender_id, bid_id):
    try:
        bid = VendorBid.objects.get(id=bid_id, tender_id=tender_id)
        bid.delete()
        return Response({'deleted': True})
    except VendorBid.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN DASHBOARD ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buyer_dashboard(request, tender_id):
    """
    Aggregated dashboard: competitive positioning + bid evolution.
    """
    try:
        tender = Tender.objects.get(id=tender_id)
    except Tender.DoesNotExist:
        return Response({'error': 'Tender not found'}, status=404)

    competitive = compute_competitive_metrics(tender_id)
    evolution   = get_vendor_evolution(tender_id)

    # Summary stats
    bids = VendorBid.objects.filter(tender_id=tender_id)
    vendor_count = bids.values('vendor').distinct().count()
    round_count  = bids.values('round_number').distinct().count()

    return Response({
        'tender_id'             : tender_id,
        'tender_title'          : tender.title,
        'tender_reference'      : tender.reference_number,
        'vendor_count'          : vendor_count,
        'round_count'           : round_count,
        'bid_count'             : bids.count(),
        'competitive_positioning': competitive,
        'bid_evolution'         : evolution,
    })


# ─────────────────────────────────────────────────────────────────────────────
# WINNER RECOMMENDATION
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def winner_recommendation(request, tender_id):
    ranking = recommend_winner(tender_id)
    return Response({
        'tender_id': tender_id,
        'ranking'  : ranking,
        'weights'  : {
            'technical'   : '25%',
            'commercial'  : '20%',
            'price'       : '15% (lowest = best)',
            'legal_risk'  : '-15% (higher risk = lower score)',
            'financial'   : '10%',
            'performance' : '10%',
            'delay'       : '-5% (higher delay prob = lower score)',
        },
    })


# ─────────────────────────────────────────────────────────────────────────────
# COLLUSION DETECTION
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def collusion_detection(request, tender_id):
    price_threshold  = float(request.query_params.get('price_threshold',  0.97))
    clause_threshold = float(request.query_params.get('clause_threshold', 0.90))

    price_alerts  = detect_price_collusion(tender_id,  threshold=price_threshold)
    clause_alerts = detect_clause_collusion(tender_id, threshold=clause_threshold)

    total_alerts = len(price_alerts) + len(clause_alerts)
    overall_risk = 'CRITICAL' if total_alerts >= 3 else 'HIGH' if total_alerts >= 1 else 'LOW'

    return Response({
        'tender_id'      : tender_id,
        'overall_risk'   : overall_risk,
        'total_alerts'   : total_alerts,
        'price_collusion' : price_alerts,
        'clause_collusion': clause_alerts,
        'thresholds'     : {
            'price_similarity' : price_threshold,
            'clause_similarity': clause_threshold,
        },
    })


# ─────────────────────────────────────────────────────────────────────────────
# LEGAL COMPARISON GRID / HEATMAP
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def legal_comparison_grid(request, tender_id):
    grid = build_comparison_grid(tender_id)
    return Response({
        'tender_id'       : tender_id,
        'comparison_grid' : grid,
    })


# ─────────────────────────────────────────────────────────────────────────────
# MOCK DATA SEEDER (dev/demo helper)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def seed_demo_data(request, tender_id):
    """Seed realistic mock vendor bids for demo/testing."""
    try:
        Tender.objects.get(id=tender_id)
    except Tender.DoesNotExist:
        return Response({'error': 'Tender not found'}, status=404)

    num_vendors = int(request.data.get('num_vendors', 6))
    num_rounds  = int(request.data.get('num_rounds', 3))
    result = seed_mock_bids(tender_id, num_vendors=num_vendors, num_rounds=num_rounds)
    return Response({'seeded': result, 'message': 'Mock data created successfully'})


# ─────────────────────────────────────────────────────────────────────────────
# VENDOR CLAUSE SUBMIT
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_vendor_clause(request, tender_id, bid_id):
    """Add a clause deviation entry for a specific bid."""
    try:
        bid = VendorBid.objects.get(id=bid_id, tender_id=tender_id)
    except VendorBid.DoesNotExist:
        return Response({'error': 'Bid not found'}, status=404)

    data = request.data
    clause, created = VendorClause.objects.get_or_create(
        vendor_bid=bid,
        clause_type=data.get('clause_type', 'OTHER'),
        defaults={
            'clause_text'    : data.get('clause_text', ''),
            'deviation_score': float(data.get('deviation_score', 0)),
            'risk_score'     : float(data.get('risk_score', 0)),
        }
    )

    # Recompute legal risk for this bid
    compute_legal_risk(bid.id)

    return Response({'id': clause.id, 'created': created}, status=201 if created else 200)
