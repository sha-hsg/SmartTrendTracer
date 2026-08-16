"""Centralised MongoDB configuration helpers.

This module exposes a lazily initialised `MongoClient` and database handle that
all services/APIs can reuse. Connection details come from environment
variables, allowing deployments to override host, authentication, TLS, replica
set, etc., without editing source code.
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from functools import lru_cache, wraps
from typing import Any, Callable, Dict, Generator, Optional, TypeVar

from bson import ObjectId
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.database import Database


logger = logging.getLogger(__name__)


def safe_object_id(value) -> Optional[ObjectId]:
    """Convert a value to ObjectId if possible, otherwise return None.

    Handles strings, existing ObjectIds, and invalid values gracefully.
    This centralises the inconsistent ObjectId conversion patterns
    scattered across services (try/except, length checks, etc.).
    """
    if value is None or value == "" or value == "None":
        return None
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str):
        try:
            return ObjectId(value)
        except Exception:
            return None
    return None


def concept_id_query_variants(concept_id) -> list:
    """All forms under which tag_instances.concept_id may store this id.

    tag_instances.concept_id is stored in mixed form: ObjectId (98%),
    stringified ObjectId, or a legacy slug id like 'c_method_...'. Querying a
    single form silently drops rows — always use
    {'concept_id': {'$in': concept_id_query_variants(cid)}}.
    (For the inverse case — you hold the concept *document* — use
    app.api.tag_ontology.utils.concept_id_variants.)
    """
    variants = []
    for v in (concept_id, str(concept_id)):
        if v not in variants:
            variants.append(v)
    oid = safe_object_id(concept_id)
    if oid is not None and oid not in variants:
        variants.append(oid)
    return variants

# Slow query threshold in seconds (configurable via environment)
SLOW_QUERY_THRESHOLD = float(os.getenv("MONGODB_SLOW_QUERY_MS", "100")) / 1000  # Default 100ms

T = TypeVar("T")


@contextmanager
def timed_query(operation: str, collection: str = "", extra: str = "") -> Generator[None, None, None]:
    """Context manager to log slow MongoDB queries.

    Usage:
        with timed_query("find", "papers", "filter={'processed': True}"):
            result = db.papers.find({'processed': True})
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        if elapsed >= SLOW_QUERY_THRESHOLD:
            details = f"{collection}.{operation}" if collection else operation
            if extra:
                details = f"{details} ({extra})"
            logger.warning(
                "SLOW_QUERY: %s took %.2fms (threshold: %.0fms)",
                details,
                elapsed * 1000,
                SLOW_QUERY_THRESHOLD * 1000
            )
        elif elapsed >= SLOW_QUERY_THRESHOLD * 0.5:
            # Log queries approaching threshold at debug level
            details = f"{collection}.{operation}" if collection else operation
            logger.debug(
                "QUERY: %s completed in %.2fms",
                details,
                elapsed * 1000
            )


def log_slow_queries(operation: str = "", collection: str = "") -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to log slow MongoDB operations.

    Usage:
        @log_slow_queries("aggregate", "papers")
        def get_paper_stats():
            return list(db.papers.aggregate([...]))
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            op = operation or func.__name__
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                if elapsed >= SLOW_QUERY_THRESHOLD:
                    details = f"{collection}.{op}" if collection else op
                    logger.warning(
                        "SLOW_QUERY: %s took %.2fms (threshold: %.0fms)",
                        details,
                        elapsed * 1000,
                        SLOW_QUERY_THRESHOLD * 1000
                    )
        return wrapper
    return decorator


@dataclass(frozen=True)
class MongoSettings:
    """Runtime configuration for MongoDB access."""

    uri: str
    database: str
    replica_set: Optional[str] = None
    app_name: Optional[str] = None
    options: Optional[Dict[str, str]] = None  # Additional driver options

    @classmethod
    def from_env(cls) -> "MongoSettings":
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        database = os.getenv("MONGODB_DB", "smarttrendtracer")
        replica_set = os.getenv("MONGODB_REPLICA_SET") or None
        app_name = os.getenv("MONGODB_APP_NAME") or None

        # Optional extra driver params (comma-separated key=value pairs)
        raw_options = os.getenv("MONGODB_OPTIONS", "")
        options: Dict[str, str] = {}
        if raw_options:
            for pair in raw_options.split(","):
                pair = pair.strip()
                if not pair or "=" not in pair:
                    continue
                key, value = pair.split("=", 1)
                options[key.strip()] = value.strip()

        return cls(
            uri=uri,
            database=database,
            replica_set=replica_set,
            app_name=app_name,
            options=options,
        )


@lru_cache(maxsize=1)
def get_settings() -> MongoSettings:
    """Return cached MongoDB settings loaded from environment variables."""

    settings = MongoSettings.from_env()
    logger.info("MongoDB settings loaded (database=%s, uri=%s)", settings.database, settings.uri)
    return settings


_indexes_initialized = False


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    """Return a shared MongoClient instance configured from `MongoSettings`."""

    settings = get_settings()
    client_kwargs = dict(settings.options or {})
    if settings.replica_set:
        client_kwargs.setdefault("replicaSet", settings.replica_set)
    if settings.app_name:
        client_kwargs.setdefault("appname", settings.app_name)

    client = MongoClient(settings.uri, **client_kwargs)
    logger.info("MongoDB client initialised")
    return client


def get_database() -> Database:
    """Return the configured MongoDB database handle."""

    client = get_client()
    settings = get_settings()
    db = client[settings.database]
    _ensure_indexes(db)
    return db


def _ensure_indexes(db: Database) -> None:
    global _indexes_initialized
    if _indexes_initialized:
        return

    # Define all indexes with descriptive names for logging
    index_definitions = [
        ("tweets", [("created_at", DESCENDING)]),
        ("tweets", [("author_username", ASCENDING)]),
        ("papers", [("created_at", DESCENDING)]),
        ("papers", [("processed", ASCENDING)]),
        ("papers", [("conference", ASCENDING)]),
        ("papers", [("concept_ids", ASCENDING)]),
        ("papers", [("authors_detailed.name", ASCENDING)]),  # PERF-002: Index for author name searches
        ("tag_instances", [("content_type", ASCENDING), ("content_id", ASCENDING), ("concept_id", ASCENDING)]),
        ("tag_instances", [("concept_id", ASCENDING)]),
        ("articles", [("created_at", DESCENDING)]),
        ("articles", [("author_id", ASCENDING)]),
        ("reddit_posts", [("created_utc", DESCENDING)]),
        ("books", [("uploaded_at", DESCENDING)]),
        ("books", [("processing_status", ASCENDING)]),
        ("books", [("concept_ids", ASCENDING)]),
        ("books", [("file_type", ASCENDING)]),
        ("books", [("publisher", ASCENDING)]),
        ("books", [("publication_year", ASCENDING)]),
    ]

    # Text indexes for full-text search (PERF-002)
    # Note: MongoDB allows only ONE text index per collection, so we combine fields
    text_index_definitions = [
        # Papers: search across title, abstract, and content
        ("papers", [("title", TEXT), ("abstract", TEXT), ("content_markdown", TEXT)], "papers_text_search"),
        # Articles: search across title and content
        ("articles", [("title", TEXT), ("content_markdown", TEXT)], "articles_text_search"),
        # Tweets: search across full_text
        ("tweets", [("full_text", TEXT)], "tweets_text_search"),
    ]

    failed_indexes = []
    successful_count = 0

    for collection_name, index_fields in index_definitions:
        try:
            db[collection_name].create_index(index_fields)
            successful_count += 1
        except Exception as exc:
            index_desc = f"{collection_name}.{[f[0] for f in index_fields]}"
            logger.error("Failed to create index %s: %s", index_desc, exc)
            failed_indexes.append(index_desc)

    # Create text indexes for full-text search (PERF-002)
    text_successful = 0
    for collection_name, index_fields, index_name in text_index_definitions:
        try:
            db[collection_name].create_index(index_fields, name=index_name)
            text_successful += 1
        except Exception as exc:
            # Text index may already exist or conflict - log but don't fail
            if "already exists" in str(exc).lower() or "Index with name" in str(exc):
                logger.debug("Text index %s already exists, skipping", index_name)
                text_successful += 1
            else:
                logger.error("Failed to create text index %s: %s", index_name, exc)
                failed_indexes.append(index_name)

    _indexes_initialized = True

    total_indexes = len(index_definitions) + len(text_index_definitions)
    total_successful = successful_count + text_successful

    if failed_indexes:
        logger.error("MongoDB index creation: %d/%d succeeded, %d failed: %s",
                     total_successful, total_indexes, len(failed_indexes), failed_indexes)
    else:
        logger.info("MongoDB performance indexes ensured (%d regular + %d text indexes)",
                    successful_count, text_successful)
