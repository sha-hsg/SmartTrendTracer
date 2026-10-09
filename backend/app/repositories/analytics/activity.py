"""
Raw rows for the concept-activity cube (app.services.trend_core): every
tweet, article and research paper with its date and author, every tag
instance, and the concepts that occur. Bulk reads only — the cube is built
in memory and cached by the service.

Papers are dated by publication date (not import date): a bulk import of old
papers is not a trend. Papers without a usable publication date are left out.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from dateutil import parser as date_parser

from app.database.mongodb import get_database

CHANNELS = ('tweet', 'article', 'paper')


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def paper_publication_date(paper: Dict[str, Any]) -> Optional[datetime]:
    """publication_date / published_date as datetime; strings of mixed format
    are parsed, year-only values are rejected (they would pile up on Jan 1)."""
    for field in ('publication_date', 'published_date'):
        value = paper.get(field)
        if isinstance(value, datetime):
            return _aware(value)
        if isinstance(value, str) and len(value.strip()) >= 7:   # at least YYYY-MM
            try:
                parsed = date_parser.parse(value.strip(), default=datetime(2000, 1, 1))
            except (ValueError, OverflowError):
                continue
            return _aware(parsed)
    return None


def load_documents() -> List[Tuple[str, str, datetime, str]]:
    """(channel, content_id, date, author) for all dated content."""
    db = get_database()
    out = []
    for t in db.tweets.find({'created_at': {'$type': 'date'}}, {'created_at': 1, 'author_username': 1}):
        out.append(('tweet', str(t['_id']), _aware(t['created_at']), t.get('author_username') or '?'))
    for a in db.articles.find({'published_at': {'$type': 'date'}}, {'published_at': 1, 'author_name': 1}):
        out.append(('article', str(a['_id']), _aware(a['published_at']), a.get('author_name') or '?'))
    for p in db.papers.find({'paper_type': {'$ne': 'review'}},
                            {'publication_date': 1, 'published_date': 1}):
        date = paper_publication_date(p)
        if date:
            out.append(('paper', str(p['_id']), date, f"paper:{p['_id']}"))   # papers are independent sources
    return out


def load_tag_instances() -> List[Tuple[str, str, str]]:
    """(channel, content_id, concept_id as string) for tweets, articles, papers."""
    db = get_database()
    return [(ti['content_type'], str(ti['content_id']), str(ti['concept_id']))
            for ti in db.tag_instances.find({'content_type': {'$in': list(CHANNELS)},
                                             'concept_id': {'$nin': [None, '']}},
                                            {'_id': 0, 'content_type': 1, 'content_id': 1, 'concept_id': 1})]


def load_concepts(concept_ids) -> Dict[str, Dict[str, Any]]:
    """Concept id (string) -> display_name, slug, entity_type, color, parents."""
    from app.database.mongodb import concept_id_query_variants
    db = get_database()
    variants = [v for cid in concept_ids for v in concept_id_query_variants(cid)]
    out = {}
    for c in db.tag_concepts_v2.find({'_id': {'$in': variants}},
                                     {'display_name': 1, 'slug': 1, 'entity_type': 1, 'color': 1, 'parents': 1}):
        out[str(c['_id'])] = {'display_name': c.get('display_name') or c.get('slug') or str(c['_id']),
                              'slug': c.get('slug', ''), 'entity_type': c.get('entity_type') or 'topic',
                              'color': c.get('color'), 'parents': [str(p) for p in c.get('parents') or []]}
    return out
