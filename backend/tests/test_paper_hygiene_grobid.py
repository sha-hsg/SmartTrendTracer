"""Automatic GROBID enrichment keeps import metadata; skipped while the server is down."""
import app.services.paper_hygiene as ph
from app.repositories.references import reference_hash


def test_reference_hash_prefers_doi_then_arxiv_then_title():
    assert reference_hash({'doi': ' 10.1/ABC ', 'arxiv_id': '2401.1'}) == 'doi:10.1/abc'
    assert reference_hash({'arxiv_id': '2401.00001'}) == 'arxiv:2401.00001'
    assert reference_hash({'title': 'Attention Is All You Need!', 'year': 2017}) == \
        reference_hash({'title': 'attention is all you need', 'year': '2017'})


def test_grobid_step_skips_without_marking_when_server_is_down(monkeypatch):
    import app.repositories.papers_grobid as pg
    import app.services.grobid_service as gs
    monkeypatch.setattr(pg, 'papers_needing_grobid', lambda limit: [{'_id': 1, 'pdf_path': 'x.pdf'}])
    marked = []
    monkeypatch.setattr(pg, 'mark_grobid_failed', lambda pid, err: marked.append(pid))
    monkeypatch.setattr(gs.GROBIDService, 'is_alive', lambda self: False)
    stats = ph.grobid_enrich(limit=1)
    assert stats['skipped'] and stats['processed'] == 0 and marked == []
