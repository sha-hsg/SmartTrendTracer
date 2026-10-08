"""Topic map of the bubble: micro-topics, families, episodes and their lineage.

1. Identity: all RAG-indexed documents (tweets, articles, papers since 2025)
   are clustered once, globally, into ~200 micro-topics (Louvain on a cosine
   kNN graph of author-debiased vectors).
2. Families: Louvain over the topic-similarity graph.
3. Episodes: weeks in which a micro-topic is clearly above its own baseline —
   when it flares up and when it fades. Named by the LLM (prompt
   episode_naming), noise filtered.
4. Lineage: an episode continues an earlier one (content similarity and
   document neighbourhood) → birth, split, merge, end.

Computed weekly by stt_scheduler.py (job topic_map) or on demand
(POST /api/analytics/trends/episodes/rebuild); stored in topic_maps.
"""
from __future__ import annotations

import logging
import threading
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional


from app.repositories import topic_maps as repo

from .documents import author_specific_concepts, load_documents, week_of
from .episodes import LINK_MAX_GAP, detect_episodes, lineage_events, link_episodes
from .naming import name_episodes
from .topics import describe_topics, global_topics, group_families

logger = logging.getLogger(__name__)

FIRST_WEEK = '2025-01-06'
FIRST_MONTH = '2025-01'

_state: Dict[str, Any] = {'running': False, 'started_at': None, 'error': None}
_lock = threading.Lock()


def compute_topic_map(llm=None) -> Dict[str, Any]:
    """Full computation (~1-3 min); returns the map document (not stored)."""
    t0, timings = time.monotonic(), {}

    def lap(name):
        nonlocal t0
        timings[name] = round(time.monotonic() - t0, 1)
        t0 = time.monotonic()

    docs, vecs = load_documents()
    skip = author_specific_concepts(docs)
    global_freq = Counter(c for d in docs for c in set(d['concepts']))
    now = datetime.now(timezone.utc)
    # the running month/week is incomplete and would distort shares
    months = sorted(m for m in {d['month'] for d in docs} if FIRST_MONTH <= m < now.strftime('%Y-%m'))
    week_totals = defaultdict(Counter)
    for d in docs:
        week_totals[d['week']][d['type']] += 1
    weeks = sorted(w for w in week_totals if FIRST_WEEK <= w < week_of(now))
    lap('load')

    labels = global_topics(vecs)
    topics = describe_topics(labels, docs, vecs, months, global_freq, skip)
    families = group_families(topics, docs, global_freq, skip)
    lap('cluster')

    episodes = []
    for t in topics:
        for e in detect_episodes(t['members'], docs, weeks, week_totals, skip):
            e.update({'family': t['family'], 'topic': t['label']})
            episodes.append(e)
    episodes.sort(key=lambda e: (e['start'], e['end']))
    lap('episodes')
    naming = name_episodes(episodes, docs, llm=llm)
    episodes = [e for e in episodes if not e['noise']]
    lap('naming')
    links = link_episodes(episodes, vecs)
    lineage_events(episodes, links, len(weeks) - 1)
    lap('lineage')

    for i, e in enumerate(episodes):
        e['id'] = i
        e.pop('_idx')
        e['movers'] = [list(m) for m in e['movers']]
    for f in families:
        f['topics'] = [{k: (v if k != 'movers' else [list(m) for m in v]) for k, v in t.items()
                        if k not in ('centroid', 'members')} for t in f['topics']]
    events = Counter(x for e in episodes for x in e['events'])
    logger.info(f"Topic map: {len(docs)} docs, {len(topics)} topics, {len(families)} families, "
                f"{len(episodes)} episodes, {len(links)} links, events {dict(events)}, naming {naming}, "
                f"timings {timings}")
    return {'created_at': datetime.now(timezone.utc), 'months': months, 'weeks': weeks,
            'families': families, 'episodes': episodes, 'episode_links': links,
            'stats': {'documents': len(docs), 'topics': len(topics), 'families': len(families),
                      'episodes': len(episodes), 'links': len(links), 'events': dict(events),
                      'naming': naming, 'timings': timings}}


def build_topic_map(llm=None) -> Dict[str, Any]:
    """Compute and store a new map; returns its stats."""
    doc = compute_topic_map(llm=llm)
    map_id = repo.save_topic_map(doc)
    return {'id': map_id, **doc['stats']}


def start_rebuild_in_background() -> bool:
    """False if a rebuild is already running in this process."""
    with _lock:
        if _state['running']:
            return False
        _state.update(running=True, started_at=datetime.now(timezone.utc), error=None)

    def run():
        try:
            build_topic_map()
        except Exception as e:
            logger.exception('Topic map rebuild failed')
            _state['error'] = f'{type(e).__name__}: {e}'[:300]
        finally:
            _state['running'] = False
    threading.Thread(target=run, daemon=True, name='topic-map-rebuild').start()
    return True


def rebuild_status() -> Dict[str, Any]:
    return dict(_state)


def latest_map() -> Optional[Dict[str, Any]]:
    """The latest map for the UI: episodes without example texts (those come
    with episode_detail), families without their micro-topics."""
    doc = repo.latest_topic_map({'families.topics': 0, 'episodes.examples': 0})
    if doc:
        doc['_id'] = str(doc['_id'])
    return doc


def episode_detail(episode_id: int) -> Dict[str, Any]:
    return repo.latest_episode(episode_id)


def digest_episodes(since: datetime, topic_map: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Episode news for the weekly digest, relative to `since` (start of the
    digest week): new (started within the last 4 weeks — detection needs two
    hot weeks), running (hot in the last complete week) and faded (ended in
    the last 4 weeks without successor)."""
    m = topic_map if topic_map is not None else repo.latest_topic_map(
        {'weeks': 1, 'families.id': 1, 'families.name': 1, 'episodes': 1})
    if not m or not m.get('weeks'):
        return {'available': False}
    last = m['weeks'][-1]
    recent = (since - timedelta(days=21)).date().isoformat()
    fam = {f['id']: f['name'] for f in m.get('families', [])}
    eps = m['episodes']

    def brief(e):
        return {'name': e['name'], 'start': e['start'], 'end': e['end'], 'intensity': e['intensity'],
                'docs': e['docs'], 'family': fam.get(e['family'], ''),
                'from': [eps[p]['name'] for p in e.get('parents', [])],
                'continues_as': [eps[c]['name'] for c in e.get('children', [])]}
    new = [brief(e) for e in eps if e['start'] >= recent]
    running = [brief(e) for e in eps if e['end'] == last and e['start'] < recent]
    faded = [brief(e) for e in eps if recent <= e['end'] < last and e['start'] < recent and not e.get('children')]
    top = lambda xs: sorted(xs, key=lambda x: -x['intensity'])[:8]  # noqa: E731
    return {'available': True, 'last_week': last, 'new': top(new), 'running': top(running), 'faded': top(faded)}


__all__ = ['build_topic_map', 'compute_topic_map', 'start_rebuild_in_background', 'rebuild_status',
           'latest_map', 'episode_detail', 'digest_episodes', 'LINK_MAX_GAP']
