import json
import time
import random
import re
from typing import List, Dict, Optional
from ddgs import DDGS
from .hr_extractor import extract_hr_score, parse_linkedin_title
from .verifier import verify_email_deep

def get_queries_for_role(role: str) -> List[str]:
    """
    Generate specialized dorks based on the role category.
    """
    role_lower = role.lower()
    
    # 1. Tech Roles (DevOps, Software Engineer, Data Scientist)
    tech_keywords = ['eng', 'dev', 'soft', 'data', 'cloud', 'security', 'full stack', 'qa', 'sre']
    is_tech = any(k in role_lower for k in tech_keywords)
    
    # 2. Creative Roles (Writer, Designer, Artist)
    creative_keywords = ['writer', 'content', 'copy', 'design', 'art', 'creative', 'ux', 'ui']
    is_creative = any(k in role_lower for k in creative_keywords)
    
    if is_tech:
        return [
            # GitHub & StackOverflow (High Tech Intent)
            f'site:github.com "{role}" "gmail.com"',
            f'site:github.com "{role}" "email" -site:github.com/orgs',
            f'site:stackoverflow.com/users "{role}" "gmail.com"',
            f'site:gitlab.com "{role}" "gmail.com"',
            f'site:dev.to "{role}" "gmail.com"',
            
            # Tech Hiring posts
            f'site:linkedin.com/posts "hiring" "{role}" "email me"',
            f'site:linkedin.com/feed "looking for" "{role}" "send resume"',
            
            # Tech Job Boards
            f'site:lever.co "{role}"',
            f'site:greenhouse.io "{role}"',
        ]
    elif is_creative:
        return [
            # Portfolio Sites
            f'site:medium.com "{role}" "gmail.com"',
            f'site:behance.net "{role}" "gmail.com"',
            f'site:dribbble.com "{role}" "email"',
            f'site:contently.com "{role}" "email"',
            f'site:journo.portfolio.com "{role}"',
            
            # Creative Communities
            f'site:twitter.com "hiring" "{role}" "dm me"',
            f'site:linkedin.com/in/ "Content Manager" "hiring" "{role}"',
        ]
    else:
        # General / default fallback
        return [
            f'site:linkedin.com/in/ "{role}" "email"',
            f'site:linkedin.com/posts "hiring" "{role}" "email me"',
            f'site:reddit.com "hiring" "{role}" "email"',
            f'site:x.com "hiring" "{role}" "email"',
            f'"{role}" "resume" "gmail.com"',
        ]

def search_leads_stream(role: str, limit: int = 20):
    """
    Generator that yields JSON lines: {"type": "status"|"result", "data": ...}
    STRICTLY uses DuckDuckGo to avoid CAPTCHA and IP blocks.
    """
    results = []
    seen_urls = set()
    
    yield json.dumps({"type": "status", "data": "Initializing safe scan engines..."}) + "\n"
    
    # Get Dynamic Queries
    role_specific_queries = get_queries_for_role(role)
    
    # Add some universal high-yield queries
    universal_queries = [
        f'site:linkedin.com/in/ "Talent Acquisition" "{role}" "email"',
        f'site:linkedin.com/posts "vacancy" "{role}" "send resume"',
    ]
    
    queries = role_specific_queries + universal_queries
    
    yield json.dumps({"type": "status", "data": f"Scanning {len(queries)} specialized sources..."}) + "\n"
    
    try:
        with DDGS() as ddgs:
            for q in queries:
                if len(results) >= limit: break
                
                yield json.dumps({"type": "status", "data": f"Query: {q[:40]}..."}) + "\n"
                
                # Careful rate limiting
                time.sleep(random.uniform(1.5, 2.5))
                
                try:
                    search_res = ddgs.text(q, max_results=20)
                except Exception as e:
                    print(f"DDG Error: {e}")
                    continue
                    
                if not search_res: continue
                    
                for r in search_res:
                    if len(results) >= limit: break
                    
                    title = r.get("title", "")
                    body = r.get("body", "")
                    url = r.get("href", "")
                    
                    if not url or url in seen_urls: continue
                    seen_urls.add(url)

                    res = process_result(title, body, url, role)
                    if res:
                        # Yield result immediately
                        yield json.dumps({"type": "result", "data": res}) + "\n"
                        results.append(res)
                        time.sleep(0.1)
                        
    except Exception as e:
        yield json.dumps({"type": "error", "data": f"Scan Error: {str(e)}"}) + "\n"

    if len(results) == 0:
        yield json.dumps({"type": "status", "data": "No public leads found. Try simpler keywords."}) + "\n"

    yield json.dumps({"type": "done", "data": f"Scan complete. Found {len(results)} leads."}) + "\n"

def search_leads(role: str, limit: int = 15):
    """Legacy wrapper"""
    results = []
    for line in search_leads_stream(role, limit):
        try:
            msg = json.loads(line)
            if msg['type'] == 'result':
                results.append(msg['data'])
        except: pass
    return results

def process_result(title, body, url, search_role):
    """Helper to process and add result"""
    
    # 1. Parsing Identity
    name = "Candidate"
    extracted_role = search_role
    company = "Unknown"
    
    # Simple extraction logic
    if "linkedin.com/in" in url:
        parsed = parse_linkedin_title(title)
        name = parsed["name"]
        extracted_role = parsed["role"]
        company = parsed["company"] or "Unknown"
    elif "github.com" in url:
        # Title usually: "Name (Username) - Role..."
        parts = title.split("-")[0].strip()
        name = parts.split("(")[0].strip() or "GitHub User"
        company = "GitHub"
    elif "stackoverflow.com" in url:
        name = title.split("-")[0].strip().replace("User ", "")
        company = "StackOverflow"
    elif "medium.com" in url:
        name = title.split("|")[0].strip()
        company = "Medium"
    
    # 2. Extract Email
    email = extract_email(body) or extract_email(title)
    
    # 3. Analyze Role (Is this an HR person?)
    hr_analysis = extract_hr_score(extracted_role)
    
    # 4. TRIPLE VERIFICATION (Strict Mode)
    if email:
        is_valid_email = verify_email_deep(email)
        if not is_valid_email:
            return None # 0 False Positives Goal: Reject if any verification stage fails
    
    # 5. Acceptance Criteria
    # We accept if we found a VALID email OR it's a high-value HR profile
    if not email and not hr_analysis["is_hr"]:
        return None
        
    return {
        "name": name,
        "title": extracted_role, 
        "company": company,
        "email": email,
        "linkedin_url": url,
        "source": "web_scan",
        "summary": body[:200],
        "is_hr": hr_analysis["is_hr"],
        "hr_score": hr_analysis["score"]
    }

def extract_email(text: str) -> Optional[str]:
    """Extract email using strict regex and filter junk"""
    if not text: return None
    
    # Normalize obfuscation
    clean = text.lower().replace("[at]", "@").replace("(at)", "@").replace(" at ", "@")
    clean = clean.replace("[dot]", ".").replace("(dot)", ".").replace(" dot ", ".")
    
    # Regex: Alphanumeric + dots/dashes @ Alphanumeric + dots . 2+ chars
    # Avoiding capturing trailing dots or junk
    match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', clean)
    if not match: return None
    
    email = match.group(0)
    
    # Filter 1: Common Non-Email file extensions usually mistaken for emails in crawl data
    image_exts = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp', '.webp', '.css', '.js', '.io'] # .io is a domain but often misparsed in code
    if any(email.endswith(ext) for ext in image_exts if ext != '.io'): # Keep .io domains
        return None

    # Filter 2: Example/Invalid domains
    ignore_domains = ['example.com', 'email.com', 'domain.com', 'yoursite.com']
    if any(d in email for d in ignore_domains): return None
    
    return email


