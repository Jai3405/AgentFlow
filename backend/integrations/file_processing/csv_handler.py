"""
CSV file processing handler
Read, write, and transform CSV files
"""

from typing import List, Dict, Any, Optional, Union
import csv
import io
from pathlib import Path

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Warning: pandas not installed. Advanced CSV features disabled.")


class CSVHandler:
    """Handler for CSV file operations"""

    def __init__(self):
        self.use_pandas = PANDAS_AVAILABLE

    async def read_csv(
        self,
        file_path: str = None,
        content: str = None,
        delimiter: str = ',',
        has_header: bool = True,
        encoding: str = 'utf-8'
    ) -> List[Dict[str, Any]]:
        """
        Read CSV file and return as list of dictionaries

        Args:
            file_path: Path to CSV file
            content: CSV content as string
            delimiter: CSV delimiter
            has_header: Whether CSV has header row
            encoding: File encoding

        Returns:
            List of row dictionaries
        """
        if self.use_pandas and file_path:
            return await self._read_csv_pandas(file_path, delimiter, has_header, encoding)
        else:
            return await self._read_csv_native(file_path, content, delimiter, has_header, encoding)

    async def _read_csv_pandas(
        self,
        file_path: str,
        delimiter: str,
        has_header: bool,
        encoding: str
    ) -> List[Dict[str, Any]]:
        """Read CSV using pandas"""
        try:
            df = pd.read_csv(
                file_path,
                delimiter=delimiter,
                header=0 if has_header else None,
                encoding=encoding
            )

            # Convert to list of dicts
            return df.to_dict('records')

        except Exception as e:
            raise Exception(f"Failed to read CSV with pandas: {str(e)}")

    async def _read_csv_native(
        self,
        file_path: str = None,
        content: str = None,
        delimiter: str = ',',
        has_header: bool = True,
        encoding: str = 'utf-8'
    ) -> List[Dict[str, Any]]:
        """Read CSV using native Python csv module"""
        try:
            if file_path:
                with open(file_path, 'r', encoding=encoding) as f:
                    return await self._parse_csv_content(f, delimiter, has_header)
            elif content:
                f = io.StringIO(content)
                return await self._parse_csv_content(f, delimiter, has_header)
            else:
                raise ValueError("Either file_path or content must be provided")

        except Exception as e:
            raise Exception(f"Failed to read CSV: {str(e)}")

    async def _parse_csv_content(
        self,
        file_obj,
        delimiter: str,
        has_header: bool
    ) -> List[Dict[str, Any]]:
        """Parse CSV content from file object"""
        reader = csv.reader(file_obj, delimiter=delimiter)

        rows = []
        headers = None

        for i, row in enumerate(reader):
            if i == 0 and has_header:
                headers = row
            else:
                if headers:
                    rows.append(dict(zip(headers, row)))
                else:
                    # No headers, use column indices
                    rows.append({f'column_{j}': val for j, val in enumerate(row)})

        return rows

    async def write_csv(
        self,
        data: List[Dict[str, Any]],
        file_path: str = None,
        delimiter: str = ',',
        include_header: bool = True,
        encoding: str = 'utf-8'
    ) -> Union[str, bool]:
        """
        Write data to CSV file

        Args:
            data: List of dictionaries to write
            file_path: Path to output file (if None, returns CSV string)
            delimiter: CSV delimiter
            include_header: Whether to include header row
            encoding: File encoding

        Returns:
            CSV string if file_path is None, otherwise True
        """
        if not data:
            raise ValueError("No data to write")

        if self.use_pandas:
            return await self._write_csv_pandas(data, file_path, delimiter, include_header, encoding)
        else:
            return await self._write_csv_native(data, file_path, delimiter, include_header, encoding)

    async def _write_csv_pandas(
        self,
        data: List[Dict[str, Any]],
        file_path: str,
        delimiter: str,
        include_header: bool,
        encoding: str
    ) -> Union[str, bool]:
        """Write CSV using pandas"""
        try:
            df = pd.DataFrame(data)

            if file_path:
                df.to_csv(
                    file_path,
                    sep=delimiter,
                    header=include_header,
                    index=False,
                    encoding=encoding
                )
                return True
            else:
                return df.to_csv(
                    sep=delimiter,
                    header=include_header,
                    index=False
                )

        except Exception as e:
            raise Exception(f"Failed to write CSV with pandas: {str(e)}")

    async def _write_csv_native(
        self,
        data: List[Dict[str, Any]],
        file_path: str,
        delimiter: str,
        include_header: bool,
        encoding: str
    ) -> Union[str, bool]:
        """Write CSV using native Python csv module"""
        try:
            headers = list(data[0].keys())

            if file_path:
                with open(file_path, 'w', encoding=encoding, newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=headers, delimiter=delimiter)
                    if include_header:
                        writer.writeheader()
                    writer.writerows(data)
                return True
            else:
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=headers, delimiter=delimiter)
                if include_header:
                    writer.writeheader()
                writer.writerows(data)
                return output.getvalue()

        except Exception as e:
            raise Exception(f"Failed to write CSV: {str(e)}")

    async def transform_csv(
        self,
        file_path: str,
        transformations: List[Dict[str, Any]],
        output_path: str = None
    ) -> Union[List[Dict[str, Any]], bool]:
        """
        Apply transformations to CSV data

        Supported transformations:
        - filter: Filter rows by condition
        - select: Select specific columns
        - rename: Rename columns
        - sort: Sort by column(s)
        - aggregate: Group and aggregate

        Args:
            file_path: Input CSV file path
            transformations: List of transformation operations
            output_path: Output file path (if None, returns transformed data)

        Returns:
            Transformed data or True if written to file
        """
        # Read CSV
        data = await self.read_csv(file_path)

        # Apply transformations
        for transform in transformations:
            operation = transform.get('operation')

            if operation == 'filter':
                # Filter rows by condition
                condition = transform.get('condition')
                data = [row for row in data if self._evaluate_condition(row, condition)]

            elif operation == 'select':
                # Select specific columns
                columns = transform.get('columns', [])
                data = [{col: row.get(col) for col in columns} for row in data]

            elif operation == 'rename':
                # Rename columns
                mapping = transform.get('mapping', {})
                data = [{mapping.get(k, k): v for k, v in row.items()} for row in data]

            elif operation == 'sort':
                # Sort by column
                sort_by = transform.get('column')
                reverse = transform.get('descending', False)
                data = sorted(data, key=lambda x: x.get(sort_by, ''), reverse=reverse)

            elif operation == 'aggregate':
                # Group and aggregate (requires pandas)
                if not PANDAS_AVAILABLE:
                    raise Exception("Aggregation requires pandas to be installed")
                data = await self._aggregate_data(data, transform)

        # Write or return
        if output_path:
            await self.write_csv(data, output_path)
            return True
        else:
            return data

    def _evaluate_condition(self, row: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Evaluate filter condition on a row"""
        column = condition.get('column')
        operator = condition.get('operator')
        value = condition.get('value')

        row_value = row.get(column)

        if operator == 'equals':
            return row_value == value
        elif operator == 'not_equals':
            return row_value != value
        elif operator == 'contains':
            return value in str(row_value)
        elif operator == 'greater_than':
            return float(row_value) > float(value)
        elif operator == 'less_than':
            return float(row_value) < float(value)
        elif operator == 'in':
            return row_value in value
        else:
            return True

    async def _aggregate_data(
        self,
        data: List[Dict[str, Any]],
        transform: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Aggregate data using pandas"""
        if not PANDAS_AVAILABLE:
            raise Exception("Pandas required for aggregation")

        df = pd.DataFrame(data)
        group_by = transform.get('group_by', [])
        aggregations = transform.get('aggregations', {})

        grouped = df.groupby(group_by).agg(aggregations).reset_index()
        return grouped.to_dict('records')

    async def merge_csvs(
        self,
        file_paths: List[str],
        merge_type: str = 'concat',
        join_on: str = None,
        output_path: str = None
    ) -> Union[List[Dict[str, Any]], bool]:
        """
        Merge multiple CSV files

        Args:
            file_paths: List of CSV file paths
            merge_type: 'concat' (stack rows) or 'join' (merge on column)
            join_on: Column to join on (for 'join' type)
            output_path: Output file path

        Returns:
            Merged data or True if written to file
        """
        if not file_paths:
            raise ValueError("No files provided")

        if self.use_pandas:
            return await self._merge_csvs_pandas(file_paths, merge_type, join_on, output_path)
        else:
            return await self._merge_csvs_native(file_paths, merge_type, join_on, output_path)

    async def _merge_csvs_pandas(
        self,
        file_paths: List[str],
        merge_type: str,
        join_on: str,
        output_path: str
    ) -> Union[List[Dict[str, Any]], bool]:
        """Merge CSVs using pandas"""
        dfs = [pd.read_csv(fp) for fp in file_paths]

        if merge_type == 'concat':
            merged = pd.concat(dfs, ignore_index=True)
        elif merge_type == 'join' and join_on:
            merged = dfs[0]
            for df in dfs[1:]:
                merged = pd.merge(merged, df, on=join_on, how='outer')
        else:
            raise ValueError("Invalid merge type or missing join column")

        if output_path:
            merged.to_csv(output_path, index=False)
            return True
        else:
            return merged.to_dict('records')

    async def _merge_csvs_native(
        self,
        file_paths: List[str],
        merge_type: str,
        join_on: str,
        output_path: str
    ) -> Union[List[Dict[str, Any]], bool]:
        """Merge CSVs using native Python"""
        if merge_type != 'concat':
            raise Exception("Join merge requires pandas. Use merge_type='concat' or install pandas.")

        merged_data = []
        for fp in file_paths:
            data = await self.read_csv(fp)
            merged_data.extend(data)

        if output_path:
            await self.write_csv(merged_data, output_path)
            return True
        else:
            return merged_data

    async def validate_csv(
        self,
        file_path: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate CSV against schema

        Args:
            file_path: CSV file path
            schema: Validation schema with column requirements

        Returns:
            Validation result with errors
        """
        data = await self.read_csv(file_path)

        if not data:
            return {
                'valid': False,
                'errors': ['CSV file is empty']
            }

        errors = []
        required_columns = schema.get('required_columns', [])
        column_types = schema.get('column_types', {})

        # Check required columns
        first_row = data[0]
        missing_columns = [col for col in required_columns if col not in first_row]
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")

        # Validate column types
        for col, expected_type in column_types.items():
            if col in first_row:
                for i, row in enumerate(data):
                    value = row.get(col)
                    if not self._validate_type(value, expected_type):
                        errors.append(f"Row {i+1}: Column '{col}' has invalid type (expected {expected_type})")
                        break  # Only report first error per column

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'row_count': len(data),
            'column_count': len(first_row.keys())
        }

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type"""
        try:
            if expected_type == 'string':
                return isinstance(value, str)
            elif expected_type == 'integer':
                int(value)
                return True
            elif expected_type == 'float':
                float(value)
                return True
            elif expected_type == 'boolean':
                return value.lower() in ['true', 'false', '1', '0']
            else:
                return True
        except:
            return False
