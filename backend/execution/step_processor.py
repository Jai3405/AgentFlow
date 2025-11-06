"""
Step processor for executing individual workflow steps
Handles different step types and integrations
"""

from typing import Dict, Any, Optional, List
import re
import json

from execution.execution_context import ExecutionContext
from integrations.integration_manager import IntegrationManager
from integrations.file_processing.csv_handler import CSVHandler
from integrations.file_processing.json_handler import JSONHandler
from integrations.file_processing.excel_handler import ExcelHandler
from integrations.database.postgres_connector import PostgreSQLConnector
from integrations.database.mysql_connector import MySQLConnector
from integrations.database.mongodb_connector import MongoDBConnector


class StepProcessor:
    """
    Processes individual workflow steps
    Supports various step types and integrations
    """

    def __init__(self, integration_manager: IntegrationManager = None):
        self.integration_manager = integration_manager or IntegrationManager()

        # File processors
        self.csv_handler = CSVHandler()
        self.json_handler = JSONHandler()
        self.excel_handler = ExcelHandler()

        # Database connectors
        self.db_connectors: Dict[str, Any] = {}

    async def process_step(
        self,
        step: Dict[str, Any],
        context: ExecutionContext
    ) -> Any:
        """
        Process a workflow step

        Args:
            step: Step configuration
            context: Execution context

        Returns:
            Step output
        """
        step_type = step.get('type')
        step_id = step.get('id')

        context.set_current_step(step_id)

        try:
            # Route to appropriate handler based on step type
            if step_type == 'email':
                result = await self._process_email_step(step, context)
            elif step_type == 'notification':
                result = await self._process_notification_step(step, context)
            elif step_type == 'webhook':
                result = await self._process_webhook_step(step, context)
            elif step_type == 'database_read':
                result = await self._process_database_read_step(step, context)
            elif step_type == 'database_write':
                result = await self._process_database_write_step(step, context)
            elif step_type == 'file_process':
                result = await self._process_file_step(step, context)
            elif step_type == 'transform':
                result = await self._process_transform_step(step, context)
            elif step_type == 'condition':
                result = await self._process_condition_step(step, context)
            elif step_type == 'loop':
                result = await self._process_loop_step(step, context)
            elif step_type == 'delay':
                result = await self._process_delay_step(step, context)
            elif step_type == 'script':
                result = await self._process_script_step(step, context)
            else:
                raise ValueError(f"Unknown step type: {step_type}")

            context.mark_step_completed(step_id, result)
            return result

        except Exception as e:
            context.mark_step_failed(step_id, str(e))
            raise

    async def _process_email_step(
        self,
        step: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Process email step"""
        config = step.get('config', {})
        action = config.get('action', 'send')

        # Interpolate variables
        config = self._interpolate_variables(config, context)

        if action == 'send':
            provider = config.get('provider', 'gmail')
            result = await self.integration_manager.send_email(
                provider=provider,
                to=config.get('to', []),
                subject=config.get('subject', ''),
                body=config.get('body', ''),
                cc=config.get('cc'),
                bcc=config.get('bcc'),
                attachments=config.get('attachments')
            )
            return result

        elif action == 'fetch':
            provider = config.get('provider', 'gmail')
            emails = await self.integration_manager.fetch_emails(
                provider=provider,
                folder=config.get('folder', 'INBOX'),
                limit=config.get('limit', 10),
                filters=config.get('filters')
            )
            return {'emails': emails, 'count': len(emails)}

        else:
            raise ValueError(f"Unknown email action: {action}")

    async def _process_notification_step(
        self,
        step: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Process notification step"""
        config = step.get('config', {})
        config = self._interpolate_variables(config, context)

        result = await self.integration_manager.send_notification(
            channels=config.get('channels', []),
            message=config.get('message', ''),
            title=config.get('title'),
            priority=config.get('priority', 'normal'),
            recipients=config.get('recipients', {})
        )

        return result

    async def _process_webhook_step(
        self,
        step: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Process webhook step"""
        config = step.get('config', {})
        config = self._interpolate_variables(config, context)

        result = await self.integration_manager.trigger_webhook(
            event_type=config.get('event_type'),
            payload=config.get('payload', {})
        )

        return result

    async def _process_database_read_step(
        self,
        step: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Process database read step"""
        config = step.get('config', {})
        db_type = config.get('database_type')
        db_name = config.get('database_name')

        # Get or create connector
        connector = await self._get_db_connector(db_type, db_name, config.get('credentials'))

        if db_type in ['postgresql', 'mysql']:
            # SQL databases
            if 'query' in config:
                # Custom query
                query = self._interpolate_variables(config['query'], context)
                results = await connector.execute_query(query)
            else:
                # Table fetch
                results = await connector.fetch_table(
                    table_name=config.get('table'),
                    columns=config.get('columns'),
                    limit=config.get('limit', 100),
                    where_clause=config.get('where')
                )

        elif db_type == 'mongodb':
            # MongoDB
            results = await connector.find(
                collection=config.get('collection'),
                query=config.get('query', {}),
                limit=config.get('limit', 100)
            )

        else:
            raise ValueError(f"Unknown database type: {db_type}")

        return {'data': results, 'count': len(results) if results else 0}

    async def _process_database_write_step(
        self,
        step: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Process database write step"""
        config = step.get('config', {})
        db_type = config.get('database_type')
        db_name = config.get('database_name')
        action = config.get('action', 'insert')

        # Get or create connector
        connector = await self._get_db_connector(db_type, db_name, config.get('credentials'))

        # Get data (may reference previous step output)
        data = config.get('data')
        if isinstance(data, str) and data.startswith('$'):
            # Reference to previous step output
            step_ref = data[1:]
            data = context.get_step_output(step_ref)

        if db_type in ['postgresql', 'mysql']:
            if action == 'insert':
                count = await connector.insert_data(config.get('table'), data)
                return {'inserted': count}
            elif action == 'update':
                count = await connector.update_data(
                    table_name=config.get('table'),
                    data=data,
                    where_clause=config.get('where')
                )
                return {'updated': count}
            elif action == 'delete':
                count = await connector.delete_data(
                    table_name=config.get('table'),
                    where_clause=config.get('where')
                )
                return {'deleted': count}

        elif db_type == 'mongodb':
            if action == 'insert':
                if isinstance(data, list):
                    ids = await connector.insert_many(config.get('collection'), data)
                    return {'inserted': len(ids)}
                else:
                    doc_id = await connector.insert_one(config.get('collection'), data)
                    return {'inserted': 1, 'id': doc_id}

        raise ValueError(f"Invalid database write action: {action}")

    async def _process_file_step(
        self,
        step: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Process file processing step"""
        config = step.get('config', {})
        file_type = config.get('file_type')
        action = config.get('action')

        if file_type == 'csv':
            handler = self.csv_handler
        elif file_type == 'json':
            handler = self.json_handler
        elif file_type == 'excel':
            handler = self.excel_handler
        else:
            raise ValueError(f"Unknown file type: {file_type}")

        if action == 'read':
            data = await handler.read_csv(config.get('file_path')) if file_type == 'csv' else \
                   await handler.read_json(config.get('file_path')) if file_type == 'json' else \
                   await handler.read_excel(config.get('file_path'))
            return {'data': data}

        elif action == 'write':
            data = config.get('data')
            if isinstance(data, str) and data.startswith('$'):
                step_ref = data[1:]
                data = context.get_step_output(step_ref)

            await handler.write_csv(data, config.get('file_path')) if file_type == 'csv' else \
            await handler.write_json(data, config.get('file_path')) if file_type == 'json' else \
            await handler.write_excel(data, config.get('file_path'))

            return {'written': True, 'file_path': config.get('file_path')}

        elif action == 'transform':
            data = config.get('data')
            if isinstance(data, str) and data.startswith('$'):
                step_ref = data[1:]
                data = context.get_step_output(step_ref)

            transformations = config.get('transformations', [])
            result = await handler.transform_csv(data, transformations) if file_type == 'csv' else \
                     await handler.transform_json(data, transformations)

            return {'data': result}

        raise ValueError(f"Invalid file action: {action}")

    async def _process_transform_step(
        self,
        step: Dict[str, Any],
        context: ExecutionContext
    ) -> Any:
        """Process data transformation step"""
        config = step.get('config', {})

        # Get input data
        input_data = config.get('input')
        if isinstance(input_data, str) and input_data.startswith('$'):
            step_ref = input_data[1:]
            input_data = context.get_step_output(step_ref)

        # Apply transformations
        transform_type = config.get('type')

        if transform_type == 'map':
            # Map transformation
            mapping = config.get('mapping', {})
            if isinstance(input_data, list):
                return [self._apply_mapping(item, mapping) for item in input_data]
            else:
                return self._apply_mapping(input_data, mapping)

        elif transform_type == 'filter':
            # Filter transformation
            condition = config.get('condition')
            if isinstance(input_data, list):
                return [item for item in input_data if self._evaluate_condition(item, condition)]
            else:
                return input_data if self._evaluate_condition(input_data, condition) else None

        elif transform_type == 'aggregate':
            # Aggregation
            if isinstance(input_data, list):
                operation = config.get('operation')
                field = config.get('field')

                if operation == 'sum':
                    return sum(item.get(field, 0) for item in input_data)
                elif operation == 'count':
                    return len(input_data)
                elif operation == 'avg':
                    values = [item.get(field, 0) for item in input_data]
                    return sum(values) / len(values) if values else 0
                elif operation == 'max':
                    return max(item.get(field, 0) for item in input_data)
                elif operation == 'min':
                    return min(item.get(field, 0) for item in input_data)

        return input_data

    async def _process_condition_step(
        self,
        step: Dict[str, Any],
        context: ExecutionContext
    ) -> bool:
        """Process conditional step"""
        config = step.get('config', {})
        condition = config.get('condition')

        return self._evaluate_condition(context.variables, condition)

    async def _process_loop_step(
        self,
        step: Dict[str, Any],
        context: ExecutionContext
    ) -> List[Any]:
        """Process loop step"""
        config = step.get('config', {})

        # Get items to loop over
        items = config.get('items')
        if isinstance(items, str) and items.startswith('$'):
            step_ref = items[1:]
            items = context.get_step_output(step_ref)

        # For now, just return items (actual loop execution handled by executor)
        return items

    async def _process_delay_step(
        self,
        step: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Process delay step"""
        config = step.get('config', {})
        import asyncio

        duration = config.get('duration', 1)
        await asyncio.sleep(duration)

        return {'delayed': duration}

    async def _process_script_step(
        self,
        step: Dict[str, Any],
        context: ExecutionContext
    ) -> Any:
        """Process custom script step (limited Python execution)"""
        config = step.get('config', {})
        script = config.get('script', '')

        # Very limited execution for safety
        # Only allow basic operations
        allowed_globals = {
            'context': context,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'dict': dict,
            'json': json
        }

        try:
            result = eval(script, {"__builtins__": {}}, allowed_globals)
            return result
        except Exception as e:
            raise ValueError(f"Script execution failed: {str(e)}")

    async def _get_db_connector(self, db_type: str, db_name: str, credentials: Dict):
        """Get or create database connector"""
        key = f"{db_type}:{db_name}"

        if key not in self.db_connectors:
            if db_type == 'postgresql':
                connector = PostgreSQLConnector()
            elif db_type == 'mysql':
                connector = MySQLConnector()
            elif db_type == 'mongodb':
                connector = MongoDBConnector()
            else:
                raise ValueError(f"Unknown database type: {db_type}")

            await connector.connect(credentials)
            self.db_connectors[key] = connector

        return self.db_connectors[key]

    def _interpolate_variables(self, config: Any, context: ExecutionContext) -> Any:
        """Interpolate variables in configuration"""
        if isinstance(config, str):
            # Replace {{variable}} with actual value
            pattern = r'\{\{(\w+)\}\}'
            matches = re.findall(pattern, config)

            for var_name in matches:
                value = context.get_variable(var_name)
                if value is not None:
                    config = config.replace(f'{{{{{var_name}}}}}', str(value))

            # Replace $step_id references
            if config.startswith('$'):
                step_ref = config[1:]
                return context.get_step_output(step_ref)

            return config

        elif isinstance(config, dict):
            return {k: self._interpolate_variables(v, context) for k, v in config.items()}

        elif isinstance(config, list):
            return [self._interpolate_variables(item, context) for item in config]

        return config

    def _apply_mapping(self, item: Dict, mapping: Dict) -> Dict:
        """Apply field mapping to item"""
        result = {}
        for new_key, old_key in mapping.items():
            if old_key in item:
                result[new_key] = item[old_key]
        return result

    def _evaluate_condition(self, data: Any, condition: Dict) -> bool:
        """Evaluate condition"""
        if not condition:
            return True

        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')

        if isinstance(data, dict):
            data_value = data.get(field)
        else:
            data_value = data

        if operator == 'equals':
            return data_value == value
        elif operator == 'not_equals':
            return data_value != value
        elif operator == 'greater_than':
            return data_value > value
        elif operator == 'less_than':
            return data_value < value
        elif operator == 'contains':
            return value in str(data_value)
        elif operator == 'in':
            return data_value in value

        return True
