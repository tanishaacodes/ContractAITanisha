"""
Risk Engine for Infor ERP contracts.
Identical scoring logic to SAP integration — same business rules, different data mapping.
"""
from typing import Dict, Any


class InforRiskEngine:

    def score(self, contract: Dict[str, Any]) -> int:
        """
        Calculate risk score (0–100) from Infor contract data.
        Infor CSI uses camelCase field names (no OData 'd' wrapper).
        """
        score = 10  # base

        # Contract value risk
        net_amount = float(contract.get("netAmount") or contract.get("totalAmount") or 0)
        if net_amount > 3_000_000:
            score += 40
        elif net_amount > 1_000_000:
            score += 25
        elif net_amount > 500_000:
            score += 15
        else:
            score += 5

        # Payment terms risk
        payment_terms = str(contract.get("paymentTerms") or "")
        if "90" in payment_terms:
            score += 20
        elif "60" in payment_terms:
            score += 10

        # Contract description risk signals
        desc = (contract.get("description") or contract.get("contractDescription") or "").upper()
        if "INDEMNITY" in desc:
            score += 25
        if "TERMINATION" in desc:
            score += 10
        if "EXCLUSIVE" in desc:
            score += 10

        # Vendor credit risk
        credit_rating = str(contract.get("vendorCreditRating") or "").upper()
        if credit_rating in ("D", "CCC"):
            score += 15
        elif credit_rating in ("B", "BB"):
            score += 8

        return min(score, 100)

    def category(self, score: int) -> str:
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 30:
            return "MEDIUM"
        return "LOW"

    def get_risk_details(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        net_amount = float(contract.get("netAmount") or 0)
        value_risk = min(40, int((net_amount / 3_000_000) * 40))
        payment_terms = str(contract.get("paymentTerms") or "")
        payment_risk = 20 if "90" in payment_terms else (10 if "60" in payment_terms else 0)

        desc = (contract.get("description") or "").upper()
        liability_risk = 25 if "INDEMNITY" in desc else 0

        credit = str(contract.get("vendorCreditRating") or "").upper()
        vendor_risk = 15 if credit in ("D", "CCC") else (8 if credit in ("B", "BB") else 0)

        return {
            "components": {
                "contract_value": value_risk,
                "payment_terms": payment_risk,
                "liability": liability_risk,
                "vendor_credit": vendor_risk,
            }
        }
