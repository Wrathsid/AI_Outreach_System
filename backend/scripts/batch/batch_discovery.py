import asyncio
import os
import sys
import json
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
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase credentials missing")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Failed to init Supabase: {e}")
    sys.exit(1)

# Import services
try:
    from services.discovery_orchestrator import DiscoveryOrchestrator
except ImportError:
    # Handle case where we might need to adjust path if not running as module
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "services"))
    from services.discovery_orchestrator import DiscoveryOrchestrator

# List of 20 Tech Roles
ROLES = [
    "Python Developer", 
    "React Developer", 
    "Java Developer", 
    "JavaScript Developer",
    "Frontend Developer", 
    "Backend Developer", 
    "Full Stack Developer", 
    "DevOps Engineer",
    "Data Scientist", 
    "Machine Learning Engineer", 
    "UI/UX Designer", 
    "Product Manager",
    "iOS Developer", 
    "Android Developer", 
    "QA Engineer", 
    "Cloud Engineer",
    "Cyber Security Analyst", 
    "Go Developer", 
    "Rust Developer", 
    "CTO"
]

async def run_batch_discovery():
    print(f"Starting batch discovery for {len(ROLES)} roles...")
    print("This process will search for leads and save unique ones to Supabase.")
    
    orchestrator = DiscoveryOrchestrator()
    stats = {}
    total_new = 0

    for role in ROLES:
        print(f"\n[{role}] Scanning...")
        leads_found_for_role = 0
        
        # We limit to 5 per role to keep execution time reasonable (~2-3 mins total)
        # Increase limit if deeper search is needed
        async for item_json in orchestrator.discover_leads_stream(role, limit=5):
            try:
                item = json.loads(item_json)
                
                if item["type"] == "status":
                    # print(f"  > {item['data']}") # Verbose
                    pass

                elif item["type"] == "result":
                    lead = item["data"]
                    
                    # Logic to save to Supabase (Avoid Duplicates)
                    try:
                        exists = False
                        
                        # check linkedin
                        if lead.get("linkedin_url"):
                            res = supabase.table("candidates").select("id").eq("linkedin_url", lead["linkedin_url"]).execute()
                            if res.data: exists = True
                        
                        # check email (if present and we haven't matched yet)
                        if not exists and lead.get("email"):
                            res = supabase.table("candidates").select("id").eq("email", lead["email"]).execute()
                            if res.data: exists = True
                        
                        if not exists:
                            # Insert
                            payload = {
                                "name": lead.get("name") or "Unknown",
                                "title": lead.get("title") or role,
                                "company": lead.get("company") or "Unknown",
                                "email": lead.get("email"),
                                "linkedin_url": lead.get("linkedin_url"),
                                "summary": lead.get("summary"),
                                "match_score": 50, # Initial score, can be updated later
                                "status": "new",
                                "tags": [role, "batch_scan"]
                            }
                            supabase.table("candidates").insert(payload).execute()
                            leads_found_for_role += 1
                            total_new += 1
                            print(f"  + SAVED: {lead.get('name')} @ {lead.get('company')}")
                        else:
                            print(f"  . EXISTS: {lead.get('name')}")
                            
                    except Exception as db_err:
                        print(f"  ! DB Error: {db_err}")

            except json.JSONDecodeError:
                pass
            except Exception as e:
                print(f"  ! Stream Error: {e}")

        stats[role] = leads_found_for_role
        print(f"  -> Processed {role}: Saved {leads_found_for_role} new leads.")

    # --- REPORT ---
    print("\n" + "="*50)
    print("BATCH DISCOVERY REPORT")
    print("="*50)
    print(f"{'ROLE':<30} | {'NEW LEADS'}")
    print("-" * 50)
    for role in ROLES:
        print(f"{role:<30} | {stats.get(role, 0)}")
    print("-" * 50)
    print(f"TOTAL NEW LEADS: {total_new}")
    print("="*50)

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(run_batch_discovery())
    except KeyboardInterrupt:
        print("\nAborted by user.")
