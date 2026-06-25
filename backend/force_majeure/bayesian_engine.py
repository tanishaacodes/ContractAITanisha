"""
Force Majeure Bayesian Risk Network
=====================================
Pure-Python Noisy-OR Bayesian inference engine (no pgmpy dependency).
35+ nodes across 4 layers:
  Layer 1 — Root Events (15 nodes)
  Layer 2 — Intermediate Disruptions (12 nodes)
  Layer 3 — Supply Chain Impacts (8 nodes)
  Layer 4 — Contract Outcome Nodes (6 nodes)

Conditional Probability Tables (CPTs) encode domain knowledge.
Forward belief propagation produces posterior probabilities for
outcome nodes given observed evidence.
"""
import math
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# NODE DEFINITIONS
# ---------------------------------------------------------------------------

# Layer 1 — Root cause events
LAYER1_EVENTS = [
    'war',
    'regional_conflict',
    'cyber_warfare',
    'terrorism',
    'pandemic',
    'epidemic',
    'earthquake',
    'flood',
    'hurricane',
    'wildfire',
    'volcanic_eruption',
    'political_coup',
    'trade_sanctions',
    'economic_collapse',
    'energy_crisis',
]

# Layer 2 — Intermediate disruptions
LAYER2_DISRUPTIONS = [
    'sanctions_expansion',
    'currency_volatility',
    'commodity_price_shock',
    'energy_price_spike',
    'labor_shortage',
    'factory_shutdown',
    'transport_shutdown',
    'port_closure',
    'airspace_closure',
    'telecom_disruption',
    'power_grid_failure',
    'financial_market_crash',
]

# Layer 3 — Supply chain impacts
LAYER3_SUPPLY = [
    'supplier_failure',
    'inventory_shortage',
    'logistics_delay',
    'shipping_route_disruption',
    'manufacturing_delay',
    'equipment_delivery_delay',
    'commodity_cost_escalation',
    'insurance_premium_spike',
]

# Layer 4 — Contract outcome nodes
LAYER4_OUTCOMES = [
    'project_delay',
    'cost_overrun',
    'contract_suspension',
    'insurance_claim',
    'fm_invocation',
    'contract_termination',
]

ALL_NODES = LAYER1_EVENTS + LAYER2_DISRUPTIONS + LAYER3_SUPPLY + LAYER4_OUTCOMES


# ---------------------------------------------------------------------------
# BASE PRIOR PROBABILITIES (unconditional priors for root nodes)
# ---------------------------------------------------------------------------
BASE_PRIORS: Dict[str, float] = {
    'war': 0.08,
    'regional_conflict': 0.15,
    'cyber_warfare': 0.12,
    'terrorism': 0.10,
    'pandemic': 0.06,
    'epidemic': 0.12,
    'earthquake': 0.05,
    'flood': 0.14,
    'hurricane': 0.08,
    'wildfire': 0.10,
    'volcanic_eruption': 0.02,
    'political_coup': 0.07,
    'trade_sanctions': 0.20,
    'economic_collapse': 0.09,
    'energy_crisis': 0.18,
}

# ---------------------------------------------------------------------------
# CONDITIONAL PROBABILITY TABLES (CPTs)
# P(child | parent) — Noisy-OR model: each parent independently causes child
# Format: { child_node: { parent_node: leak_probability } }
# ---------------------------------------------------------------------------

CPT_LAYER2: Dict[str, Dict[str, float]] = {
    'sanctions_expansion': {
        'war': 0.65, 'trade_sanctions': 0.80, 'political_coup': 0.35, 'economic_collapse': 0.40,
    },
    'currency_volatility': {
        'war': 0.55, 'economic_collapse': 0.75, 'trade_sanctions': 0.45, 'political_coup': 0.40,
    },
    'commodity_price_shock': {
        'war': 0.60, 'energy_crisis': 0.70, 'trade_sanctions': 0.50, 'natural_disaster_group': 0.30,
        'flood': 0.25, 'hurricane': 0.20, 'wildfire': 0.15,
    },
    'energy_price_spike': {
        'war': 0.55, 'energy_crisis': 0.85, 'trade_sanctions': 0.40, 'political_coup': 0.30,
    },
    'labor_shortage': {
        'pandemic': 0.75, 'epidemic': 0.55, 'war': 0.45, 'political_coup': 0.25,
    },
    'factory_shutdown': {
        'pandemic': 0.65, 'war': 0.50, 'earthquake': 0.45, 'flood': 0.40, 'hurricane': 0.35,
        'power_grid_failure': 0.50, 'energy_crisis': 0.30,
    },
    'transport_shutdown': {
        'war': 0.55, 'pandemic': 0.50, 'earthquake': 0.45, 'flood': 0.40, 'hurricane': 0.50,
        'political_coup': 0.35,
    },
    'port_closure': {
        'war': 0.45, 'hurricane': 0.55, 'flood': 0.35, 'earthquake': 0.40, 'trade_sanctions': 0.30,
        'political_coup': 0.25,
    },
    'airspace_closure': {
        'war': 0.60, 'political_coup': 0.50, 'terrorism': 0.35, 'volcanic_eruption': 0.70,
        'hurricane': 0.30,
    },
    'telecom_disruption': {
        'war': 0.40, 'cyber_warfare': 0.75, 'earthquake': 0.35, 'hurricane': 0.30,
        'power_grid_failure': 0.55,
    },
    'power_grid_failure': {
        'war': 0.45, 'cyber_warfare': 0.65, 'earthquake': 0.50, 'hurricane': 0.45,
        'energy_crisis': 0.40, 'wildfire': 0.30,
    },
    'financial_market_crash': {
        'war': 0.50, 'economic_collapse': 0.85, 'pandemic': 0.45, 'trade_sanctions': 0.40,
    },
}

CPT_LAYER3: Dict[str, Dict[str, float]] = {
    'supplier_failure': {
        'factory_shutdown': 0.70, 'financial_market_crash': 0.55, 'sanctions_expansion': 0.45,
        'labor_shortage': 0.40, 'transport_shutdown': 0.35,
    },
    'inventory_shortage': {
        'supplier_failure': 0.75, 'transport_shutdown': 0.60, 'port_closure': 0.55,
        'factory_shutdown': 0.50,
    },
    'logistics_delay': {
        'transport_shutdown': 0.80, 'port_closure': 0.70, 'airspace_closure': 0.50,
        'fuel_price_spike': 0.35, 'energy_price_spike': 0.35,
    },
    'shipping_route_disruption': {
        'port_closure': 0.75, 'war': 0.50, 'airspace_closure': 0.40, 'transport_shutdown': 0.55,
    },
    'manufacturing_delay': {
        'factory_shutdown': 0.80, 'labor_shortage': 0.65, 'inventory_shortage': 0.60,
        'power_grid_failure': 0.55,
    },
    'equipment_delivery_delay': {
        'logistics_delay': 0.75, 'shipping_route_disruption': 0.65, 'port_closure': 0.55,
        'airspace_closure': 0.40,
    },
    'commodity_cost_escalation': {
        'commodity_price_shock': 0.85, 'energy_price_spike': 0.60, 'currency_volatility': 0.50,
        'sanctions_expansion': 0.45,
    },
    'insurance_premium_spike': {
        'war': 0.55, 'pandemic': 0.40, 'commodity_cost_escalation': 0.35,
        'financial_market_crash': 0.45, 'shipping_route_disruption': 0.30,
    },
}

CPT_LAYER4: Dict[str, Dict[str, float]] = {
    'project_delay': {
        'equipment_delivery_delay': 0.85, 'manufacturing_delay': 0.80, 'logistics_delay': 0.75,
        'labor_shortage': 0.65, 'supplier_failure': 0.70, 'transport_shutdown': 0.60,
    },
    'cost_overrun': {
        'commodity_cost_escalation': 0.80, 'insurance_premium_spike': 0.65,
        'currency_volatility': 0.60, 'project_delay': 0.70, 'logistics_delay': 0.55,
    },
    'contract_suspension': {
        'project_delay': 0.45, 'supplier_failure': 0.55, 'financial_market_crash': 0.50,
        'war': 0.40, 'political_coup': 0.45,
    },
    'insurance_claim': {
        'project_delay': 0.50, 'cost_overrun': 0.45, 'contract_suspension': 0.55,
        'shipping_route_disruption': 0.40, 'war': 0.35,
    },
    'fm_invocation': {
        'project_delay': 0.55, 'contract_suspension': 0.65, 'supplier_failure': 0.50,
        'war': 0.45, 'pandemic': 0.50, 'earthquake': 0.40, 'flood': 0.35,
        'port_closure': 0.35, 'airspace_closure': 0.30,
    },
    'contract_termination': {
        'fm_invocation': 0.40, 'contract_suspension': 0.50, 'financial_market_crash': 0.35,
        'war': 0.30, 'economic_collapse': 0.35,
    },
}


# ---------------------------------------------------------------------------
# NOISY-OR FORWARD PROPAGATION
# ---------------------------------------------------------------------------

def noisy_or(parent_probs: Dict[str, float], cpt_row: Dict[str, float]) -> float:
    """
    Noisy-OR combination: P(child=T) = 1 - Π(1 - p_i * q_i)
    where p_i = P(parent_i = True), q_i = CPT weight for that parent.
    """
    product = 1.0
    for parent, weight in cpt_row.items():
        p_parent = parent_probs.get(parent, 0.0)
        product *= (1.0 - weight * p_parent)
    return max(0.0, min(1.0, 1.0 - product))


class FMBayesianEngine:
    """
    35-node Force Majeure Bayesian inference engine.
    Runs forward belief propagation given observed evidence.
    """

    def __init__(self):
        self.node_probs: Dict[str, float] = {}

    def _init_priors(self, evidence: Dict[str, float]) -> None:
        """Initialize root node probabilities from evidence + priors."""
        for node in LAYER1_EVENTS:
            if node in evidence:
                self.node_probs[node] = float(evidence[node])
            else:
                self.node_probs[node] = BASE_PRIORS.get(node, 0.10)

    def _propagate_layer2(self) -> None:
        for node, cpt_row in CPT_LAYER2.items():
            self.node_probs[node] = noisy_or(self.node_probs, cpt_row)

    def _propagate_layer3(self) -> None:
        for node, cpt_row in CPT_LAYER3.items():
            self.node_probs[node] = noisy_or(self.node_probs, cpt_row)

    def _propagate_layer4(self) -> None:
        for node, cpt_row in CPT_LAYER4.items():
            self.node_probs[node] = noisy_or(self.node_probs, cpt_row)

    def infer(self, evidence: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        Run full forward inference pass.
        evidence: dict of {node_name: probability_0_to_1}
                  e.g. {'war': 0.8, 'trade_sanctions': 0.9}
        Returns: dict of all node probabilities.
        """
        if evidence is None:
            evidence = {}

        self._init_priors(evidence)
        self._propagate_layer2()
        self._propagate_layer3()
        self._propagate_layer4()

        return dict(self.node_probs)

    def get_outcome_probs(self, evidence: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """Returns only Layer 4 outcome node probabilities."""
        all_probs = self.infer(evidence)
        return {node: all_probs.get(node, 0.0) for node in LAYER4_OUTCOMES}

    def get_top_risk_drivers(
        self, evidence: Optional[Dict[str, float]] = None, top_n: int = 5
    ) -> List[Dict]:
        """
        Returns top N root + disruption nodes ranked by their inferred probability.
        """
        all_probs = self.infer(evidence)
        driver_nodes = LAYER1_EVENTS + LAYER2_DISRUPTIONS
        ranked = sorted(
            [{'node': n, 'probability': all_probs.get(n, 0.0)} for n in driver_nodes],
            key=lambda x: x['probability'],
            reverse=True,
        )
        return ranked[:top_n]

    def get_causal_chain(
        self, outcome_node: str = 'fm_invocation', evidence: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """
        Returns the highest-probability causal path leading to the given outcome node.
        """
        all_probs = self.infer(evidence)

        # Determine which layer 3 nodes most strongly feed the outcome
        if outcome_node in CPT_LAYER4:
            l3_parents = CPT_LAYER4[outcome_node]
        else:
            return []

        chain = []
        for l3_node, weight in sorted(l3_parents.items(), key=lambda x: -x[1]):
            prob = all_probs.get(l3_node, 0.0)
            if prob > 0.1:
                chain.append({'node': l3_node, 'probability': prob, 'layer': 3})
                # Trace back to layer 2
                if l3_node in CPT_LAYER3:
                    for l2_node, w2 in sorted(CPT_LAYER3[l3_node].items(), key=lambda x: -x[1]):
                        p2 = all_probs.get(l2_node, 0.0)
                        if p2 > 0.1:
                            chain.append({'node': l2_node, 'probability': p2, 'layer': 2})
                            # Trace back to layer 1
                            if l2_node in CPT_LAYER2:
                                for l1_node, w1 in sorted(CPT_LAYER2[l2_node].items(), key=lambda x: -x[1]):
                                    p1 = all_probs.get(l1_node, 0.0)
                                    if p1 > 0.05:
                                        chain.append({'node': l1_node, 'probability': p1, 'layer': 1})
                            break
                break

        return chain

    def compute_fm_risk_score(self, evidence: Optional[Dict[str, float]] = None) -> float:
        """
        Single composite FM risk score (0-1) combining outcome probabilities.
        Weighted: fm_invocation(0.35) + project_delay(0.25) + cost_overrun(0.20)
                + contract_suspension(0.12) + contract_termination(0.08)
        """
        outcomes = self.get_outcome_probs(evidence)
        score = (
            outcomes.get('fm_invocation', 0.0) * 0.35
            + outcomes.get('project_delay', 0.0) * 0.25
            + outcomes.get('cost_overrun', 0.0) * 0.20
            + outcomes.get('contract_suspension', 0.0) * 0.12
            + outcomes.get('contract_termination', 0.0) * 0.08
        )
        return round(min(1.0, score), 4)


# Singleton instance
_engine_instance: Optional[FMBayesianEngine] = None


def get_fm_bayesian_engine() -> FMBayesianEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = FMBayesianEngine()
    return _engine_instance


# ---------------------------------------------------------------------------
# WAR RISK ONTOLOGY — 17 war-event types with causal weights
# ---------------------------------------------------------------------------
WAR_EVENT_NODES = {
    'military_invasion': {'supply_chain_disruption': 0.75, 'commodity_spike': 0.65, 'port_closure': 0.55, 'logistics_shutdown': 0.70, 'insurance_escalation': 0.60},
    'civil_war': {'supply_chain_disruption': 0.65, 'labor_shortage': 0.70, 'port_closure': 0.45, 'factory_shutdown': 0.55},
    'border_conflict': {'logistics_shutdown': 0.55, 'supply_chain_disruption': 0.50, 'commodity_spike': 0.40},
    'terrorism': {'transport_shutdown': 0.45, 'airspace_closure': 0.40, 'insurance_escalation': 0.35},
    'insurrection': {'factory_shutdown': 0.55, 'labor_shortage': 0.60, 'logistics_shutdown': 0.50},
    'military_coup': {'airspace_closure': 0.65, 'port_closure': 0.50, 'logistics_shutdown': 0.55, 'financial_market_crash': 0.45},
    'cyber_warfare': {'telecom_disruption': 0.80, 'power_grid_failure': 0.70, 'financial_market_crash': 0.50},
    'drone_strikes': {'factory_shutdown': 0.60, 'port_closure': 0.45, 'logistics_shutdown': 0.50},
    'naval_blockade': {'port_closure': 0.90, 'shipping_route_disruption': 0.85, 'commodity_spike': 0.70},
    'trade_embargo': {'sanctions_expansion': 0.80, 'commodity_spike': 0.65, 'supply_chain_disruption': 0.70},
    'sanctions': {'sanctions_expansion': 0.85, 'currency_volatility': 0.60, 'commodity_spike': 0.55},
    'government_expropriation': {'contract_termination': 0.75, 'insurance_claim': 0.65},
    'martial_law': {'labor_shortage': 0.70, 'logistics_shutdown': 0.65, 'factory_shutdown': 0.60},
    'port_shutdown': {'port_closure': 0.95, 'logistics_delay': 0.85, 'inventory_shortage': 0.75},
    'airspace_closure': {'airspace_closure': 0.95, 'logistics_delay': 0.70},
    'energy_infrastructure_attack': {'power_grid_failure': 0.85, 'energy_price_spike': 0.80, 'factory_shutdown': 0.65},
    'satellite_disruption': {'telecom_disruption': 0.70, 'logistics_delay': 0.40},
}


def compute_war_risk_score(war_events_observed: Dict[str, float]) -> Dict:
    """
    Given observed war events and their probabilities, compute composite war risk.
    Returns: {war_risk_score, top_threats, disruption_probs}
    """
    disruption_probs: Dict[str, float] = {}

    for war_event, prob in war_events_observed.items():
        causal_map = WAR_EVENT_NODES.get(war_event, {})
        for disruption, weight in causal_map.items():
            existing = disruption_probs.get(disruption, 0.0)
            # Noisy-OR combination
            disruption_probs[disruption] = 1.0 - (1.0 - existing) * (1.0 - weight * prob)

    # Composite score: weighted average of top disruptions
    if disruption_probs:
        top_disrupt = sorted(disruption_probs.items(), key=lambda x: -x[1])[:5]
        score = sum(p for _, p in top_disrupt) / max(len(top_disrupt), 1)
    else:
        score = 0.0

    top_threats = [
        {'event': e, 'probability': p}
        for e, p in sorted(war_events_observed.items(), key=lambda x: -x[1])[:5]
    ]

    return {
        'war_risk_score': round(min(1.0, score), 4),
        'top_threats': top_threats,
        'disruption_probs': disruption_probs,
    }


# ---------------------------------------------------------------------------
# DYNAMIC PRIOR UPDATE — maps live events to Bayesian prior boosts
# ---------------------------------------------------------------------------

LIVE_EVENT_TO_NODE: Dict[str, str] = {
    'war': 'war', 'sanctions': 'trade_sanctions', 'pandemic': 'pandemic',
    'earthquake': 'earthquake', 'flood': 'flood', 'port_closure': 'port_closure',
    'supply_chain_disruption': 'trade_sanctions', 'energy_shortage': 'energy_crisis',
    'cyber_attack': 'cyber_warfare', 'terrorism': 'terrorism',
    'political_coup': 'political_coup', 'natural_disaster': 'flood',
    'hurricane': 'hurricane', 'wildfire': 'wildfire',
}


def update_priors_from_live_events(live_events: list) -> dict:
    """Given live FM events, compute updated Bayesian priors vs baseline."""
    updated = {k: v for k, v in BASE_PRIORS.items()}
    node_sources: Dict[str, list] = {k: [] for k in BASE_PRIORS}

    for ev in live_events:
        ev_type = ev.get('event_type', 'unknown')
        risk_score = float(ev.get('risk_score', 0))
        node = LIVE_EVENT_TO_NODE.get(ev_type, '')
        if not node or node not in updated:
            continue
        boost = risk_score * 0.35
        new_val = min(0.95, updated[node] + boost * (1 - updated[node]))
        updated[node] = round(new_val, 4)
        node_sources[node].append({
            'title': ev.get('title', '')[:80],
            'risk_score': risk_score,
            'source': ev.get('source', ''),
        })

    result = {}
    for node in BASE_PRIORS:
        base = BASE_PRIORS[node]
        upd = updated[node]
        result[node] = {
            'base_prior': base, 'updated_prior': upd,
            'delta': round(upd - base, 4),
            'pct_change': round((upd - base) / max(base, 0.001) * 100, 1),
            'source_events': node_sources[node][:3],
        }
    return result


# ---------------------------------------------------------------------------
# OUTCOME WEIGHTS (used for formula breakdown)
# ---------------------------------------------------------------------------

OUTCOME_WEIGHTS = {
    'fm_invocation': 0.35, 'project_delay': 0.25, 'cost_overrun': 0.20,
    'contract_suspension': 0.12, 'contract_termination': 0.08,
}


def compute_risk_formula_breakdown(evidence: Dict[str, float]) -> dict:
    """Full step-by-step breakdown of FM risk score derivation."""
    engine = get_fm_bayesian_engine()
    all_probs = engine.infer(evidence)
    outcomes = {n: all_probs.get(n, 0) for n in LAYER4_OUTCOMES}

    outcome_breakdown = []
    total_score = 0.0
    for node, weight in OUTCOME_WEIGHTS.items():
        prob = outcomes.get(node, 0)
        contribution = prob * weight
        total_score += contribution
        outcome_breakdown.append({
            'outcome_node': node,
            'label': node.replace('_', ' ').title(),
            'probability': round(prob, 4),
            'weight': weight,
            'contribution': round(contribution, 4),
        })

    event_contribution = []
    base_score = engine.compute_fm_risk_score(evidence)
    for ev_node in LAYER1_EVENTS:
        ev_prob = all_probs.get(ev_node, 0)
        if ev_prob < 0.05:
            continue
        ev_null = {k: v for k, v in evidence.items()}
        ev_null[ev_node] = 0.0
        score_null = engine.compute_fm_risk_score(ev_null)
        sensitivity = round(base_score - score_null, 4)
        event_contribution.append({
            'event': ev_node,
            'label': ev_node.replace('_', ' ').title(),
            'prior': BASE_PRIORS.get(ev_node, 0),
            'evidence_override': evidence.get(ev_node),
            'inferred_prob': round(ev_prob, 4),
            'risk_contribution': max(0, sensitivity),
        })
    event_contribution.sort(key=lambda x: -x['risk_contribution'])

    formula_str = ' + '.join([f"{w}xP({n.replace('_',' ').title()})" for n, w in OUTCOME_WEIGHTS.items()])
    return {
        'formula': formula_str,
        'outcome_breakdown': outcome_breakdown,
        'event_contribution': event_contribution[:10],
        'total_fm_risk_score': round(min(1.0, total_score), 4),
        'evidence_used': evidence,
        'outcome_weights': OUTCOME_WEIGHTS,
    }


# ---------------------------------------------------------------------------
# TEMPORAL FORECAST — 12-month DBN simulation with time decay
# ---------------------------------------------------------------------------

DECAY_RATES: Dict[str, float] = {
    'war': 0.92, 'regional_conflict': 0.90, 'trade_sanctions': 0.93,
    'political_coup': 0.88, 'terrorism': 0.90, 'cyber_warfare': 0.91,
    'earthquake': 0.82, 'flood': 0.80, 'hurricane': 0.78,
    'wildfire': 0.80, 'volcanic_eruption': 0.85,
    'pandemic': 0.94, 'epidemic': 0.90,
    'economic_collapse': 0.93, 'energy_crisis': 0.91,
}

SEASONAL_BOOSTS: Dict[int, Dict[str, float]] = {
    1: {'energy_crisis': 0.12, 'flood': 0.08, 'war': 0.05},
    2: {'flood': 0.06, 'pandemic': 0.10},
    3: {'flood': 0.10, 'pandemic': 0.08},
    4: {'flood': 0.08, 'trade_sanctions': 0.06},
    5: {'flood': 0.12, 'wildfire': 0.08},
    6: {'hurricane': 0.15, 'flood': 0.12, 'wildfire': 0.10},
    7: {'hurricane': 0.20, 'wildfire': 0.15, 'energy_crisis': 0.08},
    8: {'hurricane': 0.25, 'wildfire': 0.18, 'energy_crisis': 0.10},
    9: {'hurricane': 0.20, 'flood': 0.15, 'earthquake': 0.08},
    10: {'hurricane': 0.12, 'earthquake': 0.10, 'energy_crisis': 0.06},
    11: {'energy_crisis': 0.10, 'war': 0.08},
    12: {'energy_crisis': 0.15, 'war': 0.10, 'pandemic': 0.12},
}

MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']


def compute_temporal_forecast(base_evidence: Dict[str, float], start_month: int = 1) -> list:
    """12-month FM risk forecast using time-decayed Bayesian inference per month."""
    import math
    engine = get_fm_bayesian_engine()
    current_ev = {k: float(v) for k, v in base_evidence.items()}
    results = []

    for i in range(12):
        month_idx = (start_month - 1 + i) % 12
        month_name = MONTH_NAMES[month_idx]
        month_num = month_idx + 1
        seasonal = SEASONAL_BOOSTS.get(month_num, {})

        # Create month-specific evidence with seasonal boosts
        month_ev = {k: v for k, v in current_ev.items()}
        for node, boost in seasonal.items():
            if node in LAYER1_EVENTS:
                month_ev[node] = min(0.95, month_ev.get(node, BASE_PRIORS.get(node, 0.05)) + boost)

        # Add oscillating variation for geopolitical events (simulates tension/de-escalation cycles)
        oscillation = 0.03 * math.sin(i * math.pi / 6)  # 2-cycle per year
        for geo_event in ['war', 'trade_sanctions', 'terrorism', 'political_coup']:
            if geo_event in month_ev:
                month_ev[geo_event] = max(0.05, min(0.95, month_ev[geo_event] + oscillation))

        all_probs = engine.infer(month_ev)
        fm_risk = engine.compute_fm_risk_score(month_ev)
        outcomes = {n: all_probs.get(n, 0) for n in LAYER4_OUTCOMES}
        drivers = sorted([(n, all_probs.get(n, 0)) for n in LAYER1_EVENTS], key=lambda x: -x[1])
        top_driver = drivers[0][0].replace('_', ' ').title() if drivers else 'Unknown'

        results.append({
            'month': month_name, 'month_num': month_num,
            'fm_risk': round(fm_risk, 4),
            'fm_invocation_prob': round(outcomes.get('fm_invocation', 0), 4),
            'project_delay_prob': round(outcomes.get('project_delay', 0), 4),
            'cost_overrun_prob': round(outcomes.get('cost_overrun', 0), 4),
            'risk_label': 'HIGH' if fm_risk > 0.6 else 'MED' if fm_risk > 0.3 else 'LOW',
            'dominant_driver': top_driver,
        })

        # Apply time decay to evidence for next month
        for node in list(current_ev.keys()):
            decay = DECAY_RATES.get(node, 0.88)
            # Add slight randomness to decay (±5%) for more realistic variation
            decay_variance = decay * (1 + (hash(node + str(i)) % 10 - 5) / 100)
            current_ev[node] = max(BASE_PRIORS.get(node, 0.02), current_ev[node] * decay_variance)

    return results


# ---------------------------------------------------------------------------
# RISK CASCADE — traces causal propagation for a given evidence set
# ---------------------------------------------------------------------------

def compute_risk_cascade(evidence: Dict[str, float], contract_value: float = 1_000_000) -> dict:
    """
    Returns a 4-stage cascade showing risk propagation from root events
    through disruptions, supply chain, to contract outcomes.
    """
    from .fm_service import monte_carlo_loss
    engine = get_fm_bayesian_engine()
    all_probs = engine.infer(evidence)
    fm_risk = engine.compute_fm_risk_score(evidence)

    # ALL nodes per layer, sorted by probability
    l1_all = sorted([(n, all_probs.get(n, 0)) for n in LAYER1_EVENTS], key=lambda x: -x[1])
    l2_all = sorted([(n, all_probs.get(n, 0)) for n in LAYER2_DISRUPTIONS], key=lambda x: -x[1])
    l3_all = sorted([(n, all_probs.get(n, 0)) for n in LAYER3_SUPPLY], key=lambda x: -x[1])
    l4_all = [(n, all_probs.get(n, 0)) for n in LAYER4_OUTCOMES]

    # Use top-N for graph rendering (but pass ALL to stages)
    l1_nodes = l1_all[:7]
    l2_nodes = l2_all[:7]
    l3_nodes = l3_all[:6]
    l4_nodes = l4_all  # all 6

    # Stage-level node type tags
    LAYER_LABELS = {1: 'Root Event', 2: 'Disruption', 3: 'Supply', 4: 'Outcome'}

    def node_color(p):
        if p > 0.7: return '#c0392b'
        if p > 0.5: return '#F16667'
        if p > 0.35: return '#F79767'
        if p > 0.2: return '#F1C40F'
        return '#68BC00'

    def node_border(p):
        if p > 0.5: return '2px solid #ff4444'
        if p > 0.35: return '2px solid #F79767'
        return '2px solid rgba(255,255,255,0.2)'

    def node_glow(p):
        if p > 0.7: return '0 0 14px 4px rgba(192,57,43,0.7), 0 0 4px 1px #c0392b'
        if p > 0.5: return '0 0 10px 3px rgba(241,102,103,0.6)'
        if p > 0.35: return '0 0 8px 2px rgba(247,151,103,0.5)'
        return 'none'

    ICON_MAP = {
        'war': '⚔', 'regional_conflict': '💥', 'cyber_warfare': '💻', 'terrorism': '🎯',
        'pandemic': '🦠', 'epidemic': '🏥', 'earthquake': '🌍', 'flood': '🌊',
        'hurricane': '🌀', 'wildfire': '🔥', 'volcanic_eruption': '🌋',
        'political_coup': '🏛', 'trade_sanctions': '🚫', 'economic_collapse': '📉', 'energy_crisis': '⚡',
        'sanctions_expansion': '🔒', 'currency_volatility': '💱', 'commodity_price_shock': '📦',
        'energy_price_spike': '⛽', 'labor_shortage': '👷', 'factory_shutdown': '🏭',
        'transport_shutdown': '🚢', 'port_closure': '⚓', 'airspace_closure': '✈',
        'telecom_disruption': '📡', 'power_grid_failure': '🔌', 'financial_market_crash': '💸',
        'supplier_failure': '🏗', 'inventory_shortage': '📉', 'logistics_delay': '🚛',
        'shipping_route_disruption': '🗺', 'manufacturing_delay': '⚙', 'equipment_delivery_delay': '📦',
        'commodity_cost_escalation': '💰', 'insurance_premium_spike': '🛡',
        'project_delay': '⏱', 'cost_overrun': '💸', 'contract_suspension': '⏸',
        'insurance_claim': '📋', 'fm_invocation': '⚖', 'contract_termination': '❌',
    }

    def make_stage(nodes, stage_num, x_base, width=170, y_gap=105):
        rf_nodes = []
        for i, (n, p) in enumerate(nodes):
            icon = ICON_MAP.get(n, '●')
            label = n.replace('_', ' ').title()
            rf_nodes.append({
                'id': n,
                'type': 'cascadeNode',
                'data': {
                    'label': label,
                    'probability': round(p, 4),
                    'layer': stage_num,
                    'layerLabel': LAYER_LABELS[stage_num],
                    'icon': icon,
                    'rank': i + 1,
                },
                'position': {'x': x_base, 'y': 30 + i * y_gap},
                'style': {
                    'background': f'linear-gradient(135deg, {node_color(p)}cc, {node_color(p)}88)',
                    'color': '#fff',
                    'border': node_border(p),
                    'borderRadius': '12px',
                    'padding': '10px 12px',
                    'fontSize': '10px',
                    'width': width,
                    'boxShadow': node_glow(p),
                    'backdropFilter': 'blur(4px)',
                },
            })
        return rf_nodes

    # Single-column layout, equal x spacing per stage
    nodes = (
        make_stage(l1_nodes, 1,  40, width=155, y_gap=100) +
        make_stage(l2_nodes, 2, 265, width=160, y_gap=100) +
        make_stage(l3_nodes, 3, 490, width=165, y_gap=110) +
        make_stage(l4_nodes, 4, 720, width=170, y_gap=110)
    )

    # Add stage header/separator nodes
    STAGE_HEADERS = [
        ('hdr1', 'Stage 1: Root Events',  40,  -35),
        ('hdr2', 'Stage 2: Disruptions',  265, -35),
        ('hdr3', 'Stage 3: Supply Chain', 490, -35),
        ('hdr4', 'Stage 4: Outcomes',     720, -35),
    ]
    STAGE_COLORS = ['#4C8EDA', '#F79767', '#9063CD', '#F16667']
    for idx, (hid, hlabel, hx, hy) in enumerate(STAGE_HEADERS):
        nodes.append({
            'id': hid,
            'type': 'stageHeader',
            'data': {'label': hlabel, 'stageNum': idx + 1},
            'position': {'x': hx - 10, 'y': hy},
            'style': {
                'background': f'linear-gradient(90deg, {STAGE_COLORS[idx]}44, {STAGE_COLORS[idx]}22)',
                'color': STAGE_COLORS[idx],
                'border': f'1px solid {STAGE_COLORS[idx]}88',
                'borderRadius': '8px',
                'padding': '4px 12px',
                'fontSize': '10px',
                'fontWeight': 'bold',
                'width': 190,
                'letterSpacing': '0.05em',
                'textTransform': 'uppercase',
            },
            'draggable': False,
            'selectable': False,
        })

    # Domain-knowledge causal map: which L1 event primarily causes which L2 disruptions
    L1_TO_L2 = {
        'war':               ['sanctions_expansion', 'energy_price_spike'],
        'regional_conflict': ['transport_shutdown', 'commodity_price_shock'],
        'cyber_warfare':     ['telecom_disruption', 'power_grid_failure'],
        'terrorism':         ['transport_shutdown', 'port_closure'],
        'pandemic':          ['labor_shortage', 'factory_shutdown'],
        'epidemic':          ['labor_shortage', 'factory_shutdown'],
        'earthquake':        ['power_grid_failure', 'port_closure'],
        'flood':             ['transport_shutdown', 'factory_shutdown'],
        'hurricane':         ['port_closure', 'airspace_closure'],
        'wildfire':          ['power_grid_failure', 'energy_price_spike'],
        'volcanic_eruption': ['airspace_closure', 'transport_shutdown'],
        'political_coup':    ['sanctions_expansion', 'financial_market_crash'],
        'trade_sanctions':   ['sanctions_expansion', 'commodity_price_shock'],
        'economic_collapse': ['financial_market_crash', 'currency_volatility'],
        'energy_crisis':     ['energy_price_spike', 'factory_shutdown'],
    }
    # Domain-knowledge causal map: which L2 disruption primarily causes which L3 impacts
    L2_TO_L3 = {
        'sanctions_expansion':    ['supplier_failure', 'commodity_cost_escalation'],
        'currency_volatility':    ['commodity_cost_escalation', 'insurance_premium_spike'],
        'commodity_price_shock':  ['commodity_cost_escalation', 'inventory_shortage'],
        'energy_price_spike':     ['manufacturing_delay', 'commodity_cost_escalation'],
        'labor_shortage':         ['manufacturing_delay', 'equipment_delivery_delay'],
        'factory_shutdown':       ['manufacturing_delay', 'inventory_shortage'],
        'transport_shutdown':     ['logistics_delay', 'shipping_route_disruption'],
        'port_closure':           ['shipping_route_disruption', 'inventory_shortage'],
        'airspace_closure':       ['logistics_delay', 'equipment_delivery_delay'],
        'telecom_disruption':     ['logistics_delay', 'supplier_failure'],
        'power_grid_failure':     ['manufacturing_delay', 'factory_shutdown'],
        'financial_market_crash': ['insurance_premium_spike', 'commodity_cost_escalation'],
    }
    # Domain-knowledge causal map: which L3 impact primarily drives which L4 outcomes
    L3_TO_L4 = {
        'supplier_failure':           ['project_delay', 'contract_suspension'],
        'inventory_shortage':         ['project_delay', 'cost_overrun'],
        'logistics_delay':            ['project_delay', 'cost_overrun'],
        'shipping_route_disruption':  ['project_delay', 'fm_invocation'],
        'manufacturing_delay':        ['project_delay', 'cost_overrun'],
        'equipment_delivery_delay':   ['project_delay', 'contract_suspension'],
        'commodity_cost_escalation':  ['cost_overrun', 'fm_invocation'],
        'insurance_premium_spike':    ['insurance_claim', 'cost_overrun'],
    }

    l1_set = {n for n, _ in l1_nodes}
    l2_set = {n for n, _ in l2_nodes}
    l3_set = {n for n, _ in l3_nodes}
    l4_set = {n for n, _ in l4_nodes}
    l1_prob = {n: p for n, p in l1_nodes}
    l2_prob = {n: p for n, p in l2_nodes}
    l3_prob = {n: p for n, p in l3_nodes}
    l4_prob = {n: p for n, p in l4_nodes}

    edges = []
    eid = 0
    seen_edges = set()

    def add_edge(src, tgt, sp, tp, color, edge_type='smoothstep'):
        nonlocal eid
        key = (src, tgt)
        if key in seen_edges:
            return
        seen_edges.add(key)
        strength = (sp + tp) / 2
        width = max(1.2, min(4.5, 1 + strength * 5))
        animated = strength > 0.5
        edges.append({
            'id': f'e{eid}',
            'source': src,
            'target': tgt,
            'type': edge_type,
            'animated': animated,
            'style': {
                'stroke': color,
                'strokeWidth': round(width, 1),
                'opacity': max(0.5, min(0.95, 0.45 + strength * 0.6)),
            },
            'label': f'{round(strength*100)}%',
            'labelStyle': {'fill': '#e5e7eb', 'fontSize': 9, 'fontWeight': 700},
            'labelBgStyle': {'fill': '#111827', 'fillOpacity': 0.85, 'rx': 3},
            'markerEnd': {'type': 'arrowclosed', 'color': color, 'width': 12, 'height': 12},
        })
        eid += 1

    # L1 → L2: only domain-mapped connections for nodes visible in the graph
    for src, sp in l1_nodes:
        for tgt in L1_TO_L2.get(src, []):
            if tgt in l2_set:
                add_edge(src, tgt, sp, l2_prob[tgt], '#60a5fa')

    # L2 → L3: only domain-mapped connections
    for src, sp in l2_nodes:
        for tgt in L2_TO_L3.get(src, []):
            if tgt in l3_set:
                add_edge(src, tgt, sp, l3_prob[tgt], '#fb923c')

    # L3 → L4: only domain-mapped connections
    for src, sp in l3_nodes:
        for tgt in L3_TO_L4.get(src, []):
            if tgt in l4_set:
                add_edge(src, tgt, sp, l4_prob.get(tgt, 0), '#a78bfa')

    mc = monte_carlo_loss(fm_risk, contract_value, {n: all_probs.get(n, 0) for n in LAYER4_OUTCOMES})

    # Propagation amplification: how much each stage amplifies risk
    s1_avg = sum(p for _,p in l1_nodes) / max(len(l1_nodes), 1)
    s2_avg = sum(p for _,p in l2_nodes) / max(len(l2_nodes), 1)
    s3_avg = sum(p for _,p in l3_nodes) / max(len(l3_nodes), 1)
    s4_avg = sum(p for _,p in l4_nodes) / max(len(l4_nodes), 1)

    return {
        'nodes': nodes,
        'edges': edges,
        'fm_risk_score': round(fm_risk, 4),
        'expected_loss_usd': mc['expected_loss'],
        'p50_loss': mc.get('p50', 0),
        'p95_loss': mc.get('p95', 0),
        'p99_loss': mc.get('p99', 0),
        'worst_case_loss': mc.get('worst_case', 0),
        'stages': [
            {
                'stage': 1, 'label': 'Root FM Events',
                'top_node': l1_nodes[0][0] if l1_nodes else '', 'top_prob': round(l1_nodes[0][1], 4) if l1_nodes else 0,
                'all_nodes': [{'node': n, 'prob': round(p, 4)} for n, p in l1_nodes],
                'avg_prob': round(s1_avg, 4),
                'active_count': len([p for _,p in l1_nodes if p > 0.12]),
                'description': 'Geopolitical, natural, and systemic events that trigger FM conditions',
            },
            {
                'stage': 2, 'label': 'Operational Disruptions',
                'top_node': l2_nodes[0][0] if l2_nodes else '', 'top_prob': round(l2_nodes[0][1], 4) if l2_nodes else 0,
                'all_nodes': [{'node': n, 'prob': round(p, 4)} for n, p in l2_nodes],
                'avg_prob': round(s2_avg, 4),
                'active_count': len([p for _,p in l2_nodes if p > 0.4]),
                'amplification': round(s2_avg / max(s1_avg, 0.01), 2),
                'description': 'Operational breakdowns directly caused by root FM events',
            },
            {
                'stage': 3, 'label': 'Supply Chain Impacts',
                'top_node': l3_nodes[0][0] if l3_nodes else '', 'top_prob': round(l3_nodes[0][1], 4) if l3_nodes else 0,
                'all_nodes': [{'node': n, 'prob': round(p, 4)} for n, p in l3_nodes],
                'avg_prob': round(s3_avg, 4),
                'active_count': len([p for _,p in l3_nodes if p > 0.4]),
                'amplification': round(s3_avg / max(s2_avg, 0.01), 2),
                'description': 'Physical supply chain disruptions propagated from operational failures',
            },
            {
                'stage': 4, 'label': 'Contract Outcomes',
                'top_node': l4_nodes[0][0] if l4_nodes else '', 'top_prob': round(l4_nodes[0][1], 4) if l4_nodes else 0,
                'all_nodes': [{'node': n, 'prob': round(p, 4)} for n, p in l4_nodes],
                'avg_prob': round(s4_avg, 4),
                'active_count': len([p for _,p in l4_nodes if p > 0.4]),
                'amplification': round(s4_avg / max(s3_avg, 0.01), 2),
                'description': 'Contractual and financial outcomes from the supply chain cascade',
            },
        ],
        'cascade_amplification': round(s4_avg / max(s1_avg, 0.01), 2),
        'critical_path': [
            l1_nodes[0][0] if l1_nodes else '',
            l2_nodes[0][0] if l2_nodes else '',
            l3_nodes[0][0] if l3_nodes else '',
            l4_nodes[0][0] if l4_nodes else '',
        ],
        'total_active_nodes': sum(1 for _,p in (l1_nodes+l2_nodes+l3_nodes+l4_nodes) if p > 0.12),
    }
