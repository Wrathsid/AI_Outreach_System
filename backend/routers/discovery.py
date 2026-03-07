"""
Discovery router - Lead discovery and search endpoints.
"""
from fastapi import APIRouter

from backend.config import logger

router = APIRouter(tags=["Discovery"])




from fastapi import Request, WebSocket, WebSocketDisconnect, Depends, Query
import asyncio

from backend.dependencies import get_current_user
from backend.services.crawler import Crawler
from backend.temporal.activities import polish_leads_activity, generate_email_pattern_activity, verify_email_activity

@router.websocket("/ws/discover")
async def websocket_discover(websocket: WebSocket, role: str = Query(...), limit: int = Query(15)):
    """Stream discovery results directly via WebSocket (Bypassing Temporal)"""
    await websocket.accept()
    try:
        await websocket.send_json({"status": "running", "message": f"Starting search for {role}..."})
        # 1. Start Crawl Stream
        crawler = Crawler()
        
        async def process_and_stream(raw_lead):
            from backend.temporal.activities import polish_single_lead
            
            # A. Polish single lead (ultra fast)
            lead = await polish_single_lead(raw_lead)
            
            # B. Email prediction & verification
            name = lead.get("name", "Unknown Candidate")
            company = lead.get("company", "Unknown")
            url = lead.get("url", "")
            
            lead["linkedin_url"] = url
            lead["result_type"] = "person"
            lead["resonance_score"] = 0.5
            lead["email_confidence"] = 0
            
            guess_result = await generate_email_pattern_activity(name, company)
            email = guess_result.get("email")
            if guess_result.get("confidence"):
                lead["email_confidence"] = guess_result.get("confidence")
                
            if email:
                verification = await verify_email_activity(email)
                lead["email"] = email
                lead["email_verification"] = verification
                if verification.get("status") == "invalid":
                    lead["email"] = None
            else:
                lead["email"] = None
            
            # C. STREAM RESULT TO WEBSOCKET IMMEDIATELY
            await websocket.send_json({"status": "lead_discovered", "lead": lead})
            return lead

        tasks = []
        
        # Stream results from SerpAPI & instantly fire processing tasks
        async for r in crawler.crawl_stream(role, limit=limit):
            if r["type"] == "raw_result":
                # Fire and forget a concurrent background task to process and stream
                task = asyncio.create_task(process_and_stream(r["data"]))
                tasks.append(task)
            elif r["type"] == "status":
                await websocket.send_json({"status": "running", "message": r["data"]})
                
        if not tasks:
            await websocket.send_json({"status": "completed", "results": []})
            return
            
        await websocket.send_json({"status": "running", "message": f"Found {len(tasks)} leads. Finalizing AI polishing and email verification..."})
        
        # Wait for all background tasks to finish processing before closing
        results = await asyncio.gather(*tasks)
        
        await websocket.send_json({"status": "completed", "results": results})
        
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"status": "error", "message": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
