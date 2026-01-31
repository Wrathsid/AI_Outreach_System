import re
from typing import Dict, Optional

# Keywords ranked by relevance (High to Low)
HR_KEYWORDS = {
    "high": [
        "talent acquisition", "recruiter", "people partner", "head of people", 
        "director of people", "hr manager", "hr director", "human resources", 
        "hiring manager", "vp of people", "chief people officer", "people operations"
    ],
    "medium": [
        "hiring", "talent", "people", "culture", "recruiting", "staffing", 
        "careers", "join us", "growth", "operations"
    ],
    "low": [
        "manager", "lead", "director", "founder", "ceo", "cto", "co-founder" 
        # C-levels are good "low confidence" fallback for small startups
    ]
}

def extract_hr_score(role: str) -> dict:
    """
    Analyzes a job title or role string and assigns a confidence score
    regarding whether it's an HR/Recruiting role.
    """
    if not role:
        return {"score": 0, "is_hr": False}
        
    role_lower = role.lower()
    
    # Check High Priority
    for kw in HR_KEYWORDS["high"]:
        if kw in role_lower:
            return {"score": 0.95, "is_hr": True, "match": kw}
            
    # Check Medium Priority
    for kw in HR_KEYWORDS["medium"]:
        if kw in role_lower:
            return {"score": 0.65, "is_hr": True, "match": kw}
            
    # Check Low Priority (Founders often do HR in small startups)
    for kw in HR_KEYWORDS["low"]:
        if kw in role_lower:
            return {"score": 0.3, "is_hr": False, "match": kw}
            
    return {"score": 0.1, "is_hr": False, "match": None}

def extract_context_info(text: str, email: str) -> Dict[str, Optional[str]]:
    """
    Scans text around the found email (±300 chars) to find Name/Role context.
    Returns: {"name": ..., "role": ...} (Best guess)
    """
    if not text or not email:
        return {"name": None, "role": None}

    # Find email position
    try:
        start_idx = text.find(email)
        if start_idx == -1: return {"name": None, "role": None}
        
        # Define window
        window_start = max(0, start_idx - 300)
        window_end = min(len(text), start_idx + len(email) + 300)
        context = text[window_start:window_end]
        
        lines = context.split('\n')
        
        # Heuristic: Look for lines near the email that look like names or roles
        # This is simple heuristic: "Name - Role" or "Role at Company"
        
        candidates = []
        for line in lines:
            if email in line: continue # Skip the email line itself if it's just email
            clean = line.strip()
            if len(clean) < 3 or len(clean) > 80: continue
            
            # fast check for keywords
            score_data = extract_hr_score(clean)
            if score_data["score"] > 0.3:
                return {"role": clean, "name": None} # Found a role line?
                
        return {"name": None, "role": None}
        
    except Exception:
        return {"name": None, "role": None}

def parse_linkedin_title(title: str):
    """
    Parses 'Name - Role - Company' format common in search titles
    """
    parts = title.split(" - ")
    if len(parts) >= 3:
        return {
            "name": parts[0].strip(),
            "role": parts[1].strip(),
            "company": parts[2].strip()
        }
    elif len(parts) == 2:
        return {
            "name": parts[0].strip(),
            "role": parts[1].strip(),
            "company": None
        }
    return {"name": title, "role": "Unknown", "company": None}
