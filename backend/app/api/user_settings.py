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

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.repositories import user_settings_queries as queries

router = APIRouter()

# Unique index (user_id, key) is ensured centrally in app.database.mongodb._ensure_indexes


class SettingValue(BaseModel):
    value: Any


@router.get("/{key}")
def get_setting(key: str, user_id: str = Query(default="default")):
    doc = queries.user_settings_find_one__get_setting(user_id, key)
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

    queries.user_settings_update_one__put_setting(user_id, key, body)
    return {"success": True, "user_id": user_id, "key": key}


@router.delete("/{key}")
def delete_setting(key: str, user_id: str = Query(default="default")):
    result = queries.user_settings_delete_one__delete_setting(user_id, key)
    return {"success": True, "deleted": result.deleted_count}
