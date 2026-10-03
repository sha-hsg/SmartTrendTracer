"""Weekly digest API: list, read and (re)generate the weekly briefing."""
import asyncio
from typing import Any, Dict

from fastapi import APIRouter

from app.repositories import digests as repo
from app.services import digest_service

router = APIRouter()


def _serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    out = {k: v for k, v in doc.items() if k != '_id'}
    out['id'] = str(doc['_id'])
    return out


# Static routes before /{digest_id}

@router.get('')
def list_digests():
    return [_serialize(d) for d in repo.list_digests()]


@router.get('/latest')
def latest_digest():
    return _serialize(repo.get_digest())


@router.post('/generate')
async def generate_digest():
    """Build the digest for the last 7 days now (normally weekly by the scheduler)."""
    return await asyncio.to_thread(digest_service.generate_digest)


@router.get('/{digest_id}')
def get_digest(digest_id: str):
    return _serialize(repo.get_digest(digest_id))
