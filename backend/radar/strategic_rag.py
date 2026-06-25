import os
"""
Strategic RAG
=============
Generates executive-level strategic narratives using Qwen2.5 via Ollama.
Falls back to a template-based summary if LLM is unavailable.
"""

import logging
import requests

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")) + "/api/generate"
OLLAMA_MODEL = "qwen2.5:0.5b"


def _call_ollama(prompt, max_tokens=300):
    """Call Ollama REST API to generate a completion."""
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.3},
        }
        resp = requests.post(OLLAMA_URL, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()
    except Exception as e:
        logger.warning(f"Ollama call failed: {e}")
        return None


def generate_strategic_alert(contract_title, signal, estimated_impact, exposure_type="commodity"):
    """
    Generate an executive-level strategic recommendation using Qwen2.5.

    Args:
        contract_title: str
        signal: dict from market_feed (signal_name, percent_change, current_value)
        estimated_impact: float — financial impact in currency units
        exposure_type: str

    Returns:
        str — executive narrative
    """
    signal_name = signal.get('signal_name', 'Market Signal')
    pct_change = signal.get('percent_change', 0)
    direction = "declined" if pct_change < 0 else "increased"

    prompt = f"""You are an executive contract intelligence advisor.

Contract: {contract_title}
Market Signal: {signal_name} has {direction} by {abs(pct_change):.2f}%
Current Value: {signal.get('current_value', 'N/A')}
Exposure Type: {exposure_type}
Estimated Financial Impact: ₹{estimated_impact:,.0f}

Write a concise 2-3 sentence executive recommendation. Be specific about the action required.
Focus on: what to do, who should act, and by when. Use formal business language."""

    llm_response = _call_ollama(prompt)

    if llm_response:
        return llm_response

    # Fallback template
    return _generate_template_narrative(contract_title, signal_name, pct_change, estimated_impact, direction)


def _generate_template_narrative(contract_title, signal_name, pct_change, estimated_impact, direction):
    """Template-based fallback when LLM is unavailable."""
    if pct_change < 0:
        return (
            f"Strategic opportunity detected for '{contract_title}'. "
            f"{signal_name} has {direction} by {abs(pct_change):.2f}%, creating an estimated "
            f"₹{estimated_impact:,.0f} renegotiation opportunity. "
            f"Procurement leadership should initiate supplier renegotiation within 5 business days "
            f"to capture cost savings before market recovery."
        )
    else:
        return (
            f"Cost risk alert for '{contract_title}'. "
            f"{signal_name} has {direction} by {abs(pct_change):.2f}%, exposing an estimated "
            f"₹{estimated_impact:,.0f} additional cost. "
            f"Finance team should review contract terms and assess hedging options immediately."
        )
