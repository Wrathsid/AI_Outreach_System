"""
Emails router - Email sending, guessing, and verification.
"""

from fastapi import APIRouter, HTTPException
import re as regex

from backend.config import get_supabase
from backend.models.schemas import (
    EmailGuessRequest,
    EmailVerifyRequest,
    EmailVerifyBatchRequest,
)
from backend.services.email_generator import EmailGenerator
from backend.services.email_verifier import verify_email, verify_emails_batch

router = APIRouter(tags=["Emails"])


# ==================== EMAIL GUESSING ====================


@router.post("/guess")
async def guess_email_patterns(request: EmailGuessRequest):
    """Generate likely email addresses for a person based on name and company."""
    domain = request.domain
    if not domain and request.company:
        company_clean = request.company.lower().strip()
        company_clean = regex.sub(
            r"\s+(inc\.?|llc\.?|ltd\.?|corp\.?|co\.?)$",
            "",
            company_clean,
            flags=regex.IGNORECASE,
        )
        company_clean = regex.sub(r"[^a-z0-9]", "", company_clean)
        domain = f"{company_clean}.com"

    if not domain:
        return {
            "error": "Could not determine domain. Please provide company or domain."
        }

    guesses = EmailGenerator.generate_patterns(request.name, domain)
    return {
        "name": request.name,
        "company": request.company,
        "domain": domain,
        "guesses": guesses,
    }


@router.post("/candidate/{candidate_id}/guess")
async def guess_candidate_email(candidate_id: int):
    """Guess email for a specific candidate and save the best guess."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    result = (
        supabase.table("candidates")
        .select("*")
        .eq("id", candidate_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate = result.data

    guesses = EmailGenerator.generate_patterns(
        name=candidate.get("name", ""), company=candidate.get("company", "")
    )

    best_guess = guesses[0]["email"] if guesses else None

    if best_guess:
        supabase.table("candidates").update(
            {"email": best_guess, "email_source": "guessed"}
        ).eq("id", candidate_id).execute()

    return {
        "candidate_id": candidate_id,
        "name": candidate.get("name"),
        "company": candidate.get("company"),
        "guesses": guesses,
        "saved_email": best_guess,
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
        "results": results,
    }


@router.post("/candidate/{candidate_id}/verify")
async def verify_candidate_email(candidate_id: int):
    """Verify the email of a specific candidate."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    result = (
        supabase.table("candidates")
        .select("email")
        .eq("id", candidate_id)
        .single()
        .execute()
    )
    if not result.data or not result.data.get("email"):
        raise HTTPException(status_code=404, detail="Candidate has no email")

    email = result.data["email"]
    verification = await verify_email(email)

    supabase.table("candidates").update(
        {
            "email_verified": verification.get("status") == "valid",
            "email_verification_status": verification.get("status"),
        }
    ).eq("id", candidate_id).execute()

    return {"candidate_id": candidate_id, "email": email, "verification": verification}
