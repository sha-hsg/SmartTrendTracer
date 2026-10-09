#!/usr/bin/env python
"""
Merge duplicate papers (2026-10 fitness review): the same paper imported
twice under one arXiv id (formats "arXiv:2512.24601", "2512.24601v1",
"2512.24601") or one DOI. Only groups whose titles match after
normalisation are merged — two different papers that share a wrong arXiv id
(the RAGE-KG pair on 2312.10997) stay apart.

The winner is the processed copy with the most content/analyses; the loser's
tags (deduplicated), analyses and citations (references.cited_by) move to
it, its Q&A chunk cache is dropped, then it is deleted. The RAG update marks
the deleted paper as removed on its next run.

    venv/bin/python merge_duplicate_papers.py            # dry run
    venv/bin/python merge_duplicate_papers.py --apply
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

from pymongo import MongoClient

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.config import settings  # noqa: E402
from app.services.paper_hygiene import _arxiv_key  # noqa: E402


def title_key(title: str) -> str:
    return re.sub(r'[^a-z0-9]', '', (title or '').lower())


def groups(db):
    by_key = defaultdict(list)
    fields = {'title': 1, 'arxiv_id': 1, 'doi': 1, 'content': 1, 'analyses': 1, 'processing_status': 1,
              'created_at': 1}
    for p in db.papers.find({'$or': [{'arxiv_id': {'$nin': [None, '']}}, {'doi': {'$nin': [None, '']}}]}, fields):
        if p.get('arxiv_id'):
            by_key['arxiv:' + _arxiv_key(p['arxiv_id'])].append(p)
        elif p.get('doi'):
            by_key['doi:' + p['doi'].strip().lower()].append(p)
    out = []
    for key, papers in by_key.items():
        if len(papers) < 2:
            continue
        by_title = defaultdict(list)
        for p in papers:
            by_title[title_key(p.get('title'))].append(p)
        for same in by_title.values():
            if len(same) > 1:
                same.sort(key=lambda p: (p.get('processing_status') != 'completed', -len(p.get('analyses') or []),
                                         -len(p.get('content') or ''), str(p.get('created_at'))))
                out.append((key, same[0], same[1:]))
    return out


def fold(db, winner, loser, stats):
    w, lo = str(winner['_id']), str(loser['_id'])
    for ti in db.tag_instances.find({'content_type': 'paper', 'content_id': lo}):
        if db.tag_instances.find_one({'content_type': 'paper', 'content_id': w, 'concept_id': ti['concept_id']}):
            db.tag_instances.delete_one({'_id': ti['_id']})
        else:
            db.tag_instances.update_one({'_id': ti['_id']}, {'$set': {'content_id': w}})
            stats['tags_moved'] += 1
    if loser.get('analyses'):
        db.papers.update_one({'_id': winner['_id']}, {'$push': {'analyses': {'$each': loser['analyses']}}})
        stats['analyses_moved'] += len(loser['analyses'])
    for ref in db.references.find({'cited_by': {'$in': [lo, loser['_id']]}}, {'cited_by': 1}):
        cited = [w if str(c) == lo else c for c in ref['cited_by']]
        cited = list(dict.fromkeys(map(str, cited)))
        db.references.update_one({'_id': ref['_id']}, {'$set': {'cited_by': cited, 'citation_count': len(cited)}})
        stats['citations_rewired'] += 1
    db.paper_chunks.delete_many({'_id': {'$in': [lo, loser['_id']]}})
    db.papers.delete_one({'_id': loser['_id']})
    stats['papers_deleted'] += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()
    db = MongoClient(settings.mongodb_uri)[settings.mongodb_db]
    found = groups(db)
    for key, winner, losers in found:
        print(f"{key}: keep {winner['_id']} ({(winner.get('title') or '')[:60]!r}) <- "
              + ', '.join(str(lo['_id']) for lo in losers))
    if not args.apply:
        print(f'{len(found)} groups (dry run)')
        return
    stats = defaultdict(int)
    for _, winner, losers in found:
        for loser in losers:
            fold(db, winner, loser, stats)
    print('applied:', dict(stats))


if __name__ == '__main__':
    main()
