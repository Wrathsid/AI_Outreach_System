"""
Follow-ups router - Follow-up scheduling and management.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime

from backend.config import get_supabase
from backend.services.email_sender import EmailSender
from backend.services.followup_scheduler import FollowUpScheduler, process_pending_follow_ups

router = APIRouter(tags=["Follow-ups"])


@router.get("/pending")
async def get_pending_followups():
    """Get all pending follow-ups that are due."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    now = datetime.now().isoformat()
    
    result = supabase.table("follow_ups")\
        .select("*, candidates(name, email, company)")\
        .eq("status", "pending")\
        .lte("scheduled_for", now)\
        .order("scheduled_for")\
        .execute()
    
    return {
        "count": len(result.data) if result.data else 0,
        "follow_ups": result.data if result.data else []
    }


@router.post("/process")
async def process_followups():
    """Process and send all pending follow-ups. Can be called manually or by a cron job."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    sender = EmailSender()
    await process_pending_follow_ups(supabase, sender)
    
    return {"status": "completed", "message": "Follow-ups processed"}


@router.post("/schedule/{candidate_id}")
async def schedule_candidate_followups(candidate_id: int):
    """Manually schedule follow-ups for a candidate."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    scheduler = FollowUpScheduler(supabase)
    scheduled = await scheduler.schedule_follow_ups(candidate_id)
    
    return {
        "candidate_id": candidate_id,
        "scheduled_count": len(scheduled),
        "follow_ups": scheduled
    }


@router.post("/mark-replied/{candidate_id}")
async def mark_candidate_replied(candidate_id: int):
    """Mark a candidate as having replied. This will cancel pending follow-ups."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    supabase.table("candidates").update({
        "status": "replied",
        "replied_at": datetime.now().isoformat()
    }).eq("id", candidate_id).execute()
    
    scheduler = FollowUpScheduler(supabase)
    await scheduler.check_and_cancel_if_replied(candidate_id)
    
    return {"status": "updated", "message": "Candidate marked as replied, follow-ups cancelled"}
