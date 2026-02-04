import os
import sys
import asyncio
import json
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load env variables
load_dotenv(dotenv_path=".env")

# Initialize Supabase & Groq
try:
    from supabase import create_client
    from groq import Groq
    from services.crawler import Crawler # Reuse the crawler for search
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    groq_client = Groq(api_key=GROQ_API_KEY)
    crawler = Crawler()
    
except Exception as e:
    print(f"Failed to init dependencies: {e}")
    sys.exit(1)

async def search_google_snippet(query):
    # Reuse the crawler's internal methods or just call its logic
    # Since crawler yields, we iterate
    snippets = []
    print(f"  > Searching: {query}")
    try:
        # We use a custom limit 3 to save time/quota
        async for item in crawler.crawl_stream(query, limit=3):
            if item["type"] == "raw_result":
                snippets.append(f"Title: {item['data']['title']}\nSnippet: {item['data']['body']}")
    except Exception as e:
        print(f"Search error: {e}")
    return "\n---\n".join(snippets[:3])

def extract_company_with_ai(name, title, search_context):
    prompt = f"""
    Find the current company for this person based on the search results.
    Person: {name}
    Role: {title}
    
    Search Results:
    {search_context}
    
    Return ONLY the Company Name. If not found or ambiguous, return 'Unknown'.
    Do not included 'at' or 'Inc' unless necessary. keeping it short.
    """
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a data extractor. Return pure company name or 'Unknown'."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI Error: {e}")
        return "Unknown"

async def enrich_batch(limit=20):
    # Fetch leads with Unknown company but valid names
    print(f"Fetching up to {limit} enrichable leads...")
    
    res = supabase.table("candidates").select("*").eq("company", "Unknown").limit(100).execute()
    leads = res.data
    
    # Filter out generic names
    valid_leads = [
        l for l in leads 
        if "hiring" not in l["name"].lower() 
        and "manager" not in l["name"].lower()
        and "unknown" not in l["name"].lower()
    ]
    
    to_process = valid_leads[:limit]
    
    if not to_process:
        print("No valid leads to enrich.")
        return

    print(f"Enriching {len(to_process)} leads...")
    
    enriched_count = 0
    
    for lead in to_process:
        print(f"\nProcessing: {lead['name']} ({lead['title']})")
        
        # 1. Search
        query = f"{lead['name']} {lead['title']} linkedin"
        context = await search_google_snippet(query)
        
        if not context:
            print("  ! No search results found.")
            continue
            
        # 2. Extract
        company = extract_company_with_ai(lead['name'], lead['title'], context)
        
        # 3. Update
        if company and company != "Unknown" and len(company) < 50:
            print(f"  -> FOUND: {company}")
            supabase.table("candidates").update({"company": company}).eq("id", lead["id"]).execute()
            enriched_count += 1
        else:
            print("  . Could not identify company.")

    print(f"\nDone. Enriched {enriched_count} leads.")

if __name__ == "__main__":
    if sys.platform == 'win32':
         asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(enrich_batch(limit=100))
