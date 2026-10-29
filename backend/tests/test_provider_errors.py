"""Empty provider credits fail fast and visibly (2026-10-29: a week of silent no-tagging)."""
import pytest

from app.services.provider_errors import is_billing_error, is_rate_limit

GEMINI = ("429 Your prepayment credits are depleted. Please go to AI Studio at "
          "https://ai.studio/projects to manage your project and billing.")


def test_billing_vs_rate_limit():
    assert is_billing_error(GEMINI) and not is_rate_limit(GEMINI)
    assert is_rate_limit('429 Too Many Requests') and not is_billing_error('429 Too Many Requests')
    assert is_billing_error('Error code: 429 - insufficient_quota')


def test_embedding_retry_skips_billing_errors(monkeypatch):
    from app.services.rag import index_manager
    monkeypatch.setattr(index_manager.time, 'sleep', lambda s: None)
    calls = []

    def fail():
        calls.append(1)
        raise RuntimeError(GEMINI)
    with pytest.raises(RuntimeError):
        index_manager._with_rate_limit_retry(fail)
    assert len(calls) == 1                          # no 62 s of pointless backoff

    calls.clear()

    def limited():
        calls.append(1)
        raise RuntimeError('429 Too Many Requests')
    with pytest.raises(RuntimeError):
        index_manager._with_rate_limit_retry(limited, attempts=3)
    assert len(calls) == 3


def test_tagging_stops_and_fails_when_the_model_is_unreachable(monkeypatch):
    from app.services import concept_tagging as ct
    monkeypatch.setattr(ct.repo, 'untagged_ids', lambda t, limit=None: [str(i) for i in range(50)])
    calls = []
    monkeypatch.setattr(ct, 'tag_item', lambda t, cid, llm=None: calls.append(cid) or {'error': f'llm_failed: {GEMINI}'})
    with pytest.raises(ct.TaggingFailed, match='credits are depleted'):
        ct.tag_untagged('tweet')
    assert len(calls) == ct.MAX_CONSECUTIVE_ERRORS


def test_tagging_tolerates_isolated_errors(monkeypatch):
    from app.services import concept_tagging as ct
    monkeypatch.setattr(ct.repo, 'untagged_ids', lambda t, limit=None: [str(i) for i in range(10)])
    monkeypatch.setattr(ct, 'tag_item', lambda t, cid, llm=None:
                        {'error': 'llm_failed: bad json'} if cid in ('3', '7') else {'new': ['X']})
    stats = ct.tag_untagged('tweet')
    assert stats['tagged'] == 8 and stats['errors'] == 2


def test_gemini_per_minute_quota_stays_retryable():
    msg = '429 You exceeded your current quota, please check your plan and billing details.'
    assert is_rate_limit(msg) and not is_billing_error(msg)
