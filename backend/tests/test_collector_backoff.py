"""Regression test for the X-API credits-depleted (402) backoff classification.

Sep 2026: depleted credits produced 12k log errors and ~2k pointless requests
per day because every account was retried 3x every 15 minutes. The collector
now aborts the cycle on the first 402 and backs off for CREDITS_BACKOFF_SECONDS.
"""

import pytest

try:
    from tweet_collector_service import is_credits_depleted_error, CREDITS_BACKOFF_SECONDS
    _IMPORTED = True
except Exception:
    _IMPORTED = False

pytestmark = pytest.mark.skipif(not _IMPORTED,
                                reason="collector module needs local MongoDB to import")


class TestCreditsDepletedClassification:
    def test_real_error_string(self):
        # Exact shape seen in production logs
        assert is_credits_depleted_error("402 Payment Required\ncredits depleted")

    def test_status_code_only(self):
        assert is_credits_depleted_error("Request failed: 402")

    def test_message_only(self):
        assert is_credits_depleted_error("Credits Depleted")

    def test_other_errors_not_matched(self):
        assert not is_credits_depleted_error("429 Too Many Requests")
        assert not is_credits_depleted_error("401 Unauthorized")
        assert not is_credits_depleted_error("403 Forbidden")
        assert not is_credits_depleted_error("Connection reset by peer")

    def test_backoff_is_longer_than_normal_interval(self):
        from tweet_collector_service import COLLECTION_INTERVAL_SECONDS
        assert CREDITS_BACKOFF_SECONDS > COLLECTION_INTERVAL_SECONDS
