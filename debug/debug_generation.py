
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load env before importing backend modules
load_dotenv(dotenv_path="c:\\Users\\Siddharth\\OneDrive\\Desktop\\Cold emailing\\.env")

# Add project root to sys.path
sys.path.append("c:\\Users\\Siddharth\\OneDrive\\Desktop\\Cold emailing")

from backend.config import generate_with_gemini, gemini_model
from backend.routers.drafts import generate_with_scoring

async def test_gemini_direct():
    print("\n--- Testing Direct Gemini API ---")
    if not gemini_model:
        print("ERROR: gemini_model is None")
        return
    
    try:
        response = await generate_with_gemini("Say hello", temperature=0.7)
        print(f"Direct Response: {response}")
    except Exception as e:
        print(f"Direct Error: {e}")

async def test_scoring_logic():
    print("\n--- Testing Scoring Logic ---")
    # Mock candidate context
    ctx = {
        'name': 'Test Candidate',
        'company': 'Test Corp',
        'title': 'Senior Engineer',
        'intent': 'curious'
    }
    
    try:
        result = await generate_with_scoring(
            prompt="Draft a LinkedIn message for a Senior Engineer at Test Corp.",
            contact_type="linkedin",
            candidate_context=ctx,
            num_variants=1
        )
        print(f"Scoring Result: {result}")
    except Exception as e:
        print(f"Scoring Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    await test_gemini_direct()
    await test_scoring_logic()

if __name__ == "__main__":
    asyncio.run(main())
