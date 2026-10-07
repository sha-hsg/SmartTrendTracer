#!/usr/bin/env python
"""
Topic evolution in the STT bubble — prototype (2026-10).

Measures topics with embeddings and uses tags only as labels:

1. Documents (tweets, articles, papers) with their RAG embedding vectors
   (read from the FAISS index, no API cost) are split into time windows:
   quarters until 2025-03, months from 2025-04.
2. Per window, documents are clustered: Louvain on a cosine kNN graph
   (fixed seed, deterministic).
3. Lineage between consecutive windows: every document of window t is
   assigned to the closest cluster centroid of window t-1; the counts form
   a flow matrix. Strong flows become edges, and events follow from them:
   birth (no strong source), split (one source feeds several targets),
   merge (several sources feed one target), death (no strong target).
4. Topic weight is a share, averaged over channels (tweets, articles,
   papers), so neither the growing tweet volume nor one noisy channel
   dominates.
5. Labels: concept tags over-represented in the cluster (lift), excluding
   generic ones; plus first movers, channel order and your paper-import lag.

Output: experiments/output/topic_evolution.html (alluvial diagram) and a
text report on stdout.

    cd backend && venv/bin/python experiments/topic_evolution.py
"""
from __future__ import annotations

import json
import math
import pickle
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import faiss
import networkx as nx
import numpy as np

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

INDEX_DIR = BACKEND / 'data' / 'rag_index_concepts'
OUT_DIR = BACKEND / 'experiments' / 'output'

K_NEIGHBORS = 12
RESOLUTION = 2.5
MIN_CLUSTER = 8          # smaller groups are noise in a window
EDGE_MIN = 0.25          # share of a target cluster that must come from a source
BRANCH_MIN = 0.30        # split/merge: each branch carries at least this share
NOVEL_BIRTH = 0.5        # a cluster is born when this share of its docs fits no predecessor
AUTHOR_DEBIAS = 1.0      # subtract the author's mean direction (voice), keep content
MIN_PAPERS_FOR_SHARE = 10
AUTHOR_CONCENTRATION = 0.6
GENERIC = {'large language model', 'large language models', 'llm', 'llms', 'ai', 'artificial intelligence',
           'machine learning', 'deep learning', 'openai', 'google', 'anthropic', 'empirical study'}


def window_of(dt: datetime) -> str | None:
    if dt is None:
        return None
    if dt < datetime(2024, 10, 1, tzinfo=timezone.utc):
        return None
    if dt < datetime(2025, 4, 1, tzinfo=timezone.utc):
        q = (dt.month - 1) // 3 + 1
        return f'{dt.year}-Q{q}'
    return dt.strftime('%Y-%m')


def aware(dt):
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return None
    if isinstance(dt, datetime) and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def load_documents():
    from app.database.mongodb import get_database
    db = get_database()
    index = faiss.read_index(str(INDEX_DIR / 'faiss.index'))
    metadata = pickle.load(open(INDEX_DIR / 'metadata.pkl', 'rb'))
    doc_map = pickle.load(open(INDEX_DIR / 'doc_map.pkl', 'rb'))
    paper_dates = {str(p['_id']): p.get('created_at') for p in db.papers.find({}, {'created_at': 1})}
    article_meta = {str(a['_id']): a for a in db.articles.find({}, {'author_name': 1, 'published_at': 1})}
    docs = []
    for pos, m in enumerate(metadata):
        if m.get('stale'):
            continue
        if m['type'] == 'tweet':
            dt, author = m.get('created_at'), m.get('author')
        elif m['type'] == 'article':
            a = article_meta.get(m['id'], {})
            dt, author = a.get('published_at') or m.get('published_at'), a.get('author_name') or m.get('author')
        else:
            dt, author = paper_dates.get(m['id']), 'you (import)'
        dt = aware(dt)
        w = window_of(dt) if dt else None
        if w is None:
            continue
        docs.append({'pos': pos, 'type': m['type'], 'id': m['id'], 'date': dt, 'window': w,
                     'author': author or '?', 'concepts': m.get('concepts', []),
                     'text': doc_map.get(pos, '')[:300]})
    vecs = np.stack([index.reconstruct(d['pos']) for d in docs]).astype('float32')
    faiss.normalize_L2(vecs)
    # The indexed texts start with "Tweet by @x:" / "By: x", so vectors carry the
    # author's voice; remove each author's mean direction to cluster by content.
    global_mean = vecs.mean(axis=0)
    by_author = defaultdict(list)
    for i, d in enumerate(docs):
        by_author[(d['type'], d['author'])].append(i)
    for ids in by_author.values():
        if len(ids) >= 5:
            vecs[ids] -= AUTHOR_DEBIAS * (vecs[ids].mean(axis=0) - global_mean)
    faiss.normalize_L2(vecs)
    return docs, vecs


def cluster_window(vecs: np.ndarray, seed: int = 42) -> list[int]:
    n = len(vecs)
    k = min(K_NEIGHBORS, n - 1)
    idx = faiss.IndexFlatIP(vecs.shape[1])
    idx.add(vecs)
    sims, nbrs = idx.search(vecs, k + 1)
    g = nx.Graph()
    g.add_nodes_from(range(n))
    for i in range(n):
        for s, j in zip(sims[i][1:], nbrs[i][1:]):
            if j >= 0 and s > 0:
                w = float(s)
                if g.has_edge(i, j):
                    g[i][j]['weight'] = max(g[i][j]['weight'], w)
                else:
                    g.add_edge(i, int(j), weight=w)
    comms = nx.community.louvain_communities(g, weight='weight', resolution=RESOLUTION, seed=seed)
    labels = [-1] * n
    for cid, members in enumerate(sorted(comms, key=len, reverse=True)):
        for m in members:
            labels[m] = cid if len(members) >= MIN_CLUSTER else -1
    return labels


AUTHOR_SPECIFIC: set = set()


def find_author_specific(docs):
    """Concepts mostly attached to one author describe the author, not a topic."""
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


def label_cluster(member_docs, global_freq, n_global):
    freq = Counter(c for d in member_docs for c in set(d['concepts']))
    n = len(member_docs)
    scored = []
    for c, f in freq.items():
        if c.lower() in GENERIC or c in AUTHOR_SPECIFIC or f < max(2, 0.08 * n):
            continue
        lift = (f / n) / (global_freq[c] / n_global)
        scored.append((math.log(lift + 1) * (f / n), c))
    top = [c for _, c in sorted(scored, reverse=True)[:3]]
    return ' · '.join(top) if top else '(unlabelled)'


def main():
    docs, vecs = load_documents()
    windows = sorted({d['window'] for d in docs}, key=lambda w: (w[:4], w[5:].replace('Q1', '01').replace('Q2', '04')
                                                                  .replace('Q3', '07').replace('Q4', '10')))
    global_freq = Counter(c for d in docs for c in set(d['concepts']))
    AUTHOR_SPECIFIC.update(find_author_specific(docs))
    print(f'{len(AUTHOR_SPECIFIC)} author-specific concepts excluded from labels')
    by_window = defaultdict(list)
    for i, d in enumerate(docs):
        by_window[d['window']].append(i)

    channel_totals = {w: Counter(docs[i]['type'] for i in by_window[w]) for w in windows}
    clusters = []          # node dicts
    centroids = {}         # (window, cid) -> vector
    members_of = {}        # (window, cid) -> doc indices
    for wi, w in enumerate(windows):
        ids = by_window[w]
        if len(ids) < MIN_CLUSTER * 2:
            continue
        labels = cluster_window(vecs[ids])
        groups = defaultdict(list)
        for local, cid in enumerate(labels):
            if cid >= 0:
                groups[cid].append(ids[local])
        for cid, mem in groups.items():
            key = (w, cid)
            c = vecs[mem].mean(axis=0)
            centroids[key] = c / (np.linalg.norm(c) or 1)
            members_of[key] = mem
            per_channel = Counter(docs[i]['type'] for i in mem)
            shares = [per_channel[t] / channel_totals[w][t] for t in ('tweet', 'article', 'paper')
                      if channel_totals[w][t] >= (MIN_PAPERS_FOR_SHARE if t == 'paper' else 1)]
            md = [docs[i] for i in mem]
            clusters.append({'key': key, 'window': w, 'wi': wi, 'size': len(mem),
                             'share': float(np.mean(shares)), 'channels': dict(per_channel),
                             'label': label_cluster(md, global_freq, len(docs)),
                             'examples': [docs[i]['text'][:140] for i in mem[:3]]})

    # lineage: assign docs of window t to centroids of the previous populated window
    node_index = {c['key']: n for n, c in enumerate(clusters)}
    links = []
    populated = [w for w in windows if any(c['window'] == w for c in clusters)]
    for prev_w, cur_w in zip(populated, populated[1:]):
        prev_keys = [c['key'] for c in clusters if c['window'] == prev_w]
        P = np.stack([centroids[k] for k in prev_keys])
        # a doc belongs to a predecessor only if it is as close as that topic's own
        # members typically are (20th percentile of member-to-centroid similarity)
        tau = np.array([np.percentile(vecs[members_of[k]] @ centroids[k], 20) for k in prev_keys])
        for c in [c for c in clusters if c['window'] == cur_w]:
            mem = members_of[c['key']]
            sims = vecs[mem] @ P.T
            nearest = np.argmax(sims, axis=1)
            fits = sims[np.arange(len(mem)), nearest] >= tau[nearest]
            c['novel'] = round(float(1 - fits.mean()), 3)
            counts = Counter(nearest[fits].tolist())
            for pi, cnt in counts.items():
                frac = cnt / len(mem)
                if frac >= EDGE_MIN:
                    links.append({'source': node_index[prev_keys[pi]], 'target': node_index[c['key']],
                                  'frac': round(frac, 3), 'value': round(c['share'] * frac, 5)})

    # events
    out_edges, in_edges = defaultdict(list), defaultdict(list)
    for l in links:
        out_edges[l['source']].append(l)
        in_edges[l['target']].append(l)
    first_window = populated[0]
    for n, c in enumerate(clusters):
        ev = []
        if c['window'] != first_window and (not in_edges[n] or c.get('novel', 0) >= NOVEL_BIRTH):
            ev.append('birth')
        out_total = sum(l['value'] for l in out_edges[n])
        if sum(1 for l in out_edges[n] if out_total and l['value'] / out_total >= BRANCH_MIN) >= 2:
            ev.append('split')
        if sum(1 for l in in_edges[n] if l['frac'] >= BRANCH_MIN) >= 2:
            ev.append('merge')
        if c['window'] != populated[-1] and not out_edges[n]:
            ev.append('death')
        c['events'] = ev

    report(clusters, links, docs, members_of, populated)
    write_html(clusters, links, populated)


def thread_from(clusters, links, start, docs, members_of):
    """Follow the strongest successor from a node; collect bubble facts along the thread."""
    succ = defaultdict(list)
    for l in links:
        succ[l['source']].append(l)
    path, n = [start], start
    while succ[n]:
        n = max(succ[n], key=lambda l: l['frac'])['target']
        path.append(n)
    mem = [i for p in path for i in members_of[clusters[p]['key']]]
    by_type = defaultdict(list)
    for i in mem:
        by_type[docs[i]['type']].append(docs[i]['date'])
    firsts = {t: min(v).strftime('%Y-%m-%d') for t, v in by_type.items()}
    early = sorted(mem, key=lambda i: docs[i]['date'])[:15]
    movers = Counter(docs[i]['author'] for i in early if docs[i]['type'] != 'paper').most_common(3)
    return path, firsts, movers


def report(clusters, links, docs, members_of, windows):
    print(f'{len(docs)} documents, {len(windows)} windows, {len(clusters)} topics, {len(links)} lineage links\n')
    ev = Counter(e for c in clusters for e in c['events'])
    print('events:', dict(ev), '\n')
    for c in clusters:
        if 'split' in c['events'] or ('birth' in c['events'] and c['share'] > 0.04):
            print(f"{c['window']:8s} {','.join(c['events']):14s} share {c['share']:.3f}  {c['label']}")
    print('\nagent-related topics over time:')
    for c in clusters:
        if 'agent' in c['label'].lower():
            print(f"  {c['window']:8s} {c['share']:.3f} {','.join(c['events']):12s} {c['label']}")
    births = [n for n, c in enumerate(clusters) if 'birth' in c['events'] and c['share'] > 0.03]
    print('\nthreads from notable births (first movers / first appearance per channel):')
    for b in births[:8]:
        path, firsts, movers = thread_from(clusters, links, b, docs, members_of)
        print(f"  {clusters[b]['window']} {clusters[b]['label']}")
        print(f"     lasts {len(path)} windows → {clusters[path[-1]]['window']}; first: {firsts}; movers: {movers}")


def write_html(clusters, links, windows):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = {'windows': windows,
            'nodes': [{'name': c['label'], 'window': c['window'], 'wi': windows.index(c['window']),
                       'share': round(c['share'], 4), 'size': c['size'], 'events': c['events'],
                       'channels': c['channels'], 'examples': c['examples']} for c in clusters],
            'links': links}
    html = (Path(__file__).with_name('topic_evolution_template.html').read_text()
            .replace('/*DATA*/null', json.dumps(data, default=str)))
    out = OUT_DIR / 'topic_evolution.html'
    out.write_text(html)
    print(f'\nwrote {out}')


if __name__ == '__main__':
    import logging
    logging.disable(logging.CRITICAL)
    main()
