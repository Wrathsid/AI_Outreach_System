"""
Settings router - User settings, brain context, and profile management.
"""
import re
import io
import json
from fastapi import APIRouter, UploadFile, File
from typing import List
from datetime import datetime
from pypdf import PdfReader

from backend.config import get_supabase, generate_with_gemini, logger
from backend.models.schemas import UserSettings

router = APIRouter(tags=["Settings"])


# ==================== USER SETTINGS ====================

@router.get("")
def get_settings():
    """Get user settings."""
    supabase = get_supabase()
    if supabase:
        result = supabase.table("user_settings").select("*").eq("id", 1).execute()
        if result.data:
            return result.data[0]
    return {"full_name": "", "company": "", "role": ""}


@router.put("")
def update_settings(settings: UserSettings):
    """Update user settings."""
    supabase = get_supabase()
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


# ==================== BRAIN CONTEXT ====================

def extract_skills_from_text(text: str) -> List[str]:
    """Simple keyword matching for common tech skills."""
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


@router.get("/brain")
def get_brain_context():
    """Get brain context settings."""
    supabase = get_supabase()
    if supabase:
        result = supabase.table("brain_context").select("*").limit(1).execute()
        if result.data:
            return result.data[0]
    return {"formality": 75, "detail_level": 30, "use_emojis": False}


@router.put("/brain")
def update_brain_context(formality: int = 75, detail_level: int = 30, use_emojis: bool = False):
    """Update brain context settings."""
    supabase = get_supabase()
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


@router.put("/brain/skills")
async def update_skills(skills: List[str]):
    """Update user skills directly. AI adapts its context based on these."""
    supabase = get_supabase()
    if supabase:
        try:
            supabase.table("brain_context").upsert({
                "id": 1,
                "extracted_skills": skills,
                "updated_at": datetime.now().isoformat()
            }).execute()
            return {"status": "updated", "skills_count": len(skills)}
        except Exception as e:
            logger.error(f"Skills update failed: {e}")
            return {"status": "error", "message": str(e)}
    return {"status": "not persisted"}


@router.post("/brain/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload resume/CV and extract text."""
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
            logger.error(f"Error parsing PDF: {e}")
            extracted_text = "Error extraction text from PDF"
            
    elif filename.lower().endswith('.txt'):
        extracted_text = content.decode('utf-8')
    
    identity = {}
    warning = None
    
    if not extracted_text or len(extracted_text) < 10:
        warning = "Could not extract text from this file. It might be an image-based PDF or encrypted."
    
    elif len(extracted_text) > 10:
        try:
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
            
            ai_response = await generate_with_gemini(prompt)
            
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
        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            extracted_skills = extract_skills_from_text(extracted_text)
    
    supabase = get_supabase()
    if supabase:
        # Update Brain Context
        try:
            supabase.table("brain_context").upsert({
                "id": 1,
                "resume_url": filename,
                "resume_text": extracted_text[:100000],
                "extracted_skills": extracted_skills,
                "updated_at": datetime.now().isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Brain Update Failed: {e}")
            try:
                supabase.table("brain_context").upsert({
                    "id": 1,
                    "resume_url": filename,
                    "resume_text": extracted_text[:5000],
                    "updated_at": datetime.now().isoformat()
                }).execute()
            except Exception as e2:
                logger.error(f"DB Fallback Failed: {e2}")

        # Update User Settings (if identity found)
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
            except Exception as e:
                logger.error(f"Settings Update Failed: {e}")
    
    return {
        "filename": filename,
        "size": len(content),
        "status": "uploaded",
        "extracted_skills": extracted_skills,
        "warning": warning,
        "preview_text": extracted_text[:200] + "..." if extracted_text else "No text extracted. (Is this a scanned PDF?)"
    }


@router.post("/verify-linkedin")
def verify_linkedin_url(url: str):
    """Strictly validate LinkedIn URL format."""
    pattern = r'^(https?:\/\/)?(www\.)?linkedin\.com\/in\/[\w-]+\/?$'
    
    if re.match(pattern, url):
        return {"valid": True, "message": "Valid LinkedIn Profile URL"}
    else:
        return {"valid": False, "message": "Invalid URL format. Must be linkedin.com/in/username"}
