"""
Loss Prediction & Liability Sentinel Engine
Forecasts expected losses and calculates tail risk (VaR/CVaR)
"""
import numpy as np
from typing import Dict, List, Any


def forecast_losses(base_exposure: float, risk_multiplier: float = 1.0) -> Dict[str, int]:
    """
    Forecast expected losses over 12, 24, and 36 month horizons

    Args:
        base_exposure: Total portfolio exposure value
        risk_multiplier: Adjustment factor based on portfolio risk profile

    Returns:
        Dictionary with loss forecasts for 12m, 24m, 36m
    """
    # Loss escalation factors (cumulative risk increases over time)
    # 12 months: 18% of exposure at risk
    # 24 months: 39% of exposure at risk (compounding)
    # 36 months: 62% of exposure at risk (full cycle risk)

    factors = {
        "12m": 0.18 * risk_multiplier,
        "24m": 0.39 * risk_multiplier,
        "36m": 0.62 * risk_multiplier
    }

    return {
        period: int(base_exposure * factor)
        for period, factor in factors.items()
    }


def calculate_exposure_percentage(contracts: List[Dict[str, Any]]) -> int:
    """
    Calculate portfolio exposure as percentage of total value

    Returns:
        Exposure percentage (0-100)
    """
    if not contracts:
        return 0

    total_value = sum(c.get("value", 0) for c in contracts)
    high_risk_value = sum(
        c.get("value", 0) for c in contracts
        if c.get("has_unlimited_liability") or c.get("risk_score", 0) >= 70
    )

    if total_value == 0:
        return 0

    return int((high_risk_value / total_value) * 100)


def tail_risk_distribution(base_exposure: float, risk_profile: str = "medium", runs: int = 2000) -> List[Dict[str, Any]]:
    """
    Calculate tail risk distribution using Monte Carlo simulation
    Models worst-case loss scenarios (VaR/CVaR)

    Args:
        base_exposure: Total portfolio exposure
        risk_profile: "low", "medium", "high" - affects distribution shape
        runs: Number of Monte Carlo simulations

    Returns:
        List of loss/probability pairs for distribution
    """
    # Adjust distribution parameters based on risk profile
    if risk_profile == "low":
        mean, sigma = 0.2, 0.6
    elif risk_profile == "high":
        mean, sigma = 0.5, 1.2
    else:  # medium
        mean, sigma = 0.3, 0.9

    # Generate log-normal distribution (realistic for financial losses)
    samples = np.random.lognormal(mean=mean, sigma=sigma, size=runs)

    # Convert to actual loss values (15% of exposure is loss multiplier)
    losses = samples * base_exposure * 0.15

    # Create histogram with 10 bins
    hist, bins = np.histogram(losses, bins=10, density=True)

    # Normalize to probabilities
    total = np.sum(hist)
    if total > 0:
        hist = hist / total

    return [
        {
            "loss": int(bins[i]),
            "loss_max": int(bins[i + 1]) if i < len(bins) - 1 else int(bins[i] * 1.2),
            "prob": float(hist[i]),
            "prob_pct": round(float(hist[i]) * 100, 2)
        }
        for i in range(len(hist))
    ]


def calculate_var_cvar(base_exposure: float, confidence: float = 0.95) -> Dict[str, float]:
    """
    Calculate Value at Risk (VaR) and Conditional Value at Risk (CVaR)

    Args:
        base_exposure: Total exposure value
        confidence: Confidence level (default 95%)

    Returns:
        Dictionary with VaR and CVaR values
    """
    # Generate loss distribution
    samples = np.random.lognormal(mean=0.3, sigma=0.9, size=2000)
    losses = samples * base_exposure * 0.15

    # Calculate VaR (95th percentile loss)
    var = float(np.percentile(losses, confidence * 100))

    # Calculate CVaR (expected loss beyond VaR)
    tail_losses = losses[losses >= var]
    cvar = float(np.mean(tail_losses)) if len(tail_losses) > 0 else var

    return {
        "var_95": int(var),
        "cvar_95": int(cvar),
        "var_99": int(np.percentile(losses, 99)),
        "expected_shortfall": int(cvar - var)
    }


def attribute_loss_to_clauses(contracts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Attribute portfolio loss to specific clause types
    Identifies which clauses are driving the most risk

    Args:
        contracts: List of contract dictionaries with clause data

    Returns:
        List of clause types with their loss contribution
    """
    clause_impacts = {
        "Unlimited Liability": 0,
        "Indemnity Scope": 0,
        "Termination at Will": 0,
        "No Liability Cap": 0,
        "Warranty Obligations": 0,
        "Force Majeure Exclusions": 0
    }

    for contract in contracts:
        value = contract.get("value", 0)
        risk_score = contract.get("risk_score", 0)

        # Calculate loss contribution based on risk score
        base_loss = (value * risk_score) / 100

        # Attribute to specific clauses
        if contract.get("has_unlimited_liability"):
            clause_impacts["Unlimited Liability"] += base_loss * 0.45

        if contract.get("broad_indemnity"):
            clause_impacts["Indemnity Scope"] += base_loss * 0.25

        if contract.get("unilateral_termination"):
            clause_impacts["Termination at Will"] += base_loss * 0.15

        if not contract.get("has_liability_cap"):
            clause_impacts["No Liability Cap"] += base_loss * 0.35

        if contract.get("has_warranties"):
            clause_impacts["Warranty Obligations"] += base_loss * 0.10

        if not contract.get("has_force_majeure"):
            clause_impacts["Force Majeure Exclusions"] += base_loss * 0.08

    # Convert to list and sort by impact
    result = [
        {
            "clause": clause,
            "impact_inr": int(impact),
            "impact_millions": round(impact / 1_000_000, 1)
        }
        for clause, impact in clause_impacts.items()
        if impact > 0
    ]

    # Sort by impact descending
    result.sort(key=lambda x: x["impact_inr"], reverse=True)

    return result[:6]  # Top 6 clauses
