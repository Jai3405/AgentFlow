"""
Execution context for workflow execution
Maintains state and data throughout workflow execution
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class ExecutionStatus(str, Enum):
    """Execution status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ExecutionContext:
    """
    Execution context for workflow runs
    Maintains state, variables, and metadata throughout execution
    """

    def __init__(
        self,
        execution_id: str,
        workflow_id: str,
        workflow_spec: Dict[str, Any],
        input_data: Dict[str, Any] = None,
        trigger_type: str = "manual"
    ):
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self.workflow_spec = workflow_spec
        self.trigger_type = trigger_type

        # Execution state
        self.status = ExecutionStatus.PENDING
        self.current_step: Optional[str] = None
        self.completed_steps: List[str] = []
        self.failed_steps: List[str] = []

        # Timing
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.paused_at: Optional[datetime] = None

        # Data and variables
        self.input_data = input_data or {}
        self.variables: Dict[str, Any] = {}
        self.step_outputs: Dict[str, Any] = {}

        # Logs and errors
        self.logs: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []

        # Metadata
        self.metadata: Dict[str, Any] = {
            'created_at': datetime.now().isoformat(),
            'trigger_type': trigger_type
        }

    def start(self):
        """Mark execution as started"""
        self.status = ExecutionStatus.RUNNING
        self.started_at = datetime.now()
        self.log("info", "Workflow execution started")

    def complete(self):
        """Mark execution as completed"""
        self.status = ExecutionStatus.COMPLETED
        self.completed_at = datetime.now()
        self.log("info", "Workflow execution completed successfully")

    def fail(self, error: str):
        """Mark execution as failed"""
        self.status = ExecutionStatus.FAILED
        self.completed_at = datetime.now()
        self.add_error("workflow", error)
        self.log("error", f"Workflow execution failed: {error}")

    def cancel(self):
        """Cancel execution"""
        self.status = ExecutionStatus.CANCELLED
        self.completed_at = datetime.now()
        self.log("warning", "Workflow execution cancelled")

    def pause(self):
        """Pause execution"""
        self.status = ExecutionStatus.PAUSED
        self.paused_at = datetime.now()
        self.log("info", "Workflow execution paused")

    def resume(self):
        """Resume execution"""
        self.status = ExecutionStatus.RUNNING
        self.paused_at = None
        self.log("info", "Workflow execution resumed")

    def set_current_step(self, step_id: str):
        """Set currently executing step"""
        self.current_step = step_id
        self.log("info", f"Starting step: {step_id}")

    def mark_step_completed(self, step_id: str, output: Any = None):
        """Mark step as completed"""
        if step_id not in self.completed_steps:
            self.completed_steps.append(step_id)

        if output is not None:
            self.step_outputs[step_id] = output

        self.log("info", f"Step completed: {step_id}")

    def mark_step_failed(self, step_id: str, error: str):
        """Mark step as failed"""
        if step_id not in self.failed_steps:
            self.failed_steps.append(step_id)

        self.add_error(step_id, error)
        self.log("error", f"Step failed: {step_id} - {error}")

    def set_variable(self, key: str, value: Any):
        """Set workflow variable"""
        self.variables[key] = value
        self.log("debug", f"Variable set: {key}")

    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get workflow variable"""
        return self.variables.get(key, default)

    def set_step_output(self, step_id: str, output: Any):
        """Set output from a step"""
        self.step_outputs[step_id] = output

    def get_step_output(self, step_id: str, default: Any = None) -> Any:
        """Get output from a step"""
        return self.step_outputs.get(step_id, default)

    def log(self, level: str, message: str, **kwargs):
        """Add log entry"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'step': self.current_step,
            **kwargs
        }
        self.logs.append(log_entry)

    def add_error(self, source: str, error: str, **kwargs):
        """Add error entry"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'source': source,
            'error': error,
            **kwargs
        }
        self.errors.append(error_entry)

    def get_execution_time(self) -> Optional[float]:
        """Get execution time in seconds"""
        if not self.started_at:
            return None

        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()

    def get_progress(self) -> float:
        """
        Calculate execution progress (0.0 to 1.0)
        Based on completed steps vs total steps
        """
        steps = self.workflow_spec.get('steps', [])
        if not steps:
            return 0.0

        total_steps = len(steps)
        completed = len(self.completed_steps)

        return min(completed / total_steps, 1.0)

    def is_step_completed(self, step_id: str) -> bool:
        """Check if step has been completed"""
        return step_id in self.completed_steps

    def is_step_failed(self, step_id: str) -> bool:
        """Check if step has failed"""
        return step_id in self.failed_steps

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        return {
            'execution_id': self.execution_id,
            'workflow_id': self.workflow_id,
            'status': self.status.value,
            'current_step': self.current_step,
            'completed_steps': self.completed_steps,
            'failed_steps': self.failed_steps,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'paused_at': self.paused_at.isoformat() if self.paused_at else None,
            'execution_time': self.get_execution_time(),
            'progress': self.get_progress(),
            'input_data': self.input_data,
            'variables': self.variables,
            'step_outputs': self.step_outputs,
            'logs': self.logs,
            'errors': self.errors,
            'metadata': self.metadata,
            'trigger_type': self.trigger_type
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary (without logs/outputs)"""
        return {
            'execution_id': self.execution_id,
            'workflow_id': self.workflow_id,
            'status': self.status.value,
            'current_step': self.current_step,
            'progress': self.get_progress(),
            'execution_time': self.get_execution_time(),
            'completed_steps_count': len(self.completed_steps),
            'failed_steps_count': len(self.failed_steps),
            'error_count': len(self.errors),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
