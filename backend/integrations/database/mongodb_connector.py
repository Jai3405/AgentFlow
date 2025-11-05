"""
MongoDB database connector
Connect to and query MongoDB databases
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError, ConnectionFailure
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    print("Warning: pymongo not installed. MongoDB support disabled.")

from integrations.base import BaseIntegration, IntegrationStatus, IntegrationError, AuthenticationError


class MongoDBConnector(BaseIntegration):
    """MongoDB database connector"""

    def __init__(self):
        super().__init__("MongoDB")
        self.client = None
        self.db = None
        self.connection_string = None

    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Connect to MongoDB database

        Args:
            credentials: Dict with either:
                - connection_string: Full MongoDB connection string
                OR
                - host: MongoDB host
                - port: MongoDB port (default 27017)
                - database: Database name
                - username: Username (optional)
                - password: Password (optional)

        Returns:
            True if connection successful
        """
        if not PYMONGO_AVAILABLE:
            raise IntegrationError(
                "pymongo not installed. Install with: pip install pymongo",
                "MongoDB"
            )

        try:
            # Build connection string
            if 'connection_string' in credentials:
                self.connection_string = credentials['connection_string']
                database_name = credentials.get('database', 'test')
            else:
                host = credentials.get('host', 'localhost')
                port = credentials.get('port', 27017)
                database_name = credentials.get('database', 'test')
                username = credentials.get('username')
                password = credentials.get('password')

                if username and password:
                    self.connection_string = f"mongodb://{username}:{password}@{host}:{port}/{database_name}"
                else:
                    self.connection_string = f"mongodb://{host}:{port}/{database_name}"

            # Test connection
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')

            self.db = self.client[database_name]

            self._set_connected()
            self.metadata.update({
                'database': database_name,
                'server_info': self.client.server_info()
            })

            return True

        except ConnectionFailure as e:
            self._set_error(f"MongoDB connection failed: {str(e)}")
            raise AuthenticationError(f"Failed to connect to MongoDB: {str(e)}", "MongoDB")
        except Exception as e:
            self._set_error(str(e))
            raise IntegrationError(f"Failed to connect: {str(e)}", "MongoDB")

    async def disconnect(self) -> bool:
        """Disconnect from MongoDB"""
        try:
            if self.client:
                self.client.close()

            self.client = None
            self.db = None
            self.status = IntegrationStatus.DISCONNECTED
            return True

        except Exception:
            return False

    async def test_connection(self) -> bool:
        """Test if MongoDB connection is still valid"""
        try:
            if not self.client:
                return False

            self.client.admin.command('ping')
            return True

        except Exception:
            self._set_error("Connection test failed")
            return False

    async def find(
        self,
        collection: str,
        query: Dict[str, Any] = None,
        projection: Dict[str, int] = None,
        limit: int = 100,
        skip: int = 0,
        sort: List[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Find documents in collection

        Args:
            collection: Collection name
            query: MongoDB query filter
            projection: Fields to include/exclude
            limit: Maximum number of documents
            skip: Number of documents to skip
            sort: Sort specification [(field, direction), ...]

        Returns:
            List of documents
        """
        try:
            coll = self.db[collection]

            cursor = coll.find(query or {}, projection)

            if skip:
                cursor = cursor.skip(skip)

            if limit:
                cursor = cursor.limit(limit)

            if sort:
                cursor = cursor.sort(sort)

            results = list(cursor)

            # Convert ObjectId to string
            for doc in results:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])

            return results

        except PyMongoError as e:
            raise IntegrationError(f"Query execution failed: {str(e)}", "MongoDB")

    async def find_one(
        self,
        collection: str,
        query: Dict[str, Any] = None,
        projection: Dict[str, int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find single document in collection

        Args:
            collection: Collection name
            query: MongoDB query filter
            projection: Fields to include/exclude

        Returns:
            Single document or None
        """
        try:
            coll = self.db[collection]
            doc = coll.find_one(query or {}, projection)

            if doc and '_id' in doc:
                doc['_id'] = str(doc['_id'])

            return doc

        except PyMongoError as e:
            raise IntegrationError(f"Query execution failed: {str(e)}", "MongoDB")

    async def insert_one(
        self,
        collection: str,
        document: Dict[str, Any]
    ) -> str:
        """
        Insert single document

        Args:
            collection: Collection name
            document: Document to insert

        Returns:
            Inserted document ID
        """
        try:
            coll = self.db[collection]
            result = coll.insert_one(document)
            return str(result.inserted_id)

        except PyMongoError as e:
            raise IntegrationError(f"Insert failed: {str(e)}", "MongoDB")

    async def insert_many(
        self,
        collection: str,
        documents: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Insert multiple documents

        Args:
            collection: Collection name
            documents: List of documents to insert

        Returns:
            List of inserted document IDs
        """
        try:
            coll = self.db[collection]
            result = coll.insert_many(documents)
            return [str(id) for id in result.inserted_ids]

        except PyMongoError as e:
            raise IntegrationError(f"Bulk insert failed: {str(e)}", "MongoDB")

    async def update_one(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ) -> int:
        """
        Update single document

        Args:
            collection: Collection name
            query: Query filter
            update: Update operations
            upsert: Create if not exists

        Returns:
            Number of modified documents
        """
        try:
            coll = self.db[collection]
            result = coll.update_one(query, update, upsert=upsert)
            return result.modified_count

        except PyMongoError as e:
            raise IntegrationError(f"Update failed: {str(e)}", "MongoDB")

    async def update_many(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ) -> int:
        """
        Update multiple documents

        Args:
            collection: Collection name
            query: Query filter
            update: Update operations
            upsert: Create if not exists

        Returns:
            Number of modified documents
        """
        try:
            coll = self.db[collection]
            result = coll.update_many(query, update, upsert=upsert)
            return result.modified_count

        except PyMongoError as e:
            raise IntegrationError(f"Bulk update failed: {str(e)}", "MongoDB")

    async def delete_one(
        self,
        collection: str,
        query: Dict[str, Any]
    ) -> int:
        """
        Delete single document

        Args:
            collection: Collection name
            query: Query filter

        Returns:
            Number of deleted documents
        """
        try:
            coll = self.db[collection]
            result = coll.delete_one(query)
            return result.deleted_count

        except PyMongoError as e:
            raise IntegrationError(f"Delete failed: {str(e)}", "MongoDB")

    async def delete_many(
        self,
        collection: str,
        query: Dict[str, Any]
    ) -> int:
        """
        Delete multiple documents

        Args:
            collection: Collection name
            query: Query filter

        Returns:
            Number of deleted documents
        """
        try:
            coll = self.db[collection]
            result = coll.delete_many(query)
            return result.deleted_count

        except PyMongoError as e:
            raise IntegrationError(f"Bulk delete failed: {str(e)}", "MongoDB")

    async def count_documents(
        self,
        collection: str,
        query: Dict[str, Any] = None
    ) -> int:
        """
        Count documents matching query

        Args:
            collection: Collection name
            query: Query filter

        Returns:
            Document count
        """
        try:
            coll = self.db[collection]
            return coll.count_documents(query or {})

        except PyMongoError as e:
            raise IntegrationError(f"Count failed: {str(e)}", "MongoDB")

    async def aggregate(
        self,
        collection: str,
        pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute aggregation pipeline

        Args:
            collection: Collection name
            pipeline: Aggregation pipeline stages

        Returns:
            Aggregation results
        """
        try:
            coll = self.db[collection]
            results = list(coll.aggregate(pipeline))

            # Convert ObjectId to string
            for doc in results:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])

            return results

        except PyMongoError as e:
            raise IntegrationError(f"Aggregation failed: {str(e)}", "MongoDB")

    async def list_collections(self) -> List[str]:
        """
        List all collections in database

        Returns:
            List of collection names
        """
        try:
            return self.db.list_collection_names()

        except PyMongoError as e:
            raise IntegrationError(f"Failed to list collections: {str(e)}", "MongoDB")

    async def create_index(
        self,
        collection: str,
        keys: List[tuple],
        unique: bool = False
    ) -> str:
        """
        Create index on collection

        Args:
            collection: Collection name
            keys: Index keys [(field, direction), ...]
            unique: Whether index is unique

        Returns:
            Index name
        """
        try:
            coll = self.db[collection]
            return coll.create_index(keys, unique=unique)

        except PyMongoError as e:
            raise IntegrationError(f"Index creation failed: {str(e)}", "MongoDB")

    async def drop_collection(self, collection: str) -> bool:
        """
        Drop collection

        Args:
            collection: Collection name

        Returns:
            True if successful
        """
        try:
            self.db.drop_collection(collection)
            return True

        except PyMongoError as e:
            raise IntegrationError(f"Drop collection failed: {str(e)}", "MongoDB")
