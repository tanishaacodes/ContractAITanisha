"""
Portfolio Risk Simulator with Multi-Contract Correlation
Simulates FM risk across entire contract portfolio considering dependencies
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ContractRisk:
    """Individual contract risk profile"""
    contract_id: str
    contract_value: float
    fm_risk_score: float
    region: str
    industry: str
    supplier_countries: List[str]
    fm_probability: float
    expected_loss: float


class PortfolioRiskSimulator:
    """Simulates correlated FM risks across contract portfolio"""

    def __init__(self):
        self.correlation_matrix = None
        self.contracts = []

    def simulate_portfolio_risk(
        self,
        contracts: List[Dict],
        n_simulations: int = 10000,
        confidence_level: float = 0.95
    ) -> Dict:
        """
        Run Monte Carlo simulation of portfolio-wide FM risk

        Args:
            contracts: List of contract dicts with risk profiles
            n_simulations: Number of Monte Carlo runs
            confidence_level: Confidence level for VaR calculation

        Returns:
            Portfolio risk analysis with correlations
        """

        if not contracts:
            return {
                'error': 'No contracts provided',
                'total_contracts': 0
            }

        # Parse contracts
        contract_risks = [self._parse_contract(c) for c in contracts]
        n_contracts = len(contract_risks)

        # Build correlation matrix
        correlation_matrix = self._build_correlation_matrix(contract_risks)

        # Generate correlated random variables
        np.random.seed(42)

        # Cholesky decomposition for correlated samples
        try:
            L = np.linalg.cholesky(correlation_matrix)
        except np.linalg.LinAlgError:
            # If matrix not positive definite, use uncorrelated
            logger.warning("Correlation matrix not positive definite, using identity")
            L = np.eye(n_contracts)

        # Run simulations
        portfolio_losses = []
        contract_loss_distributions = [[] for _ in range(n_contracts)]

        for _ in range(n_simulations):
            # Generate correlated uniform random variables
            z = np.random.standard_normal(n_contracts)
            correlated_uniforms = self._transform_to_uniform(L @ z)

            # Calculate losses for each contract
            simulation_losses = []
            for i, (contract, uniform_sample) in enumerate(zip(contract_risks, correlated_uniforms)):
                # FM event occurs if uniform sample < fm_probability
                if uniform_sample < contract.fm_probability:
                    # FM triggered - sample loss distribution
                    loss = np.random.lognormal(
                        np.log(contract.expected_loss),
                        0.5  # Standard deviation
                    )
                else:
                    loss = 0

                simulation_losses.append(loss)
                contract_loss_distributions[i].append(loss)

            # Total portfolio loss this simulation
            total_loss = sum(simulation_losses)
            portfolio_losses.append(total_loss)

        portfolio_losses = np.array(portfolio_losses)

        # Calculate portfolio metrics
        total_exposure = sum(c.contract_value for c in contract_risks)
        expected_portfolio_loss = np.mean(portfolio_losses)
        portfolio_std = np.std(portfolio_losses)

        # Value at Risk (VaR) and Conditional VaR (CVaR)
        var_index = int(n_simulations * confidence_level)
        sorted_losses = np.sort(portfolio_losses)
        var = sorted_losses[var_index]
        cvar = np.mean(sorted_losses[var_index:])  # CVaR = average of losses beyond VaR

        # Percentiles
        p50 = np.percentile(portfolio_losses, 50)
        p75 = np.percentile(portfolio_losses, 75)
        p90 = np.percentile(portfolio_losses, 90)
        p95 = np.percentile(portfolio_losses, 95)
        p99 = np.percentile(portfolio_losses, 99)

        # Analyze correlations
        correlation_analysis = self._analyze_correlations(
            contract_risks,
            correlation_matrix,
            contract_loss_distributions
        )

        # Identify high-risk contracts
        high_risk_contracts = self._identify_high_risk_contracts(
            contract_risks,
            contract_loss_distributions
        )

        # Diversification benefit
        uncorrelated_var = self._calculate_uncorrelated_var(contract_risks, confidence_level)
        diversification_benefit = uncorrelated_var - var

        return {
            'portfolio_summary': {
                'total_contracts': n_contracts,
                'total_exposure_usd': total_exposure,
                'expected_portfolio_loss_usd': expected_portfolio_loss,
                'portfolio_standard_deviation_usd': portfolio_std,
                'loss_as_pct_of_exposure': round((expected_portfolio_loss / total_exposure) * 100, 2) if total_exposure > 0 else 0
            },
            'risk_metrics': {
                'value_at_risk_usd': var,
                'conditional_var_usd': cvar,
                'confidence_level': confidence_level,
                'percentiles': {
                    'p50': p50,
                    'p75': p75,
                    'p90': p90,
                    'p95': p95,
                    'p99': p99
                }
            },
            'correlation_analysis': correlation_analysis,
            'high_risk_contracts': high_risk_contracts,
            'diversification': {
                'uncorrelated_var_usd': uncorrelated_var,
                'correlated_var_usd': var,
                'diversification_benefit_usd': diversification_benefit,
                'benefit_percentage': round((diversification_benefit / uncorrelated_var) * 100, 1) if uncorrelated_var > 0 else 0
            },
            'simulations': n_simulations,
            'regional_breakdown': self._calculate_regional_breakdown(contract_risks),
            'industry_breakdown': self._calculate_industry_breakdown(contract_risks),
            'recommendations': self._generate_portfolio_recommendations(
                expected_portfolio_loss,
                total_exposure,
                high_risk_contracts,
                correlation_analysis
            )
        }

    def _parse_contract(self, contract_dict: Dict) -> ContractRisk:
        """Parse contract dict into ContractRisk object"""
        return ContractRisk(
            contract_id=contract_dict.get('contract_id', 'unknown'),
            contract_value=float(contract_dict.get('contract_value', 1000000)),
            fm_risk_score=float(contract_dict.get('fm_risk_score', 0.50)),
            region=contract_dict.get('region', 'Global'),
            industry=contract_dict.get('industry', 'General'),
            supplier_countries=contract_dict.get('supplier_countries', []),
            fm_probability=float(contract_dict.get('fm_probability', 0.30)),
            expected_loss=float(contract_dict.get('expected_loss', contract_dict.get('contract_value', 1000000) * 0.15))
        )

    def _build_correlation_matrix(self, contracts: List[ContractRisk]) -> np.ndarray:
        """Build correlation matrix between contracts"""
        n = len(contracts)
        corr_matrix = np.eye(n)  # Start with identity matrix

        for i in range(n):
            for j in range(i + 1, n):
                # Calculate correlation based on shared characteristics
                corr = self._calculate_pairwise_correlation(contracts[i], contracts[j])
                corr_matrix[i, j] = corr
                corr_matrix[j, i] = corr

        # Ensure positive definite (adjust if needed)
        corr_matrix = self._ensure_positive_definite(corr_matrix)

        return corr_matrix

    def _calculate_pairwise_correlation(
        self,
        contract_a: ContractRisk,
        contract_b: ContractRisk
    ) -> float:
        """Calculate correlation between two contracts"""

        correlation = 0.0

        # Same region → high correlation
        if contract_a.region == contract_b.region:
            correlation += 0.40

        # Same industry → moderate correlation
        if contract_a.industry == contract_b.industry:
            correlation += 0.25

        # Shared supplier countries → correlation
        shared_suppliers = set(contract_a.supplier_countries) & set(contract_b.supplier_countries)
        if shared_suppliers:
            correlation += min(0.30, len(shared_suppliers) * 0.10)

        # Cap at 0.90 (contracts are never perfectly correlated)
        return min(0.90, correlation)

    def _ensure_positive_definite(self, matrix: np.ndarray) -> np.ndarray:
        """Ensure correlation matrix is positive definite"""
        try:
            # Try Cholesky decomposition
            np.linalg.cholesky(matrix)
            return matrix
        except np.linalg.LinAlgError:
            # Add small value to diagonal
            n = matrix.shape[0]
            return matrix + np.eye(n) * 0.01

    def _transform_to_uniform(self, z: np.ndarray) -> np.ndarray:
        """Transform standard normal to uniform [0,1] using CDF"""
        from scipy.stats import norm
        return norm.cdf(z)

    def _analyze_correlations(
        self,
        contracts: List[ContractRisk],
        corr_matrix: np.ndarray,
        loss_distributions: List[List[float]]
    ) -> Dict:
        """Analyze correlation structure"""

        # Find highly correlated pairs
        n = len(contracts)
        high_correlations = []

        for i in range(n):
            for j in range(i + 1, n):
                corr = corr_matrix[i, j]
                if corr > 0.60:  # High correlation threshold
                    high_correlations.append({
                        'contract_a': contracts[i].contract_id,
                        'contract_b': contracts[j].contract_id,
                        'correlation': round(corr, 3),
                        'shared_risk_factors': self._identify_shared_risks(contracts[i], contracts[j])
                    })

        # Sort by correlation
        high_correlations.sort(key=lambda x: x['correlation'], reverse=True)

        # Average correlation
        upper_triangle = corr_matrix[np.triu_indices(n, k=1)]
        avg_correlation = np.mean(upper_triangle) if len(upper_triangle) > 0 else 0

        return {
            'average_correlation': round(avg_correlation, 3),
            'highly_correlated_pairs': high_correlations[:10],  # Top 10
            'correlation_summary': {
                'high_correlation_count': len([c for c in upper_triangle if c > 0.60]),
                'moderate_correlation_count': len([c for c in upper_triangle if 0.30 < c <= 0.60]),
                'low_correlation_count': len([c for c in upper_triangle if c <= 0.30])
            }
        }

    def _identify_shared_risks(self, contract_a: ContractRisk, contract_b: ContractRisk) -> List[str]:
        """Identify shared risk factors between contracts"""
        shared = []

        if contract_a.region == contract_b.region:
            shared.append(f"Same region: {contract_a.region}")

        if contract_a.industry == contract_b.industry:
            shared.append(f"Same industry: {contract_a.industry}")

        shared_suppliers = set(contract_a.supplier_countries) & set(contract_b.supplier_countries)
        if shared_suppliers:
            shared.append(f"Shared suppliers: {', '.join(list(shared_suppliers)[:3])}")

        return shared

    def _identify_high_risk_contracts(
        self,
        contracts: List[ContractRisk],
        loss_distributions: List[List[float]]
    ) -> List[Dict]:
        """Identify contracts with highest risk contribution"""

        contract_risks = []

        for i, (contract, losses) in enumerate(zip(contracts, loss_distributions)):
            losses_array = np.array(losses)
            avg_loss = np.mean(losses_array)
            p95_loss = np.percentile(losses_array, 95)

            contract_risks.append({
                'contract_id': contract.contract_id,
                'contract_value': contract.contract_value,
                'region': contract.region,
                'industry': contract.industry,
                'fm_risk_score': round(contract.fm_risk_score, 3),
                'fm_probability': round(contract.fm_probability, 3),
                'expected_loss': avg_loss,
                'p95_loss': p95_loss,
                'loss_ratio': round((avg_loss / contract.contract_value) * 100, 1) if contract.contract_value > 0 else 0
            })

        # Sort by expected loss
        contract_risks.sort(key=lambda x: x['expected_loss'], reverse=True)

        return contract_risks[:10]  # Top 10

    def _calculate_uncorrelated_var(
        self,
        contracts: List[ContractRisk],
        confidence_level: float
    ) -> float:
        """Calculate VaR assuming no correlation (diversification baseline)"""

        # Sum of individual VaRs
        total_var = 0

        for contract in contracts:
            # Individual VaR approximation
            contract_var = contract.expected_loss * 2.0  # Simplified
            total_var += contract_var

        return total_var

    def _calculate_regional_breakdown(self, contracts: List[ContractRisk]) -> Dict:
        """Calculate exposure by region"""
        regional_exposure = {}

        for contract in contracts:
            region = contract.region
            if region not in regional_exposure:
                regional_exposure[region] = {
                    'contract_count': 0,
                    'total_exposure': 0,
                    'expected_loss': 0
                }

            regional_exposure[region]['contract_count'] += 1
            regional_exposure[region]['total_exposure'] += contract.contract_value
            regional_exposure[region]['expected_loss'] += contract.expected_loss

        return regional_exposure

    def _calculate_industry_breakdown(self, contracts: List[ContractRisk]) -> Dict:
        """Calculate exposure by industry"""
        industry_exposure = {}

        for contract in contracts:
            industry = contract.industry
            if industry not in industry_exposure:
                industry_exposure[industry] = {
                    'contract_count': 0,
                    'total_exposure': 0,
                    'expected_loss': 0
                }

            industry_exposure[industry]['contract_count'] += 1
            industry_exposure[industry]['total_exposure'] += contract.contract_value
            industry_exposure[industry]['expected_loss'] += contract.expected_loss

        return industry_exposure

    def _generate_portfolio_recommendations(
        self,
        expected_loss: float,
        total_exposure: float,
        high_risk_contracts: List[Dict],
        correlation_analysis: Dict
    ) -> List[str]:
        """Generate portfolio management recommendations"""

        recommendations = []

        loss_ratio = (expected_loss / total_exposure) * 100 if total_exposure > 0 else 0

        if loss_ratio > 20:
            recommendations.append("CRITICAL: Portfolio FM exposure exceeds 20% - immediate risk reduction required")
            recommendations.append(f"Consider divesting or insuring top {min(5, len(high_risk_contracts))} high-risk contracts")

        if loss_ratio > 10:
            recommendations.append("HIGH: Significant FM exposure detected - implement comprehensive mitigation strategy")
            recommendations.append("Increase FM clause strength across all contracts")
            recommendations.append("Secure portfolio-wide war risk insurance")

        avg_corr = correlation_analysis.get('average_correlation', 0)
        if avg_corr > 0.50:
            recommendations.append(f"Diversification needed: Average correlation {avg_corr:.1%} is high")
            recommendations.append("Increase geographic and industry diversification")
            recommendations.append("Avoid concentration in single regions or suppliers")

        highly_correlated = correlation_analysis.get('highly_correlated_pairs', [])
        if len(highly_correlated) > 5:
            recommendations.append(f"{len(highly_correlated)} highly correlated contract pairs identified")
            recommendations.append("Review and reduce shared risk factors between contracts")

        if len(high_risk_contracts) > 0:
            top_risk = high_risk_contracts[0]
            recommendations.append(f"Priority: Address contract {top_risk['contract_id']} with {top_risk['loss_ratio']}% loss ratio")

        recommendations.append("Conduct quarterly portfolio FM risk reviews")
        recommendations.append("Implement portfolio-wide FM monitoring dashboard")

        return recommendations


# Global instance
portfolio_simulator = PortfolioRiskSimulator()


# Convenience function
def simulate_portfolio(contracts: List[Dict], n_simulations: int = 10000) -> Dict:
    """Convenience function to simulate portfolio risk"""
    return portfolio_simulator.simulate_portfolio_risk(contracts, n_simulations)
