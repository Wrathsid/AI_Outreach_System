"""
Auth router - Gmail OAuth and authentication endpoints.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from datetime import datetime

from config import get_supabase
from models.schemas import GmailSendRequest
from services.gmail_oauth import get_gmail_service
from services.followup_scheduler import FollowUpScheduler

router = APIRouter(tags=["Authentication"])


@router.get("/google")
async def google_auth_start(user_id: int = 1):
    """Start Gmail OAuth flow. Returns the authorization URL."""
    supabase = get_supabase()
    gmail_service = get_gmail_service(supabase)
    auth_url = gmail_service.get_auth_url(user_id)
    return {"auth_url": auth_url}


@router.get("/google/callback")
async def google_auth_callback(code: str = None, state: str = None, error: str = None):
    """Handle OAuth callback from Google."""
    if error:
        return RedirectResponse(url=f"http://localhost:3001/settings?error={error}")
    
    if not code:
        return {"error": "No authorization code received"}
    
    supabase = get_supabase()
    gmail_service = get_gmail_service(supabase)
    result = await gmail_service.exchange_code(code, state)
    
    if result.get("error"):
        return RedirectResponse(url=f"http://localhost:3001/settings?error={result['error']}")
    
    return RedirectResponse(url=f"http://localhost:3001/settings?gmail_connected=true&email={result.get('email', '')}")


@router.get("/gmail/status")
async def gmail_status(user_id: int = 1):
    """Check if user has Gmail connected."""
    supabase = get_supabase()
    gmail_service = get_gmail_service(supabase)
    tokens = await gmail_service.get_user_tokens(user_id)
    
    if tokens:
        return {
            "connected": True,
            "email": tokens.get("email")
        }
    return {"connected": False}


@router.post("/gmail/send")
async def send_via_gmail(request: GmailSendRequest, user_id: int = 1):
    """Send email via user's connected Gmail account."""
    supabase = get_supabase()
    gmail_service = get_gmail_service(supabase)
    
    result = await gmail_service.send_email(
        user_id=user_id,
        to_email=request.to,
        subject=request.subject,
        body=request.body
    )
    
    if result.get("success"):
        if supabase:
            supabase.table("activity_log").insert({
                "action_type": "email_sent",
                "title": f"Email sent via Gmail",
                "description": f"To: {request.to}, Subject: {request.subject[:50]}...",
                "candidate_id": request.candidate_id
            }).execute()
            
            if request.candidate_id:
                supabase.table("candidates").update({
                    "status": "contacted",
                    "contacted_at": datetime.now().isoformat()
                }).eq("id", request.candidate_id).execute()
        
        return {
            "success": True,
            "message": "Email sent successfully via Gmail",
            "message_id": result.get("message_id"),
            "from": result.get("from")
        }
    else:
        return {
            "success": False,
            "error": result.get("error", "Failed to send email")
        }


@router.post("/gmail/send-draft/{draft_id}")
async def send_draft_via_gmail(draft_id: int, user_id: int = 1):
    """Send a specific draft using the user's connected Gmail."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    result = supabase.table("drafts").select("*").eq("id", draft_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    draft = result.data
    
    candidate = supabase.table("candidates").select("*").eq("id", draft["candidate_id"]).single().execute()
    if not candidate.data or not candidate.data.get("email"):
        raise HTTPException(status_code=400, detail="Candidate has no email address")
    
    to_email = candidate.data["email"]
    
    gmail_service = get_gmail_service(supabase)
    send_result = await gmail_service.send_email(
        user_id=user_id,
        to_email=to_email,
        subject=draft["subject"],
        body=draft["body"]
    )
    
    if send_result.get("success"):
        supabase.table("drafts").update({"status": "sent"}).eq("id", draft_id).execute()
        
        supabase.table("candidates").update({
            "status": "contacted",
            "contacted_at": datetime.now().isoformat()
        }).eq("id", draft["candidate_id"]).execute()
        
        supabase.table("activity_log").insert({
            "action_type": "email_sent",
            "title": f"Email sent to {candidate.data['name']}",
            "description": f"Subject: {draft['subject'][:50]}...",
            "candidate_id": draft["candidate_id"]
        }).execute()
        
        scheduler = FollowUpScheduler(supabase)
        await scheduler.schedule_follow_ups(draft["candidate_id"])
        
        return {
            "success": True,
            "message": "Email sent via Gmail",
            "from": send_result.get("from"),
            "to": to_email
        }
    else:
        raise HTTPException(status_code=500, detail=send_result.get("error", "Failed to send"))
