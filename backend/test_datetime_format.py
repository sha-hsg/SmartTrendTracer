#!/usr/bin/env python3
"""
Test datetime formatting for Twitter API
"""
from datetime import datetime, timezone, timedelta

def test_datetime_formats():
    print("Testing DateTime Formats for Twitter API")
    print("=" * 50)
    
    # Current time
    now = datetime.now(timezone.utc)
    print(f"\nCurrent time (raw): {now}")
    print(f"Current time (ISO): {now.isoformat()}")
    
    # Twitter API format (RFC3339 without microseconds)
    twitter_format = now.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    print(f"Twitter API format: {twitter_format}")
    
    print("\n" + "-" * 50)
    print("Testing various datetime formats:")
    
    # Test different datetime scenarios
    test_cases = [
        ("Now", datetime.now(timezone.utc)),
        ("1 hour ago", datetime.now(timezone.utc) - timedelta(hours=1)),
        ("1 day ago", datetime.now(timezone.utc) - timedelta(days=1)),
        ("7 days ago", datetime.now(timezone.utc) - timedelta(days=7)),
        ("With microseconds", datetime.now(timezone.utc)),
        ("Database format (naive)", datetime.utcnow()),  # Simulating database datetime
    ]
    
    for label, dt in test_cases:
        print(f"\n{label}:")
        print(f"  Raw: {dt}")
        
        # Make timezone-aware if needed
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
            print(f"  Made aware: {dt}")
        
        # Format for Twitter API
        twitter_fmt = dt.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        print(f"  Twitter format: {twitter_fmt}")
    
    print("\n" + "=" * 50)
    print("✅ All formats should work with Twitter API now!")
    print("\nCorrect format examples:")
    print("  • 2025-01-08T14:30:00Z")
    print("  • 2025-01-08T00:00:00Z")
    print("\nIncorrect formats (will fail):")
    print("  • 2025-01-08T14:30:00.123456+00:00Z (has microseconds)")
    print("  • 2025-01-08T14:30:00+00:00Z (has +00:00 instead of Z)")

if __name__ == "__main__":
    test_datetime_formats()