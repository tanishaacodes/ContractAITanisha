"""
URL routing for SAP integration endpoints
"""
from django.urls import path
from . import views

app_name = 'sap'

urlpatterns = [
    # Health check
    path('health/', views.sap_health_check, name='health'),

    # Contract listing & sync (static paths first)
    path('contracts/', views.get_contracts, name='get_contracts'),
    path('contracts/sync/', views.sync_contracts, name='sync_contracts'),

    # Batch processing — MUST be before <str:contract_id> wildcard
    path('contracts/batch-process/', views.batch_process_contracts, name='batch_process'),

    # Parameterised routes — scenarios and detail
    path('contracts/<str:contract_id>/process/', views.process_new_contract, name='process_contract'),
    path('contracts/<str:contract_id>/block-if-high-risk/', views.block_high_risk, name='block_high_risk'),
    path('contracts/<str:contract_id>/amendment/', views.process_amendment, name='amendment'),
    path('contracts/<str:contract_id>/override/', views.process_manual_override, name='override'),
    path('contracts/<str:contract_id>/suggestions/', views.add_clause_suggestions, name='suggestions'),
    path('contracts/<str:contract_id>/risk/', views.get_contract_risk_analysis, name='contract_risk'),
    path('contracts/<str:contract_id>/', views.get_contract_detail, name='contract_detail'),
]
