"""RAG embedding wiring (2026-10-03 rebuild on gemini-embedding-001)."""
import numpy as np
import pytest

from app.services.rag import index_manager as im


def test_rate_limit_retry_recovers(monkeypatch):
    monkeypatch.setattr(im.time, 'sleep', lambda s: None)
    calls = {'n': 0}

    def flaky():
        calls['n'] += 1
        if calls['n'] < 3:
            raise RuntimeError('429 You exceeded your current quota')
        return 'ok'

    assert im._with_rate_limit_retry(flaky) == 'ok'
    assert calls['n'] == 3


def test_non_rate_limit_errors_are_not_retried(monkeypatch):
    monkeypatch.setattr(im.time, 'sleep', lambda s: None)
    calls = {'n': 0}

    def broken():
        calls['n'] += 1
        raise RuntimeError('404 model not found')

    with pytest.raises(RuntimeError):
        im._with_rate_limit_retry(broken)
    assert calls['n'] == 1


def test_normalize_unit_length():
    assert np.isclose(np.linalg.norm(im._normalize(np.array([3.0, 4.0]))), 1.0)


def test_configured_primary_model_matches_dimension():
    model, dim = im._embedding_model_and_dimension(True)
    assert model == 'models/gemini-embedding-001' and dim == 768
