"""
Cold Emailing Backend - FastAPI Application
Main entry point with router registration.
"""
from fastapi import FastAPI

from config import setup_cors
from routers import candidates, drafts, discovery, emails, stats, settings, auth, followups

# Initialize FastAPI app
app = FastAPI(
    title="Cold Emailing Backend",
    description="API for cold emailing automation with AI-powered drafting",
    version="2.0.0"
)

# Setup CORS
setup_cors(app)

# Health check endpoint
@app.get("/", tags=["Health"])
def read_root():
    """Health check and system status."""
    from config import get_supabase, GROQ_API_KEY
    return {
        "status": "System Optimal",
        "supabase": "connected" if get_supabase() else "not configured",
        "groq": "connected" if GROQ_API_KEY else "not configured"
    }

# Register routers
app.include_router(candidates.router, prefix="/candidates", tags=["Candidates"])
app.include_router(drafts.router, prefix="/drafts", tags=["Drafts"])
app.include_router(discovery.router, prefix="/discover", tags=["Discovery"])
app.include_router(emails.router, prefix="/emails", tags=["Emails"])
app.include_router(stats.router, prefix="/stats", tags=["Stats"])
app.include_router(settings.router, prefix="/settings", tags=["Settings"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(followups.router, prefix="/followups", tags=["Follow-ups"])

# Legacy endpoints (for backwards compatibility)
# These redirect to the new router paths
@app.get("/activity")
def get_activity_legacy():
    """Legacy: Get activity (redirects to /stats/activity)."""
    return stats.get_activity()

@app.post("/send-email")
def send_email_legacy(request):
    """Legacy: Send email (use /emails/send-legacy instead)."""
    from models.schemas import SendEmailRequest
    return emails.send_email_legacy(request)

@app.post("/generate-draft")
async def generate_draft_legacy(candidate_id: int, context: str = ""):
    """Legacy: Generate draft (use /drafts/generate/{id} instead)."""
    return await drafts.generate_draft(candidate_id, context)

@app.post("/polish-draft")
async def polish_draft_legacy(request: dict):
    """Legacy: Polish draft (use /drafts/polish instead)."""
    return await drafts.polish_draft(request)

@app.get("/drafts")
def get_drafts_legacy():
    """Legacy: Get drafts (use /drafts instead)."""
    return drafts.get_all_drafts()

@app.post("/extract-opportunity")
def extract_legacy(request):
    """Legacy: Extract opportunity (use /discover/extract-opportunity)."""
    from models.schemas import ExtractionRequest
    return discovery.extract_opportunity(request)

@app.get("/discovery/hr-search")
async def hr_search_legacy(role: str = "Recruiter", company: str = "", broad_mode: bool = False):
    """Legacy: HR search (use /discover/hr-search)."""
    return await discovery.discovery_hr_search(role, company, broad_mode)

@app.get("/discover-stream")
def discover_stream_legacy(role: str):
    """Legacy: Discover stream (use /discover/stream)."""
    return discovery.discover_candidates_stream(role)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
