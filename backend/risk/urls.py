"""
Risk API URL Configuration
"""
from django.urls import path
from . import views
from . import health
from . import audit

urlpatterns = [
    # Contract risk analysis (sync)
    path('contracts/<str:contract_id>/analyze', views.analyze_contract_risk, name='analyze_contract_risk'),
    path('contracts/<str:contract_id>', views.get_contract_risk, name='get_contract_risk'),
    path('contracts/<str:contract_id>/correlations', views.get_contract_correlations, name='get_contract_correlations'),
    path('contracts/<str:contract_id>/detect-correlations', views.detect_correlations, name='detect_correlations'),

    # Contract risk analysis (async)
    path('contracts/<str:contract_id>/analyze-async', views.analyze_contract_async, name='analyze_contract_async'),
    path('contracts/<str:contract_id>/explain', views.explain_contract_risk, name='explain_contract_risk'),

    # Batch processing
    path('batch-analyze', views.batch_analyze_contracts, name='batch_analyze_contracts'),
    path('jobs/<str:job_id>/status', views.get_job_status, name='get_job_status'),

    # Vendor exposure
    path('vendors/<str:vendor_name>/exposure', views.get_vendor_exposure, name='get_vendor_exposure'),
    path('vendors/<str:vendor_name>/refresh', views.refresh_vendor_exposure, name='refresh_vendor_exposure'),
    path('vendors/top-exposure', views.get_top_vendors_by_exposure, name='get_top_vendors_by_exposure'),

    # Dashboard data
    path('heatmap/regional', views.get_regional_heatmap, name='get_regional_heatmap'),
    path('network', views.get_risk_network, name='get_risk_network'),
    path('portfolio/overview', views.get_portfolio_overview, name='get_portfolio_overview'),
    path('portfolio/refresh', views.refresh_portfolio_metrics, name='refresh_portfolio_metrics'),

    # Advanced analytics
    path('scenario-simulation', views.run_scenario_simulation, name='run_scenario_simulation'),
    path('systemic-risks', views.detect_systemic_risks, name='detect_systemic_risks'),

    # Health checks
    path('health', health.health_check, name='health_check'),
    path('health/detailed', health.health_check_detailed, name='health_check_detailed'),
    path('health/ready', health.readiness_check, name='readiness_check'),
    path('health/live', health.liveness_check, name='liveness_check'),

    # Audit logs (admin only)
    path('audit/logs', audit.get_audit_logs, name='get_audit_logs'),
    path('audit/stats', audit.get_audit_stats, name='get_audit_stats'),
    path('audit/clear', audit.clear_audit_cache, name='clear_audit_cache'),
]
