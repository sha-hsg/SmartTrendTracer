"""Regression tests for anomaly/trend math (2026-08 functional kaizen).

Covers the zero-baseline velocity ranking fix of calculate_tag_velocity (still
used by the substack/user trend views). The dashboard's anomaly math moved to
app.services.trend_core (tests/test_trend_core.py).
"""

from app.repositories.analytics.concept_helpers import calculate_tag_velocity


class TestVelocity:
    def test_normal_growth(self):
        assert calculate_tag_velocity(3, 1) == 200.0

    def test_decline(self):
        assert calculate_tag_velocity(1, 4) == -75.0

    def test_zero_baseline_singleton_is_not_hot(self):
        # 0 -> 1 previously returned 100.0 ("hot" threshold is > 50)
        assert calculate_tag_velocity(1, 0) == 0.0
        assert calculate_tag_velocity(2, 0) == 0.0

    def test_zero_baseline_breakout_outranks_small_growth(self):
        # 0 -> 400 previously returned 100.0 and sorted BELOW 1 -> 3 (+200%)
        assert calculate_tag_velocity(400, 0) > calculate_tag_velocity(3, 1)

    def test_zero_to_zero(self):
        assert calculate_tag_velocity(0, 0) == 0.0
