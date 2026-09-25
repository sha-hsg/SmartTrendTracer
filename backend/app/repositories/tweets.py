"""
Tweet persistence — the single write path for the tweets collection.

Used by the standalone collector (tweet_collector_service.py) and the manual
per-account collection endpoint (api/twitter_accounts/collection.py), which
previously each built and inserted tweet documents on their own.

Rules carried here:
* tweets._id is the Twitter ID string — never an ObjectId or a separate
  tweet_id field (89 legacy docs had to be migrated for exactly that).
* collection_state.last_tweet_id only ever moves forward ($max), so a stale
  run cannot rewind the since_id and re-fetch old tweets.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pymongo.errors import DuplicateKeyError

from app.database.mongodb import get_database

db = get_database()


def build_tweet_document(
    tweet_id: str,
    text: str,
    author_id: Optional[str],
    author_username: Optional[str],
    author_name: Optional[str],
    created_at: Any,
    public_metrics: Optional[Dict[str, Any]],
    entities: Optional[Dict[str, Any]],
    urls: List[Dict[str, Any]],
    referenced_tweets: Optional[List[Dict[str, Any]]],
    media: List[Dict[str, Any]],
    collected_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Canonical tweet document (schema shared by every writer)."""
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
    public_metrics = public_metrics or {}
    entities = entities or {}
    return {
        '_id': str(tweet_id),  # Twitter ID string as MongoDB _id
        'text': text,
        'author_id': author_id,
        'author_username': author_username,
        'author_name': author_name,
        'created_at': created_at,
        'collected_at': collected_at or datetime.now(timezone.utc),
        'processed': False,
        'metrics': {
            'retweet_count': public_metrics.get('retweet_count', 0),
            'like_count': public_metrics.get('like_count', 0),
            'reply_count': public_metrics.get('reply_count', 0),
            'quote_count': public_metrics.get('quote_count', 0),
        },
        'hashtags': entities.get('hashtags', []),
        'mentions': entities.get('mentions', []),
        'urls': urls,
        'referenced_tweets': referenced_tweets or [],
        'media': media,
        'media_count': len(media),
        'concept_ids': [],
    }


def tweet_exists(tweet_id: str) -> bool:
    return db.tweets.find_one({'_id': str(tweet_id)}, {'_id': 1}) is not None


def insert_tweet_if_new(tweet_doc: Dict[str, Any]) -> bool:
    """Insert unless a tweet with this _id exists. Returns True if inserted."""
    try:
        db.tweets.insert_one(tweet_doc)
        return True
    except DuplicateKeyError:
        return False


def advance_collection_state(key: str, last_run: datetime, last_tweet_id: Optional[str] = None,
                             tweets_collected: int = 0) -> None:
    """Record a collection run. last_tweet_id only moves forward ($max)."""
    now = datetime.now(timezone.utc)
    update_ops: Dict[str, Any] = {
        '$set': {
            'last_run': last_run,
            'updated_at': now,
            'tweets_collected_this_cycle': tweets_collected,
        },
        '$inc': {'tweets_collected_total': tweets_collected},
        '$setOnInsert': {'key': key, 'created_at': now},
    }
    if last_tweet_id:
        update_ops['$max'] = {'last_tweet_id': str(last_tweet_id)}
    db.collection_state.update_one({'key': key}, update_ops, upsert=True)


def get_collection_state(key: str) -> Optional[Dict[str, Any]]:
    return db.collection_state.find_one({'key': key})


_profile_image_cache: Dict[str, tuple[Optional[str], float]] = {}  # {username: (url, timestamp)}


_PROFILE_IMAGE_CACHE_TTL = 3600  # 1 hour TTL


def get_profile_images_for_usernames(usernames: List[str]) -> Dict[str, Optional[str]]:
    """
    Batch lookup profile images from twitter_accounts collection.
    Returns a dict mapping username -> profile_image_url (or None if not found).
    Uses caching with 1 hour TTL to avoid repeated lookups.
    """
    import time
    current_time = time.time()
    result = {}
    usernames_to_lookup = []

    # Check cache first (with TTL validation)
    for username in usernames:
        if username in _profile_image_cache:
            cached_url, cached_time = _profile_image_cache[username]
            if current_time - cached_time < _PROFILE_IMAGE_CACHE_TTL:
                result[username] = cached_url
            else:
                # Cache expired
                del _profile_image_cache[username]
                usernames_to_lookup.append(username)
        else:
            usernames_to_lookup.append(username)

    # Lookup remaining usernames from DB
    if usernames_to_lookup:
        accounts = list(db.twitter_accounts.find(
            {'username': {'$in': usernames_to_lookup}},
            {'username': 1, 'profile_image_url': 1}
        ))

        for account in accounts:
            username = account.get('username')
            profile_url = account.get('profile_image_url')
            result[username] = profile_url
            _profile_image_cache[username] = (profile_url, current_time)

        # Cache None for usernames not found
        for username in usernames_to_lookup:
            if username not in result:
                result[username] = None
                _profile_image_cache[username] = (None, current_time)

    return result
