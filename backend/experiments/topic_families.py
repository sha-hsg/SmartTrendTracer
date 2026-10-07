#!/usr/bin/env python
"""
Topic families in the STT bubble — prototype v2 (2026-10).

v1 (topic_evolution.py) clustered every month on its own and linked months
afterwards: coarse settings gave continuous but few topics, fine settings
tore every stream apart. v2 separates identity from time:

1. Identity: all documents are clustered once, globally, into fine
   micro-topics (Louvain on a cosine kNN graph of author-debiased vectors).
   A micro-topic keeps its identity over the whole period.
2. Life: per micro-topic the monthly share (averaged over channels) gives
   birth (first month above a floor), peak, and current status.
3. Lineage: micro-topics are grouped into families by centroid similarity
   (average linkage). Inside a family, a micro-topic born later branches off
   its closest earlier-born relative (its parent) — that is how "agents"
   gets children such as memory, deep research or harnesses.
4. Drift: the monthly centroid of a micro-topic shows how its centre moves.

Output: experiments/output/topic_families.html and a text report.

    cd backend && venv/bin/python experiments/topic_families.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import faiss
import networkx as nx
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import topic_evolution as v1  # noqa: E402  (document loading, debiasing, labels)

OUT = Path(__file__).resolve().parent / 'output' / 'topic_families.html'
K = 15
RESOLUTION = 8.0              # ~200 micro-topics for ~31k documents
MIN_TOPIC = 15
FAMILY_K = 6                  # topic-similarity graph: neighbours per topic
FAMILY_RESOLUTION = 3.0       # Louvain over topics -> balanced families
BIRTH_FLOOR = 0.002           # share needed to count as alive in a month
MIN_PAPERS_FOR_SHARE = 10


def family_label(member_docs, global_freq, n_global, min_support=0.03):
    """Like v1.label_cluster, with a lower support floor: in a family of
    thousands of documents no single concept reaches 8%."""
    freq = Counter(c for d in member_docs for c in set(d['concepts']))
    n = len(member_docs)
    scored = []
    for c, f in freq.items():
        if c.lower() in v1.GENERIC or c in v1.AUTHOR_SPECIFIC or f < max(3, min_support * n):
            continue
        lift = (f / n) / (global_freq[c] / n_global)
        scored.append((np.log(lift + 1) * (f / n), c))
    top = [c for _, c in sorted(scored, reverse=True)[:3]]
    return ' · '.join(top) if top else '(unlabelled)'


def month_of(d):
    return d['date'].strftime('%Y-%m')


def global_topics(vecs):
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


def main():
    docs, vecs = v1.load_documents()
    v1.AUTHOR_SPECIFIC.update(v1.find_author_specific(docs))
    global_freq = Counter(c for d in docs for c in set(d['concepts']))
    months = sorted({month_of(d) for d in docs})
    # drop the running month: a partial month distorts shares and status
    from datetime import datetime, timezone
    current = datetime.now(timezone.utc).strftime('%Y-%m')
    months = [m for m in months if '2025-01' <= m < current]
    labels = global_topics(vecs)
    n_topics = labels.max() + 1
    print(f'{len(docs)} docs → {n_topics} micro-topics ({(labels < 0).mean():.1%} in tiny groups)')

    month_totals = defaultdict(Counter)
    for d in docs:
        month_totals[month_of(d)][d['type']] += 1

    topics = []
    for t in range(n_topics):
        mem = np.where(labels == t)[0]
        md = [docs[i] for i in mem]
        per_month = defaultdict(Counter)
        for d in md:
            per_month[month_of(d)][d['type']] += 1
        series = []
        for m in months:
            tot = month_totals[m]
            shares = [per_month[m][ty] / tot[ty] for ty in ('tweet', 'article', 'paper')
                      if tot[ty] >= (MIN_PAPERS_FOR_SHARE if ty == 'paper' else 1)]
            series.append(float(np.mean(shares)) if shares else 0.0)
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
        # drift: similarity of first-alive-month centroid to last-alive-month centroid
        def mcentroid(mi):
            ids = [i for i in mem if month_of(docs[i]) == months[mi]]
            v = vecs[ids].mean(axis=0)
            return v / (np.linalg.norm(v) or 1)
        drift = float(1 - mcentroid(alive[0]) @ mcentroid(alive[-1])) if len(alive) > 1 else 0.0
        first_docs = sorted(mem, key=lambda i: docs[i]['date'])[:12]
        movers = Counter(docs[i]['author'] for i in first_docs if docs[i]['type'] != 'paper').most_common(3)
        first_by_channel = {ty: min((docs[i]['date'] for i in mem if docs[i]['type'] == ty), default=None)
                            for ty in ('tweet', 'article', 'paper')}
        topics.append({'id': t, 'label': v1.label_cluster(md, global_freq, len(docs)), 'size': len(mem),
                       'members': mem,
                       'series': [round(s, 5) for s in series], 'birth': birth, 'peak': peak,
                       'status': status, 'drift': round(drift, 3), 'centroid': c,
                       'movers': movers,
                       'firsts': {k: v.strftime('%Y-%m-%d') for k, v in first_by_channel.items() if v},
                       'examples': [docs[i]['text'][:140] for i in first_docs[:3]]})

    # families by centroid similarity
    C = np.stack([t['centroid'] for t in topics])
    S = C @ C.T
    tg = nx.Graph()
    tg.add_nodes_from(range(len(topics)))
    for i in range(len(topics)):
        for j in np.argsort(-S[i])[1:FAMILY_K + 1]:
            tg.add_edge(i, int(j), weight=float(max(S[i, j], 0)))
    fam_comms = nx.community.louvain_communities(tg, weight='weight', resolution=FAMILY_RESOLUTION, seed=42)
    families = defaultdict(list)
    for f, members in enumerate(sorted(fam_comms, key=len, reverse=True)):
        for i in members:
            topics[i]['family'] = f
            families[f].append(topics[i])
    # parent = closest earlier-born topic in the same family
    for members in families.values():
        members.sort(key=lambda t: (t['birth'], -t['size']))
        for i, t in enumerate(members):
            earlier = [p for p in members[:i] if p['birth'] < t['birth']]
            t['parent'] = max(earlier, key=lambda p: float(p['centroid'] @ t['centroid']))['id'] if earlier else None

    fam_list = []
    for f, members in families.items():
        series = np.sum([m['series'] for m in members], axis=0)
        fam_docs = [docs[i] for m in members for i in m['members']]
        name = family_label(fam_docs, global_freq, len(docs))
        fam_list.append({'id': f, 'name': name, 'series': [round(float(x), 5) for x in series],
                         'size': sum(m['size'] for m in members), 'n_topics': len(members),
                         'topics': [{k: v for k, v in m.items() if k not in ('centroid', 'members')} for m in members]})
    fam_list.sort(key=lambda f: -f['size'])

    print(f'{len(fam_list)} families\n')
    for f in fam_list[:12]:
        print(f"## {f['name']}  ({f['n_topics']} topics, {f['size']} docs)")
        for t in f['topics'][:10]:
            par = next((p['label'] for p in f['topics'] if p['id'] == t['parent']), '—')
            print(f"   {months[t['birth']]} {t['status']:7s} drift {t['drift']:.2f}  {t['label'][:55]:55s} ← {par[:35]}")
    print('\nagent topics (all families):')
    for f in fam_list:
        for t in f['topics']:
            if 'agent' in t['label'].lower() or 'memory' in t['label'].lower():
                par = next((p['label'] for p in f['topics'] if p['id'] == t['parent']), '—')
                print(f"   [{f['name'][:28]:28s}] {months[t['birth']]} peak {months[t['peak']]} {t['status']:7s} "
                      f"{t['label'][:50]:50s} ← {par[:30]}  movers {t['movers'][:2]}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    html = (Path(__file__).with_name('topic_families_template.html').read_text()
            .replace('/*DATA*/null', json.dumps({'months': months, 'families': fam_list}, default=str)))
    OUT.write_text(html)
    print(f'\nwrote {OUT}')


if __name__ == '__main__':
    import logging
    logging.disable(logging.CRITICAL)
    main()
