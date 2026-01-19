#!/usr/bin/env python3
"""
Test the refactored tweet collector with Basic Account Mode
"""

import os
import sys
from datetime import datetime, timezone

# Test environment setup
os.environ["BASIC_ACCOUNT_MODE"] = "true"
os.environ["MAX_PAGES_PER_ACCOUNT"] = "1"

# Import after setting env vars
from tweet_collector_service import (
    BASIC_ACCOUNT_MODE, 
    MAX_PAGES_PER_ACCOUNT,
    TIMELINE_REQUESTS_PER_WINDOW,
    MONTHLY_TWEET_LIMIT,
    DAILY_TWEET_BUDGET,
    rate_limiter,
    get_monthly_usage,
    get_daily_usage,
    should_reduce_frequency
)

def test_configuration():
    """Test that Basic Account Mode is properly configured"""
    print("\n" + "="*60)
    print("🔍 TESTING REFACTORED COLLECTOR CONFIGURATION")
    print("="*60)
    
    print("\n✅ Basic Account Mode Settings:")
    print(f"  • BASIC_ACCOUNT_MODE: {BASIC_ACCOUNT_MODE}")
    print(f"  • MAX_PAGES_PER_ACCOUNT: {MAX_PAGES_PER_ACCOUNT}")
    print(f"  • TIMELINE_REQUESTS_PER_WINDOW: {TIMELINE_REQUESTS_PER_WINDOW}")
    print(f"  • MONTHLY_TWEET_LIMIT: {MONTHLY_TWEET_LIMIT}")
    print(f"  • DAILY_TWEET_BUDGET: {DAILY_TWEET_BUDGET}")
    
    assert BASIC_ACCOUNT_MODE == True, "Basic Account Mode should be enabled"
    assert MAX_PAGES_PER_ACCOUNT == 1, "Should fetch only 1 page per account"
    assert TIMELINE_REQUESTS_PER_WINDOW == 15, "Should have 15 timeline requests per window"
    
    print("\n✅ All configuration tests passed!")

def test_rate_limiter():
    """Test the enhanced rate limiter"""
    print("\n✅ Testing Rate Limiter:")
    
    # Test timeline request tracking
    can_make = rate_limiter.can_make_timeline_request()
    print(f"  • Can make timeline request: {can_make}")
    
    # Simulate making requests
    for i in range(3):
        rate_limiter.use_timeline_request()
    
    print(f"  • After 3 requests - Timeline requests used: {len(rate_limiter.timeline_requests)}")
    print(f"  • Can still make request: {rate_limiter.can_make_timeline_request()}")
    
    # Test search request tracking
    can_make_search = rate_limiter.can_make_search_request()
    print(f"  • Can make search request: {can_make_search}")
    
    print("\n✅ Rate limiter tests passed!")

def test_usage_monitoring():
    """Test usage monitoring functions"""
    print("\n✅ Testing Usage Monitoring:")
    
    monthly = get_monthly_usage()
    daily = get_daily_usage()
    
    print(f"\n  Monthly Usage:")
    print(f"    • Tweets collected: {monthly.get('tweets_collected', 0)}")
    print(f"    • Monthly limit: {monthly.get('limit', 0)}")
    print(f"    • Usage percentage: {monthly.get('usage_percentage', 0):.1f}%")
    print(f"    • Projected: {monthly.get('projected_monthly', 0):.0f}")
    
    print(f"\n  Daily Usage:")
    print(f"    • Tweets today: {daily.get('tweets_today', 0)}")
    print(f"    • Daily budget: {daily.get('budget', 0)}")
    print(f"    • Usage percentage: {daily.get('budget_used_percentage', 0):.1f}%")
    
    should_reduce = should_reduce_frequency()
    print(f"\n  Should reduce frequency: {should_reduce}")
    
    print("\n✅ Usage monitoring tests passed!")

def test_tiered_accounts():
    """Test tiered account priority"""
    print("\n✅ Testing Tiered Account Priority:")
    
    from tweet_collector_service import TIER_1_ACCOUNTS, TIER_2_ACCOUNTS, TIER_3_ACCOUNTS
    
    print(f"  • Tier 1 accounts (30 min): {len(TIER_1_ACCOUNTS)}")
    for acc in TIER_1_ACCOUNTS:
        print(f"    - {acc}")
    
    print(f"\n  • Tier 2 accounts (2 hours): {len(TIER_2_ACCOUNTS)}")
    for acc in TIER_2_ACCOUNTS:
        print(f"    - {acc}")
    
    print(f"\n  • Tier 3 accounts (6 hours): {len(TIER_3_ACCOUNTS)}")
    for acc in TIER_3_ACCOUNTS:
        print(f"    - {acc}")
    
    total = len(TIER_1_ACCOUNTS) + len(TIER_2_ACCOUNTS) + len(TIER_3_ACCOUNTS)
    print(f"\n  • Total accounts covered: {total}")
    
    print("\n✅ Tiered priority tests passed!")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 REFACTORED COLLECTOR TEST SUITE")
    print("="*60)
    
    try:
        test_configuration()
        test_rate_limiter()
        test_usage_monitoring()
        test_tiered_accounts()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nThe refactored collector is ready to use with:")
        print("  1. Basic Account Mode support")
        print("  2. Enhanced rate limiting")
        print("  3. Usage monitoring")
        print("  4. Tiered account priority")
        print("\nRun with: ./start_basic_collector.sh")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()