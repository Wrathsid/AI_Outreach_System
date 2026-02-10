
import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv(dotenv_path="c:\\Users\\Siddharth\\OneDrive\\Desktop\\Cold emailing\\.env")
sys.path.append("c:\\Users\\Siddharth\\OneDrive\\Desktop\\Cold emailing")

from backend.routers.drafts import generate_draft
from fastapi import HTTPException

async def test_endpoint():
    print("\n--- Testing generate_draft Endpoint ---")
    candidate_id = 238
    
    try:
        result = await generate_draft(candidate_id, contact_type="linkedin")
        print("SUCCESS! Result:")
        print(result)
    except HTTPException as he:
        print(f"HTTPException caught: {he.detail}")
    except Exception as e:
        print(f"General Exception caught: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_endpoint())
