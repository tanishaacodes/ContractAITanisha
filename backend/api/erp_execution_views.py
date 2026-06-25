"""
Deep ERP Integration – Feature 9: ERP Auto-Execution Layer
===========================================================
POST /api/erp/auto-trigger/      — trigger ERP action for a contract
GET  /api/erp/execution-log/     — last 50 execution actions
POST /api/erp/bulk-execute/      — bulk trigger for multiple contracts
"""

import uuid
import logging
from datetime import datetime, timedelta
from collections import deque

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from core.models import Contract, ContractRiskAnalysis

logger = logging.getLogger(__name__)

# In-memory execution log (deque for O(1) append + bounded size)
_execution_log = deque(maxlen=200)

TRIGGER_TYPES = {
    "payment_hold": {
        "action": "Payment Hold Triggered",
        "erp_system": "SAP S/4HANA",
        "description": "Placed payment on hold in SAP FI module pending contract risk review.",
        "estimated_impact": "Preserves cash flow; delays outgoing payment by 15-30 days",
    },
    "procurement_change": {
        "action": "Procurement Order Updated",
        "erp_system": "SAP MM",
        "description": "Updated procurement order in SAP MM with revised terms from contract amendment.",
        "estimated_impact": "Aligns purchase order with new contractual pricing and delivery terms",
    },
    "vendor_alert": {
        "action": "Vendor Risk Alert Dispatched",
        "erp_system": "Infor LN",
        "description": "Dispatched vendor risk alert to Infor LN supplier management module.",
        "estimated_impact": "Triggers supplier audit; estimated $50K risk mitigation",
    },
    "contract_execute": {
        "action": "Contract Execution Initiated",
        "erp_system": "SAP CLM",
        "description": "Initiated automated contract execution workflow in SAP Contract Lifecycle Management.",
        "estimated_impact": "Reduces manual processing time from 5 days to 4 hours",
    },
}


def _get_contract_name(contract_id: str) -> str:
    try:
        contract = Contract.objects.get(id=contract_id)
        return contract.original_filename or contract_id[:12]
    except Exception:
        return contract_id[:12] if contract_id else "Unknown"


def _build_log_entry(contract_id: str, trigger_type: str, reason: str, initiated_by: str = "AI System") -> dict:
    trigger_info = TRIGGER_TYPES.get(trigger_type, {
        "action": f"Custom Action: {trigger_type}",
        "erp_system": "SAP S/4HANA",
        "description": f"Executed custom trigger: {trigger_type}",
        "estimated_impact": "Impact assessment pending",
    })

    contract_name = _get_contract_name(contract_id)

    return {
        "id": str(uuid.uuid4()),
        "contract_id": contract_id,
        "contract_name": contract_name,
        "trigger_type": trigger_type,
        "action": trigger_info["action"],
        "erp_system": trigger_info["erp_system"],
        "description": trigger_info["description"],
        "reason": reason or "Automated contract risk threshold exceeded",
        "status": "executed",
        "estimated_impact": trigger_info["estimated_impact"],
        "initiated_by": initiated_by,
        "timestamp": datetime.utcnow().isoformat(),
        "execution_time_ms": 142,  # Simulated
    }


# ─────────────────────────────────────────────
# Auto-Trigger
# ─────────────────────────────────────────────

class ERPAutoTriggerView(APIView):
    """POST /api/erp/auto-trigger/"""
    permission_classes = [AllowAny]

    def post(self, request):
        contract_id = request.data.get("contract_id", "")
        trigger_type = request.data.get("trigger_type", "")
        reason = request.data.get("reason", "")

        if not trigger_type:
            return Response({"error": "trigger_type required"}, status=status.HTTP_400_BAD_REQUEST)

        valid_triggers = list(TRIGGER_TYPES.keys())
        if trigger_type not in valid_triggers:
            return Response(
                {"error": f"trigger_type must be one of: {', '.join(valid_triggers)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        entry = _build_log_entry(contract_id, trigger_type, reason)
        _execution_log.appendleft(entry)

        return Response({
            "success": True,
            "action": entry["action"],
            "contract_id": contract_id,
            "trigger_type": trigger_type,
            "status": entry["status"],
            "erp_system": entry["erp_system"],
            "estimated_impact": entry["estimated_impact"],
            "timestamp": entry["timestamp"],
            "log_id": entry["id"],
        }, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────
# Execution Log
# ─────────────────────────────────────────────

class ERPExecutionLogView(APIView):
    """GET /api/erp/execution-log/"""
    permission_classes = [AllowAny]

    def get(self, request):
        log = list(_execution_log)[:50]

        # Summary stats
        trigger_counts = {}
        system_counts = {}
        for entry in log:
            tt = entry.get("trigger_type", "unknown")
            sys = entry.get("erp_system", "unknown")
            trigger_counts[tt] = trigger_counts.get(tt, 0) + 1
            system_counts[sys] = system_counts.get(sys, 0) + 1

        return Response({
            "executions": log,
            "total": len(log),
            "summary": {
                "by_trigger_type": trigger_counts,
                "by_erp_system": system_counts,
                "last_executed": log[0]["timestamp"] if log else None,
            },
        })


# ─────────────────────────────────────────────
# Bulk Execute
# ─────────────────────────────────────────────

class ERPBulkExecuteView(APIView):
    """POST /api/erp/bulk-execute/"""
    permission_classes = [AllowAny]

    def post(self, request):
        contract_ids = request.data.get("contract_ids", [])
        action = request.data.get("action", "")
        reason = request.data.get("reason", "Bulk ERP execution triggered")

        if not contract_ids:
            return Response({"error": "contract_ids list required"}, status=status.HTTP_400_BAD_REQUEST)
        if not action:
            return Response({"error": "action required"}, status=status.HTTP_400_BAD_REQUEST)
        if action not in TRIGGER_TYPES:
            return Response(
                {"error": f"action must be one of: {', '.join(TRIGGER_TYPES.keys())}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Cap at 50 contracts per bulk operation
        contract_ids = contract_ids[:50]

        executed = []
        for cid in contract_ids:
            entry = _build_log_entry(cid, action, reason, initiated_by="Bulk Operation")
            _execution_log.appendleft(entry)
            executed.append({
                "contract_id": cid,
                "contract_name": entry["contract_name"],
                "status": "executed",
                "log_id": entry["id"],
            })

        return Response({
            "bulk_action": action,
            "total_contracts": len(contract_ids),
            "executed": len(executed),
            "failed": 0,
            "results": executed,
            "erp_system": TRIGGER_TYPES[action]["erp_system"],
            "executed_at": datetime.utcnow().isoformat(),
        }, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────
# Contracts List for ERP dropdown
# ─────────────────────────────────────────────

class ERPContractsListView(APIView):
    """GET /api/erp/contracts/ — returns all contracts with risk scores for the dropdown."""
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            contracts = Contract.objects.all().order_by('-id')[:200]
            result = []
            for c in contracts:
                try:
                    risk_score = round(c.risk_analysis.risk_score / 100.0, 2)
                    risk_level = c.risk_analysis.risk_level
                except ContractRiskAnalysis.DoesNotExist:
                    risk_score = None
                    risk_level = None

                result.append({
                    "id": str(c.id),
                    "name": c.original_filename or c.filename,
                    "contract_type": c.contract_type,
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                })

            # Sort: high-risk contracts first (None last)
            result.sort(key=lambda x: (x["risk_score"] is None, -(x["risk_score"] or 0)))

            return Response({"contracts": result})
        except Exception as exc:
            logger.error("ERPContractsListView error: %s", exc)
            return Response({"contracts": [], "error": str(exc)})
