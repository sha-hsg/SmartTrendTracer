"""Micro-topics (global clustering, stable identity over time) and families
(groups of related micro-topics)."""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List

import faiss
import networkx as nx
import numpy as np

from .documents import concept_label

K = 15                        # neighbours in the document kNN graph
RESOLUTION = 8.0              # Louvain over documents: ~200 micro-topics for ~30k documents
MIN_TOPIC = 15
FAMILY_K = 6                  # topic-similarity graph: neighbours per topic
FAMILY_RESOLUTION = 3.0       # Louvain over topics -> balanced families
BIRTH_FLOOR = 0.002           # monthly share needed to count as alive
MIN_PAPERS_FOR_SHARE = 10
CHANNELS = ('tweet', 'article', 'paper')


def global_topics(vecs: np.ndarray) -> np.ndarray:
    """Topic label per document (-1 = in a group smaller than MIN_TOPIC)."""
    idx = faiss.IndexFlatIP(vecs.shape[1])
    idx.add(vecs)
    sims, nbrs = idx.search(vecs, K + 1)
    g = nx.Graph()
    g.add_nodes_from(range(len(vecs)))
    for i in range(len(vecs)):
        for s, j in zip(sims[i][1:], nbrs[i][1:]):
            if j >= 0 and s > 0:
                g.add_edge(i, int(j), weight=float(s))
    comms = nx.community.louvain_communities(g, weight='weight', resolution=RESOLUTION, seed=42)
    labels = np.full(len(vecs), -1)
    tid = 0
    for members in sorted(comms, key=len, reverse=True):
        if len(members) >= MIN_TOPIC:
            labels[list(members)] = tid
            tid += 1
    return labels


def channel_share(counts: Counter, totals: Counter, minimum: Dict[str, int]) -> float:
    """Share of a period, averaged over channels so that the many tweets do
    not drown articles and papers."""
    shares = [counts[ty] / totals[ty] for ty in CHANNELS if totals[ty] >= minimum.get(ty, 1)]
    return float(np.mean(shares)) if shares else 0.0


def describe_topics(labels, docs, vecs, months, global_freq, skip) -> List[Dict[str, Any]]:
    """Monthly life of every micro-topic: series, birth, peak, status, drift."""
    month_totals = defaultdict(Counter)
    for d in docs:
        month_totals[d['month']][d['type']] += 1
    topics = []
    for t in range(labels.max() + 1):
        mem = np.where(labels == t)[0]
        md = [docs[i] for i in mem]
        per_month = defaultdict(Counter)
        for d in md:
            per_month[d['month']][d['type']] += 1
        series = [channel_share(per_month[m], month_totals[m], {'paper': MIN_PAPERS_FOR_SHARE}) for m in months]
        alive = [i for i, s in enumerate(series) if s >= BIRTH_FLOOR and sum(per_month[months[i]].values()) >= 3]
        if not alive:
            continue
        c = vecs[mem].mean(axis=0)
        c /= np.linalg.norm(c) or 1
        birth = alive[0]
        smooth = np.convolve(series, np.ones(3) / 3, mode='same')
        peak = birth + int(np.argmax(smooth[birth:]))
        last3, prev3 = float(np.mean(smooth[-3:])), float(np.mean(smooth[-6:-3]))
        if last3 < 0.25 * smooth[peak]:
            status = 'faded'
        elif last3 > 1.3 * prev3 and last3 >= BIRTH_FLOOR:
            status = 'rising'
        elif last3 < 0.7 * prev3:
            status = 'declining'
        else:
            status = 'stable'

        def month_centroid(mi):
            v = vecs[[i for i in mem if docs[i]['month'] == months[mi]]].mean(axis=0)
            return v / (np.linalg.norm(v) or 1)
        drift = float(1 - month_centroid(alive[0]) @ month_centroid(alive[-1])) if len(alive) > 1 else 0.0
        first_docs = sorted(mem, key=lambda i: docs[i]['date'])[:12]
        topics.append({
            'id': t, 'label': concept_label(md, global_freq, len(docs), skip, min_support=0.08),
            'size': len(mem), 'members': mem, 'centroid': c,
            'series': [round(s, 5) for s in series], 'birth': birth, 'peak': peak,
            'status': status, 'drift': round(drift, 3),
            'movers': Counter(docs[i]['author'] for i in first_docs if docs[i]['type'] != 'paper').most_common(3),
            'examples': [docs[i]['text'][:140] for i in first_docs[:3]],
        })
    return topics


def group_families(topics, docs, global_freq, skip) -> List[Dict[str, Any]]:
    """Louvain over the topic-similarity graph; inside a family a later-born
    topic branches off its closest earlier-born relative (`parent`)."""
    C = np.stack([t['centroid'] for t in topics])
    S = C @ C.T
    tg = nx.Graph()
    tg.add_nodes_from(range(len(topics)))
    for i in range(len(topics)):
        for j in np.argsort(-S[i])[1:FAMILY_K + 1]:
            tg.add_edge(i, int(j), weight=float(max(S[i, j], 0)))
    comms = nx.community.louvain_communities(tg, weight='weight', resolution=FAMILY_RESOLUTION, seed=42)
    families = []
    for f, members in enumerate(sorted(comms, key=len, reverse=True)):
        mt = sorted((topics[i] for i in members), key=lambda t: (t['birth'], -t['size']))
        for i, t in enumerate(mt):
            t['family'] = f
            earlier = [p for p in mt[:i] if p['birth'] < t['birth']]
            t['parent'] = max(earlier, key=lambda p: float(p['centroid'] @ t['centroid']))['id'] if earlier else None
        fam_docs = [docs[i] for t in mt for i in t['members']]
        families.append({
            'id': f, 'name': concept_label(fam_docs, global_freq, len(docs), skip, min_support=0.03, min_count=3),
            'series': [round(float(x), 5) for x in np.sum([t['series'] for t in mt], axis=0)],
            'size': sum(t['size'] for t in mt), 'n_topics': len(mt), 'topics': mt})
    families.sort(key=lambda f: -f['size'])
    return families
