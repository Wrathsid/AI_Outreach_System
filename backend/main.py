from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import httpx
import sys
import json

# Ensure backend directory is in path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# from services.scanner import search_leads

# Load environment variables
load_dotenv(dotenv_path="../.env")

app = FastAPI(title="Cold Emailing Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment Variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Supabase client
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[OK] Supabase connected")
    except Exception as e:
        print(f"[ERR] Supabase not connected: {e}")
else:
    print("[WARN] Supabase credentials not found - using local storage")

if GROQ_API_KEY:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        print("[OK] Groq API configured")
    except ImportError:
        print("[WARN] Groq library not installed")
        client = None
else:
    print("[WARN] GROQ_API_KEY not found - AI features disabled")
    client = None
    print("[WARN] Groq API key not found - using template drafts")

# Models
class Candidate(BaseModel):
    id: int
    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    avatar_url: Optional[str] = None
    match_score: int = 0
    summary: Optional[str] = None
    tags: Optional[List[str]] = []
    status: Optional[str] = "new"

class CandidateCreate(BaseModel):
    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    avatar_url: Optional[str] = None
    match_score: int = 0
    summary: Optional[str] = None
    tags: Optional[List[str]] = []

class Draft(BaseModel):
    id: int
    candidate_id: int
    subject: str
    body: str
    status: str = "draft"
    candidate_name: Optional[str] = None
    candidate_company: Optional[str] = None

class DraftCreate(BaseModel):
    candidate_id: int
    subject: str
    body: str

class SendEmailRequest(BaseModel):
    candidate_id: Optional[int] = None
    to: str
    subject: str
    body: str

class ActivityLog(BaseModel):
    id: int
    action_type: str
    title: str
    description: Optional[str] = None
    created_at: str
    candidate_id: Optional[int] = None

class DashboardStats(BaseModel):
    weekly_goal_percent: int
    people_found: int
    emails_sent: int
    replies_received: int

# ==================== GROQ AI HELPER ====================

async def generate_with_groq(prompt: str) -> str:
    """Generate text using Groq API (Llama 3.3 70B)"""
    if not GROQ_API_KEY:
        return None
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are an expert at writing personalized cold outreach emails that get responses. Keep emails short, personal, and compelling."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            print(f"Groq API error: {response.status_code} - {response.text}")
            return None

# ==================== ENDPOINTS ====================

@app.get("/")
def read_root():
    return {
        "status": "System Optimal",
        "supabase": "connected" if supabase else "not configured",
        "groq": "connected" if GROQ_API_KEY else "not configured"
    }

from fastapi.responses import JSONResponse, StreamingResponse

# ... imports ...

# ...
# ...
# Ensure backend directory is in path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.discovery_orchestrator import DiscoveryOrchestrator
# from services.crawler import crawl_company_emails
# from services.email_patterns import generate_email_patterns
# from services.confidence import calculate_confidence

# Initialize Orchestrator
orchestrator = DiscoveryOrchestrator()

# ...

class ExtractionRequest(BaseModel):
    text: str

class CrawlRequest(BaseModel):
    domain: str

class PatternRequest(BaseModel):
    first_name: str
    last_name: Optional[str] = ""
    domain: str

@app.post("/extract-opportunity")
def extract_opportunity(request: ExtractionRequest):
    """Extract key info from job description text"""
    if not GROQ_API_KEY:
        return {"opportunity": "AI not configured"}
        
    try:
        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Extract the core value proposition and key requirement from this text. Summarize it in one concise sentence starting with 'Opportunity to...' or 'Seeking...'"
                },
                {
                    "role": "user", 
                    "content": request.text
                }
            ],
            model="llama3-8b-8192"
        )
        return {"opportunity": completion.choices[0].message.content}
    except Exception as e:
        print(f"Extraction Error: {e}")
        return {"opportunity": "Could not extract context"}

# ---------- DISCOVERY ----------

# @app.post("/discovery/crawl")
# def crawl_domain(request: CrawlRequest):
#     """Method 2: Safe Website Crawler"""
#     print(f"[CRAWLER] Scanning {request.domain}...")
#     # emails = crawl_company_emails(request.domain)
#     return {"results": []}

# @app.post("/discovery/pattern")
# def guess_pattern(request: PatternRequest):
#     """Method 5: Pattern Guesser with Confidence"""
#     # patterns = generate_email_patterns(request.first_name, request.last_name, request.domain)
#     
#     # Enrich with MX checks
#     # results = []
#     # for p in patterns:
#     #     conf = calculate_confidence(p['email'], "Pattern Guess", False, p['base_confidence'])
#     #     results.append({
#     #         "email": p['email'],
#     #         "confidence": conf
#     #     })
#         
#     # Sort by score
#     # results.sort(key=lambda x: x['confidence']['score'], reverse=True)
#     return {"results": []} # Top 5 only

@app.get("/discovery/hr-search")
async def discovery_hr_search(role: str = "Recruiter", company: str = "", broad_mode: bool = False):
    """Method 1 & 3: Advanced HR Search (V2 Architecture)"""
    query = f"{role} {company}".strip()
    return StreamingResponse(orchestrator.discover_leads_stream(query, limit=30, broad_mode=broad_mode), media_type="application/x-ndjson")

@app.get("/discover")
def discover_candidates(role: str):
    """Deep web scan for candidates (Legacy Wrapper)"""
    # This was a blocking call, now we just grab from the stream
    results = []
    for line in orchestrator.discover_leads_stream(role, limit=15):
        try:
            msg = json.loads(line)
            if msg['type'] == 'result':
                results.append(msg['data'])
        except: pass
    return results

@app.get("/discover-stream")
def discover_candidates_stream(role: str):
    """Deep web scan with real-time updates"""
    return StreamingResponse(search_leads_generator(role), media_type="application/x-ndjson")

def search_leads_generator(role: str):
    """Wrapper to inject AI correction before streaming"""
    # 1. AI Spelling Correction
    corrected_role = role
    try:
        if GROQ_API_KEY:
            yield json.dumps({"type": "status", "data": "AI checking spelling..."}) + "\n"
            completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a spell checker. Correct the job title or search term. Return ONLY the corrected term. No quotes, no explanation. If correct, return original."
                    },
                    {
                        "role": "user",
                        "content": role
                    }
                ],
                model="llama-3.1-8b-instant",
            )
            suggestion = completion.choices[0].message.content.strip()
            # Basic validation to ensure it didn't hallucinate a sentence
            if len(suggestion) < 50 and suggestion.lower() != role.lower():
                yield json.dumps({"type": "status", "data": f"Auto-corrected: '{role}' -> '{suggestion}'"}) + "\n"
                corrected_role = suggestion
    except Exception as e:
        yield json.dumps({"type": "error", "data": f"AI Error: {str(e)}"}) + "\n"

    # 2. Call the orchestrator
    yield from orchestrator.discover_leads_stream(corrected_role)


# ---------- CANDIDATES ----------

@app.get("/candidates", response_model=List[Candidate])
def get_all_candidates():
    """Get all candidates"""
    if supabase:
        result = supabase.table("candidates").select("*").order("created_at", desc=True).execute()
        return result.data
    return []

@app.get("/candidates/{candidate_id}", response_model=Candidate)
def get_candidate(candidate_id: int):
    """Get single candidate by ID"""
    if supabase:
        result = supabase.table("candidates").select("*").eq("id", candidate_id).single().execute()
        if result.data:
            return result.data
    raise HTTPException(status_code=404, detail="Candidate not found")

@app.post("/candidates", response_model=Candidate)
def create_candidate(candidate: CandidateCreate):
    """Create a new candidate with Auto-Scoring"""
    if supabase:
        # 1. Calculate Match Score
        score = 0
        try:
             brain_res = supabase.table("brain_context").select("*").eq("id", 1).execute()
             if brain_res.data:
                 brain = brain_res.data[0]
                 skills = brain.get("extracted_skills", []) or []
                 if skills:
                     # Simple Keyword Matching
                     text = (candidate.title or "") + " " + (candidate.summary or "")
                     text = text.lower()
                     matches = sum(1 for s in skills if s.lower() in text)
                     if len(skills) > 0:
                         score = int((matches / len(skills)) * 100)
                     
                     # Bonus for title match
                     if (candidate.title or "").lower() in text: 
                         score += 10
                     
                     score = min(max(score, 10), 95) # Clamp 10-95
        except Exception as e:
            print(f"Scoring failed: {e}")
        
        # Update candidate with score
        candidate_data = candidate.model_dump()
        candidate_data["match_score"] = score

        result = supabase.table("candidates").insert(candidate_data).execute()
        if result.data:
            # Log activity
            supabase.table("activity_log").insert({
                "candidate_id": result.data[0]["id"],
                "action_type": "lead_found",
                "title": f"Added {candidate.name}",
                "description": f"Match Score: {score}% • {candidate.company or 'Unknown Company'}"
            }).execute()
            return result.data[0]
    raise HTTPException(status_code=500, detail="Failed to create candidate")

@app.put("/candidates/{candidate_id}", response_model=Candidate)
def update_candidate(candidate_id: int, candidate: CandidateCreate):
    """Update a candidate"""
    if supabase:
        result = supabase.table("candidates").update(candidate.model_dump()).eq("id", candidate_id).execute()
        if result.data:
            return result.data[0]
    raise HTTPException(status_code=404, detail="Candidate not found")

@app.delete("/candidates/{candidate_id}")
def delete_candidate(candidate_id: int):
    """Delete a candidate"""
    if supabase:
        supabase.table("candidates").delete().eq("id", candidate_id).execute()
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Candidate not found")

@app.patch("/candidates/{candidate_id}/status")
def update_candidate_status(candidate_id: int, status: str):
    """Update candidate status (new, contacted, replied, snoozed)"""
    if supabase:
        result = supabase.table("candidates").update({"status": status}).eq("id", candidate_id).execute()
        if result.data:
            return result.data[0]
    raise HTTPException(status_code=404, detail="Candidate not found")

@app.delete("/candidates/prune")
def prune_candidates(days: int = 7):
    """Delete candidates older than X days (Default: Keep latest for this week)"""
    if supabase:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        # Delete candidates created before the cutoff
        result = supabase.table("candidates").delete().lt("created_at", cutoff).execute()
        
        # Also cleanup drafts associated with deleted candidates (optional, but good for hygiene)
        # result.data contains deleted rows if return is requested, but count is sufficient
        return {"status": "success", "message": f"Pruned candidates older than {days} days"}
    return {"status": "error", "message": "Database not connected"}

# ---------- DRAFTS ----------

@app.get("/drafts", response_model=List[Draft])
def get_all_drafts():
    """Get all drafts with candidate info"""
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

@app.post("/drafts", response_model=Draft)
def create_draft(draft: DraftCreate):
    """Create a new draft"""
    if supabase:
        result = supabase.table("drafts").insert(draft.model_dump()).execute()
        if result.data:
            # Log activity
            candidate = supabase.table("candidates").select("name").eq("id", draft.candidate_id).single().execute()
            supabase.table("activity_log").insert({
                "candidate_id": draft.candidate_id,
                "action_type": "draft_created",
                "title": f"Drafted email to {candidate.data['name'] if candidate.data else 'Unknown'}",
                "description": "AI generated based on profile"
            }).execute()
            return {**result.data[0], "candidate_name": None, "candidate_company": None}
    raise HTTPException(status_code=500, detail="Failed to create draft")

@app.post("/polish-draft")
async def polish_draft(request: dict):
    """Fix grammar and improve tone of draft"""
    text = request.get("text", "")
    if not text: return {"text": ""}
    
    if GROQ_API_KEY:
        try:
            completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional editor. Fix grammar, spelling, and improve flow. Keep the tone professional but conversational. Return ONLY the polished text. Do not add intro/outro."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                model="llama-3.1-8b-instant",
            )
            return {"text": completion.choices[0].message.content.strip()}
        except Exception as e:
            print(f"Polish error: {e}")
            return {"text": text} # Fallback to original
    
    return {"text": text}

@app.post("/generate-draft")
async def generate_draft(candidate_id: int, context: str = ""):
    """Generate AI draft for a candidate using Groq with full context"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    # 1. Get candidate info
    candidate_res = supabase.table("candidates").select("*").eq("id", candidate_id).single().execute()
    if not candidate_res.data:
        raise HTTPException(status_code=404, detail="Candidate not found")
    c = candidate_res.data
    
    # 2. Get User Settings (Who am I?)
    settings = {"full_name": "Antigravity User", "company": "My Company", "role": "Professional"}
    try:
        settings_res = supabase.table("user_settings").select("*").eq("id", 1).execute()
        if settings_res.data:
            settings = settings_res.data[0]
    except Exception as e:
        print(f"Failed to fetch settings: {e}")

    # 3. Get Brain Context (My Skills/Voice)
    brain = {"extracted_skills": [], "formality": "Professional", "anecdotes": ""}
    try:
        brain_res = supabase.table("brain_context").select("*").eq("id", 1).execute()
        if brain_res.data:
            brain = brain_res.data[0]
            # Handle extracted_skills just in case it's None (should be [])
            if not brain.get("extracted_skills"):
                brain["extracted_skills"] = []
    except Exception as e:
        print(f"Failed to fetch brain: {e}")
        
    # Try Groq first
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
        
        print("DEBUG: Generative Prompt:\n", prompt)
        
        ai_response = await generate_with_groq(prompt)
        
        if ai_response:
            lines = ai_response.strip().split('\n')
            # Extract subject
            subject = "Cold Outreach"
            body_start_index = 0
            
            for i, line in enumerate(lines):
                if "Subject:" in line or "**Subject:**" in line:
                    subject = line.replace("Subject:", "").replace("**Subject:**", "").strip()
                    body_start_index = i + 1
                    break
            
            body = "\n".join(lines[body_start_index:]).strip()
            
            # Save draft to database
            result = supabase.table("drafts").insert({
                "candidate_id": candidate_id,
                "subject": subject,
                "body": body
            }).execute()
            
            # Log activity
            supabase.table("activity_log").insert({
                "candidate_id": candidate_id,
                "action_type": "draft_created",
                "title": f"Drafted email to {c['name']}",
                "description": "AI used your Brain & Settings"
            }).execute()
            
            return {"subject": subject, "body": body, "draft_id": result.data[0]["id"] if result.data else None}
    
    # Fallback template if no Groq API
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

# ---------- SEND EMAIL ----------

@app.post("/send-email")
def send_email(request: SendEmailRequest):
    """Send an email and log it"""
    if supabase:
        # Log to sent_emails
        supabase.table("sent_emails").insert({
            "candidate_id": request.candidate_id,
            "to_email": request.to,
            "subject": request.subject,
            "body": request.body
        }).execute()
        
        # Update candidate status
        if request.candidate_id:
            supabase.table("candidates").update({"status": "contacted"}).eq("id", request.candidate_id).execute()
            
            # Update draft status
            supabase.table("drafts").update({"status": "sent", "sent_at": datetime.now().isoformat()}).eq("candidate_id", request.candidate_id).eq("status", "draft").execute()
            
            # Log activity
            candidate = supabase.table("candidates").select("name").eq("id", request.candidate_id).single().execute()
            supabase.table("activity_log").insert({
                "candidate_id": request.candidate_id,
                "action_type": "email_sent",
                "title": f"Sent email to {candidate.data['name'] if candidate.data else 'Unknown'}",
                "description": request.subject
            }).execute()
            
            # Update stats
            today = datetime.now().date().isoformat()
            existing_stats = supabase.table("dashboard_stats").select("*").eq("stat_date", today).execute()
            if existing_stats.data:
                current = existing_stats.data[0]
                supabase.table("dashboard_stats").update({
                    "emails_sent": current.get("emails_sent", 0) + 1
                }).eq("stat_date", today).execute()
            else:
                supabase.table("dashboard_stats").insert({
                    "stat_date": today,
                    "emails_sent": 1,
                    "weekly_goal_percent": 10,
                    "people_found": 0
                }).execute()
        
        return {"status": "success", "message": f"Email sent to {request.to}"}
    
    return {"status": "success", "message": f"Email sent to {request.to} (not persisted)"}

@app.get("/sent-emails")
def get_sent_emails():
    """Get all sent emails"""
    if supabase:
        result = supabase.table("sent_emails").select("*").order("sent_at", desc=True).execute()
        return {"emails": result.data}
    return {"emails": []}

# ---------- ACTIVITY & STATS ----------

@app.get("/activity", response_model=List[ActivityLog])
def get_activity():
    """Get recent activity"""
    if supabase:
        result = supabase.table("activity_log").select("*").order("created_at", desc=True).limit(10).execute()
        return result.data
    return []

@app.get("/stats", response_model=DashboardStats)
def get_stats():
    """Get dashboard stats"""
    if supabase:
        try:
            # Get candidate count
            candidates = supabase.table("candidates").select("id", count="exact").execute()
            people_found = candidates.count if candidates.count else 0
            
            # Get sent emails count
            emails = supabase.table("sent_emails").select("id", count="exact").execute()
            emails_sent = emails.count if emails.count else 0
            
            # Calculate weekly goal (assuming goal is 10 emails/week)
            weekly_goal = min(100, int((emails_sent / 10) * 100))
            
            return {
                "weekly_goal_percent": weekly_goal,
                "people_found": people_found,
                "emails_sent": emails_sent,
                "replies_received": 0
            }
        except Exception as e:
            print(f"Stats Error: {e}")
            # Fallback to zeros if DB fails transiently
            return {
                "weekly_goal_percent": 0,
                "people_found": 0,
                "emails_sent": 0,
                "replies_received": 0
            }
# ---------- USER SETTINGS ----------

class UserSettings(BaseModel):
    full_name: str = ""
    company: str = ""
    role: str = ""

@app.get("/settings")
def get_settings():
    """Get user settings"""
    if supabase:
        result = supabase.table("user_settings").select("*").eq("id", 1).execute()
        if result.data:
            return result.data[0]
    return {"full_name": "", "company": "", "role": ""}

@app.put("/settings")
def update_settings(settings: UserSettings):
    """Update user settings"""
    if supabase:
        supabase.table("user_settings").upsert({
            "id": 1,
            "full_name": settings.full_name,
            "company": settings.company,
            "role": settings.role,
            "updated_at": datetime.now().isoformat()
        }).execute()
        return {"status": "updated"}
    return {"status": "not persisted"}

# ---------- BRAIN CONTEXT ----------

import re
import io
from pypdf import PdfReader

# ... (existing code)

# ---------- BRAIN CONTEXT ----------

def extract_skills_from_text(text: str) -> List[str]:
    """Simple keyword matching for common tech skills"""
    common_skills = [
        "python", "javascript", "typescript", "react", "node", "sql", "aws", 
        "docker", "kubernetes", "fastapi", "django", "flask", "next.js", 
        "html", "css", "git", "linux", "sales", "marketing", "cold outreach",
        "copywriting", "seo", "content strategy", "lead generation",
        "java", "c++", "c#", "go", "rust", "terraform", "azure", "gcp", 
        "redis", "postgres", "mongodb", "graphql", "rest api", "communication", 
        "leadership", "agile", "scrum", "machine learning", "data analysis"
    ]
    found_skills = []
    text_lower = text.lower()
    for skill in common_skills:
        if skill in text_lower:
            found_skills.append(skill.title())
    return list(set(found_skills))

@app.post("/brain/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload resume/CV and extract text"""
    content = await file.read()
    filename = file.filename
    extracted_text = ""
    extracted_skills = []
    
    # Process PDF
    if filename.lower().endswith('.pdf'):
        try:
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                extracted_text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            extracted_text = "Error extraction text from PDF"
            
    # Simple processing for text files (or fallback)
    elif filename.lower().endswith('.txt'):
        extracted_text = content.decode('utf-8')
    
    print(f"DEBUG: Extracted text length: {len(extracted_text)}")
    
    identity = {}
    warning = None
    
    if not extracted_text or len(extracted_text) < 10:
        warning = "Could not extract text from this file. It might be an image-based PDF or encrypted."
        print(f"DEBUG: Extraction failed - text length: {len(extracted_text)}")
    
    elif len(extracted_text) > 10:
        if GROQ_API_KEY:
            try:
                print("DEBUG: Calling Groq AI for detailed extraction...")
                prompt = f"""Analyze this resume and extract the following details accurately:
                1. Full Name
                2. Current Company (most recent employer, or null if not found)
                3. ALL Technical & Professional Skills (List every single hard skill, tool, framework, language, libary, or methodology found. Do not limit the number. Be exhaustive and accurate.)
                
                Return ONLY valid JSON:
                {{
                    "full_name": "John Doe",
                    "company": "Tech Corp",
                    "skills": ["Python", "React", "AWS", "Project Management", "etc..."]
                }}
                
                Resume Text:
                {extracted_text[:30000]}"""
                
                ai_response = await generate_with_groq(prompt)
                
                if ai_response:
                    json_str = ai_response.strip()
                    if json_str.startswith("```json"):
                        json_str = json_str.replace("```json", "").replace("```", "")
                    
                    data = json.loads(json_str)
                    extracted_skills = data.get("skills", [])
                    identity = {
                        "full_name": data.get("full_name"),
                        "company": data.get("company")
                    }
                    print(f"DEBUG: Parsed Identity: {identity}")
            except Exception as e:
                print(f"DEBUG: AI extraction failed: {e}")
                extracted_skills = extract_skills_from_text(extracted_text)
        else:
             print("DEBUG: No Groq Key, using keywords")
             extracted_skills = extract_skills_from_text(extracted_text)
    
    print(f"DEBUG: Final Skills: {extracted_skills}")
    
    if supabase:
        # 1. Update Brain Context
        brain_update_success = False
        try:
            print("DEBUG: Updating brain_context with skills...")
            supabase.table("brain_context").upsert({
                "id": 1,
                "resume_url": filename,
                "resume_text": extracted_text[:100000], 
                "extracted_skills": extracted_skills,
                "updated_at": datetime.now().isoformat()
            }).execute()
            brain_update_success = True
            print("DEBUG: brain_context updated successfully")
        except Exception as e:
            print(f"Brain Update Failed (Attempt 1): {e}")

        # Fallback
        if not brain_update_success:
            try:
                print("DEBUG: Attempting fallback update (no skills)...")
                supabase.table("brain_context").upsert({
                    "id": 1,
                    "resume_url": filename,
                    "resume_text": extracted_text[:5000], 
                    "updated_at": datetime.now().isoformat()
                }).execute()
                print("DEBUG: Fallback update successful")
            except Exception as e2:
                print(f"DB Fallback Failed: {e2}")

        # 2. Update User Settings (if identity found)
        if identity.get("full_name") or identity.get("company"):
            try:
                current_settings = supabase.table("user_settings").select("*").eq("id", 1).execute()
                updates = {}
                
                current_name = None
                current_company = None
                
                if current_settings.data:
                    current_name = current_settings.data[0].get("full_name")
                    current_company = current_settings.data[0].get("company")
                
                if identity.get("full_name") and not current_name:
                    updates["full_name"] = identity["full_name"]
                if identity.get("company") and not current_company:
                    updates["company"] = identity["company"]
                
                if updates:
                    updates["updated_at"] = datetime.now().isoformat()
                    if not current_settings.data:
                         updates["id"] = 1
                         updates["role"] = "Professional"
                    
                    supabase.table("user_settings").upsert(updates).eq("id", 1).execute()
                    print(f"DEBUG: Auto-updated Settings: {updates}")
            except Exception as e:
                 print(f"Settings Update Failed: {e}")
    
    return {
        "filename": filename, 
        "size": len(content), 
        "status": "uploaded",
        "extracted_skills": extracted_skills,
        "warning": warning,
        "preview_text": extracted_text[:200] + "..." if extracted_text else "No text extracted. (Is this a scanned PDF?)"
    }

@app.get("/brain")
def get_brain_context():
    """Get brain context settings"""
    if supabase:
        result = supabase.table("brain_context").select("*").limit(1).execute()
        if result.data:
            return result.data[0]
    return {"formality": 75, "detail_level": 30, "use_emojis": False}

@app.put("/brain")
def update_brain_context(formality: int = 75, detail_level: int = 30, use_emojis: bool = False):
    """Update brain context settings"""
    if supabase:
        supabase.table("brain_context").upsert({
            "id": 1,
            "formality": formality,
            "detail_level": detail_level,
            "use_emojis": use_emojis,
            "updated_at": datetime.now().isoformat()
        }).execute()
        return {"status": "updated"}
    return {"status": "not persisted"}

@app.post("/verify-linkedin")
def verify_linkedin_url(url: str):
    """Strictly validate LinkedIn URL format"""
    # Regex for standard linkedin profile patterns
    # Matches: https://www.linkedin.com/in/username
    # Matches: linkedin.com/in/username
    pattern = r'^(https?:\/\/)?(www\.)?linkedin\.com\/in\/[\w-]+\/?$'
    
    if re.match(pattern, url):
        return {"valid": True, "message": "Valid LinkedIn Profile URL"}
    else:
        return {"valid": False, "message": "Invalid URL format. Must be linkedin.com/in/username"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
