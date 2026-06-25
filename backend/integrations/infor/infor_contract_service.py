"""
Infor ERP Contract Service

Orchestrates all 5 bi-directional integration scenarios between
PrimeContractAI and Infor ERP LN / CloudSuite Industrial.
"""
import logging
from typing import Dict, Any
from datetime import datetime

from .infor_client import InforClient, InforAPIError
from .risk_engine import InforRiskEngine
from .intent_engine import InforIntentEngine
from .clause_engine import InforClauseEngine
from .config import settings

logger = logging.getLogger(__name__)


class InforContractService:
    """
    Main service orchestrating Infor ERP ↔ PrimeContractAI integration.

    Implements 5 core scenarios (mirrors SAP integration):
    1. New Contract Processing
    2. High-Risk Contract Blocking
    3. Amendment Re-evaluation
    4. Manual Override Processing
    5. AI Clause Suggestions
    """

    def __init__(self):
        self.infor_client = InforClient()
        self.risk_engine = InforRiskEngine()
        self.intent_engine = InforIntentEngine()
        self.clause_engine = InforClauseEngine()

    async def __aenter__(self):
        await self.infor_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.infor_client.__aexit__(exc_type, exc_val, exc_tb)

    # ─────────────────────────────────────────────────────────────────
    # SCENARIO 1: NEW CONTRACT PROCESSING
    # ─────────────────────────────────────────────────────────────────
    async def process_new_contract(self, contract_id: str) -> Dict[str, Any]:
        """
        Scenario 1: Infor → AI → Infor
        Read contract, score risk, detect intent, update Infor UDFs.
        """
        logger.info(f"[INFOR S1] Processing new contract {contract_id}")

        contract = await self.infor_client.read_contract(contract_id)

        risk_score = self.risk_engine.score(contract)
        risk_category = self.risk_engine.category(risk_score)
        intent = self.intent_engine.detect(contract)
        exposure = float(contract.get("netAmount") or contract.get("totalAmount") or 0)

        if risk_score < settings.RISK_THRESHOLD_MEDIUM:
            ai_status = "APPROVED"
        elif risk_score < settings.RISK_THRESHOLD_HIGH:
            ai_status = "REVIEW_REQUIRED"
        else:
            ai_status = "BLOCKED"

        await self.infor_client.update_contract(contract_id, {
            settings.UDF_RISK_SCORE: risk_score,
            settings.UDF_RISK_CATEGORY: risk_category,
            settings.UDF_INTENT: intent,
            settings.UDF_STATUS: ai_status,
            settings.UDF_EXPOSURE: exposure,
            settings.UDF_VALIDATED_DATE: datetime.now().isoformat(),
            settings.UDF_COMPLIANCE: "PENDING",
        })

        logger.info(f"[INFOR S1] {contract_id} → Risk={risk_score}, Status={ai_status}")
        return {
            "scenario": 1,
            "erp": "infor",
            "contract_id": contract_id,
            "risk_score": risk_score,
            "risk_category": risk_category,
            "intent": intent,
            "status": ai_status,
            "exposure": exposure,
            "message": f"Contract processed with {ai_status} status",
        }

    # ─────────────────────────────────────────────────────────────────
    # SCENARIO 2: HIGH-RISK BLOCKING
    # ─────────────────────────────────────────────────────────────────
    async def block_high_risk_contract(self, contract_id: str) -> Dict[str, Any]:
        """
        Scenario 2: AI → Infor
        If risk > CRITICAL threshold, set aiStatus = BLOCKED and add note.
        """
        logger.info(f"[INFOR S2] Evaluating {contract_id} for blocking")

        contract = await self.infor_client.read_contract(contract_id)
        risk_score = self.risk_engine.score(contract)
        risk_details = self.risk_engine.get_risk_details(contract)

        if risk_score > settings.RISK_THRESHOLD_CRITICAL:
            await self.infor_client.update_contract(contract_id, {
                settings.UDF_STATUS: "BLOCKED",
                settings.UDF_RISK_SCORE: risk_score,
                settings.UDF_RISK_CATEGORY: "CRITICAL",
            })

            note = (
                f"CONTRACT BLOCKED BY AI RISK ENGINE\n\n"
                f"Risk Score: {risk_score}/100 (CRITICAL)\n\n"
                f"Risk Breakdown:\n"
                f"- Contract Value Risk: {risk_details['components']['contract_value']}\n"
                f"- Payment Terms Risk:  {risk_details['components']['payment_terms']}\n"
                f"- Liability Risk:      {risk_details['components']['liability']}\n"
                f"- Vendor Credit Risk:  {risk_details['components']['vendor_credit']}\n\n"
                f"ACTION REQUIRED: Legal review mandatory before proceeding.\n"
                f"Blocked on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await self.infor_client.add_note(contract_id, note)

            logger.warning(f"[INFOR S2] {contract_id} BLOCKED (score={risk_score})")
            return {
                "scenario": 2, "erp": "infor", "contract_id": contract_id,
                "blocked": True, "risk_score": risk_score,
                "message": f"Contract blocked due to critical risk (score: {risk_score})",
            }

        return {
            "scenario": 2, "erp": "infor", "contract_id": contract_id,
            "blocked": False, "risk_score": risk_score,
            "message": "Contract risk within acceptable limits",
        }

    # ─────────────────────────────────────────────────────────────────
    # SCENARIO 3: AMENDMENT RE-EVALUATION
    # ─────────────────────────────────────────────────────────────────
    async def process_amendment(self, contract_id: str) -> Dict[str, Any]:
        """
        Scenario 3: Infor → AI → Infor
        Re-score amended contract, flag if risk delta > 20 pts.
        """
        logger.info(f"[INFOR S3] Processing amendment for {contract_id}")

        contract = await self.infor_client.read_contract(contract_id)
        previous_risk = float(contract.get(settings.UDF_RISK_SCORE) or 0)

        new_risk_score = self.risk_engine.score(contract)
        new_risk_category = self.risk_engine.category(new_risk_score)
        intent = self.intent_engine.detect(contract)
        risk_delta = new_risk_score - previous_risk

        if new_risk_score < settings.RISK_THRESHOLD_MEDIUM:
            status = "APPROVED"
        elif new_risk_score < settings.RISK_THRESHOLD_HIGH:
            status = "REVIEW_REQUIRED"
        else:
            status = "BLOCKED"

        await self.infor_client.update_contract(contract_id, {
            settings.UDF_RISK_SCORE: new_risk_score,
            settings.UDF_RISK_CATEGORY: new_risk_category,
            settings.UDF_INTENT: intent,
            settings.UDF_STATUS: status,
            settings.UDF_VALIDATED_DATE: datetime.now().isoformat(),
        })

        if risk_delta > 20:
            note = (
                f"AMENDMENT ALERT: Risk Increased\n\n"
                f"Previous Risk: {previous_risk}\n"
                f"New Risk:      {new_risk_score}\n"
                f"Delta:         +{risk_delta}\n\n"
                f"Status: {status}\n"
                f"Re-evaluation: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await self.infor_client.add_note(contract_id, note)

        logger.info(f"[INFOR S3] {contract_id} re-evaluated: {previous_risk} → {new_risk_score}")
        return {
            "scenario": 3, "erp": "infor", "contract_id": contract_id,
            "previous_risk": previous_risk, "new_risk_score": new_risk_score,
            "risk_delta": risk_delta, "risk_increased": risk_delta > 0,
            "status": status, "message": "Amendment re-evaluation complete",
        }

    # ─────────────────────────────────────────────────────────────────
    # SCENARIO 4: MANUAL OVERRIDE
    # ─────────────────────────────────────────────────────────────────
    async def process_manual_override(self, contract_id: str) -> Dict[str, Any]:
        """
        Scenario 4: Infor → AI → Infor
        Check manualOverride UDF; if set, mark MANUALLY_APPROVED and log.
        """
        logger.info(f"[INFOR S4] Processing manual override for {contract_id}")

        contract = await self.infor_client.read_contract(contract_id)
        override_flag = contract.get("manualOverride") or contract.get("aiManualOverride", False)
        override_user = contract.get("overrideUser") or contract.get("aiOverrideUser", "Unknown")

        if override_flag:
            await self.infor_client.update_contract(contract_id, {
                settings.UDF_STATUS: "MANUALLY_APPROVED",
                settings.UDF_VALIDATED_DATE: datetime.now().isoformat(),
            })

            note = (
                f"MANUAL OVERRIDE APPLIED\n\n"
                f"Override by: {override_user}\n"
                f"Override date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Original AI Status: {contract.get(settings.UDF_STATUS, 'Unknown')}\n"
                f"Original Risk Score: {contract.get(settings.UDF_RISK_SCORE, 'Unknown')}\n\n"
                f"User has manually approved this contract overriding AI recommendation."
            )
            await self.infor_client.add_note(contract_id, note)

            logger.warning(f"[INFOR S4] Override processed for {contract_id} by {override_user}")
            return {
                "scenario": 4, "erp": "infor", "contract_id": contract_id,
                "override_applied": True, "override_user": override_user,
                "message": "Manual override processed successfully",
            }

        return {
            "scenario": 4, "erp": "infor", "contract_id": contract_id,
            "override_applied": False,
            "message": "No manual override flag found in Infor contract",
        }

    # ─────────────────────────────────────────────────────────────────
    # SCENARIO 5: AI CLAUSE SUGGESTIONS
    # ─────────────────────────────────────────────────────────────────
    async def add_clause_suggestions(self, contract_id: str) -> Dict[str, Any]:
        """
        Scenario 5: AI → Infor
        Generate clause improvement suggestions, attach as Infor note.
        """
        logger.info(f"[INFOR S5] Generating clause suggestions for {contract_id}")

        contract = await self.infor_client.read_contract(contract_id)
        risk_score = self.risk_engine.score(contract)
        suggestions = self.clause_engine.suggest(contract, risk_score)
        note_text = self.clause_engine.generate_note(contract, suggestions)

        await self.infor_client.add_note(contract_id, note_text)
        await self.infor_client.update_contract(contract_id, {
            "aiSuggestionsAdded": True,
            settings.UDF_VALIDATED_DATE: datetime.now().isoformat(),
        })

        logger.info(f"[INFOR S5] {len(suggestions)} suggestions added to {contract_id}")
        return {
            "scenario": 5, "erp": "infor", "contract_id": contract_id,
            "suggestions_count": len(suggestions),
            "suggestions": suggestions,
            "risk_score": risk_score,
            "message": "Clause suggestions added to Infor contract",
        }
