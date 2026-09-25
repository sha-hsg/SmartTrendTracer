"""Article lookups and updates used by the articles API package."""
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.database.mongodb import get_database

db = get_database()


def find_article_by_any_id(article_id: str) -> Optional[Dict[str, Any]]:
    """Article by 24-hex ObjectId, or by legacy integer old_sqlite_id; never raises."""
    try:
        if len(article_id) == 24:
            return db.articles.find_one({'_id': ObjectId(article_id)})
        return db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
        return None


def set_article_fields(article_oid, fields: Dict[str, Any]) -> None:
    db.articles.update_one({'_id': article_oid}, {'$set': fields})


def add_article_concept_id(article_oid, concept_id) -> None:
    """Keep articles.concept_ids in sync with tag_instances."""
    db.articles.update_one({'_id': article_oid}, {'$addToSet': {'concept_ids': concept_id}})


def find_article_tag_instances(article_id_str: str, sqlite_id_str: str) -> List[Dict[str, Any]]:
    return list(db.tag_instances.find({
        'content_type': 'article',
        '$or': [
            {'content_id': article_id_str},
            {'content_id': sqlite_id_str}
        ]
    }))


def find_author_name(author_id) -> Optional[str]:
    """Author name by substack_authors _id, falling back to the legacy sqlite_id."""
    author_doc = db.substack_authors.find_one({'_id': author_id})
    if not author_doc:
        author_doc = db.substack_authors.find_one({'sqlite_id': author_id})
    return author_doc.get('name', 'Unknown') if author_doc else None
