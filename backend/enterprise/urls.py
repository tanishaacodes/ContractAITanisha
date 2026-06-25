"""
Enterprise Risk Intelligence URL Configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.get_dashboard_data, name='enterprise-dashboard'),
    path('dashboard/<str:contract_id>/', views.get_dashboard_data, name='enterprise-dashboard-contract'),

    # Knowledge Graph
    path('graph/<str:contract_id>/', views.get_contract_graph, name='contract-knowledge-graph'),

    # Supply Chain
    path('supply-chain/', views.get_supply_chain_risk, name='supply-chain-risk'),
    path('supply-chain/<str:contract_id>/', views.get_supply_chain_risk, name='supply-chain-risk-contract'),

    # Geo-Political Risk
    path('geo-risk/', views.get_geopolitical_risk, name='geopolitical-risk'),
    path('geo-risk/<str:contract_id>/', views.get_geopolitical_risk, name='geopolitical-risk-contract'),

    # Commodity Forecast
    path('commodity-forecast/', views.commodity_forecast, name='commodity-forecast'),
    path('commodity-forecast/<str:contract_id>/', views.commodity_forecast, name='commodity-forecast-contract'),

    # Monte Carlo VaR
    path('monte-carlo/<str:contract_id>/', views.run_monte_carlo_simulation, name='monte-carlo-simulation'),

    # Margin Sensitivity
    path('margin-sensitivity/<str:contract_id>/', views.get_margin_sensitivity, name='margin-sensitivity'),

    # Portfolio VaR
    path('portfolio-var/', views.get_portfolio_var, name='portfolio-var'),
    path('portfolio/contracts/', views.get_portfolio_contracts, name='portfolio-contracts'),

    # Exposure Waterfall
    path('exposure-waterfall/<str:contract_id>/', views.get_exposure_waterfall, name='exposure-waterfall'),

    # Systemic Shock Simulation
    path('simulate-shock/<str:contract_id>/', views.simulate_systemic_shock, name='simulate-systemic-shock'),

    # Real-time Commodity Prices
    path('commodity-prices/update/', views.update_commodity_prices, name='update-commodity-prices'),
    path('commodity-prices/<str:commodity_name>/', views.get_realtime_commodity_price, name='realtime-commodity-price'),
]
