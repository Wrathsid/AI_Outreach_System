import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from routers.drafts import get_supabase

supabase = get_supabase()
res = (
    supabase.table("drafts")
    .select("body, candidates(name)")
    .order("created_at", desc=True)
    .limit(3)
    .execute()
)
for d in res.data:
    print(f"Name: {d['candidates']['name']}")
    print(f"Draft:\n{d['body']}")
    print(f"Length: {len(d['body'])}\n---")
