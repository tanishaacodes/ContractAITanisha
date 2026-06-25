"""
URL Configuration for Tender Intelligence API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenderViewSet, CompanyProfileViewSet
from . import bid_management_views as bv
from . import buyer_views as buyer

router = DefaultRouter()
router.register(r'tenders', TenderViewSet, basename='tender')
router.register(r'company-profile', CompanyProfileViewSet, basename='company-profile')

# ── Bid Management routes ─────────────────────────────────────────────────────
bid_urlpatterns = [
    # Per-tender endpoints
    path('tenders/<int:tender_id>/bid/generate-actions/',
         bv.generate_actions,       name='bid-generate-actions'),
    path('tenders/<int:tender_id>/bid/actions/',
         bv.list_actions,           name='bid-list-actions'),
    path('tenders/<int:tender_id>/bid/actions/<int:item_id>/',
         bv.update_action,          name='bid-update-action'),
    path('tenders/<int:tender_id>/bid/readiness/',
         bv.get_readiness,          name='bid-readiness'),
    path('tenders/<int:tender_id>/bid/propagate-risk/',
         bv.run_propagation,        name='bid-propagate-risk'),
    path('tenders/<int:tender_id>/bid/risk-cascade/',
         bv.get_risk_cascade,       name='bid-risk-cascade'),
    path('tenders/<int:tender_id>/bid/dependency-graph/',
         bv.dependency_graph,       name='bid-dependency-graph'),
    path('tenders/<int:tender_id>/bid/dashboard/',
         bv.executive_dashboard,    name='bid-dashboard'),
    path('tenders/<int:tender_id>/bid/readiness-trend/',
         bv.readiness_trend,        name='bid-readiness-trend'),
    path('tenders/<int:tender_id>/bid/snapshot-readiness/',
         bv.save_readiness_snapshot, name='bid-snapshot-readiness'),

    # Cross-tender / global
    path('tenders/bid/portfolio/',
         bv.portfolio_dashboard,    name='bid-portfolio'),
    path('tenders/bid/departments/',
         bv.list_departments,       name='bid-departments'),

    # New endpoints - Delay Prediction
    path('tenders/<int:tender_id>/bid/predict-delays/',
         bv.predict_delays,         name='bid-predict-delays'),

    # Win Probability
    path('tenders/<int:tender_id>/bid/win-probability/',
         bv.calculate_win_probability, name='bid-win-probability'),

    # BOQ Comparison
    path('tenders/<int:tender_id>/bid/boq-comparison/',
         bv.compare_boq,            name='bid-boq-comparison'),
    path('tenders/<int:tender_id>/bid/boq-auto-populate/',
         bv.auto_populate_boq,      name='bid-boq-auto-populate'),
    path('tenders/<int:tender_id>/bid/boq-recalculate/',
         bv.recalculate_boq_gaps,   name='bid-boq-recalculate'),

    # Analytics & Heatmap
    path('tenders/<int:tender_id>/bid/heatmap/',
         bv.get_heatmap,            name='bid-heatmap'),
    path('tenders/<int:tender_id>/bid/analytics/',
         bv.get_analytics,          name='bid-analytics'),
]

buyer_urlpatterns = [
    # Vendor CRUD
    path('buyer/vendors/',
         buyer.vendor_list_create,          name='buyer-vendors'),

    # Bids per tender
    path('tenders/<int:tender_id>/buyer/bids/',
         buyer.vendor_bid_list_create,      name='buyer-bid-list'),
    path('tenders/<int:tender_id>/buyer/bids/<int:bid_id>/',
         buyer.vendor_bid_delete,           name='buyer-bid-delete'),

    # Clause per bid
    path('tenders/<int:tender_id>/buyer/bids/<int:bid_id>/clauses/',
         buyer.submit_vendor_clause,        name='buyer-clause-submit'),

    # Dashboard
    path('tenders/<int:tender_id>/buyer/dashboard/',
         buyer.buyer_dashboard,             name='buyer-dashboard'),

    # Winner recommendation
    path('tenders/<int:tender_id>/buyer/winner/',
         buyer.winner_recommendation,       name='buyer-winner'),

    # Collusion detection
    path('tenders/<int:tender_id>/buyer/collusion/',
         buyer.collusion_detection,         name='buyer-collusion'),

    # Legal comparison grid / heatmap
    path('tenders/<int:tender_id>/buyer/legal-grid/',
         buyer.legal_comparison_grid,       name='buyer-legal-grid'),

    # Demo data seeder
    path('tenders/<int:tender_id>/buyer/seed-demo/',
         buyer.seed_demo_data,              name='buyer-seed-demo'),
]

urlpatterns = [
    path('', include(router.urls)),
    *bid_urlpatterns,
    *buyer_urlpatterns,
]
