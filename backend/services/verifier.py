import re
import socket
import smtplib
import dns.resolver
import time
import random
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger("backend")

class TripleVerifier:
    """
    Performs deep verification of emails:
    1. Syntax & Disposable Domain Check
    2. DNS MX Record Check
    3. SMTP Handshake (RCPT TO check)
    """

    def __init__(self):
        self.disposable_domains = {
            "tempmail.com", "throwawaymail.com", "mailinator.com", "guerrillamail.com", 
            "yopmail.com", "10minutemail.com", "sharklasers.com"
        }
        self.smtp_timeout = 8 # seconds
        self.sender_email = "verify@check.com" # Should ideally be a real domain/email

    def verify(self, email: str) -> bool:
        """
        Run the triple verification pipeline.
        Returns True if email is likely valid (or unverifiable but safe).
        Returns False if definitely invalid.
        """
        # Level 1: Syntax
        if not self._check_syntax(email):
            logger.info(f"[Verify] Syntax/Junk failed: {email}")
            return False

        domain = email.split('@')[1]

        # Level 2: DNS MX
        mx_record = self._get_mx_record(domain)
        if not mx_record:
            logger.info(f"[Verify] MX failed: {domain}")
            return False

        # Level 3: SMTP Handshake
        # Note: Some servers block this or give false positives (Catch-all).
        # We try to be strict but safe.
        is_valid_smtp = self._check_smtp(mx_record, email)
        if not is_valid_smtp:
            logger.info(f"[Verify] SMTP failed: {email}")
            return False

        return True

    def _check_syntax(self, email: str) -> bool:
        if not email or "@" not in email: return False
        
        # 1. Regex
        match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email)
        if not match: return False

        domain = email.split('@')[1].lower()
        
        # 2. Disposable Check
        if domain in self.disposable_domains: return False
        
        # 3. Example/Junk Check
        junk_indicators = ["example.com", "email.com", "test.com", "yourdomain.com", "site.com"]
        if any(j in domain for j in junk_indicators): return False
        
        # 4. Image check (captured in scanner already, but good safety net)
        if any(email.endswith(ext) for ext in ['.png', '.jpg', '.gif']): return False

        return True

    def _get_mx_record(self, domain: str) -> Optional[str]:
        try:
            records = dns.resolver.resolve(domain, 'MX')
            sorted_records = sorted(records, key=lambda r: r.preference)
            return str(sorted_records[0].exchange).rstrip('.')
        except Exception:
            # Fallback to A record? usually if no MX, no mail
            return None

    def _check_smtp(self, mx_host: str, email: str) -> bool:
        try:
            # Random delay before connecting
            time.sleep(random.uniform(0.1, 0.5))

            server = smtplib.SMTP(timeout=self.smtp_timeout)
            server.set_debuglevel(0)
            
            # 1. Connect
            code, msg = server.connect(mx_host)
            if code not in [220, 250]:  # 220 Service ready
                return False # Server won't talk to us

            # 2. HELO/EHLO
            server.helo("gmail.com") # Identify as a common domain (mimicry) or own domain
            
            # 3. MAIL FROM
            code, msg = server.mail(self.sender_email)
            if code != 250:
                server.quit()
                return True # Server accepted connection but blocked checking. Assume safe.

            # 4. RCPT TO
            code, msg = server.rcpt(email)
            server.quit()

            # Codes:
            # 250: OK (User exists)
            # 550: User unknown (User does not exist) -> STRIKE!
            # 553, 450, 451: Temporary/Policy blocks -> Assume safe to avoid false negatives?
            # User wants "0 false positives" -> If uncertain, assume FALSE? Or TRUE?
            # "0 false positives" means: If I say it's valid, it MUST be valid.
            # So if uncertain/blocked, I should probably return False or categorize as "Unverified".
            # For this strict request: Only 250 OK is True.
            
            if code == 250:
                return True
            else:
                return False

        except Exception as e:
            # Network issue or timeout
            logger.error(f"SMTP Ex: {e}")
            return False # Conservative: If we can't Verify, it's not "Verified".

# Singleton
verifier = TripleVerifier()
def verify_email_deep(email: str) -> bool:
    return verifier.verify(email)
