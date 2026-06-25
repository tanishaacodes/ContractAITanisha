"""
Intent Detection Engine for Infor ERP contracts.
"""
from typing import Dict, Any


class InforIntentEngine:

    def detect(self, contract: Dict[str, Any]) -> str:
        desc = (
            contract.get("description") or
            contract.get("contractDescription") or ""
        ).lower()

        if "termination" in desc:
            return "TERMINATION_SENSITIVE"
        elif "indemnity" in desc:
            return "HIGH_LIABILITY"
        elif "exclusiv" in desc:
            return "EXCLUSIVITY_RISK"
        elif "ip" in desc or "intellectual property" in desc:
            return "IP_TRANSFER"
        elif "penalty" in desc or "liquidated damages" in desc:
            return "PENALTY_RISK"
        return "STANDARD"
