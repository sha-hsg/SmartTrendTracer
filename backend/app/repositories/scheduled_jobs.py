"""State of the periodic jobs run by stt_scheduler.py (collection scheduled_jobs)."""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.database.mongodb import get_database

db = get_database()


def get_job_state(name: str) -> Optional[Dict[str, Any]]:
    return db.scheduled_jobs.find_one({'_id': name})


def list_job_states():
    return list(db.scheduled_jobs.find().sort('_id', 1))


def record_job_run(name: str, ok: bool, summary: Any = None, error: Optional[str] = None,
                   started_at: Optional[datetime] = None) -> None:
    """Store the outcome of one run; last_success only moves on success."""
    now = datetime.now(timezone.utc)
    fields = {'last_run': now, 'last_started': started_at or now, 'last_ok': ok,
              'last_summary': summary, 'last_error': error}
    if ok:
        fields['last_success'] = now
    db.scheduled_jobs.update_one({'_id': name}, {'$set': fields, '$inc': {'runs': 1}}, upsert=True)
