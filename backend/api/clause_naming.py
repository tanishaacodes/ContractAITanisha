import os
"""
Clause Naming Module
Uses Qwen LLM to generate semantic names for clause clusters
"""

import requests
import logging
import json

logger = logging.getLogger(__name__)


class ClauseNamer:
    """
    Generates semantic names for clause clusters using LLM
    """

    def __init__(self, ollama_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")):
        """
        Initialize the clause namer

        Args:
            ollama_url: URL for Ollama API
        """
        self.ollama_url = ollama_url
        self.model = "qwen2.5:0.5b"

    def name_clause_group(self, clauses, max_clauses=3):
        """
        Generate a semantic name for a group of similar clauses using LLM

        Args:
            clauses: List of clause texts
            max_clauses: Maximum number of clauses to include in prompt

        Returns:
            Generated clause category name
        """
        try:
            if not clauses:
                return "Miscellaneous Clause"

            # Limit clauses for prompt
            sample_clauses = clauses[:max_clauses]

            # Create prompt
            prompt = self._create_naming_prompt(sample_clauses)

            # Call LLM
            response = self._call_ollama(prompt)

            # Extract and clean the name
            clause_name = self._extract_clause_name(response)

            logger.info(f"Generated clause name: {clause_name}")
            return clause_name

        except Exception as e:
            logger.error(f"Failed to generate clause name: {e}")
            # Return a generic name on failure
            return self._generate_fallback_name(clauses)

    def _create_naming_prompt(self, clauses):
        """
        Create prompt for LLM clause naming

        Args:
            clauses: List of clause texts

        Returns:
            Prompt string
        """
        clauses_text = "\n\n".join([f"Clause {i+1}: {c[:300]}" for i, c in enumerate(clauses)])

        prompt = f"""You are a legal AI assistant specialized in contract analysis.

Below are similar clauses from a contract. Analyze them and provide a SHORT, PRECISE legal clause category name (2-5 words maximum).

The name should be:
- Professional and legal terminology
- Descriptive of the clause's purpose
- Concise (like "Payment Terms", "Indemnification", "Confidentiality Obligations", etc.)

Clauses:
{clauses_text}

Return ONLY the clause category name, nothing else. No explanation, no punctuation at the end.

Clause Category Name:"""

        return prompt

    def _call_ollama(self, prompt, timeout=30):
        """
        Call Ollama API to generate text

        Args:
            prompt: Prompt text
            timeout: Request timeout in seconds

        Returns:
            Generated text response
        """
        try:
            url = f"{self.ollama_url}/api/generate"

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more focused responses
                    "num_predict": 20,   # Limit output length
                }
            }

            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()

            result = response.json()
            return result.get('response', '').strip()

        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama: {e}")
            raise

    def _extract_clause_name(self, llm_response):
        """
        Extract and clean clause name from LLM response

        Args:
            llm_response: Raw LLM response

        Returns:
            Cleaned clause name
        """
        if not llm_response:
            return "General Provision"

        # Clean the response
        name = llm_response.strip()

        # Remove common prefixes
        prefixes_to_remove = [
            "Clause Category Name:",
            "Category:",
            "Name:",
            "The clause category name is",
            "This is a",
        ]

        for prefix in prefixes_to_remove:
            if name.lower().startswith(prefix.lower()):
                name = name[len(prefix):].strip()

        # Remove quotes
        name = name.strip('"').strip("'")

        # Capitalize properly
        name = self._capitalize_clause_name(name)

        # Truncate if too long
        if len(name) > 50:
            name = name[:47] + "..."

        # Fallback if empty
        if not name:
            name = "General Provision"

        return name

    def _capitalize_clause_name(self, name):
        """
        Properly capitalize clause name

        Args:
            name: Raw name string

        Returns:
            Properly capitalized name
        """
        # Words that should not be capitalized (unless first word)
        lowercase_words = {'and', 'or', 'of', 'the', 'in', 'to', 'for', 'a', 'an', 'on', 'at', 'by'}

        words = name.split()
        if not words:
            return name

        # Capitalize first word always
        capitalized = [words[0].capitalize()]

        # Process remaining words
        for word in words[1:]:
            if word.lower() in lowercase_words:
                capitalized.append(word.lower())
            else:
                capitalized.append(word.capitalize())

        return ' '.join(capitalized)

    def _generate_fallback_name(self, clauses):
        """
        Generate a fallback name using keyword extraction

        Args:
            clauses: List of clause texts

        Returns:
            Fallback clause name
        """
        # Common legal keywords
        legal_keywords = {
            'payment': 'Payment Terms',
            'confidential': 'Confidentiality',
            'termination': 'Termination Provisions',
            'indemnif': 'Indemnification',
            'liabilit': 'Limitation of Liability',
            'warran': 'Warranties',
            'intellectual property': 'Intellectual Property Rights',
            'dispute': 'Dispute Resolution',
            'governing law': 'Governing Law',
            'force majeure': 'Force Majeure',
            'assignment': 'Assignment and Transfer',
            'notice': 'Notice Requirements',
            'amendment': 'Amendment Procedures',
            'severab': 'Severability',
            'entire agreement': 'Entire Agreement',
        }

        # Combine all clause text
        combined_text = ' '.join(clauses).lower()

        # Find matching keywords
        for keyword, name in legal_keywords.items():
            if keyword in combined_text:
                return name

        return "General Contractual Provision"

    def batch_name_clause_groups(self, clause_groups):
        """
        Generate names for multiple clause groups

        Args:
            clause_groups: Dictionary mapping cluster labels to clause lists

        Returns:
            Dictionary mapping cluster labels to generated names
        """
        names = {}

        for label, clauses in clause_groups.items():
            try:
                name = self.name_clause_group(clauses)
                names[label] = name
            except Exception as e:
                logger.error(f"Failed to name cluster {label}: {e}")
                names[label] = self._generate_fallback_name(clauses)

        return names


# Singleton instance
_namer = None


def get_clause_namer():
    """Get or create singleton ClauseNamer instance"""
    global _namer
    if _namer is None:
        _namer = ClauseNamer()
    return _namer
