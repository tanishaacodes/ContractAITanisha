"""
PrimeContractAI - Monte Carlo Exposure Engine
Statistical risk simulation for portfolio Value-at-Risk (VaR) analysis
"""

import numpy as np
from typing import Dict, List, Tuple
from scipy import stats


class MonteCarloExposure:
    """
    Monte Carlo simulation engine for contract portfolio risk
    Simulates thousands of scenarios to estimate exposure distribution
    """

    def __init__(self, iterations: int = 10000, confidence_level: float = 0.95):
        self.iterations = iterations
        self.confidence_level = confidence_level
        self.random_state = np.random.RandomState(42)  # Reproducible results

    def simulate_exposure(
        self,
        base_value: float,
        volatility: float,
        distribution: str = "normal"
    ) -> Dict:
        """
        Run Monte Carlo simulation for exposure scenarios

        Args:
            base_value: Expected contract value/exposure
            volatility: Standard deviation (risk volatility)
            distribution: 'normal', 'lognormal', or 'triangular'

        Returns:
            Dictionary with simulation results and statistics
        """
        if distribution == "lognormal":
            simulations = self.random_state.lognormal(
                mean=np.log(base_value),
                sigma=volatility / base_value,
                size=self.iterations
            )
        elif distribution == "triangular":
            # Triangular distribution with mode at base_value
            simulations = self.random_state.triangular(
                left=base_value - volatility,
                mode=base_value,
                right=base_value + volatility,
                size=self.iterations
            )
        else:  # normal (default)
            simulations = self.random_state.normal(
                loc=base_value,
                scale=volatility,
                size=self.iterations
            )

        # Ensure non-negative values
        simulations = np.maximum(simulations, 0)

        return self._calculate_statistics(simulations, base_value)

    def simulate_portfolio_var(
        self,
        contracts: List[Dict],
        correlation_matrix: np.ndarray = None
    ) -> Dict:
        """
        Simulate Value-at-Risk for entire portfolio with correlations

        Args:
            contracts: List of contract dictionaries with 'value' and 'volatility'
            correlation_matrix: Optional correlation matrix between contracts

        Returns:
            Portfolio VaR statistics
        """
        n_contracts = len(contracts)

        if correlation_matrix is None:
            # Default: assume 30% correlation between contracts
            correlation_matrix = np.full((n_contracts, n_contracts), 0.3)
            np.fill_diagonal(correlation_matrix, 1.0)

        # Extract values and volatilities
        values = np.array([c.get("value", 0) for c in contracts])
        volatilities = np.array([c.get("volatility", 0) for c in contracts])

        # Generate correlated random scenarios
        mean = values
        cov_matrix = np.outer(volatilities, volatilities) * correlation_matrix

        # Monte Carlo simulation with correlation
        scenarios = self.random_state.multivariate_normal(
            mean=mean,
            cov=cov_matrix,
            size=self.iterations
        )

        # Portfolio value for each scenario
        portfolio_values = np.sum(scenarios, axis=1)
        portfolio_values = np.maximum(portfolio_values, 0)

        base_portfolio_value = np.sum(values)

        return self._calculate_statistics(portfolio_values, base_portfolio_value)

    def _calculate_statistics(self, simulations: np.ndarray, base_value: float) -> Dict:
        """Calculate comprehensive statistics from simulation results"""

        sorted_sims = np.sort(simulations)

        # Percentiles
        percentile_5 = np.percentile(sorted_sims, 5)
        percentile_25 = np.percentile(sorted_sims, 25)
        percentile_50 = np.percentile(sorted_sims, 50)  # Median
        percentile_75 = np.percentile(sorted_sims, 75)
        percentile_95 = np.percentile(sorted_sims, 95)
        percentile_99 = np.percentile(sorted_sims, 99)

        # Confidence intervals
        confidence_interval = stats.t.interval(
            self.confidence_level,
            len(simulations) - 1,
            loc=np.mean(simulations),
            scale=stats.sem(simulations)
        )

        # Value at Risk (VaR)
        var_95 = base_value - percentile_5  # Loss at 95% confidence
        var_99 = base_value - percentile_99  # Loss at 99% confidence

        # Conditional Value at Risk (CVaR) - expected loss beyond VaR
        cvar_95 = base_value - np.mean(sorted_sims[: int(0.05 * len(sorted_sims))])
        cvar_99 = base_value - np.mean(sorted_sims[: int(0.01 * len(sorted_sims))])

        # Risk metrics
        downside_deviation = np.std(simulations[simulations < base_value])
        probability_of_loss = np.sum(simulations < base_value) / len(simulations) * 100

        return {
            "mean_exposure": float(np.mean(simulations)),
            "median_exposure": float(percentile_50),
            "std_deviation": float(np.std(simulations)),
            "min_exposure": float(np.min(simulations)),
            "max_exposure": float(np.max(simulations)),
            "percentiles": {
                "5th": float(percentile_5),
                "25th": float(percentile_25),
                "50th": float(percentile_50),
                "75th": float(percentile_75),
                "95th": float(percentile_95),
                "99th": float(percentile_99)
            },
            "confidence_interval": {
                "level": self.confidence_level,
                "lower": float(confidence_interval[0]),
                "upper": float(confidence_interval[1])
            },
            "var": {
                "95_percent": float(var_95),
                "99_percent": float(var_99)
            },
            "cvar": {
                "95_percent": float(cvar_95),
                "99_percent": float(cvar_99)
            },
            "risk_metrics": {
                "downside_deviation": float(downside_deviation) if not np.isnan(downside_deviation) else 0,
                "probability_of_loss": float(probability_of_loss),
                "sharpe_ratio": self._calculate_sharpe_ratio(simulations, base_value)
            },
            "simulation_params": {
                "iterations": self.iterations,
                "base_value": base_value
            },
            "distribution_data": [float(x) for x in sorted_sims[::max(1, len(sorted_sims) // 100)]]  # Sample for charting
        }

    def _calculate_sharpe_ratio(self, simulations: np.ndarray, base_value: float, risk_free_rate: float = 0.03) -> float:
        """Calculate Sharpe ratio (risk-adjusted return)"""
        mean_return = (np.mean(simulations) - base_value) / base_value
        std_return = np.std(simulations) / base_value

        if std_return == 0:
            return 0.0

        sharpe = (mean_return - risk_free_rate) / std_return
        return float(sharpe)

    def stress_test(self, base_value: float, volatility: float, stress_scenarios: List[Dict]) -> Dict:
        """
        Run stress tests under extreme scenarios

        Args:
            base_value: Base contract value
            volatility: Normal volatility
            stress_scenarios: List of stress conditions

        Returns:
            Stress test results
        """
        results = {}

        for scenario in stress_scenarios:
            name = scenario.get("name", "unnamed")
            stress_vol = volatility * scenario.get("volatility_multiplier", 1.5)
            shift = scenario.get("shift", 0)

            stressed_base = base_value + shift
            stress_sims = self.random_state.normal(
                loc=stressed_base,
                scale=stress_vol,
                size=self.iterations
            )
            stress_sims = np.maximum(stress_sims, 0)

            results[name] = {
                "mean": float(np.mean(stress_sims)),
                "percentile_5": float(np.percentile(stress_sims, 5)),
                "percentile_95": float(np.percentile(stress_sims, 95)),
                "var_95": float(stressed_base - np.percentile(stress_sims, 5)),
                "worst_case": float(np.min(stress_sims)),
                "scenario_params": scenario
            }

        return results
