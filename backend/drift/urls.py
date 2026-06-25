"""
URL Configuration for Drift Detection API endpoints.
"""
from django.urls import path
from .views import (
    DriftDetectionAPIView,
    DriftAnalysisAPIView,
    DriftListAPIView,
    DriftDetailAPIView,
    DriftUpdateStatusAPIView,
    DriftAlertsAPIView,
    DriftAlertMarkReadAPIView,
    DriftBatchDetectionAPIView,
    DriftDashboardAPIView
)

app_name = 'drift'

urlpatterns = [
    # Main drift detection endpoint
    path('detect/', DriftDetectionAPIView.as_view(), name='detect'),

    # Drift analysis and patterns
    path('analysis/', DriftAnalysisAPIView.as_view(), name='analysis'),

    # Drift listing and filtering
    path('list/', DriftListAPIView.as_view(), name='list'),

    # Drift detail
    path('<int:drift_id>/', DriftDetailAPIView.as_view(), name='detail'),

    # Update drift status
    path('<int:drift_id>/status/', DriftUpdateStatusAPIView.as_view(), name='update_status'),

    # Alerts
    path('alerts/', DriftAlertsAPIView.as_view(), name='alerts'),
    path('alerts/<int:alert_id>/read/', DriftAlertMarkReadAPIView.as_view(), name='mark_alert_read'),

    # Batch processing
    path('batch-detect/', DriftBatchDetectionAPIView.as_view(), name='batch_detect'),

    # Dashboard
    path('dashboard/', DriftDashboardAPIView.as_view(), name='dashboard'),
]
