"""Documents of the bubble: the RAG index entries with date, author, concepts
and an author-debiased vector."""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Set, Tuple

import faiss
import numpy as np

from app.paths import RAG_INDEX_CONCEPTS
from app.repositories import topic_maps as repo
from app.services.rag import get_index_paths, load_index

START = datetime(2025, 1, 1, tzinfo=timezone.utc)
AUTHOR_DEBIAS = 1.0           # subtract the author's mean direction (voice), keep content
AUTHOR_CONCENTRATION = 0.6    # concept counts as author-specific above this share for one author
GENERIC = {'large language model', 'large language models', 'llm', 'llms', 'ai', 'artificial intelligence',
           'machine learning', 'deep learning', 'openai', 'google', 'anthropic', 'empirical study'}


def _aware(dt):
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return None
    if isinstance(dt, datetime) and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt if isinstance(dt, datetime) else None


def week_of(dt: datetime) -> str:
    return (dt - timedelta(days=dt.weekday())).date().isoformat()


def load_documents() -> Tuple[List[Dict[str, Any]], np.ndarray]:
    """Active index entries since START with their vectors.

    The indexed texts start with "Tweet by @x:" / "By: x", so vectors carry the
    author's voice; each author's mean direction is removed so that clustering
    follows content."""
    index, metadata, doc_map = load_index(get_index_paths(RAG_INDEX_CONCEPTS))
    if index is None:
        raise RuntimeError('RAG index not found — build it first (rebuild_rag_index.py)')
    paper_dates = repo.paper_import_dates()
    article_meta = repo.article_meta()
    docs = []
    for pos, m in enumerate(metadata):
        if m.get('stale'):
            continue
        if m['type'] == 'tweet':
            dt, author = m.get('created_at'), m.get('author')
        elif m['type'] == 'article':
            a = article_meta.get(m['id'], {})
            dt, author = a.get('published_at') or m.get('published_at'), a.get('author_name') or m.get('author')
        else:
            dt, author = paper_dates.get(m['id']), 'you (import)'
        dt = _aware(dt)
        if dt is None or dt < START:
            continue
        docs.append({'pos': pos, 'type': m['type'], 'id': m['id'], 'key': f"{m['type']}:{m['id']}",
                     'date': dt, 'week': week_of(dt), 'month': dt.strftime('%Y-%m'),
                     'author': author or '?', 'concepts': m.get('concepts', []),
                     'text': doc_map.get(pos, '')[:300]})
    vecs = np.stack([index.reconstruct(d['pos']) for d in docs]).astype('float32')
    faiss.normalize_L2(vecs)
    global_mean = vecs.mean(axis=0)
    by_author = defaultdict(list)
    for i, d in enumerate(docs):
        by_author[(d['type'], d['author'])].append(i)
    for ids in by_author.values():
        if len(ids) >= 5:
            vecs[ids] -= AUTHOR_DEBIAS * (vecs[ids].mean(axis=0) - global_mean)
    faiss.normalize_L2(vecs)
    return docs, vecs


def author_specific_concepts(docs) -> Set[str]:
    """Concepts mostly attached to one author describe the author, not a topic."""
    per = defaultdict(Counter)
    for d in docs:
        for c in set(d['concepts']):
            per[c][d['author']] += 1
    names = {d['author'].lower() for d in docs}
    out = set()
    for c, authors in per.items():
        total = sum(authors.values())
        if c.lower() in names or (total >= 5 and authors.most_common(1)[0][1] / total > AUTHOR_CONCENTRATION):
            out.add(c)
    return out


def concept_label(member_docs, ref_freq, n_ref, skip: Set[str], min_support: float, top: int = 3,
                  min_count: int = 2) -> str:
    """The concepts that stand out in member_docs against a reference
    distribution (lift weighted by support)."""
    freq = Counter(c for d in member_docs for c in set(d['concepts']))
    n = len(member_docs)
    scored = []
    for c, f in freq.items():
        if c.lower() in GENERIC or c in skip or f < max(min_count, min_support * n):
            continue
        lift = (f / n) / (ref_freq[c] / n_ref)
        scored.append((math.log(lift + 1) * (f / n), c))
    names = [c for _, c in sorted(scored, reverse=True)[:top]]
    return ' · '.join(names) if names else '(unlabelled)'
