import re
from typing import Dict, Optional

# Keywords ranked by relevance (High to Low)
HR_KEYWORDS = {
    "high": [
        "talent acquisition",
        "recruiter",
        "people partner",
        "head of people",
        "director of people",
        "hr manager",
        "hr director",
        "human resources",
        "hiring manager",
        "vp of people",
        "chief people officer",
        "people operations",
        "technical recruiter",
        "it recruiter",
        "tech recruiter",
        "sourcing specialist",
        "talent partner",
        "recruitment lead",
        "head of talent",
        "recruiting manager",
        "we are hiring",
        "we're hiring",
        "join our team",
        "hiring for",
    ],
    "medium": [
        "hiring",
        "talent",
        "people",
        "culture",
        "recruiting",
        "staffing",
        "careers",
        "join us",
        "growth",
        "operations",
        "open positions",
        "job opening",
        "now hiring",
        "seeking",
    ],
    "low": [
        "manager",
        "lead",
        "director",
        "founder",
        "ceo",
        "cto",
        "co-founder",
        # C-levels are good "low confidence" fallback for small startups
    ],
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


def classify_entity(name: str) -> str:
    """
    Classifies if a name string usually represents a Company or a Person.
    Returns: "COMPANY" or "PERSON"
    """
    if not name:
        return "PERSON"

    # 1. Check for common company suffixes
    company_suffixes = [
        " inc",
        " llc",
        " ltd",
        " corp",
        " group",
        " team",
        " careers",
        " systems",
        " technologies",
        " solutions",
        " labs",
        " agency",
        " studios",
        " ventures",
        " capital",
        " partners",
        " holdings",
        " enterprises",
        " industries",
        " networks",
        " software",
        " consulting",
        " services",
        " media",
        " entertainment",
        " recruiting",
        " staffing",
        " talent",
        " resources",
        " management",
        " bank",
        " global",
        " international",
    ]

    name_lower = name.lower()

    for suffix in company_suffixes:
        if name_lower.endswith(suffix) or (f" {suffix.strip()} " in f" {name_lower} "):
            return "COMPANY"

    # 2. Check for All Caps single word (e.g. "EXPANSIA") - strong signal for Brand/Company
    # People usually use Title Case.
    if name.isupper() and len(name.split()) == 1 and len(name) > 2:
        return "COMPANY"

    return "PERSON"


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
        if start_idx == -1:
            return {"name": None, "role": None}

        # Define window
        window_start = max(0, start_idx - 300)
        window_end = min(len(text), start_idx + len(email) + 300)
        context = text[window_start:window_end]

        lines = context.split("\n")

        for line in lines:
            if email in line:
                continue  # Skip the email line itself if it's just email
            clean = line.strip()
            if len(clean) < 3 or len(clean) > 80:
                continue

            # fast check for keywords
            score_data = extract_hr_score(clean)
            if score_data["score"] > 0.3:
                return {"role": clean, "name": None}  # Found a role line?

        return {"name": None, "role": None}

    except Exception:
        return {"name": None, "role": None}


def parse_linkedin_title(title: str):
    """
    Robust Parsing for LinkedIn Titles:
    - 'Name - Role - Company'
    - 'Name | Role | Company'
    - 'Name on LinkedIn: HIRING: Role at Company'
    """
    # 0. Cleanup prefixes/suffixes
    clean_title = title.strip()

    # Remove " | LinkedIn" or " - LinkedIn" suffix
    clean_title = re.sub(r"[\s\|\-]+LinkedIn$", "", clean_title, flags=re.IGNORECASE)

    # Handle "Name on LinkedIn: ..." pattern
    if " on LinkedIn:" in clean_title:
        parts = clean_title.split(" on LinkedIn:", 1)
        name = parts[0].strip()
        rest = parts[1].strip()

        # Check for "HIRING:" pattern in the rest
        if "HIRING:" in rest.upper():
            # "HIRING: Web Developer at Dropbox"
            # Remove "HIRING:"
            role_part = re.sub(r"HIRING:", "", rest, flags=re.IGNORECASE).strip()

            # Split by " at " or " @ "
            if " at " in role_part.lower():
                split_idx = role_part.lower().rfind(" at ")
                role = role_part[:split_idx].strip()
                company = role_part[split_idx + 4 :].strip()
            elif " @ " in role_part:
                split_idx = role_part.rfind(" @ ")
                role = role_part[:split_idx].strip()
                company = role_part[split_idx + 3 :].strip()
            else:
                role = role_part
                company = "Unknown"

            return {"name": name, "role": role, "company": company}

        else:
            # "Headline comes here" -> Treat as Role
            return {"name": name, "role": rest, "company": "Unknown"}

    # Normalize separators
    # Replace en-dash, em-dash, vertical bar with standard dash
    normalized = (
        clean_title.replace("–", "-")
        .replace("—", "-")
        .replace("|", "-")
        .replace(" at ", " - at - ")
    )

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
            if any(
                x in company.lower()
                for x in ["area", "united states", "kingdom", "canada", "city"]
            ):
                company = "Unknown"  # Likely location, not company

    elif len(parts) == 2:
        # Case: Name - Role (Company might be in Role string like "Engineer at X")
        name = parts[0]
        role_part = parts[1]

        # Check for " at " in the role part
        if " at " in role_part.lower():
            # "Senior Engineer at Google"
            # Split on LAST " at " to be safe? Or first? usually last is company
            idx = role_part.lower().rfind(" at ")
            role = role_part[:idx].strip()
            company = role_part[idx + 4 :].strip()
        else:
            role = role_part
            company = "Unknown"

    else:
        # Fallback
        name = clean_title

    return {"name": name, "role": role, "company": company}


def parse_linkedin_post_url(url: str) -> Dict[str, Optional[str]]:
    """
    Extract the poster's name from a LinkedIn /posts/ URL.

    URL format: linkedin.com/posts/firstname-lastname_hashtags-activity-ID
    The poster's slug is between '/posts/' and the first '_'.

    Examples:
        /posts/rossana-mercado_webdeveloper-ecommerce... → Rossana Mercado
        /posts/john-smith-12345_hiring-... → John Smith
    """
    result: Dict[str, Optional[str]] = {"name": None, "slug": None}

    if "/posts/" not in url:
        return result

    try:
        # Extract the slug after /posts/
        post_part = url.split("/posts/")[1]

        # The poster's name slug is before the first underscore
        if "_" in post_part:
            name_slug = post_part.split("_")[0]
        else:
            name_slug = (
                post_part.split("-activity-")[0]
                if "-activity-" in post_part
                else post_part
            )

        result["slug"] = name_slug

        # Convert slug to name: "rossana-mercado" → "Rossana Mercado"
        # Remove trailing numbers (LinkedIn ID suffixes like "john-smith-12345")
        parts = name_slug.split("-")

        # Filter out parts that are just numbers or hex-like LinkedIn IDs
        name_parts = []
        for i, part in enumerate(parts):
            if part.isdigit():
                continue  # Skip numeric ID suffixes
            # Skip trailing hex-like IDs (e.g., "5a9779326") — typically last part
            if (
                i > 0
                and len(part) >= 6
                and all(c in "0123456789abcdef" for c in part.lower())
            ):
                continue  # Skip hex ID suffixes
            if len(part) <= 1:
                continue  # Skip single characters
            name_parts.append(part.capitalize())

        if len(name_parts) >= 2:
            # Looks like a real name (at least first + last)
            result["name"] = " ".join(name_parts)
        elif len(name_parts) == 1 and len(name_parts[0]) > 2:
            result["name"] = name_parts[0]

    except Exception:
        pass

    return result


def extract_role_from_post_body(body: str) -> Optional[str]:
    """
    Extract the job role being hired for from a LinkedIn post body/snippet.

    Looks for patterns like:
        "hiring a Senior Developer"
        "looking for a DevOps Engineer"
        "we need a Cloud Architect"
    """
    if not body:
        return None

    patterns = [
        r"(?:hiring|looking for|seeking|need)\s+(?:a|an)?\s*([A-Z][A-Za-z\s/\-]+?)(?:\.|,|!|\n|to join)",
        r"(?:PART-TIME|FULL-TIME|Part-Time|Full-Time)\s+([A-Z][A-Za-z\s/\-]+?)(?:\.|,|!|\n|to join)",
        r"open\s+(?:role|position)\s*:?\s*([A-Z][A-Za-z\s/\-]+?)(?:\.|,|!|\n)",
    ]

    for pattern in patterns:
        match = re.search(pattern, body)
        if match:
            role = match.group(1).strip()
            # Sanity check: role should be reasonable length
            if 3 < len(role) < 60:
                return role

    return None


def extract_poster_info_from_snippet(title: str, body: str) -> Dict[str, Optional[str]]:
    """
    Extract poster name, title, and company from Google search snippet.

    SerpAPI snippets for LinkedIn posts often look like:
        Title: "Rossana Mercado on LinkedIn: #webdeveloper #ecommerce..."
        Body: "Recruiter at @HireWithNear · Senior Technical Recruiter · Hi everyone! At Near, we're looking for..."
    """
    result: Dict[str, Optional[str]] = {"name": None, "title": None, "company": None}

    # 1. Try to extract name from "Name on LinkedIn:" pattern in title
    if " on LinkedIn" in title:
        name_part = title.split(" on LinkedIn")[0].strip()
        # Verify it's a real name (not hashtags)
        if name_part and not name_part.startswith("#") and len(name_part) < 50:
            result["name"] = name_part

    # 2. Extract title/company from body snippet
    if body:
        # Pattern: "Role at Company" or "Role at @Company"
        role_at_match = re.search(
            r"^([A-Za-z\s]+?)\s+at\s+@?([A-Za-z0-9\s&\.]+?)(?:\s*[·•|]|\s*$)", body
        )
        if role_at_match:
            result["title"] = role_at_match.group(1).strip()
            result["company"] = role_at_match.group(2).strip()

        # Pattern: "At Company, we're..." in body
        if not result["company"]:
            at_company_match = re.search(
                r"[Aa]t\s+([A-Z][A-Za-z0-9\s&\.]+?),\s+we", body
            )
            if at_company_match:
                result["company"] = at_company_match.group(1).strip()

    return result
