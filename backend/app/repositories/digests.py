"""Weekly digest storage and the per-week content queries it needs."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.database.mongodb import get_database
from app.repositories.errors import NotFoundError

db = get_database()


def new_papers(since: datetime, limit: int = 30) -> List[Dict[str, Any]]:
    return list(db.papers.find({'created_at': {'$gte': since}, 'paper_type': {'$ne': 'review'}},
                               {'title': 1, 'authors': 1, 'source': 1, 'created_at': 1, 'abstract': 1})
                .sort('created_at', -1).limit(limit))


def new_articles(since: datetime, limit: int = 20) -> List[Dict[str, Any]]:
    return list(db.articles.find({'published_at': {'$gte': since}},
                                 {'title': 1, 'author_name': 1, 'published_at': 1, 'url': 1})
                .sort('published_at', -1).limit(limit))


def top_tweets(since: datetime, limit: int = 10) -> List[Dict[str, Any]]:
    """Most-liked original tweets (no retweets) of the period."""
    return list(db.tweets.aggregate([
        {'$match': {'created_at': {'$gte': since}, 'text': {'$not': {'$regex': '^RT @'}}}},
        {'$addFields': {'likes': {'$ifNull': ['$metrics.like_count', 0]}}},
        {'$sort': {'likes': -1}},
        {'$limit': limit},
        {'$project': {'text': 1, 'author_username': 1, 'created_at': 1, 'likes': 1}},
    ]))


def count_new(collection: str, field: str, since: datetime) -> int:
    return db[collection].count_documents({field: {'$gte': since}})


def save_digest(doc: Dict[str, Any]) -> str:
    """One digest per start date: re-running on the same day replaces it."""
    db.digests.replace_one({'week_start': doc['week_start']}, doc, upsert=True)
    return str(db.digests.find_one({'week_start': doc['week_start']}, {'_id': 1})['_id'])


def list_digests(limit: int = 52) -> List[Dict[str, Any]]:
    return list(db.digests.find({}, {'week_start': 1, 'week_end': 1, 'created_at': 1, 'stats': 1})
                .sort('week_start', -1).limit(limit))


def get_digest(digest_id: Optional[str] = None) -> Dict[str, Any]:
    """A digest by id, or the latest one."""
    if digest_id:
        if not ObjectId.is_valid(digest_id):
            raise NotFoundError('Digest not found')
        doc = db.digests.find_one({'_id': ObjectId(digest_id)})
    else:
        doc = db.digests.find_one(sort=[('week_start', -1)])
    if not doc:
        raise NotFoundError('Digest not found')
    return doc
