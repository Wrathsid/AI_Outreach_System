import json
import logging
from backend.config import generate_with_gemini

logger = logging.getLogger("lead-processor")

async def polish_leads_activity(raw_leads: list) -> list:
    """
    Uses Gemini to clean up messy search results.
    It extracts proper names, complete sentences from truncated snippets,
    and identifies if the post is a hiring announcement.
    """
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
        
        if not isinstance(response_text, str):
            logger.warning("Gemini AI did not return a valid string response. Skipping polishing.")
            return raw_leads
            
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
    prompt = f"""
    Internal Database Cleanup Task:
    I have a messy LinkedIn search result. Reconstruct a clean, professional profile.
    
    CRITICAL RULES:
    1. NAME: Extract ACTUAL PERSON'S NAME. Return "John Doe" not "John Doe on LinkedIn: I am hiring".
    2. SUMMARY: Reconstruct truncated snippets into ONE clean complete sentence.
    3. ROLE TYPE (is_hiring_post): EXTREMELY STRICT. Set to true ONLY IF the post is an actual job listing, hiring announcement, or candidate search. Set to false if it is a general discussion, an opinion piece, a complaint about interviews, or an advertisement for a service.
    
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
        
        if not isinstance(response_text, str):
            logger.warning("Gemini AI did not return a valid string response. Skipping polishing.")
            return lead
            
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
