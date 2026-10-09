"""Storage for the bubble topic map (topic_episodes service): document dates
for the RAG-indexed content, the computed maps and the episode-name cache."""
from typing import Any, Dict, List, Optional

from pymongo import DESCENDING

from app.database.mongodb import get_database
from app.repositories.errors import NotFoundError

db = get_database()

KEEP_MAPS = 8


def paper_dates() -> Dict[str, Any]:
    """Paper id -> publication date (a bulk import of old papers is not a
    burst); papers without a usable date are absent."""
    from app.repositories.analytics import paper_publication_date
    out = {}
    for p in db.papers.find({'paper_type': {'$ne': 'review'}}, {'publication_date': 1, 'published_date': 1}):
        date = paper_publication_date(p)
        if date:
            out[str(p['_id'])] = date
    return out


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


def episode_names(version: int) -> List[Dict[str, Any]]:
    """Name cache of one naming version: {name, noise, start, doc_keys}."""
    return list(db.episode_names.find({'v': version}, {'_id': 0}))


def add_episode_names(items: List[Dict[str, Any]]) -> None:
    if items:
        db.episode_names.insert_many([dict(i) for i in items])
