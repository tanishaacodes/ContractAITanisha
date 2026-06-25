"""
LLM Service for Tender Action Generation
==========================================
Integrates with Ollama (local) or OpenAI (cloud) to generate
structured action items from tender content.

Uses:
  - Ollama Qwen2.5:0.5b (default, local)
  - OpenAI GPT-4 (fallback, if API key provided)
"""

import os
import json
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Configuration from environment
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


# ─────────────────────────────────────────────────────────────────────────────
# OLLAMA Integration (Default)
# ─────────────────────────────────────────────────────────────────────────────

def call_ollama(prompt: str, system: str = "", format_json: bool = True) -> Dict:
    """
    Call Ollama API with structured JSON output.

    Args:
        prompt: The user prompt
        system: System message
        format_json: Force JSON output format

    Returns:
        Parsed JSON dict or error dict
    """
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
            }
        }

        if system:
            payload["system"] = system

        if format_json:
            payload["format"] = "json"

        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            text = result.get("response", "")

            if format_json:
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    # Try to extract JSON from markdown code blocks
                    if "```json" in text:
                        text = text.split("```json")[1].split("```")[0].strip()
                        return json.loads(text)
                    elif "```" in text:
                        text = text.split("```")[1].split("```")[0].strip()
                        return json.loads(text)
                    else:
                        logger.error(f"[LLM] Invalid JSON response: {text[:200]}")
                        return {"error": "Invalid JSON response"}

            return {"response": text}
        else:
            logger.error(f"[LLM] Ollama API error: {response.status_code}")
            return {"error": f"API error: {response.status_code}"}

    except requests.exceptions.ConnectionError:
        logger.warning("[LLM] Ollama not available, falling back to OpenAI")
        return call_openai(prompt, system) if OPENAI_API_KEY else {"error": "LLM unavailable"}
    except Exception as e:
        logger.exception(f"[LLM] Ollama call failed: {e}")
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# OpenAI Integration (Fallback)
# ─────────────────────────────────────────────────────────────────────────────

def call_openai(prompt: str, system: str = "") -> Dict:
    """
    Call OpenAI API with GPT-4.
    Fallback when Ollama is unavailable.
    """
    if not OPENAI_API_KEY:
        return {"error": "No OpenAI API key configured"}

    try:
        import openai
        openai.api_key = OPENAI_API_KEY

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        text = response.choices[0].message.content
        return json.loads(text)

    except Exception as e:
        logger.exception(f"[LLM] OpenAI call failed: {e}")
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# High-Level Action Generation Functions
# ─────────────────────────────────────────────────────────────────────────────

def generate_actions_from_text(
    text: str,
    source_type: str,
    context: str = ""
) -> List[Dict]:
    """
    Generate structured action items from arbitrary tender text.

    Args:
        text: The tender clause/BOQ/section text
        source_type: Type of source (BOQ/Clause/Risk/etc.)
        context: Additional context (tender title, etc.)

    Returns:
        List of action dicts with: title, description, priority, risk_score,
        complexity_score, financial_exposure
    """
    system = """You are an expert construction bid manager analyzing tender documents
for mega infrastructure projects (Metro Rail, High-Rise, EPC).
Extract actionable tasks for cross-functional departments."""

    prompt = f"""
Analyze this tender content and extract specific actionable tasks.

Source Type: {source_type}
Context: {context}

Content:
{text[:2000]}

Generate 1-5 actionable tasks. For each task, provide:
- title: Short task name (max 80 chars)
- description: Detailed task description (max 300 chars)
- priority: Low / Medium / High / Critical
- risk_score: 0.0 to 1.0 (financial/schedule risk)
- complexity_score: 0.0 to 1.0 (technical complexity)
- financial_exposure: Estimated financial impact in USD (0 if unknown)

Return JSON format:
{{
  "tasks": [
    {{
      "title": "Task name",
      "description": "Task details",
      "priority": "High",
      "risk_score": 0.6,
      "complexity_score": 0.5,
      "financial_exposure": 500000
    }}
  ]
}}
"""

    result = call_ollama(prompt, system, format_json=True)

    if "error" in result:
        logger.warning(f"[LLM] Action generation failed: {result['error']}")
        return []

    tasks = result.get("tasks", [])

    # Validate and normalize
    valid_tasks = []
    for task in tasks:
        if not task.get("title") or not task.get("description"):
            continue

        valid_tasks.append({
            "title": str(task.get("title", ""))[:200],
            "description": str(task.get("description", ""))[:500],
            "priority": task.get("priority", "Medium"),
            "risk_score": float(task.get("risk_score", 0.5)),
            "complexity_score": float(task.get("complexity_score", 0.5)),
            "financial_exposure": float(task.get("financial_exposure", 0)),
        })

    logger.info(f"[LLM] Generated {len(valid_tasks)} actions from {source_type}")
    return valid_tasks


def enrich_action_description(
    title: str,
    basic_description: str,
    department: str,
    context: str = ""
) -> str:
    """
    Enrich a basic action description with department-specific details.

    Args:
        title: Action title
        basic_description: Basic description
        department: Target department
        context: Tender context

    Returns:
        Enriched description string
    """
    system = f"""You are a {department} department expert in mega construction projects."""

    prompt = f"""
Enhance this task description with technical details specific to {department} department.

Task: {title}
Current Description: {basic_description}
Context: {context}

Provide a detailed, actionable description (max 300 chars) that includes:
- Specific deliverables
- Key considerations
- Standards/codes to reference

Return JSON:
{{
  "enhanced_description": "Your enhanced description here"
}}
"""

    result = call_ollama(prompt, system, format_json=True)

    if "error" in result or not result.get("enhanced_description"):
        return basic_description

    return result["enhanced_description"][:500]


def classify_department_llm(text: str) -> str:
    """
    Use LLM to classify text into department.
    Fallback for rule-based classifier.

    Args:
        text: Text to classify

    Returns:
        Department name (Civil/Mechanical/etc.)
    """
    departments = [
        "Civil", "Mechanical", "Electrical", "MEP", "Signaling",
        "Planning", "Procurement", "Finance", "Legal", "HSE", "QA/QC"
    ]

    prompt = f"""
Classify this tender item into ONE department from: {', '.join(departments)}

Text:
{text[:500]}

Return JSON:
{{
  "department": "Civil"
}}
"""

    result = call_ollama(prompt, format_json=True)

    dept = result.get("department", "Civil")
    return dept if dept in departments else "Civil"


# ─────────────────────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────────────────────

def check_llm_availability() -> Dict[str, bool]:
    """
    Check which LLM backends are available.

    Returns:
        {"ollama": bool, "openai": bool}
    """
    status = {"ollama": False, "openai": False}

    # Check Ollama
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        status["ollama"] = response.status_code == 200
    except:
        pass

    # Check OpenAI
    status["openai"] = bool(OPENAI_API_KEY)

    return status
