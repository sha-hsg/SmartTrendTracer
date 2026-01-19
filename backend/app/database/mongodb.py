"""Centralised MongoDB configuration helpers.

This module exposes a lazily initialised `MongoClient` and database handle that
all services/APIs can reuse. Connection details come from environment
variables, allowing deployments to override host, authentication, TLS, replica
set, etc., without editing source code.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Optional

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MongoSettings:
    """Runtime configuration for MongoDB access."""

    uri: str
    database: str
    replica_set: Optional[str] = None
    app_name: Optional[str] = None
    options: Dict[str, str] = None  # Additional driver options

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

    try:
        db.tweets.create_index([("created_at", DESCENDING)])
        db.tweets.create_index([("author_username", ASCENDING)])

        db.papers.create_index([("created_at", DESCENDING)])
        db.papers.create_index([("processed", ASCENDING)])
        db.papers.create_index([("conference", ASCENDING)])
        db.papers.create_index([("concept_ids", ASCENDING)])

        db.tag_instances.create_index([
            ("content_type", ASCENDING),
            ("content_id", ASCENDING)
        ])
        db.tag_instances.create_index([("concept_id", ASCENDING)])

        db.articles.create_index([("created_at", DESCENDING)])
        db.articles.create_index([("author_id", ASCENDING)])

        db.reddit_posts.create_index([("created_utc", DESCENDING)])

        # Books collection indexes
        db.books.create_index([("uploaded_at", DESCENDING)])
        db.books.create_index([("processing_status", ASCENDING)])
        db.books.create_index([("concept_ids", ASCENDING)])
        db.books.create_index([("file_type", ASCENDING)])
        db.books.create_index([("publisher", ASCENDING)])
        db.books.create_index([("publication_year", ASCENDING)])

        _indexes_initialized = True
        logger.info("MongoDB performance indexes ensured")
    except Exception as exc:
        logger.warning("Failed to ensure MongoDB indexes: %s", exc)
