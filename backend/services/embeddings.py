"""
Embeddings service - provides text embedding and similarity features.
Falls back gracefully when sentence-transformers is not available (e.g., Vercel serverless).
"""
import os
import logging
from typing import List, Optional

logger = logging.getLogger("backend.embeddings")

# sentence-transformers pulls PyTorch (~700MB), which exceeds Vercel's 250MB limit.
# Make it optional — embeddings are a nice-to-have for draft recommendations,
# not critical for core functionality.
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    _HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    _HAS_SENTENCE_TRANSFORMERS = False
    logger.warning("sentence-transformers not available — embedding features disabled")


class EmbeddingsService:
    _model = None

    @classmethod
    def get_model(cls):
        if not _HAS_SENTENCE_TRANSFORMERS:
            return None
        if cls._model is None:
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._model

    @classmethod
    def generate_embedding(cls, text: str) -> Optional[List[float]]:
        """Generates a 384-dimensional embedding for the given text."""
        model = cls.get_model()
        if model is None:
            return None
        embedding = model.encode(text)
        return embedding.tolist()

    @classmethod
    def calculate_similarity(cls, emb1: List[float], emb2: List[float]) -> float:
        """Calculates cosine similarity between two embeddings."""
        if not _HAS_SENTENCE_TRANSFORMERS:
            return 0.0
        import numpy as np
        a = np.array(emb1)
        b = np.array(emb2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# Global instance for easy access
embeddings_service = EmbeddingsService()
