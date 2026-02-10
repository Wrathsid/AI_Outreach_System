import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.services.embeddings import embeddings_service
from backend.routers.drafts import calculate_asymmetry_score, score_draft, IntentType

def test_asymmetry():
    print("\n--- Testing Paragraph Asymmetry Guards ---")
    
    symmetrical_text = """Hi John, saw you're building in the agentic space. Really impressed by the recent launch.

Noticed you're hiring for a backend lead. Happy to share some thoughts on that soon."""
    
    asymmetrical_text = """Hi John, saw you're building in the agentic space. Really impressed by the recent launch. I've been following your work for a while now and love the direction you're taking with the new protocol.

Noticed you're hiring."""

    sym_score = calculate_asymmetry_score(symmetrical_text)
    asym_score = calculate_asymmetry_score(asymmetrical_text)
    
    print(f"Symmetrical text score adjustment: {sym_score}")
    print(f"Asymmetrical text score adjustment: {asym_score}")
    
    assert sym_score < asym_score, "Symmetrical text should be penalized more than asymmetrical text"
    print("✅ Asymmetry check passed!")

def test_embeddings():
    print("\n--- Testing Semantic Embeddings ---")
    text1 = "Saw your recent post about AI agents."
    text2 = "I noticed what you wrote regarding agentic systems recently."
    text3 = "Is it raining today?"
    
    emb1 = embeddings_service.generate_embedding(text1)
    emb2 = embeddings_service.generate_embedding(text2)
    emb3 = embeddings_service.generate_embedding(text3)
    
    sim12 = embeddings_service.calculate_similarity(emb1, emb2)
    sim13 = embeddings_service.calculate_similarity(emb1, emb3)
    
    print(f"Similarity (text1, text2): {sim12:.4f}")
    print(f"Similarity (text1, text3): {sim13:.4f}")
    
    assert sim12 > 0.6, "Related sentences should have high similarity"
    assert sim13 < 0.5, "Unrelated sentences should have low similarity"
    print("✅ Semantic similarity check passed!")

async def main():
    test_asymmetry()
    test_embeddings()
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
