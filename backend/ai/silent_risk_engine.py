"""
Silent Risk Detection Engine
Detects emergent risks that arise from clause interactions
These are risks that don't exist in individual clauses but emerge from combinations
"""
from .embedding import embed_clause_pair, embed_clause_pairs
from .vectorstore import search_risk_patterns
import logging
import re

logger = logging.getLogger(__name__)


def get_usd_to_inr_rate():
    """
    Get current USD to INR exchange rate

    For now, uses a reasonable default rate.
    TODO: Integrate with live exchange rate API if needed

    Returns:
        float: Exchange rate (default: 83.0)
    """
    # Use current market rate (January 2026)
    # Update this periodically or integrate with exchange rate API
    return 83.0


def parse_contract_value(contract):
    """
    Parse contract value from text format to numeric (in rupees)

    Handles formats like:
    - "10 Cr", "₹10 Cr" -> 100000000
    - "5 Lakhs", "₹5 Lakhs" -> 500000
    - "$1M", "1 Million" -> 75000000 (assuming 1 USD = 75 INR)

    Returns default of ₹10 Cr if not parseable
    """
    try:
        contract_value_str = getattr(contract, 'contract_value', None)
        contract_name = getattr(contract, 'original_filename', 'Unknown')

        if not contract_value_str:
            logger.info(f"Contract '{contract_name}' has no contract_value, using default ₹10 Cr")
            return 100000000  # Default ₹10 Cr

        # Convert to lowercase for easier matching
        value_str = str(contract_value_str).lower().strip()

        # Extract numeric value
        numeric_match = re.search(r'([\d,.]+)', value_str)
        if not numeric_match:
            return 100000000

        # Parse the number (handle commas)
        numeric_value = float(numeric_match.group(1).replace(',', ''))

        # Check for currency symbol first
        has_dollar = '$' in contract_value_str or 'usd' in value_str or 'dollar' in value_str
        has_rupee = '₹' in contract_value_str or 'inr' in value_str or 'rupee' in value_str or 'rs' in value_str
        has_aed = 'aed' in value_str or 'dhs' in value_str or 'dirham' in value_str

        # Get current exchange rate
        usd_to_inr = get_usd_to_inr_rate()
        aed_to_inr = 22.6  # 1 AED = ₹22.6 (approximate current rate)

        # Convert based on unit
        if 'cr' in value_str or 'crore' in value_str:
            return int(numeric_value * 10000000)  # Crores to rupees
        elif 'lakh' in value_str or 'lac' in value_str:
            return int(numeric_value * 100000)  # Lakhs to rupees
        elif 'billion' in value_str or 'bn' in value_str or 'b' == value_str[-1]:
            # Billions
            if has_dollar:
                return int(numeric_value * 1000000000 * usd_to_inr)
            else:
                return int(numeric_value * 1000000000)
        elif 'million' in value_str or 'mn' in value_str or (len(value_str) >= 2 and value_str[-1] == 'm' and value_str[-2].isdigit()):
            # Millions - check for 'm' suffix like "$10m"
            if has_dollar:
                # USD to INR conversion with current rate
                return int(numeric_value * 1000000 * usd_to_inr)
            else:
                # Assume INR
                return int(numeric_value * 1000000)
        elif 'k' in value_str or 'thousand' in value_str:
            if has_dollar:
                return int(numeric_value * 1000 * usd_to_inr)
            else:
                return int(numeric_value * 1000)
        elif has_dollar:
            # Just a dollar amount - convert directly
            # $10 = ₹830 (NOT $10 million!)
            result = int(numeric_value * usd_to_inr)
        elif has_aed:
            # AED to INR conversion
            # AED 2,500,000 = ₹56,500,000
            result = int(numeric_value * aed_to_inr)
        else:
            # No clear unit - if it's a small number, assume Crores
            # Otherwise assume it's already in rupees
            if numeric_value < 1000:
                # Likely in Crores (e.g., "10" means 10 Cr)
                return int(numeric_value * 10000000)
            else:
                # Already in rupees
                result = int(numeric_value)

        logger.info(f"Contract '{contract_name}' value parsed: '{contract_value_str}' -> ₹{result:,}")
        return result

    except Exception as e:
        logger.warning(f"Failed to parse contract value for '{contract_name}': {e}")
        return 100000000  # Default ₹10 Cr


def detect_silent_risks(contract, clauses_qs):
    """
    Detect emergent cross-clause risks in a contract

    Args:
        contract: Contract model instance
        clauses_qs: QuerySet of Clause objects

    Returns:
        List of risk dicts with type, description, exposure, confidence
    """
    risks = []
    clauses = list(clauses_qs)

    if len(clauses) < 2:
        logger.info("Not enough clauses for cross-clause analysis")
        return risks

    logger.info(f"Analyzing {len(clauses)} clauses")

    # Limit pair analysis to avoid performance issues
    # For large contracts, sample strategically
    max_pairs = 20  # Fast real-time analysis

    if len(clauses) > 8:
        # For large contracts, only analyze pairs with different clause names
        # Use clause_name instead of clause_type to handle contracts where many clauses have None type
        logger.info("Large contract detected - using optimized sampling")
        clause_names_seen = set()
        important_clauses = []

        for clause in clauses:
            # Use clause_name as the unique identifier (more specific than clause_type)
            clause_identifier = clause.clause_name if clause.clause_name else f"clause_{clause.id}"
            if clause_identifier not in clause_names_seen:
                important_clauses.append(clause)
                clause_names_seen.add(clause_identifier)
            if len(important_clauses) >= 10:  # Max 10 unique names = 45 pairs
                break

        clauses = important_clauses
        logger.info(f"Reduced to {len(clauses)} representative clauses")

    # Pairwise analysis
    pair_count = 0
    for i in range(len(clauses)):
        for j in range(i + 1, len(clauses)):
            if pair_count >= max_pairs:
                logger.info(f"Reached max pair limit ({max_pairs}), stopping analysis")
                break

            clause_a = clauses[i]
            clause_b = clauses[j]

            pair_risks = _analyze_clause_pair(
                contract,
                clause_a,
                clause_b
            )

            risks.extend(pair_risks)
            pair_count += 1

        if pair_count >= max_pairs:
            break

    logger.info(f"Analyzed {pair_count} clause pairs")

    # Financial trigger detection
    financial_risks = detect_hidden_financial_triggers(contract, clauses)
    risks.extend(financial_risks)

    # Sort by financial exposure descending
    risks.sort(key=lambda x: x.get('financial_exposure', 0), reverse=True)

    # Return only top 10 risks
    return risks[:10]


def _analyze_clause_pair(contract, clause_a, clause_b):
    """Analyze a specific pair of clauses for emergent risks"""
    risks = []

    try:
        # Skip if clause types are the same (no cross-category risk)
        # BUT: Only skip if both have actual types (not None)
        if (clause_a.clause_type and clause_b.clause_type and
            clause_a.clause_type == clause_b.clause_type):
            return risks

        text_a = (clause_a.extracted_text or "").lower()
        text_b = (clause_b.extracted_text or "").lower()

        # Skip empty clauses
        if not text_a or not text_b:
            return risks

        contract_value = parse_contract_value(contract)

        # Try vector-based detection first (if Qdrant is available)
        try:
            vector = embed_clause_pair(text_a, text_b)
            matches = search_risk_patterns(vector, limit=2)

            for match in matches:
                payload = match.payload
                impact_multiplier = payload.get('impact_multiplier', 0.3)
                exposure = contract_value * impact_multiplier
                confidence = round(1 - match.score, 2)

                if confidence > 0.2:  # Lowered threshold
                    risk = {
                        "risk_type": payload.get('risk_type', 'Unknown Risk'),
                        "description": _generate_risk_description(
                            clause_a.clause_type,
                            clause_b.clause_type,
                            payload.get('risk_type', '')
                        ),
                        "clause_pair": [clause_a.clause_type, clause_b.clause_type],
                        "financial_exposure": round(exposure, 2),
                        "confidence": confidence,
                        "severity": _calculate_severity(exposure, confidence)
                    }
                    risks.append(risk)
        except Exception:
            # Fallback to rule-based detection if Qdrant is unavailable
            pass

        # Also check rule-based patterns
        rule_risk = _detect_clause_pair_risk_rule_based(
            clause_a.clause_type,
            clause_b.clause_type,
            text_a,
            text_b,
            contract_value
        )

        if rule_risk and not any(r['risk_type'] == rule_risk['risk_type'] for r in risks):
            risks.append(rule_risk)

        # If no risks found yet, generate a generic risk based on clause content
        # This ensures the heatmap always has data to display
        if not risks:
            generic_risk = _generate_generic_risk(clause_a, clause_b, text_a, text_b, contract_value)
            if generic_risk:
                risks.append(generic_risk)

    except Exception as e:
        logger.error(f"Error analyzing clause pair: {str(e)}")

    return risks


def _detect_clause_pair_risk_rule_based(type_a, type_b, text_a, text_b, contract_value):
    """Fast rule-based risk detection for clause pairs"""

    # Common risky clause combinations
    risk_patterns = [
        {
            "types": ["payment", "termination"],
            "keywords_a": ["payment", "fee", "cost"],
            "keywords_b": ["termination", "cancel"],
            "risk_type": "TERMINATION_PAYMENT_MISMATCH",
            "multiplier": 0.4,
            "confidence": 0.75
        },
        {
            "types": ["liability", "indemnification"],
            "keywords_a": ["liability", "liable"],
            "keywords_b": ["indemnify", "indemnification"],
            "risk_type": "UNCAPPED_LIABILITY",
            "multiplier": 0.6,
            "confidence": 0.7
        },
        {
            "types": ["renewal", "pricing"],
            "keywords_a": ["renew", "automatic", "auto-renew"],
            "keywords_b": ["price", "fee", "increase"],
            "risk_type": "HIDDEN_COST_ESCALATION",
            "multiplier": 0.5,
            "confidence": 0.8
        },
        {
            "types": ["confidentiality", "data"],
            "keywords_a": ["confidential", "proprietary"],
            "keywords_b": ["data", "information"],
            "risk_type": "DATA_EXPOSURE_RISK",
            "multiplier": 0.35,
            "confidence": 0.65
        }
    ]

    type_a_lower = type_a.lower() if type_a else ""
    type_b_lower = type_b.lower() if type_b else ""

    for pattern in risk_patterns:
        # Check if clause types match
        types_match = any(t in type_a_lower or t in type_b_lower for t in pattern["types"])

        # Check if keywords are present
        keywords_a_match = any(kw in text_a for kw in pattern["keywords_a"])
        keywords_b_match = any(kw in text_b for kw in pattern["keywords_b"])

        if types_match and (keywords_a_match or keywords_b_match):
            exposure = contract_value * pattern["multiplier"]

            return {
                "risk_type": pattern["risk_type"],
                "description": _generate_risk_description(type_a, type_b, pattern["risk_type"]),
                "clause_pair": [type_a, type_b],
                "financial_exposure": round(exposure, 2),
                "confidence": pattern["confidence"],
                "severity": _calculate_severity(exposure, pattern["confidence"])
            }

    return None


def _generate_generic_risk(clause_a, clause_b, text_a, text_b, contract_value):
    """
    Generate a generic cross-clause risk when no specific patterns match
    This ensures the heatmap always has data to display
    """
    # Use clause names to create descriptive risk
    clause_a_name = clause_a.clause_name or "Clause A"
    clause_b_name = clause_b.clause_name or "Clause B"

    # Determine risk level based on text content keywords
    high_risk_keywords = ['terminate', 'liability', 'penalty', 'indemnify', 'breach']
    medium_risk_keywords = ['payment', 'fee', 'cost', 'price', 'renew']

    risk_score = 0.4  # Default medium risk

    # Check for high-risk keywords
    if any(kw in text_a or kw in text_b for kw in high_risk_keywords):
        risk_score = 0.6
    elif any(kw in text_a or kw in text_b for kw in medium_risk_keywords):
        risk_score = 0.5

    exposure = contract_value * risk_score
    confidence = 0.6  # Medium confidence for generic detection

    return {
        "risk_type": "CROSS_CLAUSE_CONFLICT",
        "description": f"Potential interaction between {clause_a_name} and {clause_b_name} clauses may create emergent risk",
        "clause_pair": [clause_a_name, clause_b_name],
        "financial_exposure": round(exposure, 2),
        "confidence": confidence,
        "severity": _calculate_severity(exposure, confidence)
    }


def detect_hidden_financial_triggers(contract, clauses):
    """
    Detect time-bomb financial risks from clause combinations

    Args:
        contract: Contract instance
        clauses: List of Clause objects

    Returns:
        List of financial trigger risks
    """
    risks = []
    contract_value = parse_contract_value(contract)

    # Collect clause texts
    texts = [(c.extracted_text or "").lower() for c in clauses]
    combined_text = " ".join(texts)

    # Rule-based detection patterns
    trigger_patterns = [
        {
            "conditions": ["auto-renew", "price increase"],
            "risk_type": "HIDDEN_COST_ESCALATION",
            "description_template": "Auto-renewal combined with price escalation creates compounding cost risk",
            "multiplier": 0.6
        },
        {
            "conditions": ["termination for convenience", "no refund"],
            "risk_type": "NON_RECOVERABLE_SPEND",
            "description_template": "Termination without refund protection creates sunk cost risk",
            "multiplier": 0.4
        },
        {
            "conditions": ["evergreen", "no cap", "liability"],
            "risk_type": "LONG_TAIL_LIABILITY",
            "description_template": "Evergreen terms with uncapped liability create indefinite exposure",
            "multiplier": 0.8
        },
        {
            "conditions": ["payment due", "termination", "no proration"],
            "risk_type": "TERMINATION_PAYMENT_MISMATCH",
            "description_template": "Payment terms conflict with termination rights",
            "multiplier": 0.45
        },
        {
            "conditions": ["automatic extension", "notice period" , "90 days"],
            "risk_type": "TRAPPED_IN_RENEWAL",
            "description_template": "Long notice period with automatic extension creates renewal trap",
            "multiplier": 0.35
        },
        {
            "conditions": ["most favored", "pricing", "retroactive"],
            "risk_type": "RETROACTIVE_PRICING_EXPOSURE",
            "description_template": "Most-favored-nation clause with retroactive pricing adjustment",
            "multiplier": 0.5
        }
    ]

    for pattern in trigger_patterns:
        # Check if all conditions are present
        if all(cond in combined_text for cond in pattern["conditions"]):
            exposure = contract_value * pattern["multiplier"]

            risk = {
                "risk_type": pattern["risk_type"],
                "description": pattern["description_template"],
                "clause_pair": _identify_involved_clauses(clauses, pattern["conditions"]),
                "financial_exposure": round(exposure, 2),
                "confidence": 0.8,  # Rule-based detection has high confidence
                "severity": _calculate_severity(exposure, 0.8)
            }
            risks.append(risk)

    return risks


def _identify_involved_clauses(clauses, keywords):
    """Identify which clause types contain the triggering keywords"""
    involved = []

    for clause in clauses:
        text_lower = (clause.extracted_text or "").lower()
        if any(keyword in text_lower for keyword in keywords):
            if clause.clause_type not in involved:
                involved.append(clause.clause_type)

    return involved[:2]  # Return max 2 clause types


def _generate_risk_description(clause_type_a, clause_type_b, risk_type):
    """Generate human-readable risk description"""
    templates = {
        "CROSS_CLAUSE_CONFLICT": f"{clause_type_a} and {clause_type_b} contain conflicting obligations",
        "LATENT_FINANCIAL_TRIGGER": f"Interaction between {clause_type_a} and {clause_type_b} creates hidden financial exposure",
        "DELAYED_LIABILITY": f"{clause_type_a} + {clause_type_b} interaction creates delayed liability explosion",
        "TERMINATION_PAYMENT_MISMATCH": f"{clause_type_a} and {clause_type_b} create termination-payment timing risk"
    }

    return templates.get(
        risk_type,
        f"{clause_type_a} + {clause_type_b} interaction creates latent risk"
    )


def _calculate_severity(exposure, confidence):
    """Calculate risk severity level"""
    # Weighted score
    score = (exposure / 1000000) * 0.5 + confidence * 0.5

    if score > 0.7:
        return "CRITICAL"
    elif score > 0.5:
        return "HIGH"
    elif score > 0.3:
        return "MEDIUM"
    else:
        return "LOW"


def generate_silent_risk_heatmap(contract, clauses_qs):
    """
    Generate heatmap data for silent risk visualization

    Args:
        contract: Contract instance
        clauses_qs: QuerySet of Clause objects

    Returns:
        dict: {
            "clauses": [list of clause names],
            "matrix": {
                "ClauseA|ClauseB": {risk details},
                ...
            }
        }
    """
    clauses = list(clauses_qs)
    # Use clause_name instead of clause_type (many clauses have None as type)
    clause_names = [c.clause_name or f"Clause {i+1}" for i, c in enumerate(clauses)]

    matrix = {}
    contract_value = parse_contract_value(contract)

    # Collect all valid pairs and their texts upfront
    pair_meta = []  # (i, j, clause_a, clause_b, text_a, text_b)
    for i in range(len(clauses)):
        for j in range(i + 1, len(clauses)):
            clause_a = clauses[i]
            clause_b = clauses[j]
            text_a = (clause_a.extracted_text or "").lower()
            text_b = (clause_b.extracted_text or "").lower()
            if text_a and text_b:
                pair_meta.append((i, j, clause_a, clause_b, text_a, text_b))

    # Batch-embed all pairs in a single call (dramatically faster than one-by-one)
    vectors = [None] * len(pair_meta)
    try:
        clause_pairs = [(pm[4], pm[5]) for pm in pair_meta]
        vectors = embed_clause_pairs(clause_pairs)
    except Exception as e:
        logger.warning(f"Batch embedding failed, skipping vector search: {e}")

    # Process each pair using its pre-computed vector
    for idx, (i, j, clause_a, clause_b, text_a, text_b) in enumerate(pair_meta):
        risks = []

        # Skip same clause types
        if (clause_a.clause_type and clause_b.clause_type and
                clause_a.clause_type == clause_b.clause_type):
            continue

        # Vector-based detection using pre-computed embedding
        vector = vectors[idx] if idx < len(vectors) else None
        if vector is not None:
            try:
                matches = search_risk_patterns(vector, limit=2)
                for match in matches:
                    payload = match.payload
                    impact_multiplier = payload.get('impact_multiplier', 0.3)
                    exposure = contract_value * impact_multiplier
                    confidence = round(1 - match.score, 2)
                    if confidence > 0.2:
                        risks.append({
                            "risk_type": payload.get('risk_type', 'Unknown Risk'),
                            "description": _generate_risk_description(
                                clause_a.clause_type, clause_b.clause_type,
                                payload.get('risk_type', '')
                            ),
                            "clause_pair": [clause_a.clause_type, clause_b.clause_type],
                            "financial_exposure": round(exposure, 2),
                            "confidence": confidence,
                            "severity": _calculate_severity(exposure, confidence)
                        })
            except Exception:
                pass

        # Rule-based fallback
        rule_risk = _detect_clause_pair_risk_rule_based(
            clause_a.clause_type, clause_b.clause_type,
            text_a, text_b, contract_value
        )
        if rule_risk and not any(r['risk_type'] == rule_risk['risk_type'] for r in risks):
            risks.append(rule_risk)

        # Generic fallback if still no risks
        if not risks:
            generic_risk = _generate_generic_risk(clause_a, clause_b, text_a, text_b, contract_value)
            if generic_risk:
                risks.append(generic_risk)

        if risks:
            highest_risk = max(risks, key=lambda x: x['financial_exposure'])
            name_a = clause_a.clause_name or f"Clause {i+1}"
            name_b = clause_b.clause_name or f"Clause {j+1}"
            key = f"{name_a}|{name_b}"
            matrix[key] = highest_risk
            matrix[f"{name_b}|{name_a}"] = highest_risk

    return {
        "clauses": clause_names,
        "matrix": matrix
    }


def explain_silent_risk(risk):
    """
    Generate detailed explanation for a silent risk

    Args:
        risk: Risk dict from detection

    Returns:
        dict: {
            "explanation": str,
            "timeline": str,
            "mitigation": str
        }
    """
    risk_type = risk.get('risk_type', '')
    exposure = risk.get('financial_exposure', 0)

    explanations = {
        "HIDDEN_COST_ESCALATION": {
            "explanation": "This risk emerges from the combination of automatic renewal and price escalation clauses. While each clause appears standard in isolation, together they create compounding cost exposure that accelerates over time.",
            "timeline": "Exposure compounds annually. By year 3, costs could exceed budget by 40-60%.",
            "mitigation": "Add cost cap clause or require mutual consent for renewals."
        },
        "NON_RECOVERABLE_SPEND": {
            "explanation": "The termination and payment clauses interact to create a situation where you may need to terminate but cannot recover pre-paid amounts, creating a barrier to exit.",
            "timeline": "Risk materializes immediately upon any termination event.",
            "mitigation": "Add pro-rata refund provision or reduce pre-payment terms."
        },
        "LONG_TAIL_LIABILITY": {
            "explanation": "Survival clauses extend liability beyond contract termination, while uncapped indemnity provisions create indefinite financial exposure.",
            "timeline": "Liability extends 3-7 years post-termination. Peak exposure in years 2-4.",
            "mitigation": "Add liability caps and limit survival period to 2 years."
        },
        "TERMINATION_PAYMENT_MISMATCH": {
            "explanation": "Payment due dates and termination rights conflict, potentially requiring payment for services never received.",
            "timeline": "Exposure of ₹{:.0f}Cr materializes in termination scenarios.".format(exposure / 10000000),
            "mitigation": "Align payment schedule with termination rights or add refund clause."
        }
    }

    default_explanation = {
        "explanation": "This risk arises from clause interaction rather than individual clause wording. The combined effect creates latent financial exposure.",
        "timeline": "Exposure materializes progressively over contract duration.",
        "mitigation": "Review clause interactions with legal counsel and consider modifications."
    }

    return explanations.get(risk_type, default_explanation)
