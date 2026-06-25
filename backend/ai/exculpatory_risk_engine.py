"""
Exculpatory Risk Engine
Hybrid risk scoring combining keyword matching and pattern similarity
Enhanced with Prof. Murali's research: Risk allocation, clause interactions, and financial impact
"""

from typing import Dict, List, Any, Optional
from .exculpatory_classifier import (
    classify_by_keywords,
    infer_risk_category,
    detect_risk_allocation,
    generate_imbalance_explanation
)
from .exculpatory_embeddings import cosine_similarity
from .risk_allocation_map import (
    get_risk_imbalance,
    get_proper_allocation_advice,
    calculate_financial_exposure
)
from .clause_interaction_detector import (
    detect_clause_interactions,
    calculate_compound_risk_score,
    get_interaction_summary,
    prioritize_negotiation_points,
    ClauseData
)
from .explainability_engine import (
    generate_impact_chain,
    format_impact_chain_for_display
)


def calculate_hybrid_risk_score(
    keyword_score: float,
    pattern_matches: List[Dict[str, Any]]
) -> float:
    """
    Calculate final risk score using hybrid approach.

    Args:
        keyword_score: Score from keyword matching (0-1)
        pattern_matches: List of pattern matches with similarity scores

    Returns:
        Final risk score (0-1)
    """
    # Get best pattern similarity
    pattern_score = 0.0
    if pattern_matches:
        pattern_score = max(match["similarity"] for match in pattern_matches)

    # Weighted combination: 40% keywords, 60% patterns
    # Pattern matching is more reliable for semantic understanding
    final_score = round(0.4 * keyword_score + 0.6 * pattern_score, 2)

    return final_score


def generate_mitigation_suggestions(
    risk_score: float,
    risk_category: str,
    is_imbalanced: bool,
    pattern_matches: List[Dict[str, Any]]
) -> List[str]:
    """
    Generate actionable mitigation suggestions based on risk analysis.
    """
    suggestions = []

    # High risk suggestions
    if risk_score >= 0.7:
        suggestions.append("CRITICAL: Request immediate removal or reject tender. This clause transfers substantial uncontrollable risk creating potential unlimited liability exposure. If non-negotiable, add counter-clause limiting liability to direct costs capped at contract value or insurance limits.")
        suggestions.append("Price defensively with 25-35% contingency reserve for risks under this clause. Document contingency separately in bid breakdown for future claims justification and audit trail.")
    elif risk_score >= 0.4:
        suggestions.append("NEGOTIATE: Request modification to balance risk allocation. Propose shared responsibility mechanisms with clear triggering criteria, defined thresholds, and measurable compliance standards to prevent open-ended exposure.")

    # Category-specific suggestions
    if risk_category == "FORCE_MAJEURE":
        suggestions.append("Propose balanced FM clause: (1) clearly define qualifying events (pandemic, war, natural disasters), (2) require 7-day written notice, (3) grant time extensions for FM delays, (4) allow termination if FM persists beyond 90 days, (5) explicitly state neither party liable for FM consequences.")
    elif risk_category == "SITE_CONDITIONS":
        suggestions.append("Request employer provide geotechnical reports, utility mapping, hazardous material surveys within 12 months. Insert 'differing site conditions' clause allowing time/cost adjustments if conditions differ materially from provided information or reasonable expectations.")
        suggestions.append("Add protective language: 'Contractor pricing assumes reliance on employer-provided site data. Contractor entitled to compensation for variations arising from differing subsurface or concealed conditions discovered during execution.'")
    elif risk_category == "DELAY":
        suggestions.append("Negotiate automatic EOT for: employer delays, variations, late approvals, suspension orders, FM events, utility conflicts. Include both time AND cost compensation. Add LD relief clause suspending LD during employer-caused delays.")
    elif risk_category == "INDEMNITY":
        suggestions.append("Limit indemnification to contractor's negligence/willful misconduct only. Exclude employer's negligence and design defects. Cap at 100% contract value or insurance limit. Add temporal limit (24 months post-completion). Exclude consequential damages and lost profits.")
    elif risk_category == "STATUTORY_APPROVALS":
        suggestions.append("Clarify: Employer obtains land-use permits, environmental clearances pre-award; contractor obtains work-specific permits only. Add relief clause: 'If approvals delayed/denied beyond reasonable anticipation, contractor entitled to time extension plus cost adjustment.'")
    elif risk_category == "DESIGN":
        suggestions.append("Segregate design responsibilities clearly. Add: 'Contractor responsible only for design elements in Appendix X. Employer retains concept design and performance specs. Liability limited to professional negligence standard, not strict liability.' Require employer approval at each design stage.")
    elif risk_category == "PAYMENT":
        suggestions.append("Request monthly progress payments within 21 days, 5% retention (reducing to 2.5% at completion), final retention release within 14 days post-defects period. Add interest on late payments at statutory rate plus 2% margin.")

    # Imbalance-specific
    if is_imbalanced:
        suggestions.append("RISK IMBALANCE: Request reallocation per FIDIC principles - parties control risks they can influence, risks shared when control is joint, compensation applies for uncontrollable events. Add clause: 'Risk allocated to party best able to manage and control it.'")

    # Pattern-specific
    if pattern_matches and len(pattern_matches) > 0:
        top_pattern = pattern_matches[0].get("pattern", "")
        if "No Liability" in top_pattern or "Waiver" in top_pattern:
            suggestions.append("Replace broad waiver with specific limited waivers. Add savings clause: 'Nothing herein waives contractor's rights to claims from employer's breach, negligence, willful default, or misrepresentation per applicable law.'")

    # Default
    if risk_score < 0.4 and not suggestions:
        suggestions.append("Standard clause with balanced risk allocation. Acceptable as drafted. Verify consistency with contract terms, insurance coverage, and local law requirements through routine legal review.")

    return suggestions


def evaluate_clause(
    clause_text: str,
    clause_name: str,
    clause_embedding: List[float],
    pattern_matches: List[Dict[str, Any]],
    contract_value: Optional[float] = None
) -> Dict[str, Any]:
    """
    Perform complete clause evaluation with enhanced risk allocation analysis.

    Args:
        clause_text: Full clause text
        clause_name: Clause identifier/name
        clause_embedding: Embedding vector for the clause
        pattern_matches: Matched patterns from similarity search
        contract_value: Optional contract value for financial exposure calculation

    Returns:
        Complete analysis dictionary with enhanced metrics
    """
    # Keyword-based classification
    keyword_score, _ = classify_by_keywords(clause_text)

    # Infer category
    category = infer_risk_category(clause_text)

    # Detect risk allocation
    allocation = detect_risk_allocation(clause_text)

    # Calculate hybrid score
    risk_score = calculate_hybrid_risk_score(keyword_score, pattern_matches)

    # Enhanced risk imbalance analysis using FIDIC principles
    imbalance_severity, imbalance_score, allocation_explanation = get_risk_imbalance(
        category, clause_text
    )

    # Calculate financial exposure
    financial_exposure = {}
    if contract_value:
        financial_exposure = calculate_financial_exposure(
            category, contract_value, imbalance_score
        )

    # Determine if exculpatory (now considering both risk score and imbalance)
    is_exculpatory = risk_score >= 0.6 or imbalance_severity in ["EXTREME", "HIGH"]

    # Generate detailed explanation
    imbalance_explanation = ""
    if allocation["is_imbalanced"] or imbalance_severity in ["EXTREME", "HIGH"]:
        imbalance_explanation = allocation_explanation

    # Generate mitigation suggestions (enhanced version)
    suggestions = generate_mitigation_suggestions(
        risk_score,
        category,
        allocation["is_imbalanced"],
        pattern_matches
    )

    # Add FIDIC-based allocation advice
    proper_allocation_advice = get_proper_allocation_advice(category)

    # Generate impact chain for explainability
    impact_chain = generate_impact_chain(
        clause_text=clause_text,
        category=category,
        risk_score=risk_score,
        imbalance_severity=imbalance_severity,
        imbalance_explanation=allocation_explanation,
        financial_exposure=financial_exposure,
        contract_value=contract_value
    )

    return {
        "clause_name": clause_name,
        "text": clause_text,
        "risk_score": risk_score,
        "is_exculpatory": is_exculpatory,
        "risk_category": category,
        "controlled_by": allocation["controlled_by"],
        "bearer": allocation["bearer"],
        "is_imbalanced": allocation["is_imbalanced"],
        "imbalance_explanation": imbalance_explanation or allocation["explanation"],
        "pattern_matches": pattern_matches,
        "suggestions": suggestions,
        # Enhanced fields from Prof. Murali's research
        "imbalance_severity": imbalance_severity,
        "imbalance_score": imbalance_score,
        "financial_exposure": financial_exposure,
        "proper_allocation_advice": proper_allocation_advice,
        "impact_chain": impact_chain,
        "deal_breaker": impact_chain.deal_breaker,
        "probability": impact_chain.probability
    }


def generate_summary(
    analyzed_clauses: List[Dict[str, Any]],
    total_clauses: int,
    contract_value: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generate aggregate summary from analyzed clauses with clause interaction analysis.

    Args:
        analyzed_clauses: List of analyzed clause dictionaries
        total_clauses: Total number of clauses in contract
        contract_value: Optional contract value for aggregate financial exposure

    Returns:
        Enhanced summary dictionary with interaction risks
    """
    # Count risk levels
    high_risk = sum(1 for c in analyzed_clauses if c["risk_score"] >= 0.7)
    medium_risk = sum(1 for c in analyzed_clauses if 0.4 <= c["risk_score"] < 0.7)
    low_risk = sum(1 for c in analyzed_clauses if c["risk_score"] < 0.4)

    # Count imbalanced clauses
    imbalanced = sum(1 for c in analyzed_clauses if c["is_imbalanced"])

    # Count deal breakers
    deal_breakers = sum(1 for c in analyzed_clauses if c.get("deal_breaker", False))

    # Category breakdown
    category_breakdown = {}
    for clause in analyzed_clauses:
        if clause["is_exculpatory"]:
            category = clause["risk_category"]
            category_breakdown[category] = category_breakdown.get(category, 0) + 1

    # Calculate percentages
    analyzed_count = len(analyzed_clauses)
    high_pct = round((high_risk / analyzed_count * 100), 1) if analyzed_count > 0 else 0
    medium_pct = round((medium_risk / analyzed_count * 100), 1) if analyzed_count > 0 else 0
    low_pct = round((low_risk / analyzed_count * 100), 1) if analyzed_count > 0 else 0

    # Detect clause interactions (compound risks)
    clause_data_list = [
        ClauseData(
            clause_id=c["clause_name"],
            text=c["text"],
            category=c["risk_category"],
            risk_score=c["risk_score"],
            is_exculpatory=c["is_exculpatory"]
        )
        for c in analyzed_clauses
    ]

    interaction_risks = detect_clause_interactions(clause_data_list)

    # Calculate compound risk score considering interactions
    base_risk_score = sum(c["risk_score"] for c in analyzed_clauses) / analyzed_count if analyzed_count > 0 else 0
    compound_risk_score = calculate_compound_risk_score(base_risk_score, interaction_risks)

    # Generate interaction summary
    interaction_summary = get_interaction_summary(interaction_risks)

    # Prioritize negotiation points
    negotiation_priorities = prioritize_negotiation_points(interaction_risks)

    # Calculate aggregate financial exposure
    total_financial_exposure = {
        "maximum_exposure": 0,
        "likely_exposure": 0,
        "minimum_exposure": 0
    }

    if contract_value:
        for clause in analyzed_clauses:
            exposure = clause.get("financial_exposure", {})
            total_financial_exposure["maximum_exposure"] += exposure.get("maximum_exposure", 0)
            total_financial_exposure["likely_exposure"] += exposure.get("likely_exposure", 0)
            total_financial_exposure["minimum_exposure"] += exposure.get("minimum_exposure", 0)

    # Generate recommendation
    recommendation = generate_recommendation(high_risk, medium_risk, imbalanced, analyzed_count)

    # Enhance recommendation with interaction risks
    if len(interaction_risks) > 0:
        critical_interactions = sum(1 for i in interaction_risks if i.severity == "CRITICAL")
        if critical_interactions > 0:
            recommendation["decision"] = "VERY_HIGH_RISK"
            recommendation["message"] = f"CRITICAL: {critical_interactions} dangerous clause interaction(s) detected. " + recommendation["message"]

    return {
        "total_clauses": total_clauses,
        "analyzed_clauses": analyzed_count,
        "risk_distribution": {
            "high": high_risk,
            "medium": medium_risk,
            "low": low_risk
        },
        "risk_percentages": {
            "high": high_pct,
            "medium": medium_pct,
            "low": low_pct
        },
        "imbalanced_clauses": imbalanced,
        "deal_breakers": deal_breakers,
        "category_breakdown": category_breakdown,
        "recommendation": recommendation,
        # Enhanced fields from Prof. Murali's research
        "base_risk_score": round(base_risk_score, 2),
        "compound_risk_score": round(compound_risk_score, 2),
        "interaction_risks": [
            {
                "risk_type": i.risk_type,
                "severity": i.severity,
                "description": i.description,
                "financial_multiplier": i.financial_multiplier,
                "involved_clauses": i.involved_clauses
            }
            for i in interaction_risks
        ],
        "interaction_summary": interaction_summary,
        "negotiation_priorities": negotiation_priorities,
        "total_financial_exposure": total_financial_exposure
    }


def generate_recommendation(
    high_risk_count: int,
    medium_risk_count: int,
    imbalanced_count: int,
    total_analyzed: int
) -> Dict[str, str]:
    """
    Generate bid recommendation based on risk analysis.

    Args:
        high_risk_count: Number of high-risk clauses
        medium_risk_count: Number of medium-risk clauses
        imbalanced_count: Number of imbalanced clauses
        total_analyzed: Total clauses analyzed

    Returns:
        Recommendation dictionary
    """
    if total_analyzed == 0:
        return {
            "decision": "INSUFFICIENT_DATA",
            "message": "Not enough clauses analyzed to make recommendation"
        }

    high_pct = (high_risk_count / total_analyzed) * 100
    imbalance_pct = (imbalanced_count / total_analyzed) * 100

    # Very High Risk: >30% high risk or >50% imbalanced
    if high_pct > 30 or imbalance_pct > 50:
        return {
            "decision": "VERY_HIGH_RISK",
            "message": "Critical risk imbalance detected across multiple categories. Strongly recommend declining bid or negotiating complete clause restructure with substantial price premium."
        }

    # High Risk: >15% high risk or >30% imbalanced
    if high_pct > 15 or imbalance_pct > 30:
        return {
            "decision": "HIGH_RISK",
            "message": "Significant risk imbalance detected. Several clauses allocate uncontrollable risks to contractor. Negotiate key clauses or price defensively with contingency reserves."
        }

    # Medium Risk: >5% high risk or >15% imbalanced
    if high_pct > 5 or imbalance_pct > 15:
        return {
            "decision": "MEDIUM_RISK",
            "message": "Moderate risk detected in specific categories. Recommend targeted negotiation of high-risk clauses and appropriate risk pricing in bid."
        }

    # Low Risk
    return {
        "decision": "LOW_RISK",
        "message": "Risk allocation appears generally balanced. Minor concerns can be addressed through standard negotiation. Proceed with standard pricing."
    }
