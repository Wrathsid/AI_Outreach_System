import asyncio
import os
import logging
from temporalio.client import Client
from temporalio.worker import Worker

# Import our defined workflow and activities
from backend.temporal.workflows import DiscoveryWorkflow
from backend.temporal.activities import (
    verify_email_activity,
    generate_email_pattern_activity,
    crawl_linkedin_activity,
    polish_leads_activity
)

from backend.temporal.draft_workflows import BatchDraftWorkflow
from backend.temporal.draft_activities import generate_draft_activity

# Set up logging for the worker
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("temporal-worker")

async def main():
    """
    Main entry point for the Temporal Worker.
    This process sits here forever, polling the Temporal Server 
    for Workflow or Activity tasks to execute.
    """
    temporal_addr = os.getenv("TEMPORAL_ADDRESS", "127.0.0.1:7233")
    logger.info(f"Connecting to Temporal server at {temporal_addr}...")
    
    # 1. Connect to the Temporal Server
    client = await Client.connect(temporal_addr)
    
    logger.info("Connected successfully! Starting workers...")

    # 2. Create the Worker instances
    # Worker 1: Discovery Queue
    worker_discovery = Worker(
        client,
        task_queue="discovery-task-queue",
        workflows=[DiscoveryWorkflow],
        activities=[
            verify_email_activity,
            generate_email_pattern_activity,
            crawl_linkedin_activity,
            polish_leads_activity
        ],
    )
    
    # Worker 2: Draft Queue
    # We apply rate limits here to ensure we don't exceed API rate limits (e.g., 5 LLM requests/sec)
    worker_drafts = Worker(
        client,
        task_queue="draft-task-queue",
        workflows=[BatchDraftWorkflow],
        activities=[generate_draft_activity],
        max_activities_per_second=5.0
    )
    
    # 3. Start listening until manually stopped (Ctrl+C)
    logger.info("Workers are now polling and ready to execute tasks.")
    await asyncio.gather(worker_discovery.run(), worker_drafts.run())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nWorker stopped gracefully.")
