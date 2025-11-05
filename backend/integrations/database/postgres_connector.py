"""
PostgreSQL database connector
Connect to and query PostgreSQL databases
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("Warning: psycopg2 not installed. PostgreSQL support disabled.")

from integrations.base import BaseIntegration, IntegrationStatus, IntegrationError, AuthenticationError


class PostgreSQLConnector(BaseIntegration):
    """PostgreSQL database connector"""

    def __init__(self):
        super().__init__("PostgreSQL")
        self.connection = None
        self.connection_params = None

    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Connect to PostgreSQL database

        Args:
            credentials: Dict with:
                - host: Database host
                - port: Database port (default 5432)
                - database: Database name
                - user: Username
                - password: Password
                - sslmode: SSL mode (optional)

        Returns:
            True if connection successful
        """
        if not PSYCOPG2_AVAILABLE:
            raise IntegrationError(
                "psycopg2 not installed. Install with: pip install psycopg2-binary",
                "PostgreSQL"
            )

        try:
            self.connection_params = {
                'host': credentials.get('host', 'localhost'),
                'port': credentials.get('port', 5432),
                'database': credentials.get('database'),
                'user': credentials.get('user'),
                'password': credentials.get('password')
            }

            # Add optional parameters
            if 'sslmode' in credentials:
                self.connection_params['sslmode'] = credentials['sslmode']

            # Test connection
            self.connection = psycopg2.connect(**self.connection_params)
            self.connection.close()

            self._set_connected()
            self.metadata.update({
                'host': self.connection_params['host'],
                'database': self.connection_params['database'],
                'port': self.connection_params['port']
            })

            return True

        except psycopg2.Error as e:
            self._set_error(f"PostgreSQL error: {str(e)}")
            raise AuthenticationError(f"Failed to connect to PostgreSQL: {str(e)}", "PostgreSQL")
        except Exception as e:
            self._set_error(str(e))
            raise IntegrationError(f"Failed to connect: {str(e)}", "PostgreSQL")

    async def disconnect(self) -> bool:
        """Disconnect from PostgreSQL"""
        try:
            if self.connection and not self.connection.closed:
                self.connection.close()

            self.connection = None
            self.status = IntegrationStatus.DISCONNECTED
            return True

        except Exception:
            return False

    async def test_connection(self) -> bool:
        """Test if PostgreSQL connection is still valid"""
        try:
            conn = psycopg2.connect(**self.connection_params)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            return True

        except Exception:
            self._set_error("Connection test failed")
            return False

    async def execute_query(
        self,
        query: str,
        params: tuple = None,
        fetch_results: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute SQL query

        Args:
            query: SQL query string
            params: Query parameters (for parameterized queries)
            fetch_results: Whether to fetch and return results

        Returns:
            List of result rows as dicts (if fetch_results=True)
        """
        try:
            conn = psycopg2.connect(**self.connection_params)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            results = None
            if fetch_results:
                results = [dict(row) for row in cursor.fetchall()]

            conn.commit()
            cursor.close()
            conn.close()

            return results

        except psycopg2.Error as e:
            raise IntegrationError(f"Query execution failed: {str(e)}", "PostgreSQL")

    async def execute_many(
        self,
        query: str,
        params_list: List[tuple]
    ) -> int:
        """
        Execute query with multiple parameter sets (batch insert/update)

        Args:
            query: SQL query string
            params_list: List of parameter tuples

        Returns:
            Number of affected rows
        """
        try:
            conn = psycopg2.connect(**self.connection_params)
            cursor = conn.cursor()

            cursor.executemany(query, params_list)

            affected_rows = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()

            return affected_rows

        except psycopg2.Error as e:
            raise IntegrationError(f"Batch execution failed: {str(e)}", "PostgreSQL")

    async def fetch_table(
        self,
        table_name: str,
        columns: List[str] = None,
        limit: int = 100,
        offset: int = 0,
        where_clause: str = None,
        order_by: str = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch data from a table

        Args:
            table_name: Name of table
            columns: List of columns to fetch (None for all)
            limit: Maximum number of rows
            offset: Number of rows to skip
            where_clause: WHERE clause (without WHERE keyword)
            order_by: ORDER BY clause (without ORDER BY keyword)

        Returns:
            List of rows as dicts
        """
        cols = ', '.join(columns) if columns else '*'
        query = f"SELECT {cols} FROM {table_name}"

        if where_clause:
            query += f" WHERE {where_clause}"

        if order_by:
            query += f" ORDER BY {order_by}"

        query += f" LIMIT {limit} OFFSET {offset}"

        return await self.execute_query(query)

    async def insert_data(
        self,
        table_name: str,
        data: List[Dict[str, Any]]
    ) -> int:
        """
        Insert data into table

        Args:
            table_name: Name of table
            data: List of row dicts

        Returns:
            Number of rows inserted
        """
        if not data:
            return 0

        columns = list(data[0].keys())
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)

        query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

        params_list = [tuple(row[col] for col in columns) for row in data]

        return await self.execute_many(query, params_list)

    async def update_data(
        self,
        table_name: str,
        data: Dict[str, Any],
        where_clause: str,
        where_params: tuple = None
    ) -> int:
        """
        Update data in table

        Args:
            table_name: Name of table
            data: Dict of column -> value to update
            where_clause: WHERE clause
            where_params: Parameters for WHERE clause

        Returns:
            Number of rows updated
        """
        set_clause = ', '.join([f"{col} = %s" for col in data.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"

        params = tuple(data.values()) + (where_params if where_params else ())

        result = await self.execute_query(query, params, fetch_results=False)

        return 1  # Affected rows

    async def delete_data(
        self,
        table_name: str,
        where_clause: str,
        where_params: tuple = None
    ) -> int:
        """
        Delete data from table

        Args:
            table_name: Name of table
            where_clause: WHERE clause
            where_params: Parameters for WHERE clause

        Returns:
            Number of rows deleted
        """
        query = f"DELETE FROM {table_name} WHERE {where_clause}"

        await self.execute_query(query, where_params, fetch_results=False)

        return 1  # Affected rows

    async def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get table schema information

        Args:
            table_name: Name of table

        Returns:
            List of column definitions
        """
        query = """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
        """

        return await self.execute_query(query, (table_name,))

    async def list_tables(self, schema: str = 'public') -> List[str]:
        """
        List all tables in schema

        Args:
            schema: Schema name (default 'public')

        Returns:
            List of table names
        """
        query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """

        results = await self.execute_query(query, (schema,))
        return [row['table_name'] for row in results]

    async def execute_transaction(
        self,
        queries: List[Dict[str, Any]]
    ) -> bool:
        """
        Execute multiple queries in a transaction

        Args:
            queries: List of query dicts with 'query' and optional 'params'

        Returns:
            True if transaction successful
        """
        try:
            conn = psycopg2.connect(**self.connection_params)
            cursor = conn.cursor()

            for query_dict in queries:
                query = query_dict['query']
                params = query_dict.get('params')

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

            conn.commit()
            cursor.close()
            conn.close()

            return True

        except psycopg2.Error as e:
            if conn:
                conn.rollback()
                conn.close()
            raise IntegrationError(f"Transaction failed: {str(e)}", "PostgreSQL")
