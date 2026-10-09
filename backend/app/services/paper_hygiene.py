"""
Paper data hygiene, run daily by stt_scheduler.py (job paper_hygiene):
1. publication_date in one ISO form (repositories.paper_dates.normalize_all);
2. missing publication dates filled from arXiv (arxiv_id) or Crossref (doi),
   with a pause between arXiv calls (its API answers 429 otherwise);
3. arXiv ids without prefix/version (duplicate checks), the upload
   placeholder abstract replaced by the abstract from the processed text,
   file_md5 for stored PDFs (upload duplicate check);
4. GROBID references for up to GROBID_PER_RUN processed papers per run,
   synced into the references collection.
"""
from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Any, Dict

from app.repositories import paper_dates as repo

logger = logging.getLogger(__name__)

ARXIV_PAUSE = 3.0


def _arxiv_key(arxiv_id: str) -> str:
    """'arXiv:2512.24601v1' -> '2512.24601'."""
    return re.sub(r'v\d+$', '', re.sub(r'^arxiv:', '', arxiv_id.strip(), flags=re.I))


def backfill_dates(limit: int = 200, arxiv=None, crossref=None) -> Dict[str, int]:
    """Fill missing publication dates; returns counts."""
    stats = {'checked': 0, 'filled': 0, 'failed': 0}
    papers = repo.papers_missing_date(limit)
    if not papers:
        return stats
    if arxiv is None:
        from app.services.arxiv_import_service import get_arxiv_service
        arxiv = get_arxiv_service().fetch_metadata
    if crossref is None:
        import httpx
        from app.services import doi_import_service
        client = httpx.Client(timeout=30, follow_redirects=True,
                              headers={'User-Agent': 'SmartTrendTracer/1.0 (research tool)'})
        crossref = lambda doi: doi_import_service.fetch_metadata(client, doi).get('published_date')  # noqa: E731
    first_arxiv = True
    for p in papers:
        stats['checked'] += 1
        date = None
        try:
            if p.get('arxiv_id'):
                if not first_arxiv:
                    time.sleep(ARXIV_PAUSE)
                first_arxiv = False
                meta = arxiv(_arxiv_key(p['arxiv_id'])) or {}
                date = repo.canonical_date(meta.get('published'))
            if not date and p.get('doi'):
                date = repo.canonical_date(crossref(p['doi']))
        except Exception as e:                      # one bad id must not stop the run
            logger.warning(f"Date backfill failed for {p.get('_id')}: {type(e).__name__}: {e}")
        if date:
            repo.set_publication_date(p['_id'], date)
            stats['filled'] += 1
        else:
            stats['failed'] += 1
    return stats


def abstract_from_content(content: str) -> str:
    """First paragraph under an 'Abstract' heading of the processed markdown."""
    head = (content or '')[:20000]                      # the abstract is near the top, not in the references
    m = (re.search(r'(?ims)^[^\w\n]{0,6}abstract[^\w\n]{0,6}\n+(.+?)(?:\n\s*\n|\n#)', head)          # heading
         or re.search(r'(?ims)^[^\w\n]{0,6}abstract\b[*:.\t —-]+(.{200,2500}?)(?:\n\s*\n|\n#)', head))  # inline
    if not m:
        return ''
    text = re.sub(r'\s+', ' ', m.group(1)).strip()
    if 'http' in text or len(text) < 120 or not text[:1].isalpha():
        return ''
    return text


def fix_abstracts() -> Dict[str, int]:
    stats = {'fixed': 0, 'cleared': 0}
    for p in repo.papers_with_placeholder_abstract():
        content = p.get('content') or ''
        abstract = abstract_from_content(content)
        # '' beats a misleading placeholder; only processed papers count as checked
        repo.set_abstract(p['_id'], abstract, checked=bool(content) and not abstract)
        stats['fixed' if abstract else 'cleared'] += 1
    return stats


def fill_md5() -> int:
    import hashlib
    from app.paths import BACKEND_ROOT
    done = 0
    for p in repo.papers_without_md5():
        path = Path(p['pdf_path'])
        path = path if path.is_absolute() else BACKEND_ROOT / path
        if path.is_file():
            repo.set_file_md5(p['_id'], hashlib.md5(path.read_bytes()).hexdigest())
            done += 1
    return done


GROBID_PER_RUN = 40                # local container, ~20 s per paper: the backlog clears in ~10 days


def grobid_enrich(limit: int = GROBID_PER_RUN) -> Dict[str, int]:
    """References, TEI and citation contexts for processed papers GROBID has
    not seen (it only ever ran on demand: 11 of 227 papers added in 2026 had
    references). Import metadata (authors, sections) is kept."""
    from app.paths import resolve_stored_path
    from app.repositories import papers_grobid
    from app.services.grobid_service import GROBIDService
    stats = {'processed': 0, 'failed': 0, 'references': 0}
    papers = papers_grobid.papers_needing_grobid(limit)
    if not papers:
        return stats
    service = GROBIDService()
    if not service.is_alive():                    # do not mark papers while the server is down
        stats['skipped'] = 'GROBID server unavailable'
        return stats
    for p in papers:
        try:
            result = service.process_pdf(str(resolve_stored_path(p['pdf_path'])))
            if not result.get('success', True) and not result.get('references'):
                raise RuntimeError(result.get('error') or 'GROBID returned no result')
            out = papers_grobid.store_grobid_result(p, result, overwrite_authors=False)
            stats['processed'] += 1
            stats['references'] += out['synced']
        except Exception as e:
            papers_grobid.mark_grobid_failed(p['_id'], f'{type(e).__name__}: {e}')
            stats['failed'] += 1
    return stats


def run() -> Dict[str, Any]:
    normalized = repo.normalize_all()
    filled = backfill_dates()
    result = {'normalized': normalized['changed'], 'backfill': filled,
              'missing_after': repo.normalize_all(dry_run=True)['missing_after'],
              'arxiv_ids': repo.normalize_arxiv_ids(), 'abstracts': fix_abstracts(), 'md5': fill_md5(),
              'grobid': grobid_enrich()}
    logger.info(f'Paper hygiene: {result}')
    return result
