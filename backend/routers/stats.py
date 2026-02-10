"""
Stats router - Dashboard statistics and analytics.
"""
from fastapi import APIRouter
from typing import List
from datetime import datetime, timedelta
from collections import Counter

from backend.config import get_supabase, logger
from backend.models.schemas import DashboardStats, ActivityLog
from backend.services.throttle import throttle_service

router = APIRouter(tags=["Stats"])


@router.get("", response_model=DashboardStats)
def get_stats():
    """Get dashboard stats including recent leads and top industries."""
    supabase = get_supabase()
    if supabase:
        try:
            # Get candidate count
            candidates = supabase.table("candidates").select("id", count="exact").execute()
            people_found = candidates.count if candidates.count else 0
            
            # Get sent emails count
            emails = supabase.table("sent_emails").select("id", count="exact").execute()
            emails_sent = emails.count if emails.count else 0
            
            # Calculate weekly goal (assuming goal is 10 emails/week)
            weekly_goal = min(100, int((emails_sent / 10) * 100))

            # Recent Leads (Last 7 Days)
            recent_leads = []
            try:
                seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
                res = supabase.table("candidates").select("created_at").gte("created_at", seven_days_ago).execute()
                dates = [c['created_at'].split('T')[0] for c in res.data]
                date_counts = Counter(dates)
                
                for i in range(6, -1, -1):
                    d = (datetime.now() - timedelta(days=i)).date().isoformat()
                    recent_leads.append({
                        "date": d,
                        "count": date_counts.get(d, 0)
                    })
            except Exception as e:
                logger.error(f"Stats Aggregation Error (Recent): {e}")

            # Top Roles/Industries
            top_industries = []
            try:
                res = supabase.table("candidates").select("title").limit(500).execute()
                titles = [c['title'] for c in res.data if c.get('title')]
                title_counts = Counter(titles).most_common(5)
                top_industries = [{"name": t[0], "value": t[1]} for t in title_counts]
            except Exception as e:
                logger.error(f"Stats Aggregation Error (Industries): {e}")

            return {
                "weekly_goal_percent": weekly_goal,
                "people_found": people_found,
                "emails_sent": emails_sent,
                "replies_received": 0,
                "recent_leads": recent_leads,
                "top_industries": top_industries
            }
        except Exception as e:
            logger.error(f"Stats Error: {e}")
            return {
                "weekly_goal_percent": 0,
                "people_found": 0,
                "emails_sent": 0,
                "replies_received": 0
            }
    
    return {
        "weekly_goal_percent": 0,
        "people_found": 0,
        "emails_sent": 0,
        "replies_received": 0,
        "recent_leads": [],
        "top_industries": []
    }


@router.get("/funnel")
async def get_funnel_stats():
    """Get funnel conversion metrics: Found → Contacted → Replied."""
    supabase = get_supabase()
    if not supabase:
        return {"error": "Database not configured"}
    
    all_candidates = supabase.table("candidates").select("id, status, sent_at, reply_at, meeting_booked_at").execute()
    candidates = all_candidates.data if all_candidates.data else []
    
    total = len(candidates)
    contacted = sum(1 for c in candidates if c.get("status") in ["contacted", "replied"])
    replied = sum(1 for c in candidates if c.get("status") == "replied")
    
    def safe_percent(num, denom):
        return round((num / denom) * 100, 1) if denom > 0 else 0
    
    return {
        "funnel": [
            {"stage": "Found", "count": total, "percent": 100},
            {"stage": "Contacted", "count": contacted, "percent": safe_percent(contacted, total)},
            {"stage": "Replied", "count": replied, "percent": safe_percent(replied, total)}
        ],
        "conversions": {
            "found_to_contacted": safe_percent(contacted, total),
            "contacted_to_replied": safe_percent(replied, contacted)
        },
        "total_candidates": total
    }


@router.get("/activity", response_model=List[ActivityLog])
def get_activity():
    """Get recent activity logs."""
    supabase = get_supabase()
    if supabase:
        result = supabase.table("activity_log").select("*").order("created_at", desc=True).limit(10).execute()
        return result.data
    return []
