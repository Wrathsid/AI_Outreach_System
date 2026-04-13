from backend.config import get_supabase
import asyncio

def test():
    supabase = get_supabase()
    res = supabase.table("brain_context").select("*").limit(1).execute()
    print("Brain Context:", res.data)
    
test()
