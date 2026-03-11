"""
Email Pattern Generator
Generates probable email addresses using common patterns when real email isn't available.
"""

import re
from typing import List, Dict, Optional


class EmailGenerator:
    """Generate probable email patterns based on name and company."""

    # Common email patterns (ordered by likelihood)
    PATTERNS = [
        "{first}.{last}@{domain}",
        "{first}{last}@{domain}",
        "{first}@{domain}",
        "{first_initial}{last}@{domain}",
        "{first}{last_initial}@{domain}",
        "{last}.{first}@{domain}",
        "{first_initial}.{last}@{domain}",
    ]

    # Common company domain patterns
    COMPANY_SUFFIXES = [".com", ".io", ".ai", ".co", ".net"]

    @staticmethod
    def clean_name(name: str) -> Dict[str, str]:
        """Extract first and last name components."""
        # Remove titles, suffixes, special characters
        name = re.sub(
            r"\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|III|II|IV)\b\.?", "", name, flags=re.IGNORECASE
        )
        name = re.sub(
            r"\(.*?\)", "", name
        )  # Remove content in parentheses (e.g. pronouns)
        name = re.sub(r"[^\w\s-]", "", name).strip()

        parts = name.split()
        if len(parts) >= 2:
            first = parts[0].lower()
            last = parts[-1].lower()
        elif len(parts) == 1:
            first = parts[0].lower()
            last = ""
        else:
            first = "contact"
            last = ""

        return {
            "first": first,
            "last": last,
            "first_initial": first[0] if first else "",
            "last_initial": last[0] if last else "",
        }

    @staticmethod
    def guess_domain(company: str) -> Optional[str]:
        """Guess company email domain from company name."""
        if not company or company.lower() in ["unknown", "n/a", ""]:
            return None

        # Clean company name
        company = company.lower()
        company = re.sub(
            r"\b(inc|llc|ltd|corp|corporation|company|co)\b\.?",
            "",
            company,
            flags=re.IGNORECASE,
        )
        company = re.sub(r"[^\w\s-]", "", company).strip()
        company = company.replace(" ", "")

        # If already looks like a domain, use it
        if "." in company:
            return company

        # Try common suffixes
        return f"{company}.com"

    @classmethod
    def generate_patterns(
        cls, name: str, company: str, limit: int = 3
    ) -> List[Dict[str, str]]:
        """
        Generate probable email patterns.

        Returns list of dicts with:
        - email: generated email
        - confidence: 0-100 score
        - pattern: pattern name
        """
        domain = cls.guess_domain(company)
        if not domain:
            return []

        name_parts = cls.clean_name(name)
        results = []

        for i, pattern in enumerate(cls.PATTERNS[:limit]):
            try:
                email = pattern.format(
                    first=name_parts["first"],
                    last=name_parts["last"],
                    first_initial=name_parts["first_initial"],
                    last_initial=name_parts["last_initial"],
                    domain=domain,
                )

                # Calculate confidence (most common patterns = higher confidence)
                confidence = max(30, 100 - (i * 20))

                results.append(
                    {
                        "email": email,
                        "confidence": confidence,
                        "pattern": pattern,
                        "is_generated": True,
                    }
                )
            except (KeyError, IndexError):
                continue

        return results

    @classmethod
    def get_best_guess(cls, name: str, company: str) -> Optional[Dict[str, str]]:
        """Get single best email guess."""
        patterns = cls.generate_patterns(name, company, limit=1)
        return patterns[0] if patterns else None
