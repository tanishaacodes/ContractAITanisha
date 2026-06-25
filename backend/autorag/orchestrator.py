"""
AutoRAG Orchestrator
=====================
Intent-aware retrieval + LLM reasoning pipeline.

Flow:
  User query
      → Intent classification
      → Query embedding
      → Hybrid graph + vector retrieval
      → Context assembly
      → Qwen2.5 prompt
      → Structured answer with evidence

Uses existing:
  - embeddings.embedding_service
  - llm_engine.qwen_service
  - autorag.retriever
"""

import re
import logging
from .retriever import hybrid_retrieve, retrieve_clauses_by_entity

logger = logging.getLogger(__name__)

# Maximum characters of context to send to the LLM
MAX_CONTEXT_CHARS = 4000


# ─────────────────────────────────────────────────────────────────────────────
# 1. Intent Classification
# ─────────────────────────────────────────────────────────────────────────────

_INTENT_PATTERNS = [
    ("RISK",        r"\b(risk|risky|dangerous|hazard|exposure|liability|penalt)\b"),
    ("TERMINATION", r"\b(terminat|cancel|exit|expire|expiry|end the contract|rescind)\b"),
    ("PAYMENT",     r"\b(payment|pay|fee|invoice|cost|price|reimburse|compensation|monetary)\b"),
    ("OBLIGATION",  r"\b(obligat|shall|must|duty|required|undertake|responsible)\b"),
    ("INDEMNITY",   r"\b(indemnif|hold harmless|defend|protect from)\b"),
    ("TEMPORAL",    r"\b(date|deadline|when|timeline|period|duration|notice|renew|effective)\b"),
    ("ENTITY",      r"\b(who|party|parties|company|vendor|supplier|buyer|seller|contractor)\b"),
]


def classify_intent(query: str) -> str:
    """
    Classify a user query into one of the retrieval intent categories.

    Returns one of: RISK, TERMINATION, PAYMENT, OBLIGATION, INDEMNITY,
                    TEMPORAL, ENTITY, GENERAL
    """
    q = query.lower()
    for intent, pattern in _INTENT_PATTERNS:
        if re.search(pattern, q, re.I):
            return intent
    return "GENERAL"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Context Assembly
# ─────────────────────────────────────────────────────────────────────────────

def _assemble_context(clauses: list) -> str:
    """Format retrieved clauses into a readable LLM context block."""
    parts = []
    total_chars = 0

    for i, c in enumerate(clauses, 1):
        doc = c.get("document") or "Unknown Document"
        num = c.get("clause_number") or f"#{i}"
        risk = c.get("risk_level", "LOW")
        text = c.get("text", "").strip()

        # Truncate very long individual clauses
        if len(text) > 600:
            text = text[:600] + "…"

        entry = f"[Clause {num} | {doc} | Risk: {risk}]\n{text}"
        entry_len = len(entry)

        if total_chars + entry_len > MAX_CONTEXT_CHARS:
            break

        parts.append(entry)
        total_chars += entry_len

    return "\n\n---\n\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# 3. LLM Prompt Templates
# ─────────────────────────────────────────────────────────────────────────────

_PROMPT_TEMPLATE = """You are PrimeContractAI, an expert legal contract analyst.

Answer the user's question based ONLY on the contract clauses provided below.
If the answer is not in the clauses, say "I could not find relevant information in the indexed clauses."

Be concise, precise, and highlight any risk levels mentioned.

--- CONTRACT CLAUSES ---
{context}
--- END OF CLAUSES ---

USER QUESTION: {query}

ANSWER:"""

_RISK_PROMPT_TEMPLATE = """You are PrimeContractAI, a contract risk advisor.

Review the following HIGH/CRITICAL risk clauses and summarise the key risks for the user.
For each clause, explain: (1) what the risk is, (2) which party bears it, (3) suggested mitigation.

--- RISK CLAUSES ---
{context}
--- END OF CLAUSES ---

USER QUESTION: {query}

RISK ANALYSIS:"""


def _build_prompt(query: str, context: str, intent: str) -> str:
    if intent == "RISK":
        return _RISK_PROMPT_TEMPLATE.format(context=context, query=query)
    return _PROMPT_TEMPLATE.format(context=context, query=query)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Main Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def answer_query(query: str, document_filter: str = None) -> dict:
    """
    Full AutoRAG pipeline for a user query.

    Args:
        query:           Natural language question about contracts.
        document_filter: Optional document name to scope retrieval.

    Returns:
        {
            intent, clauses_retrieved, context_chars,
            answer, supporting_clauses
        }
    """
    intent = classify_intent(query)
    logger.info(f"[AutoRAG] Query: '{query[:60]}' | Intent: {intent}")

    # Retrieve relevant clauses
    clauses = hybrid_retrieve(query, intent=intent)

    if document_filter:
        clauses = [c for c in clauses if c.get("document") == document_filter]

    if not clauses:
        return {
            "intent": intent,
            "clauses_retrieved": 0,
            "context_chars": 0,
            "answer": "No relevant clauses found in the indexed contracts. Please upload and index the contract first.",
            "supporting_clauses": [],
        }

    context = _assemble_context(clauses)
    prompt = _build_prompt(query, context, intent)

    # LLM inference
    answer = None
    try:
        from llm_engine.qwen_service import generate_response
        answer = generate_response(prompt, max_tokens=500, temperature=0.2)
    except Exception as e:
        logger.warning(f"[AutoRAG] LLM call failed: {e}")

    if not answer:
        # Graceful fallback — return context without LLM narration
        answer = (
            f"LLM offline. Here are the {len(clauses)} most relevant clauses:\n\n"
            + "\n\n".join(
                f"[{c.get('document')} | Risk: {c.get('risk_level')}]\n{c.get('text', '')[:300]}"
                for c in clauses[:3]
            )
        )

    return {
        "intent": intent,
        "clauses_retrieved": len(clauses),
        "context_chars": len(context),
        "answer": answer,
        "supporting_clauses": [
            {
                "clause_id":    c.get("clause_id"),
                "clause_number": c.get("clause_number"),
                "document":     c.get("document"),
                "risk_level":   c.get("risk_level"),
                "risk_score":   c.get("risk_score"),
                "score":        c.get("score"),
                "text_preview": c.get("text", "")[:200],
                "flags": {
                    "obligation":  c.get("obligation"),
                    "indemnity":   c.get("indemnity"),
                    "termination": c.get("termination"),
                    "payment":     c.get("payment"),
                },
            }
            for c in clauses
        ],
    }


def answer_entity_query(query: str, entity_name: str) -> dict:
    """Retrieve clauses mentioning a specific entity and answer a query about them."""
    intent = classify_intent(query)
    clauses = retrieve_clauses_by_entity(entity_name)

    if not clauses:
        return {
            "intent": intent,
            "entity": entity_name,
            "clauses_retrieved": 0,
            "answer": f"No clauses found mentioning entity '{entity_name}'.",
            "supporting_clauses": [],
        }

    context = _assemble_context(clauses)
    prompt = (
        f"The following contract clauses mention '{entity_name}'.\n\n"
        + _PROMPT_TEMPLATE.format(context=context, query=query)
    )

    answer = None
    try:
        from llm_engine.qwen_service import generate_response
        answer = generate_response(prompt, max_tokens=400, temperature=0.2)
    except Exception as e:
        logger.warning(f"[AutoRAG] Entity LLM call failed: {e}")

    return {
        "intent": intent,
        "entity": entity_name,
        "clauses_retrieved": len(clauses),
        "answer": answer or f"Found {len(clauses)} clauses for entity '{entity_name}'.",
        "supporting_clauses": clauses,
    }
