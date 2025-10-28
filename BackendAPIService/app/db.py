import os
import logging
from typing import Tuple
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)

# PUBLIC_INTERFACE
def get_db_collection() -> Tuple[MongoClient, Collection]:
    """Create MongoClient and return (client, devices_collection) using env vars.
    Required env: MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION"""
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB")
    coll_name = os.getenv("MONGODB_COLLECTION")

    missing = [name for name, val in [("MONGODB_URI", uri), ("MONGODB_DB", db_name), ("MONGODB_COLLECTION", coll_name)] if not val]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        # Force connection attempt
        client.admin.command("ping")
        db = client[db_name]
        collection = db[coll_name]
        logger.info("MongoDB connected", extra={"db": db_name, "collection": coll_name})
        return client, collection
    except PyMongoError as e:
        logger.exception("Failed to connect to MongoDB")
        raise RuntimeError(f"Failed to connect to MongoDB: {e}") from e
