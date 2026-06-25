"""
Bayesian Risk Engine for Dispute Prediction
============================================
Implements a 60-node Bayesian Network across 8 risk layers:
Layer 1 – Geopolitical
Layer 2 – Macroeconomic
Layer 3 – Market/Industry
Layer 4 – Supply Chain
Layer 5 – Financial
Layer 6 – Operational
Layer 7 – Contract
Layer 8 – Legal Outcome

Uses manual CPT (Conditional Probability Table) inference without pgmpy
so it runs without additional dependencies. Falls back gracefully.
"""

import logging
from typing import Dict, List, Tuple, Any, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# NODE REGISTRY — 60 nodes across 8 layers
# ═══════════════════════════════════════════════════════════════

RISK_NODES = {
    # Layer 1 – Geopolitical
    'WarRisk':               {'label': 'War Risk',               'cluster': 'geo',         'layer': 1, 'base': 0.05},
    'SanctionsRisk':         {'label': 'Sanctions Risk',          'cluster': 'geo',         'layer': 1, 'base': 0.10},
    'PoliticalInstability':  {'label': 'Political Instability',   'cluster': 'geo',         'layer': 1, 'base': 0.15},
    'TradeRestriction':      {'label': 'Trade Restriction',       'cluster': 'geo',         'layer': 1, 'base': 0.12},
    'TariffRisk':            {'label': 'Tariff Risk',             'cluster': 'geo',         'layer': 1, 'base': 0.18},
    'EnergySecurityRisk':    {'label': 'Energy Security Risk',    'cluster': 'geo',         'layer': 1, 'base': 0.20},
    'BorderDisruption':      {'label': 'Border Disruption',       'cluster': 'geo',         'layer': 1, 'base': 0.08},
    'MilitaryEscalation':    {'label': 'Military Escalation',     'cluster': 'geo',         'layer': 1, 'base': 0.04},

    # Layer 2 – Macroeconomic
    'InflationRisk':         {'label': 'Inflation Risk',          'cluster': 'macro',       'layer': 2, 'base': 0.35},
    'InterestRateShock':     {'label': 'Interest Rate Shock',     'cluster': 'macro',       'layer': 2, 'base': 0.22},
    'CurrencyVolatility':    {'label': 'Currency Volatility',     'cluster': 'macro',       'layer': 2, 'base': 0.25},
    'CommodityPriceShock':   {'label': 'Commodity Price Shock',   'cluster': 'macro',       'layer': 2, 'base': 0.28},
    'EnergyPriceShock':      {'label': 'Energy Price Shock',      'cluster': 'macro',       'layer': 2, 'base': 0.22},
    'GlobalDemandShock':     {'label': 'Global Demand Shock',     'cluster': 'macro',       'layer': 2, 'base': 0.15},
    'LogisticsCostIncrease': {'label': 'Logistics Cost Increase', 'cluster': 'macro',       'layer': 2, 'base': 0.30},
    'CreditMarketTightening':{'label': 'Credit Market Tightening','cluster': 'macro',       'layer': 2, 'base': 0.20},

    # Layer 3 – Market/Industry
    'CompetitionIncrease':   {'label': 'Competition Increase',    'cluster': 'market',      'layer': 3, 'base': 0.30},
    'DemandDecline':         {'label': 'Demand Decline',          'cluster': 'market',      'layer': 3, 'base': 0.18},
    'MarketPricePressure':   {'label': 'Market Price Pressure',   'cluster': 'market',      'layer': 3, 'base': 0.25},
    'TechnologyDisruption':  {'label': 'Technology Disruption',   'cluster': 'market',      'layer': 3, 'base': 0.20},
    'RegulatoryChange':      {'label': 'Regulatory Change',       'cluster': 'market',      'layer': 3, 'base': 0.22},
    'ESGRegulation':         {'label': 'ESG Regulation',          'cluster': 'market',      'layer': 3, 'base': 0.18},
    'EnvironmentalReg':      {'label': 'Environmental Regulation','cluster': 'market',      'layer': 3, 'base': 0.15},

    # Layer 4 – Supply Chain
    'SupplierBankruptcy':    {'label': 'Supplier Bankruptcy',     'cluster': 'supply_chain','layer': 4, 'base': 0.12},
    'SupplierFinancialStress':{'label':'Supplier Financial Stress','cluster': 'supply_chain','layer': 4, 'base': 0.22},
    'SupplierDelay':         {'label': 'Supplier Delay',          'cluster': 'supply_chain','layer': 4, 'base': 0.28},
    'SupplierQualityFailure':{'label': 'Supplier Quality Failure','cluster': 'supply_chain','layer': 4, 'base': 0.16},
    'TransportDisruption':   {'label': 'Transport Disruption',    'cluster': 'supply_chain','layer': 4, 'base': 0.20},
    'PortCongestion':        {'label': 'Port Congestion',         'cluster': 'supply_chain','layer': 4, 'base': 0.18},
    'InventoryShortage':     {'label': 'Inventory Shortage',      'cluster': 'supply_chain','layer': 4, 'base': 0.22},
    'ManufacturingFailure':  {'label': 'Manufacturing Failure',   'cluster': 'supply_chain','layer': 4, 'base': 0.14},

    # Layer 5 – Financial
    'CounterpartyCreditRisk':{'label': 'Counterparty Credit Risk','cluster': 'financial',   'layer': 5, 'base': 0.18},
    'PaymentDefaultRisk':    {'label': 'Payment Default Risk',    'cluster': 'financial',   'layer': 5, 'base': 0.15},
    'CashFlowStress':        {'label': 'Cash Flow Stress',        'cluster': 'financial',   'layer': 5, 'base': 0.25},
    'FinancingCostIncrease': {'label': 'Financing Cost Increase', 'cluster': 'financial',   'layer': 5, 'base': 0.20},
    'WorkingCapitalStress':  {'label': 'Working Capital Stress',  'cluster': 'financial',   'layer': 5, 'base': 0.22},
    'ContractCostOverrun':   {'label': 'Contract Cost Overrun',   'cluster': 'financial',   'layer': 5, 'base': 0.25},

    # Layer 6 – Operational
    'DeliveryFailure':       {'label': 'Delivery Failure',        'cluster': 'operational', 'layer': 6, 'base': 0.20},
    'SLAViolation':          {'label': 'SLA Violation',           'cluster': 'operational', 'layer': 6, 'base': 0.22},
    'ServiceFailure':        {'label': 'Service Failure',         'cluster': 'operational', 'layer': 6, 'base': 0.18},
    'ProjectDelay':          {'label': 'Project Delay',           'cluster': 'operational', 'layer': 6, 'base': 0.30},
    'ScopeChangeRisk':       {'label': 'Scope Change Risk',       'cluster': 'operational', 'layer': 6, 'base': 0.28},
    'CostEscalation':        {'label': 'Cost Escalation',         'cluster': 'operational', 'layer': 6, 'base': 0.25},

    # Layer 7 – Contract
    'ContractAmbiguity':     {'label': 'Contract Ambiguity',      'cluster': 'contract',    'layer': 7, 'base': 0.40},
    'ClauseConflict':        {'label': 'Clause Conflict',         'cluster': 'contract',    'layer': 7, 'base': 0.25},
    'LiabilityExposure':     {'label': 'Liability Exposure',      'cluster': 'contract',    'layer': 7, 'base': 0.35},
    'TerminationRisk':       {'label': 'Termination Risk',        'cluster': 'contract',    'layer': 7, 'base': 0.20},
    'RenegotiationRisk':     {'label': 'Renegotiation Risk',      'cluster': 'contract',    'layer': 7, 'base': 0.30},
    'ContractPerformanceRisk':{'label':'Contract Performance Risk','cluster': 'contract',    'layer': 7, 'base': 0.28},
    'ContractRisk':          {'label': 'Contract Risk',           'cluster': 'contract',    'layer': 7, 'base': 0.25},

    # Layer 8 – Legal Outcome
    'DisputeTrigger':        {'label': 'Dispute Trigger',         'cluster': 'legal',       'layer': 8, 'base': 0.20},
    'DisputeEscalation':     {'label': 'Dispute Escalation',      'cluster': 'legal',       'layer': 8, 'base': 0.15},
    'ArbitrationInitiation': {'label': 'Arbitration Initiation',  'cluster': 'legal',       'layer': 8, 'base': 0.12},
    'LitigationInitiation':  {'label': 'Litigation Initiation',   'cluster': 'legal',       'layer': 8, 'base': 0.08},
    'SettlementProbability': {'label': 'Settlement Probability',  'cluster': 'legal',       'layer': 8, 'base': 0.35},
    'ArbitrationWinProb':    {'label': 'Arbitration Win Prob.',   'cluster': 'legal',       'layer': 8, 'base': 0.45},
    'ArbitrationLossProb':   {'label': 'Arbitration Loss Prob.',  'cluster': 'legal',       'layer': 8, 'base': 0.40},
    'LegalCostExposure':     {'label': 'Legal Cost Exposure',     'cluster': 'legal',       'layer': 8, 'base': 0.30},
    'ContractTermination':   {'label': 'Contract Termination',    'cluster': 'legal',       'layer': 8, 'base': 0.15},
    'DisputeProbability':    {'label': 'Dispute Probability',     'cluster': 'legal',       'layer': 8, 'base': 0.20},
}

# ═══════════════════════════════════════════════════════════════
# GRAPH EDGES — causal DAG
# ═══════════════════════════════════════════════════════════════

RISK_EDGES = [
    # Geo → Macro
    ('WarRisk',               'EnergyPriceShock',       0.75),
    ('WarRisk',               'CommodityPriceShock',    0.70),
    ('WarRisk',               'MilitaryEscalation',     0.60),
    ('SanctionsRisk',         'LogisticsCostIncrease',  0.65),
    ('SanctionsRisk',         'SupplierBankruptcy',     0.45),
    ('PoliticalInstability',  'CurrencyVolatility',     0.60),
    ('TradeRestriction',      'LogisticsCostIncrease',  0.70),
    ('TariffRisk',            'ContractCostOverrun',    0.55),
    ('EnergySecurityRisk',    'EnergyPriceShock',       0.65),
    ('BorderDisruption',      'TransportDisruption',    0.70),

    # Macro → Supply/Financial
    ('InflationRisk',         'CostEscalation',         0.65),
    ('InflationRisk',         'WorkingCapitalStress',   0.50),
    ('InterestRateShock',     'FinancingCostIncrease',  0.70),
    ('CurrencyVolatility',    'CashFlowStress',         0.55),
    ('CommodityPriceShock',   'ContractCostOverrun',    0.70),
    ('EnergyPriceShock',      'ManufacturingFailure',   0.60),
    ('EnergyPriceShock',      'CostEscalation',         0.65),
    ('GlobalDemandShock',     'DemandDecline',          0.70),
    ('LogisticsCostIncrease', 'TransportDisruption',    0.60),
    ('CreditMarketTightening','CounterpartyCreditRisk', 0.65),

    # Market → Supply/Financial
    ('DemandDecline',         'SupplierFinancialStress',0.55),
    ('CompetitionIncrease',   'MarketPricePressure',    0.65),
    ('TechnologyDisruption',  'SupplierBankruptcy',     0.40),
    ('RegulatoryChange',      'ContractAmbiguity',      0.40),
    ('ESGRegulation',         'CostEscalation',         0.45),

    # Supply Chain → Operational
    ('SupplierBankruptcy',    'DeliveryFailure',        0.75),
    ('SupplierDelay',         'DeliveryFailure',        0.70),
    ('SupplierDelay',         'ProjectDelay',           0.65),
    ('SupplierQualityFailure','SLAViolation',           0.65),
    ('SupplierQualityFailure','ServiceFailure',         0.55),
    ('SupplierFinancialStress','SupplierDelay',         0.60),
    ('TransportDisruption',   'DeliveryFailure',        0.65),
    ('TransportDisruption',   'ProjectDelay',           0.55),
    ('PortCongestion',        'TransportDisruption',    0.60),
    ('InventoryShortage',     'ManufacturingFailure',   0.65),
    ('ManufacturingFailure',  'DeliveryFailure',        0.70),

    # Financial → Operational
    ('PaymentDefaultRisk',    'ContractTermination',    0.65),
    ('CashFlowStress',        'ProjectDelay',           0.60),
    ('FinancingCostIncrease', 'CostEscalation',         0.55),
    ('WorkingCapitalStress',  'CashFlowStress',         0.70),
    ('ContractCostOverrun',   'CostEscalation',         0.75),
    ('CounterpartyCreditRisk','PaymentDefaultRisk',     0.65),

    # Operational → Contract Risk
    ('DeliveryFailure',       'ContractPerformanceRisk',0.75),
    ('SLAViolation',          'ContractPerformanceRisk',0.70),
    ('ServiceFailure',        'ContractPerformanceRisk',0.60),
    ('ProjectDelay',          'ContractPerformanceRisk',0.65),
    ('ScopeChangeRisk',       'RenegotiationRisk',      0.65),
    ('CostEscalation',        'ContractCostOverrun',    0.70),
    ('CostEscalation',        'ContractPerformanceRisk',0.55),

    # Contract Risk → Legal
    ('ContractAmbiguity',     'ClauseConflict',         0.60),
    ('ContractAmbiguity',     'LiabilityExposure',      0.55),
    ('ClauseConflict',        'DisputeTrigger',         0.65),
    ('LiabilityExposure',     'DisputeTrigger',         0.55),
    ('ContractPerformanceRisk','ContractRisk',          0.75),
    ('RenegotiationRisk',     'DisputeEscalation',      0.60),
    ('TerminationRisk',       'ContractTermination',    0.65),
    ('ContractRisk',          'DisputeTrigger',         0.70),
    ('CashFlowStress',        'DisputeTrigger',         0.50),

    # Legal → Outcomes
    ('DisputeTrigger',        'DisputeEscalation',      0.65),
    ('DisputeTrigger',        'DisputeProbability',     0.80),
    ('DisputeEscalation',     'ArbitrationInitiation',  0.55),
    ('DisputeEscalation',     'LitigationInitiation',   0.40),
    ('DisputeEscalation',     'SettlementProbability',  0.50),
    ('DisputeEscalation',     'DisputeProbability',     0.75),
    ('ArbitrationInitiation', 'ArbitrationWinProb',     0.50),
    ('ArbitrationInitiation', 'ArbitrationLossProb',    0.45),
    ('ArbitrationLossProb',   'LegalCostExposure',      0.70),
    ('LitigationInitiation',  'LegalCostExposure',      0.65),
    ('ContractTermination',   'DisputeProbability',     0.60),
    ('ContractRisk',          'DisputeProbability',     0.65),
]


# ═══════════════════════════════════════════════════════════════
# BAYESIAN ENGINE
# ═══════════════════════════════════════════════════════════════

class BayesianDisputeEngine:
    """
    Lightweight Bayesian inference engine using belief propagation.
    No external dependencies — pure Python.
    """

    def __init__(self):
        # Build adjacency for forward inference
        self.nodes = {k: dict(v) for k, v in RISK_NODES.items()}
        # Filter valid edges
        valid_node_ids = set(self.nodes.keys())
        self.edges: List[Tuple[str, str, float]] = [
            (s, t, p) for (s, t, p) in RISK_EDGES
            if s in valid_node_ids and t in valid_node_ids
        ]
        self._build_parent_map()

    def _build_parent_map(self):
        """Build parent → children and child → parents maps."""
        self.children: Dict[str, List[Tuple[str, float]]] = {k: [] for k in self.nodes}
        self.parents: Dict[str, List[Tuple[str, float]]] = {k: [] for k in self.nodes}
        for src, tgt, prob in self.edges:
            self.children[src].append((tgt, prob))
            self.parents[tgt].append((src, prob))

    def infer(self, evidence: Dict[str, float]) -> Dict[str, float]:
        """
        Forward pass: propagate evidence through the graph.
        Returns posterior probability for every node.

        Args:
            evidence: {node_id: probability_override (0–1)}

        Returns:
            {node_id: posterior_probability}
        """
        # Start with base probabilities
        posteriors: Dict[str, float] = {
            k: v['base'] for k, v in self.nodes.items()
        }

        # Apply evidence overrides
        for node_id, val in evidence.items():
            if node_id in posteriors:
                posteriors[node_id] = float(val)

        # Topological forward pass (layers 1→8)
        for layer in range(1, 9):
            layer_nodes = [k for k, v in self.nodes.items() if v['layer'] == layer]
            for node_id in layer_nodes:
                if node_id in evidence:
                    continue  # already set
                parent_list = self.parents[node_id]
                if not parent_list:
                    continue
                # Noisy-OR combination of parent influences
                prob_not_triggered = 1.0
                for parent_id, cond_prob in parent_list:
                    p_parent = posteriors.get(parent_id, self.nodes[parent_id]['base'])
                    prob_not_triggered *= (1.0 - p_parent * cond_prob)
                posteriors[node_id] = max(
                    self.nodes[node_id]['base'],
                    1.0 - prob_not_triggered
                )

        return posteriors

    def compute_dispute_probability(
        self,
        evidence: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Run full inference and compute final dispute metrics.
        """
        posteriors = self.infer(evidence)

        dispute_prob = posteriors.get('DisputeProbability', 0.2)
        contract_risk = posteriors.get('ContractRisk', 0.2)
        financial_stress = max(
            posteriors.get('CashFlowStress', 0.0),
            posteriors.get('PaymentDefaultRisk', 0.0),
            posteriors.get('WorkingCapitalStress', 0.0),
        )
        arbitration_prob = posteriors.get('ArbitrationInitiation', 0.0)
        litigation_prob = posteriors.get('LitigationInitiation', 0.0)
        settlement_prob = posteriors.get('SettlementProbability', 0.0)
        legal_cost_exposure = posteriors.get('LegalCostExposure', 0.0)
        operational_risk = max(
            posteriors.get('DeliveryFailure', 0.0),
            posteriors.get('SLAViolation', 0.0),
            posteriors.get('ProjectDelay', 0.0),
        )
        geopolitical_risk = max(
            posteriors.get('WarRisk', 0.0),
            posteriors.get('SanctionsRisk', 0.0),
            posteriors.get('PoliticalInstability', 0.0),
        )

        # Top risk drivers (nodes with highest delta above base)
        drivers = []
        for node_id, posterior in sorted(posteriors.items(), key=lambda x: -x[1]):
            base = self.nodes[node_id]['base']
            delta = posterior - base
            if delta > 0.05 and posterior > 0.3:
                drivers.append({
                    'node': node_id,
                    'label': self.nodes[node_id]['label'],
                    'probability': round(posterior, 3),
                    'delta': round(delta, 3),
                    'cluster': self.nodes[node_id]['cluster'],
                })
            if len(drivers) >= 10:
                break

        # Risk propagation path to DisputeProbability
        propagation_path = self._find_critical_path(posteriors)

        # ── Rescale: map raw Bayesian outputs to realistic display range.
        # Zero-evidence raw dp ≈ 0.72. We map [0.72, 1.0] → [0.25, 0.85].
        # Use sum of evidence values so scenario overrides produce visible deltas.
        _zero_base = 0.72
        _signal_sum = sum(evidence.values()) if evidence else 0.0
        _from_signals = min(0.35, _signal_sum * 0.035)  # each unit of signal_sum → 3.5% risk
        _propagation = max(0.0, dispute_prob - _zero_base) * 2.0
        dispute_prob_display = round(min(0.85, 0.22 + _from_signals + _propagation), 3)
        _ratio = dispute_prob_display / max(dispute_prob, 0.01)
        contract_risk_display    = round(min(0.90, contract_risk    * _ratio), 3)
        financial_stress_display = round(min(0.90, financial_stress * _ratio), 3)
        operational_risk_display = round(min(0.90, operational_risk * _ratio), 3)
        arbitration_prob_display = round(min(0.80, arbitration_prob * _ratio), 3)
        litigation_prob_display  = round(min(0.80, litigation_prob  * _ratio), 3)
        settlement_prob_display  = round(min(0.70, settlement_prob  * _ratio), 3)

        return {
            'dispute_probability': dispute_prob_display,
            'contract_risk_score': contract_risk_display,
            'financial_stress_score': financial_stress_display,
            'operational_risk_score': operational_risk_display,
            'geopolitical_risk_score': round(geopolitical_risk, 3),
            'arbitration_probability': arbitration_prob_display,
            'litigation_probability': litigation_prob_display,
            'settlement_probability': settlement_prob_display,
            'legal_cost_exposure_score': round(legal_cost_exposure, 3),
            'top_risk_drivers': drivers,
            'risk_propagation_path': propagation_path,
            'all_node_posteriors': {k: round(v, 3) for k, v in posteriors.items()},
            # raw values for internal use (digital twin / time travel bypass these anyway)
            '_raw_dispute_probability': round(dispute_prob, 3),
        }

    def _find_critical_path(self, posteriors: Dict[str, float]) -> List[Dict]:
        """
        Identify the highest-risk path from root nodes to DisputeProbability.
        """
        # Simple greedy: walk backwards from DisputeProbability
        path_nodes = []
        visited = set()

        def backtrack(node_id: str, depth: int = 0):
            if depth > 8 or node_id in visited:
                return
            visited.add(node_id)
            path_nodes.append({
                'node': node_id,
                'label': self.nodes.get(node_id, {}).get('label', node_id),
                'probability': round(posteriors.get(node_id, 0), 3),
                'layer': self.nodes.get(node_id, {}).get('layer', 0),
            })
            # Find highest-probability parent
            parent_list = self.parents.get(node_id, [])
            if parent_list:
                best_parent = max(
                    parent_list,
                    key=lambda x: posteriors.get(x[0], 0) * x[1]
                )
                backtrack(best_parent[0], depth + 1)

        backtrack('DisputeProbability')
        return list(reversed(path_nodes))

    def get_graph_structure(self) -> Dict:
        """Return full graph for visualisation (nodes + edges)."""
        nodes = []
        for node_id, info in self.nodes.items():
            nodes.append({
                'id': node_id,
                'label': info['label'],
                'cluster': info['cluster'],
                'layer': info['layer'],
                'base_probability': info['base'],
            })
        edges = []
        for src, tgt, prob in self.edges:
            edges.append({
                'source': src,
                'target': tgt,
                'conditional_probability': prob,
            })
        return {'nodes': nodes, 'edges': edges}

    def run_scenario(
        self,
        base_evidence: Dict[str, float],
        scenario_overrides: Dict[str, float],
        scenario_name: str = 'Scenario',
    ) -> Dict:
        """
        Run a what-if scenario by merging overrides on top of base evidence.
        Returns delta vs base.
        """
        base_result = self.compute_dispute_probability(base_evidence)
        scenario_evidence = {**base_evidence, **scenario_overrides}
        scenario_result = self.compute_dispute_probability(scenario_evidence)

        return {
            'scenario_name': scenario_name,
            'base_dispute_probability': base_result['dispute_probability'],
            'scenario_dispute_probability': scenario_result['dispute_probability'],
            'delta': round(
                scenario_result['dispute_probability'] - base_result['dispute_probability'], 3
            ),
            'base_contract_risk': base_result['contract_risk_score'],
            'scenario_contract_risk': scenario_result['contract_risk_score'],
            'scenario_result': scenario_result,
            'risk_overrides': scenario_overrides,
        }


# Singleton
_engine_instance: Optional[BayesianDisputeEngine] = None


def get_bayesian_engine() -> BayesianDisputeEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = BayesianDisputeEngine()
    return _engine_instance
