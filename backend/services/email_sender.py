"""
Email Sender Service

Integrates with SendGrid API to send actual emails.
Can be swapped with other providers (Mailgun, AWS SES, etc.)
"""

import os
import asyncio
from typing import Dict, Optional, List
from datetime import datetime
import httpx
from dotenv import load_dotenv

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@example.com")
FROM_NAME = os.getenv("FROM_NAME", "Cold Outreach")

class EmailSender:
    """
    Sends emails via SendGrid API.
    """
    
    def __init__(self):
        self.api_key = SENDGRID_API_KEY
        self.from_email = FROM_EMAIL
        self.from_name = FROM_NAME
        self.base_url = "https://api.sendgrid.com/v3"
    
    async def send(
        self, 
        to_email: str, 
        subject: str, 
        body: str,
        reply_to: Optional[str] = None,
        track_opens: bool = True,
        track_clicks: bool = True
    ) -> Dict:
        """
        Send a single email.
        
        Returns:
            {
                "success": True/False,
                "message_id": "...",
                "error": "..." (if failed)
            }
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "SendGrid API key not configured. Add SENDGRID_API_KEY to .env"
            }
        
        if not to_email:
            return {
                "success": False,
                "error": "Recipient email is required"
            }
        
        # Build SendGrid payload
        payload = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject
                }
            ],
            "from": {
                "email": self.from_email,
                "name": self.from_name
            },
            "content": [
                {
                    "type": "text/plain",
                    "value": body
                },
                {
                    "type": "text/html",
                    "value": self._text_to_html(body)
                }
            ],
            "tracking_settings": {
                "open_tracking": {"enable": track_opens},
                "click_tracking": {"enable": track_clicks}
            }
        }
        
        if reply_to:
            payload["reply_to"] = {"email": reply_to}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/mail/send",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code in [200, 201, 202]:
                    # SendGrid returns message ID in header
                    message_id = response.headers.get("X-Message-Id", "")
                    return {
                        "success": True,
                        "message_id": message_id,
                        "status_code": response.status_code
                    }
                else:
                    error_body = response.text
                    return {
                        "success": False,
                        "error": f"SendGrid API error: {response.status_code} - {error_body}",
                        "status_code": response.status_code
                    }
                    
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Request timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to send: {str(e)}"
            }
    
    def _text_to_html(self, text: str) -> str:
        """Convert plain text to simple HTML."""
        # Escape HTML
        import html
        escaped = html.escape(text)
        # Convert newlines to <br>
        html_body = escaped.replace("\n", "<br>\n")
        return f"<html><body style='font-family: Arial, sans-serif; line-height: 1.6;'>{html_body}</body></html>"
    
    async def send_batch(
        self, 
        emails: List[Dict],
        delay_between: float = 0.5
    ) -> List[Dict]:
        """
        Send multiple emails with rate limiting.
        
        Args:
            emails: List of dicts with 'to', 'subject', 'body' keys
            delay_between: Seconds between each send (for rate limiting)
        
        Returns:
            List of results for each email
        """
        results = []
        
        for email in emails:
            result = await self.send(
                to_email=email.get("to"),
                subject=email.get("subject"),
                body=email.get("body"),
                reply_to=email.get("reply_to")
            )
            result["to"] = email.get("to")
            results.append(result)
            
            if delay_between > 0:
                await asyncio.sleep(delay_between)
        
        return results


# --- Mock Sender for Testing ---

class MockEmailSender:
    """
    Mock email sender for testing without actually sending emails.
    """
    
    def __init__(self):
        self.sent_emails = []
    
    async def send(
        self, 
        to_email: str, 
        subject: str, 
        body: str,
        **kwargs
    ) -> Dict:
        self.sent_emails.append({
            "to": to_email,
            "subject": subject,
            "body": body,
            "sent_at": datetime.now().isoformat(),
            **kwargs
        })
        
        return {
            "success": True,
            "message_id": f"mock-{len(self.sent_emails)}",
            "mock": True
        }


# Convenience functions
async def send_email(to: str, subject: str, body: str, use_mock: bool = False) -> Dict:
    """Quick send of a single email."""
    if use_mock:
        sender = MockEmailSender()
    else:
        sender = EmailSender()
    return await sender.send(to, subject, body)


def get_sender() -> EmailSender:
    """Get configured email sender."""
    return EmailSender()
