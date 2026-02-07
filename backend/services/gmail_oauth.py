"""
Gmail OAuth Service

Handles:
1. OAuth flow for users to connect their Gmail
2. Token storage and refresh
3. Sending emails via Gmail API
"""

import os
import json
import base64
from typing import Dict, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import httpx
import logging

logger = logging.getLogger("backend")

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

# Gmail API scopes needed
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


class GmailOAuthService:
    """
    Handles Gmail OAuth flow and email sending.
    """
    
    def __init__(self, supabase_client=None):
        self.client_id = GOOGLE_CLIENT_ID
        self.client_secret = GOOGLE_CLIENT_SECRET
        self.redirect_uri = GOOGLE_REDIRECT_URI
        self.supabase = supabase_client
    
    def get_auth_url(self, user_id: int) -> str:
        """
        Generate OAuth URL for user to authorize Gmail access.
        """
        import urllib.parse
        
        state = base64.urlsafe_b64encode(json.dumps({"user_id": user_id}).encode()).decode()
        
        # URL-encode the scope (spaces become %20)
        scope_encoded = urllib.parse.quote(" ".join(SCOPES))
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": scope_encoded,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"
    
    async def exchange_code(self, code: str, state: str) -> Dict:
        """
        Exchange authorization code for access/refresh tokens.
        """
        # Decode state to get user_id
        try:
            state_data = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
            user_id = state_data.get("user_id")
        except:
            user_id = None
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                }
            )
            
            if response.status_code != 200:
                return {"error": f"Token exchange failed: {response.text}"}
            
            tokens = response.json()
            
            # Get user's email from Google
            user_info = await self._get_user_info(tokens["access_token"])
            
            # Store tokens in database
            if self.supabase and user_id:
                self.supabase.table("user_gmail_tokens").upsert({
                    "user_id": user_id,
                    "email": user_info.get("email"),
                    "access_token": tokens["access_token"],
                    "refresh_token": tokens.get("refresh_token"),
                    "expires_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }).execute()
            
            return {
                "success": True,
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "user_id": user_id
            }
    
    async def _get_user_info(self, access_token: str) -> Dict:
        """Get user's Google profile info."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code == 200:
                return response.json()
            return {}
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh an expired access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                }
            )
            
            if response.status_code == 200:
                tokens = response.json()
                return tokens["access_token"]
            return None
    
    async def get_user_tokens(self, user_id: int) -> Optional[Dict]:
        """Get stored tokens for a user."""
        if not self.supabase:
            return None
        
        try:
            result = self.supabase.table("user_gmail_tokens")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            # Return first result if exists, else None
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting user tokens: {e}")
            return None
    
    async def send_email(
        self,
        user_id: int,
        to_email: str,
        subject: str,
        body: str,
        reply_to: Optional[str] = None
    ) -> Dict:
        """
        Send email via Gmail API using user's connected account.
        """
        # Get user's tokens
        tokens = await self.get_user_tokens(user_id)
        if not tokens:
            return {"success": False, "error": "Gmail not connected. Please connect your Gmail first."}
        
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        
        # Try to send, refresh token if needed
        result = await self._send_gmail(access_token, to_email, subject, body, tokens.get("email"))
        
        if result.get("error") == "token_expired" and refresh_token:
            # Refresh token and retry
            new_access_token = await self.refresh_access_token(refresh_token)
            if new_access_token:
                # Update stored token
                if self.supabase:
                    self.supabase.table("user_gmail_tokens").update({
                        "access_token": new_access_token,
                        "updated_at": datetime.now().isoformat()
                    }).eq("user_id", user_id).execute()
                
                result = await self._send_gmail(new_access_token, to_email, subject, body, tokens.get("email"))
        
        return result
    
    async def _send_gmail(
        self,
        access_token: str,
        to_email: str,
        subject: str,
        body: str,
        from_email: str
    ) -> Dict:
        """Actually send the email via Gmail API."""
        
        # Create MIME message
        message = MIMEMultipart("alternative")
        message["to"] = to_email
        message["from"] = from_email
        message["subject"] = subject
        
        # Plain text and HTML versions
        text_part = MIMEText(body, "plain")
        html_body = body.replace("\n", "<br>")
        html_part = MIMEText(f"<html><body style='font-family: Arial, sans-serif;'>{html_body}</body></html>", "html")
        
        message.attach(text_part)
        message.attach(html_part)
        
        # Encode for Gmail API
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={"raw": raw}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message_id": data.get("id"),
                    "from": from_email
                }
            elif response.status_code == 401:
                return {"success": False, "error": "token_expired"}
            else:
                return {
                    "success": False,
                    "error": f"Gmail API error: {response.status_code} - {response.text}"
                }


# Convenience functions
def get_gmail_service(supabase_client=None) -> GmailOAuthService:
    """Get configured Gmail service."""
    return GmailOAuthService(supabase_client)
