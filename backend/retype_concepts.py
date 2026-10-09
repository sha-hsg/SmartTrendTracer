#!/usr/bin/env python
"""
Retype existing concepts (2026-10 fitness review #32): every auto-created
concept was stored as entity_type 'topic', so people, organisations and
products (Karpathy, Altman, Hugging Face) were indistinguishable from
methods. New concepts get the tagger's type (concepts.tagging.add_tag); this
asks the tagging model once for the most used concepts still typed 'topic'
or 'concept' ('concept' ones the model calls topic become 'topic').

    venv/bin/python retype_concepts.py               # dry run, top 500
    venv/bin/python retype_concepts.py --top 1000 --apply
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.repositories import ontology  # noqa: E402
from app.repositories.concepts.tagging import normalize_entity_type  # noqa: E402
from app.database.mongodb import get_database  # noqa: E402

BATCH = 80


def candidates(db, top: int):
    usage = ontology.usage_counts()
    # 'concept' is the older default (1873 concepts, Karpathy/Altman among them);
    # hierarchy categories (parents of other concepts) keep their type
    docs = list(db.tag_concepts_v2.find({'entity_type': {'$in': ['topic', 'concept', None]},
                                         '_id': {'$nin': ontology.hierarchy_parent_ids()}},
                                        {'slug': 1, 'display_name': 1, 'description': 1, 'entity_type': 1}))
    docs.sort(key=lambda c: -usage.get(str(c['_id']), 0))
    return [d for d in docs[:top] if d.get('slug')]


def classify(llm, batch):
    lines = '\n'.join(f"{c['slug']} | {c.get('display_name') or ''} | "
                      f"{re.sub(r'^Auto-generated concept for .*', '', c.get('description') or '')[:100]}"
                      for c in batch)
    prompt = llm.get_prompt('concept_entity_typing')
    raw = llm.complete_text('tag_suggestion', prompt['user_template'].format(concepts=lines),
                            system_prompt=prompt.get('system'))
    m = re.search(r'\{.*\}', raw, re.S)
    return json.loads(m.group(0)) if m else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--top', type=int, default=500)
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()
    from app.services.llm_manager import get_llm_manager
    llm, db = get_llm_manager(), get_database()
    todo = candidates(db, args.top)
    changes, failed = {}, 0
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        try:
            answer = classify(llm, batch)
        except Exception as e:                       # one bad batch must not stop the run
            print(f'batch {i // BATCH}: {type(e).__name__}: {e}')
            failed += len(batch)
            continue
        for c in batch:
            etype = normalize_entity_type(answer.get(c['slug']))
            if etype and (etype != 'topic' or c.get('entity_type') == 'concept'):
                changes[c['_id']] = (c.get('display_name'), etype)
    print(f'{len(todo)} concepts checked, {len(changes)} to retype, {failed} unclassified')
    print(dict(Counter(t for _, t in changes.values())))
    for name, etype in list(changes.values())[:40]:
        print(f'  {etype:13} {name}')
    if args.apply:
        for cid, (_, etype) in changes.items():
            db.tag_concepts_v2.update_one({'_id': cid}, {'$set': {'entity_type': etype}})
        print('applied')


if __name__ == '__main__':
    main()
