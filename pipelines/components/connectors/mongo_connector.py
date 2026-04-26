from typing import Any, Generator, Optional, List, Dict, Self, Tuple, Iterable

import ujson
from bson import ObjectId
from pymongo import MongoClient, ReplaceOne
from pymongo.synchronous.cursor import Cursor
from gridfs import GridFSBucket

from pipelines.components.connectors.connector import Connector
from settings import mongo_connection_url, mongo_serverSelectionTimeoutMS, mongo_socketTimeoutMS, mongo_wtimeoutMS, \
    MONGO_READ_BATCH_SIZE, MONGO_WRITE_BATCH_SIZE, MONGO_CURSOR_BATCH_SIZE


class MongoConnector(Connector):
    """
    Connector class for working with MongoDB.
    """
    _client: Optional[MongoClient[Dict[str, Any]]] = None
    _default_database: Optional[str] = None
    _default_collection: Optional[str] = None
    _default_bucket: Optional[str] = None

    def connect(self) -> None:
        if self._client:
            return
        self._client = MongoClient(
            mongo_connection_url,
            serverSelectionTimeoutMS=mongo_serverSelectionTimeoutMS,
            socketTimeoutMS=mongo_socketTimeoutMS,
            wtimeoutMS=mongo_wtimeoutMS
        )

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def select(
            self,
            query: Optional[Dict[str, Any]] = None,
            fields: Optional[str | List[str]] = None,
            sort: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None,
            database: Optional[str] = None,
            collection: Optional[str] = None,
            disk_usage: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Executes `find` query in MongoDB and returns results as list of dictionaries.
        """
        database, collection = self._infer_defaults(database, collection)
        if isinstance(fields, str):
            fields = [fields]
        cursor = self._select(query, fields, sort, limit, database, collection, allow_disk_use=disk_usage)
        return cursor.to_list()

    def insert(
            self,
            data: Dict[str, Any] | List[Dict[str, Any]],
            database: Optional[str] = None,
            collection: Optional[str] = None,
            ordered: bool = True,
            upsert_key: Optional[str | List[str]] = None,
    ) -> None:
        """
        Executes `inserts` query in MongoDB with provided data.
        """
        database, collection = self._infer_defaults(database, collection)

        if isinstance(data, dict):
            data = [data]

        if len(data) == 0:
            return

        upsert_key = upsert_key or []
        if isinstance(upsert_key, str):
            upsert_key = [upsert_key]

        self._insert_many(data, upsert_key, ordered, database, collection)

    def select_stream(
            self,
            query: Optional[Dict[str, Any]] = None,
            fields: Optional[str | List[str]] = None,
            sort: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None,
            database: Optional[str] = None,
            collection: Optional[str] = None,
            stream_batch_size: int = MONGO_READ_BATCH_SIZE,
            disk_usage: bool = False,
            disable_timeout: bool = False,
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Executes `find` query in MongoDB and streams results as lists of dictionaries with provided length.
        """
        database, collection = self._infer_defaults(database, collection)
        if isinstance(fields, str):
            fields = [fields]

        cursor = self._select(
            query,
            fields,
            sort,
            limit,
            database,
            collection,
            allow_disk_use=disk_usage,
            no_cursor_timeout=disable_timeout,
        )
        try:
            batch = []
            for record in cursor:
                if len(batch) < stream_batch_size:
                    batch.append(record)
                    continue

                yield batch
                batch = []

            if len(batch) > 0:
                yield batch
        finally:
            cursor.close()

    def insert_stream(
            self,
            data: Iterable[Dict[str, Any]],
            database: Optional[str] = None,
            collection: Optional[str] = None,
            stream_batch_size: int = MONGO_WRITE_BATCH_SIZE,
            ordered: bool = True,
            upsert_key: Optional[str | List[str]] = None,
    ) -> None:
        """
        Executes `insert` query in MongoDB with batches of dictionaries with provided lengths.
        """
        database, collection = self._infer_defaults(database, collection)

        upsert_key = upsert_key or []
        if isinstance(upsert_key, str):
            upsert_key = [upsert_key]

        batch = []
        for record in data:
            batch.append(record)
            if len(batch) >= stream_batch_size:
                self._insert_many(batch, upsert_key, ordered, database, collection)
                batch = []

        if len(batch) > 0:
            self._insert_many(batch, upsert_key, ordered, database, collection)

    def aggregate(
            self,
            group: Optional[Dict[str, Any]] = None,
            match: Optional[Dict[str, Any]] = None,
            project: Optional[Dict[str, Any]] = None,
            aggs: Optional[Dict[str, Any] | List[Dict[str, Any]]] = None,
            disk_usage: bool = False,
            database: Optional[str] = None,
            collection: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes `aggregate` query in MongoDB with provided `$group` query and returns results as list of dictionaries.
        """
        database, collection = self._infer_defaults(database, collection)

        aggs = aggs or []
        if isinstance(aggs, dict):
            aggs = [aggs]

        group_agg = ({"$group": group},) if group else ()
        match_agg = ({"$match": match},) if match else ()
        project_agg = ({"$project": project},) if project else ()
        pipeline = [*match_agg, *group_agg, *project_agg, *aggs]

        return self._client[database][collection].aggregate(pipeline, allowDiskUse=disk_usage).to_list()

    def count(
            self,
            query: Optional[Dict[str, Any]] = None,
            database: Optional[str] = None,
            collection: Optional[str] = None,
    ) -> int:
        """
        Executes `count_documents` query in MongoDB with provided `$filter` query.
        """
        database, collection = self._infer_defaults(database, collection)
        return self._client[database][collection].count_documents(query or {})

    def collection_exists(self, database: Optional[str] = None, collection: Optional[str] = None) -> bool:
        """
        Check if given collection exists in database.
        """
        database, collection = self._infer_defaults(database, collection)
        return collection in self._client[database].list_collection_names()

    def create_collection(
            self,
            database: Optional[str] = None,
            collection: Optional[str] = None,
            indexes: Optional[List[str]] = None,
    ) -> None:
        """
        Creates collection with given name and indexes in database.
        """
        database, collection = self._infer_defaults(database, collection)
        self._client[database].create_collection(collection)
        for index in (indexes or []):
            self._client[database][collection].create_index(index)

    def create_index_if_not_exists(
        self,
        index: str | List[str],
        database: Optional[str] = None,
        collection: Optional[str] = None,
    ) -> None:
        """
        Creates index on collection field.
        """
        database, collection = self._infer_defaults(database, collection)

        if isinstance(index, str):
            index = [index]

        existed_indexes = [
            key
            for existed_idx in self._client[database][collection].list_indexes()
            for key in existed_idx.get("key", {}).keys()
        ]

        for idx in index:
            if idx in existed_indexes:
                continue
            self._client[database][collection].create_index(idx)

    def create_temp_collection(
        self,
        database: Optional[str] = None,
        collection: Optional[str] = None,
        *,
        drop_temp_if_exists: bool = True,
    ) -> str:
        """
        Creates temporary collection in MongoDB with name - `{collection}_tmp`.
        If collection with this name are already exists, it will be dropped before creation.
        """
        database, collection = self._infer_defaults(database, collection)
        temp_collection = f"{collection}_tmp"

        collection_exists = self.collection_exists(database, temp_collection)

        if collection_exists and drop_temp_if_exists:
            self._client[database][temp_collection].drop()
            self._client[database].create_collection(temp_collection)

        if not collection_exists:
            self._client[database].create_collection(temp_collection)

        return temp_collection

    def db(self, database: str):
        if not self._client:
            raise RuntimeError("Not connected to MongoDB")
        return self._client[database]

    def swap_with_temp_collection(
            self,
            database: Optional[str] = None,
            collection: Optional[str] = None,
            temp_collection: Optional[str] = None,
    ) -> None:
        """
        Deletes collection from MongoDB and replaces it with temporary collection.
        """
        database, collection = self._infer_defaults(database, collection)
        collection = self._client[database][collection]
        temp_collection = self._client[database][temp_collection or f"{collection.name}_tmp"]
        collection.drop()
        temp_collection.rename(collection.name)

    def create_index_if_not_exists(
        self,
        index: str | List[str],
        database: Optional[str] = None,
        collection: Optional[str] = None,
        unique: bool = False,
    ) -> None:
        """
        Creates index on collection field.
        """
        database, collection = self._infer_defaults(database, collection)

        if isinstance(index, str):
            index = [index]

        existed_indexes = [
            key
            for existed_idx in self._client[database][collection].list_indexes()
            for key in existed_idx.get("key", {}).keys()
        ]

        for idx in index:
            if idx in existed_indexes:
                continue
            self._client[database][collection].create_index(idx, unique=unique)

    def put_file(
        self,
        filename: str,
        data: Dict[str, Any] | List[Any] | str | bytes,
        metadata: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None,
        bucket: Optional[str] = None,
    ) -> ObjectId:
        """
        Puts file into GridFS and returns it's id.
        """
        database, bucket = self._infer_defaults(database, bucket, infer_bucket=True)
        grid_fs = GridFSBucket(self._client[database], bucket)
        if isinstance(data, (dict, list)):
            data = ujson.dumps(data)
        if isinstance(data, str):
            data = data.encode("utf-8")
        return grid_fs.upload_from_stream(filename, data, metadata=metadata)

    def with_defaults(
        self, database: Optional[str] = None, collection: Optional[str] = None, bucket: Optional[str] = None
    ) -> Self:
        self._default_database = database
        self._default_collection = collection
        self._default_bucket = bucket
        return self

    def _infer_defaults(
        self, database: Optional[str], collection_or_bucket: Optional[str], *, infer_bucket: bool = False
    ) -> Tuple[str, str]:
        if (database is None) and (self._default_database is None):
            raise ValueError("Database are not specified.")
        if database is None:
            database = self._default_database

        if infer_bucket:
            if (collection_or_bucket is None) and (self._default_bucket is None):
                raise ValueError("Bucket are not specified.")
            if collection_or_bucket is None:
                collection_or_bucket = self._default_bucket
        else:
            if (collection_or_bucket is None) and (self._default_collection is None):
                raise ValueError("Collection are not specified.")
            if collection_or_bucket is None:
                collection_or_bucket = self._default_collection

        return database, collection_or_bucket

    def _select(
            self,
            query: Optional[Dict[str, Any]],
            fields: Optional[List[str]],
            sort: Optional[Dict[str, Any]],
            limit: Optional[int],
            database: str,
            collection: str,
            **cursor_kwargs: Any,
    ) -> Cursor[Dict[str, Any]]:
        if query is None:
            query = {}
        if fields is not None:
            fields = {column: 1 for column in fields}
        cursor = (
            self._client[database][collection]
            .find(query, fields, sort=sort, batch_size=MONGO_CURSOR_BATCH_SIZE, **cursor_kwargs)
        )
        if limit is not None:
            cursor = cursor.limit(limit)
        return cursor

    def _insert_many(
        self,
        documents: Iterable[Dict[str, Any]],
        upsert_key: List[str],
        ordered: bool,
        database: str,
        collection: str,
    ) -> None:
        collection = self._client[database][collection]

        if upsert_key:
            collection.bulk_write(
                [
                    ReplaceOne({key: document[key] for key in upsert_key}, document, upsert=True)
                    for document in documents
                ],
                ordered=ordered
            )
        else:
            collection.insert_many(documents, ordered=ordered)
