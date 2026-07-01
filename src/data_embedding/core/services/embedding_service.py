"""
Embedding service for creating vector embeddings
"""
import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings using SentenceTransformer model.
    """
    
    def __init__(self):
        """Initialize the embedding model"""
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}...")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        logger.info("Embedding model loaded successfully.")
    
    def encode(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Input text
            normalize: Whether to normalize the embedding

        Returns:
            Numpy array of embedding vector
        """
        if not isinstance(text, str):
            logger.warning(f"Non-string input to encode (type={type(text).__name__}), coercing to str")
            text = str(text)
        return self.model.encode(text, normalize_embeddings=normalize)
    
    def encode_batch(self, texts: List[str], normalize: bool = True) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            normalize: Whether to normalize the embeddings
        
        Returns:
            List of numpy arrays
        """
        return self.model.encode(texts, normalize_embeddings=normalize)
    
    def encode_dict(self, text_dict: Dict[str, str], normalize: bool = True) -> Dict[str, np.ndarray]:
        """
        Generate embeddings for dictionary of texts.
        
        Args:
            text_dict: Dictionary of {key: text}
            normalize: Whether to normalize the embeddings
        
        Returns:
            Dictionary of {key: embedding}
        """
        result = {}
        for key, text in text_dict.items():
            result[key] = self.encode(text, normalize)
        return result
