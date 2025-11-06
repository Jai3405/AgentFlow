"""
FastAPI endpoints for workflow execution and scheduling
Handles workflow execution, scheduling, and monitoring
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime

from execution.workflow_executor import WorkflowExecutor
from execution.scheduler import WorkflowScheduler, ScheduleType
from integrations.integration_manager import IntegrationManager

router = APIRouter(prefix="/api/execution", tags=["execution"])

# Global instances
integration_manager = IntegrationManager()
workflow_executor = WorkflowExecutor(integration_manager)
workflow_scheduler = WorkflowScheduler(workflow_executor)


# Request/Response Models

class ExecuteWorkflowRequest(BaseModel):
    """Request to execute a workflow"""
    workflow_id: str
    workflow_spec: Dict[str, Any] = Field(..., description="Workflow specification with steps")
    input_data: Optional[Dict[str, Any]] = None
    async_execution: bool = Field(False, description="Execute asynchronously in background")


class ScheduleWorkflowRequest(BaseModel):
    """Request to schedule a workflow"""
    workflow_id: str
    workflow_spec: Dict[str, Any]
    schedule_type: str = Field(..., description="cron, interval, or once")
    schedule_config: Dict[str, Any] = Field(..., description="Schedule configuration")
    input_data: Optional[Dict[str, Any]] = None


class UpdateScheduleRequest(BaseModel):
    """Request to update schedule"""
    enabled: Optional[bool] = None
    schedule_config: Optional[Dict[str, Any]] = None


# Execution Endpoints

@router.post("/execute")
async def execute_workflow(request: ExecuteWorkflowRequest, background_tasks: BackgroundTasks):
    """
    Execute a workflow

    **Sync execution**: Returns full execution context after completion
    **Async execution**: Returns execution ID immediately, workflow runs in background

    **Example workflow_spec**:
    ```json
    {
      "steps": [
        {
          "id": "step1",
          "type": "email",
          "config": {
            "action": "send",
            "provider": "gmail",
            "to": ["user@example.com"],
            "subject": "Test Email",
            "body": "Hello from AgentFlow!"
          }
        }
      ]
    }
    ```
    """
    try:
        if request.async_execution:
            # Execute asynchronously
            execution_id = await workflow_executor.execute_workflow_async(
                workflow_id=request.workflow_id,
                workflow_spec=request.workflow_spec,
                input_data=request.input_data,
                trigger_type="api"
            )

            return {
                "status": "started",
                "execution_id": execution_id,
                "message": "Workflow execution started in background"
            }
        else:
            # Execute synchronously
            context = await workflow_executor.execute_workflow(
                workflow_id=request.workflow_id,
                workflow_spec=request.workflow_spec,
                input_data=request.input_data,
                trigger_type="api"
            )

            return {
                "status": "completed",
                "execution": context.to_dict()
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@router.get("/status/{execution_id}")
async def get_execution_status(execution_id: str):
    """
    Get status of a running execution

    Returns current status, progress, and metadata
    """
    status = workflow_executor.get_execution_status(execution_id)

    if not status:
        raise HTTPException(status_code=404, detail="Execution not found or already completed")

    return {
        "status": "success",
        "execution": status
    }


@router.get("/active")
async def list_active_executions():
    """List all currently active executions"""
    executions = workflow_executor.list_active_executions()

    return {
        "status": "success",
        "count": len(executions),
        "executions": executions
    }


@router.post("/cancel/{execution_id}")
async def cancel_execution(execution_id: str):
    """Cancel a running execution"""
    success = await workflow_executor.cancel_execution(execution_id)

    if not success:
        raise HTTPException(status_code=404, detail="Execution not found or cannot be cancelled")

    return {
        "status": "success",
        "message": f"Execution {execution_id} cancelled"
    }


@router.post("/pause/{execution_id}")
async def pause_execution(execution_id: str):
    """Pause a running execution"""
    success = await workflow_executor.pause_execution(execution_id)

    if not success:
        raise HTTPException(status_code=404, detail="Execution not found or cannot be paused")

    return {
        "status": "success",
        "message": f"Execution {execution_id} paused"
    }


@router.post("/resume/{execution_id}")
async def resume_execution(execution_id: str):
    """Resume a paused execution"""
    success = await workflow_executor.resume_execution(execution_id)

    if not success:
        raise HTTPException(status_code=404, detail="Execution not found or not paused")

    return {
        "status": "success",
        "message": f"Execution {execution_id} resumed"
    }


# Scheduling Endpoints

@router.post("/schedule")
async def schedule_workflow(request: ScheduleWorkflowRequest):
    """
    Schedule a workflow for recurring or one-time execution

    **Schedule Types**:
    - **cron**: Cron expression (e.g., "0 9 * * *" for daily at 9 AM)
    - **interval**: Regular intervals (e.g., {"minutes": 30} for every 30 minutes)
    - **once**: One-time execution (e.g., {"time": "2025-12-01T10:00:00"})

    **Examples**:
    ```json
    {
      "schedule_type": "cron",
      "schedule_config": {"expression": "0 9 * * *"}
    }

    {
      "schedule_type": "interval",
      "schedule_config": {"hours": 1, "minutes": 30}
    }

    {
      "schedule_type": "once",
      "schedule_config": {"time": "2025-12-01T10:00:00"}
    }
    ```
    """
    try:
        job_id = workflow_scheduler.schedule_workflow(
            workflow_id=request.workflow_id,
            workflow_spec=request.workflow_spec,
            schedule_type=request.schedule_type,
            schedule_config=request.schedule_config,
            input_data=request.input_data
        )

        job = workflow_scheduler.get_job(job_id)

        return {
            "status": "success",
            "message": "Workflow scheduled successfully",
            "job": job
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Scheduling failed: {str(e)}")


@router.get("/schedule/{job_id}")
async def get_scheduled_job(job_id: str):
    """Get details of a scheduled job"""
    job = workflow_scheduler.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Scheduled job not found")

    return {
        "status": "success",
        "job": job
    }


@router.get("/schedule")
async def list_scheduled_jobs(workflow_id: Optional[str] = None):
    """
    List all scheduled jobs

    Optionally filter by workflow_id
    """
    jobs = workflow_scheduler.list_jobs(workflow_id=workflow_id)

    return {
        "status": "success",
        "count": len(jobs),
        "jobs": jobs
    }


@router.put("/schedule/{job_id}")
async def update_scheduled_job(job_id: str, request: UpdateScheduleRequest):
    """
    Update a scheduled job

    Can enable/disable job or update schedule configuration
    """
    job = workflow_scheduler.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Scheduled job not found")

    # Update enabled status
    if request.enabled is not None:
        if request.enabled:
            workflow_scheduler.enable_job(job_id)
        else:
            workflow_scheduler.disable_job(job_id)

    # Update schedule config (requires recreating the job)
    if request.schedule_config:
        # Get current job details
        current_job = workflow_scheduler.jobs[job_id]

        # Unschedule current job
        workflow_scheduler.unschedule_workflow(job_id)

        # Reschedule with new config
        workflow_scheduler.schedule_workflow(
            workflow_id=current_job.workflow_id,
            workflow_spec=current_job.workflow_spec,
            schedule_type=current_job.schedule_type,
            schedule_config=request.schedule_config,
            input_data=current_job.input_data,
            job_id=job_id
        )

    updated_job = workflow_scheduler.get_job(job_id)

    return {
        "status": "success",
        "message": "Scheduled job updated",
        "job": updated_job
    }


@router.delete("/schedule/{job_id}")
async def unschedule_workflow(job_id: str):
    """Remove a scheduled job"""
    success = workflow_scheduler.unschedule_workflow(job_id)

    if not success:
        raise HTTPException(status_code=404, detail="Scheduled job not found")

    return {
        "status": "success",
        "message": f"Job {job_id} unscheduled"
    }


@router.post("/schedule/{job_id}/enable")
async def enable_scheduled_job(job_id: str):
    """Enable a scheduled job"""
    success = workflow_scheduler.enable_job(job_id)

    if not success:
        raise HTTPException(status_code=404, detail="Scheduled job not found")

    return {
        "status": "success",
        "message": f"Job {job_id} enabled"
    }


@router.post("/schedule/{job_id}/disable")
async def disable_scheduled_job(job_id: str):
    """Disable a scheduled job"""
    success = workflow_scheduler.disable_job(job_id)

    if not success:
        raise HTTPException(status_code=404, detail="Scheduled job not found")

    return {
        "status": "success",
        "message": f"Job {job_id} disabled"
    }


@router.get("/schedule/upcoming")
async def get_upcoming_executions(limit: int = 10):
    """
    Get upcoming scheduled executions

    Returns next N scheduled job executions ordered by time
    """
    upcoming = workflow_scheduler.get_upcoming_executions(limit=limit)

    return {
        "status": "success",
        "count": len(upcoming),
        "upcoming": upcoming
    }


@router.get("/schedule/history")
async def get_execution_history(job_id: Optional[str] = None):
    """
    Get execution history for scheduled jobs

    Optionally filter by job_id
    """
    history = workflow_scheduler.get_execution_history(job_id=job_id)

    return {
        "status": "success",
        "count": len(history),
        "history": history
    }


# Workflow Validation

@router.post("/validate")
async def validate_workflow(workflow_spec: Dict[str, Any]):
    """
    Validate a workflow specification

    Checks for required fields, duplicate step IDs, and configuration issues
    """
    result = await workflow_executor.validate_workflow(workflow_spec)

    return {
        "status": "success",
        "validation": result
    }


# Scheduler Control

@router.post("/scheduler/start")
async def start_scheduler():
    """Start the workflow scheduler"""
    await workflow_scheduler.start()

    return {
        "status": "success",
        "message": "Scheduler started"
    }


@router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the workflow scheduler"""
    await workflow_scheduler.stop()

    return {
        "status": "success",
        "message": "Scheduler stopped"
    }


@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status"""
    return {
        "status": "success",
        "running": workflow_scheduler.running,
        "active_jobs": len(workflow_scheduler.jobs)
    }
