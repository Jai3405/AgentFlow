"""
MySQL database connector
Connect to and query MySQL databases
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    print("Warning: mysql-connector-python not installed. MySQL support disabled.")

from integrations.base import BaseIntegration, IntegrationStatus, IntegrationError, AuthenticationError


class MySQLConnector(BaseIntegration):
    """MySQL database connector"""

    def __init__(self):
        super().__init__("MySQL")
        self.connection = None
        self.connection_params = None

    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Connect to MySQL database

        Args:
            credentials: Dict with:
                - host: Database host
                - port: Database port (default 3306)
                - database: Database name
                - user: Username
                - password: Password
                - ssl_ca: SSL CA cert path (optional)

        Returns:
            True if connection successful
        """
        if not MYSQL_AVAILABLE:
            raise IntegrationError(
                "mysql-connector-python not installed. Install with: pip install mysql-connector-python",
                "MySQL"
            )

        try:
            self.connection_params = {
                'host': credentials.get('host', 'localhost'),
                'port': credentials.get('port', 3306),
                'database': credentials.get('database'),
                'user': credentials.get('user'),
                'password': credentials.get('password')
            }

            # Add optional SSL
            if 'ssl_ca' in credentials:
                self.connection_params['ssl_ca'] = credentials['ssl_ca']

            # Test connection
            conn = mysql.connector.connect(**self.connection_params)
            conn.close()

            self._set_connected()
            self.metadata.update({
                'host': self.connection_params['host'],
                'database': self.connection_params['database'],
                'port': self.connection_params['port']
            })

            return True

        except MySQLError as e:
            self._set_error(f"MySQL error: {str(e)}")
            raise AuthenticationError(f"Failed to connect to MySQL: {str(e)}", "MySQL")
        except Exception as e:
            self._set_error(str(e))
            raise IntegrationError(f"Failed to connect: {str(e)}", "MySQL")

    async def disconnect(self) -> bool:
        """Disconnect from MySQL"""
        try:
            if self.connection and self.connection.is_connected():
                self.connection.close()

            self.connection = None
            self.status = IntegrationStatus.DISCONNECTED
            return True

        except Exception:
            return False

    async def test_connection(self) -> bool:
        """Test if MySQL connection is still valid"""
        try:
            conn = mysql.connector.connect(**self.connection_params)
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
            params: Query parameters
            fetch_results: Whether to fetch and return results

        Returns:
            List of result rows as dicts (if fetch_results=True)
        """
        try:
            conn = mysql.connector.connect(**self.connection_params)
            cursor = conn.cursor(dictionary=True)

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            results = None
            if fetch_results:
                results = cursor.fetchall()

            conn.commit()
            cursor.close()
            conn.close()

            return results

        except MySQLError as e:
            raise IntegrationError(f"Query execution failed: {str(e)}", "MySQL")

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
            conn = mysql.connector.connect(**self.connection_params)
            cursor = conn.cursor()

            cursor.executemany(query, params_list)

            affected_rows = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()

            return affected_rows

        except MySQLError as e:
            raise IntegrationError(f"Batch execution failed: {str(e)}", "MySQL")

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

        await self.execute_query(query, params, fetch_results=False)

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
        query = f"DESCRIBE {table_name}"

        return await self.execute_query(query)

    async def list_tables(self) -> List[str]:
        """
        List all tables in database

        Returns:
            List of table names
        """
        query = "SHOW TABLES"

        results = await self.execute_query(query)
        # MySQL returns table names in a dict with key like 'Tables_in_dbname'
        if results:
            key = list(results[0].keys())[0]
            return [row[key] for row in results]
        return []

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
            conn = mysql.connector.connect(**self.connection_params)
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

        except MySQLError as e:
            if conn:
                conn.rollback()
                conn.close()
            raise IntegrationError(f"Transaction failed: {str(e)}", "MySQL")
