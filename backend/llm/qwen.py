import os
"""
Qwen LLM Integration Module
============================
Integration with Qwen language model via Ollama for clause analysis and naming.

This module provides functionality to:
- Generate meaningful names for clause groups
- Summarize clause content
- Analyze clause types and categories
"""

import requests
import logging
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)


class QwenClient:
    """
    Client for interacting with Qwen LLM via Ollama API.
    """

    def __init__(self, base_url: str = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")), model: str = "qwen2.5:0.5b"):
        """
        Initialize the Qwen client.

        Args:
            base_url (str): Ollama server URL (default: http://localhost:11434)
            model (str): Qwen model to use (default: qwen2.5:0.5b)
                        Available models:
                        - qwen2.5:0.5b (fastest, smallest)
                        - qwen2.5:1.5b (balanced)
                        - qwen2.5:3b (better quality)
                        - qwen2.5:7b (best quality, slower)
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.generate_url = f"{self.base_url}/api/generate"
        self.chat_url = f"{self.base_url}/api/chat"

    def _call_generate_api(self, prompt: str, temperature: float = 0.3, max_tokens: int = 100) -> str:
        """
        Call Ollama generate API.

        Args:
            prompt (str): The prompt to send to the model
            temperature (float): Sampling temperature (0-1, lower = more focused)
            max_tokens (int): Maximum tokens to generate

        Returns:
            str: Generated text response
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }

            logger.debug(f"Calling Ollama API with model: {self.model}")
            response = requests.post(self.generate_url, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            generated_text = result.get("response", "").strip()

            logger.debug(f"Generated response: {generated_text[:100]}...")
            return generated_text

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama API: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error in Qwen generation: {e}")
            return ""

    def name_clause_group(self, clauses: List[str], max_clauses_to_show: int = 3) -> str:
        """
        Generate a concise, meaningful name for a group of similar clauses.

        Args:
            clauses (List[str]): List of clause texts in the group
            max_clauses_to_show (int): Number of example clauses to show (default: 3)

        Returns:
            str: Generated clause type name (e.g., "Payment Terms", "Liability Provisions")

        Example:
            >>> client = QwenClient()
            >>> clauses = ["Payment shall be made within 30 days...", "Invoice payment terms..."]
            >>> name = client.name_clause_group(clauses)
            >>> name
            'Payment Terms'
        """
        if not clauses:
            return "General Provisions"

        # Take up to max_clauses_to_show examples
        example_clauses = clauses[:max_clauses_to_show]

        # Create concise prompt
        prompt = f"""You are a legal contract analyst. Given the following contract clauses, provide a SHORT, professional name for this clause type.

Clauses:
{chr(10).join(f"- {clause[:150]}..." for clause in example_clauses)}

Respond with ONLY the clause type name (2-4 words). Examples: "Payment Terms", "Liability Provisions", "Termination Conditions", "Confidentiality Obligations".

Clause Type Name:"""

        response = self._call_generate_api(prompt, temperature=0.2, max_tokens=20)

        # Clean up response
        response = response.strip().strip('"').strip("'")

        # Fallback if response is empty or too long
        if not response or len(response) > 50:
            return "General Provisions"

        # Capitalize properly
        response = ' '.join(word.capitalize() for word in response.split())

        return response

    def generate_clause_summary(self, clause_text: str, max_length: int = 100) -> str:
        """
        Generate a concise summary of a clause.

        Args:
            clause_text (str): The full clause text
            max_length (int): Maximum length of summary in words

        Returns:
            str: Summary of the clause

        Example:
            >>> client = QwenClient()
            >>> summary = client.generate_clause_summary(long_clause_text)
            >>> summary
            'This clause establishes payment terms requiring net-30 day payment...'
        """
        if not clause_text:
            return ""

        # Truncate very long clauses for the prompt
        truncated_text = clause_text[:1000] + ("..." if len(clause_text) > 1000 else "")

        prompt = f"""Summarize the following contract clause in 1-2 sentences:

Clause:
{truncated_text}

Summary:"""

        response = self._call_generate_api(prompt, temperature=0.3, max_tokens=max_length)
        return response.strip()

    def classify_clause_type(self, clause_text: str) -> Dict[str, any]:
        """
        Classify a clause into a legal category with confidence.

        Args:
            clause_text (str): The clause text to classify

        Returns:
            Dict: Classification result with 'type', 'confidence', 'explanation'

        Example:
            >>> client = QwenClient()
            >>> result = client.classify_clause_type(clause_text)
            >>> result
            {'type': 'Payment', 'confidence': 0.95, 'explanation': '...'}
        """
        if not clause_text:
            return {'type': 'Unknown', 'confidence': 0.0, 'explanation': ''}

        truncated_text = clause_text[:500] + ("..." if len(clause_text) > 500 else "")

        prompt = f"""Classify this contract clause into ONE of these categories:
- Payment
- Termination
- Liability
- Confidentiality
- Intellectual Property
- Warranty
- Dispute Resolution
- Force Majeure
- Governing Law
- General

Clause:
{truncated_text}

Respond with ONLY the category name:"""

        response = self._call_generate_api(prompt, temperature=0.1, max_tokens=10)
        clause_type = response.strip()

        # Validate response
        valid_types = [
            'Payment', 'Termination', 'Liability', 'Confidentiality',
            'Intellectual Property', 'Warranty', 'Dispute Resolution',
            'Force Majeure', 'Governing Law', 'General'
        ]

        if clause_type not in valid_types:
            clause_type = 'General'

        return {
            'type': clause_type,
            'confidence': 0.85,  # Placeholder - could use model confidence if available
            'explanation': f'Classified as {clause_type} based on content analysis'
        }

    def analyze_clause_risk(self, clause_text: str) -> Dict[str, any]:
        """
        Analyze potential risks in a clause.

        Args:
            clause_text (str): The clause text to analyze

        Returns:
            Dict: Risk analysis with 'risk_level', 'concerns', 'recommendations'
        """
        if not clause_text:
            return {
                'risk_level': 'UNKNOWN',
                'concerns': [],
                'recommendations': []
            }

        truncated_text = clause_text[:800] + ("..." if len(clause_text) > 800 else "")

        prompt = f"""Analyze this contract clause for potential risks. Identify the risk level (LOW, MEDIUM, HIGH) and key concerns.

Clause:
{truncated_text}

Risk Level (LOW/MEDIUM/HIGH):"""

        response = self._call_generate_api(prompt, temperature=0.4, max_tokens=50)

        # Parse response for risk level
        risk_level = 'MEDIUM'  # Default
        response_upper = response.upper()
        if 'HIGH' in response_upper:
            risk_level = 'HIGH'
        elif 'LOW' in response_upper:
            risk_level = 'LOW'

        return {
            'risk_level': risk_level,
            'concerns': [response.strip()],
            'recommendations': []
        }

    def batch_name_clause_groups(self, clause_groups: Dict[int, List[str]]) -> Dict[int, str]:
        """
        Name multiple clause groups efficiently.

        Args:
            clause_groups (Dict[int, List[str]]): Map of cluster_id -> list of clauses

        Returns:
            Dict[int, str]: Map of cluster_id -> clause type name

        Example:
            >>> groups = {0: ['payment clause 1', 'payment clause 2'], 1: ['termination clause']}
            >>> names = client.batch_name_clause_groups(groups)
            >>> names
            {0: 'Payment Terms', 1: 'Termination Conditions'}
        """
        names = {}
        for cluster_id, clauses in clause_groups.items():
            logger.info(f"Naming cluster {cluster_id} with {len(clauses)} clauses")
            name = self.name_clause_group(clauses)
            names[cluster_id] = name
            logger.info(f"Cluster {cluster_id} named: {name}")

        return names

    def check_ollama_connection(self) -> bool:
        """
        Check if Ollama server is running and accessible.

        Returns:
            bool: True if server is accessible, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            logger.info("Ollama server is accessible")
            return True
        except Exception as e:
            logger.error(f"Cannot connect to Ollama server: {e}")
            return False


# Module-level singleton instance
_default_client = None


def get_qwen_client(base_url: str = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")), model: str = "qwen2.5:0.5b") -> QwenClient:
    """
    Get or create the default Qwen client instance (singleton pattern).

    Args:
        base_url (str): Ollama server URL
        model (str): Qwen model name

    Returns:
        QwenClient: The client instance
    """
    global _default_client
    if _default_client is None:
        _default_client = QwenClient(base_url, model)
    return _default_client


def name_clause_group(clauses: List[str]) -> str:
    """
    Convenience function to name a clause group using the default client.

    Args:
        clauses (List[str]): List of clause texts

    Returns:
        str: Generated clause type name

    Example:
        >>> from llm.qwen import name_clause_group
        >>> name = name_clause_group(['payment clause 1', 'payment clause 2'])
        >>> name
        'Payment Terms'
    """
    client = get_qwen_client()
    return client.name_clause_group(clauses)


def generate_clause_summary(clause_text: str) -> str:
    """
    Convenience function to summarize a clause using the default client.

    Args:
        clause_text (str): The clause text

    Returns:
        str: Summary of the clause
    """
    client = get_qwen_client()
    return client.generate_clause_summary(clause_text)
