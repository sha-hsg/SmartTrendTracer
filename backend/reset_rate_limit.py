#!/usr/bin/env python3
"""
Reset rate limit tracking if you're stuck
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.rate_limiter import get_rate_limiter
from datetime import datetime, timezone

def reset_rate_limits():
    print("🔄 Resetting Rate Limit Tracker")
    print("=" * 40)
    
    rate_limiter = get_rate_limiter()
    
    # Show current state
    print("\nCurrent state:")
    print(f"  Requests in window: {len(rate_limiter.requests_made)}")
    print(f"  Max requests: {rate_limiter.max_requests}")
    print(f"  Window: {rate_limiter.window_minutes} minutes")
    
    if rate_limiter.backoff_until:
        if rate_limiter.backoff_until > datetime.now(timezone.utc):
            remaining = (rate_limiter.backoff_until - datetime.now(timezone.utc)).total_seconds()
            print(f"  ⚠️ Currently in backoff for {remaining:.0f} seconds")
        else:
            print(f"  Backoff expired")
    
    # Reset
    rate_limiter.reset()
    print("\n✅ Rate limiter reset!")
    print("   You can now make requests again")
    print("\n⚠️  Note: This doesn't reset Twitter's actual rate limit")
    print("   If you're still getting 429 errors, you need to wait")
    print("   Twitter Basic tier: 10 requests per 15 minutes")

if __name__ == "__main__":
    reset_rate_limits()