from temporalio import workflow
from datetime import timedelta
from typing import List, Dict

with workflow.unsafe.imports_passed_through():
    import backend.temporal.draft_activities as draft_activities

@workflow.defn
class BatchDraftWorkflow:
    """
    Temporal Workflow for batch generating drafts for multiple candidates.
    """
    @workflow.run
    async def run(self, candidate_ids: List[int], context: str = "", contact_type: str = "auto") -> Dict:
        workflow.logger.info(f"Starting Batch Draft Workflow for {len(candidate_ids)} candidates")
        
        results = []
        # Execute drafts in parallel using asyncio.gather
        import asyncio
        
        # We create a list of activity executions
        activity_tasks = [
            workflow.execute_activity(
                draft_activities.generate_draft_activity,
                args=[candidate_id, context, contact_type],
                # Draft generation can take time, give it 3 minutes
                schedule_to_close_timeout=timedelta(minutes=3),
                # If an AI provider fails, it will be caught by the activity and returned as an error,
                # but network issues to the worker itself will be retried by Temporal.
            )
            for candidate_id in candidate_ids
        ]
        
        # Wait for all drafts to complete, returning exceptions instead of raising them
        batch_results = await asyncio.gather(*activity_tasks, return_exceptions=True)
        
        successful = 0
        failed = 0
        
        for i, res in enumerate(batch_results):
            cid = candidate_ids[i]
            
            # Check if an exception was raised by the activity
            if isinstance(res, Exception):
                failed += 1
                results.append({"candidate_id": cid, "status": "error", "error": str(res)})
            # Otherwise, check the result dictionary
            elif isinstance(res, dict) and res.get("status") == "success":
                successful += 1
                results.append({"candidate_id": cid, "status": "success", "data": res.get("data")})
            else:
                failed += 1
                err_msg = res.get("error") if isinstance(res, dict) else "Unknown error"
                results.append({"candidate_id": cid, "status": "error", "error": err_msg})
                
        workflow.logger.info(f"Batch Draft Workflow complete. Success: {successful}, Failed: {failed}")
        
        return {
            "total": len(candidate_ids),
            "successful": successful,
            "failed": failed,
            "results": results
        }
