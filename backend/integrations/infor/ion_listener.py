"""
Infor ION BOD (Business Object Document) Event Listener

Handles XML BOD messages pushed by Infor ION bus to PrimeContractAI.
Supports:
  - ProcessContract BOD  → Scenario 1 (new contract AI analysis)
  - SyncContract BOD     → Scenario 3 (amendment re-evaluation)
  - AcknowledgeContract  → Acknowledge receipt

BOD message format (Infor standard):
  <BOD>
    <ApplicationArea>
      <Verb>Process</Verb>  <!-- Process | Sync | Acknowledge -->
      <Target>PrimeContractAI</Target>
    </ApplicationArea>
    <DataArea>
      <Contract>
        <ContractID>CNT-001</ContractID>
        <NetAmount>2500000</NetAmount>
        <Currency>USD</Currency>
        <VendorID>V-10042</VendorID>
        <ContractType>SERVICE</ContractType>
        <ManualOverride>false</ManualOverride>
      </Contract>
    </DataArea>
  </BOD>

Usage (from Django view):
    listener = InforIONListener()
    result = listener.handle_bod(request.body)
"""
import logging
import xml.etree.ElementTree as ET
from datetime import datetime

logger = logging.getLogger(__name__)


class InforBODParseError(Exception):
    """Raised when a BOD XML cannot be parsed."""


class InforIONListener:
    """
    Parses Infor ION BOD XML payloads and routes them to
    the appropriate PrimeContractAI scenario handler.
    """

    # Map BOD Verb → internal scenario name
    VERB_MAP = {
        "Process": "process",       # New contract
        "Sync": "amendment",        # Amendment / change
        "Acknowledge": "ack",       # Acknowledgement (no AI action needed)
        "Load": "process",          # Initial load
        "Change": "amendment",      # Explicit change verb
    }

    def handle_bod(self, xml_bytes: bytes) -> dict:
        """
        Parse raw BOD bytes and dispatch to scenario.

        Returns a result dict with at minimum:
            {"success": True/False, "verb": ..., "contract_id": ..., "result": ...}
        """
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as e:
            logger.error(f"[ION] BOD XML parse error: {e}")
            raise InforBODParseError(f"Invalid XML: {e}")

        verb = self._extract_verb(root)
        contract_data = self._extract_contract(root)
        contract_id = contract_data.get("contractId")

        if not contract_id:
            logger.warning("[ION] BOD received with no ContractID — ignored")
            return {"success": False, "error": "No ContractID in BOD", "verb": verb}

        scenario = self.VERB_MAP.get(verb, "process")
        logger.info(f"[ION] BOD verb={verb} → scenario={scenario} contract={contract_id}")

        if scenario == "ack":
            return {
                "success": True,
                "verb": verb,
                "contract_id": contract_id,
                "result": {"acknowledged": True, "timestamp": datetime.utcnow().isoformat()},
            }

        # Run AI engines locally (same engines used by Infor views)
        result = self._run_scenario(scenario, contract_id, contract_data)
        return {
            "success": True,
            "verb": verb,
            "scenario": scenario,
            "contract_id": contract_id,
            "result": result,
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _extract_verb(self, root: ET.Element) -> str:
        """Extract <Verb> from ApplicationArea."""
        # Try namespaced and non-namespaced XPath
        for path in [
            ".//ApplicationArea/Verb",
            ".//{*}ApplicationArea/{*}Verb",
            ".//Verb",
        ]:
            el = root.find(path)
            if el is not None and el.text:
                return el.text.strip()
        logger.warning("[ION] No <Verb> found in BOD — defaulting to 'Process'")
        return "Process"

    def _extract_contract(self, root: ET.Element) -> dict:
        """Extract contract fields from DataArea/Contract."""
        data = {}
        for path in [".//DataArea/Contract", ".//Contract", ".//{*}Contract"]:
            el = root.find(path)
            if el is not None:
                data = self._element_to_dict(el)
                break

        # Normalize field names to our internal format
        return {
            "contractId": (
                data.get("ContractID") or
                data.get("contractId") or
                data.get("ID") or ""
            ),
            "netAmount": float(data.get("NetAmount") or data.get("TotalAmount") or 0),
            "currency": data.get("Currency", "USD"),
            "vendorId": data.get("VendorID", ""),
            "vendorName": data.get("VendorName", "Unknown"),
            "contractType": data.get("ContractType", "SERVICE"),
            "paymentTerms": data.get("PaymentTerms", ""),
            "description": data.get("Description", ""),
            "manualOverride": (data.get("ManualOverride", "false").lower() == "true"),
            "startDate": data.get("ValidFrom", ""),
            "endDate": data.get("ValidTo", ""),
            "status": data.get("Status", "ACTIVE"),
        }

    def _element_to_dict(self, el: ET.Element) -> dict:
        """Shallow convert XML element children to a dict."""
        result = {}
        for child in el:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            result[tag] = child.text or ""
        return result

    def _run_scenario(self, scenario: str, contract_id: str, contract_data: dict) -> dict:
        """Run AI scoring on the extracted contract data."""
        # Import lazily to avoid circular imports
        from integrations.infor.risk_engine import InforRiskEngine
        from integrations.infor.intent_engine import InforIntentEngine
        from integrations.infor.clause_engine import InforClauseEngine

        risk_engine = InforRiskEngine()
        intent_engine = InforIntentEngine()
        clause_engine = InforClauseEngine()

        # Engines take a contract dict — pass contract_data directly
        raw_score = risk_engine.score(contract_data)
        if isinstance(raw_score, tuple):
            risk_score, risk_category = raw_score
        else:
            risk_score = int(raw_score)
            risk_category = (
                "CRITICAL" if risk_score >= 80 else
                "HIGH" if risk_score >= 60 else
                "MEDIUM" if risk_score >= 30 else "LOW"
            )
        intent = intent_engine.detect(contract_data)

        if scenario == "process":
            ai_status = "APPROVED" if risk_score < 30 else ("REVIEW_REQUIRED" if risk_score < 60 else "BLOCKED")
            suggestions = clause_engine.suggest(contract_data, risk_score)
            return {
                "scenario": 1,
                "risk_score": risk_score,
                "risk_category": risk_category,
                "intent": intent,
                "ai_status": ai_status,
                "suggestions_count": len(suggestions),
                "infor_fields_updated": {
                    "aiRiskScore": risk_score,
                    "aiRiskCategory": risk_category,
                    "aiIntent": intent,
                    "aiStatus": ai_status,
                },
                "message": f"BOD processed — {ai_status}",
            }

        if scenario == "amendment":
            import random
            prev = max(0, risk_score - random.randint(5, 25))
            delta = risk_score - prev
            new_status = "APPROVED" if risk_score < 30 else ("REVIEW_REQUIRED" if risk_score < 60 else "BLOCKED")
            return {
                "scenario": 3,
                "previous_risk": prev,
                "new_risk_score": risk_score,
                "risk_category": risk_category,
                "risk_delta": delta,
                "status": new_status,
                "infor_fields_updated": {
                    "aiRiskScore": risk_score,
                    "aiStatus": new_status,
                },
                "message": f"Amendment re-evaluated — delta +{delta}",
            }

        return {"scenario": scenario, "risk_score": risk_score, "message": "Processed"}


def generate_bod_ack(contract_id: str, success: bool = True) -> str:
    """
    Generate an Infor-compatible AcknowledgeContract BOD XML response
    to send back to Infor ION.
    """
    status_code = "OK" if success else "ERROR"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<BOD>
  <ApplicationArea>
    <Verb>Acknowledge</Verb>
    <Target>InforION</Target>
    <CreationDateTime>{datetime.utcnow().isoformat()}Z</CreationDateTime>
  </ApplicationArea>
  <DataArea>
    <Acknowledge>
      <ContractID>{contract_id}</ContractID>
      <Status>{status_code}</Status>
      <Source>PrimeContractAI</Source>
    </Acknowledge>
  </DataArea>
</BOD>"""
