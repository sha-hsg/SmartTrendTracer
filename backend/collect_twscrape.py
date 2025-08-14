#!/usr/bin/env python3
"""
Collect tweets using twscrape (no rate limits!)
"""
import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.collectors.twscrape_collector import TwscrapeCollector
from app.models import get_db, Tweet, CollectionState
from sqlalchemy import func

async def main():
    print("🚀 TWSCRAPE COLLECTION (No Rate Limits!)")
    print("=" * 60)
    
    db = next(get_db())
    
    try:
        # Get last collection time
        last_run = CollectionState.get_last_run(db)
        
        if last_run:
            if last_run.tzinfo is None:
                last_run = last_run.replace(tzinfo=timezone.utc)
            print(f"📊 Last collection: {last_run.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            since = last_run
        else:
            # Default to 24 hours ago
            since = datetime.now(timezone.utc) - timedelta(hours=24)
            print(f"📊 First run, collecting from: {since.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Count tweets before
        total_before = db.query(func.count(Tweet.id)).scalar()
        print(f"📈 Tweets before: {total_before}")
        
        # Create collector
        collector = TwscrapeCollector(db_session=db)
        
        print("\n🔄 Starting collection (no rate limits!)...")
        print("   This may take a minute on first run to setup...\n")
        
        # Collect from all accounts
        new_tweets = await collector.collect_all_accounts(since=since)
        
        # Update collection state
        CollectionState.update_last_run(db, tweet_count=new_tweets)
        
        # Get statistics
        total_after = db.query(func.count(Tweet.id)).scalar()
        recent_tweets = db.query(func.count(Tweet.id)).filter(
            Tweet.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        ).scalar()
        
        print("\n" + "=" * 60)
        print("✅ TWSCRAPE COLLECTION COMPLETE")
        print("=" * 60)
        print(f"📊 Results:")
        print(f"   • New tweets collected: {new_tweets}")
        print(f"   • Total tweets: {total_after}")
        print(f"   • Tweets from last 24h: {recent_tweets}")
        print(f"\n💡 Benefits of twscrape:")
        print(f"   • No rate limits!")
        print(f"   • Can collect as much as needed")
        print(f"   • Can search tweets (bonus feature)")
        print(f"   • Can get older tweets")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("\n⚠️  IMPORTANT NOTES:")
    print("   • Twscrape uses web scraping (not official API)")
    print("   • First run will be slower (setting up accounts)")
    print("   • May need periodic updates if Twitter changes")
    print("   • Use at your own risk (violates Twitter ToS)")
    
    response = input("\nProceed with twscrape collection? (y/n): ")
    
    if response.lower() == 'y':
        asyncio.run(main())
    else:
        print("Cancelled")