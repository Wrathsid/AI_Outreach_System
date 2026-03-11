"""
Stats router - Dashboard statistics and analytics.
"""

from fastapi import APIRouter
from datetime import datetime, timedelta
from collections import Counter

from backend.config import get_supabase, logger
from backend.models.schemas import DashboardStats
from backend.services.throttle import throttle_service

router = APIRouter(tags=["Stats"])


@router.get("", response_model=DashboardStats)
def get_stats():
    """Get dashboard stats including recent leads and top industries."""
    supabase = get_supabase()
    if supabase:
        try:
            # Get candidate count
            candidates = (
                supabase.table("candidates").select("id", count="exact").execute()
            )
            people_found = candidates.count if candidates.count else 0

            # Get contacted count
            contacted = (
                supabase.table("candidates")
                .select("id", count="exact")
                .eq("status", "contacted")
                .execute()
            )
            emails_sent = contacted.count if contacted.count else 0

            # Calculate weekly goal (assuming goal is 10 emails/week)
            weekly_goal = min(100, int((emails_sent / 10) * 100))

            # Recent Leads (Last 7 Days)
            recent_leads = []
            try:
                seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
                res = (
                    supabase.table("candidates")
                    .select("created_at")
                    .gte("created_at", seven_days_ago)
                    .execute()
                )
                dates = [c["created_at"].split("T")[0] for c in res.data]
                date_counts = Counter(dates)

                for i in range(6, -1, -1):
                    d = (datetime.now() - timedelta(days=i)).date().isoformat()
                    recent_leads.append({"date": d, "count": date_counts.get(d, 0)})
            except Exception as e:
                logger.error(f"Stats Aggregation Error (Recent): {e}")

            # Top Roles/Industries
            top_industries = []
            try:
                import re

                def clean_title(t: str) -> str:
                    # Remove prefixes like "Name on LinkedIn:" or "Name's Post:"
                    t = re.sub(
                        r"^.*?\bon linkedin\b[:\-]*", "", t, flags=re.IGNORECASE
                    ).strip()
                    t = re.sub(
                        r"^.*?\'s post\b[:\-]*", "", t, flags=re.IGNORECASE
                    ).strip()

                    # Remove hashtags and ellipsis
                    t = (
                        re.sub(r"#\w+", "", t)
                        .replace("\u2026", "")
                        .replace("...", "")
                        .strip()
                    )

                    # Split by common delimiters to isolate the role
                    t = re.split(r"\s*[|\-]\s*|\s+at\s+|\s+in\s+", t, maxsplit=1)[
                        0
                    ].strip()

                    # Group non-roles or junk into 'Other'
                    t_lower = t.lower()
                    if (
                        not t
                        or len(t) < 2
                        or "hiring" in t_lower
                        or "post" in t_lower
                        or "like" in t_lower
                        or "comment" in t_lower
                        or "recruiter" in t_lower
                        or "recruiting" in t_lower
                    ):
                        return "Other"

                    if len(t) > 25:
                        t = t[:22] + "..."
                    return t.title()

                res = (
                    supabase.table("candidates")
                    .select("title, tags")
                    .limit(500)
                    .execute()
                )

                roles = []
                for c in res.data:
                    tags = c.get("tags")
                    # Prioritize the explicitly searched role stored in tags by the frontend
                    if tags and isinstance(tags, list) and len(tags) > 0:
                        roles.append(str(tags[0]).title())
                    else:
                        title = c.get("title")
                        if title:
                            roles.append(clean_title(title))

                role_counts = Counter(roles).most_common(5)
                top_industries = [{"name": t[0], "value": t[1]} for t in role_counts]
            except Exception as e:
                logger.error(f"Stats Aggregation Error (Industries): {e}")

            # Get account health and safety status
            safety_status = throttle_service.is_safe_to_send(supabase)

            return {
                "weekly_goal_percent": weekly_goal,
                "people_found": people_found,
                "emails_sent": emails_sent,
                "replies_received": 0,
                "account_health": safety_status.get("health_score", 100),
                "is_safe": safety_status.get("allowed", True),
                "safety_reason": safety_status.get("reason"),
                "recent_leads": recent_leads,
                "top_industries": top_industries,
            }
        except Exception as e:
            logger.error(f"Stats Error: {e}")
            return {
                "weekly_goal_percent": 0,
                "people_found": 0,
                "emails_sent": 0,
                "replies_received": 0,
            }

    return {
        "weekly_goal_percent": 0,
        "people_found": 0,
        "emails_sent": 0,
        "replies_received": 0,
        "recent_leads": [],
        "top_industries": [],
    }
