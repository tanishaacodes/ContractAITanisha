"""
Liability Risk Calculation
Calculates financial liability exposure
"""

def liability_risk(liability_value: float, contract_value: float):
    """
    Calculate liability risk based on financial exposure

    Args:
        liability_value: Total liability cap in contract
        contract_value: Total contract value

    Returns:
        Risk score (0-100) and explanation
    """
    if contract_value == 0:
        if liability_value > 0:
            return 95, "Unlimited liability exposure"
        return 10, "No liability specified"

    ratio = liability_value / contract_value

    if ratio > 1:
        return 95, f"Liability exceeds contract value ({ratio:.1f}x)"
    elif ratio > 0.5:
        return 70, f"High liability exposure ({ratio:.1%} of contract value)"
    elif ratio > 0.25:
        return 45, f"Moderate liability ({ratio:.1%} of contract value)"
    else:
        return 30, f"Limited liability ({ratio:.1%} of contract value)"

def calculate_exposure_score(contracts: list):
    """
    Calculate financial exposure across portfolio

    Args:
        contracts: List of contract dictionaries

    Returns:
        Total exposure score
    """
    total_value = sum(c.get('contract_value', 0) for c in contracts)
    total_liability = sum(c.get('total_liability', 0) for c in contracts)

    if total_value == 0:
        return 0

    exposure_ratio = total_liability / total_value

    # Convert to 0-100 scale
    if exposure_ratio > 1:
        return 100
    else:
        return round(exposure_ratio * 100, 2)
