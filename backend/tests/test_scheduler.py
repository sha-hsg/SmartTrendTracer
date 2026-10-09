"""stt_scheduler due rules (catch-up scheduling, 2026-10)."""
from datetime import datetime, timedelta, timezone

import stt_scheduler as sch

NOW = datetime(2026, 10, 7, 9, 0, tzinfo=timezone.utc)   # Wednesday


def test_daily_due_after_20h():
    assert sch.due_daily(None, NOW)
    assert not sch.due_daily(NOW - timedelta(hours=19), NOW)
    assert sch.due_daily(NOW - timedelta(hours=21), NOW)


def test_weekly_due_once_per_week_and_catches_up():
    monday = sch.start_of_week(NOW)
    assert monday.weekday() == 0 and monday.hour == 0
    assert sch.due_weekly(None, NOW)
    # last run in the previous week -> due now (Mac was off on Monday: catch up Wednesday)
    assert sch.due_weekly(monday - timedelta(hours=1), NOW)
    # already ran this week -> not due again
    assert not sch.due_weekly(monday + timedelta(hours=3), NOW)


def test_due_jobs_uses_stored_state(monkeypatch):
    monkeypatch.setattr(sch, 'JOBS', {
        'fresh': {'run': None, 'due': sch.due_daily},
        'stale': {'run': None, 'due': sch.due_daily},
        'never': {'run': None, 'due': sch.due_daily},
    })
    state = {'fresh': {'last_success': (NOW - timedelta(hours=1)).replace(tzinfo=None)},  # naive like pymongo
             'stale': {'last_success': NOW - timedelta(days=2)}}
    assert sch.due_jobs(NOW, get_state=state.get) == ['stale', 'never']


def test_failed_job_is_recorded_and_not_raised(monkeypatch):
    recorded = []
    from app.repositories import scheduled_jobs
    monkeypatch.setattr(scheduled_jobs, 'record_job_run', lambda name, ok, **kw: recorded.append((name, ok, kw.get('error'))))

    def boom():
        raise RuntimeError('backend down')
    monkeypatch.setattr(sch, 'JOBS', {'x': {'run': boom, 'due': sch.due_daily}})
    assert sch.run_job('x') is False
    assert recorded == [('x', False, 'RuntimeError: backend down')]


def test_tagging_runs_every_six_hours():
    assert sch.due_tagging(None, NOW)
    assert not sch.due_tagging(NOW - timedelta(hours=5), NOW)
    assert sch.due_tagging(NOW - timedelta(hours=6), NOW)


def test_tagging_runs_first(monkeypatch):
    assert list(sch.JOBS)[:1] == ['tag_tweets']
    assert list(sch.JOBS).index('rag_update') < list(sch.JOBS).index('topic_map') < list(sch.JOBS).index('weekly_digest')


class _Resp:
    def __init__(self, code, body):
        self.status_code, self._body = code, body

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


def test_tag_job_polls_until_done(monkeypatch):
    import httpx
    calls = []
    monkeypatch.setattr(httpx, 'post', lambda url, **kw: calls.append(url) or _Resp(200, {'task_id': 't1', 'total': 3}))
    states = iter([{'status': 'running'}, {'status': 'completed', 'total': 3, 'processed': 3,
                                           'new_tags_count': 9, 'error_count': 0}])
    monkeypatch.setattr(httpx, 'get', lambda url, **kw: _Resp(200, next(states)))
    assert sch.job_tag_tweets(poll_seconds=0) == {'total': 3, 'processed': 3, 'new_tags_count': 9, 'error_count': 0}
    assert calls[0].endswith('/api/tweets/batch-annotate-all')


def test_tag_job_skips_when_a_ui_run_is_active(monkeypatch):
    import httpx
    monkeypatch.setattr(httpx, 'post', lambda url, **kw: _Resp(409, {}))
    assert sch.job_tag_tweets(poll_seconds=0) == {'skipped': 'annotate-all already running'}
