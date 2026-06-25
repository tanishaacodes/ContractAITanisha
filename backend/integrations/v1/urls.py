"""
URL routing for PrimeContractAI Unified ERP Integration API v1
"""
from django.urls import path
from . import views

app_name = 'v1'

urlpatterns = [
    # Health
    path('health/', views.v1_health, name='health'),

    # Contract lifecycle
    path('contracts/ingest/', views.ingest_contract, name='ingest'),
    path('contracts/<str:contract_id>/status/', views.contract_status, name='status'),
    path('contracts/<str:contract_id>/decision/', views.apply_decision, name='decision'),

    # Event webhooks
    path('events/amendment/', views.amendment_event, name='amendment'),
]
