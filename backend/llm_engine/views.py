"""LLM Engine API Views"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .qwen_service import generate_response, generate_contract_summary, is_ollama_available

logger = logging.getLogger(__name__)


class LLMGenerateView(APIView):
    """POST /api/llm/generate/ — generate text from a prompt"""
    permission_classes = [AllowAny]

    def post(self, request):
        prompt = request.data.get("prompt", "").strip()
        if not prompt:
            return Response({"error": "prompt is required"}, status=status.HTTP_400_BAD_REQUEST)
        max_tokens = int(request.data.get("max_tokens", 400))
        result = generate_response(prompt, max_tokens=max_tokens)
        return Response({
            "response": result,
            "model": "qwen2.5:0.5b",
            "ollama_available": result is not None,
        })


class LLMHealthView(APIView):
    """GET /api/llm/health/ — check if Ollama is running"""
    permission_classes = [AllowAny]

    def get(self, request):
        available = is_ollama_available()
        return Response({
            "ollama_available": available,
            "model": "qwen2.5:0.5b",
            "status": "online" if available else "offline",
        })


class LLMSummarizeView(APIView):
    """POST /api/llm/summarize/ — summarize a contract"""
    permission_classes = [AllowAny]

    def post(self, request):
        text = request.data.get("text", "").strip()
        if not text:
            return Response({"error": "text is required"}, status=status.HTTP_400_BAD_REQUEST)
        summary = generate_contract_summary(text)
        return Response({"summary": summary, "model": "qwen2.5:0.5b"})
