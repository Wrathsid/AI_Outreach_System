"""
Cold Emailing Backend - FastAPI Application
Main entry point with router registration.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from time import time
from collections import defaultdict
from typing import Dict

from backend.config import setup_cors
from backend.routers import candidates, drafts, discovery, emails, stats, settings, auth, followups

# ============================================================
# RATE LIMITING (Priority 6)
# ============================================================
# Simple in-memory rate limiter (upgrade to Redis for multi-instance)
rate_limit_storage: Dict[str, list] = defaultdict(list)

async def rate_limit_middleware(request: Request, call_next):
    """Rate limit sensitive endpoints (AI generation, discovery)."""
    path = request.url.path
    
    # Only rate-limit specific endpoints
    if not any(path.startswith(p) for p in ["/drafts/generate", "/discover/search", "/emails/verify"]):
        return await call_next(request)
    
    # Get client identifier (IP address)
    client_ip = request.client.host if request.client else "unknown"
    
    # Rate limit: 10 requests per minute per IP
    current_time = time()
    window = 60  # 1 minute window
    max_requests = 10
    
    # Clean old entries
    rate_limit_storage[client_ip] = [
        timestamp for timestamp in rate_limit_storage[client_ip]
        if current_time - timestamp < window
    ]
    
    # Check if limit exceeded
    if len(rate_limit_storage[client_ip]) >= max_requests:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again in a minute."}
        )
    
    # Record this request
    rate_limit_storage[client_ip].append(current_time)
    
    return await call_next(request)

# Initialize FastAPI app
app = FastAPI(
    title="Cold Emailing Backend",
    description="API for cold emailing automation with AI-powered drafting",
    version="2.0.0"
)

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Setup CORS
setup_cors(app)

# Health check endpoint
@app.get("/", tags=["Health"])
def read_root():
    """Health check and system status."""
    from backend.config import get_supabase
    return {
        "status": "System Optimal",
        "supabase": "connected" if get_supabase() else "not configured"
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
