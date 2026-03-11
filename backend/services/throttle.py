from datetime import datetime, timedelta
import random
import logging
import asyncio
from typing import Dict

logger = logging.getLogger("backend")


class ThrottleService:
    """
    Manages account safety and "human-like" throttling [Phase 3 - Adaptive].
    Tracks sender reputation via a Rolling Health Score.
    """

    # Configuration
    SAFE_HOURS = (9, 18)  # 9 AM to 6 PM
    BASE_DAILY_EMAILS = 50
    BASE_DAILY_LINKEDIN = 20

    # Adaptive State (In-Memory for speed, synced to DB ideally)
    _recent_errors = []  # List of timestamps
    _recent_bounces = []  # List of timestamps
    _last_429 = None

    @classmethod
    def record_outcome(cls, outcome: str):
        """Track result of a send attempt to adjust health score."""
        now = datetime.now()
        if outcome == "error":
            cls._recent_errors.append(now)
            # Keep last 24h only
            cls._recent_errors = [
                t for t in cls._recent_errors if t > now - timedelta(hours=24)
            ]
        elif outcome == "bounce":
            cls._recent_bounces.append(now)
            cls._recent_bounces = [
                t for t in cls._recent_bounces if t > now - timedelta(hours=24)
            ]
        elif outcome == "429":
            cls._last_429 = now
            logger.warning("Rate limit hit (429). Engaging cool-down.")

    @classmethod
    def calculate_health_score(cls) -> int:
        """Calculate Account Health Score (0-100)."""
        score = 100
        now = datetime.now()

        # Penalize recent errors (last 24h)
        # Each error = -5 points
        err_count = len(
            [t for t in cls._recent_errors if t > now - timedelta(hours=24)]
        )
        score -= err_count * 5

        # Penalize bounces (last 24h)
        # Each bounce = -10 points (High severity)
        bounce_count = len(
            [t for t in cls._recent_bounces if t > now - timedelta(hours=24)]
        )
        score -= bounce_count * 10

        # Penalize recent 429
        if cls._last_429 and cls._last_429 > now - timedelta(hours=1):
            score -= 20

        return max(0, score)

    @classmethod
    def get_dynamic_limits(cls) -> Dict[str, int]:
        """Get daily limits adjusted by health score."""
        health = cls.calculate_health_score()
        factor = 1.0

        if health < 50:
            factor = 0.0  # Shutdown
        elif health < 70:
            factor = 0.5  # Severe throttle
        elif health < 90:
            factor = 0.8  # Mild throttle

        return {
            "email": int(cls.BASE_DAILY_EMAILS * factor),
            "linkedin": int(cls.BASE_DAILY_LINKEDIN * factor),
            "health_score": health,
        }

    @classmethod
    def is_safe_to_send(cls, supabase, channel: str = "email") -> Dict:
        """
        Check if it's safe to send right now based on hours, limits, and health.
        """
        now = datetime.now()
        current_hour = now.hour

        # 0. Check Mandatory Cool-downs (Priority 1)
        if cls._last_429:
            # 1 hour cool-down for 429s
            if cls._last_429 > now - timedelta(hours=1):
                return {
                    "allowed": False,
                    "reason": "Cooling down from Rate Limit (429)",
                    "retry_after": "1 hour",
                }

        # 1. Check Working Hours
        if not (cls.SAFE_HOURS[0] <= current_hour < cls.SAFE_HOURS[1]):
            return {
                "allowed": False,
                "reason": f"Outside human working hours ({cls.SAFE_HOURS[0]}AM-{cls.SAFE_HOURS[1]}PM)",
                "retry_after": "tomorrow morning",
            }

        # 2. Check Account Health
        health = cls.calculate_health_score()
        if health < 50:
            return {
                "allowed": False,
                "reason": f"Account Health Critical ({health}/100). Sending Paused.",
                "retry_after": "24 hours (when errors expire)",
            }

        # 3. Check Dynamic Daily Limits
        limits = cls.get_dynamic_limits()
        daily_limit = limits.get(channel, 20)

        today = now.date().isoformat()
        try:
            res = (
                supabase.table("dashboard_stats")
                .select("*")
                .eq("stat_date", today)
                .execute()
            )
            if res.data:
                stats = res.data[0]
                sent_count = stats.get(
                    "emails_sent" if channel == "email" else "linkedin_sent", 0
                )

                if sent_count >= daily_limit:
                    msg = f"Daily {channel} limit ({daily_limit}) reached"
                    if health < 100:
                        msg += f" (Reduced due to Health {health}%)"
                    return {"allowed": False, "reason": msg, "retry_after": "tomorrow"}
        except Exception as e:
            logger.error(f"Throttle check failed: {e}")
            # Fail safe - allow if DB check fails but log it
            pass

        return {"allowed": True, "health_score": health}

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
