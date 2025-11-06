"""
FastAPI endpoints for workflow monitoring and analytics
Provides real-time metrics and performance insights
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from execution.analytics import ExecutionAnalytics

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

# Global analytics instance
analytics = ExecutionAnalytics()


@router.get("/metrics/{workflow_id}")
async def get_workflow_metrics(workflow_id: str):
    """
    Get comprehensive metrics for a specific workflow

    Returns execution counts, success rates, performance metrics
    """
    metrics = analytics.get_workflow_metrics(workflow_id)

    return {
        "status": "success",
        "metrics": metrics
    }


@router.get("/metrics")
async def get_overall_metrics():
    """
    Get overall system-wide metrics

    Returns aggregated metrics across all workflows
    """
    metrics = analytics.get_overall_metrics()

    return {
        "status": "success",
        "metrics": metrics
    }


@router.get("/trends")
async def get_execution_trends(
    workflow_id: Optional[str] = None,
    time_window_hours: int = 24
):
    """
    Get execution trends over time

    **Parameters**:
    - workflow_id: Optional filter for specific workflow
    - time_window_hours: Time window for analysis (default 24)

    Returns hourly execution trends
    """
    trends = analytics.get_execution_trends(
        workflow_id=workflow_id,
        time_window_hours=time_window_hours
    )

    return {
        "status": "success",
        "trends": trends
    }


@router.get("/performance/{workflow_id}")
async def get_step_performance(workflow_id: str):
    """
    Get performance analysis for workflow steps

    Returns completion rates and failure analysis per step
    """
    performance = analytics.get_step_performance(workflow_id)

    return {
        "status": "success",
        "performance": performance
    }


@router.get("/errors")
async def get_error_analysis(
    workflow_id: Optional[str] = None,
    limit: int = 10
):
    """
    Get error analysis

    **Parameters**:
    - workflow_id: Optional filter for specific workflow
    - limit: Maximum number of error types to return

    Returns error frequencies and examples
    """
    analysis = analytics.get_error_analysis(
        workflow_id=workflow_id,
        limit=limit
    )

    return {
        "status": "success",
        "analysis": analysis
    }


@router.get("/summary/{workflow_id}")
async def get_performance_summary(workflow_id: str):
    """
    Get comprehensive performance summary

    Combines metrics, step performance, errors, and recent executions
    """
    summary = analytics.get_performance_summary(workflow_id)

    return {
        "status": "success",
        "summary": summary
    }


@router.delete("/history")
async def clear_execution_history(workflow_id: Optional[str] = None):
    """
    Clear execution history

    **Parameters**:
    - workflow_id: Optional filter to clear specific workflow history

    If workflow_id not provided, clears all history
    """
    analytics.clear_history(workflow_id=workflow_id)

    return {
        "status": "success",
        "message": f"History cleared for {'workflow: ' + workflow_id if workflow_id else 'all workflows'}"
    }


@router.get("/health")
async def get_system_health():
    """
    Get system health status

    Returns quick health metrics for monitoring
    """
    overall = analytics.get_overall_metrics()

    # Determine health status
    success_rate = overall.get('success_rate', 0)

    if success_rate >= 95:
        health_status = "healthy"
    elif success_rate >= 80:
        health_status = "degraded"
    else:
        health_status = "unhealthy"

    return {
        "status": "success",
        "health": {
            "status": health_status,
            "success_rate": success_rate,
            "total_executions": overall.get('total_executions', 0),
            "failed_executions": overall.get('failed_executions', 0),
            "active_workflows": overall.get('total_workflows', 0)
        }
    }
