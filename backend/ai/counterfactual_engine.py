"""
Counterfactual & What-If Simulation Engine
Monte Carlo simulation for contract risk modeling
"""
import numpy as np
from typing import Dict, List, Any


def monte_carlo_losses(base_exposure: float, risk_delta: float, runs: int = 1000) -> List[float]:
    """
    Run Monte Carlo simulation to estimate loss distribution

    Args:
        base_exposure: Base contract exposure value
        risk_delta: Change in risk score (-1 to 1)
        runs: Number of Monte Carlo runs

    Returns:
        List of simulated loss values
    """
    losses = []
    for _ in range(runs):
        # Add randomness with normal distribution
        shock = np.random.normal(loc=risk_delta, scale=0.15)
        # Calculate loss (can't be negative)
        loss = max(0, base_exposure * shock)
        losses.append(loss)
    return losses


def simulate_counterfactual(contract: Dict[str, Any], actions: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate counterfactual scenario based on contract modifications

    Args:
        contract: Contract data with exposure value
        actions: Dictionary of modifications:
            - remove_clause: bool
            - add_indemnity: bool
            - liability_cap: float (1-5x)
            - governing_law: str (India/UK/US)
            - add_arbitration: bool
            - termination_rights: bool

    Returns:
        Simulation results with risk delta, exposure changes, and loss distribution
    """
    risk_delta = 0.0

    # Clause removal reduces risk
    if actions.get("remove_clause"):
        risk_delta -= 0.12

    # Adding indemnity increases protection but adds complexity
    if actions.get("add_indemnity"):
        risk_delta += 0.15

    # Liability cap reduces risk proportionally
    cap = actions.get("liability_cap", 1)
    risk_delta -= min(0.2, cap * 0.05)

    # Governing law impact
    governing_law = actions.get("governing_law", "India")
    if governing_law == "UK":
        risk_delta -= 0.04  # UK law generally favorable
    elif governing_law == "US":
        risk_delta += 0.06  # US law more litigious
    elif governing_law == "Singapore":
        risk_delta -= 0.08  # Singapore very business-friendly

    # Arbitration clause reduces litigation risk
    if actions.get("add_arbitration"):
        risk_delta -= 0.18

    # Termination rights provide flexibility
    if actions.get("termination_rights"):
        risk_delta -= 0.10

    # Run Monte Carlo simulation
    base_exposure = contract.get("exposure", 500_000_000)
    losses = monte_carlo_losses(base_exposure, risk_delta)

    # Calculate statistics
    avg_loss = int(np.mean(losses))
    percentile_95 = int(np.percentile(losses, 95))
    percentile_99 = int(np.percentile(losses, 99))

    # Create loss distribution histogram
    # Use bins=20 and get actual counts, not density
    hist, bin_edges = np.histogram(losses, bins=20, density=False)

    # Normalize to get probabilities (sum to 1)
    total = np.sum(hist)
    if total > 0:
        hist = hist / total
    else:
        # Fallback: create uniform distribution
        hist = np.ones(20) / 20

    # Negotiation leverage shifts opposite to risk
    # Higher risk = worse negotiation position
    negotiation_shift = round(-risk_delta * 1.8, 2)

    return {
        "risk_delta": round(risk_delta, 3),
        "avg_loss": avg_loss,
        "percentile_95": percentile_95,
        "percentile_99": percentile_99,
        "negotiation_shift": negotiation_shift,
        "loss_distribution": [
            {"loss": int(bin_edges[i]), "prob": float(hist[i])}
            for i in range(len(hist))
        ],
        "confidence_interval": {
            "lower": int(np.percentile(losses, 5)),
            "upper": int(np.percentile(losses, 95))
        }
    }


def calculate_var(losses: List[float], confidence: float = 0.95) -> float:
    """
    Calculate Value at Risk (VaR) at given confidence level

    Args:
        losses: List of simulated losses
        confidence: Confidence level (default 95%)

    Returns:
        VaR value
    """
    return np.percentile(losses, confidence * 100)


def calculate_cvar(losses: List[float], confidence: float = 0.95) -> float:
    """
    Calculate Conditional Value at Risk (CVaR) - expected loss beyond VaR

    Args:
        losses: List of simulated losses
        confidence: Confidence level (default 95%)

    Returns:
        CVaR value
    """
    var = calculate_var(losses, confidence)
    tail_losses = [loss for loss in losses if loss >= var]
    return np.mean(tail_losses) if tail_losses else 0
