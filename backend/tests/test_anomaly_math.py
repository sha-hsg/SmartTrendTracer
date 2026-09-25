"""Regression tests for anomaly/trend math (2026-08 functional kaizen).

Covers: baseline window exclusion of the test window, Poisson-informed std
floor (replacing the scale-dependent 1.0 floor), exact window_days bucket
count, and the zero-baseline velocity ranking fix.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.repositories.analytics.concept_helpers import calculate_tag_velocity
from app.services.anomaly_detection import AnomalyDetector


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


def _detector_with_counts(day_counts_by_key):
    """AnomalyDetector with _get_daily_counts stubbed; no DB access."""
    det = AnomalyDetector.__new__(AnomalyDetector)

    def fake_daily_counts(concept_id, start_date, end_date):
        result = {}
        current = start_date
        while current < end_date:
            key = current.strftime('%Y-%m-%d')
            if key in day_counts_by_key:
                result[key] = day_counts_by_key[key]
            current += timedelta(days=1)
        return result

    det._get_daily_counts = fake_daily_counts
    return det


class TestBaselineStats:
    def test_exact_window_bucket_count(self):
        det = _detector_with_counts({})
        stats = det.get_baseline_stats('x', window_days=30,
                                       end_date=datetime(2026, 8, 16, 14, 30, tzinfo=timezone.utc))
        assert len(stats['daily_counts']) == 30  # was 31 (off-by-one)

    def test_missing_days_count_as_zero(self):
        end = datetime(2026, 8, 16, tzinfo=timezone.utc)
        counts = {(end - timedelta(days=d)).strftime('%Y-%m-%d'): 5 for d in (1, 4)}
        det = _detector_with_counts(counts)
        stats = det.get_baseline_stats('x', window_days=4, end_date=end)
        assert stats['total'] == 10
        assert stats['mean'] == pytest.approx(2.5)
        assert stats['active_days'] == 2

    def test_poisson_floor_replaces_flat_one(self):
        # A perfectly steady 1000/day series: old floor gave std=1.0, so
        # +5/day scored z=5 (false alarm); Poisson floor gives sqrt(1000)
        end = datetime(2026, 8, 16, tzinfo=timezone.utc)
        counts = {(end - timedelta(days=d)).strftime('%Y-%m-%d'): 1000 for d in range(1, 31)}
        det = _detector_with_counts(counts)
        stats = det.get_baseline_stats('x', window_days=30, end_date=end)
        assert stats['std_dev'] == pytest.approx(1000 ** 0.5)
        z = det.calculate_z_score(1005, stats['mean'], stats['std_dev'])
        assert z < 1.0  # +5/day on a 1000/day concept is noise, not an anomaly

    def test_zero_baseline_gets_small_floor(self):
        det = _detector_with_counts({})
        stats = det.get_baseline_stats('x', window_days=30,
                                       end_date=datetime(2026, 8, 16, tzinfo=timezone.utc))
        assert stats['std_dev'] == 0.5


class TestDetectSpikes:
    def test_long_spike_not_suppressed_by_own_baseline(self):
        # 24 quiet days then 7 days of 10/day: old code baselined over all 31
        # days (spike included) -> z=1.85, no alarm. With the window excluded
        # the baseline is silent and the spike must fire.
        now = datetime.now(timezone.utc)
        counts = {}
        for d in range(0, 8):  # last 7 days incl. today
            counts[(now - timedelta(days=d)).strftime('%Y-%m-%d')] = 10
        det = _detector_with_counts(counts)
        spike = det.detect_spikes('x', threshold=2.5, recent_hours=168)
        assert spike is not None
        assert spike['z_score'] >= 2.5

    def test_steady_activity_is_not_a_spike(self):
        now = datetime.now(timezone.utc)
        counts = {(now - timedelta(days=d)).strftime('%Y-%m-%d'): 5 for d in range(0, 40)}
        det = _detector_with_counts(counts)
        assert det.detect_spikes('x', threshold=2.5, recent_hours=48) is None
