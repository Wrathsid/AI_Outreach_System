"""
Drafts router - Draft management and AI generation.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Optional
from pydantic import BaseModel
import re
import hashlib
import uuid
import json
from datetime import datetime, timedelta
import time
import asyncio
import logging

import os

from backend.config import get_supabase, generate_with_gemini, generate_with_qubrid, get_qubrid_client, logger
from backend.models.schemas import Draft, DraftCreate, DraftEditCreate, IntentType, GenerationReason
from backend.services.embeddings import embeddings_service
from backend.services.verifier import verify_skills_grounding

router = APIRouter(tags=["Drafts"])

class BatchDraftRequest(BaseModel):
    contact_type: str = "auto"
    candidate_ids: List[int]
    context: Optional[str] = None

# ============================================================
# R5: VALID CHANNELS
# ============================================================
VALID_CHANNELS = {"email", "linkedin"}


# ============================================================
# Q5: CHANNEL TONE LOCK
# ============================================================
CHANNEL_TONE = {
    "linkedin": "TONE: This is a JOB APPLICATION message. Write as someone seeking employment. Be professional, detailed, and direct about wanting to work there. Aim for ~300 words (~2000 characters). Never sound like a networking or connection request.",
    "email": "TONE: This is a direct, professional cold email for a job application or inquiry. Be concise, respectful of their time, and clear about your value proposition. Aim for ~150 words."
}

# ============================================================
# H2: PROMPT VERSIONING
# ============================================================
PROMPT_VERSION = "v1.3"


# ============================================================
# P2: BRAIN CONTEXT CACHE (5-min TTL)
# ============================================================
_brain_cache: dict = {}
_BRAIN_CACHE_TTL = 300  # 5 minutes

_biased_params_cache: dict = {}
_BIASED_PARAMS_TTL = 900  # 15 minutes


# ============================================================
# H1: DETERMINISTIC FINGERPRINT
# ============================================================
def generate_fingerprint(candidate_id: int, contact_type: str, skills: list, resume_text: str, tone_directive: str) -> str:
    """Generate a deterministic hash of all inputs affecting generation."""
    skills_str = "|".join(sorted([s.lower() for s in skills]))
    resume_hash = hashlib.sha256((resume_text or "").encode()).hexdigest()[:8]
    tone_hash = hashlib.sha256((tone_directive or "").encode()).hexdigest()[:8]
    
    raw = f"{candidate_id}|{contact_type}|{skills_str}|{resume_hash}|{PROMPT_VERSION}|{tone_hash}"
    return hashlib.sha256(raw.encode()).hexdigest()

def get_cached_brain_context(supabase) -> dict:
    """Fetch brain context with in-memory caching (P2)."""
    now = time.time()
    if "_brain" in _brain_cache and (now - _brain_cache.get("_ts", 0)) < _BRAIN_CACHE_TTL:
        return _brain_cache["_brain"]
    try:
        b_data = supabase.table("brain_context").select("*").eq("id", 1).execute().data
        brain = b_data[0] if b_data else {"extracted_skills": []}
    except Exception:
        brain = {"extracted_skills": []}
    _brain_cache["_brain"] = brain
    _brain_cache["_ts"] = now
    return brain


# ============================================================
# R3: DETERMINISTIC PROMPT ASSEMBLY
# ============================================================
PROMPT_SECTION_ORDER = [
    "system_identity",
    "user_bio",
    "candidate_context",
    "signal",
    "memory_constraint",
    "skills_grounding",
    "structural_rules",
    "negative_constraints",
    "task_instruction",
]

def assemble_prompt(sections: dict) -> str:
    """Assemble prompt in a fixed, deterministic order (R3)."""
    parts = []
    for key in PROMPT_SECTION_ORDER:
        if key in sections and sections[key]:
            parts.append(sections[key].strip())
    return "\n\n---\n\n".join(parts)


# ============================================================
# Q2: PERSONA ANCHOR
# ============================================================
PERSONA_ANCHOR = """
PERSONA: You are Siddharth Chavan, a DevOps-focused engineer actively looking for job opportunities.
You speak as yourself — first person, direct, technical but approachable.
You are a JOB APPLICANT. Every message you write is a job application or inquiry about open positions.
You never write generic networking messages or "looking to connect" messages.
You never introduce yourself in third person.
You never say "the candidate" when referring to yourself.
"""


# ============================================================
# Q1: STRUCTURAL SKELETON VALIDATOR
# ============================================================
def validate_structure(text: str, contact_type: str) -> bool:
    """Verify draft has opener -> relevance -> CTA structure (Q1)."""
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    # LinkedIn: at least greeting + body + soft close
    return len(paragraphs) >= 2


# ============================================================
# Q4: LENGTH NORMALIZATION
# ============================================================
def normalize_length(text: str, contact_type: str) -> str:
    """Hard-trim to channel limits (Q4)."""
    if contact_type == "email":
        words = text.split()
        if len(words) > 150:
            return " ".join(words[:150]) + "..."
            
    if len(text) > 2500:
        trimmed = text[:2450]
        last_period = max(trimmed.rfind('.'), trimmed.rfind('?'), trimmed.rfind('!'))
        if last_period > 1000:
            return trimmed[:last_period + 1]
        return trimmed.rstrip() + "..."
    return text


# ============================================================
# Q6: HEDGING REMOVAL
# ============================================================
HEDGE_PHRASES = [
    "I think ", "I believe ", "I feel like ",
    "Perhaps ", "Maybe ", "It seems like ",
    "I was wondering if ", "If you don't mind ",
    "I hope you don't mind ", "Not sure if this is the right ",
]

def remove_hedging(text: str) -> str:
    """Strip hedging phrases from generated text (Q6)."""
    for hedge in HEDGE_PHRASES:
        text = text.replace(hedge, "")
        text = text.replace(hedge.lower(), "")
        # Also handle sentence-start variations
        text = text.replace(hedge.capitalize(), "")
    # Clean up double spaces
    text = re.sub(r'  +', ' ', text)
    # Capitalize first letter of sentences after removal
    text = re.sub(r'(?<=\. )\w', lambda m: m.group().upper(), text)
    # Fix leading lowercase after removal at start
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text.strip()


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
    raw_name = cleaned.get('name', '') or ''
    # Strip hashtags and clean up
    name_cleaned = re.sub(r'#\w+', '', raw_name).strip()
    # Remove excess whitespace and special chars
    name_cleaned = re.sub(r'[^a-zA-Z\s\-\'.]+', '', name_cleaned).strip()
    # Remove 'Unknown' placeholder (but keep 'Hiring Team' — it's a valid label for job postings)
    if not name_cleaned or name_cleaned.lower() in ('unknown', 'n/a', 'none'):
        name_cleaned = None
    cleaned['name'] = name_cleaned
    
    # --- Clean Title ---
    raw_title = cleaned.get('title', '') or ''
    title_cleaned = raw_title.strip()
    if not title_cleaned or title_cleaned.lower() in ('unknown', 'n/a', 'none', ''):
        title_cleaned = None
    # Strip if it's just hashtags
    if title_cleaned and title_cleaned.startswith('#'):
        title_cleaned = re.sub(r'#\w+\s*', '', title_cleaned).strip() or None
    cleaned['title'] = title_cleaned
    
    # --- Clean Company ---
    raw_company = cleaned.get('company', '') or ''
    company_cleaned = raw_company.strip()
    if not company_cleaned or company_cleaned.lower() in ('unknown', 'n/a', 'none', ''):
        company_cleaned = None
    cleaned['company'] = company_cleaned
    
    # --- Clean Summary ---
    raw_summary = cleaned.get('summary', '') or ''
    if raw_summary.lower().strip() in ('unknown', 'n/a', 'none', ''):
        cleaned['summary'] = None
    
    # --- Data Quality Score ---
    quality = 0
    if cleaned['name']: quality += 1
    if cleaned['title']: quality += 1
    if cleaned['company']: quality += 1
    if cleaned.get('summary'): quality += 1
    cleaned['_data_quality'] = quality  # 0-4 scale
    
    return cleaned


# ============================================================
# REPLY-RATE OPTIMIZATION FUNCTIONS
# ============================================================

def sanitize_scraped_content(text: str) -> str:
    """Sanitize scraped content to prevent prompt injection (Priority 6).
    
    Strips URLs, emails, and special prompt-like characters.
    """
    if not text:
        return ""
    
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)
    
    # Remove emails
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove prompt-like patterns
    text = re.sub(r'(System:|User:|Assistant:|Prompt:|Ignore|Override)', '', text, flags=re.IGNORECASE)
    
    # Remove excessive newlines and special chars
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[^\w\s.,!?;:()\'"-]', '', text)
    
    return text.strip()


def get_recent_opener_hashes(supabase, limit: int = 50) -> List[str]:
    """Fetch hashes of recently sent openers to avoid repetition (Optimization 13)."""
    try:
        res = supabase.table("sent_openers").select("opener_hash").order("created_at", desc=True).limit(limit).execute()
        return [d["opener_hash"] for d in res.data]
    except Exception as e:
        logger.error(f"Memory fetch (hashes) failed: {e}")
        return []


def get_semantically_similar_openers(supabase, embedding: List[float], threshold: float = 0.85) -> List[Dict]:
    """Search for semantically similar openers in Supabase (Optimization Phase 2)."""
    try:
        res = supabase.rpc("match_sent_openers", {
            "query_embedding": embedding,
            "match_threshold": threshold,
            "match_count": 5
        }).execute()
        return res.data
    except Exception as e:
        logger.error(f"Semantic memory fetch failed: {e}")
        return []


def get_recent_openers(supabase, limit: int = 5) -> List[str]:
    """Fetch recent openers for the prompt to avoid repetition (Optimization 13)."""
    try:
        # Legacy: Still check drafts to avoid repeating what we just generated
        res = supabase.table("drafts").select("body").order("created_at", desc=True).limit(limit).execute()
        openers = []
        for d in res.data:
            body = d.get("body", "")
            if body:
                first_line = body.split('\n')[0].strip()
                if first_line:
                    if "," in first_line and len(first_line.split(',')[0]) < 20: 
                         parts = first_line.split(',', 1)
                         if len(parts) > 1:
                             openers.append(parts[1].strip()[:50])
                    else:
                        openers.append(first_line[:50])
        return list(set(openers))
    except Exception as e:
        logger.error(f"Memory fetch failed: {e}")
        return []


def get_biased_parameters(supabase) -> Dict:
    """Analyze which parameters led to replies (Optimization Phase 2) with caching."""
    now = time.time()
    if "_params" in _biased_params_cache and (now - _biased_params_cache.get("_ts", 0)) < _BIASED_PARAMS_TTL:
        return _biased_params_cache["_params"]
        
    try:
        # Fetch up to 100 recent replied drafts
        res = supabase.table("drafts").select("generation_params").eq("reply_status", "replied").limit(100).execute()
        
        if not res.data:
            _biased_params_cache["_params"] = {}
            _biased_params_cache["_ts"] = now
            return {}
        
        params_list = [d["generation_params"] for d in res.data if d.get("generation_params")]
        if not params_list:
            _biased_params_cache["_params"] = {}
            _biased_params_cache["_ts"] = now
            return {}
        
        # Calculate heuristics
        # 1. Average temperature
        temps = [p.get("temperature") for p in params_list if p.get("temperature")]
        avg_temp = sum(temps) / len(temps) if temps else None
        
        # 2. Most successful intent
        intents = [p.get("intent") for p in params_list if p.get("intent")]
        p_intent = max(set(intents), key=intents.count) if intents else None
        
        # 3. Successful Signal Types
        signals = [p.get("signal_type") for p in params_list if p.get("signal_type")]
        p_signal = max(set(signals), key=signals.count) if signals else None

        result = {
            "suggested_temperature": round(avg_temp, 2) if avg_temp else None,
            "best_intent": p_intent,
            "best_signal_type": p_signal,
            "sample_size": len(params_list)
        }
        _biased_params_cache["_params"] = result
        _biased_params_cache["_ts"] = now
        return result
    except Exception as e:
        logger.error(f"Parameter biasing retrieval failed: {e}")
        return {}


def score_draft(text: str, contact_type: str, candidate_context: dict = None) -> float:
    """Deterministic scoring for reply probability.
    
    Higher scores = better reply probability.
    Sweet spots: LinkedIn 140-200 chars, exactly 1 question, curiosity over CTA.
    """
    score = 100.0
    
    # 0. Sanity Check
    if not text or len(text.strip()) < 10:
        return 0.0

    # Length sweet spot
    length = len(text)
    if 1500 <= length <= 2500:
        score += 20
    elif length < 1000:
        score -= 10
    elif length > 2500:
        score -= 15
    
    # Question count (exactly 1 is ideal)
    question_count = text.count("?")
    if question_count == 1:
        score += 15
    elif question_count == 0:
        score -= 5
    else:
        score -= 10 * (question_count - 1)
    
    # Ends with curiosity (not hard CTA)
    last_50 = text.lower()[-50:]
    cta_words = ["schedule", "call", "meeting", "chat sometime", "book a", "let's connect", "happy to chat"]
    if any(word in last_50 for word in cta_words):
        score -= 25 # Increased penalty for generic CTAs

    # Gemini "Over-Helpful" Artifacts Check (CRITICAL)
    # Banned phrases that scream "AI" or "Gemini"
    banned_phrases = [
        "as an ai",
        "i understand",
        "hope this message finds you",
        "wanted to reach out", 
        "writing to explore",
        "love the opportunity",
        "please let me know if",
        "additionally,",
        "moreover,",
        "it's important to note",
        "based on your request",
        "this message is intended"
    ]
    for phrase in banned_phrases:
        if phrase in text.lower():
            score -= 50 # Kill this draft
            
    # Structure Enforcement
    # Allow multiple question marks for long conversations
    if text.count("?") > 4:
        score -= 50
    
    # Flexible Endings (Opt 15 + Refinement)
    # Allow 0 question marks IF ending is soft curiosity
    if text.count("?") == 0:
        soft_endings = ["curious", "wondering", "thoughts", "perspective", "interest"]
        last_sentence = text.strip().split('.')[-1].lower()
        if any(w in last_sentence for w in soft_endings):
            score += 10 # Valid soft ending
        else:
            score -= 5 # Penalty for statement with no curiosity

    # Preview Sanity Check (Refinement)
    # catch "I'm reaching out" / apologies in first 100 chars
    first_100 = text[:100].lower()
    bad_starts = ["reaching out to", "apologize", "sorry for", "hope you are"]
    if any(b in first_100 for b in bad_starts):
        score -= 50

    # Pronoun Dominance Check (Refinement)
    # Soft penalty if "I" > 2 AND "You" == 0
    i_count = len(re.findall(r'\bI\b', text)) # Case sensitive for "I"
    you_count = len(re.findall(r'\byou\b', text, re.IGNORECASE))
    
    if i_count > 2 and you_count == 0:
        score -= 15 # Self-centered penalty
    elif i_count > 2:
        score -= 5 * (i_count - 2)
    
    # Check for their name/company mention (should appear once)
    if candidate_context:
        name_first = candidate_context.get('name', '').split()[0] if candidate_context.get('name') else ''
        company = candidate_context.get('company', '')
        
        if name_first and name_first.lower() in text.lower():
            score += 5
        if company and company.lower() in text.lower():
            mentions = text.lower().count(company.lower())
            if mentions == 1:
                score += 5
            elif mentions > 1:
                score -= 5  # Over-personalization
    
    # PATH A OPTIMIZATIONS (Advanced Reply-Rate Tuning)
    
    # Optimization 15: End-of-message scoring
    ending_score = score_ending(text, contact_type)
    score += ending_score
    
    # Optimization 14: Linguistic softness
    softness_score = calculate_softness_score(text)
    score += softness_score
    
    # Optimization 20: Psychological consistency (calm tone)
    calm_score = check_calm_consistency(text)
    score += calm_score
    
    # Optimization 16: Mobile readability
    readability_score = check_mobile_readability(text, contact_type)
    score += readability_score
    
    # Optimization 16 (Part 2): Time-to-Read (Glance Test)
    ttr = calculate_time_to_read(text)
    if ttr > 180:
        score -= 10  # Too long even for detailed messages
    
    # Phase 2: Paragraph Asymmetry Guard (Heuristic for Humanness)
    asymmetry_score = calculate_asymmetry_score(text)
    score += asymmetry_score
    
    return max(0, score)


def calculate_time_to_read(text: str) -> int:
    """Estimate reading time in seconds (approx 200 wpm / 3.3 wps)."""
    words = len(text.split())
    return round(words / 3.3)


def score_ending(text: str, contact_type: str) -> float:
    """Score the final sentence for reply probability (Optimization 15)."""
    lines = text.strip().split('\n')
    last_line = lines[-1].lower() if lines else ""
    
    score = 0
    
    # Good endings (curiosity-driven)
    good_endings = [
        "curious what you think",
        "open to a quick exchange",
        "would you be up for that",
        "any thoughts on this",
        "interested in your take",
        "curious to hear"
    ]
    
    # Bad endings (hard CTAs)
    bad_endings = [
        "let's connect",
        "let me know",
        "happy to chat",
        "reach out",
        "schedule",
        "book a",
        "set up a call",
        "grab coffee",
        "sincerely",
        "best regards",
        "best,",
        "cheers",
        "warmly"
    ]
    
    # Check for good endings
    for good in good_endings:
        if good in last_line:
            score += 20
            break
    
    # Check for bad endings
    for bad in bad_endings:
        if bad in last_line:
            score -= 25
            break
    
    # Ends with question mark (curiosity)
    if last_line.endswith('?'):
        score += 15
    # Ends with period (calm confidence)
    elif last_line.endswith('.'):
        score += 5
    
    return score


def calculate_softness_score(text: str) -> float:
    """Measure linguistic softness — higher is better (Optimization 14)."""
    score = 0
    text_lower = text.lower()
    
    # Soft modal verbs (good)
    soft_modals = ["might", "could", "wondering", "curious", "perhaps", "possibly", "would you"]
    for modal in soft_modals:
        score += text_lower.count(modal) * 5
    
    # Hard imperatives (bad)
    imperatives = ["you should", "you need", "you must", "let's", "we should"]
    for imp in imperatives:
        score -= text_lower.count(imp) * 10
    
    # Future assumptions (bad — presumes relationship)
    future_words = ["will be", "going to", "excited to", "looking forward"]
    for fw in future_words:
        score -= text_lower.count(fw) * 8
    
    return score


def check_calm_consistency(text: str) -> float:
    """Ensure psychological calmness in tone (Optimization 20)."""
    score = 0
    
    # No exclamation marks (breaks calm)
    exclamation_count = text.count('!')
    if exclamation_count == 0:
        score += 10
    else:
        score -= 15 * exclamation_count
    
    # No ALL CAPS words
    words = text.split()
    caps_words = [w for w in words if w.isupper() and len(w) > 2]
    score -= len(caps_words) * 10
    
    # No hype verbs
    hype_verbs = ["revolutionize", "disrupt", "transform", "amazing", "incredible", "awesome"]
    for hype in hype_verbs:
        if hype in text.lower():
            score -= 20
    
    # Sentence rhythm (aim for 10-20 words per sentence)
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    for sent in sentences:
        word_count = len(sent.split())
        if 10 <= word_count <= 20:
            score += 3
        elif word_count > 30:
            score -= 5  # Too dense
    
    return score


def check_mobile_readability(text: str, contact_type: str) -> float:
    """Ensure message passes mobile glance test (Optimization 16)."""
    score = 0
    
    # Simulate mobile width (approx 40 chars per line)
    lines = text.split('\n')
    
    for line in lines:
        # Lines that would wrap to 2+ lines on mobile
        if len(line) > 80:
            score -= 10
    
    # Email: Prefer 2-3 short paragraphs
    if contact_type == "email":
        paragraph_count = len([p for p in lines if p.strip()])
        if 2 <= paragraph_count <= 3:
            score += 15
        elif paragraph_count > 4:
            score -= 10
    
    # No dense clauses (word count per sentence)
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    for sent in sentences:
        words = len(sent.split())
        if words > 25:  # Dense clause
            score -= 5
    
    return score
def calculate_asymmetry_score(text: str) -> float:
    """Penalize drafts with perfectly symmetrical paragraph lengths (Phase 2).
    
    Humans write with variance. Robots write in blocks.
    Ideal: 1:2 or 2:1 length ratios between consecutive paragraphs.
    """
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) < 2:
        return 0
    
    score = 0
    lengths = [len(p) for p in paragraphs]
    
    for i in range(len(lengths) - 1):
        len1 = lengths[i]
        len2 = lengths[i+1]
        
        if len1 == 0 or len2 == 0:
            continue
            
        # Calculate ratio (larger / smaller)
        ratio = max(len1, len2) / min(len1, len2)
        
        if ratio < 1.15: # Too symmetrical (within 15%)
            score -= 20
        elif 1.5 <= ratio <= 3.0: # Good variance
            score += 10
            
    return score




def _detect_hiring_context(candidate: dict) -> dict:
    """Analyze candidate data to determine if this is a hiring post or a person profile.
    
    Returns: {'is_hiring_post': bool, 'hiring_role': str or None, 'recipient_role': str}
    """
    summary = (candidate.get('summary') or '').lower()
    title = (candidate.get('title') or '').lower()
    name = (candidate.get('name') or '').lower()
    
    hiring_keywords = [
        'we are hiring', "we're hiring", 'join our team', 'hiring for',
        'now hiring', 'open position', 'job opening', 'looking for',
        'apply now', 'open role', 'job opportunity', 'career opportunity',
        'we need', 'join us', 'urgent hiring', 'immediate opening'
    ]
    
    is_hiring_post = any(kw in summary for kw in hiring_keywords)
    is_hiring_post = is_hiring_post or any(kw in title for kw in hiring_keywords)
    
    # Also check if the name itself suggests hiring (e.g., "Hr Priya Hiring")
    name_hiring_hints = ['hiring', 'hr ', 'recruiter', 'talent']
    if any(hint in name for hint in name_hiring_hints):
        is_hiring_post = True
    
    # If it's a hiring post, the title is likely the ROLE BEING HIRED, not the person's role
    hiring_role = None
    if is_hiring_post and candidate.get('title'):
        hiring_role = candidate.get('title')  # e.g., "Frontend Developer" is the role they're hiring for
    
    # Determine what the RECIPIENT's actual role is
    if is_hiring_post:
        # The person is a recruiter/HR — they're posting about a role, not working in it
        if any(w in title for w in ['recruit', 'talent', 'hr ', 'hiring']):
            recipient_role = 'recruiter'  # Explicitly a recruiter
        else:
            recipient_role = 'hiring_manager'  # Posting about hiring but title doesn't say recruiter
    else:
        recipient_role = 'professional'  # A regular person in their stated role
    
    return {
        'is_hiring_post': is_hiring_post,
        'hiring_role': hiring_role,
        'recipient_role': recipient_role
    }


def extract_primary_signal(candidate: dict) -> Dict[str, str]:
    """Extract ONE strong signal from candidate context.
    
    Prevents over-stuffed, unnatural personalization.
    Returns: {'signal': str, 'type': str, 'avoid': str, 'is_generic': bool}
    """
    signals = []
    
    title = candidate.get('title') or ''  # None-safe
    company = candidate.get('company') or ''  # None-safe
    summary = candidate.get('summary') or ''  # None-safe
    
    # NEW: Detect hiring context
    hiring_ctx = _detect_hiring_context(candidate)
    
    # Priority 4 (HIGHEST): This is a hiring post — signal = they're hiring for X role
    if hiring_ctx['is_hiring_post'] and hiring_ctx.get('hiring_role'):
        signals.append({
            'type': 'hiring_post',
            'value': f"Hiring for {hiring_ctx['hiring_role']}",
            'priority': 4
        })
    
    # Priority 3: Hiring/recruiting focus (title says recruiter)
    elif title and any(word in title.lower() for word in ['recruit', 'talent', 'hiring']):
        domain = 'technical roles' if 'tech' in title.lower() else 'hiring'
        signals.append({
            'type': 'hiring_focus',
            'value': f"Recruiter focusing on {domain}",
            'priority': 3
        })
    
    # Priority 2: Technical role (ONLY if NOT a hiring post)
    if not hiring_ctx['is_hiring_post']:
        tech_keywords = ['engineer', 'developer', 'designer', 'product', 'architect', 'lead']
        for keyword in tech_keywords:
            if title and keyword in title.lower():
                signals.append({
                    'type': 'technical_role',
                    'value': f"{keyword.capitalize()} at {company}" if company else f"{keyword.capitalize()}",
                    'priority': 2
                })
                break
    
    # Priority 1: Interesting summary snippet (first sentence only)
    if summary and len(signals) == 0:
        first_sentence = summary.split('.')[0].strip()
        if 20 < len(first_sentence) < 100:
            signals.append({
                'type': 'summary',
                'value': first_sentence,
                'priority': 1
            })
    
    # Return highest priority signal or generic fallback
    if signals:
        best_signal = max(signals, key=lambda s: s['priority'])
        return {
            'signal': best_signal['value'],
            'type': best_signal['type'],
            'avoid': 'generic experience, achievements not mentioned, overly detailed background',
            'is_generic': False
        }
    
    # IMPROVED FALLBACK: Don't say "Professional at Unknown"
    if company:
        return {
            'signal': f"the work at {company}",
            'type': 'company_only',
            'avoid': 'making assumptions about their work',
            'is_generic': True
        }
    
    return {
        'signal': 'DevOps and cloud infrastructure',
        'type': 'user_interest',
        'avoid': 'making assumptions about their work',
        'is_generic': True
    }


def generate_fallback_draft(candidate: dict, sender_intro: str, signal: str, intent: str, contact_type: str) -> str:
    """Generate a template-based draft when AI fails (Resilience).
    
    IMPORTANT: All templates must produce human-quality output even with
    minimal/missing data. Never output 'Unknown' or hashtags.
    Context-aware: detects hiring posts and generates appropriate templates.
    """
    import random
    
    # Clean inputs — never let garbage through
    raw_name = candidate.get('name') or ''
    first_name = raw_name.split()[0] if raw_name and not raw_name.startswith('#') else None
    company = candidate.get('company') or None
    title = candidate.get('title') or None
    summary = candidate.get('summary') or ''
    sender_first = sender_intro.split()[0] if sender_intro else 'Siddharth'
    
    # Determine what info we actually have
    has_name = first_name is not None and first_name.lower() not in ('unknown', 'n/a')
    has_company = company is not None and company.lower() not in ('unknown', 'n/a')
    has_title = title is not None and title.lower() not in ('unknown', 'n/a')
    
    # DETECT HIRING CONTEXT from candidate data
    hiring_ctx = _detect_hiring_context(candidate)
    is_hiring_post = hiring_ctx['is_hiring_post']
    hiring_role = hiring_ctx.get('hiring_role') or title
    
    # Build greeting (skip 'Hr' or 'Hiring' as first names)
    if has_name and first_name.lower() not in ('hiring', 'hr', 'team'):
        greeting = f"Hi {first_name}"
    else:
        greeting = "Hi there"
    
    # ============ LINKEDIN TEMPLATES (with data-quality awareness) ============
    if contact_type == "linkedin":
        # HIRING POST TEMPLATES — these take priority over all other branches
        if is_hiring_post and has_title:
            role_label = hiring_role or title
            company_label = company if has_company else "your team"
            options = [
                f"{greeting}, I noticed your post about hiring for a {role_label} position. I am a DevOps engineer with a strong background in cloud infrastructure, automation, and site reliability, and I am very interested in this opportunity.\n\nThroughout my career, I have focused on building scalable and resilient systems. I have extensive experience with Infrastructure as Code using Terraform, container orchestration with Kubernetes, and implementing comprehensive CI/CD pipelines that allow teams to ship code faster without compromising stability. I treat every deployment as a software engineering problem, ensuring everything is version-controlled, tested, and repeatable.\n\nI believe my skills in cloud architecture, Linux systems, and automation align well with what {company_label} is looking for. I would love the opportunity to discuss how my background can contribute to the goals of this role. Would you be open to reviewing my profile or scheduling a brief call?",
                f"{greeting}, came across your post about the {role_label} opening at {company_label}. I wanted to reach out directly to express my interest and share a bit about my relevant background.\n\nI am an infrastructure engineer deeply passionate about automation and reliability. My experience spans managing complex cloud environments on AWS and GCP, designing zero-downtime deployment strategies, and building observability stacks with Prometheus and Grafana. I am a firm believer in the SRE philosophy of treating operations as a software challenge.\n\nThe {role_label} role you posted about resonates strongly with my career trajectory. I am confident that my hands-on experience with DevOps tooling and cloud-native architectures can add real value to your engineering team. Would you be available for a quick conversation about this opportunity, or would it be best if I sent over my resume?",
                f"{greeting}, saw that {company_label} is looking for a {role_label}. I am actively looking for my next opportunity in cloud infrastructure and DevOps, and this position seems like a great match for my skill set.\n\nOver the past several years, I have built deep expertise in designing and maintaining highly available cloud systems. I excel at writing automation in Python and Bash, managing Kubernetes clusters at scale, and implementing security best practices across the entire deployment pipeline. I am driven by the challenge of turning complex manual processes into elegant, automated workflows.\n\nI am very enthusiastic about this opportunity and would welcome the chance to discuss how my experience aligns with the requirements. Could we connect to talk further, or would you prefer I share my resume directly?",
            ]
            return random.choice(options)
        
        # BEST: Have name + company/title
        if has_name and has_company:
            if intent == "opportunity" or intent == IntentType.OPPORTUNITY:
                # OPPORTUNITY TEMPLATES (Direct Hiring Ask)
                options = [
                    f"{greeting}, noticed you're recruiting at {company}. I am reaching out because I am a DevOps engineer with a very strong background in cloud infrastructure, automation, and site reliability engineering.\n\nThroughout my career, I have consistently focused on building scalable, resilient systems that can handle high traffic while minimizing downtime. I am deeply passionate about automating repetitive tasks using tools like Terraform, Ansible, and Kubernetes, ensuring that deployments are seamless and environments are consistent from development to production.\n\nI noticed that {company} is pushing the boundaries in your industry, and I would love to bring my expertise in Linux systems and CI/CD pipelines to your engineering team. Are you currently open to reviewing my profile for any relevant infrastructure roles? I'd love to connect and see if there is a mutual fit.",
                    f"{greeting}, saw {company} is hiring. I specialize in DevOps and site reliability, and I am reaching out to explore potential synergies between my skillset and your engineering needs.\n\nMy approach to infrastructure is heavily rooted in Infrastructure as Code (IaC) principles. I believe that every aspect of the deployment lifecycle should be version-controlled, testable, and automated. I have extensive experience managing AWS environments, orchestrating containerized applications, and setting up robust monitoring and alerting systems to catch issues before they impact users.\n\nAs {company} continues to scale, having reliable backend operations is critical. I'd love to discuss how my background in SRE can help your team achieve its goals. Would you be open to a brief chat about your engineering needs or connecting so I can share my resume?",
                    f"{greeting}, verified your role at {company}. I'm looking for DevOps/SRE opportunities and wanted to share a bit about my technical philosophy and background.\n\nI have spent years honing my skills in cloud architecture, focusing on creating systems that are not just functional, but highly optimized and secure. I thrive in environments where infrastructure is treated like software, utilizing robust CI/CD pipelines to accelerate development cycles without sacrificing stability. Whether it's managing complex Linux clusters or optimizing Database performance, I am driven by the challenge of solving hard infrastructure problems.\n\nI admire the technical work happening at {company} and would be thrilled to contribute my expertise. Are you hiring for any roles that match this profile, or open to reviewing my background for future opportunities? Worth a quick look?"
                ]
            else:
                # STANDARD CONNECTION TEMPLATES
                options = [
                    f"{greeting}, saw your profile at {company}. I work in DevOps and cloud infrastructure, and I'm always looking to connect with other professionals in the tech space who share a passion for scalable systems.\n\nMy work typically revolves around automating server provisioning, managing Kubernetes clusters, and ensuring that our applications have five-nines of reliability. It requires a constant balance between pushing new features quickly and maintaining iron-clad stability, something I'm sure you appreciate in your role.\n\nI'm looking to expand my network with people who understand the complexities of modern software delivery. Would love to connect and exchange notes on how our respective teams handle infrastructure challenges.",
                    f"{greeting}, noticed you're at {company}. I'm exploring opportunities in {signal} and your background caught my eye. I am an infrastructure engineer heavily focused on the DevOps lifecycle.\n\nI believe that the best engineering teams are built on a foundation of strong automation and clear observability. My day-to-day involves writing Terraform scripts, designing resilient AWS architectures, and troubleshooting complex systemic issues across distributed microservices. It's a challenging field, but incredibly rewarding when everything runs smoothly.\n\nI am always eager to learn how different organizations, particularly innovative ones like yours, tackle these problems. Open to connecting to share insights?",
                    f"{greeting}, came across your profile while researching {company}. I have a background in cloud ops and automation, and I'm reaching out to build my professional network within the industry.\n\nI specialize in bridging the gap between development and operations. By implementing comprehensive CI/CD pipelines and shifting security left, I help teams deliver code faster and safer. I'm deeply familiar with the intricacies of Linux administration and container orchestration, which form the backbone of the systems I manage.\n\nI'd be very interested in hearing your perspective on the current technical landscape. Curious to connect and follow your team's work."
                ]
        elif has_name and has_title:
            if intent == "opportunity" or intent == IntentType.OPPORTUNITY:
                options = [
                    f"{greeting}, saw your work as {title}. I'm a DevOps engineer looking for new challenges, specifically roles where I can architect and manage large-scale cloud infrastructure.\n\nMy technical journey has been defined by a commitment to automation and reliability. I have successfully migrated legacy hardware to the cloud, implemented comprehensive monitoring solutions with Prometheus and Grafana, and drastically reduced deployment times using modern CI/CD practices. I treat infrastructure as code, ensuring that every change is tracked, tested, and reversible.\n\nI am currently exploring the market for roles that will allow me to leverage these skills to solve complex operational problems. Are you currently hiring for any infrastructure roles on your team?",
                    f"{greeting}, noticed you're a {title}. I have a background in SRE and cloud automation, and I'm reaching out to see if my profile aligns with any of your current hiring needs.\n\nAs a Site Reliability Engineer, my primary focus is protecting the user experience by ensuring the backend services are always available and performant. I write automation scripts in Python and Bash, manage complex Kubernetes deployments, and constantly analyze system metrics to identify potential bottlenecks before they cause outages. I am a strong advocate for proactive infrastructure management.\n\nI would love the opportunity to bring this proactive, automation-first mindset to your organization. Would you be open to reviewing my resume for potential fits?"
                ]
            else:
                options = [
                    f"{greeting}, your work as {title} caught my attention. I'm building experience in DevOps and cloud infrastructure, and I'm looking to connect with leaders and peers in the field.\n\nThe challenges of managing modern, distributed systems are what drive me. I spend my time diving deep into Linux kernel tuning, optimizing network routing, and finding new ways to automate tedious operational tasks. I believe that a strong DevOps culture is the key to velocity and stability in any software company.\n\nI am trying to expand my network thoughtfully with individuals whose careers I respect. Would love to connect and follow your journey.",
                    f"{greeting}, saw your role as {title}. I work in infrastructure and automation, where I focus on building resilient backend systems that can scale dynamically with user demand.\n\nMy expertise lies in taking complex, manual processes and turning them into streamlined, automated workflows. Whether it's setting up a new CI/CD pipeline from scratch or troubleshooting a difficult networking issue in a VPC, I enjoy the puzzle of operations engineering. I am constantly exploring new tools and methodologies to improve system reliability.\n\nI find your professional background very interesting. Curious to exchange perspectives and connect here on LinkedIn."
                ]
        elif has_name:
            if intent == "opportunity" or intent == IntentType.OPPORTUNITY:
                options = [
                    f"{greeting}, came across your profile. I'm a DevOps engineer actively looking for new roles in cloud infrastructure, and I'm reaching out to share my background.\n\nI have a strong track record of designing, implementing, and maintaining highly available cloud architectures. By treating operations as a software engineering problem, I utilize tools like Terraform, Docker, and Kubernetes to automate deployments and ensure consistency. I am passionate about eliminating manual toil and fostering a culture of continuous delivery & integration.\n\nI am eager to bring my skills to a forward-thinking team. Are you hiring for any relevant positions in the SRE or DevOps space?",
                    f"{greeting}, I'm an infrastructure engineer with cloud and automation experience, writing to you to explore potential career opportunities.\n\nMy focus is always on the triad of reliability, scalability, and security. I spend my days writing automation code, managing cloud providers, and configuring robust alerting systems to make sure the platform never goes down. I believe that good infrastructure should be invisible to the end-user, functioning flawlessly in the background.\n\nI am currently looking for my next big challenge. Are you open to reviewing profiles for potential DevOps openings at your company?"
                ]
            else:
                options = [
                    f"{greeting}, came across your profile and your background resonated with the work I do in DevOps and cloud infrastructure. I am looking to expand my professional circle.\n\nI spend my professional time building the systems that allow software to run securely and at scale. It is a constantly evolving field that requires an understanding of both high-level architecture and deep, low-level system internals. I enjoy the challenge of automating complex workflows and ensuring high availability.\n\nI respect the path you've taken in your career. Open to connecting and sharing insights?",
                    f"{greeting}, I'm building my network in the infrastructure and cloud space, and your profile stood out to me as someone I would like to be connected with.\n\nMy daily work involves a mix of systems administration, software engineering, and architectural planning. I advocate for Site Reliability Engineering principles, believing that we should use software to solve operational problems. It's a role that demands constant learning and adaptation to new technologies.\n\nI am trying to learn from others navigating this industry. Would love to stay in touch and connect."
                ]
        else:
            # MINIMAL DATA: Don't pretend we know them
            if intent == "opportunity" or intent == IntentType.OPPORTUNITY:
                options = [
                    f"Hi, I'm a DevOps engineer exploring new opportunities in the cloud infrastructure space. I am reaching out to see if my background might be a fit for your needs.\n\nMy core competencies include managing AWS/GCP environments, writing Infrastructure as Code (IaC) using Terraform, and orchestrating containerized applications with Kubernetes. I am deeply committed to the principles of Site Reliability Engineering, focusing on automating manual operational toil and ensuring systems are highly observable and resilient.\n\nAre you currently hiring for any cloud infrastructure or SRE roles? I would appreciate the opportunity to share my resume.",
                    f"Hi, I specialize in cloud operations and automation, and I'm looking for my next role. I wanted to proactively reach out with my professional background.\n\nI have dedicated my career to building the invisible backbone of modern software applications. I excel at designing CI/CD pipelines that allow developers to ship code rapidly without compromising on security or stability. From managing Linux servers to optimizing database performance, I thrive on solving complex backend infrastructure challenges.\n\nIf you're recruiting for DevOps roles, would you be open to a brief chat or reviewing my profile?"
                ]
            else:
                options = [
                    f"Hi, came across your profile while exploring roles in DevOps and cloud infrastructure. Would love to connect and learn more about your work.",
                    f"Hi, I'm a DevOps-focused engineer exploring opportunities in cloud operations and automation. Would love to connect.",
                    f"Hi, your profile came up while I was researching infrastructure roles. I work in DevOps and cloud — curious to connect.",
                ]
        return random.choice(options)
    
    # ============ EMAIL TEMPLATES ============
    else:
        subject = f"{company}" if has_company else "Quick intro"
        body_greeting = f"Hi {first_name}," if has_name else "Hi,"
        
        if has_name and has_company:
            body = f"{body_greeting}\n\nCame across your profile at {company}. I work in DevOps, cloud infrastructure, and automation — and your background resonated with the kind of work I enjoy.\n\nWould you be open to a brief exchange?\n\n{sender_first}"
        elif has_name:
            body = f"{body_greeting}\n\nI found your profile while exploring opportunities in {signal}. I work in cloud ops and systems engineering — your background caught my eye.\n\nOpen to connecting?\n\n{sender_first}"
        else:
            body = f"{body_greeting}\n\nI came across your profile while researching infrastructure and DevOps roles. I have hands-on experience in cloud operations and automation.\n\nWould love to connect if there's a fit.\n\n{sender_first}"
        
        return f"Subject: {subject}\n\n{body}"


async def generate_with_scoring(prompt: str, contact_type: str, candidate_context: dict, num_variants: int = 3, suggested_temp: float = None) -> Dict:
    """Generate multiple variants and return the highest scoring one.
    
    This is the SECRET SAUCE for reply-rate optimization.
    User sees 1 draft, but we generated 3 and picked the best.
    """
    import asyncio
    
    # Initialize Supabase client for memory features
    sb_client = get_supabase()

    # RAG: Fetch recent user edits for tone matching
    try:
        edits_data = sb_client.table("draft_edits") \
            .select("original_text, edited_text") \
            .eq("contact_type", contact_type) \
            .order("created_at", desc=True) \
            .limit(3) \
            .execute()
        recent_edits = edits_data.data if edits_data else []
    except Exception as e:
        logger.error(f"Failed to fetch draft edits for RAG: {str(e)}")
        recent_edits = []

    rag_context = ""
    if recent_edits:
        rag_context = "\n\nPAST TONE EXAMPLES (RAG FEEDBACK):\n"
        rag_context += "The user has previously manually edited your drafts to sound more like them. Study these examples to match their style:\n"
        for idx, edit in enumerate(recent_edits):
            rag_context += f"--- Example {idx+1} ---\n"
            rag_context += f"Original: {edit.get('original_text', '')}\n"
            rag_context += f"User's Edit: {edit.get('edited_text', '')}\n"
        rag_context += "Focus on exactly how they change your phrasing and word choice. Adopt their edited style.\n"

    # Generate variants with CHANNEL-SPECIFIC temperatures (Gemini Tuning)
    # LinkedIn: 0.35 - 0.45 (Strict control)
    # Email: 0.45 - 0.55 (Slight flow)
    base_temp = suggested_temp if suggested_temp else (0.35 if contact_type == "linkedin" else 0.45)
    
    # Prepare tasks for parallel execution
    tasks = []
    
    for i in range(num_variants):
        temp = base_temp + (i * 0.05)
        
        # Use intent-based system prompt
        intent_value = candidate_context.get('intent', IntentType.CURIOUS)
        # Convert string back to Enum for dict lookup if needed
        if isinstance(intent_value, str):
            try:
                intent_value = IntentType(intent_value)
            except ValueError:
                intent_value = IntentType.CURIOUS
        
        system_prompt = SYSTEM_PROMPTS.get(intent_value, SYSTEM_PROMPTS[IntentType.CURIOUS])
        
        if rag_context:
            system_prompt += rag_context
        
        # Create a coroutine for each generation task (Prio: Qubrid -> Gemini)
        if get_qubrid_client():
            tasks.append(generate_with_qubrid(prompt, temperature=temp, system_prompt=system_prompt, max_tokens=1500))
        else:
            tasks.append(generate_with_gemini(prompt, temperature=temp, system_prompt=system_prompt))

    # Execute all generation tasks in parallel
    if not tasks:
        return None

    # Wait for all generations to complete
    responses = await asyncio.gather(*tasks)
    
    # Fetch recent sent hashes for deduplication
    sent_hashes = get_recent_opener_hashes(sb_client)
    
    variants = []
    for i, response_text in enumerate(responses):
        temp = base_temp + (i * 0.05)
        if response_text:
            # Extract opener for hashing
            opener = response_text.split('\n')[0].strip()
            if "," in opener and len(opener.split(',')[0]) < 20:
                opener = opener.split(',', 1)[1].strip()
            
            # Compute hash
            opener_hash = hashlib.md5(opener.lower().encode()).hexdigest()
            
            # Base score
            score = score_draft(response_text, contact_type, candidate_context)
            
            # Anti-Repetition Penalty (Optimization 13 + Phase 2 Semantic)
            if opener_hash in sent_hashes:
                logger.warning(f"Repeated opener detected (hash: {opener_hash[:8]}). Penalizing variant {i+1}.")
                score -= 80  # Heavy penalty for exact repetition
            
            # Semantic Deduplication
            embedding = embeddings_service.generate_embedding(opener)
            similar = get_semantically_similar_openers(sb_client, embedding)
            if similar:
                max_sim = max([s['similarity'] for s in similar])
                logger.warning(f"Semantically similar opener detected (sim: {max_sim:.2f}). Penalizing variant {i+1}.")
                score -= 40 * max_sim # Dynamic penalty based on similarity
            
            variants.append({
                "text": response_text, 
                "score": score, 
                "temp": temp, 
                "opener_hash": opener_hash,
                "embedding": embedding
            })
            logger.info(f"Variant {i+1}: score={score:.1f}, temp={temp}, hash={opener_hash[:8]}")
    
    # Return the best one
    if variants:
        best = max(variants, key=lambda v: v["score"])
        logger.info(f"SELECTED: score={best['score']:.1f}, temp={best['temp']}")
        return best
    
    return None


# Updated system prompts with stronger tone anchors + Q2 Persona Anchor
SYSTEM_PROMPTS = {
    IntentType.CURIOUS: PERSONA_ANCHOR + """
You are writing a LinkedIn connection request.
TONE: Casual, mid-thought, low-pressure. Like a quick note to a peer.
GOAL: Spark conversation, not a meeting.

NEGATIVE CONSTRAINTS (CRITICAL):
- Do NOT explain.
- Do NOT give advice.
- Do NOT include context-setting sentences.
- Do NOT use "I hope this finds you well".
- Do NOT use "I wanted to reach out".

RULES:
- Start MID-THOUGHT ("Saw you're...", "Noticed...")
- NO introductions ("Hi name, I am...")
- Write 1-2 distinct paragraphs.
- MAX 1 question.

STRUCTURE:
1. "Hi [Name]"
2. Observation ("Saw you're hiring for X", "Noticed your post on Y")
3. Soft question ("Curious how you're thinking about Z", "Open to a quick exchange?")

MAX: 600 chars. Write the message ONLY.
""",
    IntentType.PEER: PERSONA_ANCHOR + """
You are writing a cold email to a peer.
TONE: Professional but 'typed', not 'composed'. Slightly asymmetrical.
GOAL: Soft networking or idea exchange.

NEGATIVE CONSTRAINTS (CRITICAL):
- Do NOT explain why you are writing.
- Do NOT use formal transitions ("Additionally", "Moreover").
- Do NOT summarize.
- Do NOT look for "synergies".

RULES:
- Paragraphs should be short and punchy.
- No "Sincerely" or "Best regards".

STRUCTURE:
Subject: [Re: their work/role] or [Quick question]
Body:
1. Context (1 sentence)
2.The "Ask" / Curiosity (1 sentence)
Sign-off: "Curious how this lines up.", "Open to thoughts?"

MAX: 90 words. Write the message ONLY.
""",
    IntentType.SOFT: PERSONA_ANCHOR + """
You are writing a soft networking message.
TONE: Warm, friendly, slightly deferential but confident.
GOAL: Get on their radar without asking for anything heavy.
NEGATIVE CONSTRAINTS (CRITICAL):
- Do NOT explain.
- Do NOT use "picked your brain" or "15 mins".

RULES:
- Genuine compliment (must be specific).
- Soft open loop ("Wondering if...")

MAX: 600 chars (LI) or 80 words (Email). Write the message ONLY.
""",
    IntentType.DIRECT: PERSONA_ANCHOR + """
You are writing a high-signal value email.
TONE: Direct, calm, confident.
GOAL: Proposition value without sales hype.
NEGATIVE CONSTRAINTS (CRITICAL):
- Do NOT use buzzwords ("revolutionize", "synergy").
- Do NOT explain the value proposition ("This allows you to..."). Show it.

RULES:
- Problem -> Solution -> Soft CTA
- CTA must be soft: "Worth a look?", "Open to a peek?"

MAX: 100 words. Write the message ONLY.
""",
    IntentType.OPPORTUNITY: PERSONA_ANCHOR + """
You are writing a LinkedIn connection request to a Recruiter or TA.
TONE: Brief, professional, and high-impact.
GOAL: Ask to connect about open roles.
NEGATIVE CONSTRAINTS (CRITICAL):
- Do NOT use "I'm a DevOps engineer with experience in...". That is boring.
- Do NOT use "I hope this email finds you well".
- Do NOT write multiple paragraphs.
- Do NOT exceed 280 characters under ANY circumstances.

RULES:
- Hook them immediately with your strongest skill mapped to their role.
- Keep it to 2 short sentences total.
- Soft Ask: "Open to connecting?"

STRUCTURE:
1 sentence value prop. 1 short question.

Write the message ONLY. Make it extremely brief, ABSOLUTE MAXIMUM 280 characters.
""",


    "GENERIC": PERSONA_ANCHOR + """
You are writing a generic but polite outreach.
TONE: Honest, extremely brief.
GOAL: Connect without pretending to know them deeply.
STRATEGY: Be vulnerable ("I don't know you well but...")
MAX: 150 chars. Write the message ONLY.
"""
}





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
            return result.data[0]
    raise HTTPException(status_code=500, detail="Failed to create draft")








@router.post("/generate/{candidate_id}")
async def generate_draft(candidate_id: int, context: str = "", contact_type: str = "auto"):
    """Generate AI draft with MULTI-VARIANT SCORING (Priority 1-3 Optimizations)."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Auto-detect contact type
        if contact_type == "auto":
            contact_type = "linkedin"  # Email drafting disabled

        # R5: Strict channel lock — reject invalid contact types early
        if contact_type not in VALID_CHANNELS:
            raise HTTPException(status_code=400, detail=f"Invalid contact_type: {contact_type}. Must be one of {VALID_CHANNELS}")

        # PRE-FLIGHT: Run all independent DB queries concurrently (Massive TTFT Reduction)
        def _fetch_candidate():
            try: return supabase.table("candidates").select("*").eq("id", candidate_id).single().execute().data
            except Exception: return None

        def _fetch_settings():
            try:
                res = supabase.table("user_settings").select("*").eq("id", 1).execute()
                return res.data[0] if res and res.data else {"full_name": "Siddharth", "company": "Antigravity", "role": "Founder"}
            except Exception: return {"full_name": "Siddharth", "company": "Antigravity", "role": "Founder"}
                
        def _fetch_last_draft():
            try: return supabase.table("drafts").select("*").eq("candidate_id", candidate_id).order("created_at", desc=True).limit(1).execute().data
            except Exception: return []

        (
            raw_candidate, 
            settings, 
            brain, 
            existing_query_data,
            recent_openers, 
            biased_params
        ) = await asyncio.gather(
            asyncio.to_thread(_fetch_candidate),
            asyncio.to_thread(_fetch_settings),
            asyncio.to_thread(get_cached_brain_context, supabase),
            asyncio.to_thread(_fetch_last_draft),
            asyncio.to_thread(get_recent_openers, supabase),
            asyncio.to_thread(get_biased_parameters, supabase)
        )

        # 1. Validate Candidate Data
        if not raw_candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # 1.5 CRITICAL: Clean candidate data before it touches any prompt
        c = clean_candidate_data(raw_candidate)
        logger.info(f"Data quality for candidate {candidate_id}: {c['_data_quality']}/4 | Name: {c.get('name')} | Title: {c.get('title')} | Company: {c.get('company')}")
            
        sender_intro = f"{settings.get('full_name', 'Siddharth')} from {settings.get('company', 'Antigravity')}"

        # H1: Compute Deterministic Fingerprint
        tone_directive = CHANNEL_TONE.get(contact_type, "")
        fingerprint = generate_fingerprint(
            candidate_id, 
            contact_type, 
            brain.get("extracted_skills", []), 
            brain.get("resume_text", ""), 
            tone_directive
        )

        # R1 & H1: Idempotency Check
        if existing_query_data:
            d = existing_query_data[0]
            recent_cutoff = (datetime.utcnow() - timedelta(seconds=60)).isoformat()
            created_at = d.get("created_at")
            stored_params = d.get("generation_params") or {}
            stored_fingerprint = stored_params.get("fingerprint")
            
            is_recent = created_at >= recent_cutoff
            is_fingerprint_match = (stored_fingerprint == fingerprint)
            
            if is_recent or is_fingerprint_match:
                reason_code = GenerationReason.IDEMPOTENT_RETURN
                logger.info(f"Idempotent hit: candidate {candidate_id} | Recent: {is_recent} | HashMatch: {is_fingerprint_match}")
                
                if contact_type == "linkedin":
                    return {
                        "type": "linkedin", "message": d.get("body", ""),
                        "char_count": len(d.get("body", "")),
                        "quality_score": stored_params.get("score", 0),
                        "draft_id": d["id"],
                        "time_to_read": calculate_time_to_read(d.get("body", "")),
                        "variant_id": d.get("variant_id"), 
                        "is_idempotent": True,
                        "reason": reason_code
                    }
                else:
                    return {
                        "type": "email", "subject": d.get("subject", ""),
                        "body": d.get("body", ""),
                        "word_count": len(d.get("body", "").split()),
                        "quality_score": stored_params.get("score", 0),
                        "draft_id": d["id"],
                        "time_to_read": calculate_time_to_read(d.get("body", "")),
                        "variant_id": d.get("variant_id"), 
                        "is_idempotent": True,
                        "reason": reason_code
                    }

        # R2: Hard fail-fast on missing brain context
        if not brain.get("extracted_skills") and not brain.get("resume_text"):
            raise HTTPException(
                status_code=412,
                detail="Brain context is empty. Please add your skills first."
            )

        # EARLY EXIT: If data quality is too low, skip AI and use smart template directly
        if c['_data_quality'] <= 1:
            logger.warning(f"Low data quality ({c['_data_quality']}/4) for candidate {candidate_id}. Using smart template.")
            signal = extract_primary_signal(c)
            intent = IntentType.OPPORTUNITY
            fallback_text = generate_fallback_draft(
                c, sender_intro, signal['signal'],
                intent.value, contact_type
            )
            variant_id = str(uuid.uuid4())
            gen_params = {
                "variant_id": variant_id,
                "score": 60.0,
                "model": "smart-template-low-data",
                "context_band": "LOW",
                "signal_type": signal.get('type', 'generic'),
                "is_fallback": True,
                "data_quality": c['_data_quality']
            }
            if contact_type == "linkedin":
                res = supabase.table("drafts").insert({
                    "candidate_id": candidate_id, "subject": "",
                    "body": fallback_text, "intent": intent,
                    "temperature": 0.0, "signal_used": signal['signal'],
                    "variant_id": variant_id, "generation_params": gen_params
                }).execute()
                return {
                    "type": "linkedin", "message": fallback_text,
                    "char_count": len(fallback_text),
                    "quality_score": 60.0,
                    "draft_id": res.data[0]["id"],
                    "time_to_read": calculate_time_to_read(fallback_text),
                    "variant_id": variant_id, "is_fallback": True
                }
            else:
                lines = fallback_text.strip().split('\n')
                subject = "Quick intro"
                body_lines = []
                for line in lines:
                    if "Subject:" in line:
                        subject = line.replace("Subject:", "").strip()
                    elif line.strip():
                        body_lines.append(line)
                final_body = "\n".join(body_lines).strip()
                res = supabase.table("drafts").insert({
                    "candidate_id": candidate_id, "subject": subject,
                    "body": final_body, "intent": intent,
                    "temperature": 0.0, "signal_used": signal['signal'],
                    "variant_id": variant_id, "generation_params": gen_params
                }).execute()
                return {
                    "type": "email", "subject": subject, "body": final_body,
                    "word_count": len(final_body.split()),
                    "quality_score": 60.0,
                    "draft_id": res.data[0]["id"],
                    "time_to_read": calculate_time_to_read(final_body),
                    "variant_id": variant_id, "is_fallback": True
                }

        skills = ", ".join(brain.get("extracted_skills", [])) or "DevOps, Cloud Infrastructure, Linux, CI/CD, Automation"

        # 3. CONTEXT COMPRESSION & MEMORY (Priority 2, 13)
        signal = extract_primary_signal(c)
        
        # Fetch Memory (Avoid Repetition) - Used pre-fetched concurrent result
        memory_constraint = ""
        if recent_openers:
            blocklist = "\\n- ".join(recent_openers)
            memory_constraint = f"\\nAvoid these recent openers:\\n- {blocklist}"
        
        logger.info(f"Primary signal: {signal['signal']} | Avoid: {signal['avoid']}")

        # 4. Build Prompt (Optimization 11, 12, 17)
        # Used pre-fetched concurrent result
        logger.info(f"Biasing suggestions: {biased_params}")

        # CONTEXT-AWARE CLASSIFICATION
        hiring_ctx = _detect_hiring_context(c)
        is_hiring_post = hiring_ctx['is_hiring_post']
        hiring_role = hiring_ctx.get('hiring_role')
        recipient_role = hiring_ctx['recipient_role']
        
        # Detect POST TYPE: LinkedIn Jobs section vs hiring post vs profile
        linkedin_url = c.get('linkedin_url') or ''
        post_type = 'profile'  # default
        if '/jobs/' in linkedin_url or '/job/' in linkedin_url:
            post_type = 'linkedin_job'  # From LinkedIn Jobs section
            is_hiring_post = True  # Always a hiring post
        elif '/posts/' in linkedin_url or '/feed/' in linkedin_url:
            post_type = 'linkedin_post'  # Regular LinkedIn post
        elif '/in/' in linkedin_url:
            post_type = 'linkedin_profile'  # Profile page
        
        logger.info(f"Context: is_hiring_post={is_hiring_post}, hiring_role={hiring_role}, recipient_role={recipient_role}, post_type={post_type}")
        
        # Determine if Recipient is Company (Hiring Team) or Person
        is_company_recipient = False
        if c.get('name') == "Hiring Team" or (c.get('company') and c.get('name') and c.get('company').lower() in c.get('name').lower()):
             is_company_recipient = True
        
        # Context Bands
        context_band = "LOW"
        if len(brain.get("extracted_skills", [])) > 2 and c.get('title'):
            context_band = "MEDIUM"
        if signal.get('signal') and not signal.get('is_generic'):
            context_band = "HIGH"

        # ============================================================
        # DYNAMIC USER BIO — Built from Brain/Cortex skills
        # ============================================================
        sender_name = settings.get('full_name', 'Siddharth Chavan')
        sender_company = settings.get('company', '')
        sender_role = settings.get('role', 'DevOps Engineer')
        
        user_bio = f"""
        Name: {sender_name}
        Role: {sender_role}
        Key Skills: {skills}
        {f'Current Company: {sender_company}' if sender_company else ''}
        Status: Actively looking for opportunities where I can apply these skills.
        """.strip()

        # Get post context (first 800 chars for richer understanding)
        post_context = (c.get('summary') or '')[:800].strip()

        # ============================================================
        # INTENT ROUTING (Post-type aware)
        # ============================================================
        if is_company_recipient:
             intent = IntentType.SOFT
             role_context = c.get('title') or 'DevOps / SRE Role'
             task_instruction = "Generate a job inquiry message to a company page. Be respectful but direct about seeking opportunities."
        elif is_hiring_post:
             intent = IntentType.OPPORTUNITY
             role_context = "DevOps / Site Reliability Engineer"
             if post_type == 'linkedin_job':
                 task_instruction = f"Generate a JOB APPLICATION message. This is from a LinkedIn JOBS listing for '{hiring_role or c.get('title')}'. Write as if APPLYING for this specific position. Be specific about relevant skills."
             else:
                 task_instruction = f"Generate a JOB APPLICATION message. The recipient POSTED about hiring for '{hiring_role or c.get('title')}'. Express genuine interest in the position they mentioned. Reference specifics from their post."
        elif (c.get('title') and ("recruiter" in c.get('title').lower() or "talent" in c.get('title').lower())):
             intent = IntentType.OPPORTUNITY
             role_context = "DevOps / Site Reliability Engineer"
             task_instruction = "Generate a JOB-SEEKING message to a recruiter. Ask directly if they have DevOps/SRE/Cloud openings. Be clear you are looking for work, not just networking."
        else:
             intent = IntentType.OPPORTUNITY
             candidate_title = (c.get('title') or '').lower()
             role_context = "DevOps / Site Reliability Engineer"
             if candidate_title and "recruiter" not in candidate_title and "talent" not in candidate_title:
                 role_context = c.get('title') or 'DevOps / SRE Role'
             task_instruction = "Generate a JOB OPPORTUNITY message. You are reaching out to explore job opportunities — NOT to network. Ask about openings at their company."

        # ============================================================
        # PROMPT CONSTRUCTION (Job-Application Focused)
        # ============================================================
        if intent == IntentType.OPPORTUNITY:
            # Build context block based on post type
            if is_hiring_post:
                if post_type == 'linkedin_job':
                    context_block = f"""
            SOURCE: LinkedIn JOBS listing
            CRITICAL: This is a formal JOB POSTING from the Jobs section on LinkedIn.
            - The listing is for: {hiring_role or c.get('title')}
            - The recipient posted this job at: {c.get('company') or 'their company'}
            - Write as if you are APPLYING FOR THIS JOB. This is a job application, not a connection request.
            - Reference the specific role and why your skills ({skills}) make you a strong candidate.
            - DO NOT say 'looking to connect' or 'expand my network'.
            - DO say 'I am interested in the {hiring_role or c.get('title')} position' or 'applying for the role'.
            
            JOB DESCRIPTION:
            {post_context}
            """
                else:
                    context_block = f"""
            SOURCE: LinkedIn POST about hiring
            CRITICAL: This person WROTE A POST about hiring. They are a {recipient_role}.
            - They posted about hiring for: {hiring_role or c.get('title')}
            - They are NOT a {hiring_role or c.get('title')} themselves — they are RECRUITING for that role.
            - DO NOT say 'saw your work as {hiring_role}' — they don't work in that role.
            - DO reference their post: 'saw your post about the {hiring_role} opening' or 'noticed you are hiring for {hiring_role}'.
            - Express genuine interest in the position and explain how your skills ({skills}) are relevant.
            
            THEIR POST:
            {post_context}
            """
            else:
                # Regular profile — this person may or may not be hiring
                context_block = f"""
            SOURCE: LinkedIn Profile
            This person is {c.get('name') or 'a professional'}, working as {c.get('title') or 'a professional'} at {c.get('company') or 'their company'}.
            {f'PROFILE CONTEXT: {post_context}' if post_context else ''}
            
            You are reaching out to explore if their company has DevOps/SRE openings.
            Mention how your skills ({skills}) could add value to their team.
            """
            
            prompt = f'''
            # JOB APPLICATION MESSAGE GENERATOR
            
            You are writing a LinkedIn message on behalf of someone ACTIVELY SEEKING A JOB.
            This is a JOB APPLICATION outreach — NOT a networking or connection request.
            
            == APPLICANT (the person writing this message) ==
            {user_bio}
            
            == RECIPIENT ==
            Name: {c.get('name') or 'Hiring Professional'}
            At: {c.get('company') or 'their company'}
            
            {context_block}
            
            == RULES ==
            1. TASK: {task_instruction}
            2. This is a JOB APPLICATION. The applicant wants to WORK at their company.
            3. Mention specific skills from the applicant's profile: {skills}
            4. NEVER say: "looking to connect", "expand my network", "great to meet", "love to chat"
            5. ALWAYS say things like: "interested in the role", "would love to apply", "my skills in X align with", "available for an interview"
            6. End with a concrete CTA: ask to share resume, schedule a call, or submit application
            7. Write in first person as {sender_name}. Sound eager but professional.
            8. Be detailed and comprehensive. Aim for ~300 words / ~2000 characters.
            9. No emojis. No quotes around the message. Just the message text.
            10. Do NOT start with "I'm an experienced engineer". Start with a reference to their post/role/company.
            '''
        else:
            # SOFT INTENT (Company pages, exploratory)
            prompt = f'''
            # JOB INQUIRY MESSAGE
            
            You are writing a LinkedIn message to a company or hiring team on behalf of a job seeker.
            
            == APPLICANT ==
            {user_bio}
            
            == RECIPIENT ==
            {c.get('name') or 'Hiring Team'} at {c.get('company') or 'the company'}
            Role listed: {c.get('title') or 'not specified'}
            {f'CONTEXT: {post_context}' if post_context else ''}
            
            == TASK ==
            {task_instruction}
            - Write a professional inquiry about open positions.
            - Mention specific skills: {skills}
            - Ask if they are currently hiring for roles matching this background.
            - Sound professional and genuinely interested, not generic.
            - End with a clear ask: share resume, schedule a call, etc.
            - Be detailed. Aim for ~250 words.
            - No emojis. Only the message text.
            '''

        # Q5: Inject channel tone lock into prompt
        tone_directive = CHANNEL_TONE.get(contact_type, "")
        if tone_directive:
            prompt = f"{tone_directive}\n\n{prompt}"

        # 5. MULTI-VARIANT SCORING (Priority 1)
        # Reduced to 1 variant for Gemini Free Tier (Optimization 69)
        candidate_context = {
            'name': c.get('name'),
            'company': c.get('company'),
            'title': c.get('title'),
            'intent': intent
        }
        
        # H3: STRICT FALLBACK LADDER (Gemini -> Retry -> Template)
        # Note: Retry logic is handled inside generate_with_scoring/generate_with_gemini via tenacity
        try:
            result = await generate_with_scoring(
                prompt, 
                contact_type, 
                candidate_context, 
                num_variants=1,
                suggested_temp=biased_params.get("suggested_temperature")
            )
            reason_code = GenerationReason.FRESH_GENERATION
        except Exception as e:
            logger.error(f"H3: AI Generation CRITICAL FAILURE: {e}")
            result = None
            reason_code = GenerationReason.FALLBACK_TEMPLATE
        
        if not result:
            # H3: Final Fallback - Use Template
            logger.warning("Switching to Fallback Template (Reason: AI Failed or Result None).")
            fallback_text = generate_fallback_draft(
                c, sender_intro, signal['signal'],
                intent.value, contact_type
            )
            variant_id = str(uuid.uuid4())
            
            # H1/H2/H5: Audit Metadata
            gen_params = {
                "variant_id": variant_id,
                "score": 55.0, # Baseline for templates
                "model": "fallback-template",
                "context_band": context_band,
                "signal_type": signal.get('type', 'generic'),
                "is_fallback": True,
                "data_quality": c.get('_data_quality', 0),
                "fingerprint": fingerprint,       # H1
                "data_quality": c.get('_data_quality', 0),
                "fingerprint": fingerprint,       # H1
                "prompt_version": PROMPT_VERSION, # H2
                "reason": reason_code,            # H5
                "skill_count": len(brain.get("extracted_skills", [])) # H6
            }
            # (Duplicate block removed)
            if contact_type == "linkedin":
                res = supabase.table("drafts").insert({
                    "candidate_id": candidate_id, "subject": "",
                    "body": fallback_text, "intent": intent,
                    "temperature": 0.0, "signal_used": signal['signal'],
                    "variant_id": variant_id, "generation_params": gen_params
                }).execute()
                return {
                    "type": "linkedin", "message": fallback_text,
                    "char_count": len(fallback_text),
                    "quality_score": 55.0,
                    "draft_id": res.data[0]["id"],
                    "time_to_read": calculate_time_to_read(fallback_text),
                    "variant_id": variant_id, "is_fallback": True
                }
            else:
                lines = fallback_text.strip().split('\n')
                subject = "Quick intro"
                body_lines = []
                for line in lines:
                    if "Subject:" in line:
                        subject = line.replace("Subject:", "").strip()
                    elif line.strip():
                        body_lines.append(line)
                final_body = "\n".join(body_lines).strip()
                res = supabase.table("drafts").insert({
                    "candidate_id": candidate_id, "subject": subject,
                    "body": final_body, "intent": intent,
                    "temperature": 0.0, "signal_used": signal['signal'],
                    "variant_id": variant_id, "generation_params": gen_params
                }).execute()
                return {
                    "type": "email", "subject": subject, "body": final_body,
                    "word_count": len(final_body.split()),
                    "quality_score": 55.0,
                    "draft_id": res.data[0]["id"],
                    "time_to_read": calculate_time_to_read(final_body),
                    "variant_id": variant_id, "is_fallback": True
                }
        
        response_text = result['text']
        score = result['score']

        # ---- POST-PROCESSING PIPELINE (Q4, Q6, Q1) ----
        # Q6: Remove hedging language
        response_text = remove_hedging(response_text)
        # Q4: Length normalization + hard trim
        response_text = normalize_length(response_text, contact_type)
        # Q1: Structure validation
        if not validate_structure(response_text, contact_type):
            logger.warning(f"Q1 Structure validation failed for candidate {candidate_id}. Using as-is (still valid content).")
        # Q3: Skills grounding check
        user_skills = brain.get("extracted_skills", [])
        if user_skills:
            grounding = verify_skills_grounding(response_text, user_skills)
            if grounding["hallucinated"]:
                logger.warning(f"Q3 Hallucinated skills detected: {grounding['hallucinated']}")
        
        logger.info(f"FINAL DRAFT | Score: {score:.1f} | Type: {contact_type} | Length: {len(response_text)}")

        # 6. Parse and Save
        # Compute variant ID for this generation attempt
        variant_id = str(uuid.uuid4())
        gen_params = {
            "variant_id": variant_id,
            "score": score,
            "opener_hash": result.get('opener_hash'),
            "embedding": result.get('embedding'),
            "model": "gemini-2.0-flash",
            "temperature": result.get('temp', 0.4),
            "context_band": context_band,
            "signal_type": signal['type'],
            # H1/H2/H5: Audit Metadata
            "fingerprint": fingerprint,
            "prompt_version": PROMPT_VERSION,
            "reason": reason_code,
            "skill_count": len(brain.get("extracted_skills", [])) # H6
        }

        if contact_type == "linkedin":
            final_msg = response_text.replace("Subject:", "").strip()
            
            # Ensure proper greeting
            first_name = c['name'].split()[0] if c.get('name') else 'there'
            # Don't prepend greeting if name is garbage
            if not final_msg.lower().startswith("hi"):
                if first_name and first_name.lower() not in ('unknown', 'n/a', '#'):
                    final_msg = f"Hi {first_name}, " + final_msg
                else:
                    final_msg = "Hi, " + final_msg

            # Enforce Hard LinkedIn Limit (300 chars max, 280 safe)
            if len(final_msg) > 280:
                logger.warning(f"Draft exceeded LinkedIn limits ({len(final_msg)} chars). Truncating.")
                # Truncate to word boundary before 277 chars and add ...
                final_msg = final_msg[:277].rsplit(' ', 1)[0] + "..."

            res = supabase.table("drafts").insert({
                "candidate_id": candidate_id, 
                "subject": "", 
                "body": final_msg,
                "intent": intent,
                "temperature": result.get('temp'),
                "signal_used": signal['signal'],
                "variant_id": variant_id,
                "generation_params": gen_params
            }).execute()
            
            return {
                "type": "linkedin", 
                "message": final_msg, 
                "char_count": len(final_msg), 
                "quality_score": round(score, 1),
                "draft_id": res.data[0]["id"],
                "time_to_read": calculate_time_to_read(final_msg),
                "variant_id": variant_id
            }

        else:
            # Email parsing
            lines = response_text.strip().split('\n')
            subject = "Quick question"
            body_lines = []
            
            for line in lines:
                if "Subject:" in line:
                    subject = line.replace("Subject:", "").strip()
                elif line.strip():  # Non-empty lines
                    body_lines.append(line)
            
            final_body = "\n".join(body_lines).strip()
            
            res = supabase.table("drafts").insert({
                "candidate_id": candidate_id, 
                "subject": subject, 
                "body": final_body,
                "intent": intent,
                "temperature": result.get('temp'),
                "signal_used": signal['signal'],
                "variant_id": variant_id,
                "generation_params": gen_params
            }).execute()
            
            return {
                "type": "email", 
                "subject": subject, 
                "body": final_body, 
                "word_count": len(final_body.split()),
                "quality_score": round(score, 1),
                "draft_id": res.data[0]["id"],
                "time_to_read": calculate_time_to_read(final_body),
                "variant_id": variant_id
            }

    except HTTPException:
        # If it's a 500 from AI failure, fallback to template
        logger.warning("AI Generation failed. Switching to Fallback Template.")
        fallback_text = generate_fallback_draft(
            c, 
            sender_intro, 
            signal['signal'], 
            intent.value if hasattr(intent, 'value') else str(intent),
            contact_type
        )
        
        # We need to wrap this in the same structure as a successful result to save it
        variant_id = str(uuid.uuid4())
        gen_params = {
            "variant_id": variant_id,
            "score": 50.0, # Average score for fallback
            "model": "fallback-template",
            "context_band": context_band,
            "signal_type": signal.get('type', 'generic'),
            "is_fallback": True
        }

        # Save Fallback Draft
        if contact_type == "linkedin":
            res = supabase.table("drafts").insert({
                "candidate_id": candidate_id, 
                "subject": "", 
                "body": fallback_text,
                "intent": intent,
                "temperature": 0.0,
                "signal_used": signal['signal'],
                "variant_id": variant_id,
                "generation_params": gen_params
            }).execute()
            
            return {
                "type": "linkedin", 
                "message": fallback_text, 
                "char_count": len(fallback_text), 
                "quality_score": 50.0,
                "draft_id": res.data[0]["id"],
                "time_to_read": calculate_time_to_read(fallback_text),
                "variant_id": variant_id,
                "is_fallback": True
            }
        else:
            # Email Fallback
            subject = "Quick question"
            res = supabase.table("drafts").insert({
                "candidate_id": candidate_id, 
                "subject": subject, 
                "body": fallback_text,
                "intent": intent,
                "temperature": 0.0,
                "signal_used": signal['signal'],
                "variant_id": variant_id,
                "generation_params": gen_params
            }).execute()
            
            return {
                "type": "email", 
                "subject": subject, 
                "body": fallback_text, 
                "word_count": len(fallback_text.split()),
                "quality_score": 50.0,
                "draft_id": res.data[0]["id"],
                "time_to_read": calculate_time_to_read(fallback_text),
                "variant_id": variant_id,
                "is_fallback": True
            }

    except Exception as e:
        logger.error(f"Generate Check Failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback Logic (Optimization 10)
        logger.error("Falling back to Template Logic due to unexpected error.")
        
        # Ensure variables exist even if exception happened early in the try block
        safe_c = c if 'c' in locals() else {"summary": "Experienced professional"}
        safe_intent = intent.value if 'intent' in locals() and hasattr(intent, 'value') else "opportunity"
        safe_signal = signal['signal'] if 'signal' in locals() else "Looking to connect and explore opportunities."
        safe_sender = sender_intro if 'sender_intro' in locals() else "A professional"
        safe_contact = contact_type if 'contact_type' in locals() else "linkedin"
        
        fallback_text = generate_fallback_draft(
            safe_c, safe_sender, safe_signal, safe_intent, safe_contact
        )
        
        variant_id = str(uuid.uuid4())
        gen_params = {
            "variant_id": variant_id,
            "score": 50.0,
            "model": "fallback-template-error",
            "is_fallback": True
        }
        
        draft_id = 0
        try:
            if safe_contact == "linkedin":
                res = supabase.table("drafts").insert({
                    "candidate_id": candidate_id, "subject": "", 
                    "body": fallback_text, "intent": safe_intent,
                    "temperature": 0.0, "signal_used": safe_signal,
                    "variant_id": variant_id, "generation_params": gen_params
                }).execute()
                draft_id = res.data[0]["id"] if res.data else 0
            else:
                res = supabase.table("drafts").insert({
                    "candidate_id": candidate_id, "subject": "Quick intro", 
                    "body": fallback_text, "intent": safe_intent,
                    "temperature": 0.0, "signal_used": safe_signal,
                    "variant_id": variant_id, "generation_params": gen_params
                }).execute()
                draft_id = res.data[0]["id"] if res.data else 0
        except Exception as db_err:
            logger.error(f"Failed to save fallback draft to DB: {db_err}")

        if safe_contact == "linkedin":
            return {
                "type": "linkedin", "message": fallback_text, 
                "char_count": len(fallback_text), "quality_score": 50.0,
                "draft_id": draft_id, "time_to_read": calculate_time_to_read(fallback_text),
                "variant_id": variant_id, "is_fallback": True
            }
        else:
            return {
                "type": "email", "subject": "Quick intro", "body": fallback_text, 
                "word_count": len(fallback_text.split()), "quality_score": 50.0,
                "draft_id": draft_id, "time_to_read": calculate_time_to_read(fallback_text),
                "variant_id": variant_id, "is_fallback": True
            }

from fastapi import Request, BackgroundTasks
import asyncio
import uuid

# In-memory dictionary to track batch operations (works for single-instance/local)
# In a distributed multi-instance deployment, this would use Redis or Postgres.
_BATCH_TASKS = {}

async def _process_batch_drafts(task_id: str, candidate_ids: list, context: str, contact_type: str):
    """Background task to generate drafts sequentially without blocking."""
    _BATCH_TASKS[task_id] = {
        "status": "running", 
        "completed": 0, 
        "total": len(candidate_ids), 
        "successful": 0, 
        "failed": 0, 
        "results": []
    }
    
    for cid in candidate_ids:
        try:
            # We call the existing generate_draft function directly
            result = await generate_draft(candidate_id=cid, context=context, contact_type=contact_type)
            if result:
                _BATCH_TASKS[task_id]["successful"] += 1
                _BATCH_TASKS[task_id]["results"].append({"candidate_id": cid, "status": "success", "data": result})
            else:
                _BATCH_TASKS[task_id]["failed"] += 1
                _BATCH_TASKS[task_id]["results"].append({"candidate_id": cid, "status": "error", "error": "No result returned"})
        except Exception as e:
            logger.error(f"Batch generation error for candidate {cid}: {e}")
            _BATCH_TASKS[task_id]["failed"] += 1
            _BATCH_TASKS[task_id]["results"].append({"candidate_id": cid, "status": "error", "error": str(e)})
            
        _BATCH_TASKS[task_id]["completed"] += 1
        
        # Yield to event loop to prevent blocking other API requests
        await asyncio.sleep(0.1)
        
    _BATCH_TASKS[task_id]["status"] = "completed"

@router.post("/generate-batch")
async def generate_drafts_batch(body: dict, background_tasks: BackgroundTasks):
    """Start a background task for batch draft generation."""
    candidate_ids = body.get("candidate_ids", [])
    context = body.get("context", "")
    contact_type = body.get("contact_type", "auto")
    
    if not candidate_ids:
        raise HTTPException(status_code=400, detail="No candidate IDs provided")
        
    task_id = f"batch-draft-{uuid.uuid4()}"
    
    # Add the processing function to FastAPI's built-in BackgroundTasks
    background_tasks.add_task(_process_batch_drafts, task_id, candidate_ids, context, contact_type)
    
    return {"status": "running", "message": "Batch draft generation started", "task_id": task_id}

@router.get("/batch/{task_id}/status")
async def get_batch_status(task_id: str):
    """Check the status of a background batch draft workflow."""
    task_info = _BATCH_TASKS.get(task_id)
    
    if not task_info:
        return {"status": "error", "message": "Task not found or expired"}
        
    return task_info

@router.post("/edits")
async def save_draft_edit(edit: DraftEditCreate):
    """Save user manual edits for RAG feedback loop."""
    try:
        sb_client = get_supabase()
        
        data = {
            "candidate_id": edit.candidate_id,
            "original_text": edit.original_text,
            "edited_text": edit.edited_text,
            "contact_type": edit.contact_type
        }
        
        result = sb_client.table("draft_edits").insert(data).execute()
        return {"status": "success", "message": "Draft edit saved for RAG feedback"}
    except Exception as e:
        logger.error(f"Error saving draft edit: {e}")
        raise HTTPException(status_code=500, detail=str(e))
