"""
URL Configuration for New Features
===================================
Add these to your main urls.py
"""

from django.urls import path
from .api_endpoints import (
    mcts_negotiation_tree,
    multi_agent_negotiation,
    rl_optimize_contract,
    train_rl_model,
    match_precedents,
    precedent_graph,
)

# New URL patterns to add
new_urlpatterns = [
    # MCTS Negotiation Tree
    path('api/dispute/mcts-negotiation/', mcts_negotiation_tree, name='mcts_negotiation'),

    # Multi-Agent Negotiation
    path('api/dispute/multi-agent-negotiation/', multi_agent_negotiation, name='multi_agent_negotiation'),

    # RL Optimizer
    path('api/dispute/rl-optimize/', rl_optimize_contract, name='rl_optimize'),
    path('api/dispute/train-rl/', train_rl_model, name='train_rl'),

    # Legal Precedent Matching
    path('api/dispute/match-precedents/', match_precedents, name='match_precedents'),
    path('api/dispute/precedent-graph/', precedent_graph, name='precedent_graph'),
]
