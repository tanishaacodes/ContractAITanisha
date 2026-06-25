"""
Clause Interaction Analysis
Detects compound and hidden risks from clause combinations.

Based on Prof. Murali's research: Individual clauses may seem reasonable,
but their COMBINATION can create severe risk traps.
"""

from typing import List, Dict, Tuple, Set
from dataclasses import dataclass

@dataclass
class ClauseData:
    """Simplified clause data for interaction analysis"""
    clause_id: str
    text: str
    category: str
    risk_score: float
    is_exculpatory: bool

@dataclass
class InteractionRisk:
    """Represents a compound risk from clause interactions"""
    risk_type: str
    severity: str  # "CRITICAL" | "HIGH" | "MEDIUM"
    involved_clauses: List[str]  # clause IDs
    description: str
    financial_multiplier: float  # How much this amplifies risk (1.0 = no amplification)
    mitigation: str

# Dangerous clause combinations that create compound risks
INTERACTION_PATTERNS = [
    {
        "name": "PAYMENT_TRAP",
        "description": "Owner controls both payment timing AND has no-interest withholding rights",
        "categories": ["PAYMENT_WITHHOLDING", "VARIATION_ORDERS"],
        "keywords": {
            "PAYMENT_WITHHOLDING": ["withhold", "retain", "sole discretion"],
            "VARIATION_ORDERS": ["no additional cost", "without adjustment"]
        },
        "severity": "CRITICAL",
        "financial_multiplier": 1.8,
        "explanation": "Owner can order unlimited variations without cost adjustment, then withhold payment indefinitely. This creates severe cashflow crisis.",
        "mitigation": "Require: (1) Price adjustment for all variations, (2) Payment within fixed terms, (3) Interest on delayed payments"
    },
    {
        "name": "DELAY_LIQUIDATED_DAMAGES_TRAP",
        "description": "Force majeure gives no relief + Owner can cause delays + Liquidated damages continue",
        "categories": ["FORCE_MAJEURE", "DELAY_OWNER_CAUSED"],
        "keywords": {
            "FORCE_MAJEURE": ["no extension", "no relief", "contractor bears"],
            "DELAY_OWNER_CAUSED": ["no time extension", "liquidated damages"]
        },
        "severity": "CRITICAL",
        "financial_multiplier": 2.2,
        "explanation": "Contractor pays delay penalties for delays beyond their control (force majeure + owner delays). This is commercially catastrophic.",
        "mitigation": "Require: (1) Time extension for force majeure, (2) Time extension for owner-caused delays, (3) Suspend LD during owner delays"
    },
    {
        "name": "INDEMNITY_LIABILITY_TRAP",
        "description": "Unlimited indemnity + Unlimited liability beyond insurance + Owner controls site",
        "categories": ["INDEMNITY_SCOPE", "INSURANCE_LIABILITY", "SITE_CONDITIONS"],
        "keywords": {
            "INDEMNITY_SCOPE": ["unlimited", "hold harmless", "indemnify"],
            "INSURANCE_LIABILITY": ["not limited to insurance", "beyond coverage"],
            "SITE_CONDITIONS": ["all risk", "unforeseen conditions"]
        },
        "severity": "CRITICAL",
        "financial_multiplier": 3.0,
        "explanation": "Contractor has unlimited liability for owner-controlled risks (site conditions) beyond insurance limits. This can bankrupt the contractor.",
        "mitigation": "Require: (1) Cap indemnity at insurance limits, (2) Owner bears site condition risks, (3) Mutual indemnity only"
    },
    {
        "name": "TERMINATION_PAYMENT_TRAP",
        "description": "Owner convenience termination + Payment withholding + No profit recovery",
        "categories": ["TERMINATION_RIGHTS", "PAYMENT_WITHHOLDING"],
        "keywords": {
            "TERMINATION_RIGHTS": ["convenience", "sole discretion", "no compensation for profit"],
            "PAYMENT_WITHHOLDING": ["withhold", "set off", "retain"]
        },
        "severity": "HIGH",
        "financial_multiplier": 1.6,
        "explanation": "Owner can terminate anytime, withhold payments, and contractor loses anticipated profits plus demobilization costs.",
        "mitigation": "Require: (1) Reasonable termination notice, (2) Payment for work done plus profit on work done, (3) Demobilization costs"
    },
    {
        "name": "DESIGN_WARRANTY_TRAP",
        "description": "Contractor liable for design defects + Long warranty period + No design control",
        "categories": ["DESIGN_DEFECTS", "WARRANTY_PERIOD"],
        "keywords": {
            "DESIGN_DEFECTS": ["contractor liable", "design errors", "all defects"],
            "WARRANTY_PERIOD": ["10 year", "extended warranty", "long term"]
        },
        "severity": "HIGH",
        "financial_multiplier": 1.7,
        "explanation": "Contractor warrants owner's design for 10+ years despite having no control over design. Commercially unreasonable.",
        "mitigation": "Require: (1) Owner liability for design defects, (2) Warranty period 1-2 years for workmanship only, (3) Exclude design defects"
    },
    {
        "name": "APPROVAL_DELAY_TRAP",
        "description": "Contractor responsible for approvals + Owner controls approval process + No time relief",
        "categories": ["STATUTORY_APPROVALS", "DELAY_OWNER_CAUSED"],
        "keywords": {
            "STATUTORY_APPROVALS": ["contractor responsible", "all approvals", "permits"],
            "DELAY_OWNER_CAUSED": ["no extension", "liquidated damages continue"]
        },
        "severity": "HIGH",
        "financial_multiplier": 1.5,
        "explanation": "Contractor pays delay penalties for government approvals they cannot control, especially when owner owns land.",
        "mitigation": "Require: (1) Owner responsible for approvals, (2) Time extensions for approval delays, (3) Cost reimbursement"
    },
    {
        "name": "VARIATION_TERMINATION_TRAP",
        "description": "Unlimited variations without cost adjustment + Terminate if contractor objects",
        "categories": ["VARIATION_ORDERS", "TERMINATION_RIGHTS"],
        "keywords": {
            "VARIATION_ORDERS": ["execute all", "no adjustment", "without additional cost"],
            "TERMINATION_RIGHTS": ["terminate", "non-compliance", "failure to execute"]
        },
        "severity": "HIGH",
        "financial_multiplier": 1.8,
        "explanation": "Owner can force unlimited free work, and terminate if contractor objects. This eliminates negotiation leverage.",
        "mitigation": "Require: (1) Fair valuation of variations, (2) Termination only for material breach, (3) Dispute resolution for disagreements"
    },
    {
        "name": "FORCE_MAJEURE_INSURANCE_GAP",
        "description": "No force majeure relief + Insurance excludes force majeure + Unlimited liability",
        "categories": ["FORCE_MAJEURE", "INSURANCE_LIABILITY"],
        "keywords": {
            "FORCE_MAJEURE": ["no relief", "contractor bears cost"],
            "INSURANCE_LIABILITY": ["contractor liable", "not covered by insurance"]
        },
        "severity": "CRITICAL",
        "financial_multiplier": 2.5,
        "explanation": "Contractor liable for force majeure costs that insurance won't cover. Creates uninsurable risk.",
        "mitigation": "Require: (1) Force majeure relief provisions, (2) Shared risk for uninsurable events, (3) Contract suspension rights"
    },
    {
        "name": "DISPUTE_PAYMENT_TRAP",
        "description": "Owner-selected arbitrator + Payment withheld during disputes + No independent review",
        "categories": ["DISPUTE_RESOLUTION", "PAYMENT_WITHHOLDING"],
        "keywords": {
            "DISPUTE_RESOLUTION": ["owner selects", "sole arbitrator", "no appeal"],
            "PAYMENT_WITHHOLDING": ["dispute", "withhold", "claimed amounts"]
        },
        "severity": "HIGH",
        "financial_multiplier": 1.4,
        "explanation": "Owner controls both the dispute process AND payment during disputes. Eliminates contractor's negotiating position.",
        "mitigation": "Require: (1) Neutral arbitrator selection, (2) Continue payment of undisputed amounts, (3) Right to judicial review"
    }
]

def detect_clause_interactions(clauses: List[ClauseData]) -> List[InteractionRisk]:
    """
    Analyze clauses to detect dangerous combinations.

    Args:
        clauses: List of analyzed clauses

    Returns:
        List of detected interaction risks
    """
    detected_risks = []

    # Group clauses by category for efficient lookup
    category_map: Dict[str, List[ClauseData]] = {}
    for clause in clauses:
        if clause.category not in category_map:
            category_map[clause.category] = []
        category_map[clause.category].append(clause)

    # Check each interaction pattern
    for pattern in INTERACTION_PATTERNS:
        required_categories = pattern["categories"]
        keywords_by_category = pattern["keywords"]

        # Check if all required categories are present
        present_categories = [cat for cat in required_categories if cat in category_map]
        if len(present_categories) < len(required_categories):
            continue  # Pattern not applicable

        # Check if keywords match in each category
        matching_clauses = {}
        pattern_matched = True

        for category in required_categories:
            category_clauses = category_map.get(category, [])
            required_keywords = keywords_by_category.get(category, [])

            # Find clauses in this category that match the keywords
            matched = False
            for clause in category_clauses:
                clause_lower = clause.text.lower()
                if any(keyword.lower() in clause_lower for keyword in required_keywords):
                    matching_clauses[category] = clause.clause_id
                    matched = True
                    break

            if not matched:
                pattern_matched = False
                break

        # If pattern fully matched, create interaction risk
        if pattern_matched:
            interaction = InteractionRisk(
                risk_type=pattern["name"],
                severity=pattern["severity"],
                involved_clauses=list(matching_clauses.values()),
                description=pattern["description"],
                financial_multiplier=pattern["financial_multiplier"],
                mitigation=pattern["mitigation"]
            )
            detected_risks.append(interaction)

    return detected_risks

def calculate_compound_risk_score(base_risk_score: float, interactions: List[InteractionRisk]) -> float:
    """
    Calculate amplified risk score considering clause interactions.

    Args:
        base_risk_score: Average risk score from individual clauses
        interactions: Detected interaction risks

    Returns:
        Compound risk score (0.0 to 1.0)
    """
    if not interactions:
        return base_risk_score

    # Apply multipliers from interactions
    multiplier = 1.0
    for interaction in interactions:
        # Critical interactions have higher weight
        weight = 1.0 if interaction.severity == "CRITICAL" else 0.7
        multiplier += (interaction.financial_multiplier - 1.0) * weight

    compound_score = min(1.0, base_risk_score * multiplier)
    return compound_score

def get_interaction_summary(interactions: List[InteractionRisk]) -> str:
    """
    Generate human-readable summary of interaction risks.

    Args:
        interactions: Detected interaction risks

    Returns:
        Formatted summary text
    """
    if not interactions:
        return "No dangerous clause interactions detected."

    summary = f"**COMPOUND RISK ALERT: {len(interactions)} dangerous clause interaction(s) detected**\n\n"

    critical_count = sum(1 for i in interactions if i.severity == "CRITICAL")
    high_count = sum(1 for i in interactions if i.severity == "HIGH")

    if critical_count > 0:
        summary += f"⚠️ **{critical_count} CRITICAL interaction(s)** - Immediate attention required\n"
    if high_count > 0:
        summary += f"⚠️ **{high_count} HIGH severity interaction(s)** - Significant risk\n"

    summary += "\n---\n\n"

    for idx, interaction in enumerate(interactions, 1):
        summary += f"**{idx}. {interaction.risk_type.replace('_', ' ').title()}** ({interaction.severity})\n\n"
        summary += f"**Problem:** {interaction.description}\n\n"

        # Find the pattern explanation
        pattern_info = next((p for p in INTERACTION_PATTERNS if p["name"] == interaction.risk_type), None)
        if pattern_info:
            summary += f"**Impact:** {pattern_info['explanation']}\n\n"
            summary += f"**Financial Amplification:** {pattern_info['financial_multiplier']}x\n\n"
            summary += f"**Mitigation:** {pattern_info['mitigation']}\n\n"

        summary += f"**Involved Clauses:** {', '.join(interaction.involved_clauses)}\n\n"
        summary += "---\n\n"

    return summary

def prioritize_negotiation_points(interactions: List[InteractionRisk]) -> List[Dict[str, any]]:
    """
    Prioritize which clause interactions to negotiate first.

    Returns:
        List of negotiation priorities with action items
    """
    priorities = []

    # Sort by severity and financial impact
    severity_order = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1}
    sorted_interactions = sorted(
        interactions,
        key=lambda x: (severity_order.get(x.severity, 0), x.financial_multiplier),
        reverse=True
    )

    for rank, interaction in enumerate(sorted_interactions, 1):
        pattern_info = next((p for p in INTERACTION_PATTERNS if p["name"] == interaction.risk_type), None)

        priority = {
            "rank": rank,
            "risk_type": interaction.risk_type,
            "severity": interaction.severity,
            "description": interaction.description,
            "financial_multiplier": interaction.financial_multiplier,
            "action": pattern_info["mitigation"] if pattern_info else "Negotiate fairer allocation",
            "involved_clauses": interaction.involved_clauses
        }
        priorities.append(priority)

    return priorities
