"""Content lookups for automatic concept tagging (app.services.concept_tagging)."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.database.mongodb import get_database
from app.repositories.articles import find_article_by_any_id
from app.repositories.papers import find_paper_by_any_id

db = get_database()

COLLECTIONS = {'tweet': 'tweets', 'article': 'articles', 'paper': 'papers'}


def untagged_ids(content_type: str, limit: Optional[int] = None) -> List[str]:
    """Ids of items without any tag_instances row (a concept_id-null row marks
    "tagged, nothing found"). Papers only when processed research papers."""
    tagged = set(map(str, db.tag_instances.distinct('content_id', {'content_type': content_type})))
    query: Dict[str, Any] = {}
    if content_type == 'paper':
        query = {'paper_type': {'$ne': 'review'}, 'content': {'$nin': [None, '']}}
    sort_field = {'tweet': 'created_at', 'article': 'published_at', 'paper': 'created_at'}[content_type]
    ids = [str(d['_id']) for d in db[COLLECTIONS[content_type]].find(query, {'_id': 1}).sort(sort_field, -1)
           if str(d['_id']) not in tagged]
    return ids[:limit] if limit else ids


def load_item(content_type: str, content_id: str) -> Optional[Dict[str, Any]]:
    """title / author / text of one item, or None."""
    if content_type == 'tweet':
        t = db.tweets.find_one({'_id': content_id})
        if not t:
            return None
        return {'title': '', 'author': f"@{t.get('author_username', '')}",
                'text': t.get('full_text') or t.get('text') or ''}
    if content_type == 'article':
        a = find_article_by_any_id(content_id)
        if not a:
            return None
        return {'title': a.get('title', ''), 'author': a.get('author_name') or '',
                'text': a.get('content_markdown') or a.get('content') or ''}
    p = find_paper_by_any_id(content_id)
    if not p:
        return None
    authors = p.get('authors') or ''
    if isinstance(authors, list):
        authors = ', '.join(a if isinstance(a, str) else a.get('name', '') for a in authors[:6])
    abstract = p.get('abstract') or ''
    if abstract.startswith('PDF uploaded'):          # placeholder written at upload time
        abstract = ''
    return {'title': p.get('title', ''), 'author': authors,
            'text': (f"Abstract: {abstract}\n\n" if abstract else '') + (p.get('content') or '')}


def mark_no_concepts(content_type: str, content_id: str) -> None:
    """Record "tagged, but no concepts found" so the item is not retried."""
    db.tag_instances.update_one(
        {'content_type': content_type, 'content_id': str(content_id), 'concept_id': None},
        {'$setOnInsert': {'content_type': content_type, 'content_id': str(content_id), 'concept_id': None,
                          'display_name': '_no_concepts', 'created_at': datetime.now(timezone.utc),
                          'source': 'auto_annotation'}},
        upsert=True)
