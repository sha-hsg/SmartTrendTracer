"""Topic map: episode lineage gate, events, content-keyed name cache, digest news (2026-10)."""
from datetime import datetime, timezone

import numpy as np

from app.services import topic_episodes
from app.services.topic_episodes import episodes as ep
from app.services.topic_episodes import naming


def _episode(wi, idx, name='e'):
    return {'name': name, 'wi': list(wi), '_idx': list(idx), 'start': f'w{wi[0]}', 'end': f'w{wi[1]}'}


def _vecs():
    """Three tight groups (A, B similar to A, C unrelated) plus background noise."""
    rng = np.random.default_rng(0)
    dim = 32
    base = rng.normal(size=(3, dim))
    base[1] = base[0] + 0.3 * rng.normal(size=dim)
    groups = [base[g] + 0.05 * rng.normal(size=(10, dim)) for g in range(3)]
    noise = rng.normal(size=(200, dim))
    v = np.vstack(groups + [noise]).astype('float32')
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def test_similar_successor_is_linked_unrelated_is_not():
    v = _vecs()
    eps = [_episode((0, 3), range(0, 10)), _episode((4, 6), range(10, 20)), _episode((4, 6), range(20, 30))]
    links = ep.link_episodes(eps, v)
    assert {(l['source'], l['target']) for l in links} == {(0, 1)}


def test_no_link_backwards_or_after_long_gap():
    v = _vecs()
    late = ep.LINK_MAX_GAP + 10
    eps = [_episode((0, 2), range(0, 10)), _episode((late, late + 2), range(10, 20))]
    assert ep.link_episodes(eps, v) == []


def test_events_birth_split_merge_end():
    eps = [_episode((0, 1), []), _episode((3, 4), []), _episode((3, 5), []), _episode((6, 7), [])]
    links = [{'source': 0, 'target': 1}, {'source': 0, 'target': 2},
             {'source': 1, 'target': 3}, {'source': 2, 'target': 3}]
    ep.lineage_events(eps, links, last_week_index=30)
    assert eps[0]['events'] == ['birth', 'split']
    assert eps[3]['events'] == ['merge', 'end']
    assert eps[1]['events'] == [] and eps[1]['parents'] == [0]


class FakeRepo:
    def __init__(self, cache):
        self.cache, self.added = cache, []

    def episode_names(self):
        return [dict(c) for c in self.cache]

    def add_episode_names(self, items):
        self.added += items


class FakeLLM:
    def __init__(self):
        self.calls = 0

    def get_prompt(self, key):
        return {'system': 's', 'user_template': '{episodes}'}

    def complete_text(self, task, user, system_prompt=None):
        self.calls += 1
        return '[{"id": 0, "name": "Fresh name", "noise": false}]'


def test_cached_name_reused_when_documents_overlap(monkeypatch):
    docs = [{'key': f'tweet:{i}'} for i in range(20)]
    repo = FakeRepo([{'name': 'Agent memory', 'noise': False, 'start': 'w0',
                      'doc_keys': [f'tweet:{i}' for i in range(8)]}])
    monkeypatch.setattr(naming, 'repo', repo)
    llm = FakeLLM()
    grown = {**_episode((0, 3), range(10)), 'tags': 't', 'examples': []}       # 8 of 10 shared: reuse
    other = {**_episode((5, 7), range(12, 20)), 'tags': 't', 'examples': []}   # no overlap: ask the LLM
    counts = naming.name_episodes([grown, other], docs, llm=llm)
    assert grown['name'] == 'Agent memory' and other['name'] == 'Fresh name'
    assert counts == {'reused': 1, 'named': 1, 'unnamed': 0} and llm.calls == 1
    assert repo.added[0]['doc_keys'] == sorted(f'tweet:{i}' for i in range(12, 20))


def test_digest_news_new_running_faded():
    weeks = ['2026-08-31', '2026-09-07', '2026-09-14', '2026-09-21', '2026-09-28']
    mk = lambda name, s, e, **kw: {'name': name, 'start': s, 'end': e, 'intensity': 3.0, 'docs': 10,  # noqa: E731
                                   'family': 0, 'parents': kw.get('parents', []), 'children': kw.get('children', [])}
    m = {'weeks': weeks, 'families': [{'id': 0, 'name': 'Agents'}], 'episodes': [
        mk('old running', '2026-08-31', '2026-09-28'),
        mk('faded', '2026-09-07', '2026-09-14'),
        mk('continued', '2026-09-07', '2026-09-14', children=[3]),
        mk('new', '2026-09-21', '2026-09-28', parents=[2]),
    ]}
    news = topic_episodes.digest_episodes(datetime(2026, 10, 1, tzinfo=timezone.utc), topic_map=m)
    assert [e['name'] for e in news['new']] == ['new'] and news['new'][0]['from'] == ['continued']
    assert [e['name'] for e in news['running']] == ['old running']
    assert [e['name'] for e in news['faded']] == ['faded']
