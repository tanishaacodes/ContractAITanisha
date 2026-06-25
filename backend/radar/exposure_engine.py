"""
Exposure Engine
===============
Calculates financial exposure from market signal movements on a contract.
"""

import logging

logger = logging.getLogger(__name__)


def calculate_commodity_exposure(contract_value, percent_change, has_adjustment_clause):
    """
    Calculate financial exposure from commodity price movement.

    If the contract has a price adjustment clause, it is protected (0 exposure).
    If not, the company bears the full raw material cost swing.

    Args:
        contract_value: float — total contract value
        percent_change: float — % change in commodity price (positive = price up)
        has_adjustment_clause: bool — does the contract have a price adjustment clause?

    Returns:
        dict with exposure breakdown
    """
    if has_adjustment_clause:
        return {
            "exposure_type": "commodity",
            "estimated_impact": 0.0,
            "protected": True,
            "message": "Contract has price adjustment clause — commodity exposure is hedged.",
        }

    estimated_impact = abs(contract_value * (abs(percent_change) / 100))
    opportunity_type = "savings" if percent_change < 0 else "cost_increase"

    return {
        "exposure_type": "commodity",
        "estimated_impact": round(estimated_impact, 2),
        "protected": False,
        "opportunity_type": opportunity_type,
        "percent_change": round(percent_change, 2),
        "message": (
            f"Renegotiation opportunity: commodity prices moved {percent_change:+.2f}%. "
            f"Estimated impact: ₹{estimated_impact:,.0f}."
            if percent_change < 0
            else
            f"Cost risk: commodity prices rose {percent_change:+.2f}%. "
            f"Estimated additional cost: ₹{estimated_impact:,.0f}."
        ),
    }


def calculate_interest_exposure(contract_value, rate_change_bps):
    """
    Calculate financing cost exposure from interest rate movement.

    Args:
        contract_value: float
        rate_change_bps: float — change in basis points (e.g. 25 = +0.25%)

    Returns:
        dict with exposure breakdown
    """
    rate_change_pct = rate_change_bps / 100.0
    annual_impact = contract_value * (rate_change_pct / 100.0)

    return {
        "exposure_type": "interest_rate",
        "rate_change_bps": round(rate_change_bps, 2),
        "annual_financing_impact": round(annual_impact, 2),
        "protected": False,
        "message": (
            f"Interest rate moved {rate_change_bps:+.1f} bps. "
            f"Annual financing impact: ₹{annual_impact:,.0f}."
        ),
    }


def calculate_fx_exposure(contract_value, fx_percent_change, currency_pair="USD/INR"):
    """
    Calculate FX exposure for contracts with cross-currency elements.
    """
    fx_impact = contract_value * (abs(fx_percent_change) / 100)
    direction = "depreciation risk" if fx_percent_change > 0 else "appreciation benefit"

    return {
        "exposure_type": "fx",
        "currency_pair": currency_pair,
        "fx_change_pct": round(fx_percent_change, 2),
        "estimated_impact": round(fx_impact, 2),
        "direction": direction,
        "message": (
            f"{currency_pair} moved {fx_percent_change:+.2f}% ({direction}). "
            f"Estimated FX impact: ₹{fx_impact:,.0f}."
        ),
    }


def aggregate_total_exposure(exposures):
    """Sum up all exposure impacts across signals."""
    total = sum(e.get('estimated_impact', 0) or e.get('annual_financing_impact', 0) for e in exposures)
    return round(total, 2)
