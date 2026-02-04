"""
Email Pattern Guesser Service

Generates likely email addresses based on:
- First name
- Last name
- Company domain

Returns ranked patterns by likelihood.
"""

import re
from typing import List, Dict, Optional

# Common email patterns ranked by frequency in tech companies
PATTERNS = [
    {"pattern": "{first}@{domain}", "weight": 0.95},       # john@company.com
    {"pattern": "{first}.{last}@{domain}", "weight": 0.90}, # john.doe@company.com
    {"pattern": "{first}{last}@{domain}", "weight": 0.75},  # johndoe@company.com
    {"pattern": "{f}{last}@{domain}", "weight": 0.70},      # jdoe@company.com
    {"pattern": "{first}{l}@{domain}", "weight": 0.65},     # johnd@company.com
    {"pattern": "{first}_{last}@{domain}", "weight": 0.60}, # john_doe@company.com
    {"pattern": "{last}.{first}@{domain}", "weight": 0.50}, # doe.john@company.com
    {"pattern": "{last}@{domain}", "weight": 0.40},         # doe@company.com
    {"pattern": "{f}.{last}@{domain}", "weight": 0.35},     # j.doe@company.com
]

def extract_domain_from_url(url: str) -> Optional[str]:
    """
    Extract domain from LinkedIn URL or website.
    For LinkedIn, tries to get company domain from the profile URL.
    """
    if not url:
        return None
    
    # If it's already a domain, return it
    if re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', url):
        return url.lower()
    
    # Extract from URL
    match = re.search(r'https?://(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', url)
    if match:
        domain = match.group(1)
        # Filter out social media domains
        if any(x in domain for x in ['linkedin.com', 'github.com', 'twitter.com', 'facebook.com']):
            return None
        return domain.lower()
    
    return None

def clean_name(name: str) -> tuple:
    """
    Split a name into first and last name components.
    Handles: "John Doe", "John A. Doe", "Dr. John Doe", etc.
    """
    if not name:
        return ("", "")
    
    # Remove common titles
    name = re.sub(r'^(Dr\.?|Mr\.?|Mrs\.?|Ms\.?|Prof\.?)\s+', '', name, flags=re.IGNORECASE)
    
    # Remove suffixes
    name = re.sub(r',?\s+(Jr\.?|Sr\.?|III|II|PhD|MD)$', '', name, flags=re.IGNORECASE)
    
    # Split
    parts = name.strip().split()
    
    if len(parts) == 0:
        return ("", "")
    elif len(parts) == 1:
        return (parts[0].lower(), "")
    else:
        # First name is first part, last name is last part
        return (parts[0].lower(), parts[-1].lower())

def guess_emails(name: str, domain: str) -> List[Dict]:
    """
    Generate email guesses for a person at a company.
    
    Args:
        name: Full name of the person (e.g., "John Doe")
        domain: Company domain (e.g., "google.com")
    
    Returns:
        List of dicts with 'email' and 'confidence' keys, sorted by confidence.
    """
    if not name or not domain:
        return []
    
    first, last = clean_name(name)
    
    if not first:
        return []
    
    # Get first initial
    f = first[0] if first else ""
    l = last[0] if last else ""
    
    results = []
    
    for p in PATTERNS:
        # Skip patterns requiring last name if we don't have one
        if not last and "{last}" in p["pattern"]:
            continue
        if not last and "{l}" in p["pattern"]:
            continue
            
        email = p["pattern"].format(
            first=first,
            last=last,
            f=f,
            l=l,
            domain=domain
        )
        
        # Validate email format
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            results.append({
                "email": email,
                "confidence": p["weight"],
                "pattern": p["pattern"]
            })
    
    # Sort by confidence
    results.sort(key=lambda x: x["confidence"], reverse=True)
    
    return results

def guess_best_email(name: str, domain: str) -> Optional[str]:
    """
    Returns the single most likely email address.
    """
    guesses = guess_emails(name, domain)
    return guesses[0]["email"] if guesses else None


# --- Integration with Candidates ---

def guess_email_for_candidate(name: str, company: str, linkedin_url: str = None) -> List[Dict]:
    """
    Attempt to guess email for a candidate using multiple strategies.
    
    1. Try to extract domain from company name
    2. Try to extract from LinkedIn URL (if company has website in profile)
    """
    domain = None
    
    # Strategy 1: Company name might be a domain
    if company and company != "Unknown":
        # Clean company name to domain
        company_clean = company.lower().strip()
        company_clean = re.sub(r'\s+(inc\.?|llc\.?|ltd\.?|corp\.?|co\.?)$', '', company_clean, flags=re.IGNORECASE)
        company_clean = re.sub(r'[^a-z0-9]', '', company_clean)
        
        # Common domain patterns
        possible_domains = [
            f"{company_clean}.com",
            f"{company_clean}.io",
            f"{company_clean}.co",
        ]
        
        # For now, assume .com
        domain = f"{company_clean}.com"
    
    if domain:
        return guess_emails(name, domain)
    
    return []
