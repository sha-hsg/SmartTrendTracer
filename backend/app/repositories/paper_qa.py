"""Data access for paper Q&A: papers by id and the per-paper chunk cache (paper_chunks)."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.database.mongodb import get_database
from app.repositories import paper_feed

db = get_database()


def find_papers(ids: List[str]) -> List[Dict[str, Any]]:
    oids = [ObjectId(i) for i in ids if ObjectId.is_valid(i)]
    return list(db.papers.find({'_id': {'$in': oids}}, {'title': 1, 'content': 1}))


def paper_ids_for_concept(name: str) -> List[str]:
    """Papers tagged with a concept (same lookup as the paper feed)."""
    return paper_feed.paper_ids_for_concept(name)


def get_chunks(paper_id: str) -> Optional[Dict[str, Any]]:
    return db.paper_chunks.find_one({'_id': paper_id})


def save_chunks(paper_id: str, content_hash: str, model: str, chunks: List[Dict[str, Any]]) -> None:
    db.paper_chunks.replace_one({'_id': paper_id}, {
        'content_hash': content_hash, 'model': model, 'chunks': chunks,
        'created_at': datetime.now(timezone.utc)}, upsert=True)


def find_papers_for_scope(ids: List[str]) -> List[Dict[str, Any]]:
    """Title and whether full text exists, for the scope preview in the UI."""
    oids = [ObjectId(i) for i in ids if ObjectId.is_valid(i)]
    return [{'id': str(p['_id']), 'title': p.get('title', ''), 'has_text': bool((p.get('content') or '').strip())}
            for p in db.papers.find({'_id': {'$in': oids}}, {'title': 1, 'content': 1})]
