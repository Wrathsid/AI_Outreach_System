"""
Candidates router - CRUD operations for lead management.
"""

from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timedelta, timezone

from backend.config import get_supabase, logger
from backend.models.schemas import Candidate, CandidateCreate, BulkAddRequest

router = APIRouter(tags=["Candidates"])


def get_candidate_by_id(candidate_id: int):
    """Helper to get candidate dict by ID (internal use)."""
    supabase = get_supabase()
    if supabase:
        result = (
            supabase.table("candidates")
            .select("*")
            .eq("id", candidate_id)
            .single()
            .execute()
        )
        if result.data:
            return result.data
    return None


# ============================================================
# STATIC ROUTES (must come BEFORE /{candidate_id})
# ============================================================


@router.post("/bulk-add")
def bulk_add_to_pipeline(request: BulkAddRequest):
    """Mark multiple candidates as added to pipeline (UX Improvement)."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        # Optimize: Single query update using .in_() filter
        supabase.table("candidates").update({"status": "new"}).in_(
            "id", request.candidate_ids
        ).execute()

        logger.info(f"Bulk added {len(request.candidate_ids)} candidates to pipeline")
        return {"status": "success", "count": len(request.candidate_ids)}
    except Exception as e:
        logger.error(f"Bulk add failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sent")
def get_sent_candidates():
    """Get all candidates who have been sent messages (UX Improvement)."""
    supabase = get_supabase()
    if not supabase:
        return []

    try:
        result = (
            supabase.table("candidates")
            .select("*")
            .not_.is_("sent_at", "null")
            .order("sent_at", desc=True)
            .limit(500)
            .execute()
        )
        return result.data
    except Exception as e:
        logger.error(f"Get sent failed: {e}")
        return []


@router.delete("/prune")
def prune_candidates(days: int = 7):
    """Delete candidates older than X days."""
    supabase = get_supabase()
    if supabase:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        supabase.table("candidates").delete().lt("created_at", cutoff).execute()
        return {
            "status": "success",
            "message": f"Pruned candidates older than {days} days",
        }
    return {"status": "error", "message": "Database not connected"}


@router.delete("/all/delete")
def delete_all_candidates():
    """Delete ALL candidates (Dangerous Operation)."""
    supabase = get_supabase()
    if supabase:
        # Delete all records
        try:
            supabase.table("candidates").delete().neq("id", 0).execute()
            logger.warning("Deleted ALL candidates via API")
            return {"status": "success", "message": "All candidates deleted"}
        except Exception as e:
            logger.error(f"Delete all failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    raise HTTPException(status_code=500, detail="Database not connected")


# ============================================================
# LIST ENDPOINT
# ============================================================


@router.get("", response_model=List[Candidate])
def get_all_candidates():
    """Get all candidates ordered by creation date."""
    supabase = get_supabase()
    if supabase:
        result = (
            supabase.table("candidates")
            .select("*")
            .order("created_at", desc=True)
            .limit(500)
            .execute()
        )
        return result.data
    return []


@router.post("", response_model=Candidate)
def create_candidate(candidate: CandidateCreate):
    """Create a new candidate. If candidate exists (duplicate email/linkedin), return existing."""
    supabase = get_supabase()
    if supabase:
        # 1. Sanitize input (treat empty strings as None)
        if not candidate.email:
            candidate.email = None
        if not candidate.linkedin_url:
            candidate.linkedin_url = None

        # Truncate string fields to prevent DB varchar(500) constraint errors
        if candidate.title and len(candidate.title) > 500:
            candidate.title = candidate.title[:497] + "..."
        if candidate.company and len(candidate.company) > 500:
            candidate.company = candidate.company[:497] + "..."
        if candidate.location and len(candidate.location) > 500:
            candidate.location = candidate.location[:497] + "..."
        if candidate.summary and len(candidate.summary) > 500:
            candidate.summary = candidate.summary[:497] + "..."
        if candidate.linkedin_url and len(candidate.linkedin_url) > 500:
            candidate.linkedin_url = candidate.linkedin_url[:500]
        if candidate.avatar_url and len(candidate.avatar_url) > 500:
            candidate.avatar_url = candidate.avatar_url[:500]

        # 2. Check for duplicates first to avoid errors
        if candidate.email:
            existing = (
                supabase.table("candidates")
                .select("*")
                .eq("email", candidate.email)
                .execute()
            )
            if existing.data and len(existing.data) > 0:
                logger.info(f"Skipping duplicate candidate (email): {candidate.email}")
                return existing.data[0]

        if candidate.linkedin_url:
            existing_li = (
                supabase.table("candidates")
                .select("*")
                .eq("linkedin_url", candidate.linkedin_url)
                .execute()
            )
            if existing_li.data and len(existing_li.data) > 0:
                logger.info(
                    f"Skipping duplicate candidate (linkedin): {candidate.linkedin_url}"
                )
                return existing_li.data[0]

        # 2. Proceed with creation if no duplicate found
        candidate_data = candidate.model_dump()

        score = candidate_data.get("match_score", 0)

        # Only recalculate if the frontend didn't pass a valid score
        if score <= 0:
            try:
                # Calculate resonance score (0-100)
                from backend.services.recommendation import recommendation_service

                score = recommendation_service.calculate_resonance_score(candidate_data)
                logger.info(f"Calculated Resonance Score: {score}")
            except Exception as e:
                logger.error(f"Resonance scoring failed: {e}")
                score = 0

            candidate_data["match_score"] = score

        try:
            result = supabase.table("candidates").insert(candidate_data).execute()
            if result.data:
                supabase.table("activity_log").insert(
                    {
                        "candidate_id": result.data[0]["id"],
                        "action_type": "lead_found",
                        "title": f"Added {candidate.name}",
                        "description": f"Match Score: {score}% • {candidate.company or 'Unknown Company'}",
                    }
                ).execute()
                logger.info(f"Successfully created candidate: {candidate.name}")
                return result.data[0]
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            raise HTTPException(
                status_code=400, detail=f"Failed to create candidate: {str(e)}"
            )

    raise HTTPException(status_code=500, detail="Database connection failed")


# ============================================================
# DYNAMIC ROUTES (/{candidate_id} pattern — must come LAST)
# ============================================================


@router.get("/{candidate_id}", response_model=Candidate)
def get_candidate(candidate_id: int):
    """Get a single candidate by ID."""
    supabase = get_supabase()
    if supabase:
        result = (
            supabase.table("candidates")
            .select("*")
            .eq("id", candidate_id)
            .single()
            .execute()
        )
        if result.data:
            data = result.data
            # Compute email_source
            data["email_source"] = (
                "verified"
                if data.get("email")
                else ("generated" if data.get("generated_email") else "none")
            )
            return data
    raise HTTPException(status_code=404, detail="Candidate not found")


@router.put("/{candidate_id}", response_model=Candidate)
def update_candidate(candidate_id: int, candidate: CandidateCreate):
    """Update an existing candidate."""
    supabase = get_supabase()
    if supabase:
        result = (
            supabase.table("candidates")
            .update(candidate.model_dump())
            .eq("id", candidate_id)
            .execute()
        )
        if result.data:
            return result.data[0]
    raise HTTPException(status_code=404, detail="Candidate not found")


@router.delete("/{candidate_id}")
def delete_candidate(candidate_id: int):
    """Delete a candidate."""
    supabase = get_supabase()
    if supabase:
        supabase.table("candidates").delete().eq("id", candidate_id).execute()
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Candidate not found")


VALID_STATUSES = {"new", "contacted", "snoozed", "discovered"}


@router.patch("/{candidate_id}/status")
def update_candidate_status(candidate_id: int, status: str):
    """Update candidate status (new, contacted, snoozed)."""
    if status not in VALID_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status '{status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}",
        )
    supabase = get_supabase()
    if supabase:
        result = (
            supabase.table("candidates")
            .update({"status": status})
            .eq("id", candidate_id)
            .execute()
        )
        if result.data:
            return result.data[0]
    raise HTTPException(status_code=404, detail="Candidate not found")


@router.patch("/{candidate_id}/mark-sent")
def mark_as_sent(candidate_id: int):
    """Mark candidate as sent when message is sent (UX Improvement)."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    from datetime import datetime, timezone

    try:
        result = (
            supabase.table("candidates")
            .update(
                {
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "status": "contacted",
                }
            )
            .eq("id", candidate_id)
            .execute()
        )

        if result.data:
            logger.info(f"Marked candidate {candidate_id} as sent")
            return result.data[0]
        raise HTTPException(status_code=404, detail="Candidate not found")
    except Exception as e:
        logger.error(f"Mark sent failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
