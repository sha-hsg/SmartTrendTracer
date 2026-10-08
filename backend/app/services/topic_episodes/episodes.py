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
EP_MIN_WEEKS = 2
EP_GAP = 1                    # runs separated by <= this many weeks are one episode
EP_MIN_DOCS = 8
WEEK_MIN = {'tweet': 1, 'article': 3, 'paper': 5}

# Lineage. Episode centroids are centred (global mean removed): raw cosine
# between any two documents is ~0.78, centred cosine of random episode pairs
# has its 99th percentile at ~0.37.
LINK_SIM = 0.40               # strong content similarity alone is enough
LINK_SIM_BAND = 0.25          # weaker similarity needs document evidence:
LINK_SHARE = 0.05             # >= this share of the successor's nearest neighbours lie in the predecessor
LINK_LIFT = 40.0              # ... and that share is >= LIFT x the predecessor's share of all documents
LINK_KNN = 10
LINK_MAX_GAP = 6              # weeks between predecessor's end and successor's start
LINK_MAX_SPAN = 26            # predecessor started at most this many weeks before the successor
MAX_PARENTS = 2


def detect_episodes(mem, docs, weeks, week_totals, skip) -> List[Dict[str, Any]]:
    """Contiguous weeks in which one micro-topic gets clearly more attention
    than its own baseline."""
    per_week = defaultdict(Counter)
    for i in mem:
        per_week[docs[i]['week']][docs[i]['type']] += 1
    series = [channel_share(per_week[w], week_totals[w], WEEK_MIN) for w in weeks]
    smooth = np.convolve(series, np.ones(3) / 3, mode='same')
    nonzero = smooth[smooth > 0]
    if not len(nonzero):
        return []
    baseline = float(np.median(nonzero))
    hot = smooth >= max(EP_FACTOR * baseline, EP_FLOOR)
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
        span = set(weeks[a:b + 1])
        idx = [i for i in mem if docs[i]['week'] in span]
        if len(idx) < EP_MIN_DOCS:
            continue
        ep_docs = [docs[i] for i in idx]
        tags = concept_label(ep_docs, topic_freq, len(topic_docs), skip, min_support=0.1, top=2)
        early = sorted(ep_docs, key=lambda d: d['date'])
        peak = a + int(np.argmax(smooth[a:b + 1]))
        out.append({'name': tags, 'tags': tags, 'start': weeks[a], 'end': weeks[b], 'peak': weeks[peak],
                    'wi': [a, b], '_idx': idx, 'weeks': b - a + 1, 'docs': len(ep_docs),
                    'intensity': round(float(smooth[peak] / baseline), 1),
                    'peak_share': round(float(smooth[peak]), 4),
                    'movers': Counter(d['author'] for d in early[:10] if d['type'] != 'paper').most_common(3),
                    'channels': dict(Counter(d['type'] for d in ep_docs)),
                    'examples': [d['text'][:140] for d in early[:3]]})
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
            if sim >= LINK_SIM or (sim >= LINK_SIM_BAND and share >= LINK_SHARE and lift >= LINK_LIFT):
                cands.append((sim + share, sim, share, i))
        cands.sort(reverse=True)
        for score, sim, share, i in cands[:MAX_PARENTS]:
            if score >= cands[0][0] - 0.05:
                links.append({'source': i, 'target': j, 'sim': round(sim, 3), 'share': round(share, 3)})
    return links


def lineage_events(episodes, links, last_week_index) -> None:
    """birth (no predecessor), split (>= 2 successors), merge (>= 2
    predecessors), end (no successor and quiet for LINK_MAX_GAP weeks)."""
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
        if not kids[i] and e['wi'][1] < last_week_index - LINK_MAX_GAP:
            ev.append('end')
        e['events'] = ev
        e['parents'], e['children'] = parents[i], kids[i]
