"""
Monte Carlo Exposure Simulation Engine
========================================
Probabilistic simulation of contract exposure under various scenarios.

Features:
1. 5000+ iteration simulation for statistically significant results
2. Risk score uncertainty modeling (Normal distribution)
3. Interaction amplification variance (Uniform distribution)
4. Base exposure uncertainty (Triangular distribution)
5. Percentile analysis (P50, P75, P90, P95)
6. Value at Risk (VaR) calculation
7. Before vs After comparison for What-If scenarios

This converts point estimates into confidence ranges:
"With 90% confidence, exposure reduces between ₹14.2 Cr – ₹23.9 Cr"

Perfect for CFO/CRO/Audit discussions.
"""

import random
import logging
from typing import Dict, List, Any, Optional, Tuple
import networkx as nx

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    # Fallback implementations
    class NumpyFallback:
        @staticmethod
        def mean(arr):
            return sum(arr) / len(arr) if arr else 0

        @staticmethod
        def percentile(arr, p):
            if not arr:
                return 0
            sorted_arr = sorted(arr)
            idx = int(len(sorted_arr) * p / 100)
            idx = min(idx, len(sorted_arr) - 1)
            return sorted_arr[idx]

        @staticmethod
        def std(arr):
            if len(arr) < 2:
                return 0
            mean = sum(arr) / len(arr)
            variance = sum((x - mean) ** 2 for x in arr) / len(arr)
            return variance ** 0.5

    np = NumpyFallback()

from .exposure_engine import ExposureEngine

logger = logging.getLogger(__name__)


class MonteCarloExposureSimulator:
    """
    Monte Carlo simulation for contract exposure ranges.

    Produces audit-defensible confidence intervals.
    """

    DEFAULT_ITERATIONS = 5000

    def __init__(self, iterations: int = DEFAULT_ITERATIONS):
        """
        Args:
            iterations: Number of Monte Carlo iterations (default 5000)
        """
        self.iterations = iterations
        self.exposure_engine = ExposureEngine()

    def simulate(
        self,
        clauses: List[Any],
        graph: nx.DiGraph,
        contract_value: float
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation for contract exposure.

        Args:
            clauses: List of Clause instances
            graph: NetworkX graph
            contract_value: Total contract value

        Returns:
            Dict with distribution, percentiles, and statistics
        """
        if not clauses:
            return self._empty_result()

        samples = []

        for _ in range(self.iterations):
            total_exposure = 0.0

            for clause in clauses:
                # Get base clause attributes
                if hasattr(clause, 'id'):
                    clause_id = clause.id
                    base_risk = float(getattr(clause, 'risk_score', 0) or 0)
                    clause_text = (
                        getattr(clause, 'extracted_text', '') or
                        getattr(clause, 'context_sentences', '') or
                        getattr(clause, 'text_spans', '') or
                        ''
                    )
                    clause_type = getattr(clause, 'clause_type', None) or getattr(clause, 'clause_name', 'general') or 'general'
                else:
                    clause_id = clause.get('id')
                    base_risk = float(clause.get('risk_score', 0) or 0)
                    clause_text = (
                        clause.get('extracted_text', '') or
                        clause.get('context_sentences', '') or
                        clause.get('text_spans', '') or
                        ''
                    )
                    clause_type = clause.get('clause_type') or clause.get('clause_name', 'general')

                # Prefer graph-node values: graph builder already infers
                # risk_score and clause_type for nodes where DB fields are NULL.
                if clause_id in graph.nodes:
                    node_data = graph.nodes[clause_id]
                    base_risk = float(node_data.get('risk_score', base_risk) or base_risk)
                    clause_type = node_data.get('clause_type', clause_type) or clause_type

                # --- Risk uncertainty (Normal distribution) ---
                # Model subjective assessment variance
                risk = max(0, min(1, random.gauss(base_risk, 0.1)))

                # --- Base exposure uncertainty (Triangular distribution) ---
                # Model worst/expected/best case
                base_mult = self._get_base_multiplier(clause_text, clause_type)
                base = random.triangular(
                    contract_value * base_mult * 0.5,   # Optimistic
                    contract_value * base_mult,          # Expected
                    contract_value * base_mult * 1.5    # Pessimistic
                )

                # --- Interaction amplification (Uniform distribution) ---
                # Model clause interpretation variance
                degree = 0
                if clause_id in graph:
                    degree = graph.in_degree(clause_id) + graph.out_degree(clause_id)
                interaction = 1 + (degree * random.uniform(0.1, 0.25))

                # --- Obligation multiplier variance ---
                obligation_mult = self.exposure_engine.OBLIGATION_MULTIPLIERS.get(
                    clause_type.lower(), 0.25
                )
                # Add some variance
                obligation_mult = random.uniform(
                    obligation_mult * 0.8,
                    obligation_mult * 1.2
                )

                # Calculate clause exposure
                clause_exposure = base * risk * interaction * obligation_mult
                total_exposure += clause_exposure

            samples.append(total_exposure)

        # Calculate statistics
        return self._calculate_statistics(samples)

    def simulate_what_if(
        self,
        original_clauses: List[Any],
        remaining_clauses: List[Any],
        original_graph: nx.DiGraph,
        simulated_graph: nx.DiGraph,
        contract_value: float
    ) -> Dict[str, Any]:
        """
        Monte Carlo simulation comparing before vs after what-if scenario.

        Args:
            original_clauses: All clauses before modification
            remaining_clauses: Clauses after modification
            original_graph: Graph before modification
            simulated_graph: Graph after modification
            contract_value: Total contract value

        Returns:
            Dict with before/after distributions and delta analysis
        """
        # Run simulation for both scenarios
        before_result = self.simulate(
            original_clauses, original_graph, contract_value
        )
        after_result = self.simulate(
            remaining_clauses, simulated_graph, contract_value
        )

        # Calculate delta statistics
        delta_mean = before_result['mean'] - after_result['mean']
        delta_p90 = before_result['p90'] - after_result['p90']
        delta_p95 = before_result['p95'] - after_result['p95']

        # Reduction percentages
        reduction_pct_mean = (delta_mean / before_result['mean'] * 100) if before_result['mean'] > 0 else 0
        reduction_pct_p90 = (delta_p90 / before_result['p90'] * 100) if before_result['p90'] > 0 else 0

        return {
            "currency": "INR",
            "iterations": self.iterations,
            "before": before_result,
            "after": after_result,
            "delta": {
                "mean": round(delta_mean, 2),
                "p90": round(delta_p90, 2),
                "p95": round(delta_p95, 2),
                "reduction_pct_mean": round(reduction_pct_mean, 1),
                "reduction_pct_p90": round(reduction_pct_p90, 1)
            },
            "confidence_statement": self._generate_confidence_statement(
                delta_mean, delta_p90, before_result['mean']
            )
        }

    def calculate_var(
        self,
        clauses: List[Any],
        graph: nx.DiGraph,
        contract_value: float,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Calculate Value at Risk (VaR) for the contract.

        VaR answers: "What's the maximum expected loss at X% confidence?"

        Args:
            clauses: List of Clause instances
            graph: NetworkX graph
            contract_value: Total contract value
            confidence_level: Confidence level (default 95%)

        Returns:
            Dict with VaR metrics
        """
        result = self.simulate(clauses, graph, contract_value)

        var_percentile = int(confidence_level * 100)
        var_value = result.get(f'p{var_percentile}', result.get('p95', 0))

        return {
            "confidence_level": confidence_level,
            "var": round(var_value, 2),
            "var_formatted": self.exposure_engine.format_currency(var_value),
            "mean_exposure": round(result['mean'], 2),
            "max_exposure": round(result['max'], 2),
            "interpretation": f"At {confidence_level*100:.0f}% confidence, maximum exposure is {self.exposure_engine.format_currency(var_value)}"
        }

    def stress_test(
        self,
        clauses: List[Any],
        graph: nx.DiGraph,
        contract_value: float
    ) -> Dict[str, Any]:
        """
        Run stress scenarios (worst case analysis).

        Returns exposure under different scenarios:
        - Base case
        - Moderate stress
        - Severe stress
        - Extreme stress
        """
        base_result = self.simulate(clauses, graph, contract_value)

        scenarios = {
            "base_case": {
                "exposure": base_result['mean'],
                "description": "Expected scenario under normal conditions"
            },
            "moderate_stress": {
                "exposure": base_result['p75'],
                "description": "75th percentile - moderately adverse conditions"
            },
            "severe_stress": {
                "exposure": base_result['p90'],
                "description": "90th percentile - severe adverse conditions"
            },
            "extreme_stress": {
                "exposure": base_result['p95'],
                "description": "95th percentile - extreme tail risk scenario"
            },
            "worst_case": {
                "exposure": base_result['max'],
                "description": "Maximum simulated exposure"
            }
        }

        # Format all values
        for scenario in scenarios.values():
            scenario['exposure_formatted'] = self.exposure_engine.format_currency(
                scenario['exposure']
            )

        return {
            "scenarios": scenarios,
            "iterations": self.iterations,
            "contract_value": contract_value,
            "contract_value_formatted": self.exposure_engine.format_currency(contract_value)
        }

    def _get_base_multiplier(self, clause_text: str, clause_type: str) -> float:
        """Get base exposure multiplier for clause type"""
        text = (clause_text or "").lower()
        clause_type = (clause_type or "general").lower()

        if "indemnity" in text or "indemnif" in clause_type:
            return 1.0
        if "liability" in text or "limit" in clause_type:
            return 0.5
        if "termination" in text or "terminat" in clause_type:
            return 0.3
        if "sla" in text or "penalty" in text:
            return 0.2
        if "payment" in text or "payment" in clause_type:
            return 0.4
        if "warranty" in text:
            return 0.25
        return 0.15

    def _calculate_statistics(self, samples: List[float]) -> Dict[str, Any]:
        """Calculate statistics from Monte Carlo samples"""
        if not samples:
            return self._empty_result()

        if HAS_NUMPY:
            mean = float(np.mean(samples))
            std = float(np.std(samples))
            p50 = float(np.percentile(samples, 50))
            p75 = float(np.percentile(samples, 75))
            p90 = float(np.percentile(samples, 90))
            p95 = float(np.percentile(samples, 95))
            p99 = float(np.percentile(samples, 99))
        else:
            mean = np.mean(samples)
            std = np.std(samples)
            p50 = np.percentile(samples, 50)
            p75 = np.percentile(samples, 75)
            p90 = np.percentile(samples, 90)
            p95 = np.percentile(samples, 95)
            p99 = np.percentile(samples, 99)

        min_val = min(samples)
        max_val = max(samples)

        # Sample distribution for visualization (limit to 1000 points)
        distribution = sorted(random.sample(samples, min(1000, len(samples))))

        return {
            "mean": round(mean, 2),
            "std": round(std, 2),
            "min": round(min_val, 2),
            "max": round(max_val, 2),
            "p50": round(p50, 2),
            "p75": round(p75, 2),
            "p90": round(p90, 2),
            "p95": round(p95, 2),
            "p99": round(p99, 2),
            "mean_formatted": self.exposure_engine.format_currency(mean),
            "p90_formatted": self.exposure_engine.format_currency(p90),
            "p95_formatted": self.exposure_engine.format_currency(p95),
            "distribution": distribution,
            "iterations": self.iterations
        }

    def _generate_confidence_statement(
        self,
        delta_mean: float,
        delta_p90: float,
        baseline: float
    ) -> str:
        """Generate human-readable confidence statement"""
        reduction_pct = (delta_mean / baseline * 100) if baseline > 0 else 0

        mean_formatted = self.exposure_engine.format_currency(abs(delta_mean))
        p90_formatted = self.exposure_engine.format_currency(abs(delta_p90))

        if delta_mean > 0:
            return (
                f"Removing this clause reduces expected exposure by {mean_formatted} "
                f"({reduction_pct:.1f}%). With 90% confidence, reduction is at least {p90_formatted}."
            )
        else:
            return (
                f"Modifying this clause may increase exposure by {mean_formatted}. "
                f"Review recommended before proceeding."
            )

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            "mean": 0,
            "std": 0,
            "min": 0,
            "max": 0,
            "p50": 0,
            "p75": 0,
            "p90": 0,
            "p95": 0,
            "p99": 0,
            "mean_formatted": "₹0",
            "p90_formatted": "₹0",
            "p95_formatted": "₹0",
            "distribution": [],
            "iterations": 0
        }


# Convenience functions
def monte_carlo_exposure(
    clauses: List[Any],
    graph: nx.DiGraph,
    contract_value: float,
    iterations: int = 5000
) -> Dict[str, Any]:
    """Run Monte Carlo exposure simulation"""
    simulator = MonteCarloExposureSimulator(iterations=iterations)
    return simulator.simulate(clauses, graph, contract_value)


def monte_carlo_what_if(
    original_clauses: List[Any],
    remaining_clauses: List[Any],
    original_graph: nx.DiGraph,
    simulated_graph: nx.DiGraph,
    contract_value: float,
    iterations: int = 5000
) -> Dict[str, Any]:
    """Run Monte Carlo comparison for what-if scenario"""
    simulator = MonteCarloExposureSimulator(iterations=iterations)
    return simulator.simulate_what_if(
        original_clauses, remaining_clauses,
        original_graph, simulated_graph,
        contract_value
    )


def calculate_var(
    clauses: List[Any],
    graph: nx.DiGraph,
    contract_value: float,
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """Calculate Value at Risk"""
    simulator = MonteCarloExposureSimulator()
    return simulator.calculate_var(clauses, graph, contract_value, confidence_level)


def stress_test(
    clauses: List[Any],
    graph: nx.DiGraph,
    contract_value: float
) -> Dict[str, Any]:
    """Run stress test scenarios"""
    simulator = MonteCarloExposureSimulator()
    return simulator.stress_test(clauses, graph, contract_value)
