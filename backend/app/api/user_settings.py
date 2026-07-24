"""
Generic per-user key-value settings store backed by MongoDB.

Used today for TweetDeck column configuration; designed so other UI state
that should survive across machines / browsers can use the same endpoints.

Collection: `user_settings`
Document shape:
    {
        "user_id": "default",
        "key": "tweetdeck_columns",
        "value": <any JSON>,
        "updated_at": <datetime>
    }

Unique compound index on (user_id, key).
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from pymongo import ASCENDING

from app.database.mongodb import get_database

router = APIRouter()

db = get_database()
collection = db.user_settings

# Ensure unique index (idempotent).
collection.create_index(
    [("user_id", ASCENDING), ("key", ASCENDING)],
    unique=True,
    name="user_id_key_unique",
)


class SettingValue(BaseModel):
    value: Any


@router.get("/{key}")
def get_setting(key: str, user_id: str = Query(default="default")):
    doc = collection.find_one({"user_id": user_id, "key": key})
    if not doc:
        # Not found is not an error — caller treats absence as "use default".
        return {"user_id": user_id, "key": key, "value": None, "exists": False}
    return {
        "user_id": user_id,
        "key": key,
        "value": doc.get("value"),
        "updated_at": doc.get("updated_at").isoformat() if doc.get("updated_at") else None,
        "exists": True,
    }


@router.put("/{key}")
def put_setting(key: str, body: SettingValue, user_id: str = Query(default="default")):
    if not key or len(key) > 128:
        raise HTTPException(status_code=400, detail="Invalid key")

    collection.update_one(
        {"user_id": user_id, "key": key},
        {
            "$set": {
                "value": body.value,
                "updated_at": datetime.now(timezone.utc),
            },
            "$setOnInsert": {
                "user_id": user_id,
                "key": key,
            },
        },
        upsert=True,
    )
    return {"success": True, "user_id": user_id, "key": key}


@router.delete("/{key}")
def delete_setting(key: str, user_id: str = Query(default="default")):
    result = collection.delete_one({"user_id": user_id, "key": key})
    return {"success": True, "deleted": result.deleted_count}
