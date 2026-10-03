"""
Paper Q&A: ask questions to one paper or a collection (by concept tag),
answered from the full text with section-level [n] citations.
"""
import asyncio
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.repositories import paper_qa as repo
from app.services import paper_qa_service as qa

router = APIRouter()


class QARequest(BaseModel):
    question: str = Field(..., min_length=2)
    paper_ids: Optional[List[str]] = None
    concept: Optional[str] = None


class ScopeRequest(BaseModel):
    paper_ids: Optional[List[str]] = None
    concept: Optional[str] = None


@router.post('/qa')
async def ask_papers(body: QARequest):
    """First question on a paper embeds its sections once (cached); later ones are fast."""
    return await asyncio.to_thread(qa.ask, body.question, body.paper_ids, body.concept)


@router.post('/qa/scope')
def qa_scope(body: ScopeRequest):
    """Which papers a selection covers, and whether they have full text."""
    ids = list(body.paper_ids or [])
    if body.concept:
        ids += repo.paper_ids_for_concept(body.concept)
    return {'papers': repo.find_papers_for_scope(list(dict.fromkeys(ids))[:qa.MAX_PAPERS])}
