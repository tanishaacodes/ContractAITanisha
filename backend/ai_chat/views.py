"""
AI Chat Assistant API
=====================
Conversational AI for contract intelligence queries.

Features:
- RAG-powered responses using contract knowledge base
- Qwen2.5 LLM for natural language generation
- Context-aware multi-turn conversations
- Contract-specific question answering

Endpoints:
    POST /api/chat/message - Send chat message and get AI response
    GET /api/chat/history/{session_id} - Get chat history
    DELETE /api/chat/session/{session_id} - Clear session
"""

import logging
from typing import List, Dict, Any
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache

from llm_engine.qwen_service import generate_response
from ai.rag.bm25_bert_retriever import BM25BERTRetriever

logger = logging.getLogger(__name__)


class ContractChatAssistant:
    """
    AI assistant for contract intelligence queries.
    """

    def __init__(self):
        self.retriever = None
        self._load_retriever()

    def _load_retriever(self):
        """Load RAG retriever with contract knowledge base."""
        try:
            # Load contracts from database
            from core.models import Contract, Clause

            # Get all clauses for RAG
            clauses = Clause.objects.select_related('contract').all()[:5000]

            documents = []
            for clause in clauses:
                doc = {
                    'id': str(clause.id),
                    'text': f"{clause.clause_name or clause.clause_type}: {clause.extracted_text or ''}",
                    'contract_id': clause.contract_id,
                    'clause_type': clause.clause_type or clause.clause_name
                }
                documents.append(doc)

            if documents:
                self.retriever = BM25BERTRetriever(documents=documents)
                logger.info(f"Loaded {len(documents)} clauses for RAG")
            else:
                logger.warning("No clauses found for RAG")

        except Exception as e:
            logger.error(f"Failed to load RAG retriever: {e}")

    def get_response(
        self,
        user_message: str,
        session_id: str,
        contract_id: str = None
    ) -> Dict[str, Any]:
        """
        Generate AI response to user query.

        Args:
            user_message: User's question/message
            session_id: Conversation session ID
            contract_id: Optional specific contract context

        Returns:
            Response dict with answer, sources, and metadata
        """
        # Retrieve conversation history
        history = self._get_session_history(session_id)

        # Retrieve relevant clauses
        relevant_docs = []
        if self.retriever:
            try:
                results = self.retriever.retrieve(user_message, top_k=5)
                relevant_docs = results
            except Exception as e:
                logger.error(f"RAG retrieval error: {e}")

        # Build context from retrieved documents
        context_text = "\n\n".join([
            f"[{doc['id']}] {doc.get('clause_type', 'Clause')}: {doc['text'][:200]}..."
            for doc in relevant_docs
        ]) if relevant_docs else "No specific contract context found."

        # Build prompt
        prompt = self._build_prompt(
            user_message=user_message,
            context=context_text,
            history=history
        )

        # Generate response using Qwen2.5
        try:
            ai_response = generate_response(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3
            )

            if not ai_response:
                ai_response = self._fallback_response(user_message, relevant_docs)

        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            ai_response = self._fallback_response(user_message, relevant_docs)

        # Update session history
        self._update_session_history(session_id, user_message, ai_response)

        return {
            'answer': ai_response,
            'sources': [
                {
                    'id': doc['id'],
                    'text': doc['text'][:300],
                    'contract_id': doc.get('contract_id'),
                    'type': doc.get('clause_type')
                }
                for doc in relevant_docs[:3]
            ],
            'session_id': session_id
        }

    def _build_prompt(
        self,
        user_message: str,
        context: str,
        history: List[Dict]
    ) -> str:
        """Build LLM prompt with context and history."""

        history_text = "\n".join([
            f"User: {msg['user']}\nAssistant: {msg['assistant']}"
            for msg in history[-3:]  # Last 3 turns
        ]) if history else ""

        prompt = f"""You are PrimeContractAI Assistant, an expert in contract analysis and dispute prediction.

CONTRACT CONTEXT:
{context}

CONVERSATION HISTORY:
{history_text}

USER QUESTION:
{user_message}

INSTRUCTIONS:
- Provide a clear, concise answer based on the contract context
- If the context doesn't contain the answer, say so honestly
- Cite specific clauses when relevant
- Focus on legal risks, obligations, and dispute potential
- Be professional and precise

ANSWER:"""

        return prompt

    def _fallback_response(
        self,
        user_message: str,
        relevant_docs: List[Dict]
    ) -> str:
        """Generate fallback response when LLM is unavailable."""

        if not relevant_docs:
            return (
                "I apologize, but I couldn't find specific contract information "
                "related to your query. Could you provide more details or rephrase your question?"
            )

        # Extract key terms from user message
        terms = user_message.lower().split()
        relevant_types = [doc.get('clause_type', '') for doc in relevant_docs[:3]]

        return (
            f"Based on the contract clauses, I found relevant information about: "
            f"{', '.join(set(relevant_types))}. "
            f"However, for a detailed analysis, please ensure the AI service is running. "
            f"You can review the following clause sections for more details."
        )

    def _get_session_history(self, session_id: str) -> List[Dict]:
        """Get conversation history from cache."""
        return cache.get(f"chat_history_{session_id}", [])

    def _update_session_history(
        self,
        session_id: str,
        user_message: str,
        ai_response: str
    ):
        """Update conversation history in cache."""
        history = self._get_session_history(session_id)
        history.append({
            'user': user_message,
            'assistant': ai_response
        })

        # Keep only last 20 turns
        history = history[-20:]

        cache.set(f"chat_history_{session_id}", history, timeout=3600 * 24)  # 24 hours


# Initialize singleton assistant
_assistant = ContractChatAssistant()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_message(request):
    """
    Send message to AI chat assistant.

    Request body:
        {
            "message": "What are the payment terms in this contract?",
            "session_id": "user_session_123",
            "contract_id": "abc123"  // optional
        }

    Response:
        {
            "answer": "The payment terms specify...",
            "sources": [{"id": "...", "text": "...", "type": "payment"}],
            "session_id": "user_session_123"
        }
    """
    try:
        message = request.data.get('message', '').strip()
        session_id = request.data.get('session_id', f"user_{request.user.id}")
        contract_id = request.data.get('contract_id')

        if not message:
            return Response(
                {'error': 'Message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get AI response
        response_data = _assistant.get_response(
            user_message=message,
            session_id=session_id,
            contract_id=contract_id
        )

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Chat message error: {e}")
        return Response(
            {'error': 'Failed to process message', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_history(request, session_id):
    """
    Get chat history for a session.

    Response:
        {
            "history": [
                {"user": "...", "assistant": "..."},
                ...
            ],
            "session_id": "user_session_123"
        }
    """
    try:
        history = cache.get(f"chat_history_{session_id}", [])

        return Response({
            'history': history,
            'session_id': session_id
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Get chat history error: {e}")
        return Response(
            {'error': 'Failed to retrieve history'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_session(request, session_id):
    """
    Clear chat session history.

    Response:
        {"success": true, "message": "Session cleared"}
    """
    try:
        cache.delete(f"chat_history_{session_id}")

        return Response({
            'success': True,
            'message': 'Session cleared'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Clear session error: {e}")
        return Response(
            {'error': 'Failed to clear session'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
