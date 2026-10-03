"""
Questions to one paper or a collection of papers, answered from their full
text with section-level citations.

The paper markdown (Marker output) is split at its headings; long sections
are split again at paragraph boundaries, reference lists are dropped. Chunks
are embedded once with the RAG embedding model and cached per paper in
paper_chunks (invalidated when the content or the model changes). A question
is embedded, the closest chunks across the selected papers are retrieved (at
most MAX_PER_PAPER per paper so one long paper cannot crowd out the rest),
and the LLM (task rag_answer, prompt paper_qa) answers citing [n].
"""
from __future__ import annotations

import hashlib
import logging
import re
from typing import Any, Dict, List, Optional

import numpy as np

from app.config import settings
from app.repositories import paper_qa as repo
from app.repositories.errors import InvalidInputError

logger = logging.getLogger(__name__)

CHUNK_CHARS = 2000
MIN_CHUNK_CHARS = 150
TOP_K = 8
MAX_PER_PAPER = 4
MAX_PAPERS = 40

_HEADING = re.compile(r'^(#{1,6})\s+(.*)$')
_REFERENCES = re.compile(r'^\s*(\d+\.?\s*)?(references|bibliography|literatur(verzeichnis)?)\s*$', re.I)


def clean_heading(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)                         # <span id=..>, <sup>
    text = text.replace('\\[', '[').replace('\\]', ']')       # Marker escapes brackets
    text = re.sub(r'\[(\[?[^\]]*\]?)\]\([^)]*\)', r'\1', text)  # [label](link), [[label]](link)
    return ' '.join(text.split()).strip(' #*') or 'Untitled section'


def _split_long(text: str) -> List[str]:
    if len(text) <= CHUNK_CHARS:
        return [text]
    parts, current = [], ''
    for para in re.split(r'\n\s*\n', text):
        if current and len(current) + len(para) > CHUNK_CHARS:
            parts.append(current)
            current = ''
        current = f'{current}\n\n{para}' if current else para
        while len(current) > CHUNK_CHARS * 1.5:            # a single huge paragraph
            parts.append(current[:CHUNK_CHARS])
            current = current[CHUNK_CHARS:]
    if current.strip():
        parts.append(current)
    return parts


def chunk_markdown(markdown: str) -> List[Dict[str, str]]:
    """[{heading, text}] from paper markdown; reference lists are skipped."""
    sections: List[Dict[str, Any]] = []
    heading, level, lines, skipping = 'Beginning', 0, [], False
    skip_level = 0

    def flush():
        body = '\n'.join(lines).strip()
        if body and not skipping:
            sections.append({'heading': heading, 'text': body})

    for line in (markdown or '').splitlines():
        m = _HEADING.match(line)
        if m:
            flush()
            lines = []
            level, heading = len(m.group(1)), clean_heading(m.group(2))
            if _REFERENCES.match(heading):
                skipping, skip_level = True, level
            elif skipping and level <= skip_level:
                skipping = False
            continue
        lines.append(line)
    flush()

    # merge tiny sections (figure captions, stray headings) into the next one
    merged: List[Dict[str, str]] = []
    carry = ''
    for s in sections:
        text = f"{carry}\n\n{s['text']}".strip() if carry else s['text']
        if len(text) < MIN_CHUNK_CHARS:
            carry = text
            continue
        carry = ''
        merged.extend({'heading': s['heading'], 'text': part} for part in _split_long(text))
    if carry and merged:
        merged[-1]['text'] += f'\n\n{carry}'
    elif carry:
        merged.append({'heading': sections[-1]['heading'], 'text': carry})
    return merged


def _embed(texts: List[str], is_query: bool = False) -> np.ndarray:
    from app.services.rag import get_embedding, get_embeddings_batch, init_embedding_clients
    use_gemini, openai_client = init_embedding_clients(settings.google_api_key, settings.openai_api_key)
    if is_query:
        return get_embedding(texts[0], use_gemini, openai_client, {}, is_query=True).reshape(-1)
    vectors, failed = get_embeddings_batch(texts, use_gemini, openai_client, {})
    if failed:
        raise RuntimeError(f'{len(failed)} of {len(texts)} chunks could not be embedded; try again')
    return vectors


def _embedding_model() -> str:
    from app.services.rag import get_rag_embedding_config
    return get_rag_embedding_config()['primary']['model']


def paper_chunks(paper: Dict[str, Any], model: str, embed=_embed) -> List[Dict[str, Any]]:
    """Chunks with vectors for one paper, from cache or freshly embedded."""
    content = paper.get('content') or ''
    content_hash = hashlib.md5(content.encode()).hexdigest()
    cached = repo.get_chunks(str(paper['_id']))
    if cached and cached.get('content_hash') == content_hash and cached.get('model') == model:
        return cached['chunks']
    chunks = chunk_markdown(content)
    if not chunks:
        return []
    title = paper.get('title', '')
    vectors = embed([f"Paper: {title}\nSection: {c['heading']}\n{c['text']}" for c in chunks])
    out = [{**c, 'vector': [float(x) for x in v]} for c, v in zip(chunks, vectors)]
    repo.save_chunks(str(paper['_id']), content_hash, model, out)
    logger.info(f"Embedded {len(out)} chunks for paper {paper['_id']}")
    return out


def resolve_papers(paper_ids: Optional[List[str]], concept: Optional[str]) -> List[Dict[str, Any]]:
    ids = list(paper_ids or [])
    if concept:
        ids += repo.paper_ids_for_concept(concept)
    ids = list(dict.fromkeys(ids))
    if not ids:
        raise InvalidInputError('Select at least one paper or a concept with tagged papers')
    papers = [p for p in repo.find_papers(ids[:MAX_PAPERS]) if (p.get('content') or '').strip()]
    if not papers:
        raise InvalidInputError('None of the selected papers has processed full text yet')
    return papers


def retrieve(question_vec: np.ndarray, per_paper: Dict[str, List[Dict[str, Any]]],
             k: int = TOP_K, max_per_paper: int = MAX_PER_PAPER) -> List[Dict[str, Any]]:
    scored = []
    q = question_vec / (np.linalg.norm(question_vec) or 1)
    for paper_id, chunks in per_paper.items():
        for c in chunks:
            v = np.asarray(c['vector'])
            scored.append((float(np.dot(q, v / (np.linalg.norm(v) or 1))), paper_id, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    picked, per_count = [], {}
    for score, paper_id, c in scored:
        if per_count.get(paper_id, 0) >= max_per_paper:
            continue
        per_count[paper_id] = per_count.get(paper_id, 0) + 1
        picked.append({'paper_id': paper_id, 'heading': c['heading'], 'text': c['text'], 'score': round(score, 4)})
        if len(picked) == k:
            break
    return picked


def ask(question: str, paper_ids: Optional[List[str]] = None, concept: Optional[str] = None,
        llm=None, embed=_embed) -> Dict[str, Any]:
    question = (question or '').strip()
    if not question:
        raise InvalidInputError('Please enter a question')
    papers = resolve_papers(paper_ids, concept)
    model = _embedding_model()
    per_paper = {str(p['_id']): paper_chunks(p, model, embed) for p in papers}
    titles = {str(p['_id']): p.get('title', '') for p in papers}
    hits = retrieve(embed([question], is_query=True), per_paper)

    excerpts = '\n\n'.join(f"[{i}] {titles[h['paper_id']]} — {h['heading']}\n{h['text']}"
                           for i, h in enumerate(hits, 1))
    if llm is None:
        from app.services.llm_manager import get_llm_manager
        llm = get_llm_manager()
    prompt = llm.get_prompt('paper_qa')
    answer = llm.complete_text('rag_answer', prompt['user_template'].format(question=question, excerpts=excerpts),
                               system_prompt=prompt['system'])
    return {
        'question': question,
        'answer': answer,
        'papers': [{'id': pid, 'title': titles[pid]} for pid in per_paper],
        'sources': [{'n': i, 'paper_id': h['paper_id'], 'title': titles[h['paper_id']], 'section': h['heading'],
                     'excerpt': h['text'][:600], 'score': h['score']} for i, h in enumerate(hits, 1)],
    }
