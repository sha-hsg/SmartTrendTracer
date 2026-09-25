"""
Data access for app.api.twitter_accounts.crud (extracted by the arch-audit refactor).


"""
from app.repositories.errors import InvalidInputError, NotFoundError
from app.utils.serializers import serialize_account
from bson import ObjectId
from datetime import datetime
from datetime import timezone

from app.database.mongodb import get_database

db = get_database()




def list_accounts(enabled_only, tier, category):
    """List all Twitter accounts with optional filtering."""
    query = {}

    if enabled_only:
        query['enabled'] = True

    if tier is not None:
        query['tier'] = tier

    if category:
        query['category'] = category

    accounts = list(db.twitter_accounts.find(query).sort([
        ('tier', 1),
        ('username', 1)
    ]))

    return [serialize_account(acc) for acc in accounts]



def update_account(account_id, data):
    """Update an existing Twitter account."""
    try:
        account = db.twitter_accounts.find_one({'_id': ObjectId(account_id)})
    except Exception:
        raise InvalidInputError("Invalid account ID format")

    if not account:
        raise NotFoundError("Account not found")

    # Build update document
    update_data = {'updated_at': datetime.now(timezone.utc)}

    if data.display_name is not None:
        update_data['display_name'] = data.display_name
    if data.category is not None:
        update_data['category'] = data.category
    if data.description is not None:
        update_data['description'] = data.description
    if data.tier is not None:
        update_data['tier'] = data.tier
    if data.enabled is not None:
        update_data['enabled'] = data.enabled

    db.twitter_accounts.update_one(
        {'_id': ObjectId(account_id)},
        {'$set': update_data}
    )

    # Fetch updated document
    updated = db.twitter_accounts.find_one({'_id': ObjectId(account_id)})
    return serialize_account(updated)



def delete_account(account_id, delete_tweets):
    """Delete a Twitter account. Optionally delete all associated tweets."""
    try:
        account = db.twitter_accounts.find_one({'_id': ObjectId(account_id)})
    except Exception:
        raise InvalidInputError("Invalid account ID format")

    if not account:
        raise NotFoundError("Account not found")

    username = account.get('username')
    tweets_deleted = 0

    # Optionally delete tweets
    if delete_tweets:
        result = db.tweets.delete_many({'author_username': username})
        tweets_deleted = result.deleted_count

    # Delete account
    db.twitter_accounts.delete_one({'_id': ObjectId(account_id)})

    return {
        'message': f"Account @{username} deleted successfully",
        'tweets_deleted': tweets_deleted
    }

