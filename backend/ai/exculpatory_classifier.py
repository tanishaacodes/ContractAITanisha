"""
Exculpatory Clause Classifier
Keyword-based and pattern-based classification logic
"""

from typing import Dict, Tuple
from .exculpatory_patterns import EXCULPATORY_KEYWORDS, RISK_CATEGORIES


def classify_by_keywords(text: str) -> Tuple[float, bool]:
    """
    Classify clause using keyword matching.

    Args:
        text: Clause text

    Returns:
        Tuple of (risk_score, is_exculpatory)
    """
    text_lower = text.lower()
    matches = 0

    for keyword in EXCULPATORY_KEYWORDS:
        if keyword in text_lower:
            matches += 1

    # Calculate risk score based on keyword density
    risk_score = min(matches / 3.0, 1.0)  # Cap at 1.0
    is_exculpatory = risk_score >= 0.4

    return risk_score, is_exculpatory


def infer_risk_category(text: str) -> str:
    """
    Infer risk category from clause text.

    Args:
        text: Clause text

    Returns:
        Risk category string
    """
    text_lower = text.lower()

    # Category-specific keywords
    category_keywords = {
        "FORCE_MAJEURE": ["force majeure", "act of god", "war", "terrorism", "pandemic", "epidemic", "natural disaster", "hurricane", "earthquake", "exceptional event", "beyond control"],
        "SITE_CONDITIONS": ["site", "ground", "subsurface", "soil", "water table", "geological", "site condition", "unforeseen condition"],
        "STATUTORY_APPROVALS": ["approval", "permit", "permission", "statutory", "regulatory", "authority", "consent", "license"],
        "DELAY": ["delay", "extension", "time", "schedule", "completion", "deadline", "postpone", "extension of time"],
        "PAYMENT": ["payment", "invoice", "withhold", "retention", "pay", "certified"],
        "INDEMNITY": ["indemnify", "hold harmless", "defend", "liability", "indemnification", "release"],
        "DESIGN": ["design", "specification", "drawing", "plan", "design responsibility"],
        "VARIATION": ["variation", "change", "modification", "alteration", "change order"],
        "WARRANTY": ["warrant", "guarantee", "defect", "deficiency", "warranty"],
        "TERMINATION": ["terminate", "termination", "cancel", "cancellation"],
        "WORKMANSHIP": ["workmanship", "quality", "standard", "defect"],
    }

    # Count matches for each category
    category_scores = {}
    for category, keywords in category_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            category_scores[category] = score

    # Return category with highest score
    if category_scores:
        return max(category_scores, key=category_scores.get)

    return "OTHER"


def detect_risk_allocation(text: str) -> Dict[str, str]:
    """
    Detect who controls vs who bears the risk.

    Args:
        text: Clause text

    Returns:
        Dict with controlled_by, bearer, and is_imbalanced
    """
    text_lower = text.lower()

    # Indicators of control
    employer_control_indicators = [
        "employer shall",
        "owner shall",
        "client shall",
        "employer may",
        "employer's discretion",
        "subject to approval",
        "employer controls",
        "site access",
    ]

    # Indicators of risk bearing
    contractor_risk_indicators = [
        "contractor shall",
        "contractor's risk",
        "contractor bears",
        "at contractor's cost",
        "contractor indemnif",
        "contractor warrants",
        "deemed to have",
        "contractor acknowledges",
    ]

    employer_risk_indicators = [
        "employer shall be liable",
        "employer's risk",
        "employer bears",
        "at employer's cost",
    ]

    # Analyze control
    employer_control = any(ind in text_lower for ind in employer_control_indicators)

    # Analyze risk bearing
    contractor_bears = any(ind in text_lower for ind in contractor_risk_indicators)
    employer_bears = any(ind in text_lower for ind in employer_risk_indicators)

    # Determine allocation
    if employer_control and contractor_bears:
        return {
            "controlled_by": "employer",
            "bearer": "contractor",
            "is_imbalanced": True,
            "explanation": "Employer controls the risk factor but contractor bears the consequence"
        }
    elif contractor_bears and not employer_control:
        return {
            "controlled_by": "contractor",
            "bearer": "contractor",
            "is_imbalanced": False,
            "explanation": "Contractor controls and bears the risk - balanced allocation"
        }
    elif employer_bears:
        return {
            "controlled_by": "employer",
            "bearer": "employer",
            "is_imbalanced": False,
            "explanation": "Employer controls and bears the risk - balanced allocation"
        }
    else:
        return {
            "controlled_by": "both",
            "bearer": "both",
            "is_imbalanced": False,
            "explanation": "Balanced allocation with mutual obligations"
        }


def generate_imbalance_explanation(controlled_by: str, bearer: str, category: str) -> str:
    """
    Generate human-readable explanation for risk imbalance.

    Args:
        controlled_by: Who controls the risk
        bearer: Who bears the risk
        category: Risk category

    Returns:
        Explanation string
    """
    if controlled_by == "employer" and bearer == "contractor":
        explanations = {
            "SITE_CONDITIONS": "Employer controls site access and information, but contractor bears all risk for site conditions",
            "STATUTORY_APPROVALS": "Employer has more influence with authorities but shifts approval risk to contractor",
            "DELAY": "Contractor cannot control third-party delays but bears full consequence including time penalties",
            "DESIGN": "Employer provides design but contractor bears risk of design defects they cannot identify",
            "VARIATION": "Employer can vary scope but contractor absorbs cost and schedule impact",
            "PAYMENT": "Employer controls payment timing and conditions unilaterally",
        }
        return explanations.get(category, "Employer controls the factor but shifts risk to contractor")

    return "Risk allocation appears balanced"
