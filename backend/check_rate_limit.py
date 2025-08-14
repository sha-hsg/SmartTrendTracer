#!/usr/bin/env python3
"""
Check current rate limit status
"""
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.rate_limiter import get_rate_limiter

def check_rate_limit():
    print("🔍 RATE LIMIT STATUS")
    print("=" * 50)
    
    rate_limiter = get_rate_limiter()
    
    print(f"\n📊 Current Status:")
    print(f"   • Request count: {len(rate_limiter.requests_made)}/{rate_limiter.max_requests}")
    print(f"   • Window: {rate_limiter.window_minutes} minutes")
    
    if rate_limiter.requests_made:
        oldest_request = min(rate_limiter.requests_made)
        newest_request = max(rate_limiter.requests_made)
        window_end = oldest_request + timedelta(minutes=rate_limiter.window_minutes)
        window_remaining = (window_end - datetime.now(timezone.utc)).total_seconds()
        print(f"   • Oldest request: {oldest_request.strftime('%H:%M:%S UTC')}")
        print(f"   • Newest request: {newest_request.strftime('%H:%M:%S UTC')}")
        if window_remaining > 0:
            print(f"   • Window resets in: {window_remaining:.0f} seconds ({window_remaining/60:.1f} minutes)")
    else:
        print("   • No requests in current window")
    
    if rate_limiter.can_make_request():
        print(f"\n✅ Can make requests: {rate_limiter.max_requests - len(rate_limiter.requests_made)} remaining")
    else:
        print(f"\n⚠️  RATE LIMITED")
        if rate_limiter.backoff_until:
            wait_time = (rate_limiter.backoff_until - datetime.now(timezone.utc)).total_seconds()
            print(f"   Backoff until: {rate_limiter.backoff_until.strftime('%H:%M:%S UTC')}")
            print(f"   Must wait: {wait_time:.0f} seconds ({wait_time/60:.1f} minutes)")
        else:
            # Regular rate limit
            oldest_request = min(rate_limiter.requests_made)
            window_end = oldest_request + timedelta(minutes=rate_limiter.window_minutes)
            wait_time = (window_end - datetime.now(timezone.utc)).total_seconds()
            print(f"   Window full: {len(rate_limiter.requests_made)}/{rate_limiter.max_requests} requests")
            print(f"   Must wait: {wait_time:.0f} seconds ({wait_time/60:.1f} minutes)")
            print(f"   Will reset at: {window_end.strftime('%H:%M:%S UTC')}")
    
    # Check for backoff
    if rate_limiter.last_429_time:
        time_since_429 = (datetime.now(timezone.utc) - rate_limiter.last_429_time).total_seconds()
        print(f"\n🚫 Last 429 Error:")
        print(f"   Time: {rate_limiter.last_429_time.strftime('%H:%M:%S UTC')}")
        print(f"   {time_since_429:.0f} seconds ago ({time_since_429/60:.1f} minutes)")
        
        if rate_limiter.backoff_until and rate_limiter.backoff_until > datetime.now(timezone.utc):
            backoff_remaining = (rate_limiter.backoff_until - datetime.now(timezone.utc)).total_seconds()
            print(f"   Backoff remaining: {backoff_remaining:.0f} seconds")
    
    print("\n" + "=" * 50)
    print("💡 Tips:")
    print("   • Twitter Basic tier: 10 requests per 15 minutes")
    print("   • We monitor 7 accounts (7 requests minimum)")
    print("   • Best practice: Wait for full window reset")
    print("   • Or use: python wait_and_collect.py")

if __name__ == "__main__":
    check_rate_limit()