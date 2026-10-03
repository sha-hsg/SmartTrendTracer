"""Incremental RAG index update (capability added 2026-10-03)."""
import json
from datetime import datetime, timedelta, timezone

import faiss
import numpy as np
import pytest
from bson import ObjectId

from app.services.rag import index_manager as im

T0 = datetime(2026, 10, 1, tzinfo=timezone.utc)
P1, P2 = ObjectId(), ObjectId()


class Coll:
    def __init__(self, docs):
        self.docs = docs

    def find(self, query=None, projection=None):
        query = query or {}
        out = []
        for d in self.docs:
            ok = True
            for k, v in query.items():
                if k == '_id' and isinstance(v, dict):
                    ok &= d['_id'] in v['$in']
                elif k == 'created_at':
                    ok &= d.get('created_at', T0) > v['$gt']
                elif k == 'updated_at':
                    ok &= d.get('updated_at', T0) > v['$gt']
                elif k == '$or':
                    ok &= any(d.get(f, T0) > c[f]['$gt'] for c in v for f in c)
                elif k == 'processed':
                    ok &= d.get('processed') == v
                elif k == 'paper_type':
                    ok &= d.get('paper_type') != v['$ne']
            if ok:
                out.append(d)
        return out

    def distinct(self, field, query=None):
        return [d['_id'] for d in self.find(query)]


class DB:
    def __init__(self, tweets, papers, tags=()):
        self.tweets, self.articles, self.papers = Coll(tweets), Coll([]), Coll(papers)
        self.tag_instances = Coll(list(tags))


class Concepts:
    def __init__(self):
        self.tags = {}

    def get_tags_for_content(self, content_type, content_id):
        return [{'display_name': n, 'id': n} for n in self.tags.get(content_id, [])]


def paper(pid, content='x' * 200, **kw):
    return {'_id': pid, 'title': f'P {pid}', 'abstract': 'a', 'content': content,
            'processed': True, 'paper_type': 'research', **kw}


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(im, '_embedding_model_and_dimension', lambda g: ('test-model', 4))
    failing = set()

    def fake_batch(texts, *a, **k):
        failed = [i for i, t in enumerate(texts) if any(f in t for f in failing)]
        vecs = [np.ones(4) * (len(t) % 7 + 1) for i, t in enumerate(texts) if i not in failed]
        return np.array(vecs), failed
    monkeypatch.setattr(im, 'get_embeddings_batch', fake_batch)
    paths = {k: tmp_path / f for k, f in [('index', 'faiss.index'), ('metadata', 'm.pkl'),
                                          ('doc_map', 'd.pkl'), ('info', 'info.json')]}
    return paths, failing


def build(db, cs, paths):
    docs, meta = im.collect_documents(db, cs, {'tweet': {}, 'article': {}, 'paper': im.PAPER_INDEX_QUERY})
    index = faiss.IndexFlatL2(4)
    index.add(np.ones((len(docs), 4), dtype='float32'))
    paths['info'].write_text(json.dumps({'embedding_model': 'test-model', 'last_updated': T0.isoformat()}))
    return index, meta, {i: d for i, d in enumerate(docs)}


def run(db, cs, paths, state):
    return im.update_index(db, cs, True, None, paths, {}, *state)


def test_adds_new_marks_changed_and_deleted(env):
    paths, _ = env
    cs = Concepts()
    db = DB(tweets=[{'_id': 't1', 'text': 'old'}, {'_id': 't2', 'text': 'gone'}], papers=[paper(P1)])
    state = build(db, cs, paths)

    later = T0 + timedelta(hours=1)
    db.tweets.docs = [{'_id': 't1', 'text': 'old'}, {'_id': 't3', 'text': 'new tweet'}]   # t2 deleted, t3 new
    db.tag_instances.docs = [{'content_type': 'tweet', 'content_id': 't1', 'created_at': later}]
    cs.tags['t1'] = ['Agent Memory']                                                     # t1 newly tagged

    index, meta, doc_map, result = run(db, cs, paths, state)
    assert (result['added'], result['updated'], result['removed'], result['failed']) == (1, 1, 1, 0)
    assert index.ntotal == len(meta) == len(doc_map) == 5
    active = {(m['type'], m['id']) for m in meta if not m.get('stale')}
    assert active == {('tweet', 't1'), ('tweet', 't3'), ('paper', str(P1))}
    fresh_t1 = [doc_map[i] for i, m in enumerate(meta) if m['id'] == 't1' and not m.get('stale')]
    assert fresh_t1 == ['Tweet by @: old\nConcepts: Agent Memory']
    info = json.loads(paths['info'].read_text())
    assert info['total_documents'] == 3 and info['stale_entries'] == 2


def test_second_run_without_changes_does_nothing(env):
    paths, _ = env
    cs = Concepts()
    db = DB(tweets=[{'_id': 't1', 'text': 'a'}], papers=[])
    state = build(db, cs, paths)
    *state, first = run(db, cs, paths, state)
    *state, second = run(db, cs, paths, state)
    assert (second['added'], second['updated'], second['removed']) == (0, 0, 0)


def test_failed_embedding_is_retried_next_run(env):
    paths, failing = env
    cs = Concepts()
    db = DB(tweets=[], papers=[paper(P1)])
    state = build(db, cs, paths)
    db.papers.docs.append(paper(P2, content='needs retry ' * 20))
    failing.add('needs retry')
    *state, result = run(db, cs, paths, state)
    assert result['failed'] == 1 and result['added'] == 0
    failing.clear()
    *state, result = run(db, cs, paths, state)
    assert result['added'] == 1


def test_refuses_index_of_other_model(env):
    paths, _ = env
    cs = Concepts()
    db = DB(tweets=[{'_id': 't1', 'text': 'a'}], papers=[])
    state = build(db, cs, paths)
    paths['info'].write_text(json.dumps({'embedding_model': 'models/text-embedding-004',
                                         'last_updated': T0.isoformat()}))
    with pytest.raises(RuntimeError, match='full rebuild is required'):
        run(db, cs, paths, state)
