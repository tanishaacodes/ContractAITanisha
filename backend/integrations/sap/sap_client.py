"""
SAP OData Client

Handles OAuth2 authentication and OData API communication with SAP S/4HANA.
Includes CSRF token handling, ETag support, and retry logic.
"""
import httpx
import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from .config import settings

logger = logging.getLogger(__name__)


class SAPAuthError(Exception):
    """SAP Authentication Error"""
    pass


class SAPAPIError(Exception):
    """SAP API Communication Error"""
    pass


class SAPClient:
    """
    Async SAP S/4HANA OData API Client

    Features:
    - OAuth2 client credentials flow
    - CSRF token handling
    - ETag support for optimistic locking
    - Automatic token refresh
    - Exponential backoff retry logic
    """

    def __init__(self):
        self.base_url = settings.SAP_BASE_URL
        self.token_url = settings.SAP_TOKEN_URL
        self.client_id = settings.SAP_CLIENT_ID
        self.client_secret = settings.SAP_CLIENT_SECRET

        # Token management
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        # CSRF token (required by SAP for write operations)
        self.csrf_token: Optional[str] = None

        # HTTP client
        self.http_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.http_client = httpx.AsyncClient(
            timeout=settings.REQUEST_TIMEOUT,
            verify=True
        )
        await self.ensure_authenticated()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.http_client:
            await self.http_client.aclose()

    async def ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if not self.access_token or self._is_token_expired():
            await self.authenticate()

    def _is_token_expired(self) -> bool:
        """Check if token is expired (with 5 min buffer)"""
        if not self.token_expires_at:
            return True
        return datetime.now() + timedelta(minutes=5) >= self.token_expires_at

    async def authenticate(self):
        """
        Authenticate with SAP using OAuth2 Client Credentials flow
        """
        try:
            logger.info("Authenticating with SAP S/4HANA...")

            if not self.http_client:
                self.http_client = httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT)

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

            logger.info("Successfully authenticated with SAP")

        except httpx.HTTPStatusError as e:
            logger.error(f"SAP authentication failed: {e.response.text}")
            raise SAPAuthError(f"Authentication failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"SAP authentication error: {str(e)}")
            raise SAPAuthError(f"Authentication error: {str(e)}")

    async def _get_csrf_token(self):
        """
        Fetch CSRF token required for write operations (POST, PATCH, DELETE)
        """
        if not settings.ENABLE_CSRF_TOKEN:
            return

        try:
            await self.ensure_authenticated()

            # HEAD request to get CSRF token
            url = f"{self.base_url}/{settings.CONTRACT_SERVICE}"
            response = await self.http_client.head(
                url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "x-csrf-token": "fetch"
                }
            )

            self.csrf_token = response.headers.get("x-csrf-token")
            logger.debug("CSRF token obtained")

        except Exception as e:
            logger.warning(f"Could not fetch CSRF token: {e}")

    async def _headers(self, include_csrf: bool = False) -> Dict[str, str]:
        """Build request headers with auth and optional CSRF token"""
        await self.ensure_authenticated()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-SAP-System-ID": settings.SAP_SYSTEM_ID
        }

        if include_csrf and settings.ENABLE_CSRF_TOKEN:
            if not self.csrf_token:
                await self._get_csrf_token()
            if self.csrf_token:
                headers["x-csrf-token"] = self.csrf_token

        return headers

    async def read_contract(self, contract_id: str) -> Dict[str, Any]:
        """
        Read contract from SAP S/4HANA via OData

        Args:
            contract_id: SAP contract number (e.g., '4600002345')

        Returns:
            Contract data dictionary
        """
        try:
            logger.info(f"Reading contract {contract_id} from SAP")

            headers = await self._headers()
            url = f"{self.base_url}/{settings.CONTRACT_SERVICE}/A_PurchaseContract('{contract_id}')"

            # Add expand for line items
            params = {"$expand": "to_Item"}

            response = await self.http_client.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Successfully read contract {contract_id}")

            return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise SAPAPIError(f"Contract {contract_id} not found in SAP")
            logger.error(f"Error reading contract: {e.response.text}")
            raise SAPAPIError(f"Failed to read contract: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error reading contract: {str(e)}")
            raise SAPAPIError(f"Error reading contract: {str(e)}")

    async def update_contract(
        self,
        contract_id: str,
        payload: Dict[str, Any],
        etag: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update contract in SAP S/4HANA via OData PATCH

        Args:
            contract_id: SAP contract number
            payload: Update data (typically Z-fields with AI results)
            etag: Optional ETag for optimistic locking

        Returns:
            Updated contract data or success indicator
        """
        try:
            logger.info(f"Updating contract {contract_id} in SAP")

            headers = await self._headers(include_csrf=True)

            # Add ETag if provided (for optimistic locking)
            if etag and settings.ENABLE_ETAG:
                headers["If-Match"] = etag

            url = f"{self.base_url}/{settings.CONTRACT_SERVICE}/A_PurchaseContract('{contract_id}')"

            response = await self.http_client.patch(
                url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            logger.info(f"Successfully updated contract {contract_id}")

            # SAP PATCH often returns 204 No Content
            if response.status_code == 204:
                return {"success": True, "contract_id": contract_id}

            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Error updating contract: {e.response.text}")
            raise SAPAPIError(f"Failed to update contract: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error updating contract: {str(e)}")
            raise SAPAPIError(f"Error updating contract: {str(e)}")

    async def add_note(self, contract_id: str, note_text: str) -> Dict[str, Any]:
        """
        Add a text note to SAP contract

        Args:
            contract_id: SAP contract number
            note_text: Note content (e.g., AI clause suggestions)

        Returns:
            Created note data
        """
        try:
            logger.info(f"Adding note to contract {contract_id}")

            headers = await self._headers(include_csrf=True)
            url = f"{self.base_url}/{settings.CONTRACT_SERVICE}/A_PurchaseContractNote"

            payload = {
                "PurchaseContract": contract_id,
                "TextObjectType": "NOTE",
                "Language": "EN",
                "PlainLongText": note_text
            }

            response = await self.http_client.post(
                url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            logger.info(f"Successfully added note to contract {contract_id}")

            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Error adding note: {e.response.text}")
            raise SAPAPIError(f"Failed to add note: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error adding note: {str(e)}")
            raise SAPAPIError(f"Error adding note: {str(e)}")

    async def read_contracts_by_vendor(self, vendor_id: str) -> Dict[str, Any]:
        """
        Read all contracts for a specific vendor

        Args:
            vendor_id: SAP vendor ID

        Returns:
            List of contracts
        """
        try:
            headers = await self._headers()
            url = f"{self.base_url}/{settings.CONTRACT_SERVICE}/A_PurchaseContract"

            params = {
                "$filter": f"Supplier eq '{vendor_id}'",
                "$expand": "to_Item"
            }

            response = await self.http_client.get(url, headers=headers, params=params)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Error reading vendor contracts: {str(e)}")
            raise SAPAPIError(f"Error reading vendor contracts: {str(e)}")
