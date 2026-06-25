"""
SAP S/4HANA CSRF + ETag Compliant Write-Back

SAP OData v2 requires:
  1. First GET with "X-CSRF-Token: Fetch" header → returns token + ETag
  2. PATCH/PUT/POST with that token + ETag in If-Match header

This module handles that handshake correctly so AI decisions
(risk score, status, etc.) actually write to SAP Z-fields.
"""
import logging
import os
import requests

logger = logging.getLogger(__name__)

_SAP_SANDBOX_BASE = (
    "https://sandbox.api.sap.com/s4hanacloud/sap/opu/odata/sap"
    "/API_PURCHASECONTRACT_PROCESS_SRV"
)
_SAP_API_KEY = os.environ.get("SAP_API_KEY", "pEEcoYrNvA8GxL5m0GfGVbzxeSnnbGlY")


class SAPWriteBack:
    """
    Handles CSRF token + ETag fetch → PATCH write-back to SAP OData.

    Usage:
        wb = SAPWriteBack()
        result = wb.update_z_fields("4600001234", {
            "Z_AI_RISK_SCORE": "75",
            "Z_AI_STATUS": "BLOCKED",
        })
    """

    def __init__(self, base_url: str = _SAP_SANDBOX_BASE, api_key: str = _SAP_API_KEY):
        self.base_url = base_url
        self.api_key = api_key
        self._session = requests.Session()
        self._session.headers.update({
            "APIKey": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    # ── Step 1: Fetch CSRF token + ETag ──────────────────────────────────────

    def _fetch_csrf_and_etag(self, contract_id: str) -> tuple[str, str]:
        """
        GET the contract with X-CSRF-Token: Fetch to obtain:
          - X-CSRF-Token (required for mutating requests)
          - ETag (required in If-Match header for PATCH)

        Returns (csrf_token, etag).
        Raises if the fetch fails.
        """
        url = f"{self.base_url}/A_PurchaseContract('{contract_id}')"
        resp = self._session.get(
            url,
            params={"$format": "json"},
            headers={"X-CSRF-Token": "Fetch"},
            timeout=15,
        )
        resp.raise_for_status()

        csrf_token = resp.headers.get("X-CSRF-Token", "")
        etag = resp.headers.get("ETag", "*")  # "*" = unconditional if no ETag returned

        if not csrf_token:
            logger.warning(
                f"[SAP-WB] No X-CSRF-Token in response headers for {contract_id}. "
                "Sandbox may not enforce CSRF — proceeding with empty token."
            )

        logger.debug(f"[SAP-WB] CSRF={csrf_token[:12]}… ETag={etag}")
        return csrf_token, etag

    # ── Step 2: PATCH with CSRF + ETag ───────────────────────────────────────

    def update_z_fields(self, contract_id: str, z_fields: dict) -> dict:
        """
        Write AI decision metadata back to SAP contract Z-fields.

        Args:
            contract_id: SAP PurchaseContract number (e.g. "4600001234")
            z_fields: dict of SAP Z-field names → values
                      e.g. {"Z_AI_RISK_SCORE": "75", "Z_AI_STATUS": "BLOCKED"}

        Returns:
            {"success": True, "contract_id": ..., "fields_written": ..., "mode": ...}
            or
            {"success": False, "error": ..., "note": "sandbox-readonly"}
        """
        try:
            csrf_token, etag = self._fetch_csrf_and_etag(contract_id)
        except Exception as e:
            logger.error(f"[SAP-WB] CSRF fetch failed for {contract_id}: {e}")
            return {
                "success": False,
                "contract_id": contract_id,
                "error": f"CSRF fetch failed: {e}",
                "note": "write-back skipped",
            }

        url = f"{self.base_url}/A_PurchaseContract('{contract_id}')"
        patch_headers = {
            "X-CSRF-Token": csrf_token,
            "If-Match": etag,
        }

        try:
            resp = self._session.patch(
                url,
                json=z_fields,
                headers=patch_headers,
                params={"$format": "json"},
                timeout=20,
            )

            # SAP returns 204 No Content on successful PATCH
            if resp.status_code in (200, 204):
                logger.info(
                    f"[SAP-WB] Written to {contract_id}: {list(z_fields.keys())}"
                )
                return {
                    "success": True,
                    "contract_id": contract_id,
                    "fields_written": list(z_fields.keys()),
                    "http_status": resp.status_code,
                    "mode": "live",
                }

            # Sandbox is read-only → 403 or 405 — log but don't fail the scenario
            if resp.status_code in (403, 405, 501):
                logger.warning(
                    f"[SAP-WB] Sandbox refused PATCH for {contract_id} "
                    f"({resp.status_code}) — fields logged, not written"
                )
                return {
                    "success": False,
                    "contract_id": contract_id,
                    "http_status": resp.status_code,
                    "fields_attempted": list(z_fields.keys()),
                    "note": "sandbox-readonly — Z-fields logged but not written to SAP",
                }

            resp.raise_for_status()

        except requests.exceptions.HTTPError as e:
            logger.error(f"[SAP-WB] PATCH failed for {contract_id}: {e}")
            return {
                "success": False,
                "contract_id": contract_id,
                "error": str(e),
                "note": "write-back failed",
            }

        return {"success": False, "contract_id": contract_id, "error": "unexpected state"}

    def add_sap_note(self, contract_id: str, note_text: str) -> dict:
        """
        POST a text note to the SAP contract (PurchaseContractNote entity).
        Uses CSRF token from a fresh fetch.

        In sandbox this will return 403/405 — gracefully logged.
        """
        try:
            csrf_token, _ = self._fetch_csrf_and_etag(contract_id)
        except Exception as e:
            return {"success": False, "error": str(e)}

        url = f"{self.base_url}/A_PurchaseContractNote"
        try:
            resp = self._session.post(
                url,
                json={
                    "PurchaseContract": contract_id,
                    "LongTextID": "F01",
                    "Language": "EN",
                    "PlainLongText": note_text[:4096],  # SAP text limit
                },
                headers={"X-CSRF-Token": csrf_token},
                params={"$format": "json"},
                timeout=20,
            )
            if resp.status_code in (200, 201):
                return {"success": True, "contract_id": contract_id, "note_added": True}
            return {
                "success": False,
                "contract_id": contract_id,
                "http_status": resp.status_code,
                "note": "sandbox-readonly — note logged but not written",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
