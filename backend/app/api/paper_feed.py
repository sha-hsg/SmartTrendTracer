"""
Paper feed API: saved arXiv queries ("subscriptions") and the papers they
found ("candidates") to import or dismiss. Runs daily via stt_scheduler.py.
"""
import asyncio
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.repositories import paper_feed as repo
from app.services import paper_feed_service as feed

logger = logging.getLogger(__name__)
router = APIRouter()


class SubscriptionIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    query: str = Field(..., min_length=2, description='arXiv query, e.g. abs:"agent memory" OR ti:RAG')
    concept: Optional[str] = Field(None, description='STT concept for ranking and for tagging imports')
    max_results: int = Field(25, ge=1, le=100)


class SubscriptionPatch(BaseModel):
    name: Optional[str] = None
    query: Optional[str] = None
    concept: Optional[str] = None
    max_results: Optional[int] = Field(None, ge=1, le=100)
    active: Optional[bool] = None


def _serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    out = {k: v for k, v in doc.items() if k != '_id'}
    out['id'] = str(doc['_id'])
    if 'subscription_id' in out:
        out['subscription_id'] = str(out['subscription_id'])
    return out


# Static routes first, /{id} routes after (FastAPI matches in registration order)

@router.get('/subscriptions')
def list_subscriptions():
    return [_serialize(s) for s in repo.list_subscriptions()]


@router.post('/subscriptions')
def create_subscription(body: SubscriptionIn):
    sub_id = repo.create_subscription(body.name.strip(), body.query.strip(),
                                      (body.concept or '').strip() or None, body.max_results)
    return {'id': sub_id}


@router.get('/candidates')
def list_candidates(status: str = 'new'):
    if status not in ('new', 'imported', 'dismissed'):
        raise HTTPException(status_code=400, detail='status must be new, imported or dismissed')
    return [_serialize(c) for c in repo.list_candidates(status)]


@router.post('/run')
async def run_feed_now():
    """Check all active subscriptions now (normally done daily by the scheduler)."""
    return await asyncio.to_thread(feed.run_feed)


@router.patch('/subscriptions/{sub_id}')
def update_subscription(sub_id: str, body: SubscriptionPatch):
    fields = {k: (v.strip() if isinstance(v, str) else v)
              for k, v in body.model_dump(exclude_unset=True).items()}
    if not fields:
        raise HTTPException(status_code=400, detail='Nothing to update')
    repo.update_subscription(sub_id, fields)
    return {'success': True}


@router.delete('/subscriptions/{sub_id}')
def delete_subscription(sub_id: str):
    repo.delete_subscription(sub_id)
    return {'success': True}


@router.post('/candidates/{cand_id}/import')
async def import_candidate(cand_id: str):
    try:
        return await asyncio.to_thread(feed.import_candidate, cand_id)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post('/candidates/{cand_id}/dismiss')
def dismiss_candidate(cand_id: str):
    feed.dismiss_candidate(cand_id)
    return {'success': True}
