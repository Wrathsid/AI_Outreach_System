import logging
from typing import Dict, Optional
from backend.services.embeddings import embeddings_service

logger = logging.getLogger("backend")


class RecommendationService:
    """
    [Phase 3] Service for Resonance Ranking.
    Calculates semantic similarity between Candidate profiles and User Offer.
    """

    # Default "Offer" description (In a real app, this would come from User Settings)
    DEFAULT_OFFER_CONTEXT = """
    I am a software engineer looking for opportunities in AI/ML, full-stack development, 
    and autonomous agents. I have experience with Python, React, FastAPI, and LLMs.
    I want to connect with founders, CTOs, and recruiters hiring for these roles.
    """

    # Cache for offer embeddings (avoids recomputing for every lead in a scan)
    _offer_embedding_cache: Dict[str, list] = {}

    @classmethod
    def _get_offer_embedding(cls, context: str) -> Optional[list]:
        """Get or compute the embedding for an offer context string, with caching."""
        cache_key = context.strip()[:200]  # Use first 200 chars as key
        if cache_key in cls._offer_embedding_cache:
            return cls._offer_embedding_cache[cache_key]
        embedding = embeddings_service.generate_embedding(context)
        if embedding is not None:
            cls._offer_embedding_cache[cache_key] = embedding
        return embedding

    @classmethod
    def calculate_resonance_score(
        cls, candidate: Dict, offer_context: Optional[str] = None
    ) -> int:
        """
        Generates a 0-100 Resonance Score based on semantic match.
        """
        try:
            # 1. Construct Candidate Context
            candidate_text = (
                f"{candidate.get('title', '')} at {candidate.get('company', '')}. "
            )
            candidate_text += f"{candidate.get('summary', '')} "
            tags = candidate.get("tags")
            if tags:
                candidate_text += f"Tags: {', '.join(str(t) for t in tags)}"

            # 2. Get Embeddings (offer embedding is cached)
            context_to_match = (
                offer_context if offer_context else cls.DEFAULT_OFFER_CONTEXT
            )
            offer_emb = cls._get_offer_embedding(context_to_match)
            candidate_emb = embeddings_service.generate_embedding(candidate_text)

            # 3. Calculate Cosine Similarity (-1 to 1)
            if offer_emb is None or candidate_emb is None:
                return 0
            similarity = embeddings_service.calculate_similarity(
                offer_emb, candidate_emb
            )

            # 4. Normalize to 0-100 Score
            if similarity > 0.25:
                adjusted_similarity = (similarity - 0.25) / 0.75
            else:
                adjusted_similarity = 0

            score = max(0, min(100, int(adjusted_similarity * 100)))

            return score

        except Exception as e:
            logger.error(f"Failed to calculate resonance score: {e}")
            return 0


recommendation_service = RecommendationService()
