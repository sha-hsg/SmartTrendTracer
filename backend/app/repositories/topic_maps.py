"""Storage for the bubble topic map (topic_episodes service): document dates
for the RAG-indexed content, the computed maps and the episode-name cache."""
from typing import Any, Dict, List, Optional

from pymongo import DESCENDING

from app.database.mongodb import get_database
from app.repositories.errors import NotFoundError

db = get_database()

KEEP_MAPS = 8


def paper_import_dates() -> Dict[str, Any]:
    """Paper id -> import date (papers enter the bubble when imported)."""
    return {str(p['_id']): p.get('created_at') for p in db.papers.find({}, {'created_at': 1})}


def article_meta() -> Dict[str, Dict[str, Any]]:
    """Article id -> author_name / published_at."""
    return {str(a['_id']): a for a in db.articles.find({}, {'author_name': 1, 'published_at': 1})}


def save_topic_map(doc: Dict[str, Any]) -> str:
    """Store a computed map; older maps beyond KEEP_MAPS are removed."""
    new_id = db.topic_maps.insert_one(doc).inserted_id
    old = [d['_id'] for d in db.topic_maps.find({}, {'_id': 1}).sort('created_at', DESCENDING).skip(KEEP_MAPS)]
    if old:
        db.topic_maps.delete_many({'_id': {'$in': old}})
    return str(new_id)


def latest_topic_map(projection: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    return db.topic_maps.find_one({}, projection, sort=[('created_at', DESCENDING)])


def latest_episode(episode_id: int) -> Dict[str, Any]:
    """One episode of the latest map (with examples and movers)."""
    doc = db.topic_maps.find_one({}, {'episodes': {'$elemMatch': {'id': episode_id}}},
                                 sort=[('created_at', DESCENDING)])
    if not doc or not doc.get('episodes'):
        raise NotFoundError(f'Episode {episode_id} not found')
    return doc['episodes'][0]


def episode_names() -> List[Dict[str, Any]]:
    """Name cache: {name, noise, doc_keys} per named episode."""
    return list(db.episode_names.find({}, {'_id': 0}))


def add_episode_names(items: List[Dict[str, Any]]) -> None:
    if items:
        db.episode_names.insert_many([dict(i) for i in items])
