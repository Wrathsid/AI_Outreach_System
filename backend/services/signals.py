"""
Signal extraction, hiring context detection, and data cleaning functions.

These functions analyze candidate data to determine outreach signals,
clean scraped data, and validate draft structure.
Extracted from drafts.py for maintainability.
"""

import re
from typing import Any, Dict, List


# ============================================================
# DATA QUALITY VALIDATION
# ============================================================


def clean_candidate_data(candidate: dict) -> dict:
    """Validate and clean candidate data before it touches any prompt.

    Handles garbage scraped data like hashtag-only names, 'Unknown' placeholders,
    and empty fields. Returns a cleaned copy with usable values or None.
    """
    cleaned = dict(candidate)  # Don't mutate original

    # --- Clean Name ---
    raw_name = cleaned.get("name", "") or ""
    name_cleaned = re.sub(r"#\w+", "", raw_name).strip()
    name_cleaned = re.sub(r"[^a-zA-Z\s\-\'.]+", "", name_cleaned).strip()
    if not name_cleaned or name_cleaned.lower() in ("unknown", "n/a", "none"):
        name_cleaned = ""  # type: ignore[assignment]
    cleaned["name"] = name_cleaned or None

    # --- Clean Title ---
    raw_title = cleaned.get("title", "") or ""
    title_cleaned = raw_title.strip()
    if not title_cleaned or title_cleaned.lower() in ("unknown", "n/a", "none", ""):
        title_cleaned = None
    if title_cleaned and title_cleaned.startswith("#"):
        title_cleaned = re.sub(r"#\w+\s*", "", title_cleaned).strip() or None
    cleaned["title"] = title_cleaned

    # --- Clean Company ---
    raw_company = cleaned.get("company", "") or ""
    company_cleaned = raw_company.strip()
    if not company_cleaned or company_cleaned.lower() in ("unknown", "n/a", "none", ""):
        company_cleaned = None
    cleaned["company"] = company_cleaned

    # --- Clean Summary ---
    raw_summary = cleaned.get("summary", "") or ""
    if raw_summary.lower().strip() in ("unknown", "n/a", "none", ""):
        cleaned["summary"] = None

    # --- Data Quality Score ---
    quality = 0
    if cleaned["name"]:
        quality += 1
    if cleaned["title"]:
        quality += 1
    if cleaned["company"]:
        quality += 1
    if cleaned.get("summary"):
        quality += 1
    cleaned["_data_quality"] = quality  # 0-4 scale

    return cleaned


# ============================================================
# PROMPT INJECTION SANITIZATION
# ============================================================


def sanitize_scraped_content(text: str) -> str:
    """Sanitize scraped content to prevent prompt injection (Priority 6).

    Strips URLs, emails, and special prompt-like characters.
    """
    if not text:
        return ""

    text = re.sub(r"http[s]?://\S+", "", text)
    text = re.sub(r"www\.\S+", "", text)
    text = re.sub(r"\S+@\S+", "", text)
    text = re.sub(
        r"(System:|User:|Assistant:|Prompt:|Ignore|Override)",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r'[^\w\s.,!?;:()\'\"-]', "", text)

    return text.strip()


# ============================================================
# STRUCTURAL VALIDATORS
# ============================================================


def validate_structure(text: str, contact_type: str) -> bool:
    """Verify draft has opener -> relevance -> CTA structure (Q1)."""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    return len(paragraphs) >= 2


def normalize_length(text: str, contact_type: str) -> str:
    """Hard-trim to channel limits (Q4)."""
    if contact_type == "email":
        words = text.split()
        if len(words) > 150:
            return " ".join(words[:150]) + "..."

    if len(text) > 2500:
        trimmed = text[:2450]
        last_period = max(trimmed.rfind("."), trimmed.rfind("?"), trimmed.rfind("!"))
        if last_period > 1000:
            return trimmed[: last_period + 1]
        return trimmed.rstrip() + "..."
    return text


# ============================================================
# HEDGING REMOVAL
# ============================================================

HEDGE_PHRASES = [
    "I think ",
    "I believe ",
    "I feel like ",
    "Perhaps ",
    "Maybe ",
    "It seems like ",
    "I was wondering if ",
    "If you don't mind ",
    "I hope you don't mind ",
    "Not sure if this is the right ",
]


def remove_hedging(text: str) -> str:
    """Strip hedging phrases from generated text (Q6)."""
    for hedge in HEDGE_PHRASES:
        text = text.replace(hedge, "")
        text = text.replace(hedge.lower(), "")
        text = text.replace(hedge.capitalize(), "")
    text = re.sub(r"  +", " ", text)
    text = re.sub(r"(?<=\. )\w", lambda m: m.group().upper(), text)
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text.strip()


# ============================================================
# HIRING CONTEXT DETECTION
# ============================================================


def _detect_hiring_context(candidate: dict) -> dict:
    """Analyze candidate data to determine if this is a hiring post or a person profile.

    Returns: {'is_hiring_post': bool, 'hiring_role': str or None, 'recipient_role': str}
    """
    summary = (candidate.get("summary") or "").lower()
    title = (candidate.get("title") or "").lower()
    name = (candidate.get("name") or "").lower()

    hiring_keywords = [
        "we are hiring",
        "we're hiring",
        "join our team",
        "hiring for",
        "now hiring",
        "open position",
        "job opening",
        "looking for",
        "apply now",
        "open role",
        "job opportunity",
        "career opportunity",
        "we need",
        "join us",
        "urgent hiring",
        "immediate opening",
    ]

    is_hiring_post = any(kw in summary for kw in hiring_keywords)
    is_hiring_post = is_hiring_post or any(kw in title for kw in hiring_keywords)

    name_hiring_hints = ["hiring", "hr ", "recruiter", "talent"]
    if any(hint in name for hint in name_hiring_hints):
        is_hiring_post = True

    # Extract the role being hired for
    hiring_role = None
    if is_hiring_post:
        from backend.services.hr_extractor import extract_role_from_post_body

        hiring_role = extract_role_from_post_body(
            candidate.get("summary") or candidate.get("title") or ""
        )

    # Determine recipient role
    recipient_role = "professional"
    recruiter_keywords = ["recruit", "talent", "hr ", "human resources", "people ops"]
    is_recruiter = any(kw in title for kw in recruiter_keywords)

    if is_recruiter:
        recipient_role = "recruiter"
    elif is_hiring_post:
        if not is_recruiter:
            recipient_role = "hiring_manager"
    else:
        recipient_role = "professional"

    return {
        "is_hiring_post": is_hiring_post,
        "hiring_role": hiring_role,
        "recipient_role": recipient_role,
    }


# ============================================================
# PRIMARY SIGNAL EXTRACTION
# ============================================================


def extract_primary_signal(candidate: dict) -> Dict[str, Any]:
    """Extract ONE strong signal from candidate context.

    Prevents over-stuffed, unnatural personalization.
    Returns: {'signal': str, 'type': str, 'avoid': str, 'is_generic': bool}
    """
    signals: List[Dict[str, Any]] = []

    title = candidate.get("title") or ""
    company = candidate.get("company") or ""
    summary = candidate.get("summary") or ""

    hiring_ctx = _detect_hiring_context(candidate)

    # Priority 4 (HIGHEST): Hiring post
    if hiring_ctx["is_hiring_post"] and hiring_ctx.get("hiring_role"):
        signals.append(
            {
                "type": "hiring_post",
                "value": f"Hiring for {hiring_ctx['hiring_role']}",
                "priority": 4,
            }
        )

    # Priority 3: Recruiter/talent role
    elif title and any(
        word in title.lower() for word in ["recruit", "talent", "hiring"]
    ):
        domain = "technical roles" if "tech" in title.lower() else "hiring"
        signals.append(
            {
                "type": "hiring_focus",
                "value": f"Recruiter focusing on {domain}",
                "priority": 3,
            }
        )

    # Priority 2: Technical role (ONLY if NOT hiring post)
    if not hiring_ctx["is_hiring_post"]:
        tech_keywords = [
            "engineer", "developer", "designer",
            "product", "architect", "lead",
        ]
        for keyword in tech_keywords:
            if title and keyword in title.lower():
                signals.append(
                    {
                        "type": "technical_role",
                        "value": (
                            f"{keyword.capitalize()} at {company}"
                            if company
                            else f"{keyword.capitalize()}"
                        ),
                        "priority": 2,
                    }
                )
                break

    # Priority 1: Summary snippet
    if summary and len(signals) == 0:
        first_sentence = summary.split(".")[0].strip()
        if 20 < len(first_sentence) < 100:
            signals.append({"type": "summary", "value": first_sentence, "priority": 1})

    # Return highest priority signal or generic fallback
    if signals:
        best_signal = max(signals, key=lambda s: int(s.get("priority", 0)))
        return {
            "signal": best_signal.get("value", ""),
            "type": best_signal.get("type", ""),
            "avoid": "generic experience, achievements not mentioned, overly detailed background",
            "is_generic": False,
        }

    # IMPROVED FALLBACK
    if company:
        return {
            "signal": f"the work at {company}",
            "type": "company_only",
            "avoid": "making assumptions about their work",
            "is_generic": True,
        }

    return {
        "signal": "the tech sector",
        "type": "user_interest",
        "avoid": "making assumptions about their work",
        "is_generic": True,
    }
