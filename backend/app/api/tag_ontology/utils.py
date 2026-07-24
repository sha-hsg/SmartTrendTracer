"""
Shared utilities for the tag_ontology package.
Database helpers, logger, and collection accessors.
"""
from fastapi import HTTPException
from pymongo import ASCENDING, TEXT
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
from bson import ObjectId
import logging
import re

from app.database.mongodb import get_client, get_database

logger = logging.getLogger(__name__)


def get_mongo_client():
    """Get or create MongoDB client singleton"""
    try:
        client = get_client()
        client.admin.command('ping')
        return client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise HTTPException(status_code=503, detail="MongoDB connection failed")


def get_mongo_db():
    """Get MongoDB database connection"""
    return get_database()


def get_concepts_collection():
    """Get concepts collection with error handling"""
    try:
        db = get_mongo_db()
        return db.tag_concepts_v2
    except Exception as e:
        logger.error(f"Error accessing concepts collection: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")


def get_aliases_collection():
    """Get aliases collection with error handling"""
    try:
        db = get_mongo_db()
        return db.tag_aliases_v2
    except Exception as e:
        logger.error(f"Error accessing aliases collection: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")


def get_instances_collection():
    """Get tag instances collection with error handling"""
    try:
        db = get_mongo_db()
        return db.tag_instances
    except Exception as e:
        logger.error(f"Error accessing instances collection: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")


def find_concept_by_any_id(concepts_col, concept_id: str):
    """Find a concept by its custom id field ("c_...") or its ObjectId string."""
    concept = concepts_col.find_one({"id": concept_id})
    if concept is None and ObjectId.is_valid(concept_id):
        concept = concepts_col.find_one({"_id": ObjectId(concept_id)})
    return concept


def concept_id_variants(concept) -> list:
    """All id representations under which references to this concept may be
    stored: the ObjectId, its string form, and the legacy custom "c_..." id."""
    oid = concept["_id"]
    variants = [oid, str(oid)]
    custom_id = concept.get("id")
    if custom_id and custom_id not in variants:
        variants.append(custom_id)
    return variants
