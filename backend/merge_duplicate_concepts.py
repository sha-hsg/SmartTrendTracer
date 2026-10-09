#!/usr/bin/env python
"""
Merge mechanically duplicated concepts (2026-10 fitness review: ~900 groups
such as "Clément Delangue" / "Clement Delangue", "HuggingFace" / "Hugging
Face", "LLM" / "LLMs").

Only mechanical differences count: case, accents, punctuation/spaces and a
trailing plural "s". Semantic synonyms ("RAG" / "Retrieval Augmented
Generation") are left to the alias UI.

Per group the winner is the most used concept (ties: the one placed in the
hierarchy, then the oldest). Every loser is folded into it:
- tag_instances move to the winner (a row is deleted when the item already
  carries the winner — unique index on content_type/content_id/concept_id);
- tag_aliases_v2 point to the winner; each loser name becomes an alias;
- parents/children of all concepts are rewired, the winner gets the union;
- concept_ids arrays on tweets/articles/papers/books, feed subscription
  names and the RAG index metadata (concept_ids + names) are remapped;
- the loser concept is deleted.
Afterwards hierarchy references to missing concepts and self references are removed.

    venv/bin/python merge_duplicate_concepts.py                  # dry run, report to logs/
    venv/bin/python merge_duplicate_concepts.py --apply          # live (take a backup first)
    venv/bin/python merge_duplicate_concepts.py --apply --db stt_merge_check --no-rag   # rehearsal
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from pymongo import MongoClient

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.config import settings  # noqa: E402
from app.paths import RAG_INDEX_CONCEPTS  # noqa: E402

LOG_DIR = Path(__file__).resolve().parents[1] / 'logs'
# reviewed false friends of the plural rule (2026-10-09): different things
SKIP_KEYS = {'canva', 'muse', 'dino', 'longmemeval'}


def merge_key(name: str) -> str:
    """Case-, accent-, punctuation- and plural-insensitive key."""
    # drop only combining accents (é -> e); other letters (π, ü's base, CJK) stay
    decomposed = unicodedata.normalize('NFKD', name or '')
    folded = ''.join(ch for ch in decomposed if unicodedata.category(ch) != 'Mn').lower()
    key = ''.join(ch for ch in folded if ch.isalnum())
    if len(key) > 3 and key.endswith('s') and not key.endswith('ss'):
        key = key[:-1]
    return key


def id_forms(cid):
    """All forms a concept id may take in other collections."""
    forms = {cid, str(cid)}
    if isinstance(cid, str) and ObjectId.is_valid(cid):
        forms.add(ObjectId(cid))
    return list(forms)


def plan(db):
    usage = Counter()
    for row in db.tag_instances.aggregate([{'$match': {'concept_id': {'$nin': [None, '']}}},
                                           {'$group': {'_id': '$concept_id', 'n': {'$sum': 1}}}]):
        usage[str(row['_id'])] += row['n']
    groups = defaultdict(list)
    for c in db.tag_concepts_v2.find({}, {'display_name': 1, 'parents': 1, 'children': 1, 'created_at': 1}):
        key = merge_key(c.get('display_name', ''))
        if key:
            groups[key].append(c)
    merges = []
    for key, members in groups.items():
        if len(members) < 2 or key in SKIP_KEYS:
            continue
        members.sort(key=lambda c: (-usage[str(c['_id'])],
                                    -(len(c.get('parents') or []) + len(c.get('children') or [])),
                                    str(c.get('created_at') or '')))
        winner, losers = members[0], members[1:]
        merges.append({'key': key, 'winner': winner, 'losers': losers,
                       'usage': {str(m['_id']): usage[str(m['_id'])] for m in members}})
    return merges


def fold(db, winner, loser, stats):
    # re-read both: earlier folds may have rewired their parents/children
    winner = db.tag_concepts_v2.find_one({'_id': winner['_id']}) or winner
    loser = db.tag_concepts_v2.find_one({'_id': loser['_id']})
    if loser is None:
        return
    w_id, l_id = winner['_id'], loser['_id']
    w_forms, l_forms = id_forms(w_id), id_forms(l_id)
    # tag instances
    for ti in db.tag_instances.find({'concept_id': {'$in': l_forms}}, {'content_type': 1, 'content_id': 1}):
        dup = db.tag_instances.find_one({'content_type': ti['content_type'], 'content_id': ti['content_id'],
                                         'concept_id': {'$in': w_forms}}, {'_id': 1})
        if dup:
            db.tag_instances.delete_one({'_id': ti['_id']})
            stats['instances_deleted'] += 1
        else:
            db.tag_instances.update_one({'_id': ti['_id']}, {'$set': {'concept_id': w_id}})
            stats['instances_moved'] += 1
    # aliases: repoint, then the loser's name as alias of the winner
    for alias in db.tag_aliases_v2.find({'concept_id': {'$in': l_forms}}, {'alias_text': 1}):
        if db.tag_aliases_v2.find_one({'alias_text': alias.get('alias_text'), 'concept_id': {'$in': w_forms}}):
            db.tag_aliases_v2.delete_one({'_id': alias['_id']})      # winner already has it (unique index)
        else:
            db.tag_aliases_v2.update_one({'_id': alias['_id']}, {'$set': {'concept_id': str(w_id)}})
        stats['aliases_moved'] += 1
    name = loser.get('display_name')
    if name and name != winner.get('display_name') and not db.tag_aliases_v2.find_one(
            {'alias_text': name, 'concept_id': {'$in': w_forms}}):
        db.tag_aliases_v2.insert_one({'alias_text': name, 'concept_id': str(w_id), 'alias_type': 'variant',
                                      'confidence': 1.0, 'created_at': datetime.now(timezone.utc),
                                      'metadata': {'source': 'merge_duplicate_concepts'}})
        stats['aliases_added'] += 1
    # hierarchy: winner gets the union, other concepts point to the winner
    parents = {p for p in (winner.get('parents') or []) + (loser.get('parents') or []) if str(p) not in map(str, (w_id, l_id))}
    children = {c for c in (winner.get('children') or []) + (loser.get('children') or []) if str(c) not in map(str, (w_id, l_id))}
    db.tag_concepts_v2.update_one({'_id': w_id}, {'$set': {'parents': list(parents), 'children': list(children)}})
    for field in ('parents', 'children'):
        for doc in db.tag_concepts_v2.find({field: {'$in': l_forms}}, {field: 1}):
            new = []
            for v in doc[field]:
                v = w_id if str(v) == str(l_id) else v
                if str(v) != str(doc['_id']) and str(v) not in map(str, new):
                    new.append(v)
            db.tag_concepts_v2.update_one({'_id': doc['_id']}, {'$set': {field: new}})
            stats['hierarchy_rewired'] += 1
    # content concept_ids arrays (stored as ObjectId or string)
    for coll in ('tweets', 'articles', 'papers', 'books'):
        for doc in db[coll].find({'concept_ids': {'$in': l_forms}}, {'concept_ids': 1}):
            new, seen = [], set()
            for v in doc['concept_ids']:
                if str(v) == str(l_id):
                    v = w_id if isinstance(v, ObjectId) else str(w_id)
                if str(v) not in seen:
                    seen.add(str(v))
                    new.append(v)
            db[coll].update_one({'_id': doc['_id']}, {'$set': {'concept_ids': new}})
            stats['content_arrays'] += 1
    if name:
        stats['feed_renamed'] += db.feed_subscriptions.update_many(
            {'concept': name}, {'$set': {'concept': winner.get('display_name')}}).modified_count
        db.feed_candidates.update_many({'concept': name}, {'$set': {'concept': winner.get('display_name')}})
    db.tag_concepts_v2.delete_one({'_id': l_id})
    db.tag_concepts_v2.update_one({'_id': w_id}, {'$unset': {'usage_count': ''}})
    stats['concepts_deleted'] += 1


def remap_rag(merges):
    path = RAG_INDEX_CONCEPTS / 'metadata.pkl'
    metadata = pickle.load(open(path, 'rb'))
    id_map, name_map = {}, {}
    for m in merges:
        for loser in m['losers']:
            id_map[str(loser['_id'])] = str(m['winner']['_id'])
            name_map[loser.get('display_name')] = m['winner'].get('display_name')
    changed = 0
    for entry in metadata:
        ids, names = entry.get('concept_ids') or [], entry.get('concepts') or []
        new_ids = list(dict.fromkeys(id_map.get(str(i), str(i)) for i in ids))
        new_names = list(dict.fromkeys(name_map.get(n, n) for n in names))
        if new_ids != list(map(str, ids)) or new_names != names:
            entry['concept_ids'], entry['concepts'] = new_ids, new_names
            changed += 1
    tmp = path.with_suffix('.pkl.tmp')
    pickle.dump(metadata, open(tmp, 'wb'))
    tmp.replace(path)
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--db', default=settings.mongodb_db)
    ap.add_argument('--no-rag', action='store_true', help='do not touch the RAG index metadata')
    args = ap.parse_args()
    db = MongoClient(settings.mongodb_uri)[args.db]
    merges = plan(db)
    n_losers = sum(len(m['losers']) for m in merges)
    LOG_DIR.mkdir(exist_ok=True)
    report = LOG_DIR / f"concept_merge_{'apply' if args.apply else 'dryrun'}_{datetime.now():%Y%m%d_%H%M%S}.txt"
    with open(report, 'w') as fh:
        for m in sorted(merges, key=lambda m: -sum(m['usage'].values())):
            fh.write(f"{m['winner'].get('display_name')!r} ({m['usage'][str(m['winner']['_id'])]}) <- "
                     + ', '.join(f"{lo.get('display_name')!r} ({m['usage'][str(lo['_id'])]})" for lo in m['losers']) + '\n')
    print(f'{len(merges)} groups, {n_losers} concepts to fold; report: {report}')
    if not args.apply:
        return
    stats = Counter()
    for m in merges:
        for loser in m['losers']:
            fold(db, m['winner'], loser, stats)
    # hierarchy hygiene: references to concepts that no longer exist, and self references
    existing = {str(i) for i in db.tag_concepts_v2.distinct('_id')}
    for c in db.tag_concepts_v2.find({}, {'parents': 1, 'children': 1}):
        upd = {}
        for field in ('parents', 'children'):
            vals = c.get(field) or []
            keep = [v for v in vals if str(v) in existing and str(v) != str(c['_id'])]
            if len(keep) != len(vals):
                upd[field] = keep
                stats['dangling_refs_removed'] += len(vals) - len(keep)
        if upd:
            db.tag_concepts_v2.update_one({'_id': c['_id']}, {'$set': upd})
    print('applied:', json.dumps(dict(stats)))
    if not args.no_rag and args.db == settings.mongodb_db:
        print('RAG metadata entries remapped:', remap_rag(merges))


if __name__ == '__main__':
    main()
