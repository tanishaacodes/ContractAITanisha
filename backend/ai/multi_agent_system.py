"""
Multi-Agent Negotiation System
================================
Simulates 5 autonomous agents negotiating contract terms:
1. Buyer Agent      - Minimize cost, maximize protection
2. Supplier Agent   - Maximize revenue, minimize liability
3. Regulator Agent  - Ensure compliance, fair terms
4. Risk Agent       - Minimize dispute probability
5. Finance Agent    - Optimize cash flow, reduce exposure

Each agent proposes changes, and a consensus mechanism determines
the final contract configuration.
"""

import logging
import os
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Lazy-loaded Bayesian engine
_bayesian_engine = None

def _get_bayesian_engine():
    global _bayesian_engine
    if _bayesian_engine is None:
        try:
            import sys
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if backend_dir not in sys.path:
                sys.path.insert(0, backend_dir)
            from dispute_predictor.bayesian_engine import get_bayesian_engine
            _bayesian_engine = get_bayesian_engine()
        except Exception as e:
            logger.warning(f"Bayesian engine unavailable in multi-agent system: {e}")
    return _bayesian_engine


@dataclass
class AgentProfile:
    """Agent configuration and objectives"""
    name: str
    agent_type: str
    objective: str
    strategy: str
    weight: float  # Importance weight in consensus (0-1)


# ═══════════════════════════════════════════════════════════════
# Agent Definitions
# ═══════════════════════════════════════════════════════════════

AGENT_PROFILES = {
    'buyer': AgentProfile(
        name="Buyer Agent",
        agent_type="buyer",
        objective="Minimize cost, maximize protection",
        strategy="Aggressive cost reduction",
        weight=0.25
    ),
    'supplier': AgentProfile(
        name="Supplier Agent",
        agent_type="supplier",
        objective="Maximize revenue, minimize liability",
        strategy="Defensive profit maximization",
        weight=0.25
    ),
    'regulator': AgentProfile(
        name="Regulator Agent",
        agent_type="regulator",
        objective="Ensure compliance, fair terms",
        strategy="Balanced regulatory oversight",
        weight=0.20
    ),
    'risk': AgentProfile(
        name="Risk Agent",
        agent_type="risk",
        objective="Minimize dispute probability",
        strategy="Conservative risk mitigation",
        weight=0.20
    ),
    'finance': AgentProfile(
        name="Finance Agent",
        agent_type="finance",
        objective="Optimize cash flow, reduce exposure",
        strategy="Financial optimization",
        weight=0.10
    ),
}


# ═══════════════════════════════════════════════════════════════
# Agent Decision Logic
# ═══════════════════════════════════════════════════════════════

class Agent:
    """Base agent class"""

    def __init__(self, profile: AgentProfile):
        self.profile = profile

    def propose_changes(self, contract: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Propose contract modifications based on agent's objectives.

        Returns:
            List of actions: [
                {
                    'clause': str,
                    'type': 'increase'|'decrease',
                    'description': str,
                    'value_before': Any,
                    'value_after': Any,
                }
            ]
        """
        raise NotImplementedError


class BuyerAgent(Agent):
    """Buyer agent: minimize cost, reduce delivery time, increase protections"""

    def propose_changes(self, contract: Dict[str, Any]) -> List[Dict[str, Any]]:
        actions = []

        # Reduce price
        if contract['price'] > 90:
            actions.append({
                'clause': 'price',
                'type': 'decrease',
                'description': 'Reduce price by 10%',
                'value_before': contract['price'],
                'value_after': max(80, contract['price'] - 10),
            })

        # Reduce delivery time
        if contract['delivery_days'] > 25:
            actions.append({
                'clause': 'delivery_days',
                'type': 'decrease',
                'description': 'Accelerate delivery',
                'value_before': contract['delivery_days'],
                'value_after': max(20, contract['delivery_days'] - 5),
            })

        # Increase liability cap (more protection for buyer)
        if contract['liability_cap'] < 0.8:
            actions.append({
                'clause': 'liability_cap',
                'type': 'increase',
                'description': 'Increase liability coverage',
                'value_before': contract['liability_cap'],
                'value_after': min(1.0, contract['liability_cap'] + 0.2),
            })

        return actions


class SupplierAgent(Agent):
    """Supplier agent: maximize revenue, extend delivery, reduce liability"""

    def propose_changes(self, contract: Dict[str, Any]) -> List[Dict[str, Any]]:
        actions = []

        # Increase price
        if contract['price'] < 130:
            actions.append({
                'clause': 'price',
                'type': 'increase',
                'description': 'Increase price by 10%',
                'value_before': contract['price'],
                'value_after': min(150, contract['price'] + 10),
            })

        # Extend delivery time
        if contract['delivery_days'] < 40:
            actions.append({
                'clause': 'delivery_days',
                'type': 'increase',
                'description': 'Extend delivery timeline',
                'value_before': contract['delivery_days'],
                'value_after': min(50, contract['delivery_days'] + 5),
            })

        # Reduce liability cap
        if contract['liability_cap'] > 0.3:
            actions.append({
                'clause': 'liability_cap',
                'type': 'decrease',
                'description': 'Limit liability exposure',
                'value_before': contract['liability_cap'],
                'value_after': max(0.2, contract['liability_cap'] - 0.1),
            })

        return actions


class RegulatorAgent(Agent):
    """Regulator agent: ensure compliance, balanced terms, force majeure"""

    def propose_changes(self, contract: Dict[str, Any]) -> List[Dict[str, Any]]:
        actions = []

        # Ensure force majeure clause
        if contract['force_majeure'] == 0:
            actions.append({
                'clause': 'force_majeure',
                'type': 'increase',
                'description': 'Add force majeure protection',
                'value_before': 0,
                'value_after': 1,
            })

        # Ensure minimum liability cap (regulatory requirement)
        if contract['liability_cap'] < 0.4:
            actions.append({
                'clause': 'liability_cap',
                'type': 'increase',
                'description': 'Meet regulatory minimum liability',
                'value_before': contract['liability_cap'],
                'value_after': 0.4,
            })

        # Ensure reasonable payment terms
        if contract['payment_terms'] > 90:
            actions.append({
                'clause': 'payment_terms',
                'type': 'decrease',
                'description': 'Reduce payment terms to fair range',
                'value_before': contract['payment_terms'],
                'value_after': 90,
            })

        return actions


class RiskAgent(Agent):
    """Risk agent: minimize dispute probability, balanced terms"""

    def propose_changes(self, contract: Dict[str, Any]) -> List[Dict[str, Any]]:
        actions = []

        # Ensure force majeure (reduces risk)
        if contract['force_majeure'] == 0:
            actions.append({
                'clause': 'force_majeure',
                'type': 'increase',
                'description': 'Add force majeure to reduce dispute risk',
                'value_before': 0,
                'value_after': 1,
            })

        # Moderate liability cap (too low or too high increases risk)
        if contract['liability_cap'] < 0.4 or contract['liability_cap'] > 0.7:
            target = 0.5
            actions.append({
                'clause': 'liability_cap',
                'type': 'adjust',
                'description': 'Balance liability cap to reduce dispute risk',
                'value_before': contract['liability_cap'],
                'value_after': target,
            })

        # Reasonable delivery timeline
        if contract['delivery_days'] > 45:
            actions.append({
                'clause': 'delivery_days',
                'type': 'decrease',
                'description': 'Reduce overly long delivery to avoid disputes',
                'value_before': contract['delivery_days'],
                'value_after': 40,
            })

        return actions


class FinanceAgent(Agent):
    """Finance agent: optimize cash flow, reduce payment terms"""

    def propose_changes(self, contract: Dict[str, Any]) -> List[Dict[str, Any]]:
        actions = []

        # Reduce payment terms (faster cash flow)
        if contract['payment_terms'] > 50:
            actions.append({
                'clause': 'payment_terms',
                'type': 'decrease',
                'description': 'Accelerate payment for better cash flow',
                'value_before': contract['payment_terms'],
                'value_after': max(30, contract['payment_terms'] - 15),
            })

        # Reduce termination penalty (lower exposure)
        if contract['termination_penalty'] > 8:
            actions.append({
                'clause': 'termination_penalty',
                'type': 'decrease',
                'description': 'Reduce termination penalty exposure',
                'value_before': contract['termination_penalty'],
                'value_after': max(5, contract['termination_penalty'] - 3),
            })

        return actions


# ═══════════════════════════════════════════════════════════════
# Consensus Mechanism
# ═══════════════════════════════════════════════════════════════

def weighted_consensus(
    proposals: Dict[str, List[Dict[str, Any]]],
    initial_contract: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply weighted consensus to agent proposals.

    Each agent has a weight, and the final value for each clause
    is a weighted average of proposed changes.
    """
    final_contract = initial_contract.copy()

    # Aggregate proposals by clause
    clause_proposals = {}

    for agent_type, actions in proposals.items():
        weight = AGENT_PROFILES[agent_type].weight

        for action in actions:
            clause = action['clause']
            if clause not in clause_proposals:
                clause_proposals[clause] = []

            clause_proposals[clause].append({
                'agent': agent_type,
                'value': action['value_after'],
                'weight': weight,
            })

    # Calculate weighted average for each clause
    for clause, agent_proposals in clause_proposals.items():
        if not agent_proposals:
            continue

        # Weighted average
        total_weight = sum(p['weight'] for p in agent_proposals)
        weighted_sum = sum(p['value'] * p['weight'] for p in agent_proposals)

        if total_weight > 0:
            final_contract[clause] = round(weighted_sum / total_weight, 2)

    return final_contract


# ═══════════════════════════════════════════════════════════════
# Main Multi-Agent System
# ═══════════════════════════════════════════════════════════════

class MultiAgentNegotiationSystem:
    """Orchestrates multi-agent contract negotiation"""

    def __init__(self):
        self.agents = {
            'buyer': BuyerAgent(AGENT_PROFILES['buyer']),
            'supplier': SupplierAgent(AGENT_PROFILES['supplier']),
            'regulator': RegulatorAgent(AGENT_PROFILES['regulator']),
            'risk': RiskAgent(AGENT_PROFILES['risk']),
            'finance': FinanceAgent(AGENT_PROFILES['finance']),
        }

    def negotiate(
        self,
        initial_contract: Dict[str, Any],
        max_rounds: int = 5
    ) -> Dict[str, Any]:
        """
        Run multi-agent negotiation.

        Returns:
            {
                'final_contract': Dict,
                'initial_contract': Dict,
                'rounds': List[Dict],  # Round-by-round details
                'agent_decisions': Dict,  # Final agent decisions
                'dispute_risk_reduction': float,
            }
        """
        current_contract = initial_contract.copy()
        history = []

        for round_num in range(max_rounds):
            logger.info(f"Negotiation round {round_num + 1}/{max_rounds}")

            # Each agent proposes changes
            proposals = {}
            for agent_type, agent in self.agents.items():
                actions = agent.propose_changes(current_contract)
                proposals[agent_type] = actions

            # Apply consensus
            new_contract = weighted_consensus(proposals, current_contract)

            # Record round
            history.append({
                'round': round_num + 1,
                'contract': new_contract.copy(),
                'proposals': proposals,
            })

            # Check for convergence (no significant changes)
            if self._has_converged(current_contract, new_contract):
                logger.info(f"Negotiation converged at round {round_num + 1}")
                break

            current_contract = new_contract

        # Calculate dispute risk reduction (simplified)
        initial_risk = self._estimate_dispute_risk(initial_contract)
        final_risk = self._estimate_dispute_risk(current_contract)
        risk_reduction = initial_risk - final_risk

        # Build agent decisions summary
        agent_decisions = self._build_agent_decisions(proposals, initial_contract, current_contract)

        return {
            'final_contract': current_contract,
            'initial_contract': initial_contract,
            'rounds': history,
            'agent_decisions': agent_decisions,
            'dispute_risk_reduction': risk_reduction,
            'initial_dispute_risk': initial_risk,
            'final_dispute_risk': final_risk,
        }

    def _has_converged(
        self,
        old_contract: Dict[str, Any],
        new_contract: Dict[str, Any],
        threshold: float = 0.01
    ) -> bool:
        """Check if negotiation has converged"""
        total_change = 0.0
        for key in old_contract:
            if isinstance(old_contract[key], (int, float)):
                total_change += abs(old_contract[key] - new_contract.get(key, 0))

        return total_change < threshold

    def _estimate_dispute_risk(self, contract: Dict[str, Any]) -> float:
        """Estimate dispute risk — direct formula, bypasses Bayesian saturation."""
        dp = 0.30
        dp += max(0, (float(contract.get('payment_terms', 60)) - 30) / 200)
        dp += max(0, (float(contract.get('delivery_days', 30)) - 25) / 250)
        dp += max(0, (0.5 - float(contract.get('liability_cap', 0.3))) * 0.25)
        dp += max(0, (float(contract.get('termination_penalty', 10)) - 5) / 100)
        dp -= contract.get('force_majeure', 1) * 0.03
        dp -= max(0, (float(contract.get('price', 100)) - 100) / 1000)
        return round(min(0.85, max(0.20, dp)), 3)

    def _build_agent_decisions(
        self,
        proposals: Dict[str, List[Dict[str, Any]]],
        initial: Dict[str, Any],
        final: Dict[str, Any]
    ) -> Dict[str, Dict]:
        """Build agent decision summary for frontend"""
        agent_decisions = {}

        initial_risk = self._estimate_dispute_risk(initial)
        final_risk = self._estimate_dispute_risk(final)

        for agent_type, actions in proposals.items():
            approved = False
            impact_cost = 0.0

            # Build agent-specific state by applying only this agent's changes
            agent_state = dict(initial)
            for action in actions:
                clause = action['clause']
                if final.get(clause) != initial.get(clause):
                    approved = True
                    agent_state[clause] = final[clause]

            agent_risk = self._estimate_dispute_risk(agent_state)
            impact_dispute = round((agent_risk - initial_risk) * 100, 1)

            # Cost impact: calculate based on actual parameter changes
            # Use price as proxy for contract value (price typically in thousands)
            contract_value = initial.get('price', 100) * 10000  # e.g., price=110 → $1.1M
            impact_cost = 0.0

            # Price change impact (direct cost)
            price_delta = agent_state.get('price', 100) - initial.get('price', 100)
            if price_delta != 0:
                impact_cost += price_delta * 10000

            # Delivery days impact (delay costs)
            delivery_delta = agent_state.get('delivery_days', 0) - initial.get('delivery_days', 0)
            if delivery_delta != 0:
                impact_cost += delivery_delta * (contract_value * 0.001)

            # Liability cap impact
            liability_delta = agent_state.get('liability_cap', 0) - initial.get('liability_cap', 0)
            if liability_delta != 0:
                impact_cost += liability_delta * (contract_value * 0.05)

            # Payment terms impact (cash flow)
            payment_delta = agent_state.get('payment_terms', 0) - initial.get('payment_terms', 0)
            if payment_delta != 0:
                impact_cost += payment_delta * (contract_value * 0.0004)

            # Termination penalty impact
            termination_delta = agent_state.get('termination_penalty', 0) - initial.get('termination_penalty', 0)
            if termination_delta != 0:
                impact_cost += termination_delta * (contract_value * 0.0015)

            impact_cost = round(impact_cost, 0)

            rationale = AGENT_PROFILES[agent_type].objective

            agent_decisions[agent_type] = {
                'approved': approved,
                'actions': actions,
                'rationale': rationale,
                'impact': {
                    'disputeChange': impact_dispute,
                    'costChange': impact_cost,
                }
            }

        return agent_decisions


# ═══════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════

def run_multi_agent_negotiation(
    initial_contract: Dict[str, Any],
    max_rounds: int = 5
) -> Dict[str, Any]:
    """
    Run multi-agent negotiation system.

    Args:
        initial_contract: Dict with keys: price, delivery_days, liability_cap, etc.
        max_rounds: Maximum negotiation rounds

    Returns:
        {
            'final_contract': Dict,
            'initial_contract': Dict,
            'rounds': List,
            'agent_decisions': Dict,
            'dispute_risk_reduction': float,
        }
    """
    system = MultiAgentNegotiationSystem()
    result = system.negotiate(initial_contract, max_rounds)

    logger.info(f"Multi-agent negotiation completed. "
                f"Dispute risk: {result['initial_dispute_risk']:.2%} → "
                f"{result['final_dispute_risk']:.2%} "
                f"(reduction: {result['dispute_risk_reduction']:.2%})")

    return result
