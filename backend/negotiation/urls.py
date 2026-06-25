"""
URL routing for Negotiation Intelligence API
"""
from django.urls import path
from . import views

urlpatterns = [
    # Prediction endpoints
    path('predict', views.NegotiationPredictionAPI.as_view(), name='negotiation_predict'),
    path('predict-multiple', views.MultiClausePredictionAPI.as_view(), name='negotiation_predict_multiple'),

    # Counterparty endpoints
    path('counterparties', views.CounterpartyListAPI.as_view(), name='counterparty_list'),
    path('counterparty/<str:counterparty_id>/behavior', views.CounterpartyBehaviorAPI.as_view(), name='counterparty_behavior'),

    # Simulation endpoints
    path('simulate', views.NegotiationSimulationAPI.as_view(), name='negotiation_simulate'),
    path('simulate/<str:contract_id>/<str:counterparty_id>', views.NegotiationSimulationAPI.as_view(), name='negotiation_simulate_get'),

    # Silent risk endpoints
    path('silent-risk/<str:contract_id>', views.SilentRiskDetectionAPI.as_view(), name='silent_risk_detect'),
    path('silent-risk/<str:contract_id>/heatmap', views.SilentRiskHeatmapAPI.as_view(), name='silent_risk_heatmap'),
    path('silent-risk/explain', views.SilentRiskExplainAPI.as_view(), name='silent_risk_explain'),

    # Exculpatory clause analysis endpoints (order matters - specific before generic)
    path('exculpatory/analyze', views.ExculpatoryAnalysisAPI.as_view(), name='exculpatory_analysis_post'),
    path('exculpatory/<str:contract_id>', views.ExculpatoryAnalysisAPI.as_view(), name='exculpatory_analysis_get'),
]
