"""
Risk Allocation Knowledge Base
Based on Prof. Murali's research on construction contract risk allocation principles.

Core Principle: Risk should be allocated to the party best able to manage it.
This module defines who SHOULD control each risk type based on FIDIC principles.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class RiskControl:
    """Defines who controls a specific risk and why"""
    risk_type: str
    proper_controller: str  # "CONTRACTOR" or "OWNER" or "SHARED"
    rationale: str
    control_factors: List[str]
    typical_exculpatory_pattern: str

# FIDIC-based Risk Allocation Map
# Defines who SHOULD bear each risk in a balanced construction contract
RISK_ALLOCATION_MAP = {
    "FORCE_MAJEURE": RiskControl(
        risk_type="FORCE_MAJEURE",
        proper_controller="SHARED",
        rationale="Neither party can control acts of God, war, or pandemics. Fair contracts provide time relief (no delay penalties) but no additional cost to owner.",
        control_factors=["unforeseeable", "beyond reasonable control", "unavoidable"],
        typical_exculpatory_pattern="Contractor bears all force majeure costs and time penalties"
    ),

    "SITE_CONDITIONS": RiskControl(
        risk_type="SITE_CONDITIONS",
        proper_controller="OWNER",
        rationale="Owner controls site access and has better information about subsurface conditions. Contractor cannot verify underground conditions during bidding.",
        control_factors=["owner owns land", "better information access", "geological surveys responsibility"],
        typical_exculpatory_pattern="Contractor assumes all risk for unforeseen subsurface conditions"
    ),

    "DESIGN_DEFECTS": RiskControl(
        risk_type="DESIGN_DEFECTS",
        proper_controller="OWNER",
        rationale="Owner's design team controls design. Contractor executes per drawings. Owner should bear risk of design errors unless contractor has design responsibility.",
        control_factors=["owner's consultants", "contractor cannot verify all calculations", "professional liability"],
        typical_exculpatory_pattern="Contractor liable for all design defects even in owner's design"
    ),

    "DELAY_OWNER_CAUSED": RiskControl(
        risk_type="DELAY_OWNER_CAUSED",
        proper_controller="OWNER",
        rationale="Owner controls approvals, design changes, and payments. Delays from owner's actions should not penalize contractor.",
        control_factors=["approval authority", "payment control", "design change authority"],
        typical_exculpatory_pattern="No time extensions for owner-caused delays, liquidated damages continue"
    ),

    "INDEMNITY_SCOPE": RiskControl(
        risk_type="INDEMNITY_SCOPE",
        proper_controller="SHARED",
        rationale="Each party should indemnify for their own negligence. Unlimited indemnity for owner's negligence is unfair.",
        control_factors=["negligence causation", "insurance limits", "proportional liability"],
        typical_exculpatory_pattern="Contractor indemnifies owner for owner's own negligence with no cap"
    ),

    "PAYMENT_WITHHOLDING": RiskControl(
        risk_type="PAYMENT_WITHHOLDING",
        proper_controller="OWNER",
        rationale="Owner controls payment but must have objective criteria. Arbitrary withholding without interest is unfair cashflow burden.",
        control_factors=["payment authority", "cashflow impact", "work progress verification"],
        typical_exculpatory_pattern="Owner may withhold any amount at sole discretion without interest"
    ),

    "VARIATION_ORDERS": RiskControl(
        risk_type="VARIATION_ORDERS",
        proper_controller="OWNER",
        rationale="Owner controls scope changes. Contractor should receive fair adjustment in price and time for variations.",
        control_factors=["scope change authority", "resource planning impact", "schedule disruption"],
        typical_exculpatory_pattern="Execute all variations without price or time adjustment unless owner agrees"
    ),

    "WARRANTY_PERIOD": RiskControl(
        risk_type="WARRANTY_PERIOD",
        proper_controller="SHARED",
        rationale="Contractor warrants workmanship (1-2 years typical), but not design defects or owner's misuse. 10+ years is unreasonable.",
        control_factors=["workmanship quality", "material defects", "normal wear and tear"],
        typical_exculpatory_pattern="10-year warranty covering even owner's misuse and design defects"
    ),

    "STATUTORY_APPROVALS": RiskControl(
        risk_type="STATUTORY_APPROVALS",
        proper_controller="OWNER",
        rationale="Owner controls land and project feasibility. Contractor cannot guarantee government approvals for owner's project.",
        control_factors=["land ownership", "project viability", "government relationships"],
        typical_exculpatory_pattern="Contractor responsible for all approvals with no time/cost relief for delays"
    ),

    "TERMINATION_RIGHTS": RiskControl(
        risk_type="TERMINATION_RIGHTS",
        proper_controller="SHARED",
        rationale="Both parties should have termination rights for material breach. Owner convenience termination should compensate contractor fairly.",
        control_factors=["breach materiality", "profit expectations", "demobilization costs"],
        typical_exculpatory_pattern="Owner may terminate for convenience, contractor loses profits and demob costs"
    ),

    "INSURANCE_LIABILITY": RiskControl(
        risk_type="INSURANCE_LIABILITY",
        proper_controller="SHARED",
        rationale="Each party insures their risks. Unlimited liability beyond insurance is commercially unreasonable.",
        control_factors=["insurance market limits", "premium costs", "risk proportionality"],
        typical_exculpatory_pattern="Unlimited liability not restricted by insurance coverage limits"
    ),

    "DISPUTE_RESOLUTION": RiskControl(
        risk_type="DISPUTE_RESOLUTION",
        proper_controller="SHARED",
        rationale="Both parties should have fair access to neutral dispute resolution. Owner-selected arbitrator violates natural justice.",
        control_factors=["impartiality", "procedural fairness", "judicial review rights"],
        typical_exculpatory_pattern="Arbitrator selected solely by owner, no right to judicial review"
    )
}

def get_risk_imbalance(category: str, clause_text: str) -> Tuple[str, float, str]:
    """
    Evaluate if a clause creates unfair risk allocation.

    Returns:
        (imbalance_severity, imbalance_score, explanation)
        imbalance_severity: "EXTREME" | "HIGH" | "MODERATE" | "LOW" | "BALANCED"
        imbalance_score: 0.0 (balanced) to 1.0 (completely unfair)
        explanation: Human-readable explanation of the imbalance
    """
    if category not in RISK_ALLOCATION_MAP:
        return ("LOW", 0.2, f"Risk category {category} not in allocation map")

    risk_control = RISK_ALLOCATION_MAP[category]
    clause_lower = clause_text.lower()

    # Check for exculpatory patterns
    imbalance_indicators = {
        "EXTREME": [
            "no liability whatsoever",
            "unlimited liability",
            "solely responsible",
            "regardless of",
            "whether or not",
            "waives any right",
            "waives all rights",
            "no claim",
            "no compensation",
            "no extension",
            "at sole discretion",
            "without limitation"
        ],
        "HIGH": [
            "assumes all risk",
            "full responsibility",
            "shall indemnify",
            "hold harmless",
            "without relief",
            "no right to",
            "shall not be entitled"
        ],
        "MODERATE": [
            "contractor responsible",
            "contractor shall bear",
            "no additional cost",
            "at contractor's expense"
        ]
    }

    # Count imbalance indicators
    extreme_count = sum(1 for pattern in imbalance_indicators["EXTREME"] if pattern in clause_lower)
    high_count = sum(1 for pattern in imbalance_indicators["HIGH"] if pattern in clause_lower)
    moderate_count = sum(1 for pattern in imbalance_indicators["MODERATE"] if pattern in clause_lower)

    # Calculate imbalance score
    imbalance_score = min(1.0, (extreme_count * 0.3 + high_count * 0.15 + moderate_count * 0.05))

    # Determine severity
    if imbalance_score >= 0.7:
        severity = "EXTREME"
    elif imbalance_score >= 0.5:
        severity = "HIGH"
    elif imbalance_score >= 0.3:
        severity = "MODERATE"
    elif imbalance_score >= 0.1:
        severity = "LOW"
    else:
        severity = "BALANCED"

    # Generate explanation
    explanation = f"This {category} clause allocates risk to contractor. "
    explanation += f"According to FIDIC principles, {risk_control.proper_controller.lower()} should control this risk "
    explanation += f"because {risk_control.rationale} "

    if severity in ["EXTREME", "HIGH"]:
        explanation += f"This clause shows extreme imbalance with {extreme_count} severe and {high_count} high-risk terms."

    return (severity, imbalance_score, explanation)

def get_proper_allocation_advice(category: str) -> str:
    """Get advice on proper risk allocation for a category"""
    if category not in RISK_ALLOCATION_MAP:
        return "Standard FIDIC principles should apply for balanced risk allocation."

    risk_control = RISK_ALLOCATION_MAP[category]

    advice = f"**Proper Risk Allocation for {category}:**\n\n"
    advice += f"**Who Should Control:** {risk_control.proper_controller}\n\n"
    advice += f"**Rationale:** {risk_control.rationale}\n\n"
    advice += f"**Control Factors:**\n"
    for factor in risk_control.control_factors:
        advice += f"- {factor}\n"

    advice += f"\n**Red Flag Pattern:**\n"
    advice += f"'{risk_control.typical_exculpatory_pattern}'\n\n"
    advice += "**Recommended Action:** Negotiate to align risk allocation with control and capability."

    return advice

def calculate_financial_exposure(category: str, contract_value: float, imbalance_score: float) -> Dict[str, float]:
    """
    Estimate financial exposure from unfair risk allocation.

    Args:
        category: Risk category
        contract_value: Total contract value in currency units
        imbalance_score: 0.0 to 1.0 from get_risk_imbalance

    Returns:
        Dictionary with exposure metrics
    """
    # Risk-specific exposure multipliers (based on construction industry data)
    exposure_multipliers = {
        "FORCE_MAJEURE": 0.15,  # 15% of contract value in extreme cases
        "SITE_CONDITIONS": 0.25,  # 25% for unforeseen ground conditions
        "DESIGN_DEFECTS": 0.30,  # 30% for major design errors
        "DELAY_OWNER_CAUSED": 0.20,  # 20% for prolonged delays
        "INDEMNITY_SCOPE": 0.50,  # 50%+ for unlimited indemnity
        "PAYMENT_WITHHOLDING": 0.10,  # 10% cashflow impact
        "VARIATION_ORDERS": 0.15,  # 15% scope changes
        "WARRANTY_PERIOD": 0.12,  # 12% long-term defects
        "STATUTORY_APPROVALS": 0.18,  # 18% approval delays
        "TERMINATION_RIGHTS": 0.40,  # 40% lost profits + demob
        "INSURANCE_LIABILITY": 0.60,  # 60%+ unlimited liability
        "DISPUTE_RESOLUTION": 0.08   # 8% unfair process costs
    }

    base_multiplier = exposure_multipliers.get(category, 0.10)

    # Calculate exposure components
    max_exposure = contract_value * base_multiplier * imbalance_score
    likely_exposure = max_exposure * 0.6  # 60% probability scenario
    minimum_exposure = max_exposure * 0.3  # 30% best case

    return {
        "maximum_exposure": round(max_exposure, 2),
        "likely_exposure": round(likely_exposure, 2),
        "minimum_exposure": round(minimum_exposure, 2),
        "exposure_percentage": round(base_multiplier * imbalance_score * 100, 2)
    }
