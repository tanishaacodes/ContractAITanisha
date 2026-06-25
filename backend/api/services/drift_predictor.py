"""
Clause Drift Prediction Service
Uses MiniLM embeddings + cosine similarity to detect clause drift
and Qwen LLM to predict future clause evolution.
"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
import requests
import numpy as np
import logging

logger = logging.getLogger(__name__)


class DriftPredictorService:
    """
    Clause-level drift prediction using embedding similarity.
    """

    def __init__(self):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
        self.ollama_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')

    def predict_drift(self, original_text, current_text):
        """
        Calculate drift probability between two clause versions.

        Args:
            original_text: Original clause text
            current_text: Current/modified clause text

        Returns:
            float: Drift probability (0-1), where 1 = complete drift
        """
        try:
            if not original_text or not current_text:
                return 0.0

            # Encode both texts
            e1 = self.embedder.encode(original_text)
            e2 = self.embedder.encode(current_text)

            # Calculate cosine similarity
            similarity = cosine_similarity([e1], [e2])[0][0]

            # Convert similarity to drift probability
            # similarity = 1.0 → drift = 0.0 (no drift)
            # similarity = 0.0 → drift = 1.0 (complete drift)
            drift_prob = 1 - similarity

            return round(float(drift_prob), 3)

        except Exception as e:
            logger.error(f"Error calculating drift: {e}")
            return 0.5  # Default to medium drift on error

    def calculate_volatility_index(self, clause_versions):
        """
        Calculate volatility index based on historical clause versions.

        Args:
            clause_versions: List of clause text versions (oldest to newest)

        Returns:
            float: Volatility index (0-1), where 1 = highly volatile
        """
        try:
            if len(clause_versions) < 2:
                return 0.0

            # Encode all versions
            embeddings = [self.embedder.encode(text) for text in clause_versions]

            # Calculate pairwise drift scores
            drift_scores = []
            for i in range(len(embeddings) - 1):
                similarity = cosine_similarity([embeddings[i]], [embeddings[i+1]])[0][0]
                drift = 1 - similarity
                drift_scores.append(drift)

            # Volatility = average drift + std deviation of drifts
            avg_drift = np.mean(drift_scores)
            std_drift = np.std(drift_scores)
            volatility = min(1.0, avg_drift + (std_drift * 0.5))

            return round(float(volatility), 3)

        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return 0.0

    def predict_future_clause(self, current_text, clause_type=None, context=None):
        """
        Use Qwen LLM to predict likely future clause evolution.

        Args:
            current_text: Current clause text
            clause_type: Type of clause (e.g., "Limitation of Liability")
            context: Additional context about the contract

        Returns:
            str: Predicted future clause text or None on failure
        """
        try:
            prompt = self._build_prediction_prompt(current_text, clause_type, context)

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "qwen2.5:0.5b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,  # Slightly creative but controlled
                        "max_tokens": 300
                    }
                },
                timeout=45
            )

            if response.status_code == 200:
                predicted = response.json().get('response', '').strip()

                # If LLM produces nothing useful, return fallback
                if not predicted or len(predicted) < 20:
                    return self._fallback_prediction(current_text, clause_type)

                return predicted
            else:
                logger.warning(f"Qwen prediction failed: {response.status_code}")
                return self._fallback_prediction(current_text, clause_type)

        except Exception as e:
            logger.error(f"Error predicting future clause: {e}")
            return self._fallback_prediction(current_text, clause_type)

    def _build_prediction_prompt(self, current_text, clause_type, context):
        """Build LLM prompt for clause prediction."""
        prompt = f"""You are a legal contract analyst. Predict how this clause might evolve in future negotiations.

Current Clause Type: {clause_type or 'Unknown'}
Current Text: {current_text}

Based on common negotiation patterns and legal trends, predict the likely future version of this clause. Focus on:
1. More favorable terms for one party
2. Additional protections or limitations
3. Industry-standard modifications

Predicted Future Clause:"""

        if context:
            prompt = prompt.replace("Current Text:", f"Context: {context}\n\nCurrent Text:")

        return prompt

    def _fallback_prediction(self, current_text, clause_type):
        """
        Rule-based fallback when LLM is unavailable.
        """
        fallbacks = {
            "Limitation of Liability": "Liability shall be limited to the total contract value, excluding consequential, indirect, or punitive damages.",
            "Indemnity": "Each party shall indemnify the other for claims arising from their respective negligence or willful misconduct.",
            "Termination": "Either party may terminate with 90 days written notice. Immediate termination is allowed for material breach.",
            "Payment Terms": "Payment due within 45 days of invoice receipt. Late payments incur 2% monthly interest.",
            "Confidentiality": "Confidential information must be protected for 5 years post-termination using industry-standard security measures."
        }

        for key, fallback_text in fallbacks.items():
            if clause_type and key.lower() in clause_type.lower():
                return f"{current_text} [Predicted: {fallback_text}]"

        # Generic fallback
        return f"{current_text} [Predicted: Additional protections and risk mitigation clauses may be added]"

    def calculate_historical_deviation(self, original_text, current_text):
        """
        Calculate percentage deviation from original clause.

        Returns:
            int: Deviation percentage (0-100)
        """
        drift = self.predict_drift(original_text, current_text)
        return int(drift * 100)

    def estimate_counterparty_bias(self, clause_versions, your_party_name=None):
        """
        Estimate counterparty bias in clause evolution.

        This is a placeholder - in production, you'd analyze:
        - Which party benefits more from each version change
        - Patterns of one-sided modifications
        - Removal of protections for one party

        Returns:
            float: Bias score (0-1), where 1 = highly biased toward counterparty
        """
        # Simplified heuristic based on drift volatility
        if len(clause_versions) < 2:
            return 0.0

        volatility = self.calculate_volatility_index(clause_versions)

        # High volatility often indicates back-and-forth negotiation
        # which suggests potential bias
        bias_score = min(0.9, volatility * 1.2)

        return round(float(bias_score), 3)


# Singleton instance
_drift_predictor_instance = None

def get_drift_predictor():
    """Get singleton instance of DriftPredictorService."""
    global _drift_predictor_instance
    if _drift_predictor_instance is None:
        _drift_predictor_instance = DriftPredictorService()
    return _drift_predictor_instance
