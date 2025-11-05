"""
JSON file processing handler
Read, write, validate, and transform JSON data
"""

from typing import List, Dict, Any, Optional, Union
import json
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError


class JSONHandler:
    """Handler for JSON file operations"""

    def __init__(self):
        pass

    async def read_json(
        self,
        file_path: str = None,
        content: str = None,
        encoding: str = 'utf-8'
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Read JSON file or string

        Args:
            file_path: Path to JSON file
            content: JSON content as string
            encoding: File encoding

        Returns:
            Parsed JSON data
        """
        try:
            if file_path:
                with open(file_path, 'r', encoding=encoding) as f:
                    return json.load(f)
            elif content:
                return json.loads(content)
            else:
                raise ValueError("Either file_path or content must be provided")

        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to read JSON: {str(e)}")

    async def write_json(
        self,
        data: Union[Dict[str, Any], List[Any]],
        file_path: str = None,
        indent: int = 2,
        encoding: str = 'utf-8',
        sort_keys: bool = False
    ) -> Union[str, bool]:
        """
        Write data to JSON file or string

        Args:
            data: Data to write
            file_path: Output file path (if None, returns JSON string)
            indent: Indentation spaces
            encoding: File encoding
            sort_keys: Whether to sort keys

        Returns:
            JSON string if file_path is None, otherwise True
        """
        try:
            if file_path:
                with open(file_path, 'w', encoding=encoding) as f:
                    json.dump(data, f, indent=indent, sort_keys=sort_keys)
                return True
            else:
                return json.dumps(data, indent=indent, sort_keys=sort_keys)

        except Exception as e:
            raise Exception(f"Failed to write JSON: {str(e)}")

    async def validate_json(
        self,
        data: Union[Dict[str, Any], List[Any]],
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate JSON data against JSON Schema

        Args:
            data: JSON data to validate
            schema: JSON Schema definition

        Returns:
            Validation result with errors
        """
        try:
            validate(instance=data, schema=schema)
            return {
                'valid': True,
                'errors': []
            }
        except ValidationError as e:
            return {
                'valid': False,
                'errors': [str(e.message)],
                'path': list(e.path)
            }
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"]
            }

    async def transform_json(
        self,
        data: Union[Dict[str, Any], List[Any]],
        transformations: List[Dict[str, Any]]
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Apply transformations to JSON data

        Supported transformations:
        - extract: Extract specific fields
        - filter: Filter array elements
        - map: Transform array elements
        - flatten: Flatten nested structure
        - unflatten: Unflatten dotted keys

        Args:
            data: Input JSON data
            transformations: List of transformation operations

        Returns:
            Transformed data
        """
        result = data

        for transform in transformations:
            operation = transform.get('operation')

            if operation == 'extract':
                # Extract specific fields
                paths = transform.get('paths', [])
                result = self._extract_fields(result, paths)

            elif operation == 'filter':
                # Filter array elements
                if isinstance(result, list):
                    condition = transform.get('condition')
                    result = [item for item in result if self._evaluate_condition(item, condition)]

            elif operation == 'map':
                # Transform array elements
                if isinstance(result, list):
                    mapping = transform.get('mapping', {})
                    result = [self._apply_mapping(item, mapping) for item in result]

            elif operation == 'flatten':
                # Flatten nested structure
                separator = transform.get('separator', '.')
                result = self._flatten_dict(result, separator)

            elif operation == 'unflatten':
                # Unflatten dotted keys
                separator = transform.get('separator', '.')
                result = self._unflatten_dict(result, separator)

        return result

    def _extract_fields(
        self,
        data: Union[Dict, List],
        paths: List[str]
    ) -> Dict[str, Any]:
        """Extract specific fields from JSON using dot notation"""
        extracted = {}

        for path in paths:
            value = self._get_nested_value(data, path)
            if value is not None:
                extracted[path] = value

        return extracted

    def _get_nested_value(self, data: Any, path: str) -> Any:
        """Get nested value using dot notation path"""
        keys = path.split('.')
        value = data

        try:
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                elif isinstance(value, list) and key.isdigit():
                    value = value[int(key)]
                else:
                    return None

            return value
        except:
            return None

    def _evaluate_condition(self, item: Any, condition: Dict[str, Any]) -> bool:
        """Evaluate filter condition on an item"""
        if not condition:
            return True

        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')

        item_value = self._get_nested_value(item, field) if isinstance(item, dict) else item

        if operator == 'equals':
            return item_value == value
        elif operator == 'not_equals':
            return item_value != value
        elif operator == 'contains':
            return value in str(item_value)
        elif operator == 'greater_than':
            return float(item_value) > float(value)
        elif operator == 'less_than':
            return float(item_value) < float(value)
        elif operator == 'in':
            return item_value in value
        elif operator == 'exists':
            return item_value is not None
        else:
            return True

    def _apply_mapping(self, item: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
        """Apply field mapping to an item"""
        mapped = {}

        for new_key, old_key in mapping.items():
            value = self._get_nested_value(item, old_key)
            if value is not None:
                mapped[new_key] = value

        return mapped

    def _flatten_dict(
        self,
        data: Dict[str, Any],
        separator: str = '.',
        parent_key: str = ''
    ) -> Dict[str, Any]:
        """Flatten nested dictionary"""
        items = []

        for k, v in data.items():
            new_key = f"{parent_key}{separator}{k}" if parent_key else k

            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, separator, new_key).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, separator, f"{new_key}{separator}{i}").items())
                    else:
                        items.append((f"{new_key}{separator}{i}", item))
            else:
                items.append((new_key, v))

        return dict(items)

    def _unflatten_dict(
        self,
        data: Dict[str, Any],
        separator: str = '.'
    ) -> Dict[str, Any]:
        """Unflatten dictionary with dotted keys"""
        result = {}

        for key, value in data.items():
            parts = key.split(separator)
            d = result

            for part in parts[:-1]:
                if part not in d:
                    d[part] = {}
                d = d[part]

            d[parts[-1]] = value

        return result

    async def merge_json(
        self,
        json_objects: List[Union[Dict, List]],
        merge_strategy: str = 'deep'
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Merge multiple JSON objects

        Args:
            json_objects: List of JSON objects to merge
            merge_strategy: 'shallow' or 'deep'

        Returns:
            Merged JSON object
        """
        if not json_objects:
            return {}

        if merge_strategy == 'shallow':
            result = {}
            for obj in json_objects:
                if isinstance(obj, dict):
                    result.update(obj)
            return result
        else:
            # Deep merge
            result = json_objects[0]
            for obj in json_objects[1:]:
                result = self._deep_merge(result, obj)
            return result

    def _deep_merge(self, base: Any, update: Any) -> Any:
        """Deep merge two objects"""
        if isinstance(base, dict) and isinstance(update, dict):
            merged = base.copy()
            for key, value in update.items():
                if key in merged:
                    merged[key] = self._deep_merge(merged[key], value)
                else:
                    merged[key] = value
            return merged
        elif isinstance(base, list) and isinstance(update, list):
            return base + update
        else:
            return update

    async def convert_to_json(
        self,
        data: List[Dict[str, Any]],
        format_type: str = 'array'
    ) -> Dict[str, Any]:
        """
        Convert structured data to JSON format

        Args:
            data: List of dictionaries
            format_type: 'array', 'object', or 'nested'

        Returns:
            Formatted JSON object
        """
        if format_type == 'array':
            return {'data': data}
        elif format_type == 'object':
            # Convert to object with index keys
            return {str(i): item for i, item in enumerate(data)}
        elif format_type == 'nested':
            # Group by first key
            if not data or not isinstance(data[0], dict):
                return {'data': data}

            first_key = list(data[0].keys())[0]
            nested = {}
            for item in data:
                key_value = item.get(first_key)
                if key_value not in nested:
                    nested[key_value] = []
                nested[key_value].append(item)

            return nested
        else:
            return {'data': data}

    async def json_to_csv_format(
        self,
        data: Union[Dict[str, Any], List[Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert JSON to CSV-compatible format (flatten to list of dicts)

        Args:
            data: JSON data

        Returns:
            List of flat dictionaries
        """
        if isinstance(data, list):
            # Already list format
            result = []
            for item in data:
                if isinstance(item, dict):
                    result.append(self._flatten_dict(item))
                else:
                    result.append({'value': item})
            return result

        elif isinstance(data, dict):
            # Convert single dict to list
            flattened = self._flatten_dict(data)
            return [flattened]

        else:
            return [{'value': data}]

    async def query_json(
        self,
        data: Union[Dict, List],
        query: str
    ) -> Any:
        """
        Query JSON using JSONPath-like syntax (simplified)

        Args:
            data: JSON data
            query: Query string (e.g., "users[0].name")

        Returns:
            Query result
        """
        # Simple implementation - supports dot notation and array indexing
        return self._get_nested_value(data, query)
