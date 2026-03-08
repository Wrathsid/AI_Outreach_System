import logging
from typing import List, Dict, Optional
from backend.services.embeddings import embeddings_service

logger = logging.getLogger("backend")

class RecommendationService:
    """
    [Phase 3] Service for Resonance Ranking.
    Calculates semantic similarity between Candidate profiles and User Offer.
    """
    
    # Default "Offer" description (In a real app, this would come from User Settings)
    # This represents what the user is "selling" or "looking for".
    DEFAULT_OFFER_CONTEXT = """
    I am a software engineer looking for opportunities in AI/ML, full-stack development, 
    and autonomous agents. I have experience with Python, React, FastAPI, and LLMs.
    I want to connect with founders, CTOs, and recruiters hiring for these roles.
    """

    @classmethod
    def calculate_resonance_score(cls, candidate: Dict, offer_context: Optional[str] = None) -> int:
        """
        Generates a 0-100 Resonance Score based on semantic match.
        """
        try:
            # 1. Construct Candidate Context
            # Combine Title + Summary + Tags for a rich representation
            candidate_text = f"{candidate.get('title', '')} at {candidate.get('company', '')}. "
            candidate_text += f"{candidate.get('summary', '')} "
            if candidate.get('tags'):
                candidate_text += f"Tags: {', '.join(candidate.get('tags'))}"
            
            # 2. Get Embeddings
            context_to_match = offer_context if offer_context else cls.DEFAULT_OFFER_CONTEXT
            offer_emb = embeddings_service.generate_embedding(context_to_match)
            candidate_emb = embeddings_service.generate_embedding(candidate_text)
            
            # 3. Calculate Cosine Similarity (-1 to 1)
            similarity = embeddings_service.calculate_similarity(offer_emb, candidate_emb)
            
            # 4. Normalize to 0-100 Score
            # We treat < 0 similarity as 0 relevance.
            # We square the similarity to stretch the distribution for better UI differentiation.
            if similarity > 0:
                adjusted_similarity = similarity ** 2
            else:
                adjusted_similarity = 0
                
            score = max(0, int(adjusted_similarity * 100))
            
            return score
            
        except Exception as e:
            logger.error(f"Failed to calculate resonance score: {e}")
            return 0

recommendation_service = RecommendationService()
