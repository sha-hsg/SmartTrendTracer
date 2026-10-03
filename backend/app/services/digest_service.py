"""
Weekly digest: one briefing per week from data STT already has.

Collects the week's trend overview (rising/declining/stable concepts and
anomalies, from trend_overview_service), new papers and articles, the
most-liked tweets and new paper-feed suggestions, then asks the LLM (task
trend_analysis, prompt weekly_digest) for a short narrative. The raw data is
stored with the text, so the page shows facts even if the LLM call fails.

Run weekly by stt_scheduler.py (job weekly_digest) — the week is the last
7 days up to the run — and on demand via POST /api/digest/generate.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from app.repositories import digests as repo
from app.repositories import paper_feed as feed_repo

logger = logging.getLogger(__name__)


def _trend_item(t: Dict[str, Any]) -> Dict[str, Any]:
    return {'concept': t['display_name'], 'count': t['count'], 'previous': t['previous_count'],
            'velocity_pct': t['velocity'], 'breakdown': t.get('content_breakdown', {})}


def collect_week(now: Optional[datetime] = None) -> Dict[str, Any]:
    """Facts of the 7 days before `now` (JSON-serializable)."""
    from app.services.trend_overview_service import compute_at_a_glance
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=7)
    overview = compute_at_a_glance(hours=168, limit=10)
    papers = repo.new_papers(since)
    articles = repo.new_articles(since)
    tweets = repo.top_tweets(since)
    feed_top = [c for c in feed_repo.list_candidates('new', limit=50)
                if c.get('found_at') and c['found_at'].replace(tzinfo=timezone.utc) >= since][:5]
    return {
        'week_start': since.isoformat(),
        'week_end': now.isoformat(),
        'stats': {
            'tweets': repo.count_new('tweets', 'created_at', since),
            'articles': repo.count_new('articles', 'published_at', since),
            'papers': repo.count_new('papers', 'created_at', since),
            'feed_suggestions': feed_repo.count_candidates('new', since=since),
            'active_concepts': overview.get('statistics', {}).get('unique_concepts'),
        },
        'rising': [_trend_item(t) for t in overview.get('hot_topics', [])],
        'declining': [_trend_item(t) for t in overview.get('declining', [])[:5]],
        'stable': [_trend_item(t) for t in overview.get('stable', [])[:5]],
        'anomalies': [{'concept': a['display_name'], 'z_score': a['z_score'],
                       'current': a['current_value'], 'baseline': a['baseline_avg']}
                      for a in overview.get('anomalies', [])],
        'new_papers': [{'id': str(p['_id']), 'title': p.get('title', ''), 'source': p.get('source'),
                        'abstract': (p.get('abstract') or '')[:400]} for p in papers],
        'new_articles': [{'id': str(a['_id']), 'title': a.get('title', ''), 'author': a.get('author_name'),
                          'url': a.get('url')} for a in articles],
        'top_tweets': [{'id': str(t['_id']), 'author': t.get('author_username'), 'likes': t.get('likes', 0),
                        'text': (t.get('text') or '')[:280]} for t in tweets],
        'feed_suggestions': [{'title': c['title'], 'arxiv_id': c['arxiv_id'], 'score': c.get('score'),
                              'subscription': c.get('subscription_name')} for c in feed_top],
    }


def write_summary(data: Dict[str, Any], llm=None) -> str:
    """LLM narrative for the collected data (prompt weekly_digest)."""
    if llm is None:
        from app.services.llm_manager import get_llm_manager
        llm = get_llm_manager()
    prompt = llm.get_prompt('weekly_digest')
    # Abstracts and tweet texts are context for the model; keep the prompt compact
    compact = {**data, 'new_papers': [{k: p[k] for k in ('title', 'source', 'abstract')} for p in data['new_papers'][:15]]}
    user = prompt['user_template'].format(week_start=data['week_start'][:10], week_end=data['week_end'][:10],
                                          data=json.dumps(compact, ensure_ascii=False, default=str))
    return llm.complete_text('trend_analysis', user, system_prompt=prompt['system'])


def generate_digest(now: Optional[datetime] = None, llm=None) -> Dict[str, Any]:
    data = collect_week(now)
    try:
        summary, error = write_summary(data, llm), None
    except Exception as e:  # the facts are still worth storing
        logger.exception('Digest summary failed')
        summary, error = '', f'{type(e).__name__}: {e}'[:300]
    doc = {**data, 'week_start': data['week_start'][:10], 'week_end': data['week_end'][:10],
           'summary': summary, 'summary_error': error, 'created_at': datetime.now(timezone.utc)}
    digest_id = repo.save_digest(doc)
    logger.info(f"Digest {doc['week_start']}..{doc['week_end']} saved ({len(summary)} chars)")
    return {'id': digest_id, 'week_start': doc['week_start'], 'week_end': doc['week_end'],
            'stats': doc['stats'], 'summary_ok': error is None}
