"""
Model Cache for ML/AI Models

This module provides a singleton cache for expensive ML models to avoid
reloading them on every request, which causes significant performance issues.

Usage:
    from api.model_cache import model_cache

    # Get cached embedding model
    model = model_cache.get_embedding_model()

    # Get specific model
    model = model_cache.get_embedding_model('sentence-transformers/all-MiniLM-L6-v2')
"""

import logging
import os
from threading import Lock
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ModelCache:
    """Singleton cache for ML models"""

    _instance: Optional['ModelCache'] = None
    _lock: Lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        self._models: Dict[str, any] = {}
        self._initialized = True
        logger.info("✅ ModelCache initialized")

    def get_embedding_model(self, model_name: str = None):
        """
        Get or load an embedding model with caching

        Args:
            model_name: HuggingFace model name. If None, uses default from settings.

        Returns:
            SentenceTransformer model instance

        Raises:
            Exception: If model loading fails
        """
        # Get default model from environment or use fallback
        if model_name is None:
            model_name = os.getenv(
                'CONTRACTS_BERT_MODEL',
                'sentence-transformers/all-MiniLM-L6-v2'
            )

        # Return cached model if available
        cache_key = f"embedding_{model_name}"
        if cache_key in self._models:
            logger.debug(f"📦 Using cached model: {model_name}")
            return self._models[cache_key]

        # Load model with thread safety
        with self._lock:
            # Double-check after acquiring lock
            if cache_key in self._models:
                return self._models[cache_key]

            logger.info(f"📥 Loading embedding model: {model_name}")
            try:
                from sentence_transformers import SentenceTransformer

                model = SentenceTransformer(model_name, device='cpu')
                self._models[cache_key] = model
                logger.info(f"✅ Model loaded successfully: {model_name}")

                return model

            except Exception as e:
                logger.error(f"❌ Failed to load model {model_name}: {str(e)}")
                raise

    def get_bertopic_model(self):
        """
        Get or load BERTopic model with caching

        Returns:
            BERTopic model instance
        """
        cache_key = "bertopic_model"

        if cache_key in self._models:
            logger.debug("📦 Using cached BERTopic model")
            return self._models[cache_key]

        with self._lock:
            if cache_key in self._models:
                return self._models[cache_key]

            logger.info("📥 Loading BERTopic model...")
            try:
                from bertopic import BERTopic

                # You may want to load a pretrained model or configure it
                model = BERTopic(
                    embedding_model=self.get_embedding_model(),
                    verbose=False
                )

                self._models[cache_key] = model
                logger.info("✅ BERTopic model loaded successfully")

                return model

            except Exception as e:
                logger.error(f"❌ Failed to load BERTopic model: {str(e)}")
                raise

    def clear_cache(self, model_name: str = None):
        """
        Clear cached models

        Args:
            model_name: Specific model to clear. If None, clears all models.
        """
        with self._lock:
            if model_name:
                if model_name in self._models:
                    del self._models[model_name]
                    logger.info(f"🗑️  Cleared cached model: {model_name}")
            else:
                self._models.clear()
                logger.info("🗑️  Cleared all cached models")

    def get_cache_info(self) -> dict:
        """
        Get information about cached models

        Returns:
            Dictionary with cache statistics
        """
        return {
            'cached_models': list(self._models.keys()),
            'count': len(self._models),
        }

    def warmup(self):
        """
        Pre-load commonly used models during startup

        This should be called during application startup to avoid
        cold start latency on first requests.
        """
        logger.info("🔥 Warming up model cache...")

        try:
            # Pre-load default embedding model
            self.get_embedding_model()
            logger.info("✅ Model cache warmup completed")

        except Exception as e:
            logger.warning(f"⚠️  Model cache warmup failed: {str(e)}")
            logger.warning("Models will be loaded on first use")


# Global singleton instance
model_cache = ModelCache()


# Optional: Django app ready hook for warmup
# Add this to your apps.py:
"""
from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # Warmup model cache during startup
        from api.model_cache import model_cache
        try:
            model_cache.warmup()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Model warmup failed: {e}")
"""
