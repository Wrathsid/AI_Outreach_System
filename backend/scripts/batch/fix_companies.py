import os
import sys
import asyncio
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load env variables
load_dotenv(dotenv_path=".env")

# Initialize Supabase
try:
    from supabase import create_client
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Failed to init Supabase: {e}")
    sys.exit(1)

from services.hr_extractor import parse_linkedin_title

def fix_leads():
    print("Fetching leads with 'Unknown' company...")
    
    # Fetch candidates with Unknown company but valid title (we store original title somewhere? 
    # Actually wait, we stored PARSED title in 'title'. We might have lost the original full string if we didn't save it.
    # checking batch_discovery.py: 
    # "title": lead.get("title")
    # In discovery_orchestrator.py: 
    # title = data.get("title", "") -> parsed = parse_linkedin_title(title) -> lead['title'] = parsed['role']
    # Ah, we lost the original full title in the DB row! 
    # BUT wait, 'name' might contain the full string if parsing failed initially?
    # In old logic: if len(parts) < 2, name = title.
    # So for the ones where parsing totally failed, 'name' might be the full string.
    
    # Let's try to fix those where Name looks too long or has " - " inside it.
    
    candidates = supabase.table("candidates").select("*").eq("company", "Unknown").execute()
    data = candidates.data
    
    print(f"Found {len(data)} candidates to check.")
    
    fixed_count = 0
    
    for c in data:
        original_name = c["name"]
        
        # Check if name contains separators that imply it's actually a full title string
        if any(x in original_name for x in [" - ", " | ", " at ", " – "]):
            print(f"Re-parsing: {original_name}")
            new_data = parse_linkedin_title(original_name)
            
            if new_data["company"] != "Unknown":
                # update
                print(f"  -> FIXED: {new_data['name']} / {new_data['role']} @ {new_data['company']}")
                
                supabase.table("candidates").update({
                    "name": new_data["name"],
                    "title": new_data["role"],
                    "company": new_data["company"]
                }).eq("id", c["id"]).execute()
                
                fixed_count += 1
            else:
                print(f"  -> Still Unknown: {new_data}")
        
    print(f"Fix Complete. Fixed {fixed_count} records.")

if __name__ == "__main__":
    fix_leads()
