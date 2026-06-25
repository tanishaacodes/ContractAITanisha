"""
URL Configuration for Counterfactual Engine API endpoints.
"""
from django.urls import path
from .views import (
    CounterfactualSimulateAPIView,
    CounterfactualCompareAPIView,
    CounterfactualHistoryAPIView,
    CounterfactualScenarioDetailAPIView,
    HistoricalOutcomeAPIView
)

app_name = 'counterfactual'

urlpatterns = [
    # Main simulation endpoint
    path('simulate/', CounterfactualSimulateAPIView.as_view(), name='simulate'),

    # Compare multiple scenarios
    path('compare/', CounterfactualCompareAPIView.as_view(), name='compare'),

    # Scenario history
    path('history/', CounterfactualHistoryAPIView.as_view(), name='history'),

    # Scenario detail
    path('scenario/<int:scenario_id>/', CounterfactualScenarioDetailAPIView.as_view(), name='scenario_detail'),

    # Historical outcomes management
    path('outcomes/', HistoricalOutcomeAPIView.as_view(), name='outcomes'),
]
