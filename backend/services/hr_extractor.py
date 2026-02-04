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
    Robust Parsing for LinkedIn Titles:
    - 'Name - Role - Company'
    - 'Name | Role | Company'
    - 'Name – Role at Company'
    - 'Role at Company' (for headline extraction)
    """
    # Normalize separators
    # Replace en-dash, em-dash, vertical bar with standard dash
    normalized = title.replace("–", "-").replace("—", "-").replace("|", "-").replace(" at ", " - at - ") 
    
    parts = [p.strip() for p in normalized.split("-") if p.strip()]
    
    name = "Unknown"
    role = "Unknown"
    company = "Unknown"

    if len(parts) >= 3:
        # Best case: Name - Role - Company
        # OR: Name - Role - at - Company
        if parts[2].lower() == "at": 
            # Name - Role - at - Company -> Company is at index 3
            if len(parts) > 3:
                company = parts[3]
            name = parts[0]
            role = parts[1]
        else:
            name = parts[0]
            role = parts[1]
            company = parts[2]
            
            # Heuristic: If "Company" looks like "Location", ignore it
            # e.g. "San Francisco Bay Area"
            if any(x in company.lower() for x in ["area", "united states", "kingdom", "canada", "city"]):
                company = "Unknown" # Likely location, not company

    elif len(parts) == 2:
        # Case: Name - Role (Company might be in Role string like "Engineer at X")
        name = parts[0]
        role_part = parts[1]
        
        # Check for " at " in the role part
        if " at " in role_part.lower(): 
            # "Senior Engineer at Google"
            subparts = role_part.lower().split(" at ")
            role = role_part[:role_part.lower().find(" at ")].strip()
            company = role_part[role_part.lower().find(" at ")+4:].strip()
            # Restore capitalization roughly? No, keep original casing from slice
            # Actually, split is lowercase, so use index
            idx = role_part.lower().find(" at ")
            role = role_part[:idx].strip()
            company = role_part[idx+4:].strip()
        else:
            role = role_part
            company = "Unknown"
            
    else:
        # Fallback
        name = title
    
    # Clean up LinkedIn suffixes
    if " | LinkedIn" in name: name = name.replace(" | LinkedIn", "")
    if " | LinkedIn" in company: company = company.replace(" | LinkedIn", "")
    
    return {
        "name": name,
        "role": role,
        "company": company
    }
