from temporalio import workflow
from datetime import timedelta
from typing import List, Dict

# Import activities
# We use string names here or actual function imports depending on how the worker is set up,
# but using exactly the same signature is critical.
with workflow.unsafe.imports_passed_through():
    # Activities must be imported under this block to prevent Temporal from complaining
    # about non-deterministic modules (like network calls) being imported in workflow scope.
    import backend.temporal.activities as activities

@workflow.defn
class DiscoveryWorkflow:
    """
    Temporal Workflow for the entire Lead Discovery process.
    This workflow is deterministic. It cannot make direct network calls.
    It orchestrates Activities to do the actual work.
    """

    @workflow.run
    async def run(self, role: str, limit: int = 20) -> List[Dict]:
        """
        The main entrypoint for the workflow.
        """
        workflow.logger.info(f"Starting Discovery Workflow for role: {role}")
        
        # --- STEP 1: CRAWL ---
        # Execute the crawler activity. 
        # ScheduleToCloseTimeout is required. We give the crawler 5 minutes to finish.
        leads = await workflow.execute_activity(
            activities.crawl_linkedin_activity,
            args=[role, limit],
            schedule_to_close_timeout=timedelta(minutes=5),
            # Retry Policy is completely automatic! 
            # Temporary failures (rate limits, timeouts) will just retry.
        )
        
        workflow.logger.info(f"Crawl finished. Found {len(leads)} raw leads.")
        
        if not leads:
            return []

        # --- STEP 2: PARALLEL VERIFICATION & GENERATION ---
        # Instead of doing these one by one, we can tell Temporal to execute
        # the email guessing and SMTP verification activities for ALL leads at the same time.
        
        import asyncio

        async def process_lead(lead: dict) -> dict:
            name = lead.get("title", "Unknown").split("-")[0].strip() # basic guess
            company = "Unknown" # In a full migration, we use the hr_extractor activity here
            url = lead.get("url", "")
            
            # Update lead mapping with the fields expected by frontend
            lead["name"] = name
            lead["company"] = company
            lead["linkedin_url"] = url
            lead["result_type"] = "person"
            lead["resonance_score"] = 0.5  # placeholder
            lead["email_confidence"] = 0
            lead["summary"] = lead.get("body", "")
            
            # Predict the email pattern
            guess_result = await workflow.execute_activity(
                activities.generate_email_pattern_activity,
                args=[name, company],
                schedule_to_close_timeout=timedelta(seconds=30)
            )
            
            email = guess_result.get("email")
            if guess_result.get("confidence"):
                lead["email_confidence"] = guess_result.get("confidence")
            
            # If we guessed an email, verify it
            if email:
                verification = await workflow.execute_activity(
                    activities.verify_email_activity,
                    args=[email],
                    schedule_to_close_timeout=timedelta(minutes=1)
                )
                lead["email"] = email
                lead["email_verification"] = verification
                if verification.get("status") == "invalid":
                    lead["email"] = None
            else:
                lead["email"] = None
                
            return lead

        # Run all lead processing concurrently!
        lead_tasks = [process_lead(lead) for lead in leads]
        processed_leads = await asyncio.gather(*lead_tasks)
            
        workflow.logger.info("Discovery Workflow complete!")
        return processed_leads
