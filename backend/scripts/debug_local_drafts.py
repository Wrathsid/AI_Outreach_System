import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from routers.drafts import generate_draft, get_supabase
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

async def run_draft():
    sb = get_supabase()
    print("Clearing drafts for Candidate 239...")
    sb.table("drafts").delete().eq("candidate_id", 239).execute()
    
    print("Generating fresh draft locally for Candidate 239...")
    try:
        res = await generate_draft(239, "linkedin")
        print("\n--- GENERATE DRAFT RESPONSE ---")
        print("Type:", res.get("type"))
        text = res.get("message", "")
        print("Length:", len(text))
        print("Message:")
        print(text)
        print("-------------------------------")
    except Exception as e:
        print("Error generating draft:", e)

if __name__ == "__main__":
    asyncio.run(run_draft())
