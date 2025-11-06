"""
Workflow executor - orchestrates workflow execution
Handles step sequencing, error handling, and state management
"""

from typing import Dict, Any, Optional, List
import uuid
import asyncio

from execution.execution_context import ExecutionContext, ExecutionStatus
from execution.step_processor import StepProcessor
from integrations.integration_manager import IntegrationManager


class WorkflowExecutor:
    """
    Main workflow execution engine
    Orchestrates step execution and manages workflow state
    """

    def __init__(self, integration_manager: IntegrationManager = None):
        self.integration_manager = integration_manager or IntegrationManager()
        self.step_processor = StepProcessor(self.integration_manager)

        # Active executions
        self.active_executions: Dict[str, ExecutionContext] = {}

    async def execute_workflow(
        self,
        workflow_id: str,
        workflow_spec: Dict[str, Any],
        input_data: Dict[str, Any] = None,
        trigger_type: str = "manual",
        execution_id: str = None
    ) -> ExecutionContext:
        """
        Execute a workflow

        Args:
            workflow_id: Workflow identifier
            workflow_spec: Workflow specification with steps
            input_data: Input data for workflow
            trigger_type: How workflow was triggered (manual, scheduled, webhook)
            execution_id: Optional execution ID (generated if not provided)

        Returns:
            ExecutionContext with results
        """
        # Create execution context
        execution_id = execution_id or str(uuid.uuid4())
        context = ExecutionContext(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_spec=workflow_spec,
            input_data=input_data,
            trigger_type=trigger_type
        )

        # Store active execution
        self.active_executions[execution_id] = context

        try:
            # Start execution
            context.start()

            # Initialize input variables
            if input_data:
                for key, value in input_data.items():
                    context.set_variable(key, value)

            # Execute steps
            await self._execute_steps(workflow_spec.get('steps', []), context)

            # Mark as completed
            context.complete()

        except Exception as e:
            # Mark as failed
            context.fail(str(e))

        finally:
            # Remove from active executions
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]

        return context

    async def _execute_steps(
        self,
        steps: List[Dict[str, Any]],
        context: ExecutionContext
    ):
        """Execute workflow steps in sequence"""
        for step in steps:
            # Check if execution is cancelled or paused
            if context.status == ExecutionStatus.CANCELLED:
                return
            elif context.status == ExecutionStatus.PAUSED:
                # Wait for resume
                while context.status == ExecutionStatus.PAUSED:
                    await asyncio.sleep(0.5)

                if context.status == ExecutionStatus.CANCELLED:
                    return

            # Process step
            await self._execute_single_step(step, context)

    async def _execute_single_step(
        self,
        step: Dict[str, Any],
        context: ExecutionContext
    ):
        """Execute a single workflow step"""
        step_id = step.get('id')
        step_type = step.get('type')

        # Check conditions
        if 'condition' in step:
            condition_met = self._evaluate_step_condition(step['condition'], context)
            if not condition_met:
                context.log("info", f"Step {step_id} skipped (condition not met)")
                return

        # Handle retry logic
        retry_config = step.get('retry', {})
        max_retries = retry_config.get('max_attempts', 1)
        retry_delay = retry_config.get('delay', 1)

        last_error = None
        for attempt in range(max_retries):
            try:
                # Process the step
                result = await self.step_processor.process_step(step, context)

                # Handle conditional branching
                if step_type == 'condition':
                    branch = step.get('branches', {})
                    if result:
                        true_steps = branch.get('true', [])
                        await self._execute_steps(true_steps, context)
                    else:
                        false_steps = branch.get('false', [])
                        await self._execute_steps(false_steps, context)

                # Handle loops
                elif step_type == 'loop':
                    loop_steps = step.get('loop_steps', [])
                    items = result  # Result is the list of items to iterate

                    for i, item in enumerate(items):
                        # Set loop variables
                        context.set_variable('loop_item', item)
                        context.set_variable('loop_index', i)

                        # Execute loop body
                        await self._execute_steps(loop_steps, context)

                # Success - break retry loop
                break

            except Exception as e:
                last_error = e
                context.log("warning", f"Step {step_id} failed (attempt {attempt + 1}/{max_retries}): {str(e)}")

                if attempt < max_retries - 1:
                    # Wait before retry
                    await asyncio.sleep(retry_delay)
                else:
                    # All retries exhausted
                    error_handling = step.get('on_error', 'fail')

                    if error_handling == 'fail':
                        # Re-raise to fail workflow
                        raise
                    elif error_handling == 'continue':
                        # Log error and continue
                        context.mark_step_failed(step_id, str(e))
                        context.log("warning", f"Step {step_id} failed but continuing execution")
                    elif error_handling == 'skip':
                        # Skip and continue
                        context.log("warning", f"Step {step_id} skipped due to error")

    def _evaluate_step_condition(
        self,
        condition: Dict[str, Any],
        context: ExecutionContext
    ) -> bool:
        """Evaluate step execution condition"""
        condition_type = condition.get('type', 'variable')

        if condition_type == 'variable':
            var_name = condition.get('variable')
            operator = condition.get('operator', 'equals')
            value = condition.get('value')

            var_value = context.get_variable(var_name)

            if operator == 'equals':
                return var_value == value
            elif operator == 'not_equals':
                return var_value != value
            elif operator == 'greater_than':
                return var_value > value
            elif operator == 'less_than':
                return var_value < value
            elif operator == 'exists':
                return var_value is not None

        elif condition_type == 'step_status':
            step_id = condition.get('step_id')
            status = condition.get('status')

            if status == 'completed':
                return context.is_step_completed(step_id)
            elif status == 'failed':
                return context.is_step_failed(step_id)

        return True

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution"""
        if execution_id in self.active_executions:
            context = self.active_executions[execution_id]
            context.cancel()
            return True
        return False

    async def pause_execution(self, execution_id: str) -> bool:
        """Pause a running execution"""
        if execution_id in self.active_executions:
            context = self.active_executions[execution_id]
            if context.status == ExecutionStatus.RUNNING:
                context.pause()
                return True
        return False

    async def resume_execution(self, execution_id: str) -> bool:
        """Resume a paused execution"""
        if execution_id in self.active_executions:
            context = self.active_executions[execution_id]
            if context.status == ExecutionStatus.PAUSED:
                context.resume()
                return True
        return False

    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a running execution"""
        if execution_id in self.active_executions:
            return self.active_executions[execution_id].get_summary()
        return None

    def list_active_executions(self) -> List[Dict[str, Any]]:
        """List all active executions"""
        return [
            context.get_summary()
            for context in self.active_executions.values()
        ]

    async def execute_workflow_async(
        self,
        workflow_id: str,
        workflow_spec: Dict[str, Any],
        input_data: Dict[str, Any] = None,
        trigger_type: str = "manual"
    ) -> str:
        """
        Execute workflow asynchronously (fire and forget)

        Args:
            workflow_id: Workflow identifier
            workflow_spec: Workflow specification
            input_data: Input data
            trigger_type: Trigger type

        Returns:
            Execution ID
        """
        execution_id = str(uuid.uuid4())

        # Start execution in background
        asyncio.create_task(
            self.execute_workflow(
                workflow_id=workflow_id,
                workflow_spec=workflow_spec,
                input_data=input_data,
                trigger_type=trigger_type,
                execution_id=execution_id
            )
        )

        return execution_id

    async def validate_workflow(self, workflow_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate workflow specification

        Args:
            workflow_spec: Workflow specification

        Returns:
            Validation result
        """
        errors = []
        warnings = []

        # Check required fields
        if 'steps' not in workflow_spec:
            errors.append("Workflow must have 'steps' field")
        else:
            steps = workflow_spec['steps']

            # Validate steps
            step_ids = set()
            for i, step in enumerate(steps):
                # Check step ID
                if 'id' not in step:
                    errors.append(f"Step {i} missing 'id' field")
                else:
                    step_id = step['id']
                    if step_id in step_ids:
                        errors.append(f"Duplicate step ID: {step_id}")
                    step_ids.add(step_id)

                # Check step type
                if 'type' not in step:
                    errors.append(f"Step {step.get('id', i)} missing 'type' field")

                # Check config
                if 'config' not in step:
                    warnings.append(f"Step {step.get('id', i)} missing 'config' field")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
