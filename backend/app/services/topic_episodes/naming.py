"""Short episode names via the LLM (prompt episode_naming), with a noise flag.

Names are cached by content, not by cluster number: the clustering is redone
on every run and its topic numbers change, but an episode keeps most of its
documents. A cached name is reused when the document sets overlap enough."""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from typing import Any, Dict, List

from app.repositories import topic_maps as repo

logger = logging.getLogger(__name__)

BATCH = 6
REUSE_JACCARD = 0.5           # same episode, grown or shrunk a little
REUSE_CONTAINED = 0.8         # ... or the cached episode lies mostly inside the new one, same start


def _match(keys: set, start: str, cache: List[Dict[str, Any]], by_key) -> Dict[str, Any] | None:
    best, best_score = None, 0.0
    for ci in {ci for k in keys for ci in by_key.get(k, ())}:
        c = cache[ci]
        inter = len(keys & c['_keys'])
        jac = inter / len(keys | c['_keys'])
        contained = inter / len(c['_keys']) if c['_keys'] else 0.0
        score = jac if jac >= REUSE_JACCARD else (contained if contained >= REUSE_CONTAINED and c.get('start') == start else 0.0)
        if score > best_score:
            best, best_score = c, score
    return best


def name_episodes(episodes: List[Dict[str, Any]], docs: List[Dict[str, Any]], llm=None) -> Dict[str, int]:
    """Sets e['name'] and e['noise'] for every episode; returns counts."""
    cache = repo.episode_names()
    by_key = defaultdict(list)
    for ci, c in enumerate(cache):
        c['_keys'] = set(c.get('doc_keys', []))
        for k in c['_keys']:
            by_key[k].append(ci)
    todo = []
    for e in episodes:
        keys = {docs[i]['key'] for i in e['_idx']}
        hit = _match(keys, e['start'], cache, by_key)
        if hit:
            e['name'], e['noise'] = hit['name'], hit.get('noise', False)
        else:
            e['noise'] = False
            todo.append((e, keys))
    named = 0
    if todo:
        if llm is None:
            from app.services.llm_manager import get_llm_manager
            llm = get_llm_manager()
        prompt = llm.get_prompt('episode_naming')
        for k in range(0, len(todo), BATCH):
            chunk = todo[k:k + BATCH]
            payload = [{'id': n, 'tags': e['tags'], 'period': f"{e['start']}..{e['end']}",
                        'examples': [x[:160] for x in e['examples']]} for n, (e, _) in enumerate(chunk)]
            try:
                raw = llm.complete_text('content_classification',
                                        prompt['user_template'].format(episodes=json.dumps(payload, ensure_ascii=False)),
                                        system_prompt=prompt['system'])
                items = json.loads(raw[raw.index('['):raw.rindex(']') + 1])
            except Exception as ex:  # keep the concept-tag names for this batch
                logger.warning(f'Episode naming batch failed: {type(ex).__name__}: {ex}')
                continue
            new = []
            for it in items:
                try:
                    n = int(it.get('id', -1))
                except (AttributeError, TypeError, ValueError):
                    continue
                if 0 <= n < len(chunk) and str(it.get('name', '')).strip():
                    e, keys = chunk[n]
                    e['name'], e['noise'] = str(it['name']).strip(), bool(it.get('noise'))
                    new.append({'name': e['name'], 'noise': e['noise'], 'start': e['start'],
                                'doc_keys': sorted(keys)})
            repo.add_episode_names(new)
            named += len(new)
    return {'reused': len(episodes) - len(todo), 'named': named, 'unnamed': len(todo) - named}
