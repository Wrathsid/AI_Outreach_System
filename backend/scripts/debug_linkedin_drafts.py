import sys
import os
import asyncio

# Add backend dir to python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from routers.drafts import generate_draft, get_supabase


async def test_generation():
    supabase = get_supabase()
    # Force delete all drafts to bypass fingerprint idempotency cache
    print("Clearing old drafts...")
    try:
        supabase.table("drafts").delete().neq("id", 0).execute()
    except Exception:
        pass

    # Get 3 candidates
    res = supabase.table("candidates").select("*").limit(3).execute()
    for c in res.data:
        print(f"--- CANDIDATE: {c.get('name')} | {c.get('title')} ---")
        try:
            # Generate a fresh draft
            draft = await generate_draft(c["id"], contact_type="linkedin")
            if draft:
                print("DRAFT:")
                print(draft.get("message", ""))
                print("SCORE:", draft.get("quality_score"))
                print("LENGTH:", len(draft.get("message", "")))
            else:
                print("No draft returned.")
        except Exception as e:
            print("ERROR:", e)
        print("\n")


if __name__ == "__main__":
    asyncio.run(test_generation())
