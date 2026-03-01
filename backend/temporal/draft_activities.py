from temporalio import activity
import logging

logger = logging.getLogger("temporal-draft-activities")

@activity.defn
async def generate_draft_activity(candidate_id: int, context: str = "", contact_type: str = "auto") -> dict:
    """
    Temporal Activity for generating a draft using the existing complex logic.
    """
    from backend.routers.drafts import generate_draft
    from fastapi import HTTPException
    
    logger.info(f"Running generate_draft_activity for candidate {candidate_id}")
    
    try:
        # Re-use the exact same logic designed for the API endpoint
        result = await generate_draft(candidate_id, context, contact_type)
        return {"status": "success", "data": result}
    except HTTPException as e:
        logger.error(f"Draft Generation HTTPException: {e.detail}")
        return {"status": "error", "error": str(e.detail)}
    except Exception as e:
        logger.error(f"Draft Generation Exception: {str(e)}")
        return {"status": "error", "error": str(e)}
