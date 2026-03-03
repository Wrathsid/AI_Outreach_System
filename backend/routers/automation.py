"""
Automation router - Browser automation for LinkedIn outreach.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging

from backend.config import get_supabase

try:
    from backend.services.browser_automation import launch_linkedin_message
    _HAS_PLAYWRIGHT = True
except ImportError:
    _HAS_PLAYWRIGHT = False

logger = logging.getLogger("backend.automation")

router = APIRouter(tags=["Automation"])


@router.post("/launch/{candidate_id}")
async def launch_draft_automation(candidate_id: str, background_tasks: BackgroundTasks):
    """
    Triggers the browser automation to open LinkedIn and paste the draft.
    Runs in background to prevent timeout during the 5-minute review window.
    """
    if not _HAS_PLAYWRIGHT:
        raise HTTPException(
            status_code=501,
            detail="Browser automation is not available in cloud deployment. Use locally."
        )

    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        response = supabase.table("candidates").select("*").eq("id", candidate_id).execute()
    except Exception as e:
        logger.error(f"Failed to fetch candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")

    if not response.data:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate = response.data[0]
    linkedin_url = candidate.get("linkedin_url")
    draft_message = candidate.get("draft")

    if not linkedin_url:
        raise HTTPException(status_code=400, detail="Candidate has no LinkedIn URL")

    if not draft_message:
        raise HTTPException(status_code=400, detail="Candidate has no draft message generated")

    # Launch in background so the API returns immediately.
    # The browser stays open for 5 minutes for user review.
    background_tasks.add_task(launch_linkedin_message, linkedin_url, draft_message)

    return {"status": "success", "detail": "Automation launched in background. Please check the browser window."}
