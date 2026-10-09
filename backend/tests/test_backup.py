"""Weekly database backup (2026-10 fitness review: there was no backup at all)."""
import pytest

from app.services import backup_service as bs


def fake_dump(tmp_path, ok=True):
    """A stand-in mongodump that writes the --archive file (or fails)."""
    script = tmp_path / 'mongodump'
    body = ('for a in "$@"; do case "$a" in --archive=*) echo data > "${a#--archive=}";; esac; done'
            if ok else 'echo boom >&2; exit 3')
    script.write_text('#!/bin/sh\n' + body + '\n')
    script.chmod(0o755)
    return str(script)


def test_backup_writes_archive_and_keeps_newest(tmp_path):
    target = tmp_path / 'b'
    target.mkdir()
    for i in range(3):
        (target / f'{bs.PREFIX}2026010{i}_000000{bs.SUFFIX}').write_text('old')
    result = bs.run_backup(str(target), keep=2, dump_cmd=fake_dump(tmp_path))
    names = sorted(p.name for p in target.iterdir())
    assert len(names) == 2 and result['archive'].endswith(bs.SUFFIX)
    assert names[-1] == result['archive'].rsplit('/', 1)[1]
    assert not any(n.endswith('.partial') for n in names)


def test_failed_dump_raises_and_leaves_no_partial_file(tmp_path):
    target = tmp_path / 'b'
    with pytest.raises(RuntimeError, match='mongodump failed'):
        bs.run_backup(str(target), keep=2, dump_cmd=fake_dump(tmp_path, ok=False))
    assert list(target.iterdir()) == []
