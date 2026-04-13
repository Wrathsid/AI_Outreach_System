"""
Cortex Skills Engine — Dedicated router for managing the AI skills context.

Provides a clean API for:
  POST   /cortex/skills     — Save/overwrite active skills
  GET    /cortex/skills     — Retrieve current active skills
  DELETE /cortex/skills     — Clear all skills
"""

from fastapi import APIRouter, HTTPException
from typing import List

from backend.config import get_supabase, logger

router = APIRouter(tags=["Cortex"])


@router.post("/skills")
def save_skills(skills: List[str]):
    """Save active skills to the Cortex (brain_context)."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        # Upsert into brain_context row (there's only one row, id=1)
        existing = supabase.table("brain_context").select("id").limit(1).execute()

        if existing.data:
            supabase.table("brain_context").update(
                {"extracted_skills": skills}
            ).eq("id", existing.data[0]["id"]).execute()
        else:
            supabase.table("brain_context").insert(
                {"extracted_skills": skills}
            ).execute()

        logger.info(f"Cortex: saved {len(skills)} skills")
        return {"status": "saved", "count": len(skills), "skills": skills}
    except Exception as e:
        logger.error(f"Cortex save failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/skills")
def get_skills():
    """Retrieve current active skills from the Cortex."""
    supabase = get_supabase()
    if not supabase:
        return {"skills": [], "count": 0}

    try:
        result = supabase.table("brain_context").select("extracted_skills").limit(1).execute()
        skills = result.data[0].get("extracted_skills", []) if result.data else []
        return {"skills": skills, "count": len(skills)}
    except Exception as e:
        logger.error(f"Cortex get failed: {e}")
        return {"skills": [], "count": 0}


@router.delete("/skills")
def clear_skills():
    """Clear all skills from the Cortex."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        existing = supabase.table("brain_context").select("id").limit(1).execute()
        if existing.data:
            supabase.table("brain_context").update(
                {"extracted_skills": []}
            ).eq("id", existing.data[0]["id"]).execute()

        logger.info("Cortex: cleared all skills")
        return {"status": "cleared"}
    except Exception as e:
        logger.error(f"Cortex clear failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
