"""One storage form for paper publication dates (P2 2026-10)."""
from datetime import datetime

import pytest

from app.repositories.paper_dates import canonical_date
from app.services.paper_hygiene import _arxiv_key, backfill_dates


@pytest.mark.parametrize('value, expected', [
    ('2024-11-11', '2024-11-11'), ('2025-01-20T10:00:00Z', '2025-01-20'),
    ('2023-12-01T18:01:34.123456', '2023-12-01'), (datetime(2022, 5, 2, 13), '2022-05-02'),
    ('March 2024', '2024-03'), ('Jan 5, 2023', '2023-01-05'), ('2024-03', '2024-03'),
    (2021, '2021'), ('2021', '2021'), ('', None), (None, None), ('n/a', None),
])
def test_canonical_date(value, expected):
    assert canonical_date(value) == expected


def test_arxiv_key_strips_prefix_and_version():
    assert _arxiv_key('arXiv:2512.24601v1') == '2512.24601'
    assert _arxiv_key('1406.5823') == '1406.5823'


def test_backfill_uses_arxiv_then_crossref(monkeypatch):
    import app.services.paper_hygiene as ph
    papers = [{'_id': 1, 'arxiv_id': 'arXiv:2401.00001v2'}, {'_id': 2, 'doi': '10.1/x'}, {'_id': 3, 'doi': '10.1/y'}]
    monkeypatch.setattr(ph.repo, 'papers_missing_date', lambda limit: papers)
    stored = {}
    monkeypatch.setattr(ph.repo, 'set_publication_date', lambda pid, d: stored.__setitem__(pid, d))
    monkeypatch.setattr(ph, 'ARXIV_PAUSE', 0)
    stats = backfill_dates(arxiv=lambda aid: {'published': '2024-01-02T00:00:00Z'} if aid == '2401.00001' else None,
                           crossref=lambda doi: '2019-07' if doi == '10.1/x' else '')
    assert stored == {1: '2024-01-02', 2: '2019-07'} and stats == {'checked': 3, 'filled': 2, 'failed': 1}
