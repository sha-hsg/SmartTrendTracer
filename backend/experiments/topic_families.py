#!/usr/bin/env python
"""
Standalone HTML view of the bubble topic map (families, episodes, lineage).

The computation lives in app.services.topic_episodes (weekly scheduler job
topic_map, UI: Trend Dashboard → Episodes). This script renders the stored
map with the experiment template, which also has the family streamgraph and
the per-family branching view.

    cd backend && venv/bin/python experiments/topic_families.py             # latest stored map
    cd backend && venv/bin/python experiments/topic_families.py --recompute # compute + store first
Output: experiments/output/topic_families.html (local only, not in git).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.repositories import topic_maps  # noqa: E402
from app.services import topic_episodes  # noqa: E402

OUT = Path(__file__).resolve().parent / 'output' / 'topic_families.html'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--recompute', action='store_true', help='compute and store a new map first')
    args = parser.parse_args()
    if args.recompute:
        print(topic_episodes.build_topic_map())
    m = topic_maps.latest_topic_map({'_id': 0})
    if not m:
        sys.exit('No topic map stored yet — run with --recompute')
    data = {k: m[k] for k in ('months', 'weeks', 'families', 'episodes', 'episode_links')}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(Path(__file__).with_name('topic_families_template.html').read_text()
                   .replace('/*DATA*/null', json.dumps(data, default=str)))
    print(f'wrote {OUT} ({len(m["episodes"])} episodes, map of {m["created_at"]:%Y-%m-%d %H:%M})')


if __name__ == '__main__':
    main()
