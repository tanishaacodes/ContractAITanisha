"""
SAP Contract Service

Orchestrates all 5 bi-directional integration scenarios between
PrimeContractAI and SAP S/4HANA.
"""
import logging
from typing import Dict, Any
from datetime import datetime

from .sap_client import SAPClient, SAPAPIError
from .risk_engine import RiskEngine
from .intent_engine import IntentEngine
from .clause_engine import ClauseEngine
from .config import settings

logger = logging.getLogger(__name__)


class SAPContractService:
    """
    Main service orchestrating SAP ↔ PrimeContractAI integration

    Implements 5 core scenarios:
    1. New Contract Processing (SAP → AI → SAP)
    2. High-Risk Contract Blocking (AI → SAP)
    3. Amendment Re-evaluation (SAP → AI → SAP)
    4. Manual Override Processing (SAP → AI → SAP)
    5. AI Clause Suggestions (AI → SAP)
    """

    def __init__(self):
        self.sap_client = SAPClient()
        self.risk_engine = RiskEngine()
        self.intent_engine = IntentEngine()
        self.clause_engine = ClauseEngine()

    async def __aenter__(self):
        """Async context manager entry"""
        await self.sap_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.sap_client.__aexit__(exc_type, exc_val, exc_tb)

    # ========================================
    # SCENARIO 1: NEW CONTRACT PROCESSING
    # ========================================
    async def process_new_contract(self, contract_id: str) -> Dict[str, Any]:
        """
        Scenario 1: Process a newly created contract from SAP

        Flow:
        1. Read contract from SAP
        2. Perform risk scoring
        3. Detect intent
        4. Determine approval status
        5. Update SAP with AI results

        Args:
            contract_id: SAP contract number

        Returns:
            Processing result with risk score, status, etc.
        """
        try:
            logger.info(f"[SCENARIO 1] Processing new contract {contract_id}")

            # Step 1: Read contract from SAP
            contract = await self.sap_client.read_contract(contract_id)

            # Step 2: Risk analysis
            risk_score = self.risk_engine.score(contract)
            risk_category = self.risk_engine.category(risk_score)

            # Step 3: Intent detection
            intent = self.intent_engine.detect(contract)

            # Step 4: Determine AI status
            if risk_score < settings.RISK_THRESHOLD_MEDIUM:
                ai_status = "APPROVED"
            elif risk_score < settings.RISK_THRESHOLD_HIGH:
                ai_status = "REVIEW_REQUIRED"
            else:
                ai_status = "BLOCKED"

            # Step 5: Calculate financial exposure
            exposure = self._calculate_exposure(contract)

            # Step 6: Update SAP with AI results
            update_payload = {
                settings.Z_FIELD_RISK_SCORE: risk_score,
                settings.Z_FIELD_RISK_CATEGORY: risk_category,
                settings.Z_FIELD_INTENT: intent,
                settings.Z_FIELD_STATUS: ai_status,
                settings.Z_FIELD_EXPOSURE: exposure,
                settings.Z_FIELD_VALIDATED_DATE: datetime.now().isoformat(),
                settings.Z_FIELD_COMPLIANCE: "PENDING"
            }

            await self.sap_client.update_contract(contract_id, update_payload)

            logger.info(
                f"[SCENARIO 1] Contract {contract_id} processed: "
                f"Risk={risk_score}, Status={ai_status}"
            )

            return {
                "scenario": 1,
                "contract_id": contract_id,
                "risk_score": risk_score,
                "risk_category": risk_category,
                "intent": intent,
                "status": ai_status,
                "exposure": exposure,
                "message": f"Contract processed with {ai_status} status"
            }

        except SAPAPIError as e:
            logger.error(f"[SCENARIO 1] SAP API error: {e}")
            raise
        except Exception as e:
            logger.error(f"[SCENARIO 1] Processing error: {e}")
            raise

    # ========================================
    # SCENARIO 2: HIGH-RISK CONTRACT BLOCKING
    # ========================================
    async def block_high_risk_contract(self, contract_id: str) -> Dict[str, Any]:
        """
        Scenario 2: Automatically block high-risk contracts in SAP

        Flow:
        1. Read contract from SAP
        2. Calculate risk score
        3. If risk > threshold, BLOCK contract in SAP
        4. Add blocking reason note

        Args:
            contract_id: SAP contract number

        Returns:
            Blocking result
        """
        try:
            logger.info(f"[SCENARIO 2] Evaluating contract {contract_id} for blocking")

            # Read contract
            contract = await self.sap_client.read_contract(contract_id)

            # Risk analysis
            risk_score = self.risk_engine.score(contract)
            risk_details = self.risk_engine.get_risk_details(contract)

            # Block if risk exceeds threshold
            if risk_score > settings.RISK_THRESHOLD_HIGH:
                # Update SAP status to BLOCKED
                update_payload = {
                    settings.Z_FIELD_STATUS: "BLOCKED",
                    settings.Z_FIELD_RISK_SCORE: risk_score,
                    settings.Z_FIELD_RISK_CATEGORY: "CRITICAL"
                }

                await self.sap_client.update_contract(contract_id, update_payload)

                # Add blocking reason as note
                blocking_note = f"""
CONTRACT BLOCKED BY AI RISK ENGINE

Risk Score: {risk_score}/100 (CRITICAL)

Risk Breakdown:
- Contract Value Risk: {risk_details['components']['contract_value']}
- Payment Terms Risk: {risk_details['components']['payment_terms']}
- Liability Risk: {risk_details['components']['liability']}
- Vendor Credit Risk: {risk_details['components']['vendor_credit']}

ACTION REQUIRED: Legal review mandatory before proceeding.

Blocked on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                await self.sap_client.add_note(contract_id, blocking_note)

                logger.warning(
                    f"[SCENARIO 2] Contract {contract_id} BLOCKED "
                    f"(risk score: {risk_score})"
                )

                return {
                    "scenario": 2,
                    "contract_id": contract_id,
                    "blocked": True,
                    "risk_score": risk_score,
                    "message": f"Contract blocked due to critical risk (score: {risk_score})"
                }

            else:
                logger.info(
                    f"[SCENARIO 2] Contract {contract_id} NOT blocked "
                    f"(risk score: {risk_score})"
                )

                return {
                    "scenario": 2,
                    "contract_id": contract_id,
                    "blocked": False,
                    "risk_score": risk_score,
                    "message": "Contract risk within acceptable limits"
                }

        except Exception as e:
            logger.error(f"[SCENARIO 2] Error: {e}")
            raise

    # ========================================
    # SCENARIO 3: AMENDMENT RE-EVALUATION
    # ========================================
    async def process_amendment(self, contract_id: str) -> Dict[str, Any]:
        """
        Scenario 3: Re-evaluate contract after amendment

        Flow:
        1. Read amended contract from SAP
        2. Re-calculate risk score
        3. Update risk assessment in SAP
        4. Flag if risk increased

        Args:
            contract_id: SAP contract number

        Returns:
            Re-evaluation result
        """
        try:
            logger.info(f"[SCENARIO 3] Processing amendment for contract {contract_id}")

            # Read current contract state
            contract = await self.sap_client.read_contract(contract_id)

            # Get previous risk score (if stored)
            data = contract.get('d', contract)
            previous_risk = data.get(settings.Z_FIELD_RISK_SCORE, 0)

            # Re-calculate risk
            new_risk_score = self.risk_engine.score(contract)
            new_risk_category = self.risk_engine.category(new_risk_score)
            intent = self.intent_engine.detect(contract)

            # Determine if risk increased
            risk_increased = new_risk_score > previous_risk
            risk_delta = new_risk_score - previous_risk

            # Determine new status
            if new_risk_score < settings.RISK_THRESHOLD_MEDIUM:
                status = "APPROVED"
            elif new_risk_score < settings.RISK_THRESHOLD_HIGH:
                status = "REVIEW_REQUIRED"
            else:
                status = "BLOCKED"

            # Update SAP
            update_payload = {
                settings.Z_FIELD_RISK_SCORE: new_risk_score,
                settings.Z_FIELD_RISK_CATEGORY: new_risk_category,
                settings.Z_FIELD_INTENT: intent,
                settings.Z_FIELD_STATUS: status,
                settings.Z_FIELD_VALIDATED_DATE: datetime.now().isoformat()
            }

            await self.sap_client.update_contract(contract_id, update_payload)

            # Add note if risk increased significantly
            if risk_increased and risk_delta > 20:
                note = f"""
AMENDMENT ALERT: Risk Increased

Previous Risk: {previous_risk}
New Risk: {new_risk_score}
Delta: +{risk_delta}

Status: {status}

Re-evaluation completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                await self.sap_client.add_note(contract_id, note)

            logger.info(
                f"[SCENARIO 3] Contract {contract_id} re-evaluated: "
                f"Risk {previous_risk} → {new_risk_score}"
            )

            return {
                "scenario": 3,
                "contract_id": contract_id,
                "previous_risk": previous_risk,
                "new_risk_score": new_risk_score,
                "risk_delta": risk_delta,
                "risk_increased": risk_increased,
                "status": status,
                "message": "Amendment re-evaluation complete"
            }

        except Exception as e:
            logger.error(f"[SCENARIO 3] Error: {e}")
            raise

    # ========================================
    # SCENARIO 4: MANUAL OVERRIDE
    # ========================================
    async def process_manual_override(self, contract_id: str) -> Dict[str, Any]:
        """
        Scenario 4: Process manual override from SAP user

        Flow:
        1. Read contract from SAP
        2. Check for manual override flag
        3. If override present, mark as manually approved
        4. Log override action

        Args:
            contract_id: SAP contract number

        Returns:
            Override processing result
        """
        try:
            logger.info(f"[SCENARIO 4] Processing manual override for {contract_id}")

            # Read contract
            contract = await self.sap_client.read_contract(contract_id)
            data = contract.get('d', contract)

            # Check for override flag (custom Z field set by SAP user)
            override_flag = data.get('Z_MANUAL_OVERRIDE', False)
            override_user = data.get('Z_OVERRIDE_USER', 'Unknown')

            if override_flag:
                # Update status to manually approved
                update_payload = {
                    settings.Z_FIELD_STATUS: "MANUALLY_APPROVED",
                    settings.Z_FIELD_VALIDATED_DATE: datetime.now().isoformat()
                }

                await self.sap_client.update_contract(contract_id, update_payload)

                # Log override action
                override_note = f"""
MANUAL OVERRIDE APPLIED

Override by: {override_user}
Override date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Original AI Status: {data.get(settings.Z_FIELD_STATUS, 'Unknown')}
Original Risk Score: {data.get(settings.Z_FIELD_RISK_SCORE, 'Unknown')}

User has manually approved this contract overriding AI recommendation.
"""
                await self.sap_client.add_note(contract_id, override_note)

                logger.warning(
                    f"[SCENARIO 4] Manual override processed for {contract_id} "
                    f"by {override_user}"
                )

                return {
                    "scenario": 4,
                    "contract_id": contract_id,
                    "override_applied": True,
                    "override_user": override_user,
                    "message": "Manual override processed successfully"
                }

            else:
                return {
                    "scenario": 4,
                    "contract_id": contract_id,
                    "override_applied": False,
                    "message": "No manual override flag found"
                }

        except Exception as e:
            logger.error(f"[SCENARIO 4] Error: {e}")
            raise

    # ========================================
    # SCENARIO 5: AI CLAUSE SUGGESTIONS
    # ========================================
    async def add_clause_suggestions(self, contract_id: str) -> Dict[str, Any]:
        """
        Scenario 5: Generate and attach AI clause suggestions to SAP contract

        Flow:
        1. Read contract from SAP
        2. Calculate risk score
        3. Generate clause improvement suggestions
        4. Add suggestions as SAP note
        5. Update suggestion flag

        Args:
            contract_id: SAP contract number

        Returns:
            Clause suggestion result
        """
        try:
            logger.info(f"[SCENARIO 5] Generating clause suggestions for {contract_id}")

            # Read contract
            contract = await self.sap_client.read_contract(contract_id)

            # Risk analysis
            risk_score = self.risk_engine.score(contract)

            # Generate clause suggestions
            suggestions = self.clause_engine.suggest(contract, risk_score)

            # Create formatted note
            suggestion_note = self.clause_engine.generate_redline_summary(
                contract,
                suggestions
            )

            # Add suggestions as SAP note
            await self.sap_client.add_note(contract_id, suggestion_note)

            # Update flag indicating suggestions have been generated
            update_payload = {
                'Z_AI_SUGGESTIONS_ADDED': True,
                settings.Z_FIELD_VALIDATED_DATE: datetime.now().isoformat()
            }

            await self.sap_client.update_contract(contract_id, update_payload)

            logger.info(
                f"[SCENARIO 5] Added {len(suggestions)} clause suggestions "
                f"to contract {contract_id}"
            )

            return {
                "scenario": 5,
                "contract_id": contract_id,
                "suggestions_count": len(suggestions),
                "suggestions": suggestions,
                "risk_score": risk_score,
                "message": "Clause suggestions added successfully"
            }

        except Exception as e:
            logger.error(f"[SCENARIO 5] Error: {e}")
            raise

    # ========================================
    # UTILITY METHODS
    # ========================================
    def _calculate_exposure(self, contract: Dict[str, Any]) -> float:
        """
        Calculate financial exposure

        Args:
            contract: SAP contract data

        Returns:
            Exposure value
        """
        try:
            data = contract.get('d', contract)
            net_amount = float(data.get('NetAmount', 0))

            # Simple exposure = contract value
            # In production, this would include:
            # - Liability cap analysis
            # - Payment schedule risk
            # - Currency exposure
            # - Duration risk factor

            return net_amount

        except Exception:
            return 0.0
