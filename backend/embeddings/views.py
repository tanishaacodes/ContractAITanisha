"""Embeddings Engine API Views"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .embedding_service import (
    generate_embedding,
    generate_batch_embeddings,
    cosine_similarity,
    is_transformer_available,
)

logger = logging.getLogger(__name__)


class EmbeddingGenerateView(APIView):
    """POST /api/embeddings/generate/"""
    permission_classes = [AllowAny]

    def post(self, request):
        text = request.data.get("text", "").strip()
        if not text:
            return Response({"error": "text is required"}, status=status.HTTP_400_BAD_REQUEST)
        result = generate_embedding(text)
        return Response(result)


class EmbeddingBatchView(APIView):
    """POST /api/embeddings/batch/"""
    permission_classes = [AllowAny]

    def post(self, request):
        texts = request.data.get("texts", [])
        if not texts or not isinstance(texts, list):
            return Response({"error": "texts must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)
        if len(texts) > 100:
            return Response({"error": "Maximum 100 texts per batch"}, status=status.HTTP_400_BAD_REQUEST)
        results = generate_batch_embeddings(texts)
        return Response({"embeddings": results, "count": len(results)})


class EmbeddingSimilarityView(APIView):
    """POST /api/embeddings/similarity/"""
    permission_classes = [AllowAny]

    def post(self, request):
        text_a = request.data.get("text_a", "").strip()
        text_b = request.data.get("text_b", "").strip()
        if not text_a or not text_b:
            return Response({"error": "text_a and text_b are required"}, status=status.HTTP_400_BAD_REQUEST)
        emb_a = generate_embedding(text_a)["embedding"]
        emb_b = generate_embedding(text_b)["embedding"]
        sim = cosine_similarity(emb_a, emb_b)
        return Response({"similarity": sim, "text_a_preview": text_a[:100], "text_b_preview": text_b[:100]})


class EmbeddingHealthView(APIView):
    """GET /api/embeddings/health/"""
    permission_classes = [AllowAny]

    def get(self, request):
        available = is_transformer_available()
        return Response({
            "transformer_available": available,
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "fallback": "hash-based 384-dim",
            "status": "online" if available else "fallback",
        })
