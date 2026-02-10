import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import UploadFile

# Mock imports that might try to connect to things
sys.modules["backend.config"] = MagicMock()
from backend.routers import settings, stats

async def test_phase_4():
    print("--- Verifying Phase 4: Resume & Analytics ---")

    # --- Test 1: Resume Upload Logic ---
    print("\n1. Testing Resume Upload Logic...")
    
    # Mock dependencies
    with patch('backend.routers.settings.get_supabase') as mock_get_supabase, \
         patch('backend.routers.settings.generate_with_gemini', new_callable=AsyncMock) as mock_gemini:
        
        # Setup Mocks
        mock_db = MagicMock()
        mock_get_supabase.return_value = mock_db
        
        # Mock Geminin response
        mock_gemini.return_value = '''
        {
            "full_name": "Test User",
            "company": "Test Corp",
            "skills": ["Python", "FastAPI", "React"]
        }
        '''

        # Mock File
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "resume.txt"
        mock_file.read.return_value = b"This is a dummy resume for Test User at Test Corp. Skills: Python, FastAPI."

        # Call endpoint function directly
        result = await settings.upload_file(mock_file)
        
        # Assertions
        print(f"   Upload Result: {result['status']}")
        assert result["status"] == "uploaded"
        assert "Python" in result["extracted_skills"]
        assert result["filename"] == "resume.txt"
        
        # Verify DB updates
        # Should update brain_context
        assert mock_db.table.call_args_list[0][0][0] == "brain_context"
        print("   ✅ Resume processed and DB update triggered")


    # --- Test 2: Analytics Funnel Logic ---
    print("\n2. Testing Analytics Funnel Logic...")

    with patch('backend.routers.stats.get_supabase') as mock_get_supabase:
        mock_db = MagicMock()
        mock_get_supabase.return_value = mock_db

        # Mock Data: 10 candidates. 5 Contacted. 2 Replied.
        # Statuses: 5 'new', 3 'contacted', 2 'replied' -> Total 10. Contacted = 5 (3+2). Replied = 2.
        mock_data = [
            {"id": 1, "status": "new"},
            {"id": 2, "status": "new"},
            {"id": 3, "status": "new"},
            {"id": 4, "status": "new"},
            {"id": 5, "status": "new"},
            {"id": 6, "status": "contacted"},
            {"id": 7, "status": "contacted"},
            {"id": 8, "status": "contacted"},
            {"id": 9, "status": "replied"},
            {"id": 10, "status": "replied"},
        ]
        
        mock_db.table.return_value.select.return_value.execute.return_value.data = mock_data

        # Call endpoint
        result = await stats.get_funnel_stats()
        
        # Assertions
        print(f"   Funnel Result: {result}")
        
        # Total
        assert result["total_candidates"] == 10
        
        # Funnel Stages
        found = next(item for item in result["funnel"] if item["stage"] == "Found")
        contacted = next(item for item in result["funnel"] if item["stage"] == "Contacted")
        replied = next(item for item in result["funnel"] if item["stage"] == "Replied")
        
        assert found["count"] == 10
        assert found["percent"] == 100
        
        assert contacted["count"] == 5
        assert contacted["percent"] == 50.0  # 5/10
        
        assert replied["count"] == 2
        assert replied["percent"] == 20.0    # 2/10
        
        # Conversions
        assert result["conversions"]["found_to_contacted"] == 50.0
        assert result["conversions"]["contacted_to_replied"] == 40.0 # 2/5 = 40%

        print("   ✅ Funnel calculations correct")

    print("\n✅ Phase 4 Verification Compelte!")

if __name__ == "__main__":
    asyncio.run(test_phase_4())
