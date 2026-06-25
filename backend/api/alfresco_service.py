"""
Alfresco Document Extraction Service

Handles connection to Alfresco CMS and document extraction.
Supports both python-alfresco-api and direct REST API calls.
"""

import requests
from django.conf import settings
from typing import List, Dict, Optional, Any
import logging
from io import BytesIO
import concurrent.futures

logger = logging.getLogger(__name__)


class AlfrescoExtractor:
    """
    Service for extracting contracts from Alfresco CMS.

    Supports:
    - Fetching documents from specific folders
    - Downloading document content
    - Retrieving document metadata and properties
    - Version management
    """

    def __init__(self):
        """Initialize Alfresco connection."""
        self.base_url = getattr(settings, 'ALFRESCO_URL', 'http://localhost:8080/alfresco')
        self.username = getattr(settings, 'ALFRESCO_USER', 'admin')
        self.password = getattr(settings, 'ALFRESCO_PASSWORD', 'admin')
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.ticket = None

        # Try to authenticate
        try:
            self._authenticate()
        except Exception as e:
            logger.warning(f"Alfresco authentication failed: {e}")

    def _authenticate(self) -> Optional[str]:
        """
        Authenticate with Alfresco and get ticket.

        Returns:
            Authentication ticket or None
        """
        try:
            # Using python-alfresco-api approach
            from python_alfresco_api import ClientFactory

            self.factory = ClientFactory(
                base_url=self.base_url,
                username=self.username,
                password=self.password
            )
            self.core_client = self.factory.create_core_client()
            logger.info("✓ Alfresco authentication successful (python-alfresco-api)")
            return True

        except ImportError:
            # Fallback to REST API authentication
            logger.info("python-alfresco-api not available, using REST API")
            return self._authenticate_rest()
        except Exception as e:
            logger.warning(f"python-alfresco-api auth failed: {e}, falling back to REST API")
            return self._authenticate_rest()

    def _authenticate_rest(self) -> Optional[str]:
        """
        Authenticate using Alfresco REST API directly.

        Returns:
            Authentication ticket or None
        """
        try:
            auth_url = f"{self.base_url}/api/-default-/public/authentication/versions/1/tickets"
            response = requests.post(
                auth_url,
                json={
                    "userId": self.username,
                    "password": self.password
                },
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 201:
                self.ticket = response.json().get('entry', {}).get('id')
                logger.info("✓ Alfresco authentication successful (REST API)")
                return self.ticket
            else:
                logger.error(f"Alfresco auth failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"REST API authentication error: {e}")
            return None

    def get_all_contracts(self, folder_id: str = "-root-") -> List[Dict[str, Any]]:
        """
        Fetch all contract documents from a specific Alfresco folder.

        Args:
            folder_id: Alfresco folder node ID (default: -root-)

        Returns:
            List of contract documents with metadata and content
        """
        contracts = []

        try:
            # Use REST API directly since python-alfresco-api has compatibility issues
            # Try using python-alfresco-api first
            # if hasattr(self, 'core_client'):
            #     return self._get_contracts_via_api(folder_id)
            # else:
            #     return self._get_contracts_via_rest(folder_id)

            # Always use REST API for now
            return self._get_contracts_via_rest(folder_id)

        except Exception as e:
            logger.error(f"Error fetching contracts from Alfresco: {e}")
            return []

    def _get_contracts_via_api(self, folder_id: str) -> List[Dict[str, Any]]:
        """
        Fetch contracts using python-alfresco-api library.

        Args:
            folder_id: Alfresco folder node ID

        Returns:
            List of contract documents
        """
        contracts = []

        try:
            # Get children nodes from folder
            nodes_response = self.core_client.nodes.list_children(folder_id)

            for entry in nodes_response.list.entries:
                node = entry.entry

                # Only process files (not folders)
                if node.is_file:
                    try:
                        # Get file content
                        content_response = self.core_client.nodes.get_content(node.id)

                        contracts.append({
                            "id": node.id,
                            "name": node.name,
                            "content": content_response.content,  # Binary data
                            "metadata": {
                                "id": node.id,
                                "name": node.name,
                                "content_type": getattr(node, 'content', {}).get('mimeType', 'application/octet-stream'),
                                "size": getattr(node, 'content', {}).get('sizeInBytes', 0),
                                "created_at": str(node.created_at) if hasattr(node, 'created_at') else None,
                                "modified_at": str(node.modified_at) if hasattr(node, 'modified_at') else None,
                                "created_by": getattr(node, 'created_by_user', {}).get('displayName', 'Unknown'),
                                "properties": node.properties if hasattr(node, 'properties') else {},
                                "version": getattr(node, 'version', {}).get('label', '1.0'),
                            }
                        })

                        logger.info(f"✓ Fetched: {node.name} ({node.id})")

                    except Exception as e:
                        logger.error(f"Error fetching content for {node.name}: {e}")

        except Exception as e:
            logger.error(f"Error in _get_contracts_via_api: {e}")

        return contracts

    def _get_contracts_via_rest(self, folder_id: str) -> List[Dict[str, Any]]:
        """
        Fetch contracts using Alfresco REST API directly.

        Args:
            folder_id: Alfresco folder node ID

        Returns:
            List of contract documents
        """
        contracts = []

        try:
            # List folder children - use basic auth with session
            list_url = f"{self.base_url}/api/-default-/public/alfresco/versions/1/nodes/{folder_id}/children"
            logger.info(f"Fetching from Alfresco: {list_url}")

            # Use basic auth (username:password) if ticket auth fails
            response = self.session.get(list_url)
            logger.info(f"Alfresco response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                entries = data.get('list', {}).get('entries', [])

                for item in entries:
                    entry = item.get('entry', {})

                    # Only process files
                    if entry.get('isFile', False):
                        node_id = entry.get('id')

                        # Download file content using basic auth
                        content_url = f"{self.base_url}/api/-default-/public/alfresco/versions/1/nodes/{node_id}/content"
                        content_response = self.session.get(content_url)

                        if content_response.status_code == 200:
                            contracts.append({
                                "id": node_id,
                                "name": entry.get('name', 'Unknown'),
                                "content": content_response.content,
                                "metadata": {
                                    "id": node_id,
                                    "name": entry.get('name', 'Unknown'),
                                    "content_type": entry.get('content', {}).get('mimeType', 'application/octet-stream'),
                                    "size": entry.get('content', {}).get('sizeInBytes', 0),
                                    "created_at": entry.get('createdAt'),
                                    "modified_at": entry.get('modifiedAt'),
                                    "created_by": entry.get('createdByUser', {}).get('displayName', 'Unknown'),
                                    "properties": entry.get('properties', {}),
                                    "version": entry.get('properties', {}).get('cm:versionLabel', '1.0'),
                                }
                            })

                            logger.info(f"✓ Fetched via REST: {entry.get('name')} ({node_id})")
            else:
                logger.error(f"Failed to list folder: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error in _get_contracts_via_rest: {e}")

        return contracts

    def get_document_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific document by its Alfresco node ID.

        Args:
            node_id: Alfresco node ID

        Returns:
            Document data or None
        """
        try:
            if hasattr(self, 'core_client'):
                # Using API client - try new API format first
                try:
                    content_response = self.core_client.nodes.get_content(node_id)
                    # Get node metadata separately
                    nodes_list = self.core_client.nodes.list_children('-root-')
                    node = None
                    for entry in nodes_list.list.entries:
                        if entry.entry.id == node_id:
                            node = entry.entry
                            break

                    if not node:
                        raise Exception(f"Node {node_id} not found")

                except:
                    # Fallback to REST API
                    raise Exception("API client method failed")

                return {
                    "id": node.entry.id,
                    "name": node.entry.name,
                    "content": content_response.content,
                    "metadata": {
                        "id": node.entry.id,
                        "name": node.entry.name,
                        "content_type": getattr(node.entry, 'content', {}).get('mimeType', 'application/octet-stream'),
                        "size": getattr(node.entry, 'content', {}).get('sizeInBytes', 0),
                        "properties": node.entry.properties if hasattr(node.entry, 'properties') else {},
                    }
                }
            else:
                # Using REST API
                if not self.ticket:
                    return None

                headers = {'Authorization': f'Basic {self.ticket}'}
                content_url = f"{self.base_url}/api/-default-/public/alfresco/versions/1/nodes/{node_id}/content"
                metadata_url = f"{self.base_url}/api/-default-/public/alfresco/versions/1/nodes/{node_id}"

                # Get metadata
                meta_response = self.session.get(metadata_url, headers=headers)
                content_response = self.session.get(content_url, headers=headers)

                if meta_response.status_code == 200 and content_response.status_code == 200:
                    entry = meta_response.json().get('entry', {})

                    return {
                        "id": node_id,
                        "name": entry.get('name', 'Unknown'),
                        "content": content_response.content,
                        "metadata": {
                            "id": node_id,
                            "name": entry.get('name'),
                            "content_type": entry.get('content', {}).get('mimeType'),
                            "size": entry.get('content', {}).get('sizeInBytes', 0),
                            "properties": entry.get('properties', {}),
                        }
                    }

        except Exception as e:
            logger.error(f"Error fetching document {node_id}: {e}")

        return None

    def search_contracts(self, query: str, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for contracts in Alfresco using a query string.

        Args:
            query: Search query (e.g., "contract AND type:agreement")
            folder_id: Optional folder to search within

        Returns:
            List of matching documents
        """
        try:
            if hasattr(self, 'core_client') and hasattr(self.core_client, 'search'):
                # Use search API if available
                search_body = {
                    "query": {
                        "query": query,
                        "language": "afts"  # Alfresco Full Text Search
                    }
                }

                if folder_id:
                    search_body["scope"] = {
                        "locations": [f"nodes/{folder_id}"]
                    }

                results = self.core_client.search.search(search_body)

                # Process results similar to get_all_contracts
                return self._process_search_results(results)
            else:
                logger.warning("Search API not available, falling back to folder listing")
                return self.get_all_contracts(folder_id or "-root-")

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def _process_search_results(self, results: Any) -> List[Dict[str, Any]]:
        """Process search results from Alfresco."""
        contracts = []

        try:
            entries = results.list.entries if hasattr(results, 'list') else []

            for item in entries:
                entry = item.entry if hasattr(item, 'entry') else item

                if entry.get('isFile', False):
                    node_id = entry.get('id')

                    # Fetch full content
                    doc = self.get_document_by_id(node_id)
                    if doc:
                        contracts.append(doc)
        except Exception as e:
            logger.error(f"Error processing search results: {e}")

        return contracts

    def _check_api_health(self) -> Dict[str, Any]:
        """Helper method to check health using python-alfresco-api."""
        self.core_client.nodes.list_children('-root-')
        return {
            "status": "healthy",
            "method": "python-alfresco-api",
            "message": "Successfully connected to Alfresco"
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Check if Alfresco connection is healthy with timeout.

        Returns:
            Health status dict
        """
        try:
            # Try to access root node with timeout
            if hasattr(self, 'core_client'):
                try:
                    # Use ThreadPoolExecutor with timeout for API call
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self._check_api_health)
                        try:
                            result = future.result(timeout=3)
                            return result
                        except concurrent.futures.TimeoutError:
                            logger.warning("python-alfresco-api health check timed out")
                            raise Exception("Connection timeout")

                except Exception as api_error:
                    logger.warning(f"python-alfresco-api connection test failed: {api_error}")
                    # Fall through to REST API test - try to get ticket if we don't have one
                    if not self.ticket:
                        self._authenticate_rest()

            # Try REST API with ticket
            if self.ticket:
                headers = {'Authorization': f'Basic {self.ticket}'}
                url = f"{self.base_url}/api/-default-/public/alfresco/versions/1/nodes/-root-"
                response = self.session.get(url, headers=headers, timeout=3)

                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "method": "REST API",
                        "message": "Successfully connected to Alfresco"
                    }

            # Try with basic auth as last resort
            url = f"{self.base_url}/api/-default-/public/alfresco/versions/1/nodes/-root-"
            response = requests.get(url, auth=(self.username, self.password), timeout=3)

            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "method": "REST API (Basic Auth)",
                    "message": "Successfully connected to Alfresco"
                }

            return {
                "status": "unhealthy",
                "method": "none",
                "message": "Not authenticated with Alfresco"
            }

        except requests.Timeout:
            logger.error("Alfresco health check timed out")
            return {
                "status": "unhealthy",
                "method": "timeout",
                "message": "Connection timeout - Alfresco server not responding"
            }
        except Exception as e:
            logger.error(f"Alfresco health check error: {e}")
            return {
                "status": "unhealthy",
                "method": "error",
                "message": f"Connection error: {str(e)}"
            }
