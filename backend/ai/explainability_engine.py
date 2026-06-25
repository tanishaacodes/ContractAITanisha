"""
Enhanced Explainability Engine
Provides clear "Why → Impact → Suggestion" chains for risk decisions.

Based on Prof. Murali's research: Users need to understand not just THAT
a clause is risky, but WHY it's risky, WHAT the business impact is, and
HOW to fix it.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class ImpactChain:
    """Complete explanation chain for a risk finding"""
    clause_text: str
    category: str
    risk_score: float

    # WHY is this risky?
    risk_rationale: str
    detected_patterns: List[str]

    # WHAT is the business impact?
    business_impact: str
    financial_exposure_range: str
    probability: str  # "HIGH" | "MEDIUM" | "LOW"

    # HOW to fix it?
    negotiation_strategy: str
    fallback_position: str
    deal_breaker: bool

def generate_impact_chain(
    clause_text: str,
    category: str,
    risk_score: float,
    imbalance_severity: str,
    imbalance_explanation: str,
    financial_exposure: Dict[str, float],
    contract_value: float = None
) -> ImpactChain:
    """
    Generate complete explainability chain for a clause.

    Args:
        clause_text: The actual clause text
        category: Risk category
        risk_score: 0.0 to 1.0
        imbalance_severity: From risk_allocation_map
        imbalance_explanation: From risk_allocation_map
        financial_exposure: From calculate_financial_exposure
        contract_value: Optional contract value for context

    Returns:
        ImpactChain with complete explanation
    """

    # Extract detected patterns
    detected_patterns = _extract_risk_patterns(clause_text, category)

    # Generate risk rationale (WHY)
    risk_rationale = _generate_risk_rationale(
        category, risk_score, imbalance_severity, detected_patterns, imbalance_explanation
    )

    # Generate business impact (WHAT)
    business_impact = _generate_business_impact(
        category, risk_score, financial_exposure, contract_value
    )

    # Determine probability
    probability = _calculate_probability(category, risk_score, imbalance_severity)

    # Format financial exposure
    if financial_exposure:
        min_exp = financial_exposure.get("minimum_exposure", 0)
        max_exp = financial_exposure.get("maximum_exposure", 0)
        financial_exposure_range = f"${min_exp:,.0f} - ${max_exp:,.0f}"
    else:
        financial_exposure_range = "Unable to estimate without contract value"

    # Generate negotiation strategy (HOW)
    negotiation_strategy, fallback_position, deal_breaker = _generate_negotiation_strategy(
        category, risk_score, imbalance_severity
    )

    return ImpactChain(
        clause_text=clause_text,
        category=category,
        risk_score=risk_score,
        risk_rationale=risk_rationale,
        detected_patterns=detected_patterns,
        business_impact=business_impact,
        financial_exposure_range=financial_exposure_range,
        probability=probability,
        negotiation_strategy=negotiation_strategy,
        fallback_position=fallback_position,
        deal_breaker=deal_breaker
    )

def _extract_risk_patterns(clause_text: str, category: str) -> List[str]:
    """Extract specific risk patterns detected in the clause"""
    clause_lower = clause_text.lower()
    patterns = []

    # Common high-risk patterns across categories
    pattern_map = {
        "unlimited": "Unlimited liability exposure",
        "sole discretion": "Unilateral decision-making power",
        "no liability": "Complete liability waiver",
        "waives": "Rights waiver",
        "regardless of": "No exceptions provision",
        "hold harmless": "Indemnification obligation",
        "no right": "Rights elimination",
        "no compensation": "No financial relief",
        "no extension": "No time relief",
        "all risk": "Complete risk transfer",
        "at all times": "Perpetual obligation",
        "without limitation": "Uncapped obligation",
        "solely responsible": "Sole responsibility assignment"
    }

    for keyword, description in pattern_map.items():
        if keyword in clause_lower:
            patterns.append(description)

    return patterns if patterns else ["Standard risk allocation language"]

def _generate_risk_rationale(
    category: str,
    risk_score: float,
    imbalance_severity: str,
    detected_patterns: List[str],
    imbalance_explanation: str
) -> str:
    """Generate WHY explanation"""

    rationale = f"**Why This is Risky (Score: {risk_score:.0%}):**\n\n"

    # Add severity context
    if imbalance_severity in ["EXTREME", "HIGH"]:
        rationale += f"⚠️ This clause shows **{imbalance_severity}** risk imbalance.\n\n"

    # Add detected patterns
    if detected_patterns and detected_patterns != ["Standard risk allocation language"]:
        rationale += "**Red Flag Patterns Detected:**\n"
        for pattern in detected_patterns:
            rationale += f"- {pattern}\n"
        rationale += "\n"

    # Add allocation explanation
    rationale += f"**Risk Allocation Analysis:**\n{imbalance_explanation}\n"

    return rationale

def _generate_business_impact(
    category: str,
    risk_score: float,
    financial_exposure: Dict[str, float],
    contract_value: float = None
) -> str:
    """Generate WHAT (business impact) explanation"""

    impact = "**Business Impact:**\n\n"

    # Category-specific impacts
    impact_scenarios = {
        "FORCE_MAJEURE": "During pandemic, war, or natural disaster, you must continue work and pay delay penalties despite impossible conditions. Your company absorbs 100% of force majeure costs.",

        "SITE_CONDITIONS": "If subsurface conditions differ from drawings (rock, water, contamination), you pay for all remediation and redesign despite owner controlling the site and having better geological information.",

        "DESIGN_DEFECTS": "When owner's engineer makes calculation errors, you're liable for rebuilding. You pay for fixing design mistakes you didn't make and couldn't verify during bidding.",

        "DELAY_OWNER_CAUSED": "Owner delays payments/approvals, but you still pay liquidated damages. Your critical path is disrupted, costs escalate, yet you have no time relief or compensation.",

        "INDEMNITY_SCOPE": "If owner's negligence causes injury on site, you pay unlimited legal costs and damages from your company assets. Even if owner is 100% at fault, you indemnify them.",

        "PAYMENT_WITHHOLDING": "Owner withholds payment indefinitely at their discretion, with no interest. Your subcontractors demand payment, but your cashflow is blocked by owner's arbitrary decision.",

        "VARIATION_ORDERS": "Owner orders major scope changes. You must execute immediately without any price or time adjustment. Your resources are diverted, schedule disrupted, costs escalate, but contract price stays fixed.",

        "WARRANTY_PERIOD": "You provide 10-year warranty covering even design defects and owner's misuse. Long after project completion, you're liable for repairs you didn't cause and can't predict.",

        "STATUTORY_APPROVALS": "Government delays environmental clearance for owner's project. You pay delay penalties and overhead costs despite having no control over approval process or government relations.",

        "TERMINATION_RIGHTS": "Mid-project, owner terminates for convenience. You lose expected profits, pay demobilization costs, and have no recovery for business disruption or lost opportunities.",

        "INSURANCE_LIABILITY": "Catastrophic incident exceeds insurance coverage. You're personally liable for excess, potentially bankrupting your company for risks that should have been capped at insurable limits.",

        "DISPUTE_RESOLUTION": "In disputes, owner selects the arbitrator and you have no judicial review. The process is biased from the start, making fair resolution nearly impossible."
    }

    impact += impact_scenarios.get(category, "This clause creates unfair risk allocation that may lead to financial losses and disputes.")
    impact += "\n\n"

    # Add financial context
    if financial_exposure:
        likely = financial_exposure.get("likely_exposure", 0)
        maximum = financial_exposure.get("maximum_exposure", 0)
        percentage = financial_exposure.get("exposure_percentage", 0)

        impact += f"**Estimated Financial Exposure:**\n"
        impact += f"- Likely scenario: ${likely:,.0f}\n"
        impact += f"- Worst case: ${maximum:,.0f}\n"
        impact += f"- Risk as % of contract: {percentage:.1f}%\n"

        if contract_value:
            impact += f"- Contract value: ${contract_value:,.0f}\n"

    return impact

def _calculate_probability(category: str, risk_score: float, imbalance_severity: str) -> str:
    """Estimate probability of risk materializing"""

    # Category-based likelihood
    likelihood_map = {
        "FORCE_MAJEURE": "MEDIUM",  # Rare but catastrophic
        "SITE_CONDITIONS": "HIGH",   # Very common in construction
        "DESIGN_DEFECTS": "MEDIUM",  # Common but varying severity
        "DELAY_OWNER_CAUSED": "HIGH", # Very common
        "INDEMNITY_SCOPE": "MEDIUM",  # Depends on site safety
        "PAYMENT_WITHHOLDING": "HIGH", # Common cashflow tactic
        "VARIATION_ORDERS": "HIGH",   # Standard in construction
        "WARRANTY_PERIOD": "MEDIUM",  # Long-tail risk
        "STATUTORY_APPROVALS": "MEDIUM", # Project-dependent
        "TERMINATION_RIGHTS": "LOW",   # Usually avoided
        "INSURANCE_LIABILITY": "LOW",   # Catastrophic but rare
        "DISPUTE_RESOLUTION": "MEDIUM"  # Depends on relationship
    }

    base_probability = likelihood_map.get(category, "MEDIUM")

    # Adjust based on severity
    if imbalance_severity == "EXTREME" and base_probability == "MEDIUM":
        return "HIGH"
    elif imbalance_severity in ["LOW", "BALANCED"]:
        return "LOW"

    return base_probability

def _generate_negotiation_strategy(
    category: str,
    risk_score: float,
    imbalance_severity: str
) -> Tuple[str, str, bool]:
    """
    Generate HOW (negotiation strategy) explanation.

    Returns:
        (negotiation_strategy, fallback_position, deal_breaker)
    """

    # Category-specific negotiation strategies
    strategies = {
        "FORCE_MAJEURE": (
            "**Negotiation Strategy:**\n"
            "1. Request time extension (no cost) for force majeure events\n"
            "2. Suspend liquidated damages during force majeure\n"
            "3. Add pandemic/epidemic to force majeure list\n"
            "4. Include 'best efforts to mitigate' language\n\n"
            "**Key Argument:** Neither party controls acts of God. FIDIC provides time relief as standard. This is market practice.",

            "**Fallback:** Accept cost risk but insist on time extension and LD suspension during uncontrollable events.",

            True  # Deal breaker for extreme FM clauses
        ),

        "SITE_CONDITIONS": (
            "**Negotiation Strategy:**\n"
            "1. Request owner liability for unforeseen subsurface conditions\n"
            "2. Add 'Differing Site Conditions' clause with price/time adjustment\n"
            "3. Require owner to provide geological survey reports\n"
            "4. Limit contractor's site investigation obligation\n\n"
            "**Key Argument:** Owner owns land and has better geological information. Contractor cannot X-ray the ground during bidding.",

            "**Fallback:** Accept surface conditions risk but insist on subsurface conditions relief (e.g., rock, water table, contamination).",

            True  # Deal breaker - subsurface is unquantifiable
        ),

        "INDEMNITY_SCOPE": (
            "**Negotiation Strategy:**\n"
            "1. Request mutual indemnity (each party for own negligence)\n"
            "2. Cap indemnity at insurance coverage limits\n"
            "3. Exclude indemnity for owner's sole negligence\n"
            "4. Add proportional liability based on fault percentage\n\n"
            "**Key Argument:** No contractor can get insurance for unlimited indemnity of owner's negligence. This makes the risk uninsurable.",

            "**Fallback:** Accept indemnity for contractor's negligence only, capped at 1x contract value or insurance limit, whichever is less.",

            True  # Deal breaker - unlimited liability can bankrupt company
        ),

        "PAYMENT_WITHHOLDING": (
            "**Negotiation Strategy:**\n"
            "1. Limit withholding to specific itemized defects only\n"
            "2. Add interest on delayed payments (e.g., 2% per month)\n"
            "3. Require payment within fixed terms (e.g., 30 days)\n"
            "4. Continue payment of undisputed amounts during disputes\n\n"
            "**Key Argument:** Arbitrary withholding creates cashflow crisis. Your subcontractors won't wait unpaid. Interest compensates for financial cost.",

            "**Fallback:** Accept withholding up to 5-10% retention only, released within 60 days of completion with interest on delays.",

            False  # Negotiable - can be managed with interest
        ),

        "VARIATION_ORDERS": (
            "**Negotiation Strategy:**\n"
            "1. Request price and time adjustment for all variations\n"
            "2. Add variation approval procedure with written quotation\n"
            "3. Right to disagree with valuation (goes to dispute resolution)\n"
            "4. Suspend work on variation if price not agreed\n\n"
            "**Key Argument:** Variations disrupt schedule and add cost. Fair valuation is standard in all construction contracts (FIDIC, AIA, JCT).",

            "**Fallback:** Accept small variations (<5% contract value) without adjustment, but insist on fair valuation for major changes.",

            False  # Negotiable - but critical for large projects
        ),

        "WARRANTY_PERIOD": (
            "**Negotiation Strategy:**\n"
            "1. Limit warranty to 1-2 years for workmanship defects only\n"
            "2. Exclude design defects, owner's misuse, and normal wear\n"
            "3. Exclude consequential damages (only repair/replace)\n"
            "4. Cap warranty liability at contract value\n\n"
            "**Key Argument:** 10-year warranty is commercially unreasonable. Insurance doesn't cover it. Standard is 1-2 years for construction defects.",

            "**Fallback:** Accept 5-year warranty for structural defects only, 1-year for finishes/MEP, exclude design and misuse.",

            False  # Negotiable - can be insured with proper limits
        ),

        "DELAY_OWNER_CAUSED": (
            "**Negotiation Strategy:**\n"
            "1. Add time extension for owner-caused delays (payment delays, approval delays, design changes)\n"
            "2. Suspend liquidated damages during owner delays\n"
            "3. Add compensation for prolongation costs (overhead, equipment idle time)\n"
            "4. Define 'excusable delay' clearly in contract\n\n"
            "**Key Argument:** You cannot control owner's approval process or payment delays. Paying penalties for owner's delays violates basic fairness.",

            "**Fallback:** Accept no cost compensation but insist on time extension and LD suspension during owner-caused delays.",

            True  # Deal breaker - paying penalties for others' delays is commercially impossible
        ),

        "TERMINATION_RIGHTS": (
            "**Negotiation Strategy:**\n"
            "1. Require reasonable notice period (e.g., 30 days)\n"
            "2. Payment for work done plus profit on work completed\n"
            "3. Reimbursement of demobilization costs\n"
            "4. Add termination rights for contractor if owner breaches (payment default)\n\n"
            "**Key Argument:** Convenience termination is owner's right, but contractor should be made whole for work done and disruption costs.",

            "**Fallback:** Accept termination right but insist on payment for work done plus 50% profit on work done (not full contract profit).",

            False  # Negotiable - commercial terms can mitigate
        )
    }

    # Default strategy for unmapped categories
    default_strategy = (
        "**Negotiation Strategy:**\n"
        "1. Request balanced risk allocation per FIDIC/industry standards\n"
        "2. Add mutual obligations and rights\n"
        "3. Cap liabilities at reasonable commercial limits\n"
        "4. Include dispute resolution for disagreements\n\n"
        "**Key Argument:** Fair risk allocation per international construction standards is in both parties' interest for project success.",

        "**Fallback:** Seek compromise that shares risk between parties based on control and capability.",

        False
    )

    strategy_data = strategies.get(category, default_strategy)

    # Adjust deal-breaker based on severity
    deal_breaker = strategy_data[2]
    if imbalance_severity == "EXTREME":
        deal_breaker = True

    return strategy_data[0], strategy_data[1], deal_breaker

def format_impact_chain_for_display(chain: ImpactChain) -> str:
    """Format impact chain for frontend display"""

    output = f"# Risk Analysis: {chain.category}\n\n"
    output += f"**Risk Score:** {chain.risk_score:.0%}\n\n"
    output += "---\n\n"

    # WHY section
    output += chain.risk_rationale
    output += "\n---\n\n"

    # WHAT section
    output += chain.business_impact
    output += "\n---\n\n"

    # HOW section
    output += chain.negotiation_strategy
    output += "\n\n"
    output += f"**Fallback Position:**\n{chain.fallback_position}\n\n"

    if chain.deal_breaker:
        output += "⛔ **DEAL BREAKER:** This risk is severe enough to consider walking away if owner refuses to negotiate.\n\n"

    # Probability and exposure summary
    output += "---\n\n"
    output += "## Risk Summary\n\n"
    output += f"- **Probability:** {chain.probability}\n"
    output += f"- **Financial Exposure:** {chain.financial_exposure_range}\n"
    output += f"- **Deal Breaker:** {'Yes - Consider walking away' if chain.deal_breaker else 'No - Negotiable with fallbacks'}\n"

    return output
