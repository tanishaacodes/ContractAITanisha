"""
URL routing for Infor ERP integration endpoints
"""
from django.urls import path
from . import views

app_name = 'infor'

urlpatterns = [
    # Health check
    path('health/', views.infor_health_check, name='health'),

    # Contract listing & sync
    path('contracts/', views.get_contracts, name='get_contracts'),
    path('contracts/sync/', views.sync_contracts, name='sync_contracts'),
    path('contracts/batch-process/', views.batch_process_contracts, name='batch_process'),

    # Contract detail & risk analysis
    path('contracts/<str:contract_id>/risk/', views.get_contract_risk_analysis, name='contract_risk'),
    path('contracts/<str:contract_id>/', views.get_contract_detail, name='contract_detail'),

    # Scenario 1: Process new contract
    path('contracts/<str:contract_id>/process/', views.process_new_contract, name='process_contract'),

    # Scenario 2: Block high-risk
    path('contracts/<str:contract_id>/block-if-high-risk/', views.block_high_risk, name='block_high_risk'),

    # Scenario 3: Amendment re-evaluation
    path('contracts/<str:contract_id>/amendment/', views.process_amendment, name='amendment'),

    # Scenario 4: Manual override
    path('contracts/<str:contract_id>/override/', views.process_manual_override, name='override'),

    # Scenario 5: AI clause suggestions
    path('contracts/<str:contract_id>/suggestions/', views.add_clause_suggestions, name='suggestions'),
]
