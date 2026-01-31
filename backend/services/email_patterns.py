import re
from typing import Optional

class EmailPatterns:
    """
    Centralized email pattern matching and cleaning.
    """

    # Strict regex to avoid capturing file extensions or junk
    # Must contain @, domain, and valid TLD.
    EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Extensions often mistaken for emails in code/html
    IMAGE_EXTENSIONS = {
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp', '.webp', 
        '.css', '.js', '.woff', '.woff2', '.ttf', '.mp4'
    }

    # Domains to strictly ignore
    IGNORE_DOMAINS = {
        'example.com', 'email.com', 'domain.com', 'yoursite.com', 
        'test.com', 'sentry.io', 'ingest.sentry.io', 
        'noreply', 'do-not-reply', 'notifications'
    }

    @classmethod
    def extract(cls, text: str) -> Optional[str]:
        """
        Extracts the first valid email from text.
        Handles obfuscation (at) -> @.
        Filters junk.
        """
        if not text:
            return None

        # 1. De-obfuscate
        clean_text = cls._deobfuscate(text)

        # 2. Regex Search
        matches = re.findall(cls.EMAIL_REGEX, clean_text)
        
        for email in matches:
            if cls._is_clean(email):
                return email
        
        return None

    @classmethod
    def _deobfuscate(cls, text: str) -> str:
        """
        Converts common obfuscation patterns to standard email format.
        """
        text = text.lower()
        replacements = [
            ("[at]", "@"), ("(at)", "@"), (" at ", "@"),
            ("[dot]", "."), ("(dot)", "."), (" dot ", ".")
        ]
        for old, new in replacements:
            text = text.replace(old, new)
        return text

    @classmethod
    def _is_clean(cls, email: str) -> bool:
        """
        Validates email against junk lists.
        """
        domain = email.split('@')[-1]
        
        # Check extensions
        if any(email.endswith(ext) for ext in cls.IMAGE_EXTENSIONS):
            # Exception: some real domains end in .io, but usually not like `image.png`
            if not email.endswith('.io'): 
                return False
        
        # Check ignored domains
        if any(ign in domain for ign in cls.IGNORE_DOMAINS):
            return False
            
        # Check generic false positives
        if "rate" in email or "width" in email or "height" in email: # CSS properties often captured
            return False

        return True
