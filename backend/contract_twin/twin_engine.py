"""
Contract Twin Engine
====================
Digital twin simulation of contracts — models financial chain reactions
from real-world disruption scenarios (supplier failure, force majeure, etc.).
"""

import logging

logger = logging.getLogger(__name__)


def _parse_contract_value(contract):
    """
    Extract contract value from the Contract model.
    Priority order:
      1. contract_value field (strip currency symbols including ? as ₹)
      2. Regex scan of full_text for large monetary amounts
      3. Return 0.0 with a warning
    """
    import re

    def _clean_and_parse(raw_str):
        # Treat ? as ₹ (DB encoding issue), strip all currency symbols
        cleaned = re.sub(r'[₹$€£¥?Rs\.INR\s]', '', str(raw_str))
        cleaned = cleaned.replace(',', '').strip()
        if cleaned:
            try:
                return float(cleaned)
            except ValueError:
                pass
        return None

    # 1. Try contract_value field
    raw = getattr(contract, 'contract_value', None)
    if raw:
        val = _clean_and_parse(raw)
        if val and val > 0:
            return val

    # 2. Try extracting from full_text
    full_text = getattr(contract, 'full_text', '') or ''
    if full_text:
        # Match patterns like $15,000,000 or ₹85,00,00,000 or Rs.50,000,000
        patterns = [
            r'(?:contract\s+value|total\s+value|contract\s+sum|total\s+amount)[^\d]{0,40}([\d,]+(?:\.\d+)?)',
            r'(?:\$|₹|€|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)',
            r'\b([\d]{1,3}(?:,[\d]{2,3})+(?:\.\d+)?)\b',  # comma-separated numbers
        ]
        for pattern in patterns:
            matches = re.findall(pattern, full_text, re.I)
            for m in matches:
                val_str = m.replace(',', '')
                try:
                    val = float(val_str)
                    if val >= 10_000:  # Only use values >= 10K (realistic contract amounts)
                        return val
                except ValueError:
                    continue

    logger.warning(f"Could not extract contract value for {contract.id} — defaulting to 0")
    return 0.0


def simulate_supplier_failure(contract):
    """
    Simulate the financial chain reaction of a primary supplier failure.

    Model:
    - Revenue impact = 30% of contract value (supply disruption)
    - SLA penalty   = 10% of revenue impact (breach of delivery SLAs)
    - Insurance coverage triggered if total exposure > $100K
    - Alternative supplier flag triggered always (contingency planning)

    Args:
        contract: Django Contract model instance

    Returns:
        dict with impact breakdown
    """
    try:
        contract_value = _parse_contract_value(contract)
        revenue_impact = contract_value * 0.30
        sla_penalty = revenue_impact * 0.10
        total_exposure = revenue_impact + sla_penalty
        insurance_viability = total_exposure > 100_000

        return {
            "scenario": "supplier_failure",
            "contract_id": str(contract.id),
            "contract_title": getattr(contract, 'filename', 'Unknown'),
            "contract_value": contract_value,
            "revenue_impact": round(revenue_impact, 2),
            "sla_penalty": round(sla_penalty, 2),
            "total_exposure": round(total_exposure, 2),
            "insurance_claim": insurance_viability,
            "alternative_supplier_triggered": True,
            "recovery_timeline_days": 45,
            "risk_level": _classify_risk(total_exposure, contract_value),
            "recommendations": _get_recommendations(insurance_viability, total_exposure),
        }
    except Exception as e:
        logger.error(f"Twin simulation error for contract {contract.id}: {e}")
        return {"error": str(e), "scenario": "supplier_failure"}


def simulate_force_majeure(contract):
    """
    Simulate a force majeure event (pandemic, natural disaster, war).

    Model:
    - Revenue impact = 60% of contract value
    - SLA waiver possible (force majeure clauses)
    - Extended timeline 90-180 days
    """
    try:
        contract_value = _parse_contract_value(contract)
        revenue_impact = contract_value * 0.60
        # Check if contract has force majeure protection
        full_text = (getattr(contract, 'full_text', '') or '').lower()
        has_fm_clause = 'force majeure' in full_text or 'act of god' in full_text
        sla_waiver = has_fm_clause
        sla_penalty = 0.0 if sla_waiver else revenue_impact * 0.15

        return {
            "scenario": "force_majeure",
            "contract_id": str(contract.id),
            "contract_title": getattr(contract, 'filename', 'Unknown'),
            "contract_value": contract_value,
            "revenue_impact": round(revenue_impact, 2),
            "sla_penalty": round(sla_penalty, 2),
            "total_exposure": round(revenue_impact + sla_penalty, 2),
            "has_force_majeure_clause": has_fm_clause,
            "sla_waiver_applicable": sla_waiver,
            "recovery_timeline_days": 120,
            "risk_level": _classify_risk(revenue_impact, contract_value),
            "recommendations": [
                "Invoke force majeure clause immediately" if has_fm_clause else "Negotiate SLA waiver — no force majeure clause found",
                "Activate business continuity plan",
                "Notify all counterparties within 48 hours",
            ],
        }
    except Exception as e:
        logger.error(f"Force majeure simulation error: {e}")
        return {"error": str(e), "scenario": "force_majeure"}


def simulate_payment_default(contract):
    """
    Simulate counterparty payment default scenario.
    """
    try:
        contract_value = _parse_contract_value(contract)
        default_amount = contract_value * 0.50
        penalty_interest = default_amount * 0.18  # 18% annual
        legal_cost = default_amount * 0.05

        return {
            "scenario": "payment_default",
            "contract_id": str(contract.id),
            "contract_title": getattr(contract, 'filename', 'Unknown'),
            "contract_value": contract_value,
            "default_amount": round(default_amount, 2),
            "penalty_interest": round(penalty_interest, 2),
            "legal_recovery_cost": round(legal_cost, 2),
            "total_exposure": round(default_amount + legal_cost, 2),
            "recovery_probability": 0.72,
            "risk_level": _classify_risk(default_amount, contract_value),
            "recommendations": [
                "Initiate demand notice immediately",
                "Escalate to legal team for recovery proceedings",
                "Flag counterparty in risk registry",
            ],
        }
    except Exception as e:
        logger.error(f"Payment default simulation error: {e}")
        return {"error": str(e), "scenario": "payment_default"}


def _classify_risk(exposure, contract_value):
    """Classify risk level based on exposure as % of contract value."""
    if contract_value == 0:
        return "UNKNOWN"
    pct = (exposure / contract_value) * 100
    if pct >= 50:
        return "CRITICAL"
    elif pct >= 25:
        return "HIGH"
    elif pct >= 10:
        return "MEDIUM"
    return "LOW"


def _get_recommendations(insurance_viability, total_exposure):
    recs = [
        "Activate alternative supplier contingency plan immediately",
        "Notify procurement team of supply disruption",
    ]
    if insurance_viability:
        recs.append(f"File insurance claim — exposure ₹{total_exposure:,.0f} exceeds threshold")
    recs.append("Review SLA penalty clauses for renegotiation opportunity")
    return recs
