"""
URL Configuration for Bid Actions API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DepartmentViewSet,
    ActionItemViewSet,
    TenderActionsViewSet,
    PortfolioViewSet
)

app_name = 'bid_actions'

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'actions', ActionItemViewSet, basename='action')
router.register(r'portfolio', PortfolioViewSet, basename='portfolio')

urlpatterns = [
    # Tender-specific action endpoints
    path('tenders/', include([
        path('<uuid:tender_id>/actions/', TenderActionsViewSet.as_view({'get': 'by_tender'}), name='tender-actions'),
        path('<uuid:tender_id>/generate-actions/', TenderActionsViewSet.as_view({'post': 'generate_actions'}), name='generate-actions'),
        path('<uuid:tender_id>/regenerate-actions/', TenderActionsViewSet.as_view({'post': 'regenerate_actions'}), name='regenerate-actions'),
        path('<uuid:tender_id>/dashboard/', TenderActionsViewSet.as_view({'get': 'dashboard'}), name='tender-dashboard'),
        path('<uuid:tender_id>/risk-propagation/', TenderActionsViewSet.as_view({'get': 'risk_propagation'}), name='risk-propagation'),
        path('<uuid:tender_id>/dependency-graph/', TenderActionsViewSet.as_view({'get': 'dependency_graph'}), name='dependency-graph'),
        path('<uuid:tender_id>/critical-path/', TenderActionsViewSet.as_view({'get': 'critical_path'}), name='critical-path'),
    ])),

    # Router URLs
    path('', include(router.urls)),
]
