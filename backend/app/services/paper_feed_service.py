"""
Paper feed: finds new arXiv papers for saved queries and proposes them.

Each subscription is an arXiv query (e.g. abs:"agent memory"), optionally
linked to an STT concept. run_feed() fetches the newest matches, drops papers
already in STT or suggested before, and stores the rest as candidates.

Relevance: when the subscription names a concept, candidates are ranked by
cosine similarity to the centroid of the papers you already tagged with it.
Those paper vectors are read from the RAG FAISS index (no API cost); only the
candidate abstracts are embedded, with the same model as the index.

Run daily by stt_scheduler.py (job paper_feed) and on demand via the API.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np

from app.config import settings
from app.paths import ARXIV_PAPERS_DIR_REL, RAG_INDEX_CONCEPTS
from app.repositories import paper_feed as repo
from app.repositories import papers as papers_repo

logger = logging.getLogger(__name__)


def _strip_version(arxiv_id: str) -> str:
    base, _, version = arxiv_id.rpartition('v')
    return base if base and version.isdigit() else arxiv_id


def candidate_text(title: str, abstract: str) -> str:
    """Same shape as the RAG paper documents, so the vectors are comparable."""
    return f"Paper: {title}\nAbstract: {abstract}\n"


def concept_centroid(index, metadata, paper_ids: List[str]) -> Optional[np.ndarray]:
    """Normalized mean of the indexed vectors of these papers; None when none is indexed."""
    wanted = set(paper_ids)
    positions = [pos for pos, m in enumerate(metadata)
                 if m.get('type') == 'paper' and m.get('id') in wanted and not m.get('stale')]
    if not positions:
        return None
    centroid = np.mean([index.reconstruct(pos) for pos in positions], axis=0)
    norm = np.linalg.norm(centroid)
    return centroid / norm if norm else None


class PaperFeed:
    def __init__(self, search=None, embed=None, index_state=None):
        """search(query, max_results) -> list of arXiv dicts; embed(texts) -> (vectors, failed).
        Defaults use the arXiv service and the RAG embedding model."""
        self._search = search or self._arxiv_search
        self._embed = embed or self._rag_embed
        self._index_state = index_state

    @staticmethod
    def _arxiv_search(query: str, max_results: int):
        from app.services.arxiv_import_service import get_arxiv_service
        return get_arxiv_service().search_papers(query, max_results=max_results,
                                                 sort_by='submittedDate', summary_chars=None)

    @staticmethod
    def _rag_embed(texts: List[str]):
        from app.services.rag import get_embeddings_batch, init_embedding_clients
        use_gemini, openai_client = init_embedding_clients(settings.google_api_key, settings.openai_api_key)
        return get_embeddings_batch(texts, use_gemini, openai_client, {})

    def _index(self):
        if self._index_state is None:
            from app.services.rag import get_index_paths, load_index
            index, metadata, _ = load_index(get_index_paths(RAG_INDEX_CONCEPTS))
            self._index_state = (index, metadata or [])
        return self._index_state

    def run_subscription(self, sub: Dict[str, Any]) -> Dict[str, Any]:
        results = self._search(sub['query'], sub.get('max_results', 25)) or []
        fresh = []
        for paper in results:
            arxiv_id = _strip_version(paper['arxiv_id'])
            if repo.arxiv_id_known(arxiv_id) or repo.title_known(paper['title']):
                continue
            fresh.append({**paper, 'arxiv_id': arxiv_id})

        scores: List[Optional[float]] = [None] * len(fresh)
        if fresh and sub.get('concept'):
            index, metadata = self._index()
            centroid = concept_centroid(index, metadata, repo.paper_ids_for_concept(sub['concept'])) \
                if index is not None else None
            if centroid is not None:
                vectors, failed = self._embed([candidate_text(p['title'], p['summary']) for p in fresh])
                ok = [i for i in range(len(fresh)) if i not in set(failed)]
                for i, vec in zip(ok, vectors):
                    scores[i] = round(float(np.dot(vec, centroid)), 4)

        now = datetime.now(timezone.utc)
        for paper, score in zip(fresh, scores):
            repo.insert_candidate({
                'subscription_id': sub['_id'],
                'subscription_name': sub['name'],
                'concept': sub.get('concept'),
                'arxiv_id': paper['arxiv_id'],
                'title': paper['title'],
                'authors': paper.get('authors', []),
                'abstract': paper.get('summary', ''),
                'published': paper.get('published'),
                'url': paper.get('abs_url'),
                'pdf_url': paper.get('pdf_url'),
                'score': score,
                'found_at': now,
                'status': 'new',
            })
        repo.mark_subscription_run(sub['_id'], len(fresh))
        logger.info(f"Feed '{sub['name']}': {len(results)} results, {len(fresh)} new")
        return {'subscription': sub['name'], 'results': len(results), 'new': len(fresh)}

    def run(self) -> Dict[str, Any]:
        runs = [self.run_subscription(sub) for sub in repo.list_subscriptions(active_only=True)]
        return {'subscriptions': len(runs), 'new': sum(r['new'] for r in runs), 'runs': runs}


def run_feed() -> Dict[str, Any]:
    return PaperFeed().run()


def import_candidate(cand_id: str) -> Dict[str, Any]:
    """Import a candidate with the existing arXiv import and tag it with the subscription concept."""
    from app.services.arxiv_import_service import get_arxiv_service
    cand = repo.get_candidate(cand_id)
    if cand['status'] == 'imported' and cand.get('paper_id'):
        return {'paper_id': cand['paper_id'], 'title': cand['title'], 'already_imported': True}
    result = get_arxiv_service().import_paper(cand['arxiv_id'], download_dir=str(ARXIV_PAPERS_DIR_REL))
    if not result.get('success'):
        raise RuntimeError(f"arXiv import failed: {result.get('error', 'unknown error')}")
    paper_id = papers_repo.save_arxiv_import(result)
    if cand.get('concept'):
        # same path as tagging in the paper UI (tag instance + papers.concept_ids)
        from app.repositories.papers_concepts import add_concept_to_paper
        add_concept_to_paper(paper_id, cand['concept'])
    repo.set_candidate_status(cand['_id'], 'imported', paper_id)
    return {'paper_id': paper_id, 'title': cand['title'], 'already_imported': False}


def dismiss_candidate(cand_id: str) -> None:
    cand = repo.get_candidate(cand_id)
    repo.set_candidate_status(cand['_id'], 'dismissed')
