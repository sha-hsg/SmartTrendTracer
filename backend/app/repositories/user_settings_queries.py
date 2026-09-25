"""
MongoDB queries of app.api.user_settings, moved verbatim out of the router
(one function per former inline call site).
"""
from datetime import datetime
from datetime import timezone
from app.database.mongodb import get_database

db = get_database()


def user_settings_find_one__get_setting(user_id, key):
    """user_settings.find_one from user_settings.get_setting()"""
    return db.user_settings.find_one({"user_id": user_id, "key": key})


def user_settings_update_one__put_setting(user_id, key, body):
    """user_settings.update_one from user_settings.put_setting()"""
    return db.user_settings.update_one(
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


def user_settings_delete_one__delete_setting(user_id, key):
    """user_settings.delete_one from user_settings.delete_setting()"""
    return db.user_settings.delete_one({"user_id": user_id, "key": key})
