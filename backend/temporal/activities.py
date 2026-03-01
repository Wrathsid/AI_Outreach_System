from temporalio import activity
from typing import Dict
from datetime import timedelta
import logging

# Import existing logic instead of rewriting it!
from backend.services.email_verifier import verify_email

logger = logging.getLogger("temporal-activities")

@activity.defn
async def verify_email_activity(email: str) -> Dict:
    """
    Temporal Activity for verifying emails.
    If this function raises an exception (e.g., API timeout), 
    Temporal will automatically retry it according to the retry policy in the workflow.
    """
    logger.info(f"Running verify_email_activity for {email}")
    
    # We just call the existing function we already built!
    result = await verify_email(email)
    return result

@activity.defn
async def generate_email_pattern_activity(name: str, company: str) -> Dict:
    """
    Temporal Activity for predicting an email address based on name and company.
    """
    from backend.services.email_generator import EmailGenerator
    logger.info(f"Running generate_email_pattern_activity for {name} at {company}")
    result = EmailGenerator.get_best_guess(name, company)
    return result or {"email": None, "confidence": 0, "pattern": None, "is_generated": False}

@activity.defn
async def crawl_linkedin_activity(role: str, limit: int = 20) -> list:
    """
    Temporal Activity for crawling LinkedIn via SerpAPI.
    The original crawler uses a Python Async Generator to stream results to the UI.
    To make it durable in Temporal, we consume the stream and return a list of leads.
    """
    from backend.services.crawler import Crawler
    logger.info(f"Running crawl_linkedin_activity for role: {role} (limit: {limit})")
    crawler = Crawler()
    
    leads = []
    # Consume the async generator completely
    async for raw in crawler.crawl_stream(role, limit=limit):
        if raw["type"] == "raw_result":
            leads.append(raw["data"])
            
    return leads
