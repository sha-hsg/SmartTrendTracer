"""
Period and date helper functions for analytics.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple


def parse_period_to_days(period: str) -> int:
    """
    Convert period string to number of days.

    Args:
        period: Period string like 'today', 'week', '30days', 'all'

    Returns:
        Number of days as integer
    """
    period_mapping = {
        "today": 1,
        "3days": 3,
        "week": 7,
        "7days": 7,
        "14days": 14,
        "month": 30,
        "30days": 30,
        "60days": 60,
        "90days": 90,
        "120days": 120,
        "200days": 200,
        "365days": 365,
        "all": 3650,  # ~10 years - effectively all data
    }
    return period_mapping.get(period, 7)


def get_date_range(days: int, end_date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    """
    Calculate date range from number of days.

    Args:
        days: Number of days to look back
        end_date: End date (defaults to now)

    Returns:
        Tuple of (start_date, end_date)
    """
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def get_previous_period_range(start_date: datetime, days: int) -> Tuple[datetime, datetime]:
    """
    Calculate the previous period date range for comparison.

    Args:
        start_date: Start of current period
        days: Number of days in period

    Returns:
        Tuple of (previous_start, previous_end)
    """
    previous_end = start_date
    previous_start = previous_end - timedelta(days=days)
    return previous_start, previous_end
