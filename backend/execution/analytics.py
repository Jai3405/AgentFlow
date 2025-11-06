"""
Workflow execution analytics and monitoring
Provides insights into workflow performance and health
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class ExecutionAnalytics:
    """
    Analytics engine for workflow executions
    Tracks metrics, performance, and provides insights
    """

    def __init__(self):
        # In-memory storage (in production, would use database)
        self.execution_history: List[Dict[str, Any]] = []
        self.workflow_metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_execution_time': 0.0,
            'avg_execution_time': 0.0,
            'last_execution': None,
            'error_types': defaultdict(int)
        })

    def record_execution(self, context_dict: Dict[str, Any]):
        """Record an execution for analytics"""
        self.execution_history.append(context_dict)

        workflow_id = context_dict.get('workflow_id')
        metrics = self.workflow_metrics[workflow_id]

        # Update counts
        metrics['total_executions'] += 1

        if context_dict.get('status') == 'completed':
            metrics['successful_executions'] += 1
        elif context_dict.get('status') == 'failed':
            metrics['failed_executions'] += 1

            # Track error type
            errors = context_dict.get('errors', [])
            if errors:
                error_type = errors[0].get('source', 'unknown')
                metrics['error_types'][error_type] += 1

        # Update timing
        execution_time = context_dict.get('execution_time')
        if execution_time:
            metrics['total_execution_time'] += execution_time
            metrics['avg_execution_time'] = metrics['total_execution_time'] / metrics['total_executions']

        # Update last execution
        metrics['last_execution'] = context_dict.get('completed_at') or context_dict.get('started_at')

    def get_workflow_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get metrics for a specific workflow

        Returns:
            Dict with execution stats and performance metrics
        """
        if workflow_id not in self.workflow_metrics:
            return {
                'workflow_id': workflow_id,
                'total_executions': 0,
                'message': 'No executions found for this workflow'
            }

        metrics = self.workflow_metrics[workflow_id]

        success_rate = (
            metrics['successful_executions'] / metrics['total_executions']
            if metrics['total_executions'] > 0
            else 0
        )

        return {
            'workflow_id': workflow_id,
            'total_executions': metrics['total_executions'],
            'successful_executions': metrics['successful_executions'],
            'failed_executions': metrics['failed_executions'],
            'success_rate': round(success_rate * 100, 2),
            'avg_execution_time_seconds': round(metrics['avg_execution_time'], 2),
            'total_execution_time_seconds': round(metrics['total_execution_time'], 2),
            'last_execution': metrics['last_execution'],
            'top_errors': dict(sorted(
                metrics['error_types'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5])
        }

    def get_overall_metrics(self) -> Dict[str, Any]:
        """
        Get overall system metrics

        Returns:
            Aggregated metrics across all workflows
        """
        total_executions = sum(m['total_executions'] for m in self.workflow_metrics.values())
        total_successful = sum(m['successful_executions'] for m in self.workflow_metrics.values())
        total_failed = sum(m['failed_executions'] for m in self.workflow_metrics.values())
        total_time = sum(m['total_execution_time'] for m in self.workflow_metrics.values())

        success_rate = total_successful / total_executions if total_executions > 0 else 0
        avg_time = total_time / total_executions if total_executions > 0 else 0

        # Find most active workflows
        most_active = sorted(
            [
                {'workflow_id': wid, 'executions': m['total_executions']}
                for wid, m in self.workflow_metrics.items()
            ],
            key=lambda x: x['executions'],
            reverse=True
        )[:5]

        # Find workflows with highest error rate
        error_prone = sorted(
            [
                {
                    'workflow_id': wid,
                    'error_rate': round(m['failed_executions'] / m['total_executions'] * 100, 2)
                }
                for wid, m in self.workflow_metrics.items()
                if m['total_executions'] > 0
            ],
            key=lambda x: x['error_rate'],
            reverse=True
        )[:5]

        return {
            'total_workflows': len(self.workflow_metrics),
            'total_executions': total_executions,
            'successful_executions': total_successful,
            'failed_executions': total_failed,
            'success_rate': round(success_rate * 100, 2),
            'avg_execution_time_seconds': round(avg_time, 2),
            'most_active_workflows': most_active,
            'error_prone_workflows': error_prone
        }

    def get_execution_trends(
        self,
        workflow_id: Optional[str] = None,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get execution trends over time

        Args:
            workflow_id: Optional workflow filter
            time_window_hours: Time window for analysis

        Returns:
            Trend data with hourly buckets
        """
        now = datetime.now()
        cutoff_time = now - timedelta(hours=time_window_hours)

        # Filter executions
        relevant_executions = [
            ex for ex in self.execution_history
            if (not workflow_id or ex.get('workflow_id') == workflow_id)
            and ex.get('started_at')
            and datetime.fromisoformat(ex['started_at']) >= cutoff_time
        ]

        # Group by hour
        hourly_buckets = defaultdict(lambda: {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'avg_duration': 0.0,
            'durations': []
        })

        for ex in relevant_executions:
            started_at = datetime.fromisoformat(ex['started_at'])
            hour_key = started_at.replace(minute=0, second=0, microsecond=0)

            bucket = hourly_buckets[hour_key]
            bucket['total'] += 1

            if ex.get('status') == 'completed':
                bucket['successful'] += 1
            elif ex.get('status') == 'failed':
                bucket['failed'] += 1

            if ex.get('execution_time'):
                bucket['durations'].append(ex['execution_time'])

        # Calculate averages
        for bucket in hourly_buckets.values():
            if bucket['durations']:
                bucket['avg_duration'] = sum(bucket['durations']) / len(bucket['durations'])
            del bucket['durations']

        # Convert to sorted list
        trends = [
            {
                'timestamp': hour.isoformat(),
                **data
            }
            for hour, data in sorted(hourly_buckets.items())
        ]

        return {
            'time_window_hours': time_window_hours,
            'workflow_id': workflow_id,
            'total_executions': len(relevant_executions),
            'trends': trends
        }

    def get_step_performance(self, workflow_id: str) -> Dict[str, Any]:
        """
        Analyze performance of individual workflow steps

        Args:
            workflow_id: Workflow to analyze

        Returns:
            Performance metrics per step
        """
        # Get executions for workflow
        workflow_executions = [
            ex for ex in self.execution_history
            if ex.get('workflow_id') == workflow_id
        ]

        if not workflow_executions:
            return {
                'workflow_id': workflow_id,
                'message': 'No executions found'
            }

        # Analyze step completion rates
        step_metrics = defaultdict(lambda: {
            'total_attempts': 0,
            'completions': 0,
            'failures': 0,
            'completion_rate': 0.0
        })

        for ex in workflow_executions:
            completed = ex.get('completed_steps', [])
            failed = ex.get('failed_steps', [])

            all_steps = set(completed + failed)

            for step in all_steps:
                step_metrics[step]['total_attempts'] += 1

                if step in completed:
                    step_metrics[step]['completions'] += 1
                elif step in failed:
                    step_metrics[step]['failures'] += 1

        # Calculate rates
        for metrics in step_metrics.values():
            if metrics['total_attempts'] > 0:
                metrics['completion_rate'] = round(
                    metrics['completions'] / metrics['total_attempts'] * 100,
                    2
                )

        return {
            'workflow_id': workflow_id,
            'total_executions': len(workflow_executions),
            'step_metrics': dict(step_metrics)
        }

    def get_error_analysis(
        self,
        workflow_id: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze errors and failures

        Args:
            workflow_id: Optional workflow filter
            limit: Max errors to return

        Returns:
            Error analysis with frequencies
        """
        # Get failed executions
        failed_executions = [
            ex for ex in self.execution_history
            if ex.get('status') == 'failed'
            and (not workflow_id or ex.get('workflow_id') == workflow_id)
        ]

        # Group errors
        error_frequencies = defaultdict(int)
        error_examples = defaultdict(list)

        for ex in failed_executions:
            errors = ex.get('errors', [])
            for error in errors:
                error_msg = error.get('error', 'Unknown error')
                error_source = error.get('source', 'unknown')

                key = f"{error_source}: {error_msg[:100]}"
                error_frequencies[key] += 1

                if len(error_examples[key]) < 3:
                    error_examples[key].append({
                        'execution_id': ex.get('execution_id'),
                        'timestamp': error.get('timestamp'),
                        'full_error': error_msg
                    })

        # Sort by frequency
        top_errors = sorted(
            [
                {
                    'error': error,
                    'frequency': count,
                    'examples': error_examples[error]
                }
                for error, count in error_frequencies.items()
            ],
            key=lambda x: x['frequency'],
            reverse=True
        )[:limit]

        return {
            'workflow_id': workflow_id,
            'total_failures': len(failed_executions),
            'unique_errors': len(error_frequencies),
            'top_errors': top_errors
        }

    def get_performance_summary(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get comprehensive performance summary for a workflow

        Args:
            workflow_id: Workflow to analyze

        Returns:
            Complete performance summary
        """
        workflow_metrics = self.get_workflow_metrics(workflow_id)
        step_performance = self.get_step_performance(workflow_id)
        error_analysis = self.get_error_analysis(workflow_id=workflow_id)

        # Get recent executions
        recent = [
            {
                'execution_id': ex.get('execution_id'),
                'status': ex.get('status'),
                'execution_time': ex.get('execution_time'),
                'started_at': ex.get('started_at')
            }
            for ex in self.execution_history
            if ex.get('workflow_id') == workflow_id
        ][-10:]  # Last 10

        return {
            'workflow_id': workflow_id,
            'overview': workflow_metrics,
            'step_performance': step_performance.get('step_metrics', {}),
            'error_analysis': error_analysis,
            'recent_executions': recent
        }

    def clear_history(self, workflow_id: Optional[str] = None):
        """Clear execution history"""
        if workflow_id:
            self.execution_history = [
                ex for ex in self.execution_history
                if ex.get('workflow_id') != workflow_id
            ]
            if workflow_id in self.workflow_metrics:
                del self.workflow_metrics[workflow_id]
        else:
            self.execution_history.clear()
            self.workflow_metrics.clear()
