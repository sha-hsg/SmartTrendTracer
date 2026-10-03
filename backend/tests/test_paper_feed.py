"""Paper feed: dedupe, relevance ranking, version handling (2026-10)."""
import faiss
import numpy as np
import pytest

from app.services import paper_feed_service as svc


def unit(*v):
    a = np.array(v, dtype='float32')
    return a / np.linalg.norm(a)


@pytest.fixture
def fake_repo(monkeypatch):
    stored, runs = [], []
    known_ids, known_titles = {'2601.00001'}, {'Already Imported Paper'}
    monkeypatch.setattr(svc.repo, 'arxiv_id_known', lambda i: i in known_ids)
    monkeypatch.setattr(svc.repo, 'title_known', lambda t: t in known_titles)
    monkeypatch.setattr(svc.repo, 'insert_candidate', stored.append)
    monkeypatch.setattr(svc.repo, 'mark_subscription_run', lambda sid, n: runs.append((sid, n)))
    monkeypatch.setattr(svc.repo, 'paper_ids_for_concept', lambda name: ['p-memory'])
    return stored, runs


def results():
    return [
        {'arxiv_id': '2601.00001v2', 'title': 'Known by id', 'summary': 'x'},
        {'arxiv_id': '2610.00009v1', 'title': 'Already Imported Paper', 'summary': 'x'},
        {'arxiv_id': '2610.00010v1', 'title': 'Memory paper', 'summary': 'about agent memory'},
        {'arxiv_id': '2610.00011v3', 'title': 'Vision paper', 'summary': 'about images'},
    ]


def index_state():
    index = faiss.IndexFlatL2(2)
    index.add(np.stack([unit(1, 0), unit(0, 1)]))
    metadata = [{'type': 'paper', 'id': 'p-memory'}, {'type': 'paper', 'id': 'p-other'}]
    return index, metadata


def fake_embed(texts):
    vecs = [unit(1, 0.1) if 'memory' in t else unit(0.1, 1) for t in texts]
    return np.array(vecs), []


def test_dedupes_and_ranks_by_concept(fake_repo):
    stored, runs = fake_repo
    feed = svc.PaperFeed(search=lambda q, n: results(), embed=fake_embed, index_state=index_state())
    out = feed.run_subscription({'_id': 'sub1', 'name': 'Memory', 'query': 'q', 'concept': 'Agent Memory'})
    assert out == {'subscription': 'Memory', 'results': 4, 'new': 2}
    assert [c['arxiv_id'] for c in stored] == ['2610.00010', '2610.00011']   # version stripped
    scores = {c['title']: c['score'] for c in stored}
    assert scores['Memory paper'] > 0.9 > scores['Vision paper']
    assert all(c['status'] == 'new' and c['concept'] == 'Agent Memory' for c in stored)
    assert runs == [('sub1', 2)]


def test_without_concept_no_embedding_cost(fake_repo):
    stored, _ = fake_repo

    def no_embed(texts):
        raise AssertionError('must not embed without a concept')
    feed = svc.PaperFeed(search=lambda q, n: results(), embed=no_embed, index_state=index_state())
    feed.run_subscription({'_id': 'sub2', 'name': 'Plain', 'query': 'q'})
    assert [c['score'] for c in stored] == [None, None]


def test_failed_search_is_empty_not_error(fake_repo):
    stored, runs = fake_repo
    feed = svc.PaperFeed(search=lambda q, n: None, embed=fake_embed, index_state=index_state())
    assert feed.run_subscription({'_id': 's', 'name': 'x', 'query': 'q'})['new'] == 0
    assert stored == [] and runs == [('s', 0)]


def test_strip_version():
    assert svc._strip_version('2610.00010v12') == '2610.00010'
    assert svc._strip_version('2610.00010') == '2610.00010'
    assert svc._strip_version('cs/0112017v1') == 'cs/0112017'
