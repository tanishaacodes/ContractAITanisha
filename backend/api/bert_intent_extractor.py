import os
"""
Contracts-BERT Intent Extraction for Classification
===================================================
Extracts legal intents from contract chunks using LLM-based classification.
Used in fusion with BERTopic for high-accuracy contract classification.
"""

import requests
import json
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class BERTIntentExtractor:
    """Extract legal intents from contract text chunks"""

    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")) + "/api/generate"
        self.model_name = "qwen2.5:0.5b"

        # Standard legal intent categories for classification
        self.intent_categories = [
            "Payment",
            "Delivery",
            "Services",
            "Liability",
            "Indemnity",
            "Termination",
            "Confidentiality",
            "Intellectual Property",
            "Warranties",
            "Dispute Resolution",
            "Governing Law",
            "Force Majeure",
            "Amendment",
            "Assignment",
            "Notice"
        ]

    def extract_intents_from_text(self, text: str) -> Dict[str, float]:
        """
        Extract intent distribution from full contract text.
        Splits into chunks and aggregates intent weights.

        Args:
            text: Full contract text

        Returns:
            Dict mapping intent names to normalized weights (0-1)
            Example: {"Payment": 0.35, "Termination": 0.20, ...}
        """
        # Split into manageable chunks (paragraphs)
        chunks = self._split_into_chunks(text)

        if not chunks:
            logger.warning("No valid chunks found in contract text")
            return {}

        # Extract intent from each chunk
        chunk_intents = []
        for chunk in chunks[:20]:  # Limit to first 20 chunks for speed
            intent = self._extract_intent_from_chunk(chunk)
            if intent:
                chunk_intents.append(intent)

        # Aggregate intents across all chunks
        intent_distribution = self._aggregate_intents(chunk_intents)

        return intent_distribution

    def _split_into_chunks(self, text: str) -> List[str]:
        """Split text into meaningful chunks (paragraphs/clauses)"""
        # Split by double newlines or numbered clauses
        chunks = [
            p.strip()
            for p in text.split('\n')
            if len(p.strip()) > 50  # Only keep substantial paragraphs
        ]
        return chunks

    def _extract_intent_from_chunk(self, chunk: str) -> Dict[str, float]:
        """
        Extract primary legal intent from a single chunk using LLM.

        Args:
            chunk: Text chunk (clause/paragraph)

        Returns:
            Dict with intent name and confidence
            Example: {"intent": "Payment", "confidence": 0.85}
        """
        # Try Ollama first
        if self._is_ollama_available():
            result = self._extract_with_ollama(chunk)
            if result:
                return result

        # Fallback to keyword matching
        return self._extract_with_keywords(chunk)

    def _extract_with_ollama(self, chunk: str) -> Dict[str, float]:
        """Extract intent using Ollama LLM"""
        prompt = f"""Analyze this contract clause and identify its PRIMARY legal intent category.

CLAUSE: {chunk[:500]}

Choose ONE category from:
{', '.join(self.intent_categories)}

Respond ONLY with valid JSON:
{{"intent": "category name", "confidence": 0.85}}

JSON Response:"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()

                # Extract JSON
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}") + 1

                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    intent_data = json.loads(json_str)

                    if 'intent' in intent_data and 'confidence' in intent_data:
                        return {
                            "intent": intent_data['intent'],
                            "confidence": float(intent_data['confidence'])
                        }

        except Exception as e:
            logger.debug(f"Ollama extraction failed: {str(e)}")

        return None

    def _extract_with_keywords(self, chunk: str) -> Dict[str, float]:
        """Fallback keyword-based intent detection"""
        chunk_lower = chunk.lower()

        # Keyword mappings for each intent
        intent_keywords = {
            "Payment": ["payment", "invoice", "fee", "price", "cost", "compensation", "remuneration"],
            "Delivery": ["deliver", "shipment", "shipping", "goods", "products", "fulfillment"],
            "Services": ["services", "perform", "provide", "work", "duties", "tasks"],
            "Liability": ["liable", "liability", "damages", "losses", "responsible"],
            "Indemnity": ["indemnify", "indemnification", "hold harmless", "defend"],
            "Termination": ["terminate", "termination", "cancel", "end", "expiration"],
            "Confidentiality": ["confidential", "proprietary", "secret", "disclosure"],
            "Intellectual Property": ["intellectual property", "patent", "copyright", "trademark", "ip"],
            "Warranties": ["warrant", "warranty", "represent", "guarantee"],
            "Dispute Resolution": ["dispute", "arbitration", "mediation", "litigation"],
            "Governing Law": ["governing law", "jurisdiction", "applicable law"],
            "Force Majeure": ["force majeure", "act of god", "unforeseeable"],
            "Amendment": ["amend", "amendment", "modify", "modification", "change"],
            "Assignment": ["assign", "assignment", "transfer"],
            "Notice": ["notice", "notify", "notification", "inform"]
        }

        # Score each intent based on keyword matches
        scores = {}
        for intent, keywords in intent_keywords.items():
            score = sum(1 for kw in keywords if kw in chunk_lower)
            if score > 0:
                scores[intent] = score

        if scores:
            # Return intent with highest score
            best_intent = max(scores, key=scores.get)
            confidence = min(0.6, scores[best_intent] * 0.1)  # Cap at 0.6 for keyword matching

            return {
                "intent": best_intent,
                "confidence": confidence
            }

        return {"intent": "General", "confidence": 0.3}

    def _aggregate_intents(self, chunk_intents: List[Dict]) -> Dict[str, float]:
        """
        Aggregate intents across multiple chunks into weighted distribution.

        Args:
            chunk_intents: List of {"intent": str, "confidence": float}

        Returns:
            Normalized distribution: {"Payment": 0.35, "Termination": 0.20, ...}
        """
        if not chunk_intents:
            return {}

        # Sum confidence scores by intent
        intent_scores = {}
        for item in chunk_intents:
            intent = item.get('intent', 'General')
            confidence = item.get('confidence', 0.5)

            intent_scores[intent] = intent_scores.get(intent, 0) + confidence

        # Normalize to sum to 1.0
        total_score = sum(intent_scores.values())
        if total_score > 0:
            normalized = {
                intent: round(score / total_score, 3)
                for intent, score in intent_scores.items()
            }
            return normalized

        return {}

    def _is_ollama_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")) + "/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(self.model_name in m.get("name", "") for m in models)
            return False
        except:
            return False


# Singleton instance
_bert_extractor = None

def get_bert_extractor() -> BERTIntentExtractor:
    """Get or create singleton BERTIntentExtractor instance"""
    global _bert_extractor
    if _bert_extractor is None:
        _bert_extractor = BERTIntentExtractor()
    return _bert_extractor
