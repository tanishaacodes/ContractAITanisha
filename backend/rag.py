# rag.py
import os
import requests
import time
try:
    from qdrant_client import QdrantClient
except ImportError:
    QdrantClient = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

# Try to import Django settings if available
try:
    from django.conf import settings
    QDRANT_URL = getattr(settings, 'QDRANT_URL', os.environ.get("QDRANT_URL", "http://localhost:6333"))
    OLLAMA_BASE_URL = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = getattr(settings, 'OLLAMA_MODEL', 'qwen2.5:0.5b')
except:
    # Fallback if Django is not available
    QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")

# --------------------------------------
# CONFIG
# --------------------------------------
COLLECTION = os.environ.get("QDRANT_COLLECTION", "contracts")
EMBED_MODEL = "all-MiniLM-L6-v2"

# ✅ FORCE OLLAMA ONLY
LLM_PROVIDER = "ollama"

# ✅ FIXED OLLAMA ENDPOINT (THIS WAS YOUR 404 ISSUE)
OLLAMA_API = os.environ.get("OLLAMA_API", f"{OLLAMA_BASE_URL}/api/chat")

# --------------------------------------
# CLIENTS (lazy — initialized on first use)
# --------------------------------------
_client = None
_embedder = None


def get_client():
    global _client
    if _client is None:
        _client = QdrantClient(url=QDRANT_URL)
    return _client


def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBED_MODEL, device='cpu')
    return _embedder


# --------------------------------------
# HELPER — Build context into plain text (STABLE ORDER)
# --------------------------------------
def build_context_text(contexts):
    contexts = sorted(contexts, key=lambda x: (-x["score"], x["chunk_index"]))
    return "\n\n---\n\n".join([c["text"] for c in contexts])


# --------------------------------------
# RETRIEVE CONTEXTS (Qdrant v1.16) - USER-SCOPED
# --------------------------------------
def retrieve_contexts(query: str, user_id: str = None, top_k: int = 6):
    print(f"\n{'='*60}")
    print(f"[RAG] RETRIEVAL STARTED")
    print(f"{'='*60}")
    print(f"Query: {query[:100]}..." if len(query) > 100 else f"Query: {query}")
    print(f"User filter: {user_id if user_id else 'None (all users)'}")
    print(f"Retrieving top {top_k} chunks from Qdrant...")

    start_time = time.time()
    q_emb = get_embedder().encode(query).tolist()
    embed_time = time.time() - start_time
    print(f"[OK] Query embedded in {embed_time:.2f}s")

    # Build query filter for user-specific search
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    query_filter = None
    if user_id:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                )
            ]
        )
        print(f"[FILTER] Searching only user {user_id}'s contracts")

    result = get_client().query_points(
        collection_name=COLLECTION,
        query=q_emb,
        limit=top_k,
        with_payload=True,
        score_threshold=0.15,
        query_filter=query_filter
    )

    contexts = []
    for pt in result.points:
        payload = pt.payload or {}
        contexts.append({
            "score": pt.score,
            "text": payload.get("text", ""),
            "filename": payload.get("filename", ""),
            "contract_id": payload.get("contract_id", ""),
            "chunk_index": payload.get("chunk_index", 0),
        })

    print(f"[OK] Found {len(contexts)} relevant chunks")
    return contexts


# --------------------------------------
# CALL LLM — FULLY DETERMINISTIC OLLAMA ONLY
# --------------------------------------
def call_llm(prompt, max_tokens=1500, temperature=0.0, stream=True):
    print(f"\n{'='*60}")
    print(f"[LLM] GENERATION STARTED")
    print(f"{'='*60}")
    print(f"Provider: OLLAMA")
    print(f"Model: {OLLAMA_MODEL}")
    print(f"Max tokens: {max_tokens}")
    print(f"Temperature: 0.0 (LOCKED)")
    print(f"Streaming: {stream}")

    llm_start = time.time()

    # CPU inference is ~1 token/sec; cap tokens and timeout aggressively
    effective_tokens = min(max_tokens, 200)
    timeout = 30
    print(f"[LLM] Calling Ollama API (timeout: {timeout}s, tokens capped: {effective_tokens})...")

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "options": {
            "num_predict": effective_tokens,
            "temperature": 0.0,     # ✅ NO randomness
            "top_k": 1,             # ✅ Always best token
            "top_p": 0.1,           # ✅ Tight probability
            "repeat_penalty": 1.2   # ✅ Prevent wording drift
        },
        "stream": stream
    }

    r = requests.post(OLLAMA_API, json=payload, timeout=timeout, stream=stream)
    r.raise_for_status()

    full_response = ""
    print("[LLM] Generating response: ", end="", flush=True)

    for line in r.iter_lines():
        if line:
            import json
            chunk = json.loads(line)
            if "message" in chunk and "content" in chunk["message"]:
                token = chunk["message"]["content"]
                full_response += token
                print(token, end="", flush=True)

            if chunk.get("done", False):
                break

    llm_time = time.time() - llm_start
    print(f"\n[OK] LLM completed in {llm_time:.2f}s")
    print(f"[OK] Generated {len(full_response)} characters")

    return {"response": full_response.strip()}


# --------------------------------------
# INTELLIGENT QUERY CLASSIFIER
# --------------------------------------
def classify_query_intent(query: str, has_contexts: bool):
    """
    Determine if query is about contracts or general knowledge

    Returns: 'contract', 'general', or 'hybrid'
    """
    query_lower = query.lower()

    # Contract-specific keywords
    contract_keywords = [
        'contract', 'clause', 'agreement', 'termination', 'payment',
        'liability', 'obligation', 'party', 'indemnification', 'warranty',
        'my contract', 'this contract', 'our contract', 'the contract',
        'nda', 'msa', 'employment', 'consulting', 'lease'
    ]

    # General question patterns
    general_patterns = [
        'what is', 'who is', 'when was', 'where is', 'why does',
        'how to', 'explain', 'define', 'tell me about', 'what are the benefits',
        'compare', 'difference between', 'best practices', 'examples of'
    ]

    has_contract_keyword = any(kw in query_lower for kw in contract_keywords)
    has_general_pattern = any(pattern in query_lower for pattern in general_patterns)

    # If no contexts found, it's likely general
    if not has_contexts:
        if has_contract_keyword:
            return 'no_contracts'  # User asking about contracts but none uploaded
        return 'general'

    # If contexts exist and query mentions contracts
    if has_contexts and has_contract_keyword:
        return 'contract'

    # If both patterns present, it's hybrid
    if has_general_pattern and has_contract_keyword:
        return 'hybrid'

    # Default: if we have contexts, prefer contract search
    if has_contexts:
        return 'contract'

    return 'general'


# --------------------------------------
# Q&A FLOW — INTELLIGENT DUAL MODE
# --------------------------------------
def qa_flow(query: str, user_id: str = None, mode: str = 'auto'):
    pipeline_start = time.time()
    print(f"\n{'#'*60}")
    print(f"[Q&A] PIPELINE STARTED")
    print(f"{'#'*60}")
    print(f"Question: {query}")
    print(f"Mode: {mode}")

    contexts = retrieve_contexts(query, user_id=user_id, top_k=6)
    context_text = build_context_text(contexts)

    # Determine query intent
    if mode == 'auto':
        intent = classify_query_intent(query, len(contexts) > 0)
        print(f"[Q&A] Detected intent: {intent}")
    else:
        intent = mode

    print(f"\n[LLM] Building prompt with {len(context_text)} chars of context...")

    # Build prompt based on intent
    if intent == 'no_contracts':
        prompt = f"""
You are a helpful AI assistant with expertise in legal contracts and business matters.

The user is asking about contracts, but they haven't uploaded any contracts yet.

Question: {query}

Provide a helpful, informative response that:
1. Acknowledges they don't have contracts uploaded yet
2. Answers their question with general knowledge if applicable
3. Suggests they upload contracts to get personalized analysis

Response:
"""
        resp = call_llm(prompt, max_tokens=500)

    elif intent == 'general' or len(contexts) == 0:
        # General knowledge mode - no contract context needed
        prompt = f"""
You are a helpful AI assistant with expertise in legal contracts, business, and general knowledge.

Question: {query}

Provide a clear, informative, and helpful response. Use your knowledge to answer accurately and comprehensively.

Response:
"""
        resp = call_llm(prompt, max_tokens=800)

    elif intent == 'contract':
        # Contract-specific mode - strict adherence to context
        prompt = f"""
You are a Legal Contract Question Answering System with access to the user's uploaded contracts.

ANSWER RULES:
- Answer based on the provided contract context below
- Be specific and cite relevant information from the contracts
- If the answer isn't in the context, say "I couldn't find this information in your uploaded contracts."
- Use natural, conversational language
- Provide detailed explanations when helpful

Contract Context:
{context_text}

Question:
{query}

Answer:
"""
        resp = call_llm(prompt, max_tokens=600)

    else:  # hybrid
        # Hybrid mode - combine both
        prompt = f"""
You are a helpful AI assistant with expertise in legal contracts and general knowledge.

The user has uploaded contracts, and here's relevant context from them:

Contract Context:
{context_text}

Question: {query}

Provide a comprehensive answer that:
1. Uses information from the contract context if relevant
2. Supplements with general knowledge if needed
3. Makes it clear which information comes from the contracts vs general knowledge

Answer:
"""
        resp = call_llm(prompt, max_tokens=800)

    total_time = time.time() - pipeline_start
    print(f"\n{'#'*60}")
    print(f"[Q&A] PIPELINE COMPLETED")
    print(f"{'#'*60}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Answer length: {len(resp.get('response', ''))} characters")
    print(f"Intent: {intent}")
    print(f"{'#'*60}\n")

    return {
        "contexts": contexts,
        "ollama": resp,
        "intent": intent,
        "has_contract_context": len(contexts) > 0
    }


# --------------------------------------
# CONTRACT GENERATION FLOW — STABLE LONG CONTRACT
# --------------------------------------
def generate_contract_flow(instruction: str):
    pipeline_start = time.time()
    print(f"\n{'#'*60}")
    print(f"[CONTRACT] GENERATION PIPELINE STARTED")
    print(f"{'#'*60}")
    print(f"Instruction: {instruction[:150]}..." if len(instruction) > 150 else f"Instruction: {instruction}")

    contexts = retrieve_contexts(instruction, top_k=5)
    context_text = build_context_text(contexts)

    print(f"\n[LLM] Building prompt with {len(context_text)} chars of context...")

    prompt = f"""
You are a Professional Legal Contract Drafting Assistant.

TASK:
Generate a FULL LEGAL CONTRACT based on:
- User instructions
- Clauses from the retrieved context
- Industry-standard contract structure

RULES:
- Include headings, sections, clauses.
- Keep it formal & legally accurate.
- If data missing, use <Insert ...>.
- Do NOT write short answers here — write a full contract.
- Maintain consistency across the entire contract.

User instruction:
{instruction}

Context:
{context_text}

Write the full contract below:
"""

    resp = call_llm(prompt, max_tokens=1500)

    total_time = time.time() - pipeline_start
    print(f"\n{'#'*60}")
    print(f"[CONTRACT] GENERATION PIPELINE COMPLETED")
    print(f"{'#'*60}")
    print(f"Total time: {total_time:.2f}s ({total_time/60:.1f} min)")
    print(f"Contract length: {len(resp.get('response', ''))} characters")
    print(f"{'#'*60}\n")

    return {"contexts": contexts, "ollama": resp}


# --------------------------------------
# STREAMING CONTRACT GENERATION
# --------------------------------------
def generate_contract_stream(instruction: str):
    contexts = retrieve_contexts(instruction, top_k=5)

    prompt = f"""
You are a Professional Legal Contract Drafting Assistant.

TASK:
Generate a FULL LEGAL CONTRACT based on:
- User instructions
- Clauses from the retrieved context
- Industry-standard contract structure

RULES:
- Include headings, sections, clauses.
- Keep it formal & legally accurate.
- If data missing, use <Insert ...>.
- Do NOT write short answers here — write a full contract.

User instruction:
{instruction}

Context:
{build_context_text(contexts)}

Write the full contract below:
"""

    return call_llm(prompt, max_tokens=1500, stream=True)
