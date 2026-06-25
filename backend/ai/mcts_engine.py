"""
MCTS (Monte Carlo Tree Search) Engine for Contract Negotiation
===============================================================
Implements UCB (Upper Confidence Bound) tree search to find
optimal contract configurations that minimize dispute risk
while maximizing commercial value.

Algorithm:
1. Selection: Use UCB1 to select most promising node
2. Expansion: Add child nodes for unexplored actions
3. Simulation: Rollout to estimate node value
4. Backpropagation: Update ancestor nodes with results
"""

import math
import random
import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Lazy-loaded Bayesian engine singleton
_bayesian_engine = None

def _get_bayesian_engine():
    global _bayesian_engine
    if _bayesian_engine is None:
        try:
            import sys, os
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if backend_dir not in sys.path:
                sys.path.insert(0, backend_dir)
            from dispute_predictor.bayesian_engine import get_bayesian_engine
            _bayesian_engine = get_bayesian_engine()
        except Exception as e:
            logger.warning(f"Bayesian engine unavailable in MCTS, using heuristic fallback: {e}")
    return _bayesian_engine


@dataclass
class ContractState:
    """
    Represents a contract configuration state.
    """
    price: float = 100.0
    delivery_days: int = 30
    liability_cap: float = 0.5
    payment_terms: int = 60
    termination_penalty: float = 10.0
    force_majeure: int = 1  # 0 or 1 (boolean)

    def to_dict(self) -> Dict:
        return {
            'price': self.price,
            'delivery_days': self.delivery_days,
            'liability_cap': self.liability_cap,
            'payment_terms': self.payment_terms,
            'termination_penalty': self.termination_penalty,
            'force_majeure': self.force_majeure,
        }

    def copy(self) -> 'ContractState':
        return ContractState(
            price=self.price,
            delivery_days=self.delivery_days,
            liability_cap=self.liability_cap,
            payment_terms=self.payment_terms,
            termination_penalty=self.termination_penalty,
            force_majeure=self.force_majeure,
        )


@dataclass
class MCTSNode:
    """
    Node in the MCTS tree.
    """
    state: ContractState
    parent: Optional['MCTSNode'] = None
    children: List['MCTSNode'] = field(default_factory=list)
    visits: int = 0
    total_reward: float = 0.0
    action_taken: Optional[str] = None
    is_terminal: bool = False
    untried_actions: List[str] = field(default_factory=list)

    @property
    def value(self) -> float:
        """Average reward (Q-value)"""
        if self.visits == 0:
            return 0.0
        return self.total_reward / self.visits

    @property
    def ucb_score(self) -> float:
        """UCB1 score for selection"""
        if self.visits == 0:
            return float('inf')  # Prioritize unvisited nodes

        if self.parent is None or self.parent.visits == 0:
            return self.value

        # UCB1 formula: Q(v) + C * sqrt(ln(N(parent)) / N(v))
        C = 1.414  # Exploration constant (sqrt(2))
        exploitation = self.value
        exploration = C * math.sqrt(math.log(self.parent.visits) / self.visits)

        return exploitation + exploration


# ═══════════════════════════════════════════════════════════════
# Available Actions (contract clause modifications)
# ═══════════════════════════════════════════════════════════════

ACTIONS = [
    'increase_price',
    'decrease_price',
    'increase_delivery_days',
    'decrease_delivery_days',
    'increase_liability_cap',
    'decrease_liability_cap',
    'increase_payment_terms',
    'decrease_payment_terms',
    'increase_termination_penalty',
    'decrease_termination_penalty',
    'toggle_force_majeure',
]


def apply_action(state: ContractState, action: str) -> ContractState:
    """
    Apply an action to a contract state, returning a new state.
    """
    new_state = state.copy()

    if action == 'increase_price':
        new_state.price = min(200, state.price + 10)
    elif action == 'decrease_price':
        new_state.price = max(50, state.price - 10)
    elif action == 'increase_delivery_days':
        new_state.delivery_days = min(90, state.delivery_days + 5)
    elif action == 'decrease_delivery_days':
        new_state.delivery_days = max(10, state.delivery_days - 5)
    elif action == 'increase_liability_cap':
        new_state.liability_cap = min(1.0, state.liability_cap + 0.1)
    elif action == 'decrease_liability_cap':
        new_state.liability_cap = max(0.1, state.liability_cap - 0.1)
    elif action == 'increase_payment_terms':
        new_state.payment_terms = min(120, state.payment_terms + 10)
    elif action == 'decrease_payment_terms':
        new_state.payment_terms = max(10, state.payment_terms - 10)
    elif action == 'increase_termination_penalty':
        new_state.termination_penalty = min(30, state.termination_penalty + 5)
    elif action == 'decrease_termination_penalty':
        new_state.termination_penalty = max(0, state.termination_penalty - 5)
    elif action == 'toggle_force_majeure':
        new_state.force_majeure = 1 - state.force_majeure

    return new_state


def evaluate_state(state: ContractState) -> Tuple[float, float, float]:
    """
    Evaluate a contract state using the real 60-node Bayesian engine.

    Returns:
        (score, dispute_risk, commercial_value)
    """
    engine = _get_bayesian_engine()

    if engine is not None:
        # Map contract state to Bayesian risk signals
        signals = {
            'ContractAmbiguity': max(0.0, min(0.9, 0.65 - state.liability_cap * 0.5)),
            'PaymentDefaultRisk': max(0.0, min(0.9, (state.payment_terms - 30) / 90)),
            'TerminationRisk': max(0.0, min(0.9, state.termination_penalty / 30)),
            'SupplierDelay': max(0.0, min(0.9, (state.delivery_days - 15) / 75)),
        }
        if state.force_majeure == 0:
            signals['ContractAmbiguity'] = min(0.9, signals['ContractAmbiguity'] + 0.15)
        result = engine.compute_dispute_probability(signals)
        dispute_risk = result['dispute_probability']
    else:
        # Heuristic fallback only if Bayesian engine is truly unavailable
        risk_factors = 0.0
        if state.price > 120:
            risk_factors += (state.price - 120) * 0.01
        if state.delivery_days > 40:
            risk_factors += (state.delivery_days - 40) * 0.005
        if state.liability_cap < 0.3:
            risk_factors += (0.3 - state.liability_cap) * 0.5
        if state.payment_terms > 70:
            risk_factors += (state.payment_terms - 70) * 0.003
        if state.force_majeure == 0:
            risk_factors += 0.15
        dispute_risk = min(0.99, 0.20 + risk_factors)

    # Commercial value: lower price + faster delivery + higher liability coverage = more buyer value
    commercial_value = (200 - state.price) * 1_000_000

    # Composite: maximise value, minimise risk
    score = (commercial_value * 0.7) - (dispute_risk * 100_000_000 * 0.3)

    return score, dispute_risk, commercial_value


# ═══════════════════════════════════════════════════════════════
# MCTS Algorithm
# ═══════════════════════════════════════════════════════════════

class MCTSEngine:
    """
    MCTS engine for contract negotiation optimization.
    """
    def __init__(self, max_depth: int = 5, max_iterations: int = 1000):
        self.max_depth = max_depth
        self.max_iterations = max_iterations
        self.root: Optional[MCTSNode] = None

    def search(self, initial_state: ContractState) -> Dict[str, Any]:
        """
        Run MCTS search from initial state.

        Returns:
            {
                'best_state': ContractState,
                'best_score': float,
                'dispute_risk': float,
                'commercial_value': float,
                'tree': List[Dict]  # For visualization
            }
        """
        # Initialize root
        self.root = MCTSNode(
            state=initial_state,
            untried_actions=ACTIONS.copy()
        )

        # Run iterations
        for i in range(self.max_iterations):
            # 1. Selection
            node = self._select(self.root)

            # 2. Expansion
            if not node.is_terminal and node.untried_actions:
                node = self._expand(node)

            # 3. Simulation
            reward = self._simulate(node)

            # 4. Backpropagation
            self._backpropagate(node, reward)

            if (i + 1) % 100 == 0:
                logger.info(f"MCTS iteration {i + 1}/{self.max_iterations}")

        # Find best child of root
        best_child = max(self.root.children, key=lambda c: c.visits) if self.root.children else self.root
        best_score, best_dispute, best_value = evaluate_state(best_child.state)

        # Build tree for visualization
        tree_data = self._build_tree_data()

        return {
            'best_state': best_child.state.to_dict(),
            'best_score': best_score,
            'dispute_risk': best_dispute,
            'commercial_value': best_value,
            'tree': tree_data,
        }

    def _select(self, node: MCTSNode) -> MCTSNode:
        """
        Select a leaf node using UCB1.
        """
        current = node
        depth = 0

        while current.children and depth < self.max_depth:
            if current.untried_actions:
                return current  # Expand this node

            # Select child with highest UCB score
            current = max(current.children, key=lambda c: c.ucb_score)
            depth += 1

        return current

    def _expand(self, node: MCTSNode) -> MCTSNode:
        """
        Expand node by trying an untried action.
        """
        if not node.untried_actions:
            return node

        action = node.untried_actions.pop(0)
        new_state = apply_action(node.state, action)

        child = MCTSNode(
            state=new_state,
            parent=node,
            action_taken=action,
            untried_actions=ACTIONS.copy()
        )

        node.children.append(child)
        return child

    def _simulate(self, node: MCTSNode) -> float:
        """
        Simulate (rollout) from node to estimate value.
        """
        state = node.state.copy()
        depth = 0
        max_sim_depth = self.max_depth

        while depth < max_sim_depth:
            action = random.choice(ACTIONS)
            state = apply_action(state, action)
            depth += 1

        score, _, _ = evaluate_state(state)
        return score

    def _backpropagate(self, node: MCTSNode, reward: float):
        """
        Backpropagate reward up the tree.
        """
        current = node

        while current is not None:
            current.visits += 1
            current.total_reward += reward
            current = current.parent

    def _build_tree_data(self) -> Dict[str, List]:
        """
        Convert tree to frontend-friendly format.
        """
        nodes = []
        edges = []
        node_id_map = {}
        counter = [0]  # Mutable counter

        def traverse(node: MCTSNode, level: int = 0):
            node_id = counter[0]
            counter[0] += 1
            node_id_map[id(node)] = node_id

            score, dispute_risk, comm_value = evaluate_state(node.state)

            nodes.append({
                'id': node_id,
                'level': level,
                'state': node.state.to_dict(),
                'score': round(score, 1),
                'disputeRisk': round(dispute_risk * 100, 1),
                'commercialValue': round(comm_value, 0),
                'visits': node.visits,
                'action': node.action_taken or "Root",
                'isOptimal': node == max(self.root.children, key=lambda c: c.visits) if level == 1 and self.root.children else False,
            })

            for child in node.children:
                traverse(child, level + 1)
                edges.append({
                    'source': node_id,
                    'target': node_id_map[id(child)],
                    'label': child.action_taken or "",
                })

        if self.root:
            traverse(self.root)

        return {'nodes': nodes, 'edges': edges}


# ═══════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════

def run_mcts_negotiation(
    initial_contract: Dict[str, Any],
    max_iterations: int = 500,
    max_depth: int = 5
) -> Dict[str, Any]:
    """
    Run MCTS negotiation search.

    Args:
        initial_contract: Dict with keys: price, delivery_days, liability_cap, etc.
        max_iterations: Number of MCTS iterations
        max_depth: Maximum tree depth

    Returns:
        {
            'best_state': Dict,
            'best_score': float,
            'dispute_risk': float,
            'commercial_value': float,
            'tree': {'nodes': [...], 'edges': [...]}
        }
    """
    initial_state = ContractState(
        price=initial_contract.get('price', 100),
        delivery_days=initial_contract.get('delivery_days', 30),
        liability_cap=initial_contract.get('liability_cap', 0.5),
        payment_terms=initial_contract.get('payment_terms', 60),
        termination_penalty=initial_contract.get('termination_penalty', 10),
        force_majeure=initial_contract.get('force_majeure', 1),
    )

    engine = MCTSEngine(max_depth=max_depth, max_iterations=max_iterations)
    result = engine.search(initial_state)

    logger.info(f"MCTS completed. Best score: {result['best_score']:.2f}, "
                f"Dispute risk: {result['dispute_risk']:.2%}")

    return result
