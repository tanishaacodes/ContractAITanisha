"""
Force Majeure Advanced Features — Views
=========================================
  POST  /api/force-majeure/counterfactual/        — Counterfactual Risk Engine
  POST  /api/force-majeure/portfolio-simulate/    — Portfolio-Wide FM Simulation
  GET   /api/force-majeure/knowledge-graph/       — FM Knowledge Graph (NetworkX-based)
  POST  /api/force-majeure/digital-twin/          — Contract Digital Twin Engine
  POST  /api/force-majeure/multi-agent-negotiate/ — Multi-Agent Clause Negotiation
  GET   /api/force-majeure/supply-chain-map/      — Supply Chain Risk Map
"""
import logging
import math
import random
import re
from typing import Any, Dict, List, Optional

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .bayesian_engine import get_fm_bayesian_engine, LAYER1_EVENTS, LAYER2_DISRUPTIONS, LAYER3_SUPPLY, LAYER4_OUTCOMES, ALL_NODES
from .fm_service import (
    audit_fm_clause, predict_fm_risk, monte_carlo_loss,
    analyze_war_risk, FM_EVENT_CATEGORIES, BENCHMARK_SCORES,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. COUNTERFACTUAL RISK ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class FMCounterfactualView(APIView):
    """
    POST /api/force-majeure/counterfactual/
    "What would the risk have been if X had not occurred?"
    Compares baseline prediction vs. counterfactual (with one or more root events removed).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        data = request.data
        contract_text = data.get('contract_text', '')
        contract_value = float(data.get('contract_value', 1_000_000))
        base_evidence = data.get('base_evidence', {})         # e.g. {"war":0.8, "pandemic":0.6}
        remove_events = data.get('remove_events', [])         # events to set to 0 in counterfactual
        what_if_values = data.get('what_if_values', {})       # optional override values

        if not base_evidence:
            return Response({'error': 'base_evidence required'}, status=status.HTTP_400_BAD_REQUEST)

        engine = get_fm_bayesian_engine()

        # ── Baseline ──────────────────────────────────────────────────────────
        base_probs = engine.infer(base_evidence)
        base_risk = engine.compute_fm_risk_score(base_evidence)
        base_mc = monte_carlo_loss(base_risk, contract_value, {n: base_probs.get(n, 0) for n in LAYER4_OUTCOMES})

        # ── Counterfactual ────────────────────────────────────────────────────
        cf_evidence = {k: v for k, v in base_evidence.items() if k not in remove_events}
        for k, v in what_if_values.items():
            cf_evidence[k] = float(v)
        # Set removed events to 0
        for ev in remove_events:
            cf_evidence[ev] = 0.0

        cf_probs = engine.infer(cf_evidence)
        cf_risk = engine.compute_fm_risk_score(cf_evidence)
        cf_mc = monte_carlo_loss(cf_risk, contract_value, {n: cf_probs.get(n, 0) for n in LAYER4_OUTCOMES})

        # ── Delta Analysis ────────────────────────────────────────────────────
        risk_reduction = round(base_risk - cf_risk, 4)
        loss_reduction = round(base_mc['expected_loss'] - cf_mc['expected_loss'], 2)
        pct_risk_reduction = round(risk_reduction / max(base_risk, 0.001) * 100, 1)

        # Per-outcome deltas
        outcome_deltas = {}
        for node in LAYER4_OUTCOMES:
            base_p = base_probs.get(node, 0)
            cf_p = cf_probs.get(node, 0)
            outcome_deltas[node] = {
                'baseline': round(base_p, 4),
                'counterfactual': round(cf_p, 4),
                'delta': round(cf_p - base_p, 4),
                'reduction_pct': round((base_p - cf_p) / max(base_p, 0.001) * 100, 1),
            }

        # Causal attribution: which removed event contributed most?
        # For events not in base_evidence, assume default probability of 0.5 to measure potential impact
        event_attribution = []
        for ev in remove_events:
            ev_base_val = base_evidence.get(ev, 0.5)
            # Compute risk WITH this event set to its value (or default 0.5)
            with_ev = dict(base_evidence)
            with_ev[ev] = ev_base_val
            risk_with = engine.compute_fm_risk_score(with_ev)
            # Compute risk WITHOUT this event
            without_ev = dict(base_evidence)
            without_ev[ev] = 0.0
            risk_without = engine.compute_fm_risk_score(without_ev)
            contribution = max(0.0, risk_with - risk_without)
            event_attribution.append({
                'event': ev,
                'base_probability': round(ev_base_val, 4),
                'risk_if_removed': round(risk_without, 4),
                'risk_reduction': round(contribution, 4),
                'contribution_pct': round(contribution / max(risk_with, 0.001) * 100, 1),
            })

        # Sort by contribution
        event_attribution.sort(key=lambda x: x['risk_reduction'], reverse=True)

        # Clause impact
        clause_audit = None
        if contract_text:
            try:
                clause_audit = audit_fm_clause(contract_text)
            except Exception:
                pass

        return Response({
            'baseline': {
                'fm_risk_score': round(base_risk, 4),
                'expected_loss_usd': base_mc['expected_loss'],
                'p95_loss_usd': base_mc['p95'],
                'fm_invocation_prob': round(base_probs.get('fm_invocation', 0), 4),
                'project_delay_prob': round(base_probs.get('project_delay', 0), 4),
                'evidence': base_evidence,
            },
            'counterfactual': {
                'fm_risk_score': round(cf_risk, 4),
                'expected_loss_usd': cf_mc['expected_loss'],
                'p95_loss_usd': cf_mc['p95'],
                'fm_invocation_prob': round(cf_probs.get('fm_invocation', 0), 4),
                'project_delay_prob': round(cf_probs.get('project_delay', 0), 4),
                'evidence': cf_evidence,
                'events_removed': remove_events,
            },
            'delta_analysis': {
                'risk_reduction': risk_reduction,
                'pct_risk_reduction': pct_risk_reduction,
                'loss_reduction_usd': loss_reduction,
                'loss_pct_reduction': round(loss_reduction / max(base_mc['expected_loss'], 1) * 100, 1),
                'outcome_deltas': outcome_deltas,
            },
            'causal_attribution': event_attribution,
            'clause_coverage': {
                'strength_score': clause_audit.get('strength_score', 0) if clause_audit else 0,
                'covered_events': clause_audit.get('covered_events', []) if clause_audit else [],
                'missing_events': clause_audit.get('missing_events', []) if clause_audit else [],
            },
            'insight': _counterfactual_insight(event_attribution, pct_risk_reduction, loss_reduction),
        })


def _counterfactual_insight(attribution: list, pct_reduction: float, loss_reduction: float) -> str:
    if not attribution:
        return "No counterfactual events specified."
    top = attribution[0] if attribution else {}
    top_event = top.get('event', '').replace('_', ' ')
    if pct_reduction > 40:
        return (
            f"Removing '{top_event}' would reduce FM risk by {pct_reduction:.0f}% "
            f"and save ${loss_reduction:,.0f} in expected losses. "
            "This event is the dominant causal driver — contractual mitigation is strongly recommended."
        )
    elif pct_reduction > 15:
        return (
            f"Removing '{top_event}' would reduce FM risk by {pct_reduction:.0f}%. "
            f"Expected loss savings: ${loss_reduction:,.0f}. "
            "Moderate causal influence — consider targeted clause upgrades."
        )
    else:
        return (
            f"Removing the selected event(s) has limited risk impact ({pct_reduction:.0f}% reduction). "
            "Other risk drivers dominate — review the full Bayesian network for deeper mitigation."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. PORTFOLIO-WIDE FM SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════
class FMPortfolioSimulateView(APIView):
    """
    POST /api/force-majeure/portfolio-simulate/
    Simulates a global FM event across an entire portfolio of contracts.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        data = request.data
        scenario_type = data.get('scenario_type', 'war_escalation')
        custom_evidence = data.get('evidence', {})
        portfolio_contracts = data.get('contracts', [])  # optional: [{id, title, value, text, industry, jurisdiction}]
        iterations = int(data.get('iterations', 1000))

        # If no contracts passed, fetch from DB
        if not portfolio_contracts:
            try:
                from api.models import Contract
                qs = Contract.objects.all().values('id', 'title', 'content', 'industry', 'jurisdiction')[:30]
                portfolio_contracts = [
                    {
                        'id': str(c['id']),
                        'title': c.get('title', f"Contract {c['id']}"),
                        'contract_value': random.uniform(500_000, 10_000_000),
                        'text': c.get('content', ''),
                        'industry': c.get('industry', 'General'),
                        'jurisdiction': c.get('jurisdiction', 'International'),
                    }
                    for c in qs
                ]
            except Exception:
                # Demo mode: generate synthetic portfolio
                portfolio_contracts = _generate_demo_portfolio()

        # ── Scenario evidence presets ──────────────────────────────────────────
        SCENARIO_PRESETS = {
            'war_escalation':    {'war': 0.75, 'trade_sanctions': 0.65, 'energy_crisis': 0.55, 'political_coup': 0.35},
            'financial_crisis':  {'economic_collapse': 0.55, 'currency_volatility': 0.60, 'financial_market_crash': 0.50},
            'supply_chain':      {'supplier_failure': 0.60, 'port_closure': 0.55, 'transport_shutdown': 0.50},
            'pandemic':          {'pandemic': 0.65, 'labor_shortage': 0.55, 'factory_shutdown': 0.50},
            'cyber_attack':      {'cyber_attack': 0.60, 'infrastructure_failure': 0.50},
            'climate_disaster':  {'extreme_weather': 0.55, 'flooding': 0.50, 'wildfire': 0.40},
            'commodity_shock':   {'commodity_price_shock': 0.50, 'energy_price_spike': 0.45},
            'base_case':         {},
            'custom':            {},
        }

        evidence = {**SCENARIO_PRESETS.get(scenario_type, {}), **custom_evidence}

        engine = get_fm_bayesian_engine()
        base_probs = engine.infer(evidence)
        scenario_risk = engine.compute_fm_risk_score(evidence)

        # ── Simulate each contract ────────────────────────────────────────────
        contract_results = []
        total_exposure = 0.0
        total_worst_case = 0.0
        critical_count = 0
        high_count = 0

        for c in portfolio_contracts:
            cv = float(c.get('contract_value', c.get('value', 1_000_000)) or 1_000_000)

            # Industry multiplier (small adjustments to preserve scenario differences)
            industry_mult = {
                'EPC': 1.08, 'Construction': 1.05, 'Energy': 1.10, 'Defence': 1.12,
                'Shipping': 1.10, 'Pharma': 0.98, 'IT': 0.92, 'Finance': 0.95,
                'Semiconductor': 1.10,  # High-tech critical infrastructure
            }.get(c.get('industry', ''), 1.0)

            # Jurisdiction vulnerability (small adjustments)
            juris_mult = {
                'Ukraine': 1.15, 'Russia': 1.12, 'Middle East': 1.10, 'Africa': 1.08,
                'Asia Pacific': 1.04, 'EU': 0.96, 'US': 0.95, 'UK': 0.97,
                'Taiwan': 1.08,  # High geopolitical risk (Taiwan Strait tensions)
            }.get(c.get('jurisdiction', ''), 1.0)

            # Use scenario_risk directly without multipliers if single contract
            # to preserve scenario differentiation
            if len(portfolio_contracts) == 1:
                effective_risk = scenario_risk  # Direct scenario risk, no multipliers
            else:
                effective_risk = min(1.0, scenario_risk * industry_mult * juris_mult)

            # Clause coverage penalty
            text = c.get('text', c.get('contract_text', ''))
            clause_penalty = 1.0
            if text:
                try:
                    audit = audit_fm_clause(text, c.get('id', ''))
                    strength = audit.get('strength_score', 0.5)
                    clause_penalty = 1.0 + (1.0 - strength) * 0.5  # weak clause = 50% more loss
                except Exception:
                    pass

            mc = monte_carlo_loss(effective_risk, cv * clause_penalty, {n: base_probs.get(n, 0) for n in LAYER4_OUTCOMES}, iterations=iterations)

            risk_label = 'CRITICAL' if effective_risk > 0.75 else 'HIGH' if effective_risk > 0.50 else 'MEDIUM' if effective_risk > 0.30 else 'LOW'
            if risk_label == 'CRITICAL':
                critical_count += 1
            elif risk_label == 'HIGH':
                high_count += 1

            total_exposure += mc['expected_loss']
            total_worst_case += mc['worst_case']

            contract_results.append({
                'contract_id': str(c.get('id', '')),
                'contract_title': c.get('title', 'Unknown'),
                'contract_value': cv,
                'industry': c.get('industry', 'General'),
                'jurisdiction': c.get('jurisdiction', 'International'),
                'fm_risk_score': round(effective_risk, 4),
                'risk_label': risk_label,
                'expected_loss_usd': mc['expected_loss'],
                'p50_loss_usd': mc['p50'],
                'p95_loss_usd': mc['p95'],
                'worst_case_loss_usd': mc['worst_case'],
                'fm_invocation_prob': round(base_probs.get('fm_invocation', 0) * effective_risk / max(scenario_risk, 0.01), 4),
                'delay_days': round(base_probs.get('project_delay', 0) * 180 * (effective_risk / max(scenario_risk, 0.01)), 1),
            })

        # Sort by risk
        contract_results.sort(key=lambda x: x['fm_risk_score'], reverse=True)

        # Industry breakdown
        industry_stats = {}
        for r in contract_results:
            ind = r['industry']
            if ind not in industry_stats:
                industry_stats[ind] = {'count': 0, 'total_exposure': 0.0, 'avg_risk': 0.0, 'risks': []}
            industry_stats[ind]['count'] += 1
            industry_stats[ind]['total_exposure'] += r['expected_loss_usd']
            industry_stats[ind]['risks'].append(r['fm_risk_score'])
        for ind, stats in industry_stats.items():
            stats['avg_risk'] = round(sum(stats['risks']) / max(len(stats['risks']), 1), 4)
            del stats['risks']

        return Response({
            'scenario': {
                'type': scenario_type,
                'evidence': evidence,
                'scenario_risk_score': round(scenario_risk, 4),
            },
            'portfolio_summary': {
                'total_contracts': len(contract_results),
                'critical_risk_contracts': critical_count,
                'high_risk_contracts': high_count,
                'total_expected_exposure_usd': round(total_exposure, 2),
                'total_worst_case_exposure_usd': round(total_worst_case, 2),
                'average_fm_risk': round(sum(r['fm_risk_score'] for r in contract_results) / max(len(contract_results), 1), 4),
            },
            'contract_results': contract_results,
            'industry_breakdown': industry_stats,
            'top_5_at_risk': contract_results[:5],
        })


def _generate_demo_portfolio():
    industries = ['EPC', 'Construction', 'Energy', 'Shipping', 'IT', 'Finance', 'Pharma', 'Defence']
    jurisdictions = ['Middle East', 'Ukraine', 'Asia Pacific', 'EU', 'US', 'Africa', 'UK', 'India']
    portfolio = []
    for i in range(20):
        portfolio.append({
            'id': f'demo-{i+1:03d}',
            'title': f'Contract #{i+1:03d} — {industries[i % len(industries)]}',
            'contract_value': random.randint(1, 50) * 500_000,
            'text': '',
            'industry': industries[i % len(industries)],
            'jurisdiction': jurisdictions[i % len(jurisdictions)],
        })
    return portfolio


# ═══════════════════════════════════════════════════════════════════════════════
# 3. FM KNOWLEDGE GRAPH
# ═══════════════════════════════════════════════════════════════════════════════
class FMKnowledgeGraphView(APIView):
    """
    GET /api/force-majeure/knowledge-graph/
    Returns a knowledge graph of FM events, contracts, clauses, and risk propagation paths.
    Provides React Flow compatible format for visualization.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        focus = request.query_params.get('focus', 'all')  # all | war | pandemic | supply_chain
        depth = int(request.query_params.get('depth', 3))

        # ── Node categories ───────────────────────────────────────────────────
        node_colors = {
            'fm_event': '#F16667',       # red — FM root events
            'disruption': '#F79767',      # orange — disruption nodes
            'supply_impact': '#FFD86E',   # yellow — supply chain impacts
            'outcome': '#9063CD',         # purple — contract outcomes
            'clause': '#4C8EDA',          # blue — FM clause types
            'mitigation': '#68BC00',      # green — mitigation strategies
            'jurisdiction': '#06B6D4',    # cyan — jurisdictions
            'industry': '#10b981',        # teal — industries
        }

        nodes = []
        edges = []
        node_id = 0

        # ── Layer 1: FM Root Events ───────────────────────────────────────────
        event_nodes = {}
        events_to_show = LAYER1_EVENTS
        if focus == 'war':
            events_to_show = [e for e in LAYER1_EVENTS if any(k in e for k in ['war', 'sanction', 'political', 'military'])]
        elif focus == 'pandemic':
            events_to_show = [e for e in LAYER1_EVENTS if any(k in e for k in ['pandemic', 'health', 'epidemic', 'bio'])]
        elif focus == 'supply_chain':
            events_to_show = [e for e in LAYER1_EVENTS if any(k in e for k in ['supply', 'port', 'trade', 'commodity'])]

        for i, ev in enumerate(events_to_show):
            nid = f'event_{ev}'
            x = 100 + (i % 5) * 220
            y = 50 + (i // 5) * 120
            nodes.append({
                'id': nid,
                'data': {'label': ev.replace('_', ' ').title(), 'type': 'fm_event', 'category': 'Root FM Event'},
                'position': {'x': x, 'y': y},
                'style': _node_style(node_colors['fm_event'], 140),
                'type': 'default',
            })
            event_nodes[ev] = nid

        if depth >= 2:
            # ── Layer 2: Disruptions ──────────────────────────────────────────
            disruption_nodes = {}
            for i, dis in enumerate(LAYER2_DISRUPTIONS):
                nid = f'dis_{dis}'
                x = 150 + (i % 4) * 250
                y = 350
                nodes.append({
                    'id': nid,
                    'data': {'label': dis.replace('_', ' ').title(), 'type': 'disruption', 'category': 'Operational Disruption'},
                    'position': {'x': x, 'y': y},
                    'style': _node_style(node_colors['disruption'], 150),
                    'type': 'default',
                })
                disruption_nodes[dis] = nid

            # Edges: events → disruptions (rich causal links with weights)
            causal_links = [
                ('war', 'port_closure', 0.85), ('war', 'transport_shutdown', 0.80), ('war', 'factory_shutdown', 0.75),
                ('war', 'labor_shortage', 0.65), ('war', 'supplier_failure', 0.78),
                ('regional_conflict', 'port_closure', 0.72), ('regional_conflict', 'transport_shutdown', 0.68),
                ('regional_conflict', 'supplier_failure', 0.70),
                ('trade_sanctions', 'supplier_failure', 0.88), ('trade_sanctions', 'port_closure', 0.75),
                ('trade_sanctions', 'factory_shutdown', 0.65),
                ('pandemic', 'labor_shortage', 0.92), ('pandemic', 'factory_shutdown', 0.85),
                ('pandemic', 'transport_shutdown', 0.70), ('pandemic', 'supplier_failure', 0.68),
                ('epidemic', 'labor_shortage', 0.80), ('epidemic', 'factory_shutdown', 0.72),
                ('earthquake', 'infrastructure_failure', 0.88), ('earthquake', 'transport_shutdown', 0.82),
                ('earthquake', 'factory_shutdown', 0.75), ('earthquake', 'port_closure', 0.70),
                ('flood', 'transport_shutdown', 0.85), ('flood', 'port_closure', 0.78),
                ('flood', 'factory_shutdown', 0.68), ('flood', 'infrastructure_failure', 0.82),
                ('hurricane', 'port_closure', 0.90), ('hurricane', 'transport_shutdown', 0.85),
                ('hurricane', 'infrastructure_failure', 0.80),
                ('wildfire', 'factory_shutdown', 0.75), ('wildfire', 'infrastructure_failure', 0.70),
                ('volcanic_eruption', 'transport_shutdown', 0.65), ('volcanic_eruption', 'airspace_closure', 0.95),
                ('political_coup', 'port_closure', 0.68), ('political_coup', 'transport_shutdown', 0.72),
                ('political_coup', 'supplier_failure', 0.75),
                ('economic_collapse', 'supplier_failure', 0.82), ('economic_collapse', 'labor_shortage', 0.70),
                ('economic_collapse', 'factory_shutdown', 0.65),
                ('energy_crisis', 'factory_shutdown', 0.88), ('energy_crisis', 'infrastructure_failure', 0.78),
                ('energy_crisis', 'transport_shutdown', 0.82),
                ('cyber_warfare', 'infrastructure_failure', 0.90), ('cyber_warfare', 'factory_shutdown', 0.75),
                ('terrorism', 'transport_shutdown', 0.80), ('terrorism', 'port_closure', 0.75),
                ('terrorism', 'infrastructure_failure', 0.72),
                ('telecom_disruption', 'supplier_failure', 0.65), ('telecom_disruption', 'factory_shutdown', 0.68),
                ('power_grid_failure', 'factory_shutdown', 0.92), ('power_grid_failure', 'infrastructure_failure', 0.95),
                ('financial_market_crash', 'supplier_failure', 0.78), ('financial_market_crash', 'labor_shortage', 0.62),
                ('airspace_closure', 'transport_shutdown', 0.85), ('airspace_closure', 'supplier_failure', 0.70),
            ]
            node_ids = {n['id'] for n in nodes}
            eid = 0
            for (ev, dis, weight) in causal_links:
                src, tgt = f'event_{ev}', f'dis_{dis}'
                if src in node_ids and tgt in node_ids:
                    edges.append({
                        'id': f'e_ed_{eid}',
                        'source': src,
                        'target': tgt,
                        'label': f'{weight:.0%}',
                        'animated': True,
                        'style': {'stroke': '#F79767', 'strokeWidth': 1.5},
                    })
                    eid += 1

        if depth >= 3:
            # ── Layer 3: Supply Chain Impacts ─────────────────────────────────
            supply_nodes = {}
            for i, sn in enumerate(LAYER3_SUPPLY):
                nid = f'sup_{sn}'
                x = 200 + (i % 4) * 260
                y = 600
                nodes.append({
                    'id': nid,
                    'data': {'label': sn.replace('_', ' ').title(), 'type': 'supply_impact', 'category': 'Supply Chain Impact'},
                    'position': {'x': x, 'y': y},
                    'style': _node_style(node_colors['supply_impact'], 150),
                    'type': 'default',
                })
                supply_nodes[sn] = nid

            # ── Edges: disruptions → supply chain impacts (with weights) ──────
            node_ids = {n['id'] for n in nodes}  # refresh after supply nodes added
            dis_supply_links = [
                ('port_closure', 'inventory_shortage', 0.82), ('port_closure', 'logistics_delay', 0.88),
                ('port_closure', 'shipping_route_disruption', 0.92),
                ('transport_shutdown', 'logistics_delay', 0.90), ('transport_shutdown', 'shipping_route_disruption', 0.85),
                ('transport_shutdown', 'equipment_delivery_delay', 0.80),
                ('factory_shutdown', 'inventory_shortage', 0.88), ('factory_shutdown', 'manufacturing_delay', 0.92),
                ('factory_shutdown', 'equipment_delivery_delay', 0.75),
                ('labor_shortage', 'manufacturing_delay', 0.85), ('labor_shortage', 'logistics_delay', 0.70),
                ('supplier_failure', 'inventory_shortage', 0.90), ('supplier_failure', 'equipment_delivery_delay', 0.82),
                ('supplier_failure', 'commodity_cost_escalation', 0.78),
                ('infrastructure_failure', 'logistics_delay', 0.85), ('infrastructure_failure', 'shipping_route_disruption', 0.80),
                ('infrastructure_failure', 'manufacturing_delay', 0.75),
                ('airspace_closure', 'equipment_delivery_delay', 0.88), ('airspace_closure', 'logistics_delay', 0.82),
                ('telecom_disruption', 'logistics_delay', 0.68), ('telecom_disruption', 'manufacturing_delay', 0.70),
                ('power_grid_failure', 'manufacturing_delay', 0.92), ('power_grid_failure', 'inventory_shortage', 0.75),
                ('financial_market_crash', 'commodity_cost_escalation', 0.85), ('financial_market_crash', 'insurance_premium_spike', 0.88),
            ]
            sup_node_ids = {n['id'] for n in nodes}
            for i2, (dis, sup, weight) in enumerate(dis_supply_links):
                src, tgt = f'dis_{dis}', f'sup_{sup}'
                if src in sup_node_ids and tgt in sup_node_ids:
                    edges.append({
                        'id': f'e_ds_{i2}',
                        'source': src,
                        'target': tgt,
                        'label': f'{weight:.0%}',
                        'animated': True,
                        'style': {'stroke': '#FFD86E', 'strokeWidth': 1.5},
                    })

            # ── Layer 4: Contract Outcomes (created BEFORE edges that reference them) ──
            for i, oc in enumerate(LAYER4_OUTCOMES):
                nid = f'oc_{oc}'
                x = 300 + i * 260
                y = 860
                nodes.append({
                    'id': nid,
                    'data': {'label': oc.replace('_', ' ').title(), 'type': 'outcome', 'category': 'Contract Outcome'},
                    'position': {'x': x, 'y': y},
                    'style': _node_style(node_colors['outcome'], 160),
                    'type': 'default',
                })

            # ── Edges: supply impacts → contract outcomes (with weights) ──────
            all_node_ids = {n['id'] for n in nodes}
            sup_outcome_links = [
                ('inventory_shortage', 'project_delay', 0.85), ('inventory_shortage', 'cost_overrun', 0.78),
                ('logistics_delay', 'project_delay', 0.90), ('logistics_delay', 'contract_suspension', 0.70),
                ('shipping_route_disruption', 'project_delay', 0.82), ('shipping_route_disruption', 'cost_overrun', 0.75),
                ('manufacturing_delay', 'project_delay', 0.92), ('manufacturing_delay', 'cost_overrun', 0.80),
                ('equipment_delivery_delay', 'project_delay', 0.88), ('equipment_delivery_delay', 'contract_suspension', 0.72),
                ('commodity_cost_escalation', 'cost_overrun', 0.95), ('commodity_cost_escalation', 'fm_invocation', 0.82),
                ('insurance_premium_spike', 'cost_overrun', 0.75), ('insurance_premium_spike', 'insurance_claim', 0.88),
                ('inventory_shortage', 'fm_invocation', 0.75), ('manufacturing_delay', 'fm_invocation', 0.78),
                ('logistics_delay', 'contract_termination', 0.65), ('commodity_cost_escalation', 'contract_termination', 0.70),
            ]
            for i3, (sup, oc, weight) in enumerate(sup_outcome_links):
                src, tgt = f'sup_{sup}', f'oc_{oc}'
                if src in all_node_ids and tgt in all_node_ids:
                    edges.append({
                        'id': f'e_so_{i3}',
                        'source': src,
                        'target': tgt,
                        'label': f'{weight:.0%}',
                        'animated': True,
                        'style': {'stroke': '#9063CD', 'strokeWidth': 1.5},
                    })

        # ── Mitigation strategies linked to outcomes ─────────────────────────
        mitigations = [
            ('fm_invocation', 'Price Adjustment Clause', 'mitigation'),
            ('fm_invocation', 'Extension of Time Clause', 'mitigation'),
            ('project_delay', 'Liquidated Damages Cap', 'mitigation'),
            ('project_delay', 'Delay Penalty Waiver', 'mitigation'),
            ('contract_termination', 'Force Majeure Termination Rights', 'mitigation'),
            ('cost_overrun', 'Cost Escalation Clause', 'mitigation'),
        ]
        mit_nodes = {}
        for i, (oc, mit_name, _) in enumerate(mitigations):
            nid = f'mit_{i}'
            if nid not in mit_nodes:
                x = 100 + i * 220
                y = 1100
                nodes.append({
                    'id': nid,
                    'data': {'label': mit_name, 'type': 'mitigation', 'category': 'Mitigation Strategy'},
                    'position': {'x': x, 'y': y},
                    'style': _node_style(node_colors['mitigation'], 180),
                    'type': 'default',
                })
                mit_nodes[nid] = nid
                # Edge: outcome → mitigation
                oc_nid = f'oc_{oc}'
                if any(n['id'] == oc_nid for n in nodes):
                    edges.append({
                        'id': f'e_mit_{i}',
                        'source': oc_nid,
                        'target': nid,
                        'style': {'stroke': '#68BC00', 'strokeWidth': 1.5, 'strokeDasharray': '5,5'},
                        'label': 'mitigated by',
                    })

        return Response({
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'fm_event_nodes': len([n for n in nodes if n['data'].get('type') == 'fm_event']),
                'disruption_nodes': len([n for n in nodes if n['data'].get('type') == 'disruption']),
                'outcome_nodes': len([n for n in nodes if n['data'].get('type') == 'outcome']),
                'mitigation_nodes': len([n for n in nodes if n['data'].get('type') == 'mitigation']),
            },
            'legend': [
                {'type': 'fm_event', 'color': '#F16667', 'label': 'FM Root Event'},
                {'type': 'disruption', 'color': '#F79767', 'label': 'Operational Disruption'},
                {'type': 'supply_impact', 'color': '#FFD86E', 'label': 'Supply Chain Impact'},
                {'type': 'outcome', 'color': '#9063CD', 'label': 'Contract Outcome'},
                {'type': 'mitigation', 'color': '#68BC00', 'label': 'Mitigation Strategy'},
            ],
            'focus': focus,
            'depth': depth,
        })


def _node_style(color: str, width: int = 150) -> dict:
    return {
        'background': color,
        'color': '#fff',
        'border': '2px solid rgba(255,255,255,0.3)',
        'borderRadius': '8px',
        'padding': '8px',
        'fontSize': '11px',
        'width': width,
        'textAlign': 'center',
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 4. CONTRACT DIGITAL TWIN ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class FMDigitalTwinView(APIView):
    """
    POST /api/force-majeure/digital-twin/
    Creates a real-time digital twin of a contract's FM risk profile.
    Monitors live events and simulates their impact on the contract continuously.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        data = request.data
        contract_id = data.get('contract_id', '')
        contract_text = data.get('contract_text', '')
        contract_value = float(data.get('contract_value', 1_000_000))
        contract_title = data.get('contract_title', 'Contract Digital Twin')
        jurisdiction = data.get('jurisdiction', 'International')
        industry = data.get('industry', 'General')
        project_location = data.get('project_location', '')
        supplier_locations = data.get('supplier_locations', [])

        if not contract_text:
            return Response({'error': 'contract_text required'}, status=status.HTTP_400_BAD_REQUEST)

        # ── Step 1: Fetch live global events ──────────────────────────────────
        live_events = []
        try:
            from .live_data_engine import fetch_all_live_events
            live_data = fetch_all_live_events()
            live_events = live_data.get('events', [])
        except Exception as e:
            logger.warning(f"Digital twin: live data fetch failed: {e}")

        # ── Step 2: Map live events to Bayesian evidence ──────────────────────
        evidence = _map_live_events_to_evidence(live_events, project_location, supplier_locations)

        # ── Step 3: Full FM risk prediction ───────────────────────────────────
        engine = get_fm_bayesian_engine()
        # Industry-specific evidence boosts — different industries have different FM sensitivities
        industry_boosts = {
            'Energy': {'energy_crisis': 0.15, 'port_closure': 0.10, 'trade_sanctions': 0.10},
            'Construction': {'flood': 0.12, 'earthquake': 0.10, 'supplier_failure': 0.08},
            'Manufacturing': {'factory_shutdown': 0.15, 'supplier_failure': 0.12, 'trade_sanctions': 0.10},
            'Technology': {'cyber_warfare': 0.20, 'trade_sanctions': 0.15, 'factory_shutdown': 0.10},
            'Logistics': {'port_closure': 0.18, 'transport_shutdown': 0.15, 'flood': 0.08},
            'Finance': {'economic_collapse': 0.20, 'trade_sanctions': 0.15, 'political_coup': 0.10},
            'Healthcare': {'pandemic': 0.25, 'epidemic': 0.20, 'government_lockdown': 0.15},
            'Agriculture': {'flood': 0.20, 'drought': 0.18, 'commodity_shock': 0.15},
            'Semiconductor': {'trade_sanctions': 0.25, 'factory_shutdown': 0.20, 'cyber_warfare': 0.15, 'port_closure': 0.12},
            'Defence': {'war': 0.20, 'trade_sanctions': 0.18, 'political_coup': 0.12},
        }
        boosted_evidence = dict(evidence)
        for node, boost in industry_boosts.get(industry, {}).items():
            boosted_evidence[node] = min(1.0, boosted_evidence.get(node, 0.3) + boost)

        all_probs = engine.infer(boosted_evidence)
        fm_risk = engine.compute_fm_risk_score(boosted_evidence)
        mc = monte_carlo_loss(fm_risk, contract_value, {n: all_probs.get(n, 0) for n in LAYER4_OUTCOMES})

        # ── Step 4: Clause audit ───────────────────────────────────────────────
        clause_audit = audit_fm_clause(contract_text, contract_id, contract_title)

        # ── Step 5: Real-time stress test ──────────────────────────────────────
        stress_scenarios = _run_digital_twin_stress(engine, evidence, contract_value, mc)

        # ── Step 6: Exposure timeline (12-month forecast) ─────────────────────
        exposure_timeline = _generate_exposure_timeline(fm_risk, mc['expected_loss'])

        # ── Step 7: Health score ────────────────────────────────────────────────
        clause_strength = clause_audit.get('strength_score', 0)
        covered_count = len(clause_audit.get('covered_events', []))
        # Industry-specific health weighting
        industry_health_weight = {
            'Semiconductor': 0.5, 'Defence': 0.5, 'Healthcare': 0.45,
            'Energy': 0.42, 'Technology': 0.42, 'Finance': 0.40,
            'Logistics': 0.38, 'Construction': 0.35, 'Manufacturing': 0.35,
            'Agriculture': 0.30,
        }.get(industry, 0.35)
        # Multi-factor health: risk exposure, clause quality, event coverage, industry resilience
        coverage_score = covered_count / 14.0
        health_raw = (
            (1.0 - fm_risk) * 0.40 +          # FM risk exposure (40%)
            clause_strength * 0.30 +            # Clause quality (30%)
            coverage_score * 0.20 +             # Event coverage (20%)
            industry_health_weight * 0.10       # Industry resilience baseline (10%)
        )
        health_score = round(health_raw, 4)
        health_label = 'HEALTHY' if health_score > 0.6 else 'AT RISK' if health_score > 0.35 else 'CRITICAL'

        # ── Step 8: Action recommendations ────────────────────────────────────
        actions = _digital_twin_actions(fm_risk, clause_audit, live_events[:5], industry, jurisdiction)

        # Industry risk profile for frontend display
        industry_profile = {
            'name': industry,
            'top_risks': sorted(industry_boosts.get(industry, {}).items(), key=lambda x: x[1], reverse=True)[:3],
            'sensitivity': 'HIGH' if industry in ['Semiconductor','Defence','Healthcare'] else 'MEDIUM' if industry in ['Energy','Technology','Finance'] else 'STANDARD',
            'boosted_nodes': list(industry_boosts.get(industry, {}).keys()),
        }

        return Response({
            'twin_id': f'twin_{contract_id[:8] if contract_id else "new"}_{int(random.random() * 9999):04d}',
            'contract_id': contract_id,
            'contract_title': contract_title,
            'industry': industry,
            'jurisdiction': jurisdiction,
            'timestamp': _utcnow(),
            'health': {
                'score': health_score,
                'label': health_label,
                'fm_risk_score': round(fm_risk, 4),
                'clause_strength': clause_strength,
            },
            'industry_profile': industry_profile,
            'live_risk': {
                'live_events_detected': len(live_events),
                'evidence_signals': boosted_evidence,
                'fm_risk_score': round(fm_risk, 4),
                'fm_invocation_prob': round(all_probs.get('fm_invocation', 0), 4),
                'project_delay_prob': round(all_probs.get('project_delay', 0), 4),
                'contract_termination_prob': round(all_probs.get('contract_termination', 0), 4),
                'cost_overrun_prob': round(all_probs.get('cost_overrun', 0), 4),
                'contract_suspension_prob': round(all_probs.get('contract_suspension', 0), 4),
            },
            'financial_exposure': {
                'expected_loss_usd': mc['expected_loss'],
                'p50_loss_usd': mc['p50'],
                'p95_loss_usd': mc['p95'],
                'p99_loss_usd': mc['p99'],
                'worst_case_loss_usd': mc['worst_case'],
                'contract_value': contract_value,
                'exposure_pct': round(mc['expected_loss'] / max(contract_value, 1) * 100, 1),
            },
            'clause_status': {
                'strength_score': clause_strength,
                'covered_events': clause_audit.get('covered_events', []),
                'missing_events': clause_audit.get('missing_events', []),
                'status': clause_audit.get('status', 'unknown'),
            },
            'stress_scenarios': stress_scenarios,
            'exposure_timeline': exposure_timeline,
            'live_events_affecting': _filter_relevant_events(live_events, project_location, supplier_locations),
            'recommended_actions': actions,
        })


def _map_live_events_to_evidence(live_events: list, project_location: str, supplier_locations: list) -> dict:
    """Maps live global events to Bayesian evidence nodes."""
    evidence = {}
    event_type_map = {
        'war': 'war',
        'sanctions': 'trade_sanctions',
        'pandemic': 'pandemic',
        'natural_disaster': 'natural_disaster',
        'port_closure': 'port_closure',
        'supply_chain_disruption': 'supplier_failure',
        'energy_shortage': 'energy_crisis',
        'cyber_attack': 'cyber_attack',
        'political_coup': 'political_unrest',
        'terrorism': 'terrorism',
        'earthquake': 'natural_disaster',
        'flood': 'natural_disaster',
    }
    for ev in live_events:
        ev_type = ev.get('event_type', 'unknown')
        risk_score = ev.get('risk_score', 0)
        bayesian_node = event_type_map.get(ev_type, '')
        if bayesian_node and risk_score > 0.3:
            # Amplify if event is in relevant region
            location = ev.get('location', '').lower()
            project_loc = project_location.lower()
            supplier_locs = [s.lower() for s in supplier_locations]
            amplifier = 1.5 if (project_loc and project_loc in location) else 1.0
            for sl in supplier_locs:
                if sl in location:
                    amplifier = max(amplifier, 1.3)
            current = evidence.get(bayesian_node, 0)
            evidence[bayesian_node] = min(1.0, max(current, risk_score * amplifier))
    return evidence


def _run_digital_twin_stress(engine, base_evidence: dict, contract_value: float, base_mc: dict) -> list:
    """Runs 5 stress scenarios on top of base live evidence."""
    scenarios = [
        {'name': 'Base (Live Data)', 'extra': {}, 'color': '#68BC00'},
        {'name': 'War Escalation', 'extra': {'war': 0.8, 'trade_sanctions': 0.7}, 'color': '#F16667'},
        {'name': 'Supply Collapse', 'extra': {'supplier_failure': 0.7, 'port_closure': 0.65}, 'color': '#F79767'},
        {'name': 'Pandemic Surge', 'extra': {'pandemic': 0.75, 'labor_shortage': 0.6}, 'color': '#9063CD'},
        {'name': 'Financial Crisis', 'extra': {'economic_collapse': 0.7, 'currency_volatility': 0.75}, 'color': '#4C8EDA'},
    ]
    results = []
    for s in scenarios:
        ev = {**base_evidence, **s['extra']}
        risk = engine.compute_fm_risk_score(ev)
        probs = engine.infer(ev)
        mc = monte_carlo_loss(risk, contract_value, {n: probs.get(n, 0) for n in LAYER4_OUTCOMES}, iterations=1000)
        results.append({
            'scenario': s['name'],
            'color': s['color'],
            'fm_risk_score': round(risk, 4),
            'expected_loss_usd': mc['expected_loss'],
            'p95_loss_usd': mc['p95'],
            'fm_invocation_prob': round(probs.get('fm_invocation', 0), 4),
        })
    return results


def _generate_exposure_timeline(base_risk: float, base_loss: float) -> list:
    """Generates a 12-month FM exposure forecast."""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    timeline = []
    risk = base_risk
    for i, month in enumerate(months):
        # Simulate risk drift
        drift = random.uniform(-0.05, 0.08)
        risk = max(0.05, min(0.95, risk + drift))
        loss = round(base_loss * (risk / max(base_risk, 0.01)) * random.uniform(0.85, 1.15), 2)
        timeline.append({
            'month': month,
            'fm_risk': round(risk, 3),
            'expected_loss_usd': loss,
            'risk_label': 'HIGH' if risk > 0.6 else 'MED' if risk > 0.3 else 'LOW',
        })
    return timeline


def _filter_relevant_events(live_events: list, project_location: str, supplier_locations: list) -> list:
    """Returns live events most relevant to this contract."""
    relevant = []
    seen_ids = set()
    pl = project_location.lower() if project_location else ''
    sl = [s.lower() for s in supplier_locations if s]

    def _add(ev, tag):
        eid = id(ev)
        if eid not in seen_ids:
            ev['relevance'] = tag
            relevant.append(ev)
            seen_ids.add(eid)

    for ev in live_events[:20]:
        loc = ev.get('location', '').lower()
        score = ev.get('risk_score', 0)
        if pl and pl in loc:
            _add(ev, 'project_location')
        elif any(s in loc for s in sl):
            _add(ev, 'supplier_location')
        elif score > 0.3:
            _add(ev, 'high_global_risk')

    # Always ensure at least 5 events shown (top global monitors)
    for ev in live_events[:10]:
        if len(relevant) >= 8:
            break
        _add(ev, 'global_monitor')

    return relevant[:10]


def _digital_twin_actions(fm_risk: float, clause_audit: dict, top_events: list, industry: str, jurisdiction: str) -> list:
    actions = []
    if fm_risk > 0.6:
        actions.append({
            'priority': 'CRITICAL',
            'action': 'Invoke FM clause review immediately',
            'description': 'FM risk exceeds 60% — notify counterparty and legal team.',
            'icon': 'alert',
        })
    missing = clause_audit.get('missing_events', [])
    if missing:
        actions.append({
            'priority': 'HIGH',
            'action': f'Update FM clause — {len(missing)} events not covered',
            'description': f"Missing: {', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}",
            'icon': 'file-edit',
        })
    if fm_risk > 0.4:
        actions.append({
            'priority': 'MEDIUM',
            'action': 'Review insurance coverage for FM events',
            'description': f'Consider parametric insurance for {industry} in {jurisdiction}.',
            'icon': 'shield',
        })
    for ev in top_events:
        if ev.get('risk_score', 0) > 0.7:
            actions.append({
                'priority': 'HIGH',
                'action': f"Monitor: {ev.get('title', 'Live FM Event')[:60]}",
                'description': f"Location: {ev.get('location', 'Global')} · Source: {ev.get('source', 'Live')}",
                'icon': 'eye',
            })
            break
    if not actions:
        actions.append({
            'priority': 'LOW',
            'action': 'Contract FM risk within acceptable limits',
            'description': 'Continue monitoring. Schedule quarterly clause review.',
            'icon': 'check',
        })
    return actions[:5]


def _utcnow() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════════════
# 5. MULTI-AGENT CLAUSE NEGOTIATION
# ═══════════════════════════════════════════════════════════════════════════════
class FMMultiAgentNegotiateView(APIView):
    """
    POST /api/force-majeure/multi-agent-negotiate/
    Simulates multi-party FM clause negotiation (Buyer vs. Seller vs. Insurer agents).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        data = request.data
        clause_text = data.get('clause_text', '')
        contract_value = float(data.get('contract_value', 1_000_000))
        buyer_jurisdiction = data.get('buyer_jurisdiction', 'EU')
        seller_jurisdiction = data.get('seller_jurisdiction', 'Asia Pacific')
        dispute_event = data.get('dispute_event', 'war')
        rounds = int(data.get('rounds', 3))

        if not clause_text:
            return Response({'error': 'clause_text required'}, status=status.HTTP_400_BAD_REQUEST)

        # Audit original clause
        audit = audit_fm_clause(clause_text)
        strength = audit.get('strength_score', 0.5)

        # ── Agent personas ─────────────────────────────────────────────────────
        agents = {
            'buyer': {
                'name': 'Buyer Agent',
                'role': 'buyer',
                'objective': 'maximize FM coverage, minimize financial exposure',
                'risk_tolerance': 0.3,
                'jurisdiction': buyer_jurisdiction,
            },
            'seller': {
                'name': 'Seller Agent',
                'role': 'seller',
                'objective': 'limit FM obligations, preserve profit margins',
                'risk_tolerance': 0.7,
                'jurisdiction': seller_jurisdiction,
            },
            'insurer': {
                'name': 'Insurer Agent',
                'role': 'insurer',
                'objective': 'ensure insurability, define clear triggers',
                'risk_tolerance': 0.4,
                'jurisdiction': 'International',
            },
            'legal': {
                'name': 'Legal Agent',
                'role': 'legal',
                'objective': 'ensure compliance, minimize legal risk, define enforceable terms',
                'risk_tolerance': 0.2,
                'jurisdiction': buyer_jurisdiction,
            },
            'finance': {
                'name': 'Finance Agent',
                'role': 'finance',
                'objective': 'minimize cost impact, ensure cash flow protection',
                'risk_tolerance': 0.5,
                'jurisdiction': buyer_jurisdiction,
            },
        }

        # ── Simulate negotiation rounds ────────────────────────────────────────
        negotiation_log = []
        current_clause = clause_text
        current_strength = strength

        for round_num in range(1, rounds + 1):
            round_proposals = []

            for role, agent in agents.items():
                proposal = _agent_propose(agent, current_clause, current_strength, dispute_event, contract_value, round_num)
                round_proposals.append(proposal)

            # Mediator: pick best balanced proposal
            best_proposal = _mediator_decide(round_proposals, current_strength)
            current_clause = best_proposal.get('proposed_clause', current_clause)
            # Re-audit after each round — strength must never decrease (negotiation only improves)
            try:
                new_audit = audit_fm_clause(current_clause)
                new_strength = new_audit.get('strength_score', current_strength)
                current_strength = max(current_strength + 0.05, new_strength)
            except Exception:
                current_strength = min(1.0, current_strength + 0.05)
            current_strength = min(1.0, current_strength)

            consensus_idx = min(round_num - 1, len(_CONSENSUS_SUMMARIES) - 1)
            negotiation_log.append({
                'round': round_num,
                'proposals': round_proposals,
                'accepted_proposal': best_proposal,
                'clause_strength_after': round(current_strength, 4),
                'consensus_summary': _CONSENSUS_SUMMARIES[consensus_idx],
                'round_outcome': 'agreement' if round_num == rounds else 'ongoing',
            })

        # ── Final outcome ──────────────────────────────────────────────────────
        final_strength = round(current_strength, 4)
        improvement = round((final_strength - strength) * 100, 1)
        final_clause = _build_final_clause(dispute_event, buyer_jurisdiction, seller_jurisdiction, contract_value)

        # Key negotiated terms summary
        negotiated_terms = {
            'fm_definition': f"{dispute_event.replace('_',' ').title()} and all directly related sub-events",
            'notification_window': '14 days (21 days for remote/war zones)',
            'relief_duration': '90 days maximum',
            'termination_right': 'Either party after 90 days FM (14-day notice)',
            'liability_cap': f"10% of contract value (${contract_value * 0.10:,.0f})" if contract_value else '10% of contract value',
            'cost_sharing': f"60/40 (Seller {seller_jurisdiction} / Buyer {buyer_jurisdiction}) for local events; 50/50 global",
            'governing_law': 'Singapore law (neutral)',
            'arbitration': 'ICC Arbitration — Singapore seat',
            'fm_escrow': f"5% of contract value (${contract_value * 0.05:,.0f})" if contract_value else '5% of contract value',
            'insurance_required': '60% contract exposure minimum',
        }

        return Response({
            'original_strength': round(strength, 4),
            'final_strength': final_strength,
            'improvement_pct': improvement,
            'negotiation_rounds': negotiation_log,
            'final_clause': final_clause,
            'negotiated_terms': negotiated_terms,
            'final_audit': {'strength_score': final_strength},
            'agents': list(agents.values()),
            'consensus_reached': improvement > 0,
            'dispute_event': dispute_event,
            'buyer_jurisdiction': buyer_jurisdiction,
            'seller_jurisdiction': seller_jurisdiction,
            'contract_value': contract_value,
        })


_ROUND_ESCALATION = {
    # Each round agents escalate their demands — different language per round
    'buyer': [
        {
            'stance': 'expand_coverage',
            'demand': "Include all {event} sub-events and cascading effects",
            'position': "Buyer demands broad {event} coverage with automatic 30-day recovery extension. Any {event} event preventing performance shall trigger full FM relief including partial disruptions.",
            'clause_fragment': "Force Majeure shall include {event} and all directly related sub-events, cascading supply chain failures, and governmental orders arising therefrom, with automatic time extension equal to FM duration plus 30 days.",
            'concession': None,
        },
        {
            'stance': 'push_liability_cap',
            'demand': "Liability cap at 10% of contract value during FM",
            'position': "Buyer escalates: demands liability cap of 10% contract value during {event} events and shared cost-burden mechanism. Buyer will not accept force majeure exclusions that leave buyer exposed beyond 10%.",
            'clause_fragment': "During any {event} FM event, Buyer's total liability shall not exceed 10% of the contract value. Costs beyond this threshold shall be shared equally between parties pending resolution.",
            'concession': "Buyer concedes: accepts 14-day notification requirement from Seller.",
        },
        {
            'stance': 'final_position',
            'demand': "Binding arbitration clause + FM committee",
            'position': "Buyer final position: Accepts seller's 90-day cap IF a joint FM Review Committee is established. Buyer insists on ICC arbitration within 30 days of any FM dispute.",
            'clause_fragment': "A joint FM Review Committee (2 buyer + 2 seller representatives) shall convene within 7 days of any FM notice. Disputes unresolved within 30 days shall proceed to ICC arbitration.",
            'concession': "Buyer concedes: accepts seller's 90-day relief cap with mutual termination rights thereafter.",
        },
    ],
    'seller': [
        {
            'stance': 'narrow_coverage',
            'demand': "Strict definition — only direct {event} preventing performance",
            'position': "Seller counters: FM relief only for direct {event} that makes performance physically impossible, not merely uneconomic. Seller proposes 90-day maximum FM relief period before termination rights arise.",
            'clause_fragment': "Force Majeure shall be strictly limited to {event} events that directly and physically prevent performance. Economic hardship, cost increases, or foreseeable supply disruptions shall not qualify.",
            'concession': None,
        },
        {
            'stance': 'resist_liability_cap',
            'demand': "No liability cap — full exclusion during FM",
            'position': "Seller rejects buyer's liability cap proposal. Seller's position: complete exclusion of liability during documented {event} FM events. Seller will accept shared costs only for events exceeding 60 days.",
            'clause_fragment': "Seller shall have no liability for any losses, costs, or damages arising during a qualifying {event} FM event. Shared cost mechanisms apply only where FM duration exceeds 60 days.",
            'concession': "Seller concedes: accepts 7-day (not 14-day) notification window for operational feasibility.",
        },
        {
            'stance': 'final_position',
            'demand': "90-day cap + automatic termination right",
            'position': "Seller final position: 90-day FM cap is non-negotiable. After 90 days either party may terminate without penalty. Seller accepts joint FM committee but only as advisory, not binding.",
            'clause_fragment': "After 90 consecutive days of FM relief, either party may terminate this contract upon 14 days written notice without penalty, liability, or damages to either party.",
            'concession': "Seller concedes: accepts ICC arbitration for disputes but requires Singapore seat of arbitration.",
        },
    ],
    'insurer': [
        {
            'stance': 'define_triggers',
            'demand': "Certified trigger documentation within 14 days",
            'position': "Insurer requires: (1) Certification from recognized body that {event} directly caused performance failure, (2) 14-day notification, (3) Best-efforts mitigation obligation throughout FM period.",
            'clause_fragment': "FM invocation requires: (i) Written notice within 14 days; (ii) Certification from a recognized governmental or industry body confirming {event}; (iii) Documented evidence of direct causal link to performance failure.",
            'concession': None,
        },
        {
            'stance': 'coverage_conditions',
            'demand': "Insurance coverage conditional on mitigation evidence",
            'position': "Insurer escalates: Insurance coverage for {event} FM losses conditional on proof of mitigation efforts. Insurer will require monthly status reports during FM period. Any failure to mitigate voids FM protection.",
            'clause_fragment': "Insurance coverage during {event} FM events is conditional upon: (i) Monthly mitigation progress reports; (ii) Evidence of alternative sourcing efforts; (iii) Demonstrated best-efforts to resume performance.",
            'concession': "Insurer concedes: accepts 21-day notification window for remote/war-zone {event} events.",
        },
        {
            'stance': 'final_coverage_terms',
            'demand': "Standardized FM clause per ICC model",
            'position': "Insurer final position: Recommends adoption of ICC Force Majeure Clause 2020 as base. Coverage capped at 80% of contract value for {event} losses. Deductible of 5% applies.",
            'clause_fragment': "This Force Majeure clause shall be interpreted in accordance with ICC Force Majeure Clause 2020 standards. Insurance coverage for qualifying {event} events is capped at 80% of contract value with a 5% deductible.",
            'concession': "Insurer concedes: waives deductible for catastrophic {event} events (severity >7.0 on applicable scale).",
        },
    ],
    'legal': [
        {
            'stance': 'ensure_enforceability',
            'demand': "Precise legal definitions per {buyer_juris} law",
            'position': "Legal counsel requires: precise legal definition of {event} per {buyer_juris} statutory law, ICC arbitration clause, explicit governing law provision, and documented evidence requirements meeting court evidentiary standards.",
            'clause_fragment': "For purposes of this Agreement, '{event}' shall have the meaning ascribed to it under {buyer_juris} law and applicable international conventions. Any dispute shall be resolved by ICC arbitration, seat: Singapore, language: English.",
            'concession': None,
        },
        {
            'stance': 'jurisdictional_alignment',
            'demand': "Align {buyer_juris} and {seller_juris} legal standards",
            'position': "Legal escalates: Given {buyer_juris} vs {seller_juris} jurisdictional conflict on {event} definition, recommend incorporation of UNIDROIT Principles. Both parties must agree on a neutral governing law.",
            'clause_fragment': "In the event of conflict between {buyer_juris} and {seller_juris} law on the definition or scope of {event}, the UNIDROIT Principles of International Commercial Contracts 2016 shall govern interpretation.",
            'concession': "Legal concedes: accepts Singapore law as neutral governing law for FM provisions.",
        },
        {
            'stance': 'final_legal_framework',
            'demand': "Comprehensive FM protocol with legal safeguards",
            'position': "Legal final position: FM clause must include (1) precise event definitions, (2) notice procedures, (3) mitigation obligations, (4) termination rights, (5) governing law, and (6) dispute resolution. All six elements are non-negotiable for enforceability.",
            'clause_fragment': "The FM clause shall be deemed legally enforceable only when it contains: defined triggering events, notice timelines, mitigation duties, relief duration, termination rights, and a dispute resolution mechanism compliant with {buyer_juris} law.",
            'concession': "Legal concedes: accepts 30-day (not 14-day) cure period before FM formally invoked.",
        },
    ],
    'finance': [
        {
            'stance': 'protect_cash_flow',
            'demand': "Payment suspension + 15% cost cap during {event}",
            'position': "Finance team requires: automatic payment suspension rights during {event} FM events, cost escalation cap of 15% above contract price, advance payment protection via bank guarantees, and detailed cost documentation.",
            'clause_fragment': "Upon FM invocation: (i) All payments suspended within 48 hours; (ii) Cost increases capped at 15% of original contract price; (iii) Advance payments protected by irrevocable bank guarantee; (iv) All FM-related costs documented monthly.",
            'concession': None,
        },
        {
            'stance': 'exposure_mitigation',
            'demand': "Escrow account for FM losses + force majeure insurance",
            'position': "Finance escalates: For contract value ${cv_m}M, a dedicated FM escrow account of 5% contract value required. Parties must maintain FM insurance covering minimum 60% of contract value. Monthly exposure reporting mandatory.",
            'clause_fragment': "Parties shall establish a joint FM Escrow Account equal to 5% of contract value within 30 days of signing. Each party shall maintain FM business interruption insurance covering minimum 60% of their contract exposure.",
            'concession': "Finance concedes: accepts phased escrow funding (2.5% at signing, 2.5% at project midpoint).",
        },
        {
            'stance': 'final_financial_terms',
            'demand': "Agreed FM cost-sharing formula",
            'position': "Finance final position: FM costs beyond 30 days split 60/40 (seller/buyer) for {event} events in seller's jurisdiction. Buyer bears 100% for events in buyer's jurisdiction. Mutual events split 50/50.",
            'clause_fragment': "FM cost-sharing: (i) Events in Seller's jurisdiction ({seller_juris}): 60% Seller / 40% Buyer; (ii) Events in Buyer's jurisdiction ({buyer_juris}): 100% Buyer; (iii) Global/mutual events: 50% each party.",
            'concession': "Finance concedes: accepts seller's request to exclude indirect costs from FM cost-sharing formula.",
        },
    ],
}

# Consensus summaries per round — what the mediator synthesizes
_CONSENSUS_SUMMARIES = [
    "Round 1 establishes opening positions. Buyer seeks broad coverage; Seller seeks narrow definition. Insurer sets documentation requirements. Legal flags jurisdictional conflicts. Finance demands payment suspension.",
    "Round 2 escalates key conflicts. Buyer-Seller gap narrows on liability cap vs. full exclusion. Insurer introduces coverage conditions. Legal recommends UNIDROIT as neutral framework. Finance proposes FM escrow.",
    "Round 3 reaches final positions. All parties converge on: ICC arbitration, 90-day FM cap, joint FM committee, 14-21 day notification window, and cost-sharing formula. Consensus clause drafted.",
]

# Final synthesized FM clauses per round accepted
_FINAL_CLAUSE_TEMPLATE = """FORCE MAJEURE CLAUSE — NEGOTIATED AGREEMENT
(Effective upon execution by all parties)

1. DEFINITION
"Force Majeure Event" means {event_def}, including but not limited to: {event_examples}. Economic hardship or foreseeable supply disruptions do not qualify unless directly caused by a qualifying event.

2. NOTIFICATION
The affected party shall provide written notice within {notice_days} days of the FM event occurrence, including: (a) description of the event; (b) expected impact on performance; (c) certification from a recognized authority; (d) estimated duration.

3. RELIEF & DURATION
Upon valid FM invocation: (a) Performance obligations suspended for up to 90 days; (b) Payment obligations suspended within 48 hours of notice; (c) After 90 days, either party may terminate upon 14 days written notice without penalty.

4. MITIGATION OBLIGATIONS
The affected party must: (a) Use best efforts to resume performance; (b) Submit monthly mitigation progress reports; (c) Explore alternative sourcing/performance routes; (d) Failure to mitigate voids FM protection.

5. COST SHARING
FM costs beyond 30 days: {cost_share}. An FM Escrow Account equal to 5% of contract value ({cv_escrow}) shall be funded within 30 days of signing.

6. INSURANCE
Each party shall maintain FM business interruption insurance covering minimum 60% of contract exposure. Coverage per ICC Force Majeure Clause 2020, capped at 80% of contract value, 5% deductible.

7. GOVERNING LAW & DISPUTE RESOLUTION
This FM clause is governed by {governing_law}. Disputes unresolved within 30 days proceed to ICC arbitration, seat: Singapore, language: English. A joint FM Review Committee (2 representatives per party) convenes within 7 days of any FM notice.

8. LIABILITY CAP
During a qualifying FM event, each party's liability is capped at 10% of contract value ({cv_cap}). Consequential damages are excluded.
"""


def _build_final_clause(event: str, buyer_juris: str, seller_juris: str, contract_value: float) -> str:
    event_defs = {
        'war': 'armed conflict, hostilities, invasion, military operations, or acts of war declared or undeclared',
        'factory_shutdown': 'government-mandated or force-induced closure of manufacturing or production facilities',
        'trade_sanctions': 'governmental or intergovernmental economic sanctions, trade embargoes, or export/import restrictions',
        'pandemic': 'epidemic or pandemic disease declared by the WHO or national health authority',
        'natural_disaster': 'earthquake, flood, hurricane, typhoon, or other natural catastrophe of unusual severity',
        'cyber_warfare': 'state-sponsored or criminal cyberattack rendering critical systems inoperable',
        'port_closure': 'closure of key ports, shipping lanes, or critical transport infrastructure',
        'energy_crisis': 'systemic failure or government-imposed restriction of energy supply',
        'commodity_shock': 'extreme commodity price movement exceeding 40% within 90 days making performance uneconomic',
    }
    event_examples = {
        'war': 'military strikes, blockades, conscription of personnel, destruction of facilities',
        'factory_shutdown': 'regulatory shutdown orders, safety closures, environmental enforcement',
        'trade_sanctions': 'OFAC sanctions, EU trade restrictions, export control regulations',
        'pandemic': 'COVID-19 type events, government lockdowns, border closures',
        'natural_disaster': 'Richter 6.0+ earthquakes, Category 3+ hurricanes, major flooding',
        'cyber_warfare': 'ransomware attacks on SCADA/ERP systems, infrastructure attacks',
        'port_closure': 'Suez/Panama Canal closure, Taiwan Strait blockade, port strikes',
        'energy_crisis': 'grid failures, gas supply cutoffs, fuel rationing',
        'commodity_shock': 'semiconductor shortage, rare earth export bans, steel price spikes',
    }
    cost_share = f"60% {seller_juris} Seller / 40% {buyer_juris} Buyer for events in Seller's jurisdiction; 50/50 for global events"
    cv_escrow = f"${contract_value * 0.05:,.0f}" if contract_value else "5% of contract value"
    cv_cap = f"${contract_value * 0.10:,.0f}" if contract_value else "10% of contract value"
    governing_law = f"Singapore law (as neutral jurisdiction between {buyer_juris} and {seller_juris})"
    return _FINAL_CLAUSE_TEMPLATE.format(
        event_def=event_defs.get(event, f'{event.replace("_"," ")} events and related disruptions'),
        event_examples=event_examples.get(event, f'{event.replace("_"," ")} and directly related sub-events'),
        notice_days=14,
        cost_share=cost_share,
        cv_escrow=cv_escrow,
        cv_cap=cv_cap,
        governing_law=governing_law,
    )


def _agent_propose(agent: dict, current_clause: str, strength: float, event: str, cv: float, round_num: int) -> dict:
    """Generates escalating per-round agent proposals with unique content each round."""
    role = agent['role']
    rt = agent['risk_tolerance']
    round_idx = min(round_num - 1, 2)  # cap at index 2 (3 rounds defined)

    role_rounds = _ROUND_ESCALATION.get(role, _ROUND_ESCALATION['buyer'])
    rd = role_rounds[round_idx]

    buyer_juris = agent.get('jurisdiction', 'the applicable jurisdiction')
    seller_juris = agent.get('jurisdiction', 'the seller jurisdiction')
    cv_m = f"{cv/1_000_000:.0f}" if cv >= 1_000_000 else f"{cv:,.0f}"

    stance = rd['stance']
    demand = rd['demand'].format(event=event.replace('_',' '), buyer_juris=buyer_juris, seller_juris=seller_juris, cv_m=cv_m)
    position = rd['position'].format(event=event.replace('_',' '), buyer_juris=buyer_juris, seller_juris=seller_juris, cv_m=cv_m)
    clause_fragment = rd['clause_fragment'].format(event=event.replace('_',' '), buyer_juris=buyer_juris, seller_juris=seller_juris, cv_m=cv_m)
    concession = rd.get('concession')
    if concession:
        concession = concession.format(event=event.replace('_',' '), buyer_juris=buyer_juris, seller_juris=seller_juris)

    # Strength delta: buyers improve, sellers reduce, others neutral/small positive
    strength_deltas = {'buyer': 0.08, 'insurer': 0.04, 'legal': 0.05, 'finance': 0.03, 'seller': -0.03}
    proposed_strength = min(1.0, strength + strength_deltas.get(role, 0.03))

    return {
        'agent': agent['name'],
        'role': role,
        'stance': stance,
        'demand': demand,
        'position': position,
        'clause_fragment': clause_fragment,
        'concession': concession,
        'proposed_clause': clause_fragment,
        'estimated_strength': round(proposed_strength, 4),
        'risk_tolerance': rt,
        'win_probability': round(0.5 + (0.5 - rt) * 0.4 + (round_idx * 0.05), 2),
    }


def _mediator_decide(proposals: list, current_strength: float) -> dict:
    """Picks the proposal that best improves clause strength (mediator favours coverage expansion)."""
    positive_roles = {'buyer', 'legal', 'insurer'}
    positive_proposals = [p for p in proposals if p.get('role') in positive_roles]
    candidates = positive_proposals if positive_proposals else proposals
    best = max(candidates, key=lambda p: p.get('estimated_strength', 0))
    return best


# ═══════════════════════════════════════════════════════════════════════════════
# 6. SUPPLY CHAIN RISK MAP
# ═══════════════════════════════════════════════════════════════════════════════
class FMSupplyChainMapView(APIView):
    """
    POST /api/force-majeure/supply-chain-map/
    Returns supply chain risk data with live disruption scores, personalised to the contract.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        return self.post(request)

    def post(self, request) -> Response:
        contract_text       = request.data.get('contract_text', '')
        project_location    = request.data.get('project_location', '')
        supplier_locations  = request.data.get('supplier_locations', '')
        jurisdiction        = request.data.get('jurisdiction', '')
        industry            = request.data.get('industry', '')

        # Combine all location hints into a searchable string
        all_locations = ' '.join([
            contract_text[:3000],   # first 3k chars of contract usually has supplier names
            project_location,
            supplier_locations,
            jurisdiction,
            industry,
        ]).lower()

        # Fetch live events for disruption scoring
        live_disruptions = {}
        try:
            from .live_data_engine import fetch_all_live_events
            ld = fetch_all_live_events()
            for ev in ld.get('events', []):
                loc = ev.get('location', '').lower()
                rs = ev.get('risk_score', 0)
                live_disruptions[loc] = max(live_disruptions.get(loc, 0), rs)
        except Exception:
            pass

        # Major trade routes
        routes = [
            {
                'id': 'suez_canal', 'name': 'Suez Canal', 'region': 'Middle East',
                'from': 'Asia', 'to': 'Europe', 'base_risk': 0.65,
                'keywords': ['suez', 'red sea', 'egypt', 'houthis'],
                'cargo_value_bday': 9_600_000_000,
                'lat': 30.5, 'lon': 32.3,
            },
            {
                'id': 'strait_hormuz', 'name': 'Strait of Hormuz', 'region': 'Persian Gulf',
                'from': 'Persian Gulf', 'to': 'Indian Ocean', 'base_risk': 0.70,
                'keywords': ['hormuz', 'iran', 'persian gulf', 'tanker'],
                'cargo_value_bday': 1_600_000_000,
                'lat': 26.5, 'lon': 56.2,
            },
            {
                'id': 'black_sea', 'name': 'Black Sea Route', 'region': 'Eastern Europe',
                'from': 'Ukraine/Russia', 'to': 'EU/Turkey', 'base_risk': 0.80,
                'keywords': ['black sea', 'ukraine', 'russia', 'odessa'],
                'cargo_value_bday': 400_000_000,
                'lat': 43.0, 'lon': 34.0,
            },
            {
                'id': 'south_china_sea', 'name': 'South China Sea', 'region': 'Asia Pacific',
                'from': 'China/Southeast Asia', 'to': 'Pacific', 'base_risk': 0.55,
                'keywords': ['south china sea', 'taiwan', 'spratly', 'paracel'],
                'cargo_value_bday': 5_300_000_000,
                'lat': 12.0, 'lon': 114.0,
            },
            {
                'id': 'panama_canal', 'name': 'Panama Canal', 'region': 'Central America',
                'from': 'Pacific', 'to': 'Atlantic', 'base_risk': 0.30,
                'keywords': ['panama', 'canal', 'drought', 'central america'],
                'cargo_value_bday': 800_000_000,
                'lat': 9.1, 'lon': -79.6,
            },
            {
                'id': 'strait_malacca', 'name': 'Strait of Malacca', 'region': 'Southeast Asia',
                'from': 'Indian Ocean', 'to': 'Pacific', 'base_risk': 0.35,
                'keywords': ['malacca', 'singapore', 'piracy', 'indonesia'],
                'cargo_value_bday': 3_400_000_000,
                'lat': 2.5, 'lon': 102.0,
            },
            {
                'id': 'cape_good_hope', 'name': 'Cape of Good Hope', 'region': 'Southern Africa',
                'from': 'Atlantic', 'to': 'Indian Ocean', 'base_risk': 0.25,
                'keywords': ['cape', 'south africa', 'good hope'],
                'cargo_value_bday': 200_000_000,
                'lat': -34.3, 'lon': 18.5,
            },
        ]

        # ── Contract location matching keywords ───────────────────────────────
        # Map each route to the location/supplier keywords that would appear in a contract
        route_contract_keywords = {
            'suez_canal':     ['suez', 'red sea', 'egypt', 'netherlands', 'europe', 'rotterdam', 'hamburg', 'asml', 'basf', 'merck', 'germany', 'france'],
            'strait_hormuz':  ['hormuz', 'iran', 'gulf', 'saudi', 'uae', 'dubai', 'qatar', 'oil', 'energy', 'lng', 'middle east'],
            'black_sea':      ['black sea', 'ukraine', 'russia', 'odessa', 'grain', 'wheat', 'steel', 'posco', 'nippon'],
            'south_china_sea':['south china sea', 'taiwan', 'china', 'hsinchu', 'tsmc', 'asml', 'samsung', 'korea', 'japan', 'tokyo electron', 'shin-etsu', 'globalwafers', 'jsr', 'kaohsiung', 'pacific'],
            'panama_canal':   ['panama', 'pacific', 'atlantic', 'san francisco', 'usa', 'united states', 'american'],
            'strait_malacca': ['malacca', 'singapore', 'malaysia', 'indonesia', 'indian ocean', 'southeast asia', 'air liquide', 'specialty gas'],
            'cape_good_hope': ['cape', 'south africa', 'good hope', 'alternative route'],
        }

        # Score routes from live data AND contract matching
        for route in routes:
            live_boost = 0.0
            for kw in route['keywords']:
                boost = live_disruptions.get(kw, 0)
                live_boost = max(live_boost, boost)
            route['live_risk'] = round(min(1.0, route['base_risk'] + live_boost * 0.3), 4)
            route['disruption_pct'] = round(route['live_risk'] * 100, 1)
            route['status'] = 'DISRUPTED' if route['live_risk'] > 0.65 else 'ELEVATED' if route['live_risk'] > 0.40 else 'NORMAL'
            route['color'] = '#F16667' if route['live_risk'] > 0.65 else '#F79767' if route['live_risk'] > 0.40 else '#68BC00'

            # Check if this route is relevant to the pasted contract
            contract_kws = route_contract_keywords.get(route['id'], [])
            matched_kws = [kw for kw in contract_kws if kw in all_locations]
            route['contract_relevant'] = len(matched_kws) > 0
            route['matched_keywords'] = matched_kws[:5]  # top 5 matched terms

        # ── Contract-specific supplier hub detection ──────────────────────────
        all_supplier_hubs = [
            {'id': 'taiwan',     'name': 'Taiwan Semiconductor Hub',  'risk': 0.60, 'lat': 25.1,  'lon': 121.6, 'type': 'Semiconductors',   'keywords': ['taiwan', 'tsmc', 'hsinchu', 'kaohsiung', 'globalwafers', 'shin-etsu']},
            {'id': 'netherlands','name': 'Netherlands Tech Hub',       'risk': 0.25, 'lat': 52.4,  'lon': 4.9,   'type': 'High-Tech Equip', 'keywords': ['netherlands', 'asml', 'rotterdam', 'amsterdam']},
            {'id': 'japan',      'name': 'Japan Precision Mfg Hub',   'risk': 0.30, 'lat': 35.7,  'lon': 139.7, 'type': 'Precision Mfg',   'keywords': ['japan', 'tokyo', 'tokyo electron', 'shin-etsu', 'jsr', 'yokohama']},
            {'id': 'south_korea','name': 'South Korea Electronics Hub','risk': 0.35, 'lat': 37.5,  'lon': 127.0, 'type': 'Electronics',     'keywords': ['korea', 'samsung', 'busan', 'posco', 'sk hynix']},
            {'id': 'usa',        'name': 'USA Materials Hub',          'risk': 0.25, 'lat': 37.7,  'lon': -122.4,'type': 'Materials/Chem',  'keywords': ['usa', 'united states', 'san francisco', 'applied materials', 'dupont']},
            {'id': 'germany',    'name': 'Germany Industrial Hub',     'risk': 0.22, 'lat': 52.5,  'lon': 13.4,  'type': 'Industrial',      'keywords': ['germany', 'basf', 'merck', 'hamburg', 'munich']},
            {'id': 'france',     'name': 'France Specialty Gas Hub',   'risk': 0.22, 'lat': 48.9,  'lon': 2.3,   'type': 'Specialty Chem',  'keywords': ['france', 'air liquide', 'linde', 'paris']},
            {'id': 'ukraine',    'name': 'Ukraine Grain/Steel Hub',    'risk': 0.85, 'lat': 50.4,  'lon': 30.5,  'type': 'Commodity',       'keywords': ['ukraine', 'odessa', 'grain', 'wheat', 'steel']},
            {'id': 'saudi',      'name': 'Saudi Arabia Oil Hub',       'risk': 0.50, 'lat': 24.7,  'lon': 46.7,  'type': 'Energy',          'keywords': ['saudi', 'aramco', 'oil', 'gulf', 'riyadh']},
            {'id': 'india',      'name': 'India IT/Pharma Hub',        'risk': 0.30, 'lat': 19.1,  'lon': 72.9,  'type': 'IT/Pharma',       'keywords': ['india', 'mumbai', 'bangalore', 'pharma', 'infosys']},
            {'id': 'china',      'name': 'China Manufacturing Hub',    'risk': 0.45, 'lat': 31.2,  'lon': 121.5, 'type': 'Manufacturing',   'keywords': ['china', 'beijing', 'shanghai', 'shenzhen', 'foxconn']},
            {'id': 'singapore',  'name': 'Singapore Logistics Hub',    'risk': 0.28, 'lat': 1.35,  'lon': 103.8, 'type': 'Logistics',       'keywords': ['singapore', 'port of singapore', 'changi']},
        ]

        # Mark hubs active in contract
        contract_hubs = []
        for hub in all_supplier_hubs:
            matched = [kw for kw in hub['keywords'] if kw in all_locations]
            if matched:
                hub = dict(hub)
                hub['contract_active'] = True
                hub['matched_on'] = matched[:3]
            else:
                hub = dict(hub)
                hub['contract_active'] = False
                hub['matched_on'] = []
            contract_hubs.append(hub)

        contract_relevant_routes = [r for r in routes if r['contract_relevant']]
        contract_hubs_active = [h for h in contract_hubs if h['contract_active']]

        # ── Contract FM exposure from supply chain ────────────────────────────
        total_daily_at_risk = sum(
            r['cargo_value_bday'] for r in contract_relevant_routes if r['status'] in ('DISRUPTED', 'ELEVATED')
        )
        contract_route_fm_boost = min(0.4, len([r for r in contract_relevant_routes if r['status'] == 'DISRUPTED']) * 0.12
                                      + len([r for r in contract_relevant_routes if r['status'] == 'ELEVATED']) * 0.06)

        disrupted_routes = [r for r in routes if r['status'] == 'DISRUPTED']
        elevated_routes  = [r for r in routes if r['status'] == 'ELEVATED']

        return Response({
            'trade_routes': routes,
            'supplier_hubs': contract_hubs,
            'contract_relevant_routes': contract_relevant_routes,
            'contract_active_hubs': contract_hubs_active,
            'contract_analysis': {
                'has_contract': bool(contract_text or project_location or supplier_locations),
                'relevant_route_count': len(contract_relevant_routes),
                'active_hub_count': len(contract_hubs_active),
                'disrupted_relevant_routes': [r['name'] for r in contract_relevant_routes if r['status'] == 'DISRUPTED'],
                'elevated_relevant_routes':  [r['name'] for r in contract_relevant_routes if r['status'] == 'ELEVATED'],
                'total_daily_trade_at_risk_usd': total_daily_at_risk,
                'fm_probability_boost': round(contract_route_fm_boost, 3),
                'supply_chain_verdict': (
                    'CRITICAL' if contract_route_fm_boost > 0.25 else
                    'HIGH'     if contract_route_fm_boost > 0.15 else
                    'MEDIUM'   if contract_route_fm_boost > 0.05 else
                    'LOW'
                ),
                'project_location': project_location,
                'supplier_locations': supplier_locations,
            },
            'summary': {
                'total_routes': len(routes),
                'disrupted_routes': len(disrupted_routes),
                'elevated_routes':  len(elevated_routes),
                'normal_routes':    len(routes) - len(disrupted_routes) - len(elevated_routes),
                'highest_risk_route': max(routes, key=lambda r: r['live_risk'])['name'],
                'avg_disruption_pct': round(sum(r['disruption_pct'] for r in routes) / len(routes), 1),
            },
            'live_data_applied': len(live_disruptions) > 0,
        })


# ═══════════════════════════════════════════════════════════════════════════════
# 7. DYNAMIC BAYESIAN PRIOR UPDATE (Live event → prior boost)
# ═══════════════════════════════════════════════════════════════════════════════
class FMDynamicPriorsView(APIView):
    """
    GET /api/force-majeure/dynamic-priors/
    Returns how live events shift Bayesian priors for each node.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        from .live_data_engine import fetch_all_live_events
        from .bayesian_engine import update_priors_from_live_events, BASE_PRIORS
        try:
            live_events = fetch_all_live_events().get('events', [])
        except Exception:
            live_events = []

        prior_updates = update_priors_from_live_events(live_events)

        # Build summary of top movers
        movers = sorted(
            [
                {
                    'node': node,
                    'base_prior': round(data['base_prior'], 4),
                    'updated_prior': round(data['updated_prior'], 4),
                    'delta': round(data['delta'], 4),
                    'pct_change': round(data['pct_change'], 1),
                    'source_events': data['source_events'],
                }
                for node, data in prior_updates.items()
                if data['delta'] > 0.001
            ],
            key=lambda x: -x['delta'],
        )

        return Response({
            'prior_updates': prior_updates,
            'top_movers': movers[:10],
            'live_events_count': len(live_events),
            'nodes_boosted': len([m for m in movers if m['delta'] > 0]),
            'base_priors': BASE_PRIORS,
        })


# ═══════════════════════════════════════════════════════════════════════════════
# 8. RISK CASCADE VIEW (4-stage propagation React Flow graph)
# ═══════════════════════════════════════════════════════════════════════════════
class FMRiskCascadeView(APIView):
    """
    POST /api/force-majeure/risk-cascade/
    Body: { evidence: {node: prob}, contract_value: float }
    Returns React-Flow compatible nodes/edges for 4-stage cascade.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        from .bayesian_engine import compute_risk_cascade
        evidence = request.data.get('evidence', {})
        contract_value = float(request.data.get('contract_value', 1_000_000))

        if not evidence:
            # Use default war-scenario evidence
            evidence = {'war': 0.7, 'trade_sanctions': 0.6, 'energy_crisis': 0.5}

        try:
            result = compute_risk_cascade(evidence, contract_value)
            return Response(result)
        except Exception as exc:
            logger.exception('Risk cascade error')
            return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════════════════════════════════════════
# 9. COUNTERFACTUAL CLAUSE OPTIMIZER
# ═══════════════════════════════════════════════════════════════════════════════
class FMClauseOptimizerView(APIView):
    """
    POST /api/force-majeure/clause-optimizer/
    Tests adding protective FM clause types and measures risk reduction.
    Body: { evidence: {node: prob}, contract_value: float }
    """
    permission_classes = [IsAuthenticated]

    CLAUSE_PROTECTIONS = {
        'SanctionsProtectionClause': {'trade_sanctions': -0.30, 'sanctions_expansion': -0.25},
        'PandemicProtectionClause': {'pandemic': -0.35, 'epidemic': -0.25, 'port_closure': -0.15},
        'AlternativeSupplierClause': {'supplier_bankruptcy': -0.40, 'logistics_disruption': -0.30},
        'ForceDisruptionClause': {'hurricane': -0.20, 'earthquake': -0.20, 'flood': -0.20, 'wildfire': -0.15},
        'WarEscalationClause': {'war': -0.30, 'regional_conflict': -0.25, 'terrorism': -0.20},
        'EnergyShortageClause': {'energy_crisis': -0.35, 'energy_price_spike': -0.30},
        'PoliticalRiskClause': {'political_coup': -0.30, 'civil_unrest_spread': -0.25},
        'CurrencyRiskClause': {'currency_volatility': -0.30, 'economic_collapse': -0.20},
        'CyberForceClause': {'cyber_warfare': -0.40, 'infrastructure_disruption': -0.30},
        'CompositeShieldClause': {
            'war': -0.20, 'pandemic': -0.20, 'trade_sanctions': -0.20,
            'earthquake': -0.15, 'hurricane': -0.15, 'energy_crisis': -0.20,
        },
    }

    def post(self, request) -> Response:
        from .bayesian_engine import get_fm_bayesian_engine
        engine = get_fm_bayesian_engine()
        evidence = {k: float(v) for k, v in request.data.get('evidence', {}).items()}
        contract_value = float(request.data.get('contract_value', 1_000_000))

        if not evidence:
            evidence = {'war': 0.6, 'trade_sanctions': 0.5}

        baseline_risk = engine.compute_fm_risk_score(evidence)

        results = []
        for clause_name, reductions in self.CLAUSE_PROTECTIONS.items():
            modified_ev = dict(evidence)
            for node, delta in reductions.items():
                if node in modified_ev:
                    modified_ev[node] = max(0.01, modified_ev[node] + delta)
            new_risk = engine.compute_fm_risk_score(modified_ev)
            reduction = baseline_risk - new_risk
            results.append({
                'clause': clause_name,
                'baseline_risk': round(baseline_risk, 4),
                'new_risk': round(new_risk, 4),
                'risk_reduction': round(reduction, 4),
                'risk_reduction_pct': round(reduction / max(baseline_risk, 0.001) * 100, 1),
                'loss_saved_usd': round(reduction * contract_value * 0.35, 0),
                'recommendation': 'STRONGLY RECOMMENDED' if reduction > 0.15 else 'RECOMMENDED' if reduction > 0.07 else 'OPTIONAL',
                'nodes_affected': list(reductions.keys()),
            })

        results.sort(key=lambda x: -x['risk_reduction'])

        return Response({
            'baseline_risk': round(baseline_risk, 4),
            'contract_value': contract_value,
            'clause_recommendations': results,
            'top_recommendation': results[0]['clause'] if results else '',
            'max_possible_reduction': round(results[0]['risk_reduction'], 4) if results else 0,
        })


# ═══════════════════════════════════════════════════════════════════════════════
# 10. TEMPORAL DBN FORECAST (12-month)
# ═══════════════════════════════════════════════════════════════════════════════
class FMTemporalForecastView(APIView):
    """
    POST /api/force-majeure/temporal-forecast/
    Body: { evidence: {node: prob}, start_month: int (1-12) }
    Returns 12-month Bayesian risk forecast with seasonal boosts.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        from .bayesian_engine import compute_temporal_forecast
        evidence = {k: float(v) for k, v in request.data.get('evidence', {}).items()}
        start_month = int(request.data.get('start_month', 1))

        if not evidence:
            evidence = {'war': 0.5, 'trade_sanctions': 0.4}

        try:
            forecast = compute_temporal_forecast(evidence, start_month)
            peak = max(forecast, key=lambda m: m['fm_risk'])
            trough = min(forecast, key=lambda m: m['fm_risk'])

            return Response({
                'forecast': forecast,
                'peak_month': peak,
                'trough_month': trough,
                'avg_risk': round(sum(m['fm_risk'] for m in forecast) / len(forecast), 4),
                'months_high_risk': len([m for m in forecast if m['risk_label'] == 'HIGH']),
            })
        except Exception as exc:
            logger.exception('Temporal forecast error')
            return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════════════════════════════════════════
# 11. RISK FORMULA BREAKDOWN
# ═══════════════════════════════════════════════════════════════════════════════
class FMRiskFormulaView(APIView):
    """
    POST /api/force-majeure/risk-formula/
    Body: { evidence: {node: prob} }
    Returns weighted outcome contributions and per-event sensitivity.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        from .bayesian_engine import compute_risk_formula_breakdown
        evidence = {k: float(v) for k, v in request.data.get('evidence', {}).items()}

        if not evidence:
            evidence = {'war': 0.6, 'pandemic': 0.4, 'trade_sanctions': 0.5}

        try:
            breakdown = compute_risk_formula_breakdown(evidence)
            return Response(breakdown)
        except Exception as exc:
            logger.exception('Risk formula breakdown error')
            return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════════════════════════════════════════
# 12. BULK AUTO-CORRECT GRID
# ═══════════════════════════════════════════════════════════════════════════════
class FMBulkAutoCorrectView(APIView):
    """
    POST /api/force-majeure/bulk-auto-correct/
    Body: { clauses: [{id, text, type}] }
    Audits all clauses, returns grid with status + auto-fix suggestion per row.
    """
    permission_classes = [IsAuthenticated]

    STRONG_INDICATORS = [
        'natural disaster', 'act of god', 'war', 'pandemic', 'epidemic',
        'government action', 'force majeure', 'unforeseeable', 'beyond reasonable control',
        'notification within', 'mitigation obligations', 'excuse performance',
    ]
    WEAK_INDICATORS = [
        'circumstances beyond', 'unexpected event', 'inability to perform',
        'delay', 'disruption',
    ]
    AUTO_FIXES = {
        'missing': 'Add: "Neither party shall be liable for delay or failure to perform obligations resulting from causes beyond its reasonable control, including but not limited to acts of God, war, pandemic, government actions, or natural disasters, provided the affected party gives prompt written notice and uses reasonable efforts to mitigate."',
        'weak': 'Strengthen by adding: explicit enumeration of FM events, notification timeline (within 48-72 hours), mitigation obligations, and a sunset clause (e.g., termination right after 90 days of FM).',
        'strong': 'Clause meets standard FM requirements. Consider adding jurisdiction-specific carve-outs if applicable.',
    }

    def post(self, request) -> Response:
        from .fm_service import audit_fm_clause
        clauses = request.data.get('clauses', [])
        if not clauses:
            return Response({'error': 'No clauses provided'}, status=status.HTTP_400_BAD_REQUEST)

        grid_rows = []
        stats = {'strong': 0, 'weak': 0, 'missing': 0}

        for clause in clauses:
            text = clause.get('text', '')
            clause_type = clause.get('type', 'GENERAL')
            text_lower = text.lower()

            strong_hits = sum(1 for kw in self.STRONG_INDICATORS if kw in text_lower)
            weak_hits = sum(1 for kw in self.WEAK_INDICATORS if kw in text_lower)

            if strong_hits >= 3:
                fm_status = 'strong'
                color = '#68BC00'
            elif strong_hits >= 1 or weak_hits >= 2:
                fm_status = 'weak'
                color = '#F79767'
            else:
                fm_status = 'missing'
                color = '#F16667'

            stats[fm_status] += 1

            grid_rows.append({
                'id': clause.get('id', ''),
                'type': clause_type,
                'text_preview': text[:150] + '...' if len(text) > 150 else text,
                'full_text': text[:400] + '...' if len(text) > 400 else text,  # Limited to 400 chars
                'fm_status': fm_status,
                'color': color,
                'strong_indicators_found': strong_hits,
                'weak_indicators_found': weak_hits,
                'auto_fix': self.AUTO_FIXES[fm_status],
                'priority': 'HIGH' if fm_status == 'missing' else 'MEDIUM' if fm_status == 'weak' else 'LOW',
            })

        grid_rows.sort(key=lambda r: {'missing': 0, 'weak': 1, 'strong': 2}[r['fm_status']])

        return Response({
            'grid': grid_rows,
            'stats': stats,
            'total_clauses': len(clauses),
            'coverage_score': round(stats['strong'] / max(len(clauses), 1) * 100, 1),
            'risk_score': round((stats['missing'] * 2 + stats['weak']) / max(len(clauses) * 2, 1) * 100, 1),
        })


# ═══════════════════════════════════════════════════════════════════════════════
# NEW ADVANCED FEATURES - LLM CLAUSE REWRITING
# ═══════════════════════════════════════════════════════════════════════════════
class FMLLMClauseRewriteView(APIView):
    """
    POST /api/force-majeure/llm-clause-rewrite/
    Use LLM (GPT-4) to intelligently rewrite weak FM clauses
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .llm_service import llm_clause_service
        except ImportError:
            return Response({'error': 'LLM service not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        existing_clause = data.get('existing_clause', '')
        missing_events = data.get('missing_events', [])
        weak_events = data.get('weak_events', [])
        contract_value = data.get('contract_value')
        jurisdiction = data.get('jurisdiction')

        if not existing_clause:
            return Response({'error': 'existing_clause required'}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare weakness analysis
        weakness_analysis = {
            'missing_events': missing_events,
            'weak_events': weak_events,
            'vague_language': 'General weakness detected'
        }

        improvements = [
            f"Add coverage for: {', '.join(missing_events)}" if missing_events else "Strengthen event coverage",
            f"Strengthen coverage for: {', '.join(weak_events)}" if weak_events else "Clarify language",
            "Add clear notice requirements",
            "Define mitigation obligations"
        ]

        result = llm_clause_service.rewrite_weak_clause(
            existing_clause,
            weakness_analysis,
            improvements
        )

        return Response(result)


class FMLLMGenerateClauseView(APIView):
    """
    POST /api/force-majeure/llm-generate-clause/
    Generate new FM clause from scratch using LLM
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .llm_service import llm_clause_service
        except ImportError:
            return Response({'error': 'LLM service not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        missing_events = data.get('missing_events', [])
        contract_value = data.get('contract_value')
        jurisdiction = data.get('jurisdiction')
        industry_standard = data.get('industry_standard', 'FIDIC')

        if not missing_events:
            return Response({'error': 'missing_events required'}, status=status.HTTP_400_BAD_REQUEST)

        context = {}
        if contract_value:
            context['value'] = float(contract_value)
        if jurisdiction:
            context['jurisdiction'] = jurisdiction

        generated_clause = llm_clause_service.generate_clause(
            'force_majeure',
            missing_events,
            context,
            industry_standard
        )

        return Response({
            'generated_clause': generated_clause,
            'events_covered': missing_events,
            'industry_standard': industry_standard,
            'contract_context': context
        })


# ═══════════════════════════════════════════════════════════════════════════════
# WAR SUPPLY CHAIN DISRUPTION ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
class FMWarSupplyChainView(APIView):
    """
    POST /api/force-majeure/war-supply-chain/
    Analyze war impact on contract supply chains
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .war_supply_chain_engine import war_supply_chain_engine
        except ImportError:
            return Response({'error': 'War supply chain engine not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        war_event = data.get('war_event', {})
        dependencies = data.get('dependencies', [])

        if not war_event:
            # Default war event
            war_event = {
                'type': 'war',
                'region': data.get('region', 'Eastern Europe'),
                'severity': data.get('severity', 0.7)
            }

        if not dependencies:
            # Create sample dependencies if none provided
            dependencies = [
                {
                    'name': 'Primary Steel Supplier',
                    'type': 'supplier',
                    'location': war_event.get('region', 'Eastern Europe'),
                    'criticality': 0.9,
                    'alternatives': []
                }
            ]

        result = war_supply_chain_engine.analyze_war_impact(war_event, dependencies)
        return Response(result)


class FMRouteClosureSimView(APIView):
    """
    POST /api/force-majeure/route-closure/
    Simulate closure of critical shipping route
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .war_supply_chain_engine import war_supply_chain_engine
        except ImportError:
            return Response({'error': 'War supply chain engine not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        route_id = data.get('route_id', 'suez_canal')
        closure_duration = data.get('closure_duration_days', 30)

        result = war_supply_chain_engine.simulate_route_closure(route_id, closure_duration)
        return Response(result)


# ═══════════════════════════════════════════════════════════════════════════════
# WAR LOSS PREDICTION
# ═══════════════════════════════════════════════════════════════════════════════
class FMWarLossPredictionView(APIView):
    """
    POST /api/force-majeure/war-loss-prediction/
    Predict financial losses from war events
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .war_loss_engine import war_loss_engine
        except ImportError:
            return Response({'error': 'War loss engine not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        contract_value = float(data.get('contract_value', 100_000_000))
        war_event = data.get('war_event', {'type': 'war', 'severity': 0.7})
        duration_days = data.get('duration_estimate_days', 180)

        project_data = {
            'workforce_size': data.get('workforce_size', 500),
            'equipment_count': data.get('equipment_count', 50),
            'phase': data.get('project_phase', 'execution'),
            'location_risk': data.get('location_risk', 0.7),
            'daily_burn_rate': data.get('daily_burn_rate', contract_value / 730)
        }

        result = war_loss_engine.predict_war_losses(
            contract_value,
            war_event,
            project_data,
            duration_days
        )

        return Response(result)


class FMWarInsurancePremiumView(APIView):
    """
    POST /api/force-majeure/war-insurance-premium/
    Calculate war risk insurance premium
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .war_loss_engine import war_loss_engine
        except ImportError:
            return Response({'error': 'War loss engine not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        contract_value = float(data.get('contract_value', 100_000_000))
        location_risk = float(data.get('location_risk', 0.5))
        war_probability = float(data.get('war_probability', 0.3))
        coverage_pct = float(data.get('coverage_percentage', 80.0))

        result = war_loss_engine.calculate_war_insurance_premium(
            contract_value,
            location_risk,
            war_probability,
            coverage_pct
        )

        return Response(result)


# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCED DATA SOURCES
# ═══════════════════════════════════════════════════════════════════════════════
class FMShippingDisruptionsView(APIView):
    """
    GET /api/force-majeure/shipping-disruptions/
    Get real-time shipping disruptions
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        try:
            from .advanced_data_sources import advanced_data_sources
        except ImportError:
            return Response({'error': 'Advanced data sources not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        region = request.query_params.get('region', 'global')
        disruptions = advanced_data_sources.get_shipping_disruptions(region)
        routes = advanced_data_sources.get_shipping_routes_status()

        return Response({
            'disruptions': disruptions,
            'major_routes': routes,
            'timestamp': '2026-03-17T00:00:00Z'
        })


class FMCommodityPricesView(APIView):
    """
    GET /api/force-majeure/commodity-prices/
    Get commodity prices and shock probabilities
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        try:
            from .advanced_data_sources import advanced_data_sources
        except ImportError:
            return Response({'error': 'Advanced data sources not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        commodities = request.query_params.get('commodities', 'oil,gas,steel,copper').split(',')
        shock_analysis = advanced_data_sources.get_commodity_shock_probability(commodities)

        return Response({
            'commodity_analysis': shock_analysis,
            'timestamp': '2026-03-17T00:00:00Z'
        })


class FMSanctionsCheckView(APIView):
    """
    POST /api/force-majeure/sanctions-check/
    Check entity against sanctions lists
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .advanced_data_sources import advanced_data_sources
        except ImportError:
            return Response({'error': 'Advanced data sources not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        entity_name = data.get('entity_name', '')
        country = data.get('country')

        if not entity_name:
            return Response({'error': 'entity_name required'}, status=status.HTTP_400_BAD_REQUEST)

        result = advanced_data_sources.check_sanctions_list(entity_name, country)
        active_sanctions = advanced_data_sources.get_active_sanctions()

        return Response({
            'entity_check': result,
            'active_sanctions': active_sanctions
        })


class FMPoliticalRiskView(APIView):
    """
    GET /api/force-majeure/political-risk/
    Get political risk index for country
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        try:
            from .advanced_data_sources import advanced_data_sources
        except ImportError:
            return Response({'error': 'Advanced data sources not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        country = request.query_params.get('country', 'USA')
        risk_index = advanced_data_sources.get_political_risk_index(country)

        return Response(risk_index)


class FMLaborStrikeRiskView(APIView):
    """
    GET /api/force-majeure/labor-strike-risk/
    Get labor strike probability
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        try:
            from .advanced_data_sources import advanced_data_sources
        except ImportError:
            return Response({'error': 'Advanced data sources not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        industry = request.query_params.get('industry', 'construction')
        region = request.query_params.get('region', 'Global')

        result = advanced_data_sources.get_labor_strike_probability(industry, region)
        return Response(result)


# ═══════════════════════════════════════════════════════════════════════════════
# GEOPOLITICAL INFERENCE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class FMGeopoliticalRiskView(APIView):
    """
    POST /api/force-majeure/geopolitical-risk/
    Analyze geopolitical risks and conflict escalation
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .geopolitical_engine import geopolitical_engine
        except ImportError:
            return Response({'error': 'Geopolitical engine not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        region = data.get('region', 'Global')
        project_location = data.get('project_location', {})
        supply_chain_locations = data.get('supply_chain_locations', [])
        time_horizon_days = data.get('time_horizon_days', 365)

        result = geopolitical_engine.analyze_geopolitical_risk(
            region,
            project_location,
            supply_chain_locations,
            time_horizon_days
        )

        return Response(result)


class FMConflictEscalationView(APIView):
    """
    POST /api/force-majeure/conflict-escalation/
    Predict conflict escalation probability
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .geopolitical_engine import geopolitical_engine
        except ImportError:
            return Response({'error': 'Geopolitical engine not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        current_events = data.get('current_events', [])
        region = data.get('region', 'Global')
        days_ahead = data.get('days_ahead', 90)

        result = geopolitical_engine.predict_conflict_escalation(
            current_events,
            region,
            days_ahead
        )

        return Response(result)


class FMDiplomaticStabilityView(APIView):
    """
    POST /api/force-majeure/diplomatic-stability/
    Assess diplomatic stability between countries
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .geopolitical_engine import geopolitical_engine
        except ImportError:
            return Response({'error': 'Geopolitical engine not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        countries = data.get('countries', [])
        include_alliances = data.get('include_alliances', True)

        if not countries:
            return Response({'error': 'countries list required'}, status=status.HTTP_400_BAD_REQUEST)

        result = geopolitical_engine.assess_diplomatic_stability(
            countries,
            include_alliances
        )

        return Response(result)


# ═══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO RISK SIMULATOR
# ═══════════════════════════════════════════════════════════════════════════════
class FMPortfolioSimulatorView(APIView):
    """
    POST /api/force-majeure/portfolio-simulator/
    Simulate correlated FM risks across entire portfolio
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .portfolio_simulator import portfolio_simulator
        except ImportError:
            return Response({'error': 'Portfolio simulator not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        contracts = data.get('contracts', [])
        n_simulations = data.get('n_simulations', 10000)
        confidence_level = data.get('confidence_level', 0.95)

        if not contracts:
            return Response({'error': 'contracts list required'}, status=status.HTTP_400_BAD_REQUEST)

        result = portfolio_simulator.simulate_portfolio_risk(
            contracts,
            n_simulations,
            confidence_level
        )

        return Response(result)


# ═══════════════════════════════════════════════════════════════════════════════
# DYNAMIC BAYESIAN NETWORK (TEMPORAL FORECASTING)
# ═══════════════════════════════════════════════════════════════════════════════
class FMTemporalForecastAdvancedView(APIView):
    """
    POST /api/force-majeure/temporal-forecast-advanced/
    Forecast FM risk evolution over time using Dynamic Bayesian Network
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .dynamic_bayesian_engine import dynamic_bayesian_network
        except ImportError:
            return Response({'error': 'Dynamic Bayesian Network not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        initial_evidence = data.get('initial_evidence', {})
        time_steps = data.get('time_steps', 12)
        time_unit = data.get('time_unit', 'months')
        target_outcomes = data.get('target_outcomes', None)

        if not initial_evidence:
            return Response({'error': 'initial_evidence required'}, status=status.HTTP_400_BAD_REQUEST)

        result = dynamic_bayesian_network.forecast_temporal_risk(
            initial_evidence,
            time_steps,
            time_unit,
            target_outcomes
        )

        return Response(result)


class FMScenarioComparisonView(APIView):
    """
    POST /api/force-majeure/scenario-comparison/
    Compare risk trajectories across multiple scenarios over time
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .dynamic_bayesian_engine import dynamic_bayesian_network
        except ImportError:
            return Response({'error': 'Dynamic Bayesian Network not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        baseline_evidence = data.get('baseline_evidence', {})
        alternative_scenarios = data.get('alternative_scenarios', [])
        time_steps = data.get('time_steps', 12)

        if not baseline_evidence:
            return Response({'error': 'baseline_evidence required'}, status=status.HTTP_400_BAD_REQUEST)

        if not alternative_scenarios:
            return Response({'error': 'alternative_scenarios required'}, status=status.HTTP_400_BAD_REQUEST)

        result = dynamic_bayesian_network.compare_scenarios(
            baseline_evidence,
            alternative_scenarios,
            time_steps
        )

        return Response(result)


# ═══════════════════════════════════════════════════════════════════════════════
# CONTRACT DIGITAL TWIN ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class FMDigitalTwinCreateView(APIView):
    """
    POST /api/force-majeure/digital-twin/create/
    Create a digital twin for a contract
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .digital_twin_engine import digital_twin_engine
        except ImportError:
            return Response({'error': 'Digital Twin Engine not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        contract_id = data.get('contract_id')
        contract_data = data.get('contract_data', {})

        if not contract_id:
            return Response({'error': 'contract_id required'}, status=status.HTTP_400_BAD_REQUEST)

        twin_id = digital_twin_engine.create_twin(contract_id, contract_data)

        result = {
            'twin_id': twin_id,
            'contract_id': contract_id,
            'message': 'Digital twin created successfully'
        }

        return Response(result)


class FMDigitalTwinSimulateView(APIView):
    """
    POST /api/force-majeure/digital-twin/simulate/
    Simulate FM scenario on contract digital twin
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .digital_twin_engine import digital_twin_engine
        except ImportError:
            return Response({'error': 'Digital Twin Engine not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        twin_id = data.get('twin_id')
        fm_scenario = data.get('fm_scenario', {})
        simulation_params = data.get('simulation_params', None)

        if not twin_id:
            return Response({'error': 'twin_id required'}, status=status.HTTP_400_BAD_REQUEST)

        if not fm_scenario:
            return Response({'error': 'fm_scenario required'}, status=status.HTTP_400_BAD_REQUEST)

        result = digital_twin_engine.simulate_fm_scenario(
            twin_id,
            fm_scenario,
            simulation_params
        )

        return Response(result)


class FMDigitalTwinStatusView(APIView):
    """
    GET /api/force-majeure/digital-twin/status/<twin_id>/
    Get current status of digital twin
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, twin_id: str) -> Response:
        try:
            from .digital_twin_engine import digital_twin_engine
        except ImportError:
            return Response({'error': 'Digital Twin Engine not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        result = digital_twin_engine.get_twin_status(twin_id)

        if 'error' in result:
            return Response(result, status=status.HTTP_404_NOT_FOUND)

        return Response(result)


class FMDigitalTwinCompareView(APIView):
    """
    POST /api/force-majeure/digital-twin/compare-scenarios/
    Compare multiple FM scenarios on same digital twin
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .digital_twin_engine import digital_twin_engine
        except ImportError:
            return Response({'error': 'Digital Twin Engine not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        twin_id = data.get('twin_id')
        scenarios = data.get('scenarios', [])

        if not twin_id:
            return Response({'error': 'twin_id required'}, status=status.HTTP_400_BAD_REQUEST)

        if not scenarios:
            return Response({'error': 'scenarios list required'}, status=status.HTTP_400_BAD_REQUEST)

        result = digital_twin_engine.compare_scenarios(twin_id, scenarios)

        return Response(result)


# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED COUNTERFACTUAL ENGINE (DO-CALCULUS)
# ═══════════════════════════════════════════════════════════════════════════════
class FMDoInterventionView(APIView):
    """
    POST /api/force-majeure/do-intervention/
    Perform do-operator intervention analysis (causal inference)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .enhanced_counterfactual_engine import enhanced_counterfactual_engine
        except ImportError:
            return Response({'error': 'Enhanced Counterfactual Engine not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        intervention = data.get('intervention', {})
        target_outcomes = data.get('target_outcomes', [])
        background_evidence = data.get('background_evidence', None)

        if not intervention:
            return Response({'error': 'intervention required'}, status=status.HTTP_400_BAD_REQUEST)

        if not target_outcomes:
            return Response({'error': 'target_outcomes required'}, status=status.HTTP_400_BAD_REQUEST)

        result = enhanced_counterfactual_engine.do_intervention(
            intervention,
            target_outcomes,
            background_evidence
        )

        return Response(result)


class FMCounterfactualQueryView(APIView):
    """
    POST /api/force-majeure/counterfactual-query/
    Perform counterfactual reasoning: "What if X had been different?"
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .enhanced_counterfactual_engine import enhanced_counterfactual_engine
        except ImportError:
            return Response({'error': 'Enhanced Counterfactual Engine not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        factual_world = data.get('factual_world', {})
        counterfactual_intervention = data.get('counterfactual_intervention', {})
        target_outcome = data.get('target_outcome')

        if not factual_world:
            return Response({'error': 'factual_world required'}, status=status.HTTP_400_BAD_REQUEST)

        if not counterfactual_intervention:
            return Response({'error': 'counterfactual_intervention required'}, status=status.HTTP_400_BAD_REQUEST)

        if not target_outcome:
            return Response({'error': 'target_outcome required'}, status=status.HTTP_400_BAD_REQUEST)

        result = enhanced_counterfactual_engine.counterfactual_query(
            factual_world,
            counterfactual_intervention,
            target_outcome
        )

        return Response(result)


class FMCausalEffectView(APIView):
    """
    POST /api/force-majeure/causal-effect/
    Estimate average causal effect of treatment on outcome
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .enhanced_counterfactual_engine import enhanced_counterfactual_engine
        except ImportError:
            return Response({'error': 'Enhanced Counterfactual Engine not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        treatment = data.get('treatment')
        outcome = data.get('outcome')
        adjustment_set = data.get('adjustment_set', None)

        if not treatment:
            return Response({'error': 'treatment variable required'}, status=status.HTTP_400_BAD_REQUEST)

        if not outcome:
            return Response({'error': 'outcome variable required'}, status=status.HTTP_400_BAD_REQUEST)

        result = enhanced_counterfactual_engine.estimate_causal_effect(
            treatment,
            outcome,
            adjustment_set
        )

        return Response(result)


class FMSensitivityAnalysisView(APIView):
    """
    POST /api/force-majeure/sensitivity-analysis/
    Perform sensitivity analysis to unmeasured confounding
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .enhanced_counterfactual_engine import enhanced_counterfactual_engine
        except ImportError:
            return Response({'error': 'Enhanced Counterfactual Engine not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        intervention = data.get('intervention', {})
        target_outcome = data.get('target_outcome')
        unmeasured_confounder_strength = data.get('unmeasured_confounder_strength', 0.3)

        if not intervention:
            return Response({'error': 'intervention required'}, status=status.HTTP_400_BAD_REQUEST)

        if not target_outcome:
            return Response({'error': 'target_outcome required'}, status=status.HTTP_400_BAD_REQUEST)

        result = enhanced_counterfactual_engine.sensitivity_analysis(
            intervention,
            target_outcome,
            unmeasured_confounder_strength
        )

        return Response(result)


# ═══════════════════════════════════════════════════════════════════════════════
# CLAUSE OPTIMIZATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class FMClauseOptimizeView(APIView):
    """
    POST /api/force-majeure/clause-optimize/
    Multi-objective optimization for FM clause improvement
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .clause_optimization_engine import clause_optimization_engine
        except ImportError:
            return Response({'error': 'Clause Optimization Engine not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        current_clause = data.get('current_clause', '')
        optimization_objectives = data.get('optimization_objectives', None)
        constraints = data.get('constraints', None)
        party_preferences = data.get('party_preferences', None)

        if not current_clause:
            return Response({'error': 'current_clause required'}, status=status.HTTP_400_BAD_REQUEST)

        result = clause_optimization_engine.optimize_clause(
            current_clause,
            optimization_objectives,
            constraints,
            party_preferences
        )

        return Response(result)


class FMMultiPartyOptimizeView(APIView):
    """
    POST /api/force-majeure/multi-party-optimize/
    Optimize clause balancing multiple party interests
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .clause_optimization_engine import clause_optimization_engine
        except ImportError:
            return Response({'error': 'Clause Optimization Engine not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        current_clause = data.get('current_clause', '')
        buyer_preferences = data.get('buyer_preferences', {})
        seller_preferences = data.get('seller_preferences', {})
        neutral_arbitrator = data.get('neutral_arbitrator', True)

        if not current_clause:
            return Response({'error': 'current_clause required'}, status=status.HTTP_400_BAD_REQUEST)

        result = clause_optimization_engine.multi_party_negotiation_optimize(
            current_clause,
            buyer_preferences,
            seller_preferences,
            neutral_arbitrator
        )

        return Response(result)


# ═══════════════════════════════════════════════════════════════════════════════
# APPROVAL WORKFLOW SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
class FMApprovalRequestCreateView(APIView):
    """
    POST /api/force-majeure/approval/create/
    Create approval request for clause change
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .approval_workflow import approval_workflow_engine
        except ImportError:
            return Response({'error': 'Approval Workflow not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        contract_id = data.get('contract_id')
        contract_name = data.get('contract_name', '')
        change_type = data.get('change_type', 'rewrite')
        original_clause = data.get('original_clause', '')
        proposed_clause = data.get('proposed_clause', '')
        change_justification = data.get('change_justification', '')
        risk_reduction = data.get('risk_reduction', 0.0)
        improvement_score = data.get('improvement_score', 0.5)

        if not contract_id:
            return Response({'error': 'contract_id required'}, status=status.HTTP_400_BAD_REQUEST)

        if not original_clause or not proposed_clause:
            return Response({'error': 'original_clause and proposed_clause required'}, status=status.HTTP_400_BAD_REQUEST)

        request_id = approval_workflow_engine.create_approval_request(
            contract_id,
            contract_name,
            change_type,
            original_clause,
            proposed_clause,
            change_justification,
            risk_reduction,
            improvement_score,
            request.user.id,
            request.user.get_full_name() or request.user.username
        )

        return Response({'request_id': request_id, 'status': 'created'})


class FMApprovalApproveView(APIView):
    """
    POST /api/force-majeure/approval/approve/
    Approve an approval step
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .approval_workflow import approval_workflow_engine
        except ImportError:
            return Response({'error': 'Approval Workflow not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        request_id = data.get('request_id')
        comments = data.get('comments', '')

        if not request_id:
            return Response({'error': 'request_id required'}, status=status.HTTP_400_BAD_REQUEST)

        result = approval_workflow_engine.approve_step(
            request_id,
            str(request.user.id),
            comments
        )

        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(result)


class FMApprovalRejectView(APIView):
    """
    POST /api/force-majeure/approval/reject/
    Reject an approval request
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        try:
            from .approval_workflow import approval_workflow_engine
        except ImportError:
            return Response({'error': 'Approval Workflow not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        data = request.data
        request_id = data.get('request_id')
        reason = data.get('reason', '')

        if not request_id:
            return Response({'error': 'request_id required'}, status=status.HTTP_400_BAD_REQUEST)

        if not reason:
            return Response({'error': 'reason required'}, status=status.HTTP_400_BAD_REQUEST)

        result = approval_workflow_engine.reject_step(
            request_id,
            str(request.user.id),
            reason
        )

        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(result)


class FMApprovalStatusView(APIView):
    """
    GET /api/force-majeure/approval/status/<request_id>/
    Get approval request status
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, request_id: str) -> Response:
        try:
            from .approval_workflow import approval_workflow_engine
        except ImportError:
            return Response({'error': 'Approval Workflow not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        result = approval_workflow_engine.get_request_status(request_id)

        if 'error' in result:
            return Response(result, status=status.HTTP_404_NOT_FOUND)

        return Response(result)


class FMApprovalPendingView(APIView):
    """
    GET /api/force-majeure/approval/pending/
    Get pending approvals for current user
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        try:
            from .approval_workflow import approval_workflow_engine
        except ImportError:
            return Response({'error': 'Approval Workflow not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        pending = approval_workflow_engine.get_pending_approvals(str(request.user.id))

        return Response({
            'pending_count': len(pending),
            'approvals': pending
        })
