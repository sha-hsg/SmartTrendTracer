"""
MongoDB queries of app.api.twitter_accounts.collection, moved verbatim out of the router
(one function per former inline call site).
"""
from bson import ObjectId
from app.database.mongodb import get_database

db = get_database()


def twitter_accounts_update_one__refresh_account_info(update_data, account_id):
    """twitter_accounts.update_one from twitter_accounts.collection.refresh_account_info()"""
    return db.twitter_accounts.update_one(
        {'_id': ObjectId(account_id)},
        {'$set': update_data}
    )


def twitter_accounts_find_one__refresh_account_info(account_id):
    """twitter_accounts.find_one from twitter_accounts.collection.refresh_account_info()"""
    return db.twitter_accounts.find_one({'_id': ObjectId(account_id)})


def tweets_count_documents__trigger_collection(month_start):
    """tweets.count_documents from twitter_accounts.collection.trigger_collection()"""
    return db.tweets.count_documents({'collected_at': {'$gte': month_start}})


def twitter_accounts_find_one__refresh_account_info_2(account_id):
    """twitter_accounts.find_one from twitter_accounts.collection.refresh_account_info()"""
    return db.twitter_accounts.find_one({'_id': ObjectId(account_id)})


def collection_state_find_one___collect_tweets_sync(username):
    """collection_state.find_one from twitter_accounts.collection._collect_tweets_sync()"""
    return db.collection_state.find_one({'key': f'twitter_{username}'})


def twitter_accounts_update_one___collect_tweets_sync(account_id, now, tweets_collected):
    """twitter_accounts.update_one from twitter_accounts.collection._collect_tweets_sync()"""
    return db.twitter_accounts.update_one(
        {'_id': ObjectId(account_id)},
        {
            '$set': {'last_collected_at': now},
            '$inc': {'tweets_collected': tweets_collected}
        }
    )


def twitter_accounts_find_one__trigger_collection(account_id):
    """twitter_accounts.find_one from twitter_accounts.collection.trigger_collection()"""
    return db.twitter_accounts.find_one({'_id': ObjectId(account_id)})
