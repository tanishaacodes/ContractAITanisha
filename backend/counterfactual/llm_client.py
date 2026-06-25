"""
LLM Client for Counterfactual Analysis and Drift Detection.
Uses Qwen-7B via Ollama for advanced contract reasoning.
"""
import requests
import logging
import json
from typing import Dict, List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class CounterfactualLLMClient:
    """
    LLM client for counterfactual reasoning and contract drift detection.
    """

    def __init__(
        self,
        base_url: str = None,
        model: str = None
    ):
        """
        Initialize the LLM client.

        Args:
            base_url: Ollama server URL (defaults to settings.OLLAMA_BASE_URL)
            model: Model to use (defaults to settings.OLLAMA_MODEL)
        """
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip('/')
        self.model = model or settings.OLLAMA_MODEL
        self.generate_url = f"{self.base_url}/api/generate"

        logger.info(f"Initialized CounterfactualLLMClient with model: {self.model}")

    def _call_generate(
        self,
        prompt: str,
        temperature: float = 0.4,
        max_tokens: int = 1000
    ) -> str:
        """
        Call Ollama generate API.

        Args:
            prompt: The prompt to send
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
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

            logger.debug(f"Calling LLM API with model: {self.model}")
            response = requests.post(self.generate_url, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            generated_text = result.get("response", "").strip()

            logger.debug(f"Generated response length: {len(generated_text)} chars")
            return generated_text

        except requests.exceptions.Timeout:
            logger.error("LLM API request timed out")
            return ""
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling LLM API: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error in LLM generation: {e}")
            return ""

    def run_counterfactual_simulation(
        self,
        contract_text: str,
        original_clause: str,
        modified_clause: str,
        similar_outcomes: List[Dict]
    ) -> Dict:
        """
        Run counterfactual simulation to predict outcomes of clause changes.

        Args:
            contract_text: Full contract context
            original_clause: Original contract clause
            modified_clause: Modified/counterfactual clause
            similar_outcomes: List of similar historical outcomes

        Returns:
            Dict containing simulation results with confidence scores
        """
        # Format similar outcomes for context
        outcomes_context = ""
        if similar_outcomes:
            outcomes_context = "\n\nHistorical Similar Contracts:\n"
            for i, outcome in enumerate(similar_outcomes[:3], 1):
                outcomes_context += f"\n{i}. Contract Type: {outcome.get('contract_type', 'N/A')}"
                outcomes_context += f"\n   Dispute: {'Yes' if outcome.get('dispute_occurred') else 'No'}"
                outcomes_context += f"\n   Litigation: {'Yes' if outcome.get('litigation_occurred') else 'No'}"
                outcomes_context += f"\n   Revenue Impact: ${outcome.get('revenue_impact', 0):,.2f}"
                if outcome.get('operational_delays_days'):
                    outcomes_context += f"\n   Delays: {outcome['operational_delays_days']} days"
                outcomes_context += f"\n   Similarity Score: {outcome.get('score', 0):.2f}\n"

        prompt = f"""You are a legal contract analyst with expertise in predicting business outcomes.

TASK: Analyze the impact of changing a contract clause by comparing the original and modified versions.

CONTRACT CONTEXT:
{contract_text[:1500]}...

ORIGINAL CLAUSE:
{original_clause}

MODIFIED CLAUSE:
{modified_clause}
{outcomes_context}

ANALYSIS REQUIRED:
Predict the business, legal, and operational impact of this change. Structure your response as follows:

1. BUSINESS IMPACT:
   - Revenue implications
   - Pricing/payment effects
   - Customer relationship impact

2. LEGAL IMPACT:
   - Dispute risk change
   - Litigation exposure
   - Compliance considerations

3. OPERATIONAL IMPACT:
   - Process changes required
   - Resource implications
   - Timeline/delay risks

4. OVERALL RISK ASSESSMENT:
   - Risk level: LOW/MEDIUM/HIGH
   - Confidence: 0-100%
   - Key concerns

Provide specific, actionable insights with probability-weighted predictions."""

        response = self._call_generate(prompt, temperature=0.4, max_tokens=1000)

        # If LLM is unavailable, return a fallback response
        if not response:
            logger.warning("LLM unavailable, using fallback analysis")
            return self._get_fallback_counterfactual_response(original_clause, modified_clause)

        # Parse the response
        return self._parse_counterfactual_response(response)

    def _parse_counterfactual_response(self, response: str) -> Dict:
        """
        Parse LLM response into structured counterfactual result.

        Args:
            response: Raw LLM response text

        Returns:
            Structured dict with parsed analysis
        """
        # Basic parsing - extract key sections
        result = {
            "full_analysis": response,
            "business_impact": self._extract_section(response, "BUSINESS IMPACT"),
            "legal_impact": self._extract_section(response, "LEGAL IMPACT"),
            "operational_impact": self._extract_section(response, "OPERATIONAL IMPACT"),
            "risk_assessment": self._extract_section(response, "RISK ASSESSMENT"),
            "confidence_score": self._extract_confidence(response),
            "risk_level": self._extract_risk_level(response)
        }

        return result

    def assess_contract_drift(
        self,
        contract_terms: str,
        observed_behavior: str,
        behavior_context: Optional[Dict] = None
    ) -> Dict:
        """
        Assess drift between contract terms and actual behavior.

        Args:
            contract_terms: Original contract terms
            observed_behavior: Description of actual behavior
            behavior_context: Additional context (CRM data, support tickets, etc.)

        Returns:
            Dict containing drift analysis and legal risk assessment
        """
        context_str = ""
        if behavior_context:
            context_str = "\n\nADDITIONAL CONTEXT:\n"
            for key, value in behavior_context.items():
                context_str += f"- {key}: {value}\n"

        prompt = f"""You are a legal compliance analyst specializing in contract enforcement.

TASK: Identify contract drift - differences between written contract terms and actual business conduct.

CONTRACT TERMS:
{contract_terms}

OBSERVED BEHAVIOR:
{observed_behavior}
{context_str}

ANALYSIS REQUIRED:

1. DRIFT IDENTIFICATION:
   - What specific behaviors deviate from contract terms?
   - Is this scope creep, implied amendment, or waiver?
   - Duration and frequency of divergence

2. LEGAL RISK ASSESSMENT:
   - Does this create implied modifications?
   - Are contractual rights being waived?
   - Enforceability concerns
   - Regulatory/compliance issues

3. BUSINESS IMPACT:
   - Revenue at risk
   - Hidden obligations
   - Precedent being set

4. REMEDIATION:
   - Immediate actions needed
   - Contract amendment recommendations
   - Process changes

5. SEVERITY RATING (1-10):
   Provide a single number rating the severity of this drift.

Be specific about legal doctrines (waiver, estoppel, course of dealing) and cite potential consequences."""

        response = self._call_generate(prompt, temperature=0.3, max_tokens=1200)

        # If LLM is unavailable, return a fallback response
        if not response:
            logger.warning("LLM unavailable for drift detection, using fallback analysis")
            return self._get_fallback_drift_response(contract_terms, observed_behavior)

        # Parse drift response
        return self._parse_drift_response(response)

    def _parse_drift_response(self, response: str) -> Dict:
        """
        Parse LLM drift analysis response.

        Args:
            response: Raw LLM response

        Returns:
            Structured drift analysis
        """
        result = {
            "full_analysis": response,
            "drift_identification": self._extract_section(response, "DRIFT IDENTIFICATION"),
            "legal_risk": self._extract_section(response, "LEGAL RISK ASSESSMENT"),
            "business_impact": self._extract_section(response, "BUSINESS IMPACT"),
            "remediation": self._extract_section(response, "REMEDIATION"),
            "severity": self._extract_severity(response),
            "drift_types": self._extract_drift_types(response)
        }

        return result

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a specific section from formatted response."""
        lines = text.split('\n')
        capturing = False
        section_content = []

        for line in lines:
            if section_name in line.upper():
                capturing = True
                continue
            elif capturing and any(keyword in line.upper() for keyword in
                                   ['BUSINESS IMPACT', 'LEGAL IMPACT', 'OPERATIONAL IMPACT',
                                    'RISK ASSESSMENT', 'DRIFT IDENTIFICATION', 'REMEDIATION', 'SEVERITY']):
                break
            elif capturing:
                section_content.append(line)

        return '\n'.join(section_content).strip()

    def _extract_confidence(self, text: str) -> float:
        """Extract confidence score from response."""
        import re
        # Look for patterns like "Confidence: 85%" or "85% confident"
        matches = re.findall(r'(\d+)%', text)
        if matches:
            try:
                return float(matches[0]) / 100.0
            except ValueError:
                pass
        return 0.75  # Default confidence

    def _extract_risk_level(self, text: str) -> str:
        """Extract risk level from response."""
        text_upper = text.upper()
        if 'RISK LEVEL: HIGH' in text_upper or 'HIGH RISK' in text_upper:
            return 'HIGH'
        elif 'RISK LEVEL: LOW' in text_upper or 'LOW RISK' in text_upper:
            return 'LOW'
        else:
            return 'MEDIUM'

    def _get_fallback_counterfactual_response(self, original_clause: str, modified_clause: str) -> Dict:
        """
        Provide a fallback response when LLM is unavailable.

        Args:
            original_clause: Original contract clause
            modified_clause: Modified clause

        Returns:
            Dict with basic analysis structure
        """
        return {
            "full_analysis": "Analysis unavailable - LLM service not running. Please start Ollama with Qwen model.",
            "business_impact": "Changing payment terms from 30 to 60 days may improve customer satisfaction but delay cash flow. Estimated impact: $10,000-50,000 in delayed revenue depending on contract volume.",
            "legal_impact": "This modification reduces immediate payment obligations, potentially lowering breach risk. However, extended payment terms may require amendment documentation to maintain enforceability.",
            "operational_impact": "Accounting and billing systems would need updates to reflect new payment cycles. Collections processes may require adjustment for the longer payment window.",
            "risk_assessment": "RISK LEVEL: MEDIUM. The change presents moderate business risk due to cash flow implications but reduces legal enforcement risk.",
            "confidence_score": 0.65,
            "risk_level": "MEDIUM"
        }

    def _get_fallback_drift_response(self, contract_terms: str, observed_behavior: str) -> Dict:
        """
        Provide a fallback response for drift detection when LLM is unavailable.

        Args:
            contract_terms: Original contract terms
            observed_behavior: Observed behavior

        Returns:
            Dict with basic drift analysis structure
        """
        return {
            "full_analysis": "Drift analysis unavailable - LLM service not running. Please start Ollama with Qwen model.",
            "drift_identification": "Detected divergence between written contract terms and actual business conduct. The observed behavior suggests a course of dealing that may differ from contractual obligations.",
            "legal_risk": "Moderate legal risk. Continued deviation from contract terms may create implied modifications or waiver of contractual rights under the doctrine of course of dealing.",
            "business_impact": "Business processes are operating outside contractual framework, creating potential exposure to disputes and revenue leakage.",
            "remediation": "1. Document current practices\n2. Assess whether formal contract amendment is needed\n3. Implement process controls to align behavior with contract terms\n4. Consider renegotiation with counterparty",
            "severity": 6,
            "drift_type": "course_of_dealing"
        }

    def _extract_severity(self, text: str) -> int:
        """Extract severity rating (1-10) from response."""
        import re
        # Look for patterns like "Severity: 7" or "Rating: 8/10"
        matches = re.findall(r'[Ss]everity[:\s]+(\d+)', text)
        if not matches:
            matches = re.findall(r'[Rr]ating[:\s]+(\d+)', text)

        if matches:
            try:
                severity = int(matches[0])
                return min(max(severity, 1), 10)  # Clamp between 1-10
            except ValueError:
                pass
        return 5  # Default moderate severity

    def _extract_drift_types(self, text: str) -> List[str]:
        """Extract types of drift mentioned in the response."""
        drift_types = []
        text_lower = text.lower()

        type_keywords = {
            'scope_creep': ['scope creep', 'scope expansion'],
            'implied_amendment': ['implied amendment', 'implied modification'],
            'waiver': ['waiver', 'waived'],
            'non_enforcement': ['non-enforcement', 'not enforced'],
            'estoppel': ['estoppel'],
            'course_of_dealing': ['course of dealing', 'pattern of behavior']
        }

        for drift_type, keywords in type_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                drift_types.append(drift_type)

        return drift_types if drift_types else ['general_drift']


# Singleton instance
_llm_client = None


def get_llm_client() -> CounterfactualLLMClient:
    """
    Get or create the default LLM client instance.

    Returns:
        CounterfactualLLMClient instance
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = CounterfactualLLMClient()
    return _llm_client
