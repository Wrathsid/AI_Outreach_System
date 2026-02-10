
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load env before importing backend modules
load_dotenv(dotenv_path="c:\\Users\\Siddharth\\OneDrive\\Desktop\\Cold emailing\\.env")
sys.path.append("c:\\Users\\Siddharth\\OneDrive\\Desktop\\Cold emailing")

from backend.config import get_supabase
from backend.routers.drafts import generate_fallback_draft, calculate_time_to_read

async def test_fallback_logic():
    print("\n--- Testing Fallback Logic ---")
    
    # Mock Data
    c = {
        'name': 'Test Candidate',
        'company': 'Test Corp',
        'title': 'Senior Engineer'
    }
    sender_intro = "Siddharth from Antigravity"
    signal = {'signal': 'Technical Leadership', 'type': 'technical_role'}
    intent = "curious"
    contact_type = "linkedin"
    
    try:
        print("Attempting to generate fallback draft...")
        draft = generate_fallback_draft(c, sender_intro, signal['signal'], intent, contact_type)
        print(f"Fallback Draft: {draft}")
        
        # Test DB Insert (Mocking the structure)
        # We won't actually insert to DB to avoid polluting, but we'll check variables
        import uuid
        variant_id = "fallback-" + str(uuid.uuid4())
        gen_params = {
            "variant_id": variant_id,
            "score": 50.0,
            "model": "fallback-template",
            "context_band": "LOW",
            "signal_type": signal.get('type', 'generic')
        }
        
        print(f"Gen Params: {gen_params}")
        print("Fallback logic seems VALID.")
        
    except Exception as e:
        print(f"Fallback Logic Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fallback_logic())
