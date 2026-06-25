"""
Fivetran API Service Layer
Handles all interactions with Fivetran REST API v1
Documentation: https://fivetran.com/docs/rest-api
"""
import os
import requests
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FivetranService:
    """
    Service class for interacting with Fivetran REST API.
    Requires API key and secret from Fivetran dashboard.
    """

    BASE_URL = "https://api.fivetran.com/v1"

    def __init__(self):
        """Initialize Fivetran service with credentials from environment."""
        self.api_key = os.getenv('FIVETRAN_API_KEY', '')
        self.api_secret = os.getenv('FIVETRAN_API_SECRET', '')
        self.use_mock = not (self.api_key and self.api_secret)

        if self.use_mock:
            logger.warning("Fivetran credentials not found. Using mock data.")
        else:
            logger.info("Fivetran service initialized with real API credentials.")

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Make authenticated request to Fivetran API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (e.g., '/connectors')
            data: Request payload for POST/PATCH requests

        Returns:
            Response JSON data
        """
        if self.use_mock:
            return self._get_mock_response(endpoint)

        url = f"{self.BASE_URL}{endpoint}"
        auth = (self.api_key, self.api_secret)

        try:
            if method == 'GET':
                response = requests.get(url, auth=auth, timeout=30)
            elif method == 'POST':
                response = requests.post(url, auth=auth, json=data, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, auth=auth, json=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, auth=auth, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Fivetran API request failed: {str(e)}")
            # Fallback to mock data on API failure
            return self._get_mock_response(endpoint)

    def get_connectors(self) -> List[Dict]:
        """
        Get list of all Fivetran connectors.

        Returns:
            List of connector objects with details
        """
        response = self._make_request('GET', '/connectors')

        if self.use_mock or 'data' not in response:
            return self._get_mock_connectors()

        # Transform Fivetran API response to our format
        connectors = []
        for connector in response.get('data', {}).get('items', []):
            connectors.append({
                'id': connector.get('id'),
                'name': connector.get('schema', 'Unknown Connector'),
                'source': self._get_source_name(connector.get('service')),
                'status': 'active' if connector.get('status', {}).get('setup_state') == 'connected' else 'inactive',
                'recordsSynced': connector.get('status', {}).get('sync_state', {}).get('records_synced', 0),
                'lastSync': self._format_timestamp(connector.get('succeeded_at')),
                'paused': connector.get('paused', False),
                'syncFrequency': connector.get('sync_frequency', 360),  # minutes
            })

        return connectors

    def get_connector_details(self, connector_id: str) -> Dict:
        """
        Get detailed information about a specific connector.

        Args:
            connector_id: Fivetran connector ID

        Returns:
            Connector details
        """
        response = self._make_request('GET', f'/connectors/{connector_id}')

        if self.use_mock or 'data' not in response:
            return self._get_mock_connector_details(connector_id)

        connector = response.get('data', {})
        return {
            'id': connector.get('id'),
            'name': connector.get('schema'),
            'source': self._get_source_name(connector.get('service')),
            'status': connector.get('status', {}).get('setup_state'),
            'config': connector.get('config', {}),
            'createdAt': connector.get('created_at'),
            'succeededAt': connector.get('succeeded_at'),
            'failedAt': connector.get('failed_at'),
        }

    def trigger_sync(self, connector_id: str) -> Dict:
        """
        Manually trigger a sync for a connector.

        Args:
            connector_id: Fivetran connector ID

        Returns:
            Sync trigger response
        """
        response = self._make_request('POST', f'/connectors/{connector_id}/force')

        if self.use_mock:
            return {
                'success': True,
                'message': f'Sync triggered for connector: {connector_id}',
                'status': 'pending',
                'estimatedCompletionTime': '2-5 minutes'
            }

        return {
            'success': response.get('code') == 'Success',
            'message': response.get('message', 'Sync triggered successfully'),
            'data': response.get('data', {})
        }

    def get_connection_status(self) -> Dict:
        """
        Get overall Fivetran connection status.

        Returns:
            Connection status information
        """
        if self.use_mock:
            return self._get_mock_status()

        try:
            # Test API connection by fetching user info
            response = self._make_request('GET', '/users')

            if response and 'data' in response:
                connectors = self.get_connectors()
                return {
                    'status': 'connected',
                    'lastSync': datetime.now().isoformat(),
                    'totalConnectors': len(connectors),
                    'activeConnectors': len([c for c in connectors if c['status'] == 'active']),
                }
            else:
                return {'status': 'disconnected', 'error': 'Invalid API response'}

        except Exception as e:
            logger.error(f"Failed to get Fivetran status: {str(e)}")
            return {'status': 'disconnected', 'error': str(e)}

    def _get_source_name(self, service: str) -> str:
        """Map Fivetran service name to friendly display name."""
        mapping = {
            'docusign': 'DocuSign',
            'salesforce': 'Salesforce',
            'sap': 'SAP',
            'hubspot': 'HubSpot',
            'netsuite': 'NetSuite',
            'workday': 'Workday',
        }
        return mapping.get(service.lower(), service.title())

    def _format_timestamp(self, timestamp: Optional[str]) -> str:
        """Format ISO timestamp to relative time."""
        if not timestamp:
            return 'Never'

        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.now(dt.tzinfo)
            diff = now - dt

            if diff.seconds < 60:
                return 'Just now'
            elif diff.seconds < 3600:
                mins = diff.seconds // 60
                return f'{mins} min{"s" if mins > 1 else ""} ago'
            elif diff.days == 0:
                hours = diff.seconds // 3600
                return f'{hours} hour{"s" if hours > 1 else ""} ago'
            elif diff.days == 1:
                return 'Yesterday'
            else:
                return f'{diff.days} days ago'
        except Exception:
            return timestamp

    # ==================== MOCK DATA METHODS ====================

    def _get_mock_response(self, endpoint: str) -> Dict:
        """Return mock response for development/testing."""
        if '/connectors' in endpoint:
            return {'data': {'items': []}}
        return {'data': {}}

    def _get_mock_connectors(self) -> List[Dict]:
        """Return mock connector data for development."""
        return [
            {
                'id': 'docusign_connector',
                'name': 'DocuSign Connector',
                'source': 'DocuSign',
                'status': 'active',
                'recordsSynced': 1543,
                'lastSync': '2 mins ago',
                'paused': False,
                'syncFrequency': 15,
            },
            {
                'id': 'sap_connector',
                'name': 'SAP Connector',
                'source': 'SAP',
                'status': 'active',
                'recordsSynced': 3287,
                'lastSync': '15 mins ago',
                'paused': False,
                'syncFrequency': 60,
            },
            {
                'id': 'salesforce_connector',
                'name': 'Salesforce Connector',
                'source': 'Salesforce',
                'status': 'active',
                'recordsSynced': 2156,
                'lastSync': '30 mins ago',
                'paused': False,
                'syncFrequency': 30,
            }
        ]

    def _get_mock_connector_details(self, connector_id: str) -> Dict:
        """Return mock connector details."""
        connectors = {
            'docusign_connector': {
                'id': 'docusign_connector',
                'name': 'DocuSign Connector',
                'source': 'DocuSign',
                'status': 'connected',
                'config': {'api_version': 'v2'},
                'createdAt': '2026-01-01T00:00:00Z',
                'succeededAt': '2026-01-14T12:30:00Z',
            },
            'sap_connector': {
                'id': 'sap_connector',
                'name': 'SAP Connector',
                'source': 'SAP',
                'status': 'connected',
                'config': {'system_id': 'PRD'},
                'createdAt': '2026-01-01T00:00:00Z',
                'succeededAt': '2026-01-14T12:15:00Z',
            },
            'salesforce_connector': {
                'id': 'salesforce_connector',
                'name': 'Salesforce Connector',
                'source': 'Salesforce',
                'status': 'connected',
                'config': {'api_version': '56.0'},
                'createdAt': '2026-01-01T00:00:00Z',
                'succeededAt': '2026-01-14T12:00:00Z',
            }
        }
        return connectors.get(connector_id, {})

    def _get_mock_status(self) -> Dict:
        """Return mock connection status."""
        return {
            'status': 'connected',
            'lastSync': datetime.now().isoformat(),
            'totalConnectors': 3,
            'activeConnectors': 3,
            'message': 'Using mock data - Set FIVETRAN_API_KEY and FIVETRAN_API_SECRET to use real API'
        }
