"""
Cold Emailing Backend - FastAPI Application
Main entry point with router registration.
"""
import logging
from fastapi import FastAPI, Request, Depends

logger = logging.getLogger("backend")
from fastapi.responses import JSONResponse
from time import time
from collections import defaultdict
from typing import Dict

from backend.config import setup_cors
from backend.routers import candidates, drafts, discovery, emails, stats, settings
from backend.dependencies import get_current_user

# ============================================================
# RATE LIMITING (Priority 6)
# ============================================================
# Simple in-memory rate limiter (upgrade to Redis for multi-instance)
rate_limit_storage: Dict[str, list] = defaultdict(list)

async def rate_limit_middleware(request: Request, call_next):
    """Rate limit sensitive endpoints (AI generation, discovery)."""
    # WebSockets are handled differently, skip HTTP middleware
    if request.scope["type"] == "websocket":
        return await call_next(request)
        
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
    title="Intelligent Outreach Backend",
    description="API for intelligent outreach with AI-powered discovery and drafting",
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

# Include routers with Dependencies where Auth is required
app.include_router(candidates.router, prefix="/candidates", tags=["Candidates"], dependencies=[Depends(get_current_user)])
app.include_router(drafts.router, prefix="/drafts", tags=["Drafts"], dependencies=[Depends(get_current_user)])
app.include_router(discovery.router, prefix="/discover", tags=["Discovery"])
app.include_router(emails.router, prefix="/emails", tags=["Emails"], dependencies=[Depends(get_current_user)])
app.include_router(stats.router, prefix="/stats", tags=["Stats"], dependencies=[Depends(get_current_user)])
app.include_router(settings.router, prefix="/settings", tags=["Settings"], dependencies=[Depends(get_current_user)])



if __name__ == "__main__":
    import uvicorn
    import os
    # Read port from environment variable for cloud deployment
    port = int(os.getenv("PORT", 8000))
    # 0.0.0.0 allows containers and cloud platforms to reach the server
    host = os.getenv("HOST", "0.0.0.0")
    is_prod = os.getenv("ENV") == "production"
    print(f"Starting server on {host}:{port}")
    uvicorn.run("backend.main:app", host=host, port=port, reload=not is_prod)
