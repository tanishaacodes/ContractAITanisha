"""
Infor ERP REST API Client

Handles OAuth2 authentication and REST API communication with
Infor ERP LN / CloudSuite Industrial via Infor ION API Gateway.
"""
import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from .config import settings

logger = logging.getLogger(__name__)


class InforAuthError(Exception):
    """Infor Authentication Error"""
    pass


class InforAPIError(Exception):
    """Infor API Communication Error"""
    pass


class InforClient:
    """
    Async Infor ERP REST API Client

    Features:
    - OAuth2 Client Credentials (Infor OS)
    - Automatic token refresh
    - Async context manager support
    - Handles Infor ION API Gateway routing
    """

    def __init__(self):
        self.base_url = settings.INFOR_BASE_URL
        self.token_url = settings.INFOR_TOKEN_URL
        self.client_id = settings.INFOR_CLIENT_ID
        self.client_secret = settings.INFOR_CLIENT_SECRET
        self.tenant_id = settings.INFOR_TENANT_ID

        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.http_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self.http_client = httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT)
        await self.ensure_authenticated()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.http_client:
            await self.http_client.aclose()

    def _is_token_expired(self) -> bool:
        if not self.token_expires_at:
            return True
        return datetime.now() + timedelta(minutes=5) >= self.token_expires_at

    async def ensure_authenticated(self):
        if not self.access_token or self._is_token_expired():
            await self.authenticate()

    async def authenticate(self):
        """OAuth2 Client Credentials via Infor OS"""
        try:
            logger.info("Authenticating with Infor ION...")

            if not self.http_client:
                self.http_client = httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT)

            # Infor uses standard OAuth2 CC flow
            response = await self.http_client.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            token_data = response.json()

            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            logger.info("Authenticated with Infor ION successfully")

        except httpx.HTTPStatusError as e:
            logger.error(f"Infor auth failed: {e.response.text}")
            raise InforAuthError(f"Authentication failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Infor auth error: {e}")
            raise InforAuthError(f"Authentication error: {e}")

    async def _headers(self) -> Dict[str, str]:
        await self.ensure_authenticated()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Infor-TenantId": self.tenant_id,
        }

    async def read_contract(self, contract_id: str) -> Dict[str, Any]:
        """Read a single contract from Infor ERP"""
        try:
            headers = await self._headers()
            url = f"{self.base_url}{settings.CONTRACT_API_PATH}/{contract_id}"

            response = await self.http_client.get(url, headers=headers)
            response.raise_for_status()

            logger.info(f"Read Infor contract {contract_id}")
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise InforAPIError(f"Contract {contract_id} not found in Infor")
            raise InforAPIError(f"Failed to read contract: {e.response.status_code}")
        except Exception as e:
            raise InforAPIError(f"Error reading Infor contract: {e}")

    async def update_contract(self, contract_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update contract user-defined fields in Infor ERP"""
        try:
            headers = await self._headers()
            url = f"{self.base_url}{settings.CONTRACT_API_PATH}/{contract_id}"

            response = await self.http_client.patch(url, headers=headers, json=payload)
            response.raise_for_status()

            logger.info(f"Updated Infor contract {contract_id}")

            if response.status_code == 204:
                return {"success": True, "contract_id": contract_id}
            return response.json()

        except httpx.HTTPStatusError as e:
            raise InforAPIError(f"Failed to update contract: {e.response.status_code}")
        except Exception as e:
            raise InforAPIError(f"Error updating Infor contract: {e}")

    async def add_note(self, contract_id: str, note_text: str) -> Dict[str, Any]:
        """Add a note/memo to the Infor contract"""
        try:
            headers = await self._headers()
            url = f"{self.base_url}{settings.CONTRACT_API_PATH}/{contract_id}/notes"

            payload = {
                "noteText": note_text,
                "noteType": "AI_ANALYSIS",
                "createdBy": "PrimeContractAI"
            }

            response = await self.http_client.post(url, headers=headers, json=payload)
            response.raise_for_status()

            logger.info(f"Added note to Infor contract {contract_id}")
            return response.json()

        except httpx.HTTPStatusError as e:
            raise InforAPIError(f"Failed to add note: {e.response.status_code}")
        except Exception as e:
            raise InforAPIError(f"Error adding note to Infor contract: {e}")

    async def list_contracts(self, top: int = 50) -> Dict[str, Any]:
        """List contracts from Infor ERP"""
        try:
            headers = await self._headers()
            url = f"{self.base_url}{settings.CONTRACT_API_PATH}"
            params = {"$top": top, "$orderby": "createdDate desc"}

            response = await self.http_client.get(url, headers=headers, params=params)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            raise InforAPIError(f"Error listing Infor contracts: {e}")
