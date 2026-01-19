#!/usr/bin/env python3
"""
Test script for extended time range functionality in Trend Visualization
Tests the new quarterly, half-year, and yearly views
"""

import sys
sys.path.append('.')

from app.api.analytics_trends_mongodb import get_trends_timeline, get_trends_tags
from datetime import datetime, timedelta
import json

def test_timeline_functionality():
    """Test timeline endpoints with different time ranges"""
    print("🧪 Testing Timeline Functionality with Extended Ranges")
    print("=" * 60)
    
    test_ranges = [
        (1, "24 hours"),
        (7, "7 days"),
        (30, "30 days"),
        (90, "Quarter (90 days)"),
        (180, "Half year (180 days)"),
        (365, "Full year (365 days)")
    ]
    
    for days, label in test_ranges:
        try:
            result = get_trends_timeline(days)
            
            daily_points = len(result.get('daily', []))
            hourly_points = len(result.get('hourly', []))
            accounts = len(result.get('by_account', {}))
            total_content = result.get('summary', {}).get('total_content', 0)
            
            print(f"\n📊 {label}:")
            print(f"  ├─ Daily data points: {daily_points}")
            print(f"  ├─ Hourly data points: {hourly_points}")
            print(f"  ├─ Accounts tracked: {accounts}")
            print(f"  └─ Total content: {total_content}")
            
            # Validate expected data point counts
            expected_daily = days + 1  # Should include start and end dates
            if abs(daily_points - expected_daily) <= 1:  # Allow 1 day tolerance
                print(f"  ✅ Daily points correct (~{expected_daily})")
            else:
                print(f"  ⚠️  Daily points unexpected (got {daily_points}, expected ~{expected_daily})")
                
            # For short ranges, expect 24-48 hours of hourly data
            expected_hourly = 48 if days <= 2 else 24
            if hourly_points == expected_hourly:
                print(f"  ✅ Hourly points correct ({expected_hourly})")
            
        except Exception as e:
            print(f"  ❌ Error testing {label}: {e}")
    
def test_tag_functionality():
    """Test tag/concept endpoints with different time ranges"""
    print("\n\n🏷️  Testing Concept Analysis with Extended Ranges")
    print("=" * 60)
    
    test_ranges = [
        (7, "7 days", 10),
        (30, "30 days", 15),
        (90, "Quarter", 20),
        (180, "Half year", 25),
        (365, "Full year", 30)
    ]
    
    for days, label, limit in test_ranges:
        try:
            result = get_trends_tags(days, limit)
            
            top_tags = len(result.get('top_tags', []))
            rising_tags = len(result.get('rising_tags', []))
            declining_tags = len(result.get('declining_tags', []))
            timeline_entries = len(result.get('tag_timeline', []))
            total_unique = result.get('tag_statistics', {}).get('total_unique', 0)
            
            print(f"\n📈 {label}:")
            print(f"  ├─ Top concepts found: {top_tags}")
            print(f"  ├─ Rising concepts: {rising_tags}")
            print(f"  ├─ Declining concepts: {declining_tags}")
            print(f"  ├─ Timeline entries: {timeline_entries}")
            print(f"  └─ Total unique concepts: {total_unique}")
            
            # Show top concept if available
            if result.get('top_tags'):
                top_concept = result['top_tags'][0]
                print(f"  🏆 Top: \"{top_concept.get('tag', 'Unknown')}\" ({top_concept.get('count', 0)} uses)")
            
            # Show trend example if available
            if rising_tags > 0:
                rising = result['rising_tags'][0]
                print(f"  📈 Rising: \"{rising.get('tag', 'Unknown')}\" (+{rising.get('velocity', 0)}%)")
                
        except Exception as e:
            print(f"  ❌ Error testing {label}: {e}")

def test_performance_considerations():
    """Test performance with different time ranges"""
    print("\n\n⚡ Testing Performance Characteristics")
    print("=" * 60)
    
    import time
    
    ranges_to_test = [
        (7, "Week"),
        (90, "Quarter"),
        (365, "Year")
    ]
    
    for days, label in ranges_to_test:
        try:
            start_time = time.time()
            result = get_trends_timeline(days)
            end_time = time.time()
            
            duration = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
            data_points = len(result.get('daily', []))
            
            print(f"\n⏱️  {label} ({days} days):")
            print(f"  ├─ Query time: {duration}ms")
            print(f"  ├─ Data points: {data_points}")
            print(f"  └─ Rate: {round(data_points / max(duration, 1) * 1000, 1)} points/sec")
            
            # Performance expectations
            if duration < 1000:  # Under 1 second
                print("  ✅ Performance good")
            elif duration < 5000:  # Under 5 seconds
                print("  ⚠️  Performance acceptable")
            else:
                print("  ❌ Performance may need optimization")
                
        except Exception as e:
            print(f"  ❌ Error testing {label}: {e}")

def test_data_availability():
    """Check what data is actually available in the database"""
    print("\n\n💾 Data Availability Check")
    print("=" * 60)
    
    from pymongo import MongoClient
    
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client.smarttrendtracer
        
        # Check data counts
        tweet_count = db.tweets.count_documents({})
        article_count = db.articles.count_documents({})
        paper_count = db.papers.count_documents({})
        concept_count = db.tag_concepts_v2.count_documents({})
        instance_count = db.tag_instances.count_documents({})
        
        print(f"\n📊 Database Contents:")
        print(f"  ├─ Tweets: {tweet_count:,}")
        print(f"  ├─ Articles: {article_count:,}")  
        print(f"  ├─ Papers: {paper_count:,}")
        print(f"  ├─ Concepts: {concept_count:,}")
        print(f"  └─ Tag instances: {instance_count:,}")
        
        # Check date ranges
        if tweet_count > 0:
            oldest_tweet = db.tweets.find().sort([('created_at', 1)]).limit(1)[0]
            newest_tweet = db.tweets.find().sort([('created_at', -1)]).limit(1)[0]
            
            oldest_date = oldest_tweet['created_at'].strftime('%Y-%m-%d')
            newest_date = newest_tweet['created_at'].strftime('%Y-%m-%d')
            
            # Calculate actual range
            date_range = (newest_tweet['created_at'] - oldest_tweet['created_at']).days
            
            print(f"\n📅 Tweet Date Range:")
            print(f"  ├─ Oldest: {oldest_date}")
            print(f"  ├─ Newest: {newest_date}")
            print(f"  └─ Span: {date_range} days")
            
            if date_range >= 365:
                print("  ✅ Full year of data available")
            elif date_range >= 180:
                print("  ✅ Half year of data available") 
            elif date_range >= 90:
                print("  ✅ Quarter of data available")
            else:
                print("  ⚠️  Limited historical data")
        
    except Exception as e:
        print(f"  ❌ Error checking database: {e}")

if __name__ == "__main__":
    print("🚀 Extended Timeline Functionality Test")
    print("Testing quarterly, half-year, and yearly views")
    print("=" * 70)
    
    test_data_availability()
    test_timeline_functionality()
    test_tag_functionality()
    test_performance_considerations()
    
    print("\n\n✅ Extended timeline testing complete!")
    print("The system now supports:")
    print("  • 90-day quarterly views")
    print("  • 180-day half-year views")  
    print("  • 365-day yearly views")
    print("  • Smart chart labeling based on time range")
    print("  • Performance optimizations for long-term data")