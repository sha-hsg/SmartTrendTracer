#!/usr/bin/env python3
"""
Compare Twitter API vs Twscrape collectors
"""
import sys
import os
from datetime import datetime, timezone, timedelta
from tabulate import tabulate

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.rate_limiter import get_rate_limiter
from app.config import ACCOUNTS_TO_FOLLOW

def compare_collectors():
    print("🔍 COLLECTOR COMPARISON: Twitter API vs Twscrape")
    print("=" * 70)
    
    # Create comparison table
    comparison = [
        ["Feature", "Twitter API (Current)", "Twscrape (Alternative)"],
        ["="*20, "="*25, "="*25],
        
        # Rate Limits
        ["Rate Limits", 
         "❌ 10 requests/15 min", 
         "✅ No limits!"],
        
        ["Accounts/hour", 
         "~40 (with waiting)", 
         "Unlimited"],
        
        ["Collection Speed", 
         "Slow (rate limited)", 
         "Fast (parallel possible)"],
        
        # Authentication
        ["Authentication", 
         "API Bearer Token", 
         "Login or Guest Token"],
        
        ["Setup Complexity", 
         "Need Twitter Dev Account", 
         "Just need any account"],
        
        # Features
        ["Search Tweets", 
         "❌ Not in Basic tier", 
         "✅ Full search"],
        
        ["Get Replies", 
         "❌ Limited", 
         "✅ All replies"],
        
        ["Historical Data", 
         "7 days max", 
         "Much older tweets"],
        
        ["Media Access", 
         "✅ Direct URLs", 
         "✅ Direct URLs"],
        
        # Reliability
        ["Reliability", 
         "✅ Very stable", 
         "⚠️  Can break"],
        
        ["ToS Compliance", 
         "✅ Official API", 
         "❌ Violates ToS"],
        
        ["Account Risk", 
         "✅ No risk", 
         "⚠️  Suspension risk"],
        
        # Cost
        ["Cost", 
         "Free (Basic tier)", 
         "Free"],
        
        ["Maintenance", 
         "Low (stable API)", 
         "High (updates needed)"],
    ]
    
    # Print comparison
    for row in comparison:
        if row[0].startswith("="):
            print(f"{row[0]} {row[1]} {row[2]}")
        else:
            print(f"{row[0]:20} {row[1]:25} {row[2]:25}")
    
    # Current rate limit status
    print("\n" + "=" * 70)
    print("📊 CURRENT STATUS")
    print("=" * 70)
    
    rate_limiter = get_rate_limiter()
    
    print(f"\n🚀 Twitter API Status:")
    print(f"   • Requests used: {len(rate_limiter.requests_made)}/10")
    print(f"   • Accounts to track: {len(ACCOUNTS_TO_FOLLOW)}")
    
    if rate_limiter.can_make_request():
        print(f"   • Status: ✅ Can collect")
    else:
        print(f"   • Status: ❌ Rate limited")
    
    # Calculate collection times
    print(f"\n⏱️  Time Estimates:")
    
    # API collection time
    if len(ACCOUNTS_TO_FOLLOW) <= 10:
        api_time = "Immediate (if not rate limited)"
    else:
        batches = (len(ACCOUNTS_TO_FOLLOW) + 9) // 10
        api_time = f"{(batches - 1) * 15} minutes (with waiting)"
    
    print(f"   • Twitter API: {api_time}")
    print(f"   • Twscrape: < 1 minute (no limits!)")
    
    # Recommendations
    print("\n" + "=" * 70)
    print("💡 RECOMMENDATIONS")
    print("=" * 70)
    
    print("\n🎯 When to use Twitter API:")
    print("   • Production systems")
    print("   • When reliability is critical")
    print("   • Commercial applications")
    print("   • When you need guaranteed uptime")
    
    print("\n🎯 When to use Twscrape:")
    print("   • Personal projects")
    print("   • Research/analysis")
    print("   • When you need lots of data fast")
    print("   • Historical data collection")
    print("   • Search functionality needed")
    
    print("\n⚠️  HYBRID APPROACH (Best of both):")
    print("   1. Use API as primary (reliable)")
    print("   2. Fall back to twscrape when rate limited")
    print("   3. Use twscrape for search/historical data")
    print("   4. Monitor both for failures")
    
    print("\n" + "=" * 70)
    print("🔧 SETUP COMMANDS")
    print("=" * 70)
    
    print("\n🔵 Twitter API (current):")
    print("   python wait_and_collect.py     # Respects rate limits")
    print("   python monitor_collection.py   # Check status")
    
    print("\n🔴 Twscrape (new):")
    print("   python setup_twscrape.py       # One-time setup")
    print("   python collect_twscrape.py     # Collect without limits")
    
    print("\n🔶 Hybrid:")
    print("   python smart_collect.py        # Coming soon...")

if __name__ == "__main__":
    compare_collectors()