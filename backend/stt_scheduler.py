#!/usr/bin/env python3
"""
STT scheduler: runs periodic jobs (content tagging every few hours, daily paper
feed and RAG index update, weekly topic map, digest and database backup)
while STT is running.

The Mac does not run around the clock, so jobs are not bound to a clock time:
every few minutes the scheduler checks which jobs are due — "daily" means the
last success is more than DAILY_AFTER old, "weekly" means no success since the
start of the current week (Monday, local time) — and catches up missed runs
right after STT starts. Job state lives in MongoDB (scheduled_jobs).

Started/stopped by start_stt.sh / stop_stt.sh; log: logs/scheduler.log.
    venv/bin/python stt_scheduler.py            # run until SIGTERM
    venv/bin/python stt_scheduler.py --once     # run due jobs once and exit
    venv/bin/python stt_scheduler.py --run NAME # run one job now
"""
import argparse
import logging
import signal
import sys
import threading
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("stt_scheduler")

CHECK_EVERY_SECONDS = 300
DAILY_AFTER = timedelta(hours=20)
TAGGING_EVERY = timedelta(hours=6)
FAILURE_BACKOFF = timedelta(hours=2)   # after a failed run, wait before retrying (no retry storm)


def due_daily(last_success: Optional[datetime], now: datetime) -> bool:
    return last_success is None or now - last_success >= DAILY_AFTER


def start_of_week(now: datetime) -> datetime:
    """Monday 00:00 in the machine's local time zone, as an aware datetime."""
    local = now.astimezone()
    monday = (local - timedelta(days=local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return monday


def due_weekly(last_success: Optional[datetime], now: datetime) -> bool:
    return last_success is None or last_success < start_of_week(now)


def due_tagging(last_success: Optional[datetime], now: datetime) -> bool:
    return last_success is None or now - last_success >= TAGGING_EVERY


# --- jobs ---------------------------------------------------------------------

def job_rag_update():
    """Add new/changed content to the RAG index via the running backend, so its
    in-memory index stays current (a separate process would only update files)."""
    import httpx
    from app.config import settings
    r = httpx.post(f'http://localhost:{settings.backend_port}/api/rag/update', timeout=1800)
    r.raise_for_status()
    return r.json().get('stats')


def job_tag_content():
    """Concept tags for untagged tweets, articles and processed papers
    (app.services.concept_tagging, LLM task tag_suggestion). Trend views only
    count tagged days; untagged papers/articles were missing from search."""
    from app.services import concept_tagging
    return {t: concept_tagging.tag_untagged(t) for t in ('tweet', 'article', 'paper')}


def job_paper_hygiene():
    """Paper publication dates in one ISO form; missing ones from arXiv/Crossref."""
    from app.services import paper_hygiene
    return paper_hygiene.run()


def job_newsletters():
    """Substack newsletters from Gmail (direct subscriptions and forwarded
    authors, backend/forwarded_authors.json). Never opens a browser: a
    missing/revoked token fails with the command for a one-time login."""
    from app.collectors.gmail_substack_collector import GmailSubstackCollector
    collector = GmailSubstackCollector()
    collector.authenticate(interactive=False)
    from app.database.mongodb import get_database
    before = get_database().articles.count_documents({'source': 'email'})
    collector.collect_newsletters(max_results=50)       # its count includes already stored mails
    saved = get_database().articles.count_documents({'source': 'email'}) - before
    # senders not in backend/newsletter_sources.json: add them there to keep them
    return {'new_articles': saved, 'skipped_senders': sorted(collector.skipped_senders)}


def job_paper_feed():
    """Check all paper feed subscriptions for new arXiv papers."""
    from app.services.paper_feed_service import run_feed
    result = run_feed()
    if result.get('failed'):     # partial failure: report it, retry after the backoff
        raise RuntimeError(f"{len(result['failed'])} of {result['subscriptions']} feeds failed "
                           f"({', '.join(result['failed'])}); {result['new']} new from the others")
    return {'subscriptions': result['subscriptions'], 'new': result['new']}


def job_topic_map():
    """Topics, episodes and their lineage in the bubble (topic_episodes)."""
    from app.services.topic_episodes import build_topic_map
    stats = build_topic_map()
    return {k: stats[k] for k in ('episodes', 'links', 'events', 'naming')}


def job_backup():
    """Weekly mongodump of the smarttrendtracer database (backup_service)."""
    from app.services.backup_service import run_backup
    return run_backup()


def job_weekly_digest():
    """Weekly briefing; runs after the feed so its suggestions are included."""
    from app.services.digest_service import generate_digest
    return generate_digest()


# Run order matters: tags first (the RAG update picks up newly tagged content,
# trend views count only tagged days), the topic map uses the freshly updated
# RAG index, the digest uses the feed and the topic map.
JOBS: Dict[str, Dict] = {
    # 'newsletters' (Gmail) paused 2026-10-09: Substack posts are fetched directly
    # (Playwright collector / URL import). Re-enable by adding:
    # 'newsletters': {'run': job_newsletters, 'due': due_daily},
    'tag_content': {'run': job_tag_content, 'due': due_tagging},
    'paper_hygiene': {'run': job_paper_hygiene, 'due': due_daily},
    'paper_feed': {'run': job_paper_feed, 'due': due_daily},
    'rag_update': {'run': job_rag_update, 'due': due_daily},
    'topic_map': {'run': job_topic_map, 'due': due_weekly},
    'weekly_digest': {'run': job_weekly_digest, 'due': due_weekly},
    'backup': {'run': job_backup, 'due': due_weekly},
}


def run_job(name: str) -> bool:
    from app.repositories import scheduled_jobs
    job = JOBS[name]
    started = datetime.now(timezone.utc)
    logger.info(f"Running job {name}")
    try:
        summary = job['run']()
        scheduled_jobs.record_job_run(name, True, summary=summary, started_at=started)
        logger.info(f"Job {name} done: {summary}")
        return True
    except Exception as e:
        scheduled_jobs.record_job_run(name, False, error=f'{type(e).__name__}: {e}'[:500], started_at=started)
        logger.exception(f"Job {name} failed")
        return False


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is not None and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)  # pymongo returns naive UTC
    return dt


def due_jobs(now: Optional[datetime] = None, get_state: Optional[Callable] = None):
    if get_state is None:
        from app.repositories.scheduled_jobs import get_job_state as get_state
    now = now or datetime.now(timezone.utc)
    due = []
    for name, job in JOBS.items():
        state = get_state(name) or {}
        last_run = _aware(state.get('last_run'))
        if state.get('last_ok') is False and last_run and now - last_run < FAILURE_BACKOFF:
            continue          # 2026-10-06: a failing rag_update was retried 10x and blocked all jobs for 6 h
        if job['due'](_aware(state.get('last_success')), now):
            due.append(name)
    return due


def run_due_jobs() -> None:
    for name in due_jobs():
        run_job(name)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true', help='run due jobs once and exit')
    parser.add_argument('--run', choices=sorted(JOBS), help='run one job now and exit')
    args = parser.parse_args(argv)

    if args.run:
        return 0 if run_job(args.run) else 1
    if args.once:
        run_due_jobs()
        return 0

    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: (logger.info("Shutdown signal received"), stop.set()))
    logger.info(f"Scheduler started; jobs: {', '.join(JOBS)}")
    while not stop.is_set():
        try:
            run_due_jobs()
        except Exception:
            logger.exception("Scheduler cycle failed")
        stop.wait(CHECK_EVERY_SECONDS)
    logger.info("Scheduler stopped")
    return 0


if __name__ == '__main__':
    sys.exit(main())
