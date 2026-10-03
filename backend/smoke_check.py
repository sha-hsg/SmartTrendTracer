#!/usr/bin/env python
"""
STT smoke check: verifies that the services actually work, not just that a
port is open. Run at the end of start_stt.sh and on demand:

    venv/bin/python smoke_check.py          # fast checks (~5 s)
    venv/bin/python smoke_check.py --deep   # + real 1-page Marker conversion (~30-60 s)

Exit code 0 when everything passes, 1 otherwise. Each failure prints one
line with the probable cause and the log file to look at.

Background: on 2026-10-01 the backend died at startup (LiteLLM router), on
2026-09-24 Marker lost its packages, and on 2026-10-03 the RAG search failed
because its embedding model had been retired — all three went unnoticed
because start_stt.sh only checked ports.
"""
import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

import warnings

import httpx

# google.generativeai prints a FutureWarning on import; irrelevant for this check
warnings.filterwarnings('ignore', category=FutureWarning)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.config import settings  # noqa: E402  (env is read only in app.config)

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
LOG_DIR = PROJECT_DIR / 'logs'
BACKEND = f'http://localhost:{settings.backend_port}'
MARKER = 'http://localhost:8002'
MINERU = 'http://localhost:8003'
FRONTEND = 'http://localhost:3470'

GREEN, RED, YELLOW, RESET = '\033[0;32m', '\033[0;31m', '\033[0;33m', '\033[0m'
if not sys.stdout.isatty():
    GREEN = RED = YELLOW = RESET = ''

results = []


def report(ok: bool, name: str, detail: str = '', hint: str = ''):
    results.append(ok)
    mark = f'{GREEN}✓{RESET}' if ok else f'{RED}✗{RESET}'
    line = f'  {mark} {name}'
    if detail:
        line += f' — {detail}'
    print(line)
    if not ok and hint:
        print(f'      {YELLOW}→ {hint}{RESET}')


def last_error(log_name: str) -> str:
    """Last ERROR/Exception line of a log file, for a one-line diagnosis."""
    path = LOG_DIR / log_name
    if not path.exists():
        return f'logs/{log_name} not found'
    lines = path.read_text(errors='ignore').splitlines()[-400:]
    for line in reversed(lines):
        if 'ERROR' in line or 'Error:' in line or 'Exception' in line:
            return line.strip()[:220]
    return f'no error line in logs/{log_name}'


def get_json(client: httpx.Client, url: str):
    r = client.get(url)
    r.raise_for_status()
    return r.json()


def check_backend(client):
    try:
        health = get_json(client, f'{BACKEND}/health')
        cols = health.get('collections', {})
        ok = health.get('status') == 'healthy'
        report(ok, 'Backend + MongoDB',
               f"{cols.get('papers', '?')} papers, {cols.get('tweets', '?')} tweets",
               hint=f'see logs/backend.log: {last_error("backend.log")}')
        return ok
    except Exception as e:
        report(False, 'Backend + MongoDB', f'not reachable ({type(e).__name__})',
               hint=f'see logs/backend.log: {last_error("backend.log")}')
        return False


def check_llm(client):
    try:
        status = get_json(client, f'{BACKEND}/api/llm/status')
        models = get_json(client, f'{BACKEND}/api/llm/models')
        missing = [p for p, v in status.get('providers', {}).items() if not v.get('configured')]
        ok = bool(models) and not missing
        detail = f'{len(models)} routes'
        if missing:
            detail += f', no API key for: {", ".join(missing)}'
        report(ok, 'LLM routing', detail, hint='API keys belong in ~/.env; router config: backend/litellm_config.yaml')
    except Exception as e:
        report(False, 'LLM routing', f'{type(e).__name__}: {e}'[:160],
               hint=f'see logs/backend.log: {last_error("backend.log")}')


def check_pdf_service(client, name, url, log_name):
    try:
        health = get_json(client, f'{url}/health')
        ok = health.get('status') == 'healthy'
        report(ok, name, health.get('detail') or 'healthy' if ok else str(health)[:120],
               hint=f'see logs/{log_name}: {last_error(log_name)}')
        return ok
    except Exception as e:
        report(False, name, f'not reachable ({type(e).__name__})',
               hint=f'see logs/{log_name}: {last_error(log_name)}')
        return False


def check_marker_deep(client):
    """Convert one real PDF page with Marker (catches missing models/binaries)."""
    import pypdfium2 as pdfium
    sample = next((p for p in sorted((BACKEND_DIR / 'data' / 'papers').glob('**/*.pdf'))
                   if p.read_bytes()[:5] == b'%PDF-'), None)
    if sample is None:
        report(False, 'Marker conversion', 'no sample PDF in data/papers')
        return
    with tempfile.TemporaryDirectory() as tmp:
        one_page = Path(tmp) / 'smoke_check.pdf'
        src = pdfium.PdfDocument(str(sample))
        dst = pdfium.PdfDocument.new()
        dst.import_pages(src, [0])
        dst.save(str(one_page))
        start = time.time()
        try:
            with open(one_page, 'rb') as f:
                r = client.post(f'{MARKER}/convert', files={'file': ('smoke_check.pdf', f, 'application/pdf')},
                                data={'output_format': 'markdown', 'use_llm': 'false'}, timeout=600)
            body = r.json()
            words = len(str(body.get('content') or '').split())
            ok = r.status_code == 200 and words > 20
            report(ok, 'Marker conversion', f'{words} words from 1 page in {time.time() - start:.0f}s',
                   hint=f'HTTP {r.status_code}: {str(body)[:160]} — see logs/marker.log')
        except Exception as e:
            report(False, 'Marker conversion', f'{type(e).__name__}: {e}'[:160], hint='see logs/marker.log')


def check_rag(client):
    try:
        stats = get_json(client, f'{BACKEND}/api/rag/stats')
    except Exception as e:
        report(False, 'RAG search', f'stats not reachable ({type(e).__name__})', hint='see logs/backend.log')
        return
    llm_config = json.loads((BACKEND_DIR / 'llm.json').read_text())
    configured = llm_config['models']['rag_embedding']['primary']['model']
    built_with = stats.get('embedding_model')
    if not stats.get('is_ready'):
        report(False, 'RAG search', 'index not loaded', hint='build it: venv/bin/python rebuild_rag_index.py')
        return
    if built_with != configured:
        report(False, 'RAG search', f'index built with {built_with}, config uses {configured}',
               hint='queries fail until the index is rebuilt: venv/bin/python rebuild_rag_index.py')
        return
    # One real query embedding: catches retired models and missing keys
    try:
        from app.services.rag import get_embedding, init_embedding_clients
        use_gemini, openai_client = init_embedding_clients(settings.google_api_key, settings.openai_api_key)
        vec = get_embedding('smoke check', use_gemini, openai_client, {}, is_query=True)
        ok = vec.shape[-1] == llm_config['models']['rag_embedding']['primary']['dimension'] if use_gemini else True
        report(ok, 'RAG search', f"{stats.get('indexed_documents')} docs, {configured}, test embedding ok"
               if ok else f'embedding dimension {vec.shape[-1]} does not match the index',
               hint='rebuild the index: venv/bin/python rebuild_rag_index.py')
    except Exception as e:
        report(False, 'RAG search', f'test embedding failed: {e}'[:200],
               hint='model retired or API key missing — check llm.json models.rag_embedding and ~/.env')


def check_frontend(client):
    try:
        r = client.get(FRONTEND)
        report(r.status_code == 200, 'Frontend', f'HTTP {r.status_code}', hint='see logs/frontend.log')
    except Exception as e:
        report(False, 'Frontend', f'not reachable ({type(e).__name__})', hint='see logs/frontend.log')


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--deep', action='store_true', help='also convert one PDF page with Marker')
    args = parser.parse_args()

    print('STT smoke check')
    with httpx.Client(timeout=30) as client:
        backend_ok = check_backend(client)
        if backend_ok:
            check_llm(client)
        marker_ok = check_pdf_service(client, 'Marker', MARKER, 'marker.log')
        check_pdf_service(client, 'MinerU', MINERU, 'mineru.log')
        if args.deep and marker_ok:
            check_marker_deep(client)
        if backend_ok:
            check_rag(client)
        check_frontend(client)

    failed = results.count(False)
    if failed:
        print(f'{RED}{failed} of {len(results)} checks failed{RESET}')
        return 1
    print(f'{GREEN}All {len(results)} checks passed{RESET}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
