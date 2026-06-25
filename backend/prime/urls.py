"""
PrimeContractAI - URL Configuration
API endpoints for executive dashboard
"""

from django.urls import path
from . import views

app_name = 'prime'

urlpatterns = [
    # Dashboard Stats
    path('stats/', views.prime_dashboard_stats, name='dashboard_stats'),

    # Risk Analysis
    path('risk/calculate/', views.calculate_risk, name='calculate_risk'),

    # Monte Carlo Simulation
    path('monte-carlo/simulate/', views.simulate_monte_carlo, name='simulate_monte_carlo'),
    path('monte-carlo/portfolio-var/', views.simulate_portfolio_var, name='portfolio_var'),
    path('monte-carlo/stress-test/', views.stress_test, name='stress_test'),

    # Counterfactual AI
    path('counterfactual/generate/', views.generate_counterfactual, name='generate_counterfactual'),
    path('counterfactual/suggestions/', views.get_optimal_suggestions, name='optimal_suggestions'),

    # Knowledge Graph
    path('graph/', views.get_contract_graph, name='contract_graph'),

    # Profitability Analysis
    path('profitability/contract/', views.calculate_contract_profitability, name='contract_profitability'),
    path('profitability/portfolio/', views.calculate_portfolio_profitability, name='portfolio_profitability'),
]
