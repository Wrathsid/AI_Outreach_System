"""
Drafts router - Draft management and AI generation.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Optional
import re
import hashlib
import uuid
import json

from backend.config import get_supabase, generate_with_gemini, logger
from backend.models.schemas import Draft, DraftCreate, IntentType

router = APIRouter(tags=["Drafts"])

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
    text = re.sub(r'[^\w\s.,!?;:()\'\"-]', '', text)
    
    return text.strip()


def get_recent_opener_hashes(supabase, limit: int = 50) -> List[str]:
    """Fetch hashes of recently sent openers to avoid repetition (Optimization 13)."""
    try:
        res = supabase.table("sent_openers").select("opener_hash").order("created_at", desc=True).limit(limit).execute()
        return [d["opener_hash"] for d in res.data]
    except Exception as e:
        logger.error(f"Memory fetch (hashes) failed: {e}")
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
    if contact_type == "linkedin":
        length = len(text)
        if 140 <= length <= 200:
            score += 20
        elif length < 120:
            score -= 10
        elif length > 250:
            score -= 15
    else:  # Email
        word_count = len(text.split())
        if 80 <= word_count <= 120:
            score += 15
        elif word_count > 150:
            score -= 20
    
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
    # MAX 1 question mark allowed
    if text.count("?") > 1:
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
    if ttr < 30:
        score += 10  # Excellent glance-ability
    elif ttr > 45:
        score -= 10  # Too long for mobile
    
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



def extract_primary_signal(candidate: dict) -> Dict[str, str]:
    """Extract ONE strong signal from candidate context.
    
    Prevents over-stuffed, unnatural personalization.
    Returns: {'signal': str, 'avoid': str}
    """
    signals = []
    
    title = candidate.get('title', '')
    company = candidate.get('company', '')
    summary = candidate.get('summary', '')
    
    # Priority 3: Hiring/recruiting focus
    if title and any(word in title.lower() for word in ['recruit', 'talent', 'hiring']):
        domain = 'technical roles' if 'tech' in title.lower() else 'hiring'
        signals.append({
            'type': 'hiring_focus',
            'value': f"Recruiter focusing on {domain}",
            'priority': 3
        })
    
    # Priority 2: Technical role
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
            'avoid': 'generic experience, achievements not mentioned, overly detailed background',
            'is_generic': False
        }
    
    return {
        'signal': f"Professional at {company}" if company else "Professional in their field",
        'avoid': 'making assumptions about their work',
        'is_generic': True
    }


async def generate_with_scoring(prompt: str, contact_type: str, candidate_context: dict, num_variants: int = 3) -> Dict:
    """Generate multiple variants and return the highest scoring one.
    
    This is the SECRET SAUCE for reply-rate optimization.
    User sees 1 draft, but we generated 3 and picked the best.
    """
    import asyncio
    
    # Generate variants with CHANNEL-SPECIFIC temperatures (Gemini Tuning)
    # LinkedIn: 0.35 - 0.45 (Strict control)
    # Email: 0.45 - 0.55 (Slight flow)
    base_temp = 0.35 if contact_type == "linkedin" else 0.45
    
    # Prepare tasks for parallel execution
    tasks = []
    
    for i in range(num_variants):
        temp = base_temp + (i * 0.05)
        
        # Use intent-based system prompt
        intent_value = candidate_context.get('intent', IntentType.CURIOUS)
        system_prompt = SYSTEM_PROMPTS.get(intent_value, SYSTEM_PROMPTS[IntentType.CURIOUS])
        
        # Create a coroutine for each generation task
        tasks.append(generate_with_gemini(prompt, temperature=temp, system_prompt=system_prompt))

    # Execute all generation tasks in parallel
    if not tasks:
        return None

    # Wait for all generations to complete
    responses = await asyncio.gather(*tasks)
    
    # Fetch recent sent hashes for deduplication
    sent_hashes = get_recent_opener_hashes(supabase)
    
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
            
            # Anti-Repetition Penalty (Optimization 13)
            if opener_hash in sent_hashes:
                logger.warning(f"Repeated opener detected (hash: {opener_hash[:8]}). Penalizing variant {i+1}.")
                score -= 80  # Heavy penalty for repetition
            
            variants.append({"text": response_text, "score": score, "temp": temp, "opener_hash": opener_hash})
            logger.info(f"Variant {i+1}: score={score:.1f}, temp={temp}, hash={opener_hash[:8]}")
    
    # Return the best one
    if variants:
        best = max(variants, key=lambda v: v["score"])
        logger.info(f"SELECTED: score={best['score']:.1f}, temp={best['temp']}")
        return best
    
    return None


# Updated system prompts with stronger tone anchors
SYSTEM_PROMPTS = {
    IntentType.CURIOUS: """
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
- ONE paragraph only.
- MAX 1 question.

STRUCTURE:
1. "Hi [Name]"
2. Observation ("Saw you're hiring for X", "Noticed your post on Y")
3. Soft question ("Curious how you're thinking about Z", "Open to a quick exchange?")

MAX: 220 chars. Write the message ONLY.
""",
    IntentType.PEER: """
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
    IntentType.SOFT: """
You are writing a soft networking message.
TONE: Warm, friendly, slightly deferential but confident.
GOAL: Get on their radar without asking for anything heavy.
NEGATIVE CONSTRAINTS (CRITICAL):
- Do NOT explain.
- Do NOT use "picked your brain" or "15 mins".

RULES:
- Genuine compliment (must be specific).
- Soft open loop ("Wondering if...")

MAX: 200 chars (LI) or 80 words (Email). Write the message ONLY.
""",
    IntentType.DIRECT: """
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
    "GENERIC": """
You are writing a generic but polite outreach.
TONE: Honest, extremely brief.
GOAL: Connect without pretending to know them deeply.
STRATEGY: Be vulnerable ("I don't know you well but...")
MAX: 150 chars. Write the message ONLY.
"""
}


@router.get("", response_model=List[Draft])
def get_all_drafts():
    """Get all drafts with candidate info."""
    supabase = get_supabase()
    if supabase:
        result = supabase.table("drafts").select("*, candidates(name, company, title, email, generated_email, email_confidence)").eq("status", "draft").order("created_at", desc=True).execute()
        drafts = []
        for d in result.data:
            draft = {
                "id": d["id"],
                "candidate_id": d["candidate_id"],
                "subject": d["subject"],
                "body": d["body"],
                "status": d["status"],
                "candidate_name": d["candidates"]["name"] if d.get("candidates") else None,
                "candidate_company": d["candidates"]["company"] if d.get("candidates") else None,
                "candidate_title": d["candidates"]["title"] if d.get("candidates") else None,
                "candidate_email": d["candidates"]["email"] if d.get("candidates") else None,
                "candidate_generated_email": d["candidates"]["generated_email"] if d.get("candidates") else None,
                "candidate_email_confidence": d["candidates"]["email_confidence"] if d.get("candidates") else None,
                "email_source": "verified" if d.get("candidates", {}).get("email") else ("generated" if d.get("candidates", {}).get("generated_email") else "none")
            }
            drafts.append(draft)
        return drafts
    return []

@router.delete("", response_model=dict)
def delete_all_drafts():
    """Delete all drafts."""
    supabase = get_supabase()
    if supabase:
        # Delete all drafts with status 'draft'
        result = supabase.table("drafts").delete().eq("status", "draft").execute()
        return {"message": "All drafts deleted successfully"}
    raise HTTPException(status_code=500, detail="Database not configured")


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


@router.patch("/{draft_id}/reply")
def track_reply(draft_id: int, status: str = "replied"):
    """Update reply status for a draft (Learning Loop)."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    if status not in ["replied", "no_reply", "bounced"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    result = supabase.table("drafts").update({"reply_status": status}).eq("id", draft_id).execute()
    if result.data:
        return {"message": f"Draft {draft_id} marked as {status}"}
    raise HTTPException(status_code=404, detail="Draft not found")


@router.post("/polish")
async def polish_draft(request: dict):
    """Fix grammar and improve tone of draft."""
    text = request.get("text", "")
    if not text:
        return {"text": ""}
    
    from backend.config import gemini_model
    
    if gemini_model:
        try:
            polished = await generate_with_gemini(
                prompt=text,
                system_prompt="You are a professional editor. Fix grammar, spelling, and improve flow. Keep the tone professional but conversational. Return ONLY the polished text. Do not add intro/outro.",
                temperature=0.4
            )
            return {"text": polished.strip() if polished else text}
        except Exception as e:
            logger.error(f"Polish error: {e}")
            return {"text": text}
    
    return {"text": text}


@router.post("/generate/{candidate_id}")
async def generate_draft(candidate_id: int, context: str = "", contact_type: str = "auto"):
    """Generate AI draft with MULTI-VARIANT SCORING (Priority 1-3 Optimizations)."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # 1. Fetch Candidate Data
        c = supabase.table("candidates").select("*").eq("id", candidate_id).single().execute().data
        if not c:
            raise HTTPException(status_code=404, detail="Candidate not found")
            
        # Auto-detect contact type
        if contact_type == "auto":
            contact_type = "email" if (c.get("email") or c.get("generated_email")) else "linkedin"

        # 2. Fetch User/Brain Context
        settings = {"full_name": "Siddharth", "company": "Antigravity", "role": "Founder"}  # Fallback
        try:
            s_data = supabase.table("user_settings").select("*").eq("id", 1).execute().data
            if s_data:
                settings = s_data[0]
            
            b_data = supabase.table("brain_context").select("*").eq("id", 1).execute().data
            brain = b_data[0] if b_data else {"extracted_skills": []}
        except Exception as e:
            logger.error(f"Context fetch error: {e}")
            brain = {"extracted_skills": []}

        skills = ", ".join(brain.get("extracted_skills", [])) or "Technical Hiring"

        # 3. CONTEXT COMPRESSION & MEMORY (Priority 2, 13)
        signal = extract_primary_signal(c)
        
        # Fetch Memory (Avoid Repetition)
        recent_openers = get_recent_openers(supabase)
        memory_constraint = ""
        if recent_openers:
            blocklist = "\\n- ".join(recent_openers)
            memory_constraint = f"\\nAvoid these recent openers:\\n- {blocklist}"
        
        logger.info(f"Primary signal: {signal['signal']} | Avoid: {signal['avoid']}")

        # 4. Build Prompt (Optimization 11, 12, 17)
        # Simplify sender intro — focus on curiosity, not credentials
        sender_intro = f"{settings['full_name']} (curious about {skills.split(',')[0].strip()})"
        
        # Determine Intent (with Surgical Override - Refinement 73)
        if contact_type == "linkedin":
            intent = IntentType.CURIOUS
        else:
            intent = IntentType.PEER
            
        # Intent Override Rules
        title_lower = c.get('title', '').lower()
        high_value_roles = ["director", "head of", "vp", "chief", "lead", "founder", "owner"]
        if any(role in title_lower for role in high_value_roles):
            intent = IntentType.CURIOUS # Always be curious with leaders
            logger.info(f"Intent Override: {c.get('title')} -> CURIOUS")

        # Context Bands (Refinement 74)
        # Simplify context for cleaner prompting
        context_band = "LOW"
        if len(brain.get("extracted_skills", [])) > 2 and c.get('title'):
            context_band = "MEDIUM"
        if signal.get('signal') and not signal.get('is_generic'):
            context_band = "HIGH"

        # Check Fallback (Optimization 12: Nothing to Say)
        if signal.get('is_generic', False) or context_band == "LOW":
            intent = "GENERIC"
            prompt = f"""
            Sender: {settings['full_name']}
            Recipient: {c['name']}
            
            Intent: GENERIC / FALLBACK
            Reason: Profile context is weak (Band: {context_band}).
            
            Write a very polite, honest generic opener. 
            Admit you found them via search/network but don't fake specific knowledge.
            Keep it under 2 sentences.
            """
        else:
            # Standard High-Context Prompt
            prompt = f"""
            Sender: {sender_intro}
            Recipient: {c['name']}, {c.get('title', 'Professional')}
            Intent: {intent.value.upper() if hasattr(intent, 'value') else str(intent).upper()}
            Context Strength: {context_band}
            
            Primary signal: {signal['signal']}
            AVOID: {signal['avoid']}
            
            Context: {context if context else "Reach out about their work"}
            
            Constraints:
            - Use modal verbs ("might", "wondering") -> Softness (Opt 14)
            - NO credentials ("As a X...") -> (Opt 17)
            - NO "I hope this finds you well"
            - End with a question OR soft curiosity -> (Opt 15 + Refinement){memory_constraint}
            """

        # 5. MULTI-VARIANT SCORING (Priority 1)
        # Reduced to 1 variant for Gemini Free Tier (Optimization 69)
        candidate_context = {
            'name': c.get('name'),
            'company': c.get('company'),
            'title': c.get('title'),
            'intent': intent
        }
        
        result = await generate_with_scoring(prompt, contact_type, candidate_context, num_variants=1)
        
        if not result:
            raise HTTPException(status_code=500, detail="AI generation failed after retries")
        
        response_text = result['text']
        score = result['score']
        
        logger.info(f"FINAL DRAFT | Score: {score:.1f} | Type: {contact_type} | Length: {len(response_text)}")

        # 6. Parse and Save
        # Compute variant ID for this generation attempt
        variant_id = str(uuid.uuid4())
        gen_params = {
            "model": "gemini-2.0-flash",
            "temperature": result.get('temp'),
            "context_band": context_band,
            "signal_type": signal['type']
        }

        if contact_type == "linkedin":
            final_msg = response_text.replace("Subject:", "").strip()
            
            # Ensure proper greeting
            first_name = c['name'].split()[0] if c.get('name') else 'there'
            if not final_msg.lower().startswith("hi"):
                final_msg = f"Hi {first_name}, " + final_msg

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
        raise
    except Exception as e:
        logger.error(f"Generate Check Failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Generation logic error: {str(e)}")
