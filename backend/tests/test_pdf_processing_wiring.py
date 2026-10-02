"""Regressions from 2026-10-02: PDF processing silently fell back to plain text.

* _run_async_coro swallowed its own "inside a running loop" error and then
  called asyncio.run() inside the loop, so the Marker client never ran.
* Routes passed the MongoDB id as paper_id; Marker/MinerU expect an int and
  answered HTTP 422.
"""
import asyncio

import pytest

from app.services import pdf_processor_service as pps


async def _answer():
    return 42


def test_run_async_coro_without_loop():
    assert pps._run_async_coro(_answer()) == 42


def test_run_async_coro_inside_loop_raises():
    async def caller():
        with pytest.raises(RuntimeError, match="active event loop"):
            pps._run_async_coro(_answer())
    asyncio.run(caller())


def test_mongo_id_becomes_integer_paper_id(monkeypatch, tmp_path):
    pdf = tmp_path / 'x.pdf'
    pdf.write_bytes(b'%PDF-1.4\n')
    seen = {}

    def fake_marker(self, pdf_path, paper_id=None):
        seen['paper_id'] = paper_id
        return 'text', {}

    svc = pps.PDFProcessorService.__new__(pps.PDFProcessorService)
    svc.marker_service_available = True
    svc.mineru_service_available = False
    svc.marker_available = False
    monkeypatch.setattr(pps.PDFProcessorService, '_process_with_marker_service', fake_marker, raising=False)
    try:
        svc.process_pdf(str(pdf), prefer_method='marker', paper_id='6ac015ddc99eff7815cc5503')
    except Exception:
        pass  # only the id handed to Marker matters here
    assert seen.get('paper_id') == int('15cc5503', 16)
