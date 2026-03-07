from temporalio import activity
from typing import Dict
from datetime import timedelta
import logging

# Import existing logic instead of rewriting it!
from backend.services.email_verifier import verify_email

logger = logging.getLogger("temporal-activities")

@activity.defn
async def verify_email_activity(email: str) -> Dict:
    """
    Temporal Activity for verifying emails.
    If this function raises an exception (e.g., API timeout), 
    Temporal will automatically retry it according to the retry policy in the workflow.
    """
    logger.info(f"Running verify_email_activity for {email}")
    
    # We just call the existing function we already built!
    result = await verify_email(email)
    return result

@activity.defn
async def generate_email_pattern_activity(name: str, company: str) -> Dict:
    """
    Temporal Activity for predicting an email address based on name and company.
    """
    from backend.services.email_generator import EmailGenerator
    logger.info(f"Running generate_email_pattern_activity for {name} at {company}")
    result = EmailGenerator.get_best_guess(name, company)
    return result or {"email": None, "confidence": 0, "pattern": None, "is_generated": False}

@activity.defn
async def crawl_linkedin_activity(role: str, limit: int = 20) -> list:
    """
    Temporal Activity for crawling LinkedIn via SerpAPI.
    The original crawler uses a Python Async Generator to stream results to the UI.
    To make it durable in Temporal, we consume the stream and return a list of leads.
    """
    from backend.services.crawler import Crawler
    logger.info(f"Running crawl_linkedin_activity for role: {role} (limit: {limit})")
    crawler = Crawler()
    
    leads = []
    # Consume the async generator completely
    async for raw in crawler.crawl_stream(role, limit=limit):
        if raw["type"] == "raw_result":
            leads.append(raw["data"])
            
    return leads

@activity.defn
async def polish_leads_activity(raw_leads: list) -> list:
    """
    Temporal Activity that uses Gemini to clean up messy search results.
    It extracts proper names, complete sentences from truncated snippets,
    and identifies if the post is a hiring announcement.
    """
    from backend.config import generate_with_gemini
    import json
    
    if not raw_leads:
        return []

    logger.info(f"Polishing {len(raw_leads)} leads via Gemini...")
    
    # Prepare the prompt for batch processing to save tokens/time
    leads_context = ""
    for i, lead in enumerate(raw_leads):
        leads_context += f"LEAD {i}:\nTitle: {lead.get('title')}\nSnippet: {lead.get('body')}\nURL: {lead.get('url')}\n\n"

    prompt = f"""
    Internal Database Cleanup Task:
    I have a list of messy LinkedIn search results. For each one, I need you to reconstruct a clean, professional profile.
    
    CRITICAL RULES:
    1. NAME: Extract the ACTUAL PERSON'S NAME. LinkedIn titles often look like "John Doe on LinkedIn: I am hiring...". Just return "John Doe". 
    2. SUMMARY: The search snippets are often truncated mid-sentence (ending in ...). Reconstruct the snippet into ONE clean, professional sentence. If it's a hiring post, summarize that they are hiring.
    3. ROLE TYPE: Identify if this is a "person" profile or a "hiring_post".
    4. GREETING: If this is a hiring post by a person, identify the PERSON'S first name for a greeting.
    
    {leads_context}
    
    Return a JSON list of objects with these exact keys:
    [
      {{
        "id": (index from LEAD X),
        "name": "Clean Name",
        "title": "Professional Title (e.g. Recruiter at X)",
        "company": "Company Name",
        "summary": "One clean complete sentence summary.",
        "is_hiring_post": true/false
      }}
    ]
    
    Return ONLY valid JSON. No markdown formatting.
    """

    try:
        response_text = await generate_with_gemini(prompt)
        
        # Clean potential markdown from response
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        polished_data = json.loads(clean_json)
        
        # Map back to the original leads
        results = []
        for p in polished_data:
            idx = p.get("id")
            if idx is not None and idx < len(raw_leads):
                orig = raw_leads[idx]
                orig.update({
                    "name": p.get("name", "Unknown"),
                    "title": p.get("title", "Unknown"),
                    "company": p.get("company", "Unknown"),
                    "summary": p.get("summary", ""),
                    "is_hiring_post": p.get("is_hiring_post", False)
                })
                results.append(orig)
            
        return results if results else raw_leads
    except Exception as e:
        logger.error(f"Lead polishing failed: {e}")
        # Graceful fallback: return raw data if AI fails
        return raw_leads

async def polish_single_lead(lead: dict) -> dict:
    """
    Non-batch version of polishing. Processes a single lead via Gemini for ultra-low latency streaming.
    """
    from backend.config import generate_with_gemini
    import json
    
    prompt = f"""
    Internal Database Cleanup Task:
    I have a messy LinkedIn search result. Reconstruct a clean, professional profile.
    
    CRITICAL RULES:
    1. NAME: Extract ACTUAL PERSON'S NAME. Return "John Doe" not "John Doe on LinkedIn: I am hiring".
    2. SUMMARY: Reconstruct truncated snippets into ONE clean complete sentence.
    3. ROLE TYPE: Identify if "person" or "hiring_post".
    
    LEAD:
    Title: {lead.get('title')}
    Snippet: {lead.get('body')}
    URL: {lead.get('url')}
    
    Return a JSON object with EXACT keys:
    {{
      "name": "Clean Name",
      "title": "Professional Title (e.g. Recruiter at X)",
      "company": "Company Name",
      "summary": "One clean complete sentence summary.",
      "is_hiring_post": true/false
    }}
    
    Return ONLY valid JSON. No markdown formatting.
    """
    try:
        response_text = await generate_with_gemini(prompt)
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        p = json.loads(clean_json)
        
        lead.update({
            "name": p.get("name", "Unknown"),
            "title": p.get("title", "Unknown"),
            "company": p.get("company", "Unknown"),
            "summary": p.get("summary", ""),
            "is_hiring_post": p.get("is_hiring_post", False)
        })
        return lead
    except Exception as e:
        logger.error(f"Single lead polishing failed: {e}")
        return lead
