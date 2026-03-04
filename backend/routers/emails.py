"""
Emails router - Email sending, guessing, and verification.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import re as regex

from backend.config import get_supabase
import hashlib
from backend.models.schemas import (
    SendEmailRequest, SendEmailDirectRequest, 
    EmailGuessRequest, EmailVerifyRequest, EmailVerifyBatchRequest
)
from backend.services.email_generator import EmailGenerator
from backend.services.email_verifier import verify_email, verify_emails_batch
from backend.services.email_sender import EmailSender
from backend.services.embeddings import embeddings_service
from backend.services.throttle import throttle_service
import asyncio

router = APIRouter(tags=["Emails"])


# ==================== EMAIL GUESSING ====================

@router.post("/guess")
async def guess_email_patterns(request: EmailGuessRequest):
    """Generate likely email addresses for a person based on name and company."""
    domain = request.domain
    if not domain and request.company:
        company_clean = request.company.lower().strip()
        company_clean = regex.sub(r'\s+(inc\.?|llc\.?|ltd\.?|corp\.?|co\.?)$', '', company_clean, flags=regex.IGNORECASE)
        company_clean = regex.sub(r'[^a-z0-9]', '', company_clean)
        domain = f"{company_clean}.com"
    
    if not domain:
        return {"error": "Could not determine domain. Please provide company or domain."}
    
    guesses = EmailGenerator.generate_patterns(request.name, domain)
    return {
        "name": request.name,
        "company": request.company,
        "domain": domain,
        "guesses": guesses
    }


@router.post("/candidate/{candidate_id}/guess")
async def guess_candidate_email(candidate_id: int):
    """Guess email for a specific candidate and save the best guess."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    result = supabase.table("candidates").select("*").eq("id", candidate_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    candidate = result.data
    
    guesses = EmailGenerator.generate_patterns(
        name=candidate.get("name", ""),
        company=candidate.get("company", "")
    )
    
    best_guess = guesses[0]["email"] if guesses else None
    
    if best_guess:
        supabase.table("candidates").update({
            "email": best_guess,
            "email_source": "guessed"
        }).eq("id", candidate_id).execute()
    
    return {
        "candidate_id": candidate_id,
        "name": candidate.get("name"),
        "company": candidate.get("company"),
        "guesses": guesses,
        "saved_email": best_guess
    }


# ==================== EMAIL VERIFICATION ====================

@router.post("/verify")
async def verify_single_email(request: EmailVerifyRequest):
    """Verify a single email address for deliverability."""
    result = await verify_email(request.email)
    return result


@router.post("/verify-batch")
async def verify_multiple_emails(request: EmailVerifyBatchRequest):
    """Verify multiple email addresses (max 25 at a time)."""
    if len(request.emails) > 25:
        raise HTTPException(status_code=400, detail="Maximum 25 emails per batch")
    
    results = await verify_emails_batch(request.emails)
    valid_count = sum(1 for r in results if r.get("status") == "valid")
    invalid_count = sum(1 for r in results if r.get("status") == "invalid")
    
    return {
        "total": len(results),
        "valid": valid_count,
        "invalid": invalid_count,
        "results": results
    }


@router.post("/candidate/{candidate_id}/verify")
async def verify_candidate_email(candidate_id: int):
    """Verify the email of a specific candidate."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    result = supabase.table("candidates").select("email").eq("id", candidate_id).single().execute()
    if not result.data or not result.data.get("email"):
        raise HTTPException(status_code=404, detail="Candidate has no email")
    
    email = result.data["email"]
    verification = await verify_email(email)
    
    supabase.table("candidates").update({
        "email_verified": verification.get("status") == "valid",
        "email_verification_status": verification.get("status")
    }).eq("id", candidate_id).execute()
    
    return {
        "candidate_id": candidate_id,
        "email": email,
        "verification": verification
    }


# ==================== EMAIL SENDING ====================

@router.post("/send")
async def send_email_direct(request: SendEmailDirectRequest):
    """Send an email directly via SendGrid."""
    sender = EmailSender()
    result = await sender.send(
        to_email=request.to_email,
        subject=request.subject,
        body=request.body,
        reply_to=request.reply_to
    )
    return result





@router.post("/draft/{draft_id}/send")
async def send_draft(draft_id: int):
    """Send a draft email to the candidate."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    draft_result = supabase.table("drafts").select("*, candidates(*)").eq("id", draft_id).single().execute()
    if not draft_result.data:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    draft = draft_result.data
    candidate = draft.get("candidates", {})
    
    to_email = candidate.get("email")
    if not to_email:
        raise HTTPException(status_code=400, detail="Candidate has no email address")
    
    # Phase 3: Adaptive Throttle Check
    throttle = throttle_service.is_safe_to_send(supabase, channel="email")
    if not throttle["allowed"]:
        raise HTTPException(status_code=429, detail=throttle["reason"])

    # Human-like delay
    await asyncio.sleep(throttle_service.get_random_delay())
    
    sender = EmailSender()
    result = await sender.send(
        to_email=to_email,
        subject=draft.get("subject"),
        body=draft.get("body")
    )
    
    if result.get("success"):
        supabase.table("drafts").update({"status": "sent"}).eq("id", draft_id).execute()
        supabase.table("candidates").update({
            "status": "contacted",
            "sent_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", candidate.get("id")).execute()
        
        supabase.table("activity_log").insert({
            "action_type": "email_sent",
            "title": f"Email sent to {candidate.get('name')}",
            "description": f"Subject: {draft.get('subject')}",
            "candidate_id": candidate.get("id")
        }).execute()

        # Record opener in sent_openers for Anti-Repetition Memory (Optimization 13)
        try:
            body = draft.get("body", "")
            first_line = body.split('\n')[0].strip()
            if "," in first_line and len(first_line.split(',')[0]) < 20: 
                parts = first_line.split(',', 1)
                if len(parts) > 1:
                    opener = parts[1].strip()
                else:
                    opener = first_line
            else:
                opener = first_line
            
            if opener:
                opener_hash = hashlib.md5(opener.lower().encode()).hexdigest()
                embedding = embeddings_service.generate_embedding(opener)
                supabase.table("sent_openers").insert({
                    "opener_hash": opener_hash,
                    "embedding": embedding
                }).execute()
        except Exception as e:
            from backend.config import logger
            logger.error(f"Failed to record opener memory in send_draft: {e}")
    
    return {
        "draft_id": draft_id,
        "to": to_email,
        "result": result
    }


@router.get("/sent")
def get_sent_emails():
    """Get all sent emails."""
    supabase = get_supabase()
    if supabase:
        result = supabase.table("sent_emails").select("*").order("sent_at", desc=True).execute()
        return {"emails": result.data}
    return {"emails": []}
