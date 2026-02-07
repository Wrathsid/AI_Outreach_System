"""
Follow-up Scheduler Service

Handles:
1. Scheduling follow-up emails for candidates who haven't replied
2. Generating AI follow-up content (shorter, references first email)
3. Processing scheduled follow-ups (background job)
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger("backend")

load_dotenv()

from backend.config import generate_with_gemini

# Follow-up timing configuration
DEFAULT_FOLLOW_UP_DAYS = [3, 7, 14]  # Days after initial email to send follow-ups

class FollowUpScheduler:
    """
    Manages follow-up email scheduling and generation.
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    async def schedule_follow_ups(self, candidate_id: int, initial_sent_at: datetime = None) -> List[Dict]:
        """
        Schedule follow-up emails for a candidate.
        
        Args:
            candidate_id: The candidate to schedule follow-ups for
            initial_sent_at: When the first email was sent (defaults to now)
        
        Returns:
            List of scheduled follow-ups
        """
        if initial_sent_at is None:
            initial_sent_at = datetime.now()
        
        scheduled = []
        
        for i, days in enumerate(DEFAULT_FOLLOW_UP_DAYS, start=1):
            scheduled_for = initial_sent_at + timedelta(days=days)
            
            # Insert into follow_ups table
            result = self.supabase.table("follow_ups").insert({
                "candidate_id": candidate_id,
                "follow_up_number": i,
                "scheduled_for": scheduled_for.isoformat(),
                "status": "pending"
            }).execute()
            
            if result.data:
                scheduled.append(result.data[0])
        
        return scheduled
    
    async def check_and_cancel_if_replied(self, candidate_id: int) -> bool:
        """
        Check if candidate has replied. If so, cancel pending follow-ups.
        
        Returns:
            True if follow-ups were cancelled
        """
        # Check candidate status
        candidate = self.supabase.table("candidates").select("status, reply_at").eq("id", candidate_id).single().execute()
        
        if candidate.data and candidate.data.get("status") == "replied":
            # Cancel all pending follow-ups
            self.supabase.table("follow_ups").update({
                "status": "cancelled"
            }).eq("candidate_id", candidate_id).eq("status", "pending").execute()
            return True
        
        return False
    
    async def get_pending_follow_ups(self) -> List[Dict]:
        """
        Get all follow-ups that are due to be sent (scheduled_for <= now).
        """
        now = datetime.now().isoformat()
        
        result = self.supabase.table("follow_ups")\
            .select("*, candidates(name, email, title, company)")\
            .eq("status", "pending")\
            .lte("scheduled_for", now)\
            .order("scheduled_for")\
            .execute()
        
        return result.data if result.data else []
    
    async def generate_follow_up_content(
        self, 
        candidate_name: str,
        candidate_company: str,
        original_subject: str,
        follow_up_number: int,
        user_name: str = "Siddharth"
    ) -> Dict:
        """
        Generate follow-up email content using AI.
        
        Returns:
            {"subject": "...", "body": "..."}
        """
        tone_map = {
            1: "friendly reminder",
            2: "gentle nudge",
            3: "final follow-up"
        }
        tone = tone_map.get(follow_up_number, "follow-up")
        
        prompt = f"""
        Write a {tone} email to {candidate_name} at {candidate_company}.
        
        This is follow-up #{follow_up_number} to our previous email with subject: "{original_subject}"
        
        Rules:
        1. Keep it under 50 words
        2. Reference the previous email briefly
        3. {"Ask if now is a better time" if follow_up_number == 1 else ""}
        4. {"Offer to close the loop if they're not interested" if follow_up_number >= 2 else ""}
        5. {"This is the final follow-up, be respectful of their time" if follow_up_number >= 3 else ""}
        6. Sign off as {user_name}
        
        Format:
        Subject: [Short subject line]
        [Body]
        """
        
        try:
            content = await generate_with_gemini(
                prompt,
                system_prompt="You write concise follow-up emails."
            )
            
            if content:
                # Parse
                lines = content.strip().split('\n')
                subject = f"Re: {original_subject}"
                body = content
                
                for i, line in enumerate(lines):
                    if line.lower().startswith("subject:"):
                        subject = line.replace("Subject:", "").strip()
                        body = "\n".join(lines[i+1:]).strip()
                        break
                
                return {"subject": subject, "body": body}
            else:
                return self._get_template_follow_up(candidate_name, original_subject, follow_up_number, user_name)
            
        except Exception as e:
            logger.error(f"AI Error: {e}")
            return self._get_template_follow_up(candidate_name, original_subject, follow_up_number, user_name)
    
    def _get_template_follow_up(
        self, 
        name: str, 
        original_subject: str, 
        follow_up_number: int,
        user_name: str
    ) -> Dict:
        """Fallback template-based follow-ups."""
        
        templates = {
            1: {
                "subject": f"Re: {original_subject}",
                "body": f"Hi {name},\n\nJust wanted to bump this to the top of your inbox. Let me know if now is a better time to chat.\n\nBest,\n{user_name}"
            },
            2: {
                "subject": f"Quick follow-up: {original_subject}",
                "body": f"Hi {name},\n\nI know things get busy. If you're interested, I'd love to find 15 minutes. If not, no worries at all - just let me know and I'll close the loop.\n\nCheers,\n{user_name}"
            },
            3: {
                "subject": f"Final note: {original_subject}",
                "body": f"Hi {name},\n\nThis will be my last follow-up. If timing isn't right, I completely understand. Feel free to reach out whenever makes sense.\n\nAll the best,\n{user_name}"
            }
        }
        
        return templates.get(follow_up_number, templates[1])
    
    async def mark_sent(self, follow_up_id: int) -> None:
        """Mark a follow-up as sent."""
        self.supabase.table("follow_ups").update({
            "status": "sent",
            "sent_at": datetime.now().isoformat()
        }).eq("id", follow_up_id).execute()


# --- Background Job Runner ---

async def process_pending_follow_ups(supabase_client, email_sender):
    """
    Background job to process and send pending follow-ups.
    Should be called periodically (e.g., every hour).
    """
    scheduler = FollowUpScheduler(supabase_client)
    
    pending = await scheduler.get_pending_follow_ups()
    logger.info(f"[Follow-ups] Found {len(pending)} pending follow-ups")
    
    for followup in pending:
        candidate = followup.get("candidates", {})
        candidate_id = followup["candidate_id"]
        
        # Check if they replied
        was_cancelled = await scheduler.check_and_cancel_if_replied(candidate_id)
        if was_cancelled:
            logger.info(f"  [Cancelled] {candidate.get('name')} replied - skipping")
            continue
        
        # Skip if no email
        email = candidate.get("email")
        if not email:
            logger.info(f"  [Skipped] {candidate.get('name')} - no email")
            continue
        
        # Get original email subject
        original_draft = supabase_client.table("drafts")\
            .select("subject")\
            .eq("candidate_id", candidate_id)\
            .order("created_at")\
            .limit(1)\
            .execute()
        
        original_subject = "Our conversation"
        if original_draft.data:
            original_subject = original_draft.data[0].get("subject", original_subject)
        
        # Generate content
        content = await scheduler.generate_follow_up_content(
            candidate_name=candidate.get("name", "there"),
            candidate_company=candidate.get("company", "your company"),
            original_subject=original_subject,
            follow_up_number=followup["follow_up_number"]
        )
        
        # Send
        result = await email_sender.send(
            to_email=email,
            subject=content["subject"],
            body=content["body"]
        )
        
        if result.get("success"):
            await scheduler.mark_sent(followup["id"])
            logger.info(f"  [Sent] Follow-up #{followup['follow_up_number']} to {candidate.get('name')}")
        else:
            logger.error(f"  [Failed] {candidate.get('name')}: {result.get('error')}")
