import os
import sys
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Load env variables
load_dotenv(dotenv_path=".env")

# Initialize Supabase & OpenAI
try:
    from supabase import create_client
    from backend.config import generate_with_gemini
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
except Exception as e:
    print(f"Failed to init dependencies: {e}")
    sys.exit(1)

async def generate_draft_content(candidate, user_settings):
    """
    Generates subject and body using OpenAI
    """
    prompt = f"""
    You are {user_settings['full_name']}, {user_settings['role']} at {user_settings['company']}.
    Write a cold email to:
    Name: {candidate['name']}
    Role: {candidate['title']}
    Company: {candidate['company']}
    Summary: {candidate.get('summary', 'No summary')}
    
    Goal: Schedule a 15-min chat about collaboration.
    Tone: Professional, concise, friendly.
    
    Format:
    Subject: [Subject Line]
    [Body Paragraphs]
    [Sign-off]
    
    Keep it under 150 words.
    """
    
    try:
        content = await generate_with_gemini(
            prompt,
            system_prompt="You are an expert copywriter."
        )
        
        if content:
            # Parse Subject
            lines = content.strip().split('\n')
            subject = "Quick Question"
            body_start = 0
            
            for i, line in enumerate(lines):
                if line.lower().startswith("subject:"):
                    subject = line.replace("Subject:", "").strip().replace("*", "")
                    body_start = i + 1
                    break
                    
            body = "\n".join(lines[body_start:]).strip()
            return subject, body
        return None, None
        
    except Exception as e:
        print(f"  ! Gen Error: {e}")
        return None, None

async def process_drafts(limit=50):
    print("Fetching candidates eligible for drafts...")
    
    # Get candidates who don't have drafts yet
    # Supabase doesn't support complex NOT IN / Join filter easily via REST, so we filter in python for simplicity
    # fetch all candidates
    candidates_res = supabase.table("candidates").select("*").order("created_at", desc=True).limit(200).execute()
    all_candidates = candidates_res.data
    
    # fetch all draft candidate_ids
    drafts_res = supabase.table("drafts").select("candidate_id").execute()
    existing_ids = set(d['candidate_id'] for d in drafts_res.data)
    
    # Filter: Unknown company is OK, but Enriched is better. We just want to ensure we don't duplicate.
    to_process = [c for c in all_candidates if c['id'] not in existing_ids][:limit]
    
    print(f"Found {len(to_process)} candidates needing drafts.")
    
    # Get User Settings for context
    settings = {"full_name": "Siddharth", "company": "Antigravity", "role": "Founder"}
    try:
        s_res = supabase.table("user_settings").select("*").limit(1).execute()
        if s_res.data: settings = s_res.data[0]
    except: pass
    
    count = 0
    for c in to_process:
        print(f"Drafting for: {c['name']} @ {c['company']}...")
        
        subject, body = await generate_draft_content(c, settings)
        
        if subject and body:
            supabase.table("drafts").insert({
                "candidate_id": c['id'],
                "subject": subject,
                "body": body,
                "status": "draft"
            }).execute()
            print(f"  -> Created Draft: '{subject}'")
            count += 1
            await asyncio.sleep(0.5) # Rate limit protection
            
    print(f"Done. Generated {count} drafts.")

if __name__ == "__main__":
    if sys.platform == 'win32':
         asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(process_drafts(limit=100))
