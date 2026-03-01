"""
Discovery router - Lead discovery and search endpoints.
"""
from fastapi import APIRouter

from backend.config import logger

router = APIRouter(tags=["Discovery"])




import uuid
from fastapi import Request

@router.post("/temporal-discover")
async def start_temporal_discovery(request: Request, role: str, limit: int = 20):
    """Start a Temporal workflow for discovery."""
    client = request.app.state.temporal_client
    if not client:
        return {"status": "error", "message": "Temporal client not connected"}
        
    job_id = f"discovery-{uuid.uuid4()}"
    
    try:
        from backend.temporal.workflows import DiscoveryWorkflow
        
        # Start the workflow in the background. Does not block!
        handle = await client.start_workflow(
            DiscoveryWorkflow.run,
            args=[role, limit],
            id=job_id,
            task_queue="discovery-task-queue"
        )
        return {"status": "running", "job_id": job_id}
    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/temporal-discover/{job_id}")
async def get_temporal_discovery_status(request: Request, job_id: str):
    """Check the status of a Temporal discovery workflow."""
    client = request.app.state.temporal_client
    if not client:
         return {"status": "error", "message": "Temporal client not connected"}
         
    try:
        handle = client.get_workflow_handle(job_id)
        description = await handle.describe()
        
        from temporalio.client import WorkflowExecutionStatus
        
        # If it's done, we can get the result
        if description.status == WorkflowExecutionStatus.COMPLETED:
            results = await handle.result()
            return {"status": "completed", "results": results}
        elif description.status == WorkflowExecutionStatus.FAILED:
            return {"status": "failed", "message": "Workflow failed"}
        else:
            return {"status": "running"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}
