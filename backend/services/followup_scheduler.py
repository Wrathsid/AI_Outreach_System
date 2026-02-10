"""
Follow-up Scheduler Service

Handles:
1. Scheduling follow-up emails for candidates who haven't replied
2. Generating AI follow-up content (shorter, references first email)
3. Processing scheduled follow-ups (background job)
"""

import os
import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger("backend")

load_dotenv()

from backend.config import generate_with_gemini
from .embeddings import embeddings_service
from .throttle import throttle_service
import re

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
        
        # [Phase 3] Asymmetric Scheduling with Jitter
        # We don't want to send at the exact same time every day
        
        start_hour, end_hour = throttle_service.SAFE_HOURS
        
        for i, days in enumerate(DEFAULT_FOLLOW_UP_DAYS, start=1):
            # 1. Base Logic
            base_time = initial_sent_at + timedelta(days=days)
            
            # 2. Add Jitter (-4 hours to +6 hours) to look human
            # This ensures we don't send at exactly 9:00 AM every time
            jitter_hours = random.uniform(-4.0, 6.0)
            scheduled_for = base_time + timedelta(hours=jitter_hours)
            
            # 3. Enforce Safe Hours (9 AM - 6 PM)
            # If outside window, move to next valid window
            if scheduled_for.hour < start_hour:
                # Too early? Move to start_hour + random offset
                scheduled_for = scheduled_for.replace(hour=start_hour, minute=0) + timedelta(minutes=random.randint(5, 45))
            elif scheduled_for.hour >= end_hour:
                # Too late? Move to tomorrow morning
                scheduled_for = scheduled_for.replace(hour=start_hour, minute=0) + timedelta(days=1, minutes=random.randint(5, 45))
                
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
        Generate follow-up email content using AI with humanness scoring (Phase 3).
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
        7. Use natural paragraph breaks for human-like rhythm.
        
        Format:
        Subject: [Short subject line]
        [Body]
        """
        
        try:
            # Generate 3 variants and score them
            variants = []
            for i in range(3):
                temp = 0.4 + (i * 0.1)
                content = await generate_with_gemini(
                    prompt,
                    system_prompt="You write concise, human-like follow-up emails. Avoid corporate buzzwords.",
                    temperature=temp
                )
                if content:
                    score = self._score_follow_up(content)
                    variants.append({"content": content, "score": score})
            
            if variants:
                # Pick best variant
                best = max(variants, key=lambda x: x["score"])["content"]
                
                # Parse
                lines = best.strip().split('\n')
                subject = f"Re: {original_subject}"
                body = best
                
                for i, line in enumerate(lines):
                    if line.lower().startswith("subject:"):
                        subject = line.replace("Subject:", "").strip()
                        body = "\n".join(lines[i+1:]).strip()
                        break
                
                return {"subject": subject, "body": body}
            else:
                return self._get_template_follow_up(candidate_name, original_subject, follow_up_number, user_name)
            
        except Exception as e:
            logger.error(f"AI Error in Follow-up Generation: {e}")
            return self._get_template_follow_up(candidate_name, original_subject, follow_up_number, user_name)

    def _score_follow_up(self, text: str) -> float:
        """Heuristic scoring for follow-ups (Simplified Phase 2/3 Guards)."""
        score = 100.0
        
        # 1. Length - shorter is better for follow-ups
        word_count = len(text.split())
        if word_count > 60:
            score -= 20
        elif 20 <= word_count <= 40:
            score += 15
            
        # 2. Banned AI phrases
        banned = ["hope this finds you well", "i understand you're busy", "just checking in"]
        for b in banned:
            if b in text.lower():
                score -= 30
                
        # 3. Asymmetry Check
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if len(paragraphs) >= 2:
            len1 = len(paragraphs[0])
            len2 = len(paragraphs[1])
            ratio = max(len1, len2) / max(min(len1, len2), 1)
            if ratio < 1.15: # Too symmetrical
                score -= 20
            elif 1.5 <= ratio <= 3.0: # Good variance
                score += 10
                
        return score
    
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
    
    # Global Throttle Check (Safe Hours & Daily Limits)
    status = throttle_service.is_safe_to_send(supabase_client, channel="email")
    if not status["allowed"]:
        logger.warning(f"[Follow-ups] Throttled: {status.get('reason')}. Retrying later.")
        return

    for followup in pending:
        # Human Jitter (Wait before processing each)
        await throttle_service.wait_for_human_delay()

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
