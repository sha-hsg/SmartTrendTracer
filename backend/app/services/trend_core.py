"""
Trend core: one concept-activity cube for all concept-based trend views
(Trend Dashboard overview, heatmap, bubble chart, co-occurrence/network,
timeline; weekly digest; substack trends).

Rules shared by every view (they come from the 2026-10 dashboard audit and
the bubble topic map in app.services.topic_episodes):
- Documents: tweets (created_at), articles (published_at), research papers
  by *publication* date. Counts are distinct documents per concept.
- data_through: the last complete day whose tweets are mostly tagged. The
  running day is partial and tagging may lag; either would look like a
  collapse, so windows end there and the UI says "data through …".
- Generic hub concepts (AI, LLM, ML, big lab names) and near-duplicate
  concept pairs are left out of rankings: they are always on top and say
  nothing about change.
- Change is judged against the concept's own baseline (median of the
  preceding windows, normalised for volume) with a Poisson z-score and
  minimum counts — not "% versus the one previous period", which turned
  0 -> 3 into +300 %.
- Associations use NPMI (how much more often two concepts meet than chance),
  not raw co-occurrence counts, which only rediscover the biggest concepts.
"""
from __future__ import annotations

import math
import statistics
import threading
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from itertools import combinations
from typing import Any, Dict, List, Tuple

from app.repositories import analytics as repo

CHANNELS = ('tweet', 'article', 'paper')
CACHE_SECONDS = 600
TAGGED_SHARE = 0.5            # a day counts as tagged when >= half its tweets carry tags
GENERIC = {'large language model', 'large language models', 'llm', 'llms', 'ai', 'artificial intelligence',
           'machine learning', 'deep learning', 'generative ai', 'natural language processing',
           'openai', 'google', 'anthropic', 'empirical study'}
GENERIC_DOC_SHARE = 0.2       # a concept on more than this share of the documents of the last
HUB_DAYS = 90                 # ... HUB_DAYS is a hub (judged long-run: a launch-day burst is not a hub)
AUTHOR_CONCENTRATION = 0.6    # topic labels: concepts mostly attached to one author describe the author
MIN_HOT = 5                   # current count needed to be "hot"
MIN_DECLINE_BASELINE = 4      # expected count needed to call something "declining"
BASELINE_WINDOWS = 8
MIN_PAIR = 3                  # co-occurrence support
MIN_PAIR_AUTHORS = 2          # ... from at least this many sources (one account's template is not an association)
ALIAS_JACCARD = 0.8           # pairs this similar are two names for one thing
COLORS = {'tweet': '#3b82f6', 'article': '#f59e0b', 'paper': '#10b981'}


def author_specific_concepts(docs) -> set:
    """Concepts mostly attached to one author describe the author, not a
    topic. `docs`: iterable of dicts with 'author' and 'concepts'."""
    per = defaultdict(Counter)
    for d in docs:
        for c in set(d['concepts']):
            per[c][d['author']] += 1
    names = {d['author'].lower() for d in docs}
    out = set()
    for c, authors in per.items():
        total = sum(authors.values())
        if c.lower() in names or (total >= 5 and authors.most_common(1)[0][1] / total > AUTHOR_CONCENTRATION):
            out.add(c)
    return out


class Cube:
    """Daily distinct-document counts per concept and channel."""

    def __init__(self, documents, tag_instances, concepts_loader):
        meta = {}
        for ch, cid, dt, author in documents:
            meta[(ch, cid)] = (dt.date().toordinal(), author)
        self.doc_concepts: Dict[Tuple[str, str], set] = defaultdict(set)
        for ch, cid, concept in tag_instances:
            if (ch, cid) in meta:
                self.doc_concepts[(ch, cid)].add(concept)
        self.day_total = defaultdict(lambda: [0, 0, 0])
        self.day_tagged = defaultdict(lambda: [0, 0, 0])
        self.daily = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))   # concept -> day -> [t, a, p]
        self.docs_by_day = defaultdict(list)
        self.first_seen, self.last_seen = {}, {}
        for key, (day, _) in meta.items():
            ci = CHANNELS.index(key[0])
            self.day_total[day][ci] += 1
            concepts = self.doc_concepts.get(key)
            if not concepts:
                continue
            self.day_tagged[day][ci] += 1
            self.docs_by_day[day].append(key)
            for c in concepts:
                self.daily[c][day][ci] += 1
                if day < self.first_seen.get(c, 10 ** 9):
                    self.first_seen[c] = day
                if day > self.last_seen.get(c, 0):
                    self.last_seen[c] = day
        self.meta = meta
        self.concepts = concepts_loader(set(self.daily))
        # last complete (UTC) day whose tweets are mostly tagged: the running
        # day is partial and would count as a drop in every window
        last_complete = datetime.now(timezone.utc).date().toordinal() - 1
        tagged_days = [d for d, tot in self.day_total.items()
                       if d <= last_complete and tot[0] and self.day_tagged[d][0] / tot[0] >= TAGGED_SHARE]
        self.data_through = max(tagged_days) if tagged_days else last_complete
        per, totals = self.counts(self.data_through - HUB_DAYS + 1, self.data_through)
        n = sum(totals) or 1
        self.hub_set = {c for c, v in per.items() if self.is_generic(c) or sum(v) / n > GENERIC_DOC_SHARE}
        # items after data_through (the running day, untagged days) — not counted yet
        self.untagged_after = sum(sum(t) for d, t in self.day_total.items() if d > self.data_through)
        self.built_at = time.time()

    # -- basic access -------------------------------------------------------

    def name(self, c: str) -> str:
        return self.concepts.get(c, {}).get('display_name', c)

    def is_generic(self, c: str) -> bool:
        return self.name(c).lower() in GENERIC

    def counts(self, start: int, end: int) -> Tuple[Dict[str, List[int]], List[int]]:
        """Per-concept [t, a, p] document counts and channel totals of tagged
        documents for days start..end (ordinals, inclusive)."""
        per = defaultdict(lambda: [0, 0, 0])
        totals = [0, 0, 0]
        for day in range(start, end + 1):
            for i, v in enumerate(self.day_tagged.get(day, (0, 0, 0))):
                totals[i] += v
            for key in self.docs_by_day.get(day, ()):
                ci = CHANNELS.index(key[0])
                for c in self.doc_concepts[key]:
                    per[c][ci] += 1
        return per, totals

    def day_count(self, c: str, day: int) -> int:
        v = self.daily.get(c, {}).get(day)
        return sum(v) if v else 0

    def hubs(self, per=None, totals=None) -> set:
        """Generic by name, or on more than GENERIC_DOC_SHARE of the last
        HUB_DAYS days' documents (fixed per cube, not per window)."""
        return self.hub_set

    def info(self, c: str) -> Dict[str, Any]:
        meta = self.concepts.get(c, {})
        return {'concept_id': c, 'display_name': self.name(c), 'slug': meta.get('slug', ''),
                'entity_type': meta.get('entity_type', 'topic'), 'color': meta.get('color')}


_cache: Dict[str, Any] = {'cube': None}
_lock = threading.Lock()


def get_cube(force: bool = False) -> Cube:
    with _lock:
        cube = _cache['cube']
        if force or cube is None or time.time() - cube.built_at > CACHE_SECONDS:
            cube = Cube(repo.load_activity_documents(), repo.load_activity_tag_instances(),
                        repo.load_activity_concepts)
            _cache['cube'] = cube
        return cube


def _iso(day: int) -> str:
    return date.fromordinal(day).isoformat()


def _poisson_z(current: float, expected: float) -> float:
    return (current - expected) / math.sqrt(max(expected, 1.0))


def _windows(end: int, length: int, n: int) -> List[Tuple[int, int]]:
    """n windows of `length` days before the window ending at `end`, oldest first."""
    return [(end - length * (k + 1) + 1, end - length * k) for k in range(n, 0, -1)]


def _baseline(cube: Cube, end: int, length: int, n: int = BASELINE_WINDOWS):
    """Current window counts plus per-concept expected count from the median of
    the preceding windows, scaled to the current window's document volume."""
    cur_per, cur_tot = cube.counts(end - length + 1, end)
    base = [cube.counts(s, e) for s, e in _windows(end, length, n)]
    base = [(p, t) for p, t in base if sum(t)]                     # skip windows before the data starts
    vol = sum(cur_tot) / (statistics.median([sum(t) for _, t in base]) if base else 1) if base else 1.0
    concepts = set(cur_per) | {c for p, _ in base for c in p}
    expected, history = {}, {}
    for c in concepts:
        series = [sum(p.get(c, (0, 0, 0))) for p, _ in base]
        history[c] = series
        expected[c] = (statistics.median(series) if series else 0.0) * vol
    return cur_per, cur_tot, expected, history, base


# -- views ---------------------------------------------------------------------

def overview(hours: int = 48, anomaly_threshold: float = 2.5, limit: int = 10) -> Dict[str, Any]:
    """Hot / declining / stable concepts and day-level spikes for the last
    `hours` (rounded to whole days) up to data_through."""
    cube = get_cube()
    length = max(1, round(hours / 24))
    end = cube.data_through
    cur_per, cur_tot, expected, history, base = _baseline(cube, end, length)
    hubs = cube.hubs(cur_per, cur_tot)

    def item(c, trend):
        cur = sum(cur_per.get(c, (0, 0, 0)))
        exp = expected[c]
        t, a, p = cur_per.get(c, (0, 0, 0))
        return {**cube.info(c), 'count': cur, 'previous_count': round(exp, 1),
                'velocity': round((cur - exp) / max(exp, 1.0) * 100, 1), 'z_score': round(_poisson_z(cur, exp), 2),
                'trend': trend, 'sparkline': history[c] + [cur],
                'content_breakdown': {'tweets': t, 'articles': a, 'papers': p, 'reddit': 0}}

    scored = [(c, sum(cur_per.get(c, (0, 0, 0))), expected[c]) for c in expected if c not in hubs]
    hot = sorted((x for x in scored if x[1] >= MIN_HOT and x[1] >= 2 * x[2] and _poisson_z(x[1], x[2]) >= 3),
                 key=lambda x: -_poisson_z(x[1], x[2]))
    declining = sorted((x for x in scored if x[2] >= MIN_DECLINE_BASELINE and x[1] <= 0.5 * x[2]
                        and _poisson_z(x[1], x[2]) <= -2), key=lambda x: _poisson_z(x[1], x[2]))
    steady = sorted((x for x in scored if x[1] >= 3 and abs(_poisson_z(x[1], x[2])) < 1.5
                     and sum(1 for v in history[x[0]] if v) >= max(1, len(history[x[0]]) - 1)),
                    key=lambda x: -x[1])

    # day-level spikes inside the current window against the baseline days
    base_days = list(range(end - length * (len(base) + 1) + 1, end - length + 1))
    anomalies = []
    for c in cur_per:
        if c in hubs:
            continue
        vals = [cube.day_count(c, d) for d in base_days]
        mean = sum(vals) / len(vals) if vals else 0.0
        sd = max(statistics.pstdev(vals) if len(vals) > 1 else 0.0, math.sqrt(max(mean, 0.25)))
        best = max(((cube.day_count(c, d), d) for d in range(end - length + 1, end + 1)), default=(0, end))
        z = (best[0] - mean) / sd
        if best[0] >= MIN_HOT and z >= anomaly_threshold:
            anomalies.append({'concept_id': c, 'display_name': cube.name(c), 'spike_magnitude': round(best[0] - mean, 1),
                              'z_score': round(z, 2), 'timestamp': _iso(best[1]), 'baseline_avg': round(mean, 2),
                              'current_value': best[0]})
    anomalies.sort(key=lambda a: -a['z_score'])

    # median change of concepts with a real baseline (0 -> n would dominate a mean)
    velocities = [item(c, '')['velocity'] for c, cur, exp in scored if exp >= 3]
    return {
        'hot_topics': [item(c, 'hot') for c, _, _ in hot[:limit]],
        'declining': [item(c, 'declining') for c, _, _ in declining[:limit]],
        'stable': [item(c, 'stable') for c, _, _ in steady[:limit]],
        'anomalies': anomalies[:limit],
        'time_range': {'start': _iso(end - length + 1), 'end': _iso(end), 'hours': length * 24,
                       'data_through': _iso(end), 'untagged_after': cube.untagged_after,
                       'baseline_windows': len(base)},
        'statistics': {'total_content': sum(cur_tot), 'unique_concepts': sum(1 for v in cur_per.values() if sum(v)),
                       'avg_velocity': round(statistics.median(velocities), 1) if velocities else 0.0},
    }


def heatmap(days: int = 30, top_n: int = 20) -> Dict[str, Any]:
    """Daily document counts of the window's most active non-hub concepts."""
    cube = get_cube()
    end = cube.data_through
    start = end - days + 1
    per, totals = cube.counts(start, end)
    hubs = cube.hubs(per, totals)
    top = sorted((c for c in per if c not in hubs), key=lambda c: -sum(per[c]))[:top_n]
    day_range = list(range(start, end + 1))
    matrix = [[cube.day_count(c, d) for d in day_range] for c in top]
    flat = [v for row in matrix for v in row]
    return {'concepts': [cube.name(c) for c in top], 'concept_ids': top, 'dates': [_iso(d) for d in day_range],
            'matrix': matrix, 'row_totals': [sum(per[c]) for c in top],
            'max_value': max(flat, default=0), 'min_value': min(flat, default=0),
            'data_through': _iso(end), 'excluded_hubs': sorted(cube.name(c) for c in hubs)[:20]}


def bubbles(days: int = 30, limit: int = 50) -> Dict[str, Any]:
    """Age (days since first seen) against growth (current window vs its
    baseline) for the window's most active and fastest-growing concepts."""
    cube = get_cube()
    end = cube.data_through
    cur_per, cur_tot, expected, _, base = _baseline(cube, end, days, n=4)
    hubs = cube.hubs(cur_per, cur_tot)
    cands = [c for c in cur_per if c not in hubs and sum(cur_per[c]) >= 3]
    by_volume = sorted(cands, key=lambda c: -sum(cur_per[c]))[:limit // 2]
    by_growth = sorted(cands, key=lambda c: -_poisson_z(sum(cur_per[c]), expected[c]))[:limit]
    chosen = list(dict.fromkeys(by_volume + by_growth))[:limit]
    data = []
    for c in chosen:
        cur = sum(cur_per[c])
        growth = (cur + 1) / (expected[c] + 1)
        channel = CHANNELS[max(range(3), key=lambda i: cur_per[c][i])]
        data.append({**cube.info(c), 'x': max(1, end - cube.first_seen[c]), 'y': round(growth, 2), 'z': cur,
                     'growth': round(growth, 2), 'expected': round(expected[c], 1),
                     'z_score': round(_poisson_z(cur, expected[c]), 2), 'channel': channel, 'color': COLORS[channel],
                     'first_seen': _iso(cube.first_seen[c]), 'last_seen': _iso(cube.last_seen[c])})

    def rng(key):
        vals = [d[key] for d in data] or [0]
        return {'min': min(vals), 'max': max(vals)}
    return {'data': data, 'x_range': rng('x'), 'y_range': rng('y'), 'z_range': rng('z'),
            'data_through': _iso(end), 'baseline_windows': len(base)}


def _pairs(cube: Cube, start: int, end: int):
    """Document frequencies, pair counts and pair sources (authors, up to
    MIN_PAIR_AUTHORS) of non-hub concepts in a window."""
    df, pairs = Counter(), Counter()
    sources = defaultdict(set)
    n = 0
    per, totals = cube.counts(start, end)
    hubs = cube.hubs(per, totals)
    for day in range(start, end + 1):
        for key in cube.docs_by_day.get(day, ()):
            cs = sorted(c for c in cube.doc_concepts[key] if c not in hubs)
            n += 1
            df.update(cs)
            author = cube.meta[key][1]
            for pair in combinations(cs, 2):
                pairs[pair] += 1
                if len(sources[pair]) < MIN_PAIR_AUTHORS:
                    sources[pair].add(author)
    return df, pairs, n, hubs, sources


def associations(days: int = 30, top_n: int = 25, min_cooccurrence: int = MIN_PAIR) -> Dict[str, Any]:
    """Concept pairs that meet more often than chance (NPMI), with support,
    near-duplicate pairs removed, and whether a pair is new against the
    previous window. Feeds the matrix, the pair list and the network."""
    cube = get_cube()
    end = cube.data_through
    start = end - days + 1
    df, pairs, n, hubs, sources = _pairs(cube, start, end)
    prev_pairs = _pairs(cube, start - days, start - 1)[1]
    min_support = max(min_cooccurrence, MIN_PAIR)
    scored = []
    for (a, b), k in pairs.items():
        if k < min_support or len(sources[(a, b)]) < MIN_PAIR_AUTHORS:
            continue
        jac = k / (df[a] + df[b] - k)
        if jac >= ALIAS_JACCARD:
            continue
        p_ab, p_a, p_b = k / n, df[a] / n, df[b] / n
        npmi = math.log(p_ab / (p_a * p_b)) / -math.log(p_ab) if p_ab < 1 else 1.0
        if npmi <= 0:
            continue
        scored.append({'concept_a': cube.name(a), 'concept_a_id': a, 'concept_b': cube.name(b), 'concept_b_id': b,
                       'count': k, 'strength': round(npmi, 3), 'npmi': round(npmi, 3), 'jaccard': round(jac, 3),
                       'score': round(npmi * math.log2(1 + k), 3), 'new': prev_pairs.get((a, b), 0) == 0})
    # NPMI alone favours rare pairs (3 of 3); weight by support
    scored.sort(key=lambda p: (-p['score'], -p['count']))
    # matrix over the concepts that take part in the strongest pairs
    order = list(dict.fromkeys(c for p in scored for c in (p['concept_a_id'], p['concept_b_id'])))[:top_n]
    idx = {c: i for i, c in enumerate(order)}
    matrix = [[0.0] * len(order) for _ in order]
    for p in scored:
        i, j = idx.get(p['concept_a_id']), idx.get(p['concept_b_id'])
        if i is not None and j is not None:
            matrix[i][j] = matrix[j][i] = p['npmi']
    return {'concepts': [cube.name(c) for c in order], 'concept_ids': order, 'matrix': matrix,
            'counts': {c: df[c] for c in order}, 'pairs': scored[:max(40, top_n * 2)],
            'total_pairs': len(scored), 'total_documents': n, 'data_through': _iso(end),
            'excluded_hubs': sorted(cube.name(c) for c in hubs)[:20]}


def network(days: int = 30, top_n: int = 40) -> Dict[str, Any]:
    """Graph of the strongest associations: node size = documents, edge =
    NPMI; clusters by modularity."""
    import networkx as nx
    assoc = associations(days=days, top_n=top_n)
    cube = get_cube()
    g = nx.Graph()
    for p in assoc['pairs'] if len(assoc['pairs']) <= top_n * 2 else assoc['pairs'][:top_n * 2]:
        g.add_edge(p['concept_a_id'], p['concept_b_id'], weight=p['npmi'], count=p['count'], new=p['new'])
    # keep the top_n best-connected nodes
    keep = sorted(g.nodes, key=lambda c: -g.degree(c, weight='weight'))[:top_n]
    g = g.subgraph(keep).copy()
    comms = nx.community.louvain_communities(g, weight='weight', seed=42) if g.number_of_edges() else []
    palette = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc948', '#b07aa1', '#ff9da7', '#9c755f', '#bab0ac']
    cluster_of = {}
    clusters = []
    for i, members in enumerate(sorted(comms, key=len, reverse=True)):
        color = palette[i % len(palette)]
        head = max(members, key=lambda c: assoc['counts'].get(c, 0) or len(list(g.neighbors(c))))
        clusters.append({'id': i, 'name': cube.name(head), 'nodes': sorted(members), 'color': color})
        for c in members:
            cluster_of[c] = i
    df = Counter()
    per, _ = cube.counts(cube.data_through - days + 1, cube.data_through)
    for c in g.nodes:
        df[c] = sum(per.get(c, (0, 0, 0)))
    nodes = [{'id': c, 'name': cube.name(c), 'val': df[c], 'activity': df[c], 'degree': g.degree(c),
              'entity_type': cube.concepts.get(c, {}).get('entity_type', 'topic'),
              'cluster': cluster_of.get(c), 'color': clusters[cluster_of[c]]['color'] if c in cluster_of else '#8f8f8f'}
             for c in g.nodes]
    links = [{'source': a, 'target': b, 'value': d['count'], 'strength': round(d['weight'], 3), 'new': d['new']}
             for a, b, d in g.edges(data=True)]
    n_nodes, n_edges = g.number_of_nodes(), g.number_of_edges()
    return {'nodes': nodes, 'links': links, 'clusters': clusters,
            'statistics': {'total_nodes': n_nodes, 'total_edges': n_edges,
                           'significant_pairs': assoc['total_pairs'],
                           'avg_connections': round(2 * n_edges / n_nodes, 2) if n_nodes else 0,
                           'density': round(nx.density(g), 3) if n_nodes > 1 else 0},
            'pairs': assoc['pairs'][:40], 'total_documents': assoc['total_documents'],
            'excluded_hubs': assoc['excluded_hubs'], 'data_through': assoc['data_through']}


def timeline(days: int = 30, top_n: int = 15, window: int = 7) -> Dict[str, Any]:
    """Bar-chart race over a rolling `window`-day count: each frame ranks the
    concepts by their activity in the week up to that day, so newcomers
    enter and fading topics leave."""
    cube = get_cube()
    end = cube.data_through
    start = end - days + 1
    per, totals = cube.counts(start - window + 1, end)
    hubs = cube.hubs(per, totals)
    cands = [c for c in per if c not in hubs and sum(per[c]) >= 3]
    frames, prev_top, seen = [], set(), Counter()
    for day in range(start, end + 1):
        vals = {c: sum(cube.day_count(c, d) for d in range(day - window + 1, day + 1)) for c in cands}
        top = [c for c in sorted(cands, key=lambda c: (-vals[c], cube.name(c))) if vals[c] > 0][:top_n]
        frames.append({'date': _iso(day), 'rankings': [
            {'concept_id': c, 'display_name': cube.name(c), 'value': vals[c], 'rank': r + 1,
             'color': None, 'isNew': c not in prev_top and bool(prev_top)} for r, c in enumerate(top)]})
        prev_top = set(top)
        seen.update({c: vals[c] for c in top})
    palette = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc948', '#b07aa1', '#ff9da7', '#9c755f',
               '#1f77b4', '#d62728', '#2ca02c', '#9467bd', '#8c564b', '#e377c2', '#17becf', '#bcbd22', '#6b6ecf']
    colors = {c: palette[i % len(palette)] for i, (c, _) in enumerate(seen.most_common())}
    for f in frames:
        for r in f['rankings']:
            r['color'] = colors[r['concept_id']]
    return {'frames': frames,
            'concepts': [{'concept_id': c, 'display_name': cube.name(c), 'color': colors[c],
                          'total_value': sum(per[c])} for c, _ in seen.most_common()],
            'date_range': {'start': _iso(start), 'end': _iso(end)}, 'window_days': window,
            'data_through': _iso(end)}
