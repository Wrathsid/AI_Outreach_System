from datetime import datetime
import random
import logging
import asyncio
from typing import Dict, Optional

logger = logging.getLogger("backend")

class ThrottleService:
    """
    Manages account safety and "human-like" throttling.
    """
    
    # Configuration
    SAFE_HOURS = (9, 18)  # 9 AM to 6 PM
    MAX_DAILY_EMAILS = 50
    MAX_DAILY_LINKEDIN = 20
    
    @classmethod
    def is_safe_to_send(cls, supabase, channel: str = "email") -> Dict:
        """
        Check if it's safe to send right now based on hours and daily limits.
        """
        now = datetime.now()
        current_hour = now.hour
        
        # 1. Check Working Hours
        if not (cls.SAFE_HOURS[0] <= current_hour < cls.SAFE_HOURS[1]):
            return {
                "allowed": False, 
                "reason": f"Outside human working hours ({cls.SAFE_HOURS[0]}AM-{cls.SAFE_HOURS[1]}PM)",
                "retry_after": "tomorrow morning"
            }
            
        # 2. Check Daily Limits
        today = now.date().isoformat()
        try:
            res = supabase.table("dashboard_stats").select("*").eq("stat_date", today).execute()
            if res.data:
                stats = res.data[0]
                sent_count = stats.get("emails_sent" if channel == "email" else "linkedin_sent", 0)
                limit = cls.MAX_DAILY_EMAILS if channel == "email" else cls.MAX_DAILY_LINKEDIN
                
                if sent_count >= limit:
                    return {
                        "allowed": False, 
                        "reason": f"Daily {channel} limit ({limit}) reached",
                        "retry_after": "tomorrow"
                    }
        except Exception as e:
            logger.error(f"Throttle check failed: {e}")
            # Fail safe - allow if DB check fails but log it
            pass
            
        return {"allowed": True}

    @classmethod
    def get_random_delay(cls) -> float:
        """Get a 'human' delay between 30 and 120 seconds for safety."""
        return random.uniform(30.0, 120.0)

    @classmethod
    async def wait_for_human_delay(cls):
        """Async sleep for a random human duration."""
        delay = cls.get_random_delay()
        logger.info(f"Human-like pause of {delay:.1f}s initiated...")
        await asyncio.sleep(delay)

throttle_service = ThrottleService()
