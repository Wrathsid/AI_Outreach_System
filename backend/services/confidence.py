from typing import Dict, List

class ConfidenceScorer:
    """
    Calculates a confidence score (0.0 - 1.0) for a lead based on multiple signals.
    """

    @staticmethod
    def score(lead: Dict) -> Dict:
        """
        Enriches the lead dictionary with 'confidence' and 'signals'.
        """
        score = 0.0
        signals = []

        # 1. Email Verification (The biggest factor)
        if lead.get('email'):
            score += 0.4
            signals.append("has_email")
            
            # If strictly verified (checked via SMTP/DNS in previous step)
            # We assume if it passed the verifier at all, it's good, but let's check metadata if available
            # For now, just presence of validated email is huge.
        
        # 2. Source Credibility
        url = lead.get('linkedin_url', '').lower() # defaulting key for url
        if "github.com" in url:
            score += 0.2
            signals.append("source_github")
        elif "linkedin.com/in" in url:
            score += 0.3
            signals.append("source_linkedin_profile")
        elif "stackoverflow.com" in url:
            score += 0.2
            signals.append("source_stackoverflow")
        elif "lever.co" in url or "greenhouse.io" in url:
            score += 0.25
            signals.append("source_ats")
            
        # 3. Role/Context Match
        hr_score = lead.get('hr_score', 0)
        if hr_score > 0:
            score += hr_score * 0.2 # Explicit HR/Recruiter role
            signals.append("role_match")
            
        # 4. Content Signals
        summary = lead.get('summary', '').lower()
        if "hiring" in summary or "looking for" in summary:
            score += 0.1
            signals.append("intent_hiring")
            
        # Cap at 1.0 (or 0.99)
        final_score = min(score, 0.99)
        
        # Round for display
        lead['confidence'] = round(final_score, 2)
        lead['signals'] = signals
        
        return lead
