import os
"""
Ollama-based contract classification using Qwen 7B
Provides better, more meaningful contract type labels
"""
import requests
import json
from typing import Dict, Optional


OLLAMA_API_URL = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")) + "/api/generate"
MODEL_NAME = "qwen2.5:7b"


def classify_with_ollama(contract_text: str) -> Dict[str, any]:
    """
    Classify contract using Ollama Qwen 7B model.
    Returns contract type and confidence.
    """
    # Truncate long contracts to first 2000 chars for speed
    text_sample = contract_text[:2000] if len(contract_text) > 2000 else contract_text

    prompt = f"""You are a legal contract classification expert. Analyze this contract excerpt and classify it into ONE of these categories:

Contract Types:
1. Master Service Agreement (MSA)
2. Non-Disclosure Agreement (NDA)
3. Employment Agreement
4. Sales Agreement
5. Vendor Agreement
6. Service Level Agreement (SLA)
7. Consulting Agreement
8. Lease Agreement
9. Partnership Agreement
10. Other

Contract Excerpt:
{text_sample}

Respond in JSON format only:
{{"contractType": "exact category name", "confidence": 0-100, "reasoning": "brief explanation"}}"""

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for consistent classification
                    "top_p": 0.9
                }
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "")

            # Try to extract JSON from response
            try:
                # Find JSON in response
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}") + 1

                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    classification = json.loads(json_str)

                    return {
                        "contractType": classification.get("contractType", "Other"),
                        "confidenceScore": float(classification.get("confidence", 50)),
                        "reasoning": classification.get("reasoning", ""),
                        "source": "ollama"
                    }
                else:
                    # Fallback parsing
                    return parse_fallback(response_text)

            except json.JSONDecodeError:
                return parse_fallback(response_text)
        else:
            return {
                "contractType": "Classification Failed",
                "confidenceScore": 0,
                "reasoning": f"API Error: {response.status_code}",
                "source": "ollama"
            }

    except requests.exceptions.Timeout:
        return {
            "contractType": "Classification Timeout",
            "confidenceScore": 0,
            "reasoning": "Request timed out",
            "source": "ollama"
        }
    except Exception as e:
        return {
            "contractType": "Classification Error",
            "confidenceScore": 0,
            "reasoning": str(e),
            "source": "ollama"
        }


def parse_fallback(text: str) -> Dict:
    """Fallback parser if JSON extraction fails"""
    # Simple keyword matching
    text_lower = text.lower()

    contract_keywords = {
        "Master Service Agreement": ["master service", "msa"],
        "NDA": ["non-disclosure", "nda", "confidentiality"],
        "Employment Agreement": ["employment", "employee", "hire"],
        "Sales Agreement": ["sales", "purchase", "buyer", "seller"],
        "Vendor Agreement": ["vendor", "supplier"],
        "Service Level Agreement": ["sla", "service level"],
        "Consulting Agreement": ["consulting", "consultant"],
        "Lease Agreement": ["lease", "rent", "tenant"],
    }

    for contract_type, keywords in contract_keywords.items():
        if any(kw in text_lower for kw in keywords):
            return {
                "contractType": contract_type,
                "confidenceScore": 60,
                "reasoning": "Keyword match",
                "source": "ollama_fallback"
            }

    return {
        "contractType": "Other",
        "confidenceScore": 30,
        "reasoning": "No clear match",
        "source": "ollama_fallback"
    }


def is_ollama_available() -> bool:
    """Check if Ollama is running and model is available"""
    try:
        response = requests.get(os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")) + "/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(m.get("name") == MODEL_NAME for m in models)
        return False
    except:
        return False
