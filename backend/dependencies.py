from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.config import get_supabase
import logging

logger = logging.getLogger("backend.auth")
security = HTTPBearer(auto_error=False)

# ⚡ DEV BYPASS: Set to True to skip auth for local testing. Set to False in production.
DEV_BYPASS = False

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # In dev bypass mode, return a fake user so all routes work without a real token
    if DEV_BYPASS:
        return {"id": "dev-user", "email": "dev@localhost"}

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    supabase = get_supabase()
    
    if not supabase:
        logger.error("Supabase not initialized for auth.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth provider unreachable"
        )

    try:
        response = supabase.auth.get_user(token)
        if hasattr(response, 'user') and response.user:
            return response.user
        else:
            raise ValueError("No user returned")
    except Exception as e:
        logger.error(f"JWT Validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
