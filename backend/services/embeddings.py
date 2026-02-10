from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

class EmbeddingsService:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            # Using a lightweight, fast model suitable for short text (openers)
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._model

    @classmethod
    def generate_embedding(cls, text: str) -> List[float]:
        """Generates a 384-dimensional embedding for the given text."""
        model = cls.get_model()
        embedding = model.encode(text)
        return embedding.tolist()

    @classmethod
    def calculate_similarity(cls, emb1: List[float], emb2: List[float]) -> float:
        """Calculates cosine similarity between two embeddings."""
        a = np.array(emb1)
        b = np.array(emb2)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Global instance for easy access
embeddings_service = EmbeddingsService()
