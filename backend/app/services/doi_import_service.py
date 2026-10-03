"""
Import a paper from a DOI or any paper link.

Accepted input: a bare DOI ("10.1145/..."), a doi.org link, an SSRN page link
(mapped to its DOI 10.2139/ssrn.N), any other link that contains a DOI, or an
arXiv link/id (delegated to the existing arXiv import).

Metadata comes from Crossref; open-access PDF locations from OpenAlex. Both
are free and need no API key. The first location that really returns a PDF
(starts with %PDF-) is stored — publisher landing pages and bot-block pages
are HTML and are rejected, which is how HTML files once ended up saved as
.pdf. Without an open PDF the paper is still created with its metadata and
flagged pdf_missing so the user can upload the file.
"""
from __future__ import annotations

import hashlib
import html
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.paths import ARXIV_PAPERS_DIR_REL, PAPERS_DIR_REL
from app.repositories import papers as papers_repo

logger = logging.getLogger(__name__)

HEADERS = {'User-Agent': 'SmartTrendTracer/1.0 (research paper import)'}
MAX_PDF_BYTES = 100 * 1024 * 1024

_DOI_RE = re.compile(r'\b(10\.\d{4,9}/[^\s"<>?#]+)', re.I)
_ARXIV_RE = re.compile(r'(?:arxiv\.org/(?:abs|pdf)/|^arxiv:\s*|^)(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?$', re.I)
_SSRN_RE = re.compile(r'ssrn\.com/(?:sol3/papers\.cfm\?abstract_id=|abstract=)(\d+)', re.I)


class DOIImportError(Exception):
    """Input could not be resolved to a paper (maps to HTTP 4xx in the API)."""


def parse_identifier(text: str) -> Tuple[str, str]:
    """Return ('arxiv', id) or ('doi', doi) for user input; raise DOIImportError otherwise."""
    value = (text or '').strip()
    if not value:
        raise DOIImportError('Please enter a DOI or a paper link')
    arxiv = _ARXIV_RE.search(value.rstrip('/'))
    if arxiv and ('arxiv' in value.lower() or re.fullmatch(r'\d{4}\.\d{4,5}(v\d+)?', value)):
        return 'arxiv', arxiv.group(1)
    ssrn = _SSRN_RE.search(value)
    if ssrn:
        return 'doi', f'10.2139/ssrn.{ssrn.group(1)}'
    doi = _DOI_RE.search(value)
    if doi:
        doi_value = doi.group(1).rstrip('.,;)').lower()
        arxiv_doi = re.fullmatch(r'10\.48550/arxiv\.(\d{4}\.\d{4,5})(v\d+)?', doi_value)
        if arxiv_doi:  # arXiv DataCite DOI -> richer arXiv import
            return 'arxiv', arxiv_doi.group(1)
        return 'doi', doi_value
    raise DOIImportError(f'No DOI or arXiv id found in "{value[:100]}"')


def _clean_abstract(raw: Optional[str]) -> str:
    """Crossref abstracts are JATS XML ("<jats:p>...")."""
    if not raw:
        return ''
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = html.unescape(text)
    text = re.sub(r'^\s*Abstract\s*', '', ' '.join(text.split()), flags=re.I)
    return text


def _abstract_from_inverted_index(index: Optional[Dict[str, List[int]]]) -> str:
    if not index:
        return ''
    positions = [(pos, word) for word, poss in index.items() for pos in poss]
    return ' '.join(word for _, word in sorted(positions))


def _join_title(title: str, subtitle: str) -> str:
    """Crossref keeps the subtitle separately ("On the Dangers of Stochastic Parrots" + "Can Language Models Be Too Big?")."""
    clean = lambda t: html.unescape(' '.join((t or '').split())).replace('&nbsp;', '').replace('\xa0', ' ').strip()
    title, subtitle = clean(title), clean(subtitle)
    if subtitle and subtitle.lower() not in title.lower():
        return f'{title}: {subtitle}'
    return title


def fetch_metadata(client: httpx.Client, doi: str) -> Dict[str, Any]:
    """Crossref metadata for a DOI; raises DOIImportError when the DOI is unknown."""
    r = client.get(f'https://api.crossref.org/works/{doi}')
    if r.status_code == 404:
        raise DOIImportError(f'DOI {doi} is not registered at Crossref')
    r.raise_for_status()
    m = r.json()['message']
    authors = [' '.join(p for p in (a.get('given'), a.get('family')) if p) or a.get('name', '')
               for a in m.get('author', [])]
    parts = (m.get('published') or m.get('issued') or {}).get('date-parts', [[None]])[0]
    date = '-'.join(f'{p:02d}' if i else str(p) for i, p in enumerate(parts) if p) if parts and parts[0] else ''
    container = (m.get('container-title') or [''])[0]
    return {
        'title': _join_title((m.get('title') or [''])[0], (m.get('subtitle') or [''])[0]),
        'authors': [a for a in authors if a],
        'published_date': date,
        'venue': container,
        'venue_type': m.get('type', ''),
        'abstract': _clean_abstract(m.get('abstract')),
        'url': m.get('URL') or f'https://doi.org/{doi}',
    }


def fetch_open_pdf_urls(client: httpx.Client, doi: str) -> Tuple[List[str], str]:
    """Open-access PDF candidates from OpenAlex (best first) and its abstract, if any."""
    r = client.get(f'https://api.openalex.org/works/doi:{doi}')
    if r.status_code == 404:
        return [], ''
    r.raise_for_status()
    w = r.json()
    urls: List[str] = []
    for loc in [w.get('best_oa_location')] + (w.get('locations') or []):
        if loc and loc.get('pdf_url') and loc['pdf_url'] not in urls:
            urls.append(loc['pdf_url'])
    oa_url = (w.get('open_access') or {}).get('oa_url')
    if oa_url and oa_url not in urls:
        urls.append(oa_url)
    return urls, _abstract_from_inverted_index(w.get('abstract_inverted_index'))


def download_first_pdf(client: httpx.Client, urls: List[str]) -> Optional[Tuple[str, bytes]]:
    """First URL that returns a real PDF, as (url, bytes); None when none does."""
    for url in urls:
        try:
            with client.stream('GET', url, follow_redirects=True) as r:
                if r.status_code != 200:
                    logger.info(f'PDF candidate {url}: HTTP {r.status_code}')
                    continue
                data = bytearray()
                for chunk in r.iter_bytes():
                    data.extend(chunk)
                    if len(data) > MAX_PDF_BYTES:
                        break
            if bytes(data[:5]) == b'%PDF-' and len(data) <= MAX_PDF_BYTES:
                return url, bytes(data)
            logger.info(f'PDF candidate {url}: not a PDF ({bytes(data[:15])!r})')
        except httpx.HTTPError as e:
            logger.info(f'PDF candidate {url}: {type(e).__name__}')
    return None


def _pdf_filename(doi: str, title: str) -> str:
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    digest = hashlib.md5(doi.encode()).hexdigest()[:8]
    slug = re.sub(r'[^A-Za-z0-9]+', '_', title).strip('_')[:120] or 'paper'
    return f'{stamp}_{digest}_{slug}.pdf'


def import_doi(doi: str, client: Optional[httpx.Client] = None) -> Dict[str, Any]:
    """Create a paper for a DOI. Returns a result dict for the API layer."""
    existing = papers_repo.find_paper_by_doi(doi)
    if existing:
        return {'success': False, 'existing': True, 'paper_id': str(existing['_id']),
                'message': f'Paper with DOI {doi} is already in the database'}

    own_client = client is None
    client = client or httpx.Client(headers=HEADERS, timeout=30)
    try:
        meta = fetch_metadata(client, doi)
        try:
            pdf_urls, oa_abstract = fetch_open_pdf_urls(client, doi)
        except httpx.HTTPError as e:
            logger.warning(f'OpenAlex lookup failed for {doi}: {e}')
            pdf_urls, oa_abstract = [], ''
        pdf = download_first_pdf(client, pdf_urls)
    finally:
        if own_client:
            client.close()

    same_title = papers_repo.find_paper_by_title(meta['title'])
    if same_title:
        # e.g. imported earlier from arXiv, where no DOI is stored
        return {'success': False, 'existing': True, 'paper_id': str(same_title['_id']),
                'message': f'Paper "{meta["title"]}" is already in the database'}

    paper_doc: Dict[str, Any] = {
        'title': meta['title'] or doi,
        'authors': ', '.join(meta['authors']),
        'authors_list': [{'name': n, 'position': i} for i, n in enumerate(meta['authors'])],
        'abstract': meta['abstract'] or oa_abstract,
        'doi': doi,
        'url': meta['url'],
        'published_date': meta['published_date'],
        'publication_date': meta['published_date'],
        'created_at': datetime.now(timezone.utc),
        'processed': False,
        'source': 'doi',
        'import_source': 'doi',
        'import_url': f'https://doi.org/{doi}',
        'paper_type': 'research',
    }
    if meta['venue']:
        paper_doc['journal' if meta['venue_type'] == 'journal-article' else 'conference'] = meta['venue']

    if pdf:
        pdf_url, data = pdf
        save_dir = PAPERS_DIR_REL
        save_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = save_dir / _pdf_filename(doi, paper_doc['title'])
        pdf_path.write_bytes(data)
        paper_doc.update({'pdf_path': str(pdf_path), 'pdf_url': pdf_url})
    else:
        paper_doc['pdf_missing'] = True

    paper_id = str(papers_repo.insert_paper(paper_doc).inserted_id)
    logger.info(f'Imported DOI {doi} as paper {paper_id} (pdf: {bool(pdf)})')
    return {
        'success': True,
        'paper_id': paper_id,
        'doi': doi,
        'title': paper_doc['title'],
        'authors': paper_doc['authors'],
        'has_pdf': bool(pdf),
        'pdf_url': pdf[0] if pdf else None,
        'pdf_candidates': len(pdf_urls),
        'message': (f'Imported "{paper_doc["title"]}" with PDF' if pdf else
                    f'Imported "{paper_doc["title"]}" without PDF — no open-access PDF found '
                    f'({len(pdf_urls)} candidate(s) blocked or not a PDF); upload it manually'),
    }


def import_arxiv(arxiv_id: str) -> Dict[str, Any]:
    """Delegate to the existing arXiv import (same document as /api/arxiv/import)."""
    from app.services.arxiv_import_service import get_arxiv_service
    result = get_arxiv_service().import_paper(arxiv_id, download_dir=str(ARXIV_PAPERS_DIR_REL))
    if not result.get('success'):
        raise DOIImportError(f"arXiv import failed: {result.get('error', 'unknown error')}")
    paper_id = papers_repo.save_arxiv_import(result)
    return {'success': True, 'paper_id': paper_id, 'arxiv_id': arxiv_id,
            'title': result['metadata']['title'], 'has_pdf': True,
            'message': f"Imported arXiv {arxiv_id}: {result['metadata']['title']}"}


def import_identifier(text: str) -> Dict[str, Any]:
    """Entry point: DOI, doi.org/SSRN/publisher link or arXiv link/id."""
    kind, value = parse_identifier(text)
    return import_arxiv(value) if kind == 'arxiv' else import_doi(value)
