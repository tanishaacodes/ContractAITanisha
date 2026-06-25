"""
Trust Engine - Trust Badge Assignment

Assigns human-readable trust badges based on multi-dimensional analysis.
Badges are explainable and defensible to legal/business stakeholders.
"""


def assign_trust_badge(trust_score, ambiguity, negotiability, enforceability):
    """
    Assign trust badge based on clause characteristics.

    Badges:
        - COURT_PROVEN: High trust (>0.8), low ambiguity (<0.3), proven in litigation
        - DEAL_MAKER: High negotiability (>0.7), smooth deal closure
        - NEGOTIATION_FRAGILE: Low negotiability (<0.4), high dispute rate
        - SILENT_KILLER: Low trust (<0.4), high ambiguity (>0.7), hidden risk
        - UNTESTED: No outcome history, presumed safe but unproven
        - STANDARD: Normal clause, no special characteristics

    Args:
        trust_score: Overall trust score (0-1)
        ambiguity: Ambiguity score (0-1)
        negotiability: Negotiability score (0-1)
        enforceability: Enforceability score (0-1)

    Returns:
        dict: Badge information
    """
    # Court-Proven: Best case scenario
    if trust_score > 0.8 and ambiguity < 0.3 and enforceability > 0.75:
        return {
            "badge": "COURT_PROVEN",
            "label": "Court-Proven",
            "color": "#10b981",  # Green
            "icon": "⚖️",
            "description": "Proven enforceable in court with clear language",
            "priority": 1
        }

    # Deal Maker: Closes deals smoothly
    if negotiability > 0.7 and trust_score > 0.65:
        return {
            "badge": "DEAL_MAKER",
            "label": "Deal Maker",
            "color": "#3b82f6",  # Blue
            "icon": "🤝",
            "description": "Smoothly accepted, low negotiation friction",
            "priority": 2
        }

    # Negotiation-Fragile: Kills deals
    if negotiability < 0.4:
        return {
            "badge": "NEGOTIATION_FRAGILE",
            "label": "Negotiation-Fragile",
            "color": "#f59e0b",  # Amber
            "icon": "⚠️",
            "description": "High dispute rate, consider rewording",
            "priority": 3
        }

    # Silent Killer: Hidden danger
    if trust_score < 0.4 and ambiguity > 0.7:
        return {
            "badge": "SILENT_KILLER",
            "label": "Silent Killer",
            "color": "#ef4444",  # Red
            "icon": "💀",
            "description": "Ambiguous language + poor outcomes = high risk",
            "priority": 4
        }

    # Litigation Risk: Court failures
    if enforceability < 0.3:
        return {
            "badge": "LITIGATION_RISK",
            "label": "Litigation Risk",
            "color": "#dc2626",  # Dark red
            "icon": "⚡",
            "description": "Failed in court, likely unenforceable",
            "priority": 5
        }

    # Untested: No history
    if enforceability == 0.8 and negotiability == 0.5:  # Default scores indicate no history
        return {
            "badge": "UNTESTED",
            "label": "Untested",
            "color": "#6b7280",  # Gray
            "icon": "❓",
            "description": "No outcome history, presumed safe but unproven",
            "priority": 6
        }

    # Standard: Normal clause
    return {
        "badge": "STANDARD",
        "label": "Standard",
        "color": "#8b5cf6",  # Purple
        "icon": "📄",
        "description": "Normal clause performance",
        "priority": 7
    }


def badge_recommendation(badge_info):
    """
    Get actionable recommendation based on badge.

    Args:
        badge_info: Badge dict from assign_trust_badge()

    Returns:
        str: Recommendation text
    """
    recommendations = {
        "COURT_PROVEN": "Use with confidence. This clause has proven itself in real litigation.",
        "DEAL_MAKER": "Excellent choice for smooth negotiations. Counterparties rarely object.",
        "NEGOTIATION_FRAGILE": "Consider rewording for clarity. This clause frequently triggers disputes.",
        "SILENT_KILLER": "HIGH RISK: Ambiguous language has led to poor outcomes. Rewrite immediately.",
        "LITIGATION_RISK": "CRITICAL: This clause has failed in court. Replace with proven alternative.",
        "UNTESTED": "No historical data. Monitor outcomes carefully if used.",
        "STANDARD": "Acceptable clause. Monitor for any emerging patterns."
    }

    return recommendations.get(badge_info["badge"], "No specific recommendation.")


def badge_alternatives(badge_info):
    """
    Suggest alternative actions based on badge.

    Args:
        badge_info: Badge dict from assign_trust_badge()

    Returns:
        list: Action suggestions
    """
    alternatives = {
        "COURT_PROVEN": [
            "Promote to standard library",
            "Use as template for similar clauses"
        ],
        "DEAL_MAKER": [
            "Add to preferred clauses",
            "Share with legal team as best practice"
        ],
        "NEGOTIATION_FRAGILE": [
            "Review and simplify language",
            "Add negotiation fallback options",
            "Consider jurisdictional variations"
        ],
        "SILENT_KILLER": [
            "URGENT: Replace with court-proven alternative",
            "Consult legal counsel before using",
            "Add explicit definitions to reduce ambiguity"
        ],
        "LITIGATION_RISK": [
            "CRITICAL: Remove from all contracts",
            "Search for proven alternative in library",
            "Legal review required before any use"
        ],
        "UNTESTED": [
            "Monitor first 5 uses closely",
            "Track negotiation feedback",
            "Request legal review if uncertain"
        ],
        "STANDARD": [
            "Continue monitoring",
            "Compare with similar clauses for optimization"
        ]
    }

    return alternatives.get(badge_info["badge"], ["Monitor clause performance"])


def all_badges():
    """
    Get list of all possible badges with metadata.

    Returns:
        list: All badge definitions
    """
    return [
        {
            "badge": "COURT_PROVEN",
            "label": "Court-Proven",
            "color": "#10b981",
            "icon": "⚖️",
            "description": "Proven enforceable in court"
        },
        {
            "badge": "DEAL_MAKER",
            "label": "Deal Maker",
            "color": "#3b82f6",
            "icon": "🤝",
            "description": "Smoothly accepted in negotiations"
        },
        {
            "badge": "NEGOTIATION_FRAGILE",
            "label": "Negotiation-Fragile",
            "color": "#f59e0b",
            "icon": "⚠️",
            "description": "High dispute rate"
        },
        {
            "badge": "SILENT_KILLER",
            "label": "Silent Killer",
            "color": "#ef4444",
            "icon": "💀",
            "description": "Ambiguous + poor outcomes"
        },
        {
            "badge": "LITIGATION_RISK",
            "label": "Litigation Risk",
            "color": "#dc2626",
            "icon": "⚡",
            "description": "Failed in court"
        },
        {
            "badge": "UNTESTED",
            "label": "Untested",
            "color": "#6b7280",
            "icon": "❓",
            "description": "No outcome history"
        },
        {
            "badge": "STANDARD",
            "label": "Standard",
            "color": "#8b5cf6",
            "icon": "📄",
            "description": "Normal performance"
        }
    ]
