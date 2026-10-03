"""Paper feed data: subscriptions (arXiv queries) and found candidates."""
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.database.mongodb import concept_id_query_variants, get_database
from app.repositories.errors import NotFoundError

db = get_database()


def _oid(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise NotFoundError('Not found')
    return ObjectId(value)


# --- subscriptions ------------------------------------------------------------

def list_subscriptions(active_only: bool = False) -> List[Dict[str, Any]]:
    query = {'active': True} if active_only else {}
    return list(db.feed_subscriptions.find(query).sort('created_at', 1))


def create_subscription(name: str, query: str, concept: Optional[str], max_results: int) -> str:
    doc = {'name': name, 'query': query, 'concept': concept or None, 'max_results': max_results,
           'active': True, 'created_at': datetime.now(timezone.utc)}
    return str(db.feed_subscriptions.insert_one(doc).inserted_id)


def update_subscription(sub_id: str, fields: Dict[str, Any]) -> None:
    if db.feed_subscriptions.update_one({'_id': _oid(sub_id)}, {'$set': fields}).matched_count == 0:
        raise NotFoundError('Subscription not found')


def delete_subscription(sub_id: str) -> None:
    """Delete a subscription and its still-open candidates (imported ones stay)."""
    oid = _oid(sub_id)
    if db.feed_subscriptions.delete_one({'_id': oid}).deleted_count == 0:
        raise NotFoundError('Subscription not found')
    db.feed_candidates.delete_many({'subscription_id': oid, 'status': 'new'})


def mark_subscription_run(sub_id: ObjectId, found: int) -> None:
    db.feed_subscriptions.update_one({'_id': sub_id}, {'$set': {
        'last_run': datetime.now(timezone.utc), 'last_found': found}})


# --- candidates ---------------------------------------------------------------

def arxiv_id_known(arxiv_id: str) -> bool:
    """True when the paper is already in STT or was suggested before (any version)."""
    pattern = {'$regex': f'^{re.escape(arxiv_id)}(v\\d+)?$'}
    return bool(db.papers.find_one({'arxiv_id': pattern}, {'_id': 1})
                or db.feed_candidates.find_one({'arxiv_id': arxiv_id}, {'_id': 1}))


def title_known(title: str) -> bool:
    if not title.strip():
        return False
    return bool(db.papers.find_one(
        {'title': {'$regex': f'^\\s*{re.escape(title.strip())}\\s*$', '$options': 'i'}}, {'_id': 1}))


def insert_candidate(doc: Dict[str, Any]) -> None:
    db.feed_candidates.insert_one(doc)


def list_candidates(status: str = 'new', limit: int = 200) -> List[Dict[str, Any]]:
    return list(db.feed_candidates.find({'status': status})
                .sort([('score', -1), ('published', -1)]).limit(limit))


def count_candidates(status: str = 'new', since: Optional[datetime] = None) -> int:
    query: Dict[str, Any] = {'status': status}
    if since:
        query['found_at'] = {'$gte': since}
    return db.feed_candidates.count_documents(query)


def get_candidate(cand_id: str) -> Dict[str, Any]:
    doc = db.feed_candidates.find_one({'_id': _oid(cand_id)})
    if not doc:
        raise NotFoundError('Candidate not found')
    return doc


def set_candidate_status(cand_id: ObjectId, status: str, paper_id: Optional[str] = None) -> None:
    fields: Dict[str, Any] = {'status': status, 'decided_at': datetime.now(timezone.utc)}
    if paper_id:
        fields['paper_id'] = paper_id
    db.feed_candidates.update_one({'_id': cand_id}, {'$set': fields})


# --- relevance reference set --------------------------------------------------

def paper_ids_for_concept(name: str) -> List[str]:
    """Ids of papers tagged with the concept of this display name (all id forms)."""
    concept = db.tag_concepts_v2.find_one(
        {'display_name': {'$regex': f'^{re.escape(name.strip())}$', '$options': 'i'}}, {'_id': 1, 'id': 1})
    if not concept:
        return []
    variants = concept_id_query_variants(concept['_id'])
    if concept.get('id'):
        variants = list(variants) + [concept['id']]
    return [str(t['content_id']) for t in db.tag_instances.find(
        {'content_type': 'paper', 'concept_id': {'$in': variants}}, {'content_id': 1})]
