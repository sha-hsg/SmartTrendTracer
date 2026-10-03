"""The smoke check must turn real outages into red lines (2026-10 incidents)."""
import httpx
import pytest

import smoke_check as sc


@pytest.fixture(autouse=True)
def fresh_results(monkeypatch, tmp_path):
    sc.results.clear()
    monkeypatch.setattr(sc, 'LOG_DIR', tmp_path)
    (tmp_path / 'backend.log').write_text(
        'INFO ok\n08:00:52 - llm_manager - ERROR - LLM Provider NOT provided. You passed model=claude-sonnet-5\n')


def client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_backend_down_reports_last_log_error(capsys):
    def handler(request):
        raise httpx.ConnectError('refused')
    assert sc.check_backend(client(handler)) is False
    out = capsys.readouterr().out
    assert '✗ Backend + MongoDB' in out
    assert 'LLM Provider NOT provided' in out


def test_backend_healthy():
    def handler(request):
        return httpx.Response(200, json={'status': 'healthy', 'collections': {'papers': 1, 'tweets': 2}})
    assert sc.check_backend(client(handler)) is True
    assert sc.results == [True]


def test_marker_unhealthy_is_red():
    def handler(request):
        return httpx.Response(200, json={'status': 'unhealthy', 'detail': 'marker_single not found'})
    assert sc.check_pdf_service(client(handler), 'Marker', sc.MARKER, 'marker.log') is False


def test_rag_model_mismatch_is_red(capsys):
    def handler(request):
        return httpx.Response(200, json={'is_ready': True, 'embedding_model': 'models/text-embedding-004',
                                         'indexed_documents': 5})
    sc.check_rag(client(handler))
    assert sc.results == [False]
    assert 'index built with models/text-embedding-004' in capsys.readouterr().out


def test_missing_provider_key_is_red():
    def handler(request):
        if request.url.path.endswith('/status'):
            return httpx.Response(200, json={'providers': {'google': {'configured': False}}})
        return httpx.Response(200, json={'summarization': []})
    sc.check_llm(client(handler))
    assert sc.results == [False]
