"""
Workflow scheduler - handles scheduled and recurring workflow executions
Supports cron expressions and interval-based scheduling
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
import asyncio
import uuid

try:
    from croniter import croniter
    CRONITER_AVAILABLE = True
except ImportError:
    CRONITER_AVAILABLE = False
    print("Warning: croniter not installed. Cron scheduling disabled. Install with: pip install croniter")

from execution.workflow_executor import WorkflowExecutor


class ScheduleType:
    """Schedule type constants"""
    CRON = "cron"
    INTERVAL = "interval"
    ONCE = "once"


class ScheduledJob:
    """Represents a scheduled workflow job"""

    def __init__(
        self,
        job_id: str,
        workflow_id: str,
        workflow_spec: Dict[str, Any],
        schedule_type: str,
        schedule_config: Dict[str, Any],
        input_data: Dict[str, Any] = None,
        enabled: bool = True
    ):
        self.job_id = job_id
        self.workflow_id = workflow_id
        self.workflow_spec = workflow_spec
        self.schedule_type = schedule_type
        self.schedule_config = schedule_config
        self.input_data = input_data or {}
        self.enabled = enabled

        # Execution tracking
        self.last_execution: Optional[datetime] = None
        self.next_execution: Optional[datetime] = None
        self.execution_count = 0
        self.failure_count = 0

        # Calculate next execution
        self._calculate_next_execution()

    def _calculate_next_execution(self):
        """Calculate next execution time"""
        now = datetime.now()

        if self.schedule_type == ScheduleType.CRON:
            if not CRONITER_AVAILABLE:
                raise Exception("croniter not installed")

            cron_expression = self.schedule_config.get('expression')
            cron = croniter(cron_expression, now)
            self.next_execution = cron.get_next(datetime)

        elif self.schedule_type == ScheduleType.INTERVAL:
            interval_seconds = self.schedule_config.get('seconds', 0)
            interval_minutes = self.schedule_config.get('minutes', 0)
            interval_hours = self.schedule_config.get('hours', 0)

            total_seconds = interval_seconds + (interval_minutes * 60) + (interval_hours * 3600)

            if self.last_execution:
                self.next_execution = self.last_execution + timedelta(seconds=total_seconds)
            else:
                self.next_execution = now + timedelta(seconds=total_seconds)

        elif self.schedule_type == ScheduleType.ONCE:
            scheduled_time = self.schedule_config.get('time')
            if isinstance(scheduled_time, str):
                self.next_execution = datetime.fromisoformat(scheduled_time)
            else:
                self.next_execution = scheduled_time

    def should_execute_now(self) -> bool:
        """Check if job should execute now"""
        if not self.enabled:
            return False

        if not self.next_execution:
            return False

        return datetime.now() >= self.next_execution

    def mark_executed(self, success: bool = True):
        """Mark job as executed"""
        self.last_execution = datetime.now()
        self.execution_count += 1

        if not success:
            self.failure_count += 1

        # Calculate next execution (except for one-time jobs)
        if self.schedule_type != ScheduleType.ONCE:
            self._calculate_next_execution()
        else:
            self.enabled = False  # Disable after execution

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'job_id': self.job_id,
            'workflow_id': self.workflow_id,
            'schedule_type': self.schedule_type,
            'schedule_config': self.schedule_config,
            'enabled': self.enabled,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'next_execution': self.next_execution.isoformat() if self.next_execution else None,
            'execution_count': self.execution_count,
            'failure_count': self.failure_count
        }


class WorkflowScheduler:
    """
    Workflow scheduler
    Manages scheduled and recurring workflow executions
    """

    def __init__(self, workflow_executor: WorkflowExecutor = None):
        self.executor = workflow_executor or WorkflowExecutor()

        # Scheduled jobs
        self.jobs: Dict[str, ScheduledJob] = {}

        # Scheduler state
        self.running = False
        self.scheduler_task: Optional[asyncio.Task] = None

        # Callbacks
        self.on_execution_start: Optional[Callable] = None
        self.on_execution_complete: Optional[Callable] = None
        self.on_execution_failed: Optional[Callable] = None

    def schedule_workflow(
        self,
        workflow_id: str,
        workflow_spec: Dict[str, Any],
        schedule_type: str,
        schedule_config: Dict[str, Any],
        input_data: Dict[str, Any] = None,
        job_id: str = None
    ) -> str:
        """
        Schedule a workflow for execution

        Args:
            workflow_id: Workflow identifier
            workflow_spec: Workflow specification
            schedule_type: Type of schedule (cron, interval, once)
            schedule_config: Schedule configuration
            input_data: Input data for workflow
            job_id: Optional job ID

        Returns:
            Job ID

        Examples:
            # Cron schedule (every day at 9 AM)
            schedule_workflow(..., schedule_type="cron", schedule_config={'expression': '0 9 * * *'})

            # Interval schedule (every 30 minutes)
            schedule_workflow(..., schedule_type="interval", schedule_config={'minutes': 30})

            # One-time schedule
            schedule_workflow(..., schedule_type="once", schedule_config={'time': '2025-12-01T10:00:00'})
        """
        job_id = job_id or str(uuid.uuid4())

        job = ScheduledJob(
            job_id=job_id,
            workflow_id=workflow_id,
            workflow_spec=workflow_spec,
            schedule_type=schedule_type,
            schedule_config=schedule_config,
            input_data=input_data
        )

        self.jobs[job_id] = job

        # Start scheduler if not running
        if not self.running:
            asyncio.create_task(self.start())

        return job_id

    def unschedule_workflow(self, job_id: str) -> bool:
        """Remove scheduled job"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            return True
        return False

    def enable_job(self, job_id: str) -> bool:
        """Enable a scheduled job"""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = True
            return True
        return False

    def disable_job(self, job_id: str) -> bool:
        """Disable a scheduled job"""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = False
            return True
        return False

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details"""
        if job_id in self.jobs:
            return self.jobs[job_id].to_dict()
        return None

    def list_jobs(self, workflow_id: str = None) -> List[Dict[str, Any]]:
        """List all scheduled jobs"""
        jobs = self.jobs.values()

        if workflow_id:
            jobs = [job for job in jobs if job.workflow_id == workflow_id]

        return [job.to_dict() for job in jobs]

    async def start(self):
        """Start the scheduler"""
        if self.running:
            return

        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())

    async def stop(self):
        """Stop the scheduler"""
        self.running = False

        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass

    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Check all jobs
                for job in list(self.jobs.values()):
                    if job.should_execute_now():
                        # Execute job in background
                        asyncio.create_task(self._execute_job(job))

                # Sleep for a short interval
                await asyncio.sleep(1)

            except Exception as e:
                print(f"Scheduler error: {str(e)}")
                await asyncio.sleep(5)

    async def _execute_job(self, job: ScheduledJob):
        """Execute a scheduled job"""
        try:
            # Callback: execution start
            if self.on_execution_start:
                self.on_execution_start(job.job_id, job.workflow_id)

            # Execute workflow
            context = await self.executor.execute_workflow(
                workflow_id=job.workflow_id,
                workflow_spec=job.workflow_spec,
                input_data=job.input_data,
                trigger_type="scheduled"
            )

            # Mark as executed
            success = context.status.value == "completed"
            job.mark_executed(success)

            # Callback: execution complete
            if success and self.on_execution_complete:
                self.on_execution_complete(job.job_id, job.workflow_id, context)
            elif not success and self.on_execution_failed:
                self.on_execution_failed(job.job_id, job.workflow_id, context)

        except Exception as e:
            job.mark_executed(False)

            if self.on_execution_failed:
                self.on_execution_failed(job.job_id, job.workflow_id, e)

    def get_upcoming_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get upcoming job executions"""
        upcoming = []

        for job in self.jobs.values():
            if job.enabled and job.next_execution:
                upcoming.append({
                    'job_id': job.job_id,
                    'workflow_id': job.workflow_id,
                    'next_execution': job.next_execution.isoformat(),
                    'schedule_type': job.schedule_type
                })

        # Sort by next execution time
        upcoming.sort(key=lambda x: x['next_execution'])

        return upcoming[:limit]

    def get_execution_history(self, job_id: str = None) -> List[Dict[str, Any]]:
        """Get execution history"""
        # For now, return basic stats
        # In production, this would query execution history from database
        history = []

        jobs = [self.jobs[job_id]] if job_id and job_id in self.jobs else self.jobs.values()

        for job in jobs:
            history.append({
                'job_id': job.job_id,
                'workflow_id': job.workflow_id,
                'execution_count': job.execution_count,
                'failure_count': job.failure_count,
                'last_execution': job.last_execution.isoformat() if job.last_execution else None,
                'success_rate': (job.execution_count - job.failure_count) / job.execution_count if job.execution_count > 0 else 0
            })

        return history
