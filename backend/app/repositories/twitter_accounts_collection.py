"""
Data access for app.api.twitter_accounts.collection (extracted by the arch-audit refactor).


"""
from app.repositories.errors import InvalidInputError, NotFoundError
from bson import ObjectId
from datetime import datetime
from datetime import timezone

from app.database.mongodb import get_database

db = get_database()




def toggle_account(account_id):
    """Toggle the enabled status of an account."""
    try:
        account = db.twitter_accounts.find_one({'_id': ObjectId(account_id)})
    except Exception:
        raise InvalidInputError("Invalid account ID format")

    if not account:
        raise NotFoundError("Account not found")

    new_status = not account.get('enabled', True)

    db.twitter_accounts.update_one(
        {'_id': ObjectId(account_id)},
        {'$set': {'enabled': new_status, 'updated_at': datetime.now(timezone.utc)}}
    )

    return {
        'id': str(account['_id']),
        'username': account.get('username'),
        'enabled': new_status
    }

