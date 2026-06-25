from django.urls import path
from .views import (
    DisputePredictView,
    DisputeSimulateView,
    DisputeGraphView,
    DisputePredictionListView,
    DisputePredictionDetailView,
    DisputePredictFromContractView,
    DisputePrebuiltScenariosView,
    DisputeSimilarClausesView,
    DisputeAIStatusView,
)
from .advanced_views import (
    ClauseRiskTableView,
    TimeTravelRiskView,
    DigitalTwinSimulateView,
    NegotiationSimulatorView,
    MultiAgentNegotiationView,
    PortfolioDisputeHeatmapView,
)
from .api_endpoints import (
    mcts_negotiation_tree,
    multi_agent_negotiation,
    rl_optimize_contract,
    train_rl_model,
    match_precedents,
    precedent_graph,
)

urlpatterns = [
    # ── Core Prediction ──────────────────────────────────────
    path('predict/', DisputePredictView.as_view(), name='dispute-predict'),
    path('simulate/', DisputeSimulateView.as_view(), name='dispute-simulate'),
    path('graph/', DisputeGraphView.as_view(), name='dispute-graph'),
    path('predictions/', DisputePredictionListView.as_view(), name='dispute-predictions'),
    path('predictions/<str:prediction_id>/', DisputePredictionDetailView.as_view(), name='dispute-prediction-detail'),
    path('predict-from-contract/<str:contract_id>/', DisputePredictFromContractView.as_view(), name='dispute-predict-from-contract'),
    path('prebuilt-scenarios/', DisputePrebuiltScenariosView.as_view(), name='dispute-prebuilt-scenarios'),
    path('similar-clauses/', DisputeSimilarClausesView.as_view(), name='dispute-similar-clauses'),
    path('ai-status/', DisputeAIStatusView.as_view(), name='dispute-ai-status'),

    # ── Clause Risk Table ─────────────────────────────────────
    path('clause-risk-table/', ClauseRiskTableView.as_view(), name='dispute-clause-risk-table'),
    path('clause-risk-table/<str:contract_id>/', ClauseRiskTableView.as_view(), name='dispute-clause-risk-table-contract'),

    # ── Time-Travel Risk ──────────────────────────────────────
    path('time-travel/', TimeTravelRiskView.as_view(), name='dispute-time-travel'),
    path('time-travel/<str:contract_id>/', TimeTravelRiskView.as_view(), name='dispute-time-travel-contract'),

    # ── Digital Twin ──────────────────────────────────────────
    path('digital-twin/simulate/', DigitalTwinSimulateView.as_view(), name='dispute-digital-twin'),

    # ── Negotiation Simulator ─────────────────────────────────
    path('negotiation/simulate/', NegotiationSimulatorView.as_view(), name='dispute-negotiation-simulate'),

    # ── Multi-Agent Negotiation ───────────────────────────────
    path('multi-agent/negotiate/', MultiAgentNegotiationView.as_view(), name='dispute-multi-agent'),

    # ── Portfolio Heatmap ─────────────────────────────────────
    path('portfolio-heatmap/', PortfolioDisputeHeatmapView.as_view(), name='dispute-portfolio-heatmap'),

    # ── NEW ADVANCED AI FEATURES ──────────────────────────────
    # MCTS Negotiation Tree
    path('mcts-negotiation/', mcts_negotiation_tree, name='mcts-negotiation'),

    # Multi-Agent Negotiation (NEW - Advanced version)
    path('multi-agent-negotiation/', multi_agent_negotiation, name='multi-agent-negotiation-advanced'),

    # RL Optimizer
    path('rl-optimize/', rl_optimize_contract, name='rl-optimize'),
    path('train-rl/', train_rl_model, name='train-rl'),

    # Legal Precedent Matching
    path('match-precedents/', match_precedents, name='match-precedents'),
    path('precedent-graph/', precedent_graph, name='precedent-graph'),
]
