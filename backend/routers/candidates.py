"""
Candidates router - CRUD operations for lead management.
"""
from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timedelta

from config import get_supabase
from models.schemas import Candidate, CandidateCreate

router = APIRouter(tags=["Candidates"])


@router.get("", response_model=List[Candidate])
def get_all_candidates():
    """Get all candidates ordered by creation date."""
    supabase = get_supabase()
    if supabase:
        result = supabase.table("candidates").select("*").order("created_at", desc=True).execute()
        return result.data
    return []


@router.get("/{candidate_id}", response_model=Candidate)
def get_candidate(candidate_id: int):
    """Get a single candidate by ID."""
    supabase = get_supabase()
    if supabase:
        result = supabase.table("candidates").select("*").eq("id", candidate_id).single().execute()
        if result.data:
            return result.data
    raise HTTPException(status_code=404, detail="Candidate not found")


@router.post("", response_model=Candidate)
def create_candidate(candidate: CandidateCreate):
    """Create a new candidate. If candidate exists (duplicate email/linkedin), return existing."""
    supabase = get_supabase()
    if supabase:
        # 1. Check for duplicates first to avoid errors
        if candidate.email:
            existing = supabase.table("candidates").select("*").eq("email", candidate.email).execute()
            if existing.data and len(existing.data) > 0:
                print(f"Skipping duplicate candidate (email): {candidate.email}")
                return existing.data[0]

        if candidate.linkedin_url:
            existing_li = supabase.table("candidates").select("*").eq("linkedin_url", candidate.linkedin_url).execute()
            if existing_li.data and len(existing_li.data) > 0:
                print(f"Skipping duplicate candidate (linkedin): {candidate.linkedin_url}")
                return existing_li.data[0]

        # 2. Proceed with creation if no duplicate found
        # Calculate Match Score
        score = 0
        try:
            brain_res = supabase.table("brain_context").select("*").eq("id", 1).execute()
            if brain_res.data:
                brain = brain_res.data[0]
                skills = brain.get("extracted_skills", []) or []
                if skills:
                    text = (candidate.title or "") + " " + (candidate.summary or "")
                    text = text.lower()
                    matches = sum(1 for s in skills if s.lower() in text)
                    if len(skills) > 0:
                        score = int((matches / len(skills)) * 100)
                    if (candidate.title or "").lower() in text:
                        score += 10
                    score = min(max(score, 10), 95)
        except Exception as e:
            print(f"Scoring failed: {e}")
        
        candidate_data = candidate.model_dump()
        candidate_data["match_score"] = score

        try:
            result = supabase.table("candidates").insert(candidate_data).execute()
            if result.data:
                supabase.table("activity_log").insert({
                    "candidate_id": result.data[0]["id"],
                    "action_type": "lead_found",
                    "title": f"Added {candidate.name}",
                    "description": f"Match Score: {score}% • {candidate.company or 'Unknown Company'}"
                }).execute()
                print(f"Successfully created candidate: {candidate.name}")
                return result.data[0]
        except Exception as e:
            print(f"Insert failed: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to create candidate: {str(e)}")

    raise HTTPException(status_code=500, detail="Database connection failed")


@router.put("/{candidate_id}", response_model=Candidate)
def update_candidate(candidate_id: int, candidate: CandidateCreate):
    """Update an existing candidate."""
    supabase = get_supabase()
    if supabase:
        result = supabase.table("candidates").update(candidate.model_dump()).eq("id", candidate_id).execute()
        if result.data:
            return result.data[0]
    raise HTTPException(status_code=404, detail="Candidate not found")


@router.delete("/{candidate_id}")
def delete_candidate(candidate_id: int):
    """Delete a candidate."""
    supabase = get_supabase()
    if supabase:
        supabase.table("candidates").delete().eq("id", candidate_id).execute()
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Candidate not found")


@router.patch("/{candidate_id}/status")
def update_candidate_status(candidate_id: int, status: str):
    """Update candidate status (new, contacted, replied, snoozed)."""
    supabase = get_supabase()
    if supabase:
        result = supabase.table("candidates").update({"status": status}).eq("id", candidate_id).execute()
        if result.data:
            return result.data[0]
    raise HTTPException(status_code=404, detail="Candidate not found")


@router.delete("/prune")
def prune_candidates(days: int = 7):
    """Delete candidates older than X days."""
    supabase = get_supabase()
    if supabase:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        supabase.table("candidates").delete().lt("created_at", cutoff).execute()
        return {"status": "success", "message": f"Pruned candidates older than {days} days"}
    return {"status": "error", "message": "Database not connected"}
