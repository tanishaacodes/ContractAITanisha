import os
"""
LLM Service — Qwen2.5 (0.5B) via Ollama
==========================================
Standalone LLM module for PrimeContractAI.
Provides text generation using local Qwen2.5 model via Ollama REST API.
Falls back to template responses when Ollama is offline.
"""

import logging
import requests

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")) + "/api/generate"
OLLAMA_MODEL = "qwen2.5:0.5b"
DEFAULT_MAX_TOKENS = 400


def generate_response(prompt, max_tokens=DEFAULT_MAX_TOKENS, temperature=0.3):
    """
    Generate a text response using Qwen2.5 via Ollama.

    Args:
        prompt: str — the input prompt
        max_tokens: int — max tokens to generate
        temperature: float — sampling temperature (0=deterministic, 1=creative)

    Returns:
        str — generated text
    """
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "top_p": 0.9,
            },
        }
        resp = requests.post(OLLAMA_URL, json=payload, timeout=45)
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        logger.warning("Ollama not running — LLM unavailable")
        return None
    except Exception as e:
        logger.error(f"Qwen2.5 generation error: {e}")
        return None


def generate_contract_summary(contract_text, max_tokens=300):
    """Generate an executive summary of a contract."""
    prompt = f"""You are a senior legal analyst. Summarize the following contract in 3 concise bullet points covering: parties, key obligations, and main risks.

Contract text:
{contract_text[:3000]}

Summary:"""
    return generate_response(prompt, max_tokens=max_tokens) or \
        "Summary unavailable — LLM offline. Key contract details should be reviewed manually."


def generate_risk_narrative(clause_text, risk_score, risk_level):
    """Generate a plain-English risk explanation for a clause."""
    prompt = f"""You are a contract risk advisor. Explain in 2 sentences why this clause is {risk_level} risk (score: {risk_score:.2f}).

Clause: {clause_text[:500]}

Risk explanation:"""
    return generate_response(prompt, max_tokens=150) or \
        f"This clause carries {risk_level} risk. Manual legal review recommended."


def generate_negotiation_suggestion(clause_text, position="buyer"):
    """Generate a negotiation counter-proposal for a clause."""
    prompt = f"""You are a contract negotiation expert representing the {position}.
Suggest a specific amendment to this clause in one sentence.

Clause: {clause_text[:400]}

Suggested amendment:"""
    return generate_response(prompt, max_tokens=200) or \
        "Negotiation suggestion unavailable — review clause terms manually."


def is_ollama_available():
    """Quick health check for Ollama availability."""
    try:
        resp = requests.get(os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")) + "/api/tags", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False
