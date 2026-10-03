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
