"""
Database backup: mongodump of the `smarttrendtracer` database as one gzip
archive per run into settings.backup_dir (default ~/Backups/SmartTrendTracer,
override with STT_BACKUP_DIR — ideally a path on another disk). The newest
settings.backup_keep archives are kept. Run weekly by stt_scheduler.py (job
"backup"); restore with
    mongorestore --gzip --archive=<file> --nsInclude='smarttrendtracer.*' --drop
"""
from __future__ import annotations

import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from app.config import settings

PREFIX = 'smarttrendtracer_'
SUFFIX = '.archive.gz'


def run_backup(backup_dir: str | None = None, keep: int | None = None, dump_cmd: str | None = None) -> Dict[str, Any]:
    target = Path(backup_dir or settings.backup_dir).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    mongodump = dump_cmd or shutil.which('mongodump')
    if not mongodump:
        raise RuntimeError('mongodump not found (brew install mongodb-database-tools)')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    archive = target / f'{PREFIX}{stamp}{SUFFIX}'
    partial = archive.with_name(archive.name + '.partial')
    result = subprocess.run(
        [mongodump, f'--uri={settings.mongodb_uri}', f'--db={settings.mongodb_db}',
         f'--archive={partial}', '--gzip', '--quiet'],
        capture_output=True, text=True, timeout=1800)
    if result.returncode != 0 or not partial.exists() or partial.stat().st_size == 0:
        partial.unlink(missing_ok=True)
        raise RuntimeError(f'mongodump failed ({result.returncode}): {result.stderr.strip()[:300]}')
    partial.rename(archive)                      # only complete archives count
    archives = sorted(target.glob(f'{PREFIX}*{SUFFIX}'))
    removed = []
    for old in archives[:-(keep or settings.backup_keep)]:
        old.unlink()
        removed.append(old.name)
    return {'archive': str(archive), 'size_mb': round(archive.stat().st_size / 1e6, 1),
            'kept': len(archives) - len(removed), 'removed': removed}
