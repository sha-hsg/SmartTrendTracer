#!/usr/bin/env python3
"""
Test script to verify the Timeline tab functionality is working
Tests all timeline views: Timeline, Hourly, Concepts, By Account
"""

import sys
sys.path.append('.')

from app.api.analytics_trends_mongodb import get_trends_timeline, get_trends_tags

def test_timeline_tab():
    """Test the Timeline tab functionality"""
    print("🧪 Testing Timeline Tab Functionality")
    print("=" * 50)
    
    try:
        result = get_trends_timeline(7)
        
        # Check daily timeline data
        daily = result.get('daily', [])
        print(f"\n📅 Daily Timeline:")
        print(f"  ├─ Entries: {len(daily)}")
        print(f"  ├─ Frontend expects: array with .date and .count fields")
        
        if daily:
            sample = daily[0]
            has_date = 'date' in sample
            has_count = 'count' in sample
            print(f"  ├─ Has .date field: {'✅' if has_date else '❌'}")
            print(f"  ├─ Has .count field: {'✅' if has_count else '❌'}")
            
            if has_date and has_count:
                total_content = sum(entry.get('count', 0) for entry in daily)
                peak_day = max(daily, key=lambda x: x.get('count', 0))
                print(f"  ├─ Total content: {total_content}")
                print(f"  └─ Peak day: {peak_day.get('date', '')[:10]} ({peak_day.get('count', 0)} items)")
            else:
                print(f"  ❌ Missing required fields for frontend")
        
        return len(daily) > 0 and daily[0].get('count') is not None
        
    except Exception as e:
        print(f"❌ Timeline test failed: {e}")
        return False

def test_hourly_tab():
    """Test the Hourly tab functionality"""
    print("\n⏰ Testing Hourly Tab Functionality")
    print("=" * 50)
    
    try:
        result = get_trends_timeline(7)
        
        # Check hourly timeline data
        hourly = result.get('hourly', [])
        print(f"\n🕐 Hourly Timeline:")
        print(f"  ├─ Entries: {len(hourly)}")
        print(f"  ├─ Frontend expects: array with .hour and .count fields")
        
        if hourly:
            sample = hourly[0]
            has_hour = 'hour' in sample
            has_count = 'count' in sample
            print(f"  ├─ Has .hour field: {'✅' if has_hour else '❌'}")
            print(f"  ├─ Has .count field: {'✅' if has_count else '❌'}")
            
            if has_hour and has_count:
                # Test hour formatting for frontend
                hour_raw = sample.get('hour', '')
                hour_formatted = hour_raw.split(' ')[1] if ' ' in hour_raw else hour_raw
                print(f"  ├─ Hour format: '{hour_raw}' -> '{hour_formatted}'")
                
                # Find peak hour
                non_zero_hours = [h for h in hourly if h.get('count', 0) > 0]
                if non_zero_hours:
                    peak_hour = max(non_zero_hours, key=lambda x: x.get('count', 0))
                    peak_formatted = peak_hour.get('hour', '').split(' ')[1] if ' ' in peak_hour.get('hour', '') else peak_hour.get('hour', '')
                    print(f"  └─ Peak hour: {peak_formatted} ({peak_hour.get('count', 0)} items)")
                else:
                    print(f"  └─ No activity in tracked hours")
            else:
                print(f"  ❌ Missing required fields for frontend")
                
        return len(hourly) > 0 and hourly[0].get('count') is not None
        
    except Exception as e:
        print(f"❌ Hourly test failed: {e}")
        return False

def test_concepts_tab():
    """Test the Concepts tab functionality"""  
    print("\n🏷️  Testing Concepts Tab Functionality")
    print("=" * 50)
    
    try:
        result = get_trends_tags(7, 10)
        
        # Check concepts data
        top_tags = result.get('top_tags', [])
        timeline = result.get('tag_timeline', [])
        
        print(f"\n🏆 Top Concepts:")
        print(f"  ├─ Found: {len(top_tags)} concepts")
        print(f"  ├─ Frontend expects: array with .tag and .count fields")
        
        if top_tags:
            sample = top_tags[0]
            has_tag = 'tag' in sample
            has_count = 'count' in sample
            print(f"  ├─ Has .tag field: {'✅' if has_tag else '❌'}")
            print(f"  ├─ Has .count field: {'✅' if has_count else '❌'}")
            
            if has_tag and has_count:
                print(f"  └─ Top concept: \"{sample.get('tag')}\" ({sample.get('count')} mentions)")
                
                # Show top 3
                for i, concept in enumerate(top_tags[:3], 1):
                    trend_emoji = {"rising": "📈", "declining": "📉", "stable": "➡️"}.get(concept.get('trend', 'stable'), '➡️')
                    print(f"      {i}. {concept.get('tag')} - {concept.get('count')} mentions {trend_emoji}")
        
        print(f"\n📈 Concept Timeline:")
        print(f"  ├─ Timeline entries: {len(timeline)}")
        if timeline:
            entry = timeline[0]
            print(f"  └─ Sample: {entry.get('date')} had {len(entry.get('tags', []))} active concepts")
        
        return len(top_tags) > 0
        
    except Exception as e:
        print(f"❌ Concepts test failed: {e}")
        return False

def test_by_account_tab():
    """Test the By Account tab functionality"""
    print("\n👥 Testing By Account Tab Functionality")
    print("=" * 50)
    
    try:
        result = get_trends_timeline(7)
        
        # Check by-account data
        by_account = result.get('by_account', {})
        print(f"\n📊 Account Timeline:")
        print(f"  ├─ Accounts tracked: {len(by_account)}")
        print(f"  ├─ Frontend expects: object with account names as keys")
        
        if by_account:
            # Test data structure
            account_name = list(by_account.keys())[0]
            account_data = by_account[account_name]
            
            print(f"  ├─ Sample account: @{account_name}")
            print(f"  ├─ Data points: {len(account_data)}")
            
            if account_data:
                sample = account_data[0]
                has_date = 'date' in sample
                has_count = 'count' in sample
                print(f"  ├─ Has .date field: {'✅' if has_date else '❌'}")
                print(f"  ├─ Has .count field: {'✅' if has_count else '❌'}")
                
                if has_date and has_count:
                    total_by_account = sum(entry.get('count', 0) for entry in account_data)
                    print(f"  └─ @{account_name}: {total_by_account} total items")
                    
                    # Show top accounts by activity
                    account_totals = []
                    for acc_name, acc_data in by_account.items():
                        total = sum(entry.get('count', 0) for entry in acc_data)
                        account_totals.append((acc_name, total))
                    
                    account_totals.sort(key=lambda x: x[1], reverse=True)
                    print(f"\n  📊 Top 3 accounts:")
                    for i, (name, total) in enumerate(account_totals[:3], 1):
                        print(f"    {i}. @{name}: {total} items")
        
        return len(by_account) > 0
        
    except Exception as e:
        print(f"❌ By Account test failed: {e}")
        return False

def run_all_tests():
    """Run all timeline functionality tests"""
    print("🚀 Timeline Tab Functionality Tests")
    print("Testing all 4 tabs: Timeline, Hourly, Concepts, By Account")
    print("=" * 70)
    
    results = {}
    
    # Test each tab
    results['timeline'] = test_timeline_tab()
    results['hourly'] = test_hourly_tab() 
    results['concepts'] = test_concepts_tab()
    results['by_account'] = test_by_account_tab()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    
    all_passed = True
    for tab_name, passed in results.items():
        emoji = "✅" if passed else "❌"
        status = "WORKING" if passed else "NEEDS FIX"
        print(f"  {emoji} {tab_name.upper()} tab: {status}")
        if not passed:
            all_passed = False
    
    print(f"\n🎯 Overall Result: {'🎉 ALL WORKING' if all_passed else '⚠️  SOME ISSUES FOUND'}")
    
    if all_passed:
        print("\n✅ The Timeline functionality is now fully operational!")
        print("   You should see useful data in all 4 tabs:")
        print("   • Timeline: Daily activity charts")
        print("   • Hourly: Hour-by-hour activity patterns") 
        print("   • Concepts: Top trending concepts with charts")
        print("   • By Account: Per-account activity comparison")

if __name__ == "__main__":
    run_all_tests()