"""
Drafts router - Draft management and AI generation.
"""
from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime

from config import get_supabase, get_groq_client, generate_with_groq, GROQ_API_KEY
from models.schemas import Draft, DraftCreate

router = APIRouter(tags=["Drafts"])


@router.get("", response_model=List[Draft])
def get_all_drafts():
    """Get all drafts with candidate info."""
    supabase = get_supabase()
    if supabase:
        result = supabase.table("drafts").select("*, candidates(name, company)").eq("status", "draft").order("created_at", desc=True).execute()
        drafts = []
        for d in result.data:
            draft = {
                "id": d["id"],
                "candidate_id": d["candidate_id"],
                "subject": d["subject"],
                "body": d["body"],
                "status": d["status"],
                "candidate_name": d["candidates"]["name"] if d.get("candidates") else None,
                "candidate_company": d["candidates"]["company"] if d.get("candidates") else None
            }
            drafts.append(draft)
        return drafts
    return []


@router.post("", response_model=Draft)
def create_draft(draft: DraftCreate):
    """Create a new draft."""
    supabase = get_supabase()
    if supabase:
        result = supabase.table("drafts").insert(draft.model_dump()).execute()
        if result.data:
            candidate = supabase.table("candidates").select("name").eq("id", draft.candidate_id).single().execute()
            supabase.table("activity_log").insert({
                "candidate_id": draft.candidate_id,
                "action_type": "draft_created",
                "title": f"Drafted email to {candidate.data['name'] if candidate.data else 'Unknown'}",
                "description": "AI generated based on profile"
            }).execute()
            return {**result.data[0], "candidate_name": None, "candidate_company": None}
    raise HTTPException(status_code=500, detail="Failed to create draft")


@router.post("/polish")
async def polish_draft(request: dict):
    """Fix grammar and improve tone of draft."""
    text = request.get("text", "")
    if not text:
        return {"text": ""}
    
    client = get_groq_client()
    if GROQ_API_KEY and client:
        try:
            completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional editor. Fix grammar, spelling, and improve flow. Keep the tone professional but conversational. Return ONLY the polished text. Do not add intro/outro."
                    },
                    {"role": "user", "content": text}
                ],
                model="llama-3.3-70b-versatile",
            )
            return {"text": completion.choices[0].message.content.strip()}
        except Exception as e:
            print(f"Polish error: {e}")
            return {"text": text}
    
    return {"text": text}


@router.post("/generate/{candidate_id}")
async def generate_draft(candidate_id: int, context: str = ""):
    """Generate AI draft for a candidate using Groq with full context."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    # Get candidate info
    candidate_res = supabase.table("candidates").select("*").eq("id", candidate_id).single().execute()
    if not candidate_res.data:
        raise HTTPException(status_code=404, detail="Candidate not found")
    c = candidate_res.data
    
    # Get User Settings
    settings = {"full_name": "User", "company": "My Company", "role": "Professional"}
    try:
        settings_res = supabase.table("user_settings").select("*").eq("id", 1).execute()
        if settings_res.data:
            settings = settings_res.data[0]
    except Exception as e:
        print(f"Failed to fetch settings: {e}")

    # Get Brain Context
    brain = {"extracted_skills": [], "formality": "Professional", "anecdotes": ""}
    try:
        brain_res = supabase.table("brain_context").select("*").eq("id", 1).execute()
        if brain_res.data:
            brain = brain_res.data[0]
            if not brain.get("extracted_skills"):
                brain["extracted_skills"] = []
    except Exception as e:
        print(f"Failed to fetch brain: {e}")
        
    if GROQ_API_KEY:
        skills_str = ", ".join(brain["extracted_skills"]) if brain["extracted_skills"] else "General Professional Skills"
        
        prompt = f"""
[ROLE]
You are {settings['full_name']}, the {settings['role']} at {settings['company']}.
Your core expertise/skills: {skills_str}.
Your speaking style: {brain.get('formality', 'Professional')}.
Detail Level: {brain.get('detail_level', 'Concise')}.

[OBJECTIVE]
Write a personalized cold outreach email to a potential candidate/lead.

[RECIPIENT]
Name: {c['name']}
Title: {c.get('title', 'Professional')}
Company: {c.get('company', 'their company')}
Summary: {c.get('summary', 'No additional context')}

[ADDITIONAL CONTEXT]
{context if context else 'None'}
Anecdotes to potentially use: {brain.get('anecdotes', '')}

[REQUIREMENTS]
1. Start with "Subject:" on the first line.
2. Be brief (under 120 words).
3. Reference their work/summary specifically.
4. Relate it to YOUR expertise ({skills_str}) if relevant.
5. End with a clear Call to Action (CTA).
6. Sign off as {settings['full_name']}.
"""
        
        ai_response = await generate_with_groq(prompt)
        
        if ai_response:
            lines = ai_response.strip().split('\n')
            subject = "Cold Outreach"
            body_start_index = 0
            
            for i, line in enumerate(lines):
                if "Subject:" in line or "**Subject:**" in line:
                    subject = line.replace("Subject:", "").replace("**Subject:**", "").strip()
                    body_start_index = i + 1
                    break
            
            body = "\n".join(lines[body_start_index:]).strip()
            
            result = supabase.table("drafts").insert({
                "candidate_id": candidate_id,
                "subject": subject,
                "body": body
            }).execute()
            
            supabase.table("activity_log").insert({
                "candidate_id": candidate_id,
                "action_type": "draft_created",
                "title": f"Drafted email to {c['name']}",
                "description": "AI used your Brain & Settings"
            }).execute()
            
            return {"subject": subject, "body": body, "draft_id": result.data[0]["id"] if result.data else None}
    
    # Fallback template
    subject = f"Connect: {settings['company']} x {c.get('company', 'You')}"
    body = f"""Hi {c['name']},

I'm {settings['full_name']} from {settings['company']}. I noticed your work at {c.get('company', 'your company')} and was impressed.

Given your background in {c.get('title', 'the industry')}, I think we see things similarly.

Best,
{settings['full_name']}"""
    
    result = supabase.table("drafts").insert({
        "candidate_id": candidate_id,
        "subject": subject,
        "body": body
    }).execute()
    
    return {"subject": subject, "body": body, "draft_id": result.data[0]["id"] if result.data else None}
