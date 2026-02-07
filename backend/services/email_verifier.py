"""
Email Verification Service

Integrates with Hunter.io Email Verifier API to check if an email is deliverable.
Falls back to basic MX record check if no API key is provided.
"""

import os
import re
import socket
import asyncio
from typing import Dict, Optional
import httpx
from dotenv import load_dotenv
import logging

logger = logging.getLogger("backend")

load_dotenv()

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")

class EmailVerifier:
    """
    Verifies email deliverability using Hunter.io API or fallback MX check.
    """
    
    def __init__(self):
        self.api_key = HUNTER_API_KEY
        self.cache = {}  # Simple in-memory cache
    
    async def verify(self, email: str) -> Dict:
        """
        Verify an email address.
        
        Returns:
            {
                "email": "john@example.com",
                "status": "valid" | "invalid" | "risky" | "unknown",
                "score": 0-100,
                "reason": "Explanation",
                "source": "hunter" | "mx_check"
            }
        """
        if not email or not self._is_valid_format(email):
            return {
                "email": email,
                "status": "invalid",
                "score": 0,
                "reason": "Invalid email format",
                "source": "format_check"
            }
        
        # Check cache
        if email in self.cache:
            return self.cache[email]
        
        # Try Hunter.io first
        if self.api_key:
            result = await self._verify_with_hunter(email)
            if result:
                self.cache[email] = result
                return result
        
        # Fallback to MX check
        result = await self._verify_with_mx(email)
        self.cache[email] = result
        return result
    
    def _is_valid_format(self, email: str) -> bool:
        """Basic email format validation."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    async def _verify_with_hunter(self, email: str) -> Optional[Dict]:
        """
        Verify using Hunter.io API.
        Docs: https://hunter.io/api-documentation/v2#email-verifier
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.hunter.io/v2/email-verifier",
                    params={
                        "email": email,
                        "api_key": self.api_key
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json().get("data", {})
                    
                    # Map Hunter.io result to our format
                    result_map = {
                        "deliverable": "valid",
                        "undeliverable": "invalid",
                        "risky": "risky",
                        "unknown": "unknown"
                    }
                    
                    return {
                        "email": email,
                        "status": result_map.get(data.get("result"), "unknown"),
                        "score": data.get("score", 0),
                        "reason": data.get("status", "Verified via Hunter.io"),
                        "source": "hunter",
                        "details": {
                            "mx_records": data.get("mx_records", False),
                            "smtp_check": data.get("smtp_check", False),
                            "disposable": data.get("disposable", False),
                            "webmail": data.get("webmail", False),
                        }
                    }
                elif response.status_code == 401:
                    logger.warning("[WARN] Hunter.io API key invalid")
                    return None
                elif response.status_code == 429:
                    logger.warning("[WARN] Hunter.io rate limit reached")
                    return None
                else:
                    logger.warning(f"[WARN] Hunter.io error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"[ERR] Hunter.io request failed: {e}")
            return None
    
    async def _verify_with_mx(self, email: str) -> Dict:
        """
        Fallback: Check if domain has valid MX records.
        This doesn't verify the mailbox, just that the domain can receive email.
        """
        try:
            domain = email.split("@")[1]
            
            # Run DNS lookup in thread pool
            def _check_mx(domain):
                import dns.resolver
                try:
                    answers = dns.resolver.resolve(domain, 'MX')
                    return len(list(answers)) > 0
                except:
                    return False
            
            # Try simple socket approach first (no external lib needed)
            try:
                socket.gethostbyname(f"mail.{domain}")
                has_mx = True
            except socket.gaierror:
                try:
                    socket.gethostbyname(domain)
                    has_mx = True  # Domain exists at least
                except:
                    has_mx = False
            
            if has_mx:
                return {
                    "email": email,
                    "status": "risky",  # MX exists but mailbox unverified
                    "score": 50,
                    "reason": "Domain has MX records, mailbox unverified",
                    "source": "mx_check"
                }
            else:
                return {
                    "email": email,
                    "status": "invalid",
                    "score": 0,
                    "reason": "Domain has no MX records",
                    "source": "mx_check"
                }
                
        except Exception as e:
            return {
                "email": email,
                "status": "unknown",
                "score": 25,
                "reason": f"Verification failed: {str(e)}",
                "source": "mx_check"
            }


# Convenience function
async def verify_email(email: str) -> Dict:
    """Quick verification of a single email."""
    verifier = EmailVerifier()
    return await verifier.verify(email)


# Batch verification
async def verify_emails_batch(emails: list, concurrency: int = 5) -> list:
    """Verify multiple emails with concurrency limit."""
    verifier = EmailVerifier()
    semaphore = asyncio.Semaphore(concurrency)
    
    async def _verify_one(email):
        async with semaphore:
            return await verifier.verify(email)
    
    tasks = [_verify_one(email) for email in emails]
    return await asyncio.gather(*tasks)
