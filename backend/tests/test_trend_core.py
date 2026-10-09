"""Trend core (2026-10 dashboard audit): baseline-relative trends, tagging lag,
hub exclusion, publication-dated papers, NPMI associations, rolling timeline."""
from datetime import datetime, timedelta, timezone

import pytest

from app.repositories.analytics.activity import paper_publication_date
from app.services import trend_core as tc

END = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)
NAMES = {'hub': 'Artificial Intelligence', 'steady': 'AI Agents', 'burst': 'Kimi K3', 'gone': 'Old Thing',
         'a': 'Moonshot AI', 'b': 'Kimi K3', 'x': 'Clay', 'y': 'Jeff Barg'}


def build(days_back=80, extra=()):
    """Synthetic bubble: steady concept every day, a burst in the last 2 days,
    a concept that stopped 20 days ago, a generic hub, background topics;
    plus `extra` (day_offset, author, concepts)."""
    docs, tags, n = [], [], 0

    def add(offset, author, concepts, channel='tweet'):
        nonlocal n
        n += 1
        cid = f'd{n}'
        docs.append((channel, cid, END - timedelta(days=offset), author))
        tags.extend((channel, cid, c) for c in concepts)
    for off in range(days_back):
        add(off, f'u{off % 5}', ['hub', 'steady'])
        add(off, f'v{off % 7}', ['hub'])
        if off >= 20:
            add(off, 'w', ['gone', 'hub'])
        for k in range(6):                       # background: many small topics
            add(off, f'f{k}', [f'filler{(off + k) % 40}'])
    for off in (0, 1):
        for k in range(6):
            add(off, f'z{k}', ['burst', 'hub'])
    for e in extra:
        add(*e)
    loader = lambda ids: {c: {'display_name': NAMES.get(c, c)} for c in ids}  # noqa: E731
    return tc.Cube(docs, tags, loader)


@pytest.fixture
def cube(monkeypatch):
    c = build()
    monkeypatch.setattr(tc, 'get_cube', lambda force=False: c)
    return c


def test_burst_is_hot_hub_is_never_listed(cube):
    o = tc.overview(hours=48)
    assert [x['display_name'] for x in o['hot_topics']] == ['Kimi K3']
    names = {x['display_name'] for k in ('hot_topics', 'declining', 'stable') for x in o[k]}
    assert 'Artificial Intelligence' not in names
    assert 'AI Agents' in {x['display_name'] for x in tc.overview(hours=168)['stable']}   # 1 doc/day, unchanged


def test_stopped_concept_declines_against_its_baseline(cube):
    o = tc.overview(hours=168)
    assert 'Old Thing' in {x['display_name'] for x in o['declining']}


def test_tiny_counts_are_not_trends(monkeypatch):
    c = build(extra=[(0, 'q', ['tiny']), (0, 'q2', ['tiny']), (1, 'q3', ['tiny'])])   # 0 -> 3
    monkeypatch.setattr(tc, 'get_cube', lambda force=False: c)
    assert 'tiny' not in {x['concept_id'] for x in tc.overview(hours=48)['hot_topics']}


def test_untagged_recent_days_are_cut_off():
    c = build(extra=[(-2, 'late', []), (-2, 'late2', [])])        # newer days, no tags yet
    assert c.data_through == END.date().toordinal()
    assert c.untagged_after == 2


def test_the_running_day_is_never_counted(monkeypatch):
    import datetime as dt

    class Frozen(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return END                                              # "today" = END's day, partly over
    monkeypatch.setattr(tc, 'datetime', Frozen)
    c = build()                                                     # END's day is fully tagged
    assert c.data_through == END.date().toordinal() - 1


def test_associations_need_two_sources_and_drop_aliases(monkeypatch):
    extra = [(off, f'p{off}', ['a', 'b', 'steady']) for off in range(4)]          # 4 sources: real pair
    extra += [(off, 'podcast', ['x', 'y', 'steady']) for off in range(5)]          # one source only
    c = build(extra=extra)
    monkeypatch.setattr(tc, 'get_cube', lambda force=False: c)
    pairs = {(p['concept_a'], p['concept_b']) for p in tc.associations(days=30)['pairs']}
    assert ('Clay', 'Jeff Barg') not in pairs and ('Jeff Barg', 'Clay') not in pairs
    # a and b always appear together -> one thing under two names, not an association
    assert not any({'Moonshot AI', 'Kimi K3'} == {a, b} for a, b in pairs)


def test_timeline_frames_rank_rolling_week(cube):
    t = tc.timeline(days=10, top_n=3)
    first = [r['display_name'] for r in t['frames'][0]['rankings']]
    last = [r['display_name'] for r in t['frames'][-1]['rankings']]
    assert 'Kimi K3' not in first and 'Kimi K3' in last
    assert 'Artificial Intelligence' not in last


@pytest.mark.parametrize('paper, expected', [
    ({'publication_date': '2024-11-11'}, '2024-11-11'),
    ({'publication_date': '', 'published_date': '2025-03'}, '2025-03-01'),
    ({'publication_date': datetime(2023, 5, 2)}, '2023-05-02'),
    ({'publication_date': '2021'}, None),          # year only: would pile up on Jan 1
    ({}, None),
])
def test_paper_dates_use_publication_not_import(paper, expected):
    d = paper_publication_date(paper)
    assert (d.date().isoformat() if d else None) == expected
