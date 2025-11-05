"""
Workflow validation system
Validates workflow specifications for completeness, correctness, and best practices
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime


class WorkflowValidator:
    """Validate workflow specifications"""

    def __init__(self):
        self.required_step_fields = ['id', 'type', 'name', 'description']
        self.valid_step_types = ['email', 'data', 'process', 'decision', 'action', 'notification', 'integration']

    def validate_workflow(self, workflow: Dict, intent: str = None) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a workflow specification

        Returns:
            (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        if not workflow:
            errors.append("Workflow is empty")
            return False, errors, warnings

        # Validate basic structure
        struct_errors, struct_warnings = self._validate_structure(workflow)
        errors.extend(struct_errors)
        warnings.extend(struct_warnings)

        # Validate steps
        if 'steps' in workflow:
            step_errors, step_warnings = self._validate_steps(workflow['steps'])
            errors.extend(step_errors)
            warnings.extend(step_warnings)

        # Validate connections if present
        if 'connections' in workflow and workflow['connections']:
            conn_errors, conn_warnings = self._validate_connections(
                workflow['connections'],
                workflow.get('steps', [])
            )
            errors.extend(conn_errors)
            warnings.extend(conn_warnings)

        # Intent-specific validation
        if intent:
            intent_errors, intent_warnings = self._validate_for_intent(workflow, intent)
            errors.extend(intent_errors)
            warnings.extend(intent_warnings)

        # Best practices validation
        bp_warnings = self._validate_best_practices(workflow)
        warnings.extend(bp_warnings)

        is_valid = len(errors) == 0

        return is_valid, errors, warnings

    def _validate_structure(self, workflow: Dict) -> Tuple[List[str], List[str]]:
        """Validate basic workflow structure"""
        errors = []
        warnings = []

        # Check required fields
        if 'steps' not in workflow:
            errors.append("Workflow must have 'steps' field")
        elif not isinstance(workflow['steps'], list):
            errors.append("'steps' must be a list")
        elif len(workflow['steps']) == 0:
            warnings.append("Workflow has no steps defined")

        # Check optional but recommended fields
        if 'metadata' not in workflow:
            warnings.append("Workflow missing 'metadata' field")

        return errors, warnings

    def _validate_steps(self, steps: List[Dict]) -> Tuple[List[str], List[str]]:
        """Validate workflow steps"""
        errors = []
        warnings = []

        step_ids = set()

        for i, step in enumerate(steps):
            step_num = i + 1

            # Check required fields
            for field in self.required_step_fields:
                if field not in step:
                    errors.append(f"Step {step_num}: Missing required field '{field}'")

            # Validate step ID uniqueness
            if 'id' in step:
                if step['id'] in step_ids:
                    errors.append(f"Step {step_num}: Duplicate step ID '{step['id']}'")
                step_ids.add(step['id'])

            # Validate step type
            if 'type' in step and step['type'] not in self.valid_step_types:
                warnings.append(
                    f"Step {step_num}: Unknown step type '{step['type']}'. "
                    f"Valid types: {', '.join(self.valid_step_types)}"
                )

            # Validate description quality
            if 'description' in step:
                if len(step['description']) < 10:
                    warnings.append(f"Step {step_num}: Description is too short")

            # Check for configuration if it's a complex step type
            if step.get('type') in ['email', 'integration', 'notification']:
                if 'config' not in step:
                    warnings.append(f"Step {step_num}: Complex step missing 'config' field")

        return errors, warnings

    def _validate_connections(
        self,
        connections: List[Dict],
        steps: List[Dict]
    ) -> Tuple[List[str], List[str]]:
        """Validate workflow connections"""
        errors = []
        warnings = []

        if not isinstance(connections, list):
            errors.append("'connections' must be a list")
            return errors, warnings

        step_ids = {step.get('id') for step in steps if 'id' in step}

        for i, conn in enumerate(connections):
            conn_num = i + 1

            # Check required fields
            if 'from' not in conn:
                errors.append(f"Connection {conn_num}: Missing 'from' field")
            if 'to' not in conn:
                errors.append(f"Connection {conn_num}: Missing 'to' field")

            # Validate step IDs exist
            if 'from' in conn and conn['from'] not in step_ids:
                errors.append(f"Connection {conn_num}: 'from' references non-existent step '{conn['from']}'")
            if 'to' in conn and conn['to'] not in step_ids:
                errors.append(f"Connection {conn_num}: 'to' references non-existent step '{conn['to']}'")

        # Check for disconnected steps
        connected_steps = set()
        for conn in connections:
            connected_steps.add(conn.get('from'))
            connected_steps.add(conn.get('to'))

        disconnected = step_ids - connected_steps
        if disconnected:
            warnings.append(f"Steps not connected in workflow: {', '.join(disconnected)}")

        return errors, warnings

    def _validate_for_intent(self, workflow: Dict, intent: str) -> Tuple[List[str], List[str]]:
        """Validate workflow against intent-specific requirements"""
        errors = []
        warnings = []

        steps = workflow.get('steps', [])
        step_types = {step.get('type') for step in steps}

        validators = {
            'email_automation': self._validate_email_workflow,
            'data_processing': self._validate_data_workflow,
            'approval_workflow': self._validate_approval_workflow,
            'notification_system': self._validate_notification_workflow
        }

        validator = validators.get(intent)
        if validator:
            intent_errors, intent_warnings = validator(workflow)
            errors.extend(intent_errors)
            warnings.extend(intent_warnings)

        return errors, warnings

    def _validate_email_workflow(self, workflow: Dict) -> Tuple[List[str], List[str]]:
        """Validate email automation workflow"""
        errors = []
        warnings = []

        steps = workflow.get('steps', [])
        step_types = {step.get('type') for step in steps}

        # Must have email monitoring
        if 'email' not in step_types:
            errors.append("Email workflow must have at least one 'email' type step for monitoring")

        # Should have classification/processing
        if 'process' not in step_types:
            warnings.append("Email workflow should have a 'process' step for classification")

        # Should have routing decision
        if 'decision' not in step_types:
            warnings.append("Email workflow should have a 'decision' step for routing")

        # Should have notification
        if 'notification' not in step_types:
            warnings.append("Email workflow should have a 'notification' step")

        return errors, warnings

    def _validate_data_workflow(self, workflow: Dict) -> Tuple[List[str], List[str]]:
        """Validate data processing workflow"""
        errors = []
        warnings = []

        steps = workflow.get('steps', [])
        step_types = {step.get('type') for step in steps}

        # Must have data input
        if 'data' not in step_types:
            errors.append("Data workflow must have at least one 'data' type step for input")

        # Should have processing
        if 'process' not in step_types:
            warnings.append("Data workflow should have a 'process' step for transformation")

        # Should have action for output
        if 'action' not in step_types:
            warnings.append("Data workflow should have an 'action' step for output")

        return errors, warnings

    def _validate_approval_workflow(self, workflow: Dict) -> Tuple[List[str], List[str]]:
        """Validate approval workflow"""
        errors = []
        warnings = []

        steps = workflow.get('steps', [])
        step_types = {step.get('type') for step in steps}

        # Must have decision point
        if 'decision' not in step_types:
            errors.append("Approval workflow must have at least one 'decision' step for approval logic")

        # Should have action for submission
        if 'action' not in step_types:
            warnings.append("Approval workflow should have an 'action' step for request submission")

        # Should have notification
        if 'notification' not in step_types:
            warnings.append("Approval workflow should notify stakeholders of decisions")

        return errors, warnings

    def _validate_notification_workflow(self, workflow: Dict) -> Tuple[List[str], List[str]]:
        """Validate notification system workflow"""
        errors = []
        warnings = []

        steps = workflow.get('steps', [])
        step_types = {step.get('type') for step in steps}

        # Must have notification step
        if 'notification' not in step_types:
            errors.append("Notification workflow must have at least one 'notification' step")

        # Should have process for event monitoring
        if 'process' not in step_types:
            warnings.append("Notification workflow should have a 'process' step for event monitoring")

        # Should have decision for filtering
        if 'decision' not in step_types:
            warnings.append("Notification workflow should have a 'decision' step for filtering events")

        return errors, warnings

    def _validate_best_practices(self, workflow: Dict) -> List[str]:
        """Validate against best practices"""
        warnings = []

        steps = workflow.get('steps', [])

        # Check workflow size
        if len(steps) < 2:
            warnings.append("Best practice: Workflows should have at least 2 steps")
        elif len(steps) > 10:
            warnings.append("Best practice: Consider breaking down workflows with more than 10 steps")

        # Check for error handling
        has_error_handling = any(
            'error' in step.get('name', '').lower() or
            'error' in step.get('description', '').lower() or
            'exception' in step.get('description', '').lower()
            for step in steps
        )
        if not has_error_handling and len(steps) > 3:
            warnings.append("Best practice: Consider adding error handling steps")

        # Check for logging/monitoring
        has_monitoring = any(
            'log' in step.get('name', '').lower() or
            'monitor' in step.get('name', '').lower() or
            'track' in step.get('name', '').lower()
            for step in steps
        )
        if not has_monitoring and len(steps) > 4:
            warnings.append("Best practice: Consider adding logging or monitoring steps")

        return warnings

    def check_completeness(self, workflow: Dict, intent: str) -> Dict[str, any]:
        """
        Check workflow completeness and return detailed status

        Returns:
            Dict with completeness score, missing elements, and recommendations
        """
        result = {
            "completeness_score": 0.0,
            "missing_elements": [],
            "recommendations": [],
            "is_deployable": False
        }

        if not workflow:
            result['missing_elements'].append("Entire workflow specification")
            result['recommendations'].append("Start by defining workflow steps")
            return result

        score = 0.0
        max_score = 1.0

        # Steps defined (30%)
        steps = workflow.get('steps', [])
        if steps:
            score += 0.3
        else:
            result['missing_elements'].append("Workflow steps")

        # Steps complete (30%)
        if steps:
            complete_steps = sum(
                1 for step in steps
                if all(field in step for field in self.required_step_fields)
            )
            score += 0.3 * (complete_steps / len(steps))

            incomplete = len(steps) - complete_steps
            if incomplete > 0:
                result['missing_elements'].append(f"{incomplete} incomplete step(s)")

        # Connections defined (10%)
        if workflow.get('connections'):
            score += 0.1
        elif len(steps) > 1:
            result['missing_elements'].append("Step connections")

        # Metadata present (10%)
        if workflow.get('metadata'):
            score += 0.1
        else:
            result['missing_elements'].append("Workflow metadata")

        # Intent-specific requirements (20%)
        is_valid, errors, warnings = self.validate_workflow(workflow, intent)
        if is_valid:
            score += 0.2
        else:
            result['missing_elements'].extend(errors)

        result['completeness_score'] = round(score, 2)

        # Generate recommendations
        if score < 0.5:
            result['recommendations'].append("Define all required workflow steps")
        if score < 0.7:
            result['recommendations'].append("Add step descriptions and configurations")
        if score < 0.9:
            result['recommendations'].append("Connect workflow steps and add metadata")

        # Deployable if score is high and no critical errors
        result['is_deployable'] = score >= 0.8 and is_valid

        return result

    def suggest_improvements(self, workflow: Dict, intent: str) -> List[str]:
        """Suggest specific improvements to the workflow"""
        suggestions = []

        is_valid, errors, warnings = self.validate_workflow(workflow, intent)

        # Add error-based suggestions
        for error in errors:
            suggestions.append(f"Fix: {error}")

        # Add improvement suggestions based on warnings
        for warning in warnings:
            if "missing 'config'" in warning:
                suggestions.append("Add configuration details to complex steps")
            elif "too short" in warning:
                suggestions.append("Expand step descriptions with more details")
            elif "disconnected" in warning:
                suggestions.append("Connect all workflow steps")

        # Add general improvements
        completeness = self.check_completeness(workflow, intent)
        if completeness['completeness_score'] < 1.0:
            suggestions.extend(completeness['recommendations'])

        return suggestions[:5]  # Return top 5 suggestions
