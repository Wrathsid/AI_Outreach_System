from backend.services.recommendation import recommendation_service

def verify_resonance():
    print("--- Verifying Resonance Ranking (Semantic Match) ---")
    
    # 1. Define Test Candidates
    # Candidate A: Highly Relevant (Target: AI Engineer)
    candidate_a = {
        "title": "Machine Learning Engineer",
        "company": "TechCorp AI",
        "summary": "Building autonomous agents and LLM applications using Python and LangChain.",
        "tags": ["AI", "Python", "LLMs"]
    }
    
    # Candidate B: Irrelevant (Target: Marketing)
    candidate_b = {
        "title": "Senior Marketing Manager",
        "company": "AdGlobal",
        "summary": "Expert in digital marketing strategies, SEO, and brand growth.",
        "tags": ["Marketing", "SEO", "Branding"]
    }
    
    # 2. Calculate Scores
    print("\nCalculating Score for Candidate A (AI Engineer)...")
    score_a = recommendation_service.calculate_resonance_score(candidate_a)
    print(f"Score A: {score_a}/100")
    
    print("\nCalculating Score for Candidate B (Marketing Manager)...")
    score_b = recommendation_service.calculate_resonance_score(candidate_b)
    print(f"Score B: {score_b}/100")
    
    # 3. Assertions
    # A should be significantly higher than B
    assert score_a > score_b, f"Error: Relevant candidate ({score_a}) should score higher than irrelevant ({score_b})"
    assert score_a > 50, f"Error: Relevant candidate score ({score_a}) is too low"
    assert score_b < 50, f"Error: Irrelevant candidate score ({score_b}) is too high"
    
    print("\n✅ Resonance Ranking Verified!")

if __name__ == "__main__":
    try:
        verify_resonance()
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
