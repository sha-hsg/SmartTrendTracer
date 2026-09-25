"""
MongoDB queries of app.api.twitter_accounts.crud, moved verbatim out of the router
(one function per former inline call site).
"""
from app.database.mongodb import get_database

db = get_database()


def twitter_accounts_find_one__create_account(username):
    """twitter_accounts.find_one from twitter_accounts.crud.create_account()"""
    return db.twitter_accounts.find_one({'username': {'$regex': f'^{username}$', '$options': 'i'}})


def twitter_accounts_insert_one__create_account(document):
    """twitter_accounts.insert_one from twitter_accounts.crud.create_account()"""
    return db.twitter_accounts.insert_one(document)
