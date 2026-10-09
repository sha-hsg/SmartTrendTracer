"""Episodes (bursts inside a micro-topic, with a start and an end) and their
lineage: continuation, split, merge, end."""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List

import faiss
import numpy as np

from .documents import concept_label
from .topics import channel_share

EP_FACTOR = 2.5               # smoothed weekly share >= factor x the topic's own baseline
EP_FLOOR = 0.003              # ... and at least this share of the week
EP_MIN_WEEKS = 2              # weeks hot in the smoothed series (a strong single week qualifies)
EP_TRIM = 0.5                 # bounds are trimmed to weeks whose raw share reaches this part of the threshold
EP_GAP = 1                    # runs separated by <= this many weeks are one episode
EP_EXAMPLES = 3               # naming/examples: documents of the peak week closest to the episode centre
EP_MIN_DOCS = 8
WEEK_MIN = {'tweet': 1, 'article': 3, 'paper': 5}

# Lineage. Episode centroids are centred (global mean removed): raw cosine
# between any two documents is ~0.78, centred cosine of random episode pairs
# has its 99th percentile at ~0.37.
LINK_SIM = 0.40               # strong content similarity ...
LINK_EVIDENCE = 0.02          # ... plus some document evidence (except within one micro-topic: a recurrence)
LINK_SIM_BAND = 0.25          # weaker similarity needs strong document evidence:
LINK_SHARE = 0.05             # >= this share of the successor's nearest neighbours lie in the predecessor
LINK_LIFT = 40.0              # ... and that share is >= LIFT x the predecessor's share of all documents
END_MIN_DOCS = 30             # "ended" is only shown for episodes that had a predecessor or this many documents
LINK_KNN = 10
LINK_MAX_GAP = 6              # weeks between predecessor's end and successor's start
LINK_MAX_SPAN = 26            # predecessor started at most this many weeks before the successor
MAX_PARENTS = 2


def smooth3(series) -> np.ndarray:
    """3-week moving average with edge correction: the first and last week
    are averaged over the weeks that exist (zero padding made a burst in the
    last complete week count only two thirds)."""
    x = np.asarray(series, dtype=float)
    return np.convolve(x, np.ones(3), mode='same') / np.convolve(np.ones(len(x)), np.ones(3), mode='same')


def detect_episodes(mem, docs, weeks, week_totals, skip, vecs=None) -> List[Dict[str, Any]]:
    """Contiguous weeks in which one micro-topic gets clearly more attention
    than its own baseline. Detection runs on the smoothed series; the bounds
    are then trimmed to the weeks that really carry the burst, since
    smoothing alone started every episode a week early and stretched a
    single hot week to three."""
    per_week = defaultdict(Counter)
    for i in mem:
        per_week[docs[i]['week']][docs[i]['type']] += 1
    series = [channel_share(per_week[w], week_totals[w], WEEK_MIN) for w in weeks]
    smooth = smooth3(series)
    nonzero = smooth[smooth > 0]
    if not len(nonzero):
        return []
    baseline = float(np.median(nonzero))
    thr = max(EP_FACTOR * baseline, EP_FLOOR)
    hot = smooth >= thr
    runs, start = [], None
    for i, h in enumerate(list(hot) + [False]):
        if h and start is None:
            start = i
        if not h and start is not None:
            runs.append([start, i - 1])
            start = None
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] - 1 <= EP_GAP:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    topic_docs = [docs[i] for i in mem]
    topic_freq = Counter(c for d in topic_docs for c in set(d['concepts']))
    out = []
    for a, b in merged:
        if b - a + 1 < EP_MIN_WEEKS:
            continue
        strong = [w for w in range(a, b + 1) if series[w] >= EP_TRIM * thr]
        if not strong:
            continue
        a, b = strong[0], strong[-1]
        span = set(weeks[a:b + 1])
        idx = [i for i in mem if docs[i]['week'] in span]
        if len(idx) < EP_MIN_DOCS:
            continue
        ep_docs = [docs[i] for i in idx]
        tags = concept_label(ep_docs, topic_freq, len(topic_docs), skip, min_support=0.1, top=2)
        early = sorted(ep_docs, key=lambda d: d['date'])
        peak = a + int(np.argmax([series[w] for w in range(a, b + 1)]))
        peak_idx = [i for i in idx if docs[i]['week'] == weeks[peak]] or idx
        if vecs is not None:
            centre = vecs[idx].mean(axis=0)
            peak_idx = sorted(peak_idx, key=lambda i: -float(vecs[i] @ centre))
        examples = [docs[i]['text'][:140] for i in peak_idx[:EP_EXAMPLES]]
        out.append({'name': tags, 'tags': tags, 'start': weeks[a], 'end': weeks[b], 'peak': weeks[peak],
                    'wi': [a, b], '_idx': idx, 'weeks': b - a + 1, 'docs': len(ep_docs),
                    'intensity': round(float(max(smooth[peak], series[peak]) / baseline), 1),
                    'peak_share': round(float(series[peak]), 4),
                    'movers': Counter(d['author'] for d in early[:10] if d['type'] != 'paper').most_common(3),
                    'channels': dict(Counter(d['type'] for d in ep_docs)),
                    'examples': examples})
    return out


def _neighbour_votes(episodes, vecs):
    """For every episode B: how many of the LINK_KNN nearest neighbours of its
    documents (outside B) belong to each other episode, and the vote total."""
    owner = defaultdict(set)
    for i, e in enumerate(episodes):
        for x in e['_idx']:
            owner[x].add(i)
    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)
    votes, totals = [], []
    for b in episodes:
        mine = set(b['_idx'])
        _, nbrs = index.search(vecs[b['_idx']], LINK_KNN + min(len(mine), 40))
        cnt, n = Counter(), 0
        for row in nbrs:
            row = [x for x in row if x >= 0 and x not in mine][:LINK_KNN]
            n += len(row)
            for x in row:
                cnt.update(owner.get(x, ()))
        votes.append(cnt)
        totals.append(max(n, 1))
    return votes, totals


def link_episodes(episodes, vecs) -> List[Dict[str, Any]]:
    """B descends from A when A was active shortly before B started and either
    their centred centroids are clearly similar, or they are moderately similar
    and B's documents sit unusually often next to A's documents."""
    gm = vecs.mean(axis=0)
    C = np.stack([vecs[e['_idx']].mean(axis=0) - gm for e in episodes])
    C /= np.linalg.norm(C, axis=1, keepdims=True)
    S = C @ C.T
    votes, totals = _neighbour_votes(episodes, vecs)
    n_docs = len(vecs)
    links = []
    for j, b in enumerate(episodes):
        cands = []
        for i, a in enumerate(episodes):
            if not (a['wi'][0] < b['wi'][0] and b['wi'][0] - a['wi'][1] <= LINK_MAX_GAP
                    and b['wi'][0] - a['wi'][0] <= LINK_MAX_SPAN):
                continue
            sim = float(S[i, j])
            share = votes[j][i] / totals[j]
            lift = share / (len(a['_idx']) / n_docs)
            recurrence = a.get('topic_id') is not None and a.get('topic_id') == b.get('topic_id')
            strong = sim >= LINK_SIM and (recurrence or share >= LINK_EVIDENCE)
            if strong or (sim >= LINK_SIM_BAND and share >= LINK_SHARE and lift >= LINK_LIFT):
                cands.append((sim + share, sim, share, i))
        cands.sort(reverse=True)
        for score, sim, share, i in cands[:MAX_PARENTS]:
            if score >= cands[0][0] - 0.05:
                links.append({'source': i, 'target': j, 'sim': round(sim, 3), 'share': round(share, 3)})
    return links


def lineage_events(episodes, links, last_week_index) -> None:
    """birth (no predecessor), split (>= 2 successors), merge (>= 2
    predecessors), end (no successor, quiet for LINK_MAX_GAP weeks, and the
    episode mattered: a predecessor or END_MIN_DOCS documents)."""
    kids, parents = defaultdict(list), defaultdict(list)
    for link in links:
        kids[link['source']].append(link['target'])
        parents[link['target']].append(link['source'])
    for i, e in enumerate(episodes):
        ev = []
        if not parents[i]:
            ev.append('birth')
        if len(kids[i]) >= 2:
            ev.append('split')
        if len(parents[i]) >= 2:
            ev.append('merge')
        if (not kids[i] and e['wi'][1] < last_week_index - LINK_MAX_GAP
                and (parents[i] or e['docs'] >= END_MIN_DOCS)):
            ev.append('end')
        e['events'] = ev
        e['parents'], e['children'] = parents[i], kids[i]
