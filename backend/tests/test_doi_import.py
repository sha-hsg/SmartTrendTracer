"""DOI / paper-link import (capability added 2026-10-03)."""
import httpx
import pytest

from app.services import doi_import_service as svc


@pytest.mark.parametrize('text,expected', [
    ('10.1145/3442188.3445922', ('doi', '10.1145/3442188.3445922')),
    ('https://doi.org/10.1145/3442188.3445922', ('doi', '10.1145/3442188.3445922')),
    ('https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4974382', ('doi', '10.2139/ssrn.4974382')),
    ('https://ssrn.com/abstract=4974382', ('doi', '10.2139/ssrn.4974382')),
    ('https://dl.acm.org/doi/pdf/10.24963/ijcai.2024/1002', ('doi', '10.24963/ijcai.2024/1002')),
    ('https://arxiv.org/abs/2502.12110v3', ('arxiv', '2502.12110')),
    ('https://arxiv.org/pdf/2502.12110.pdf', ('arxiv', '2502.12110')),
    ('2502.12110', ('arxiv', '2502.12110')),
    ('DOI: 10.1000/ABC.Def.', ('doi', '10.1000/abc.def')),
    ('https://doi.org/10.48550/arXiv.2405.20441', ('arxiv', '2405.20441')),
])
def test_parse_identifier(text, expected):
    assert svc.parse_identifier(text) == expected


@pytest.mark.parametrize('text', ['', '   ', 'https://example.com/some/page', 'hello world'])
def test_parse_identifier_rejects(text):
    with pytest.raises(svc.DOIImportError):
        svc.parse_identifier(text)


CROSSREF = {'message': {
    'title': ['Conversations at Scale&amp;nbsp;'],
    'author': [{'given': 'Friedrich', 'family': 'Geiecke'}, {'given': 'Xavier', 'family': 'Jaravel'}],
    'published': {'date-parts': [[2024, 10, 2]]},
    'container-title': ['SSRN Electronic Journal'], 'type': 'posted-content',
    'abstract': '<jats:p>The advent of LLMs.</jats:p>', 'URL': 'https://doi.org/10.2139/ssrn.4974382'}}


def _transport(pdf_ok: bool):
    def handler(request):
        url = str(request.url)
        if 'api.crossref.org' in url:
            return httpx.Response(200, json=CROSSREF)
        if 'api.openalex.org' in url:
            return httpx.Response(200, json={'locations': [
                {'pdf_url': 'https://blocked.example/x.pdf'}, {'pdf_url': 'https://open.example/x.pdf'}]})
        if 'blocked.example' in url:
            return httpx.Response(200, content=b'<html><title>Content Blocked</title>')
        if 'open.example' in url:
            return httpx.Response(200, content=b'%PDF-1.7 fake') if pdf_ok else httpx.Response(403)
        return httpx.Response(404)
    return httpx.MockTransport(handler)


@pytest.fixture
def fake_repo(monkeypatch, tmp_path):
    saved = {}

    class Result:
        inserted_id = 'new-id'

    monkeypatch.setattr(svc.papers_repo, 'find_paper_by_doi', lambda doi: None)
    monkeypatch.setattr(svc.papers_repo, 'find_paper_by_title', lambda title: None)
    monkeypatch.setattr(svc.papers_repo, 'insert_paper', lambda doc: saved.update(doc) or Result())
    monkeypatch.setattr(svc, 'PAPERS_DIR_REL', tmp_path)
    return saved


def test_import_skips_html_block_page_and_stores_real_pdf(fake_repo, tmp_path):
    with httpx.Client(transport=_transport(pdf_ok=True)) as client:
        result = svc.import_doi('10.2139/ssrn.4974382', client=client)
    assert result['success'] and result['has_pdf']
    assert result['pdf_url'] == 'https://open.example/x.pdf'
    assert fake_repo['title'] == 'Conversations at Scale'
    assert fake_repo['authors'] == 'Friedrich Geiecke, Xavier Jaravel'
    assert fake_repo['abstract'] == 'The advent of LLMs.'
    assert fake_repo['published_date'] == '2024-10-02'
    from pathlib import Path
    assert Path(fake_repo['pdf_path']).read_bytes().startswith(b'%PDF-')


def test_import_without_open_pdf_keeps_metadata(fake_repo):
    with httpx.Client(transport=_transport(pdf_ok=False)) as client:
        result = svc.import_doi('10.2139/ssrn.4974382', client=client)
    assert result['success'] and not result['has_pdf']
    assert fake_repo['pdf_missing'] is True and 'pdf_path' not in fake_repo
    assert 'upload it manually' in result['message']


def test_duplicate_doi_is_not_imported_twice(monkeypatch):
    monkeypatch.setattr(svc.papers_repo, 'find_paper_by_doi', lambda doi: {'_id': 'abc'})
    result = svc.import_doi('10.2139/ssrn.4974382')
    assert result == {'success': False, 'existing': True, 'paper_id': 'abc',
                      'message': 'Paper with DOI 10.2139/ssrn.4974382 is already in the database'}


def test_same_title_from_other_source_is_not_duplicated(monkeypatch):
    monkeypatch.setattr(svc.papers_repo, 'find_paper_by_doi', lambda doi: None)
    monkeypatch.setattr(svc.papers_repo, 'find_paper_by_title', lambda title: {'_id': 'arxiv-copy'})
    with httpx.Client(transport=_transport(pdf_ok=True)) as client:
        result = svc.import_doi('10.2139/ssrn.4974382', client=client)
    assert result['existing'] and result['paper_id'] == 'arxiv-copy'
