# utils/embeddings.py
"""Embedding model loader and utilities."""

import logging
from sentence_transformers import SentenceTransformer
from config.settings import EMBEDDING_MODEL_NAME

logger = logging.getLogger(__name__)

# Global embedding model instance (singleton)
_embedding_model = None


def get_embedding_model() -> SentenceTransformer | None:
    """
    Returns a singleton instance of the embedding model.
    Lazy loading - only loads when first called.
    """
    global _embedding_model
    
    if _embedding_model is None:
        try:
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
            _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return None
    
    return _embedding_model


def encode_text(text: str, normalize: bool = True) -> list[float] | None:
    """
    Encode text to embedding vector.
    
    Args:
        text: The text to encode
        normalize: Whether to normalize embeddings (default True for cosine similarity)
    
    Returns:
        List of floats representing the embedding, or None if model unavailable
    """
    model = get_embedding_model()
    if model is None:
        return None
    
    return model.encode(text, normalize_embeddings=normalize).tolist()
