#!/usr/bin/env python3
"""
Continuous tweet collector that runs indefinitely
Collects newest tweets every 15 minutes with proper rate limiting
"""
import sys
import os
import time
import signal
from datetime import datetime, timezone

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.collectors.twitter_collector import TwitterCollector
from app.models import get_db, Tweet
from sqlalchemy import func

# Global flag for graceful shutdown
running = True

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global running
    if running:
        print(f"\n🛑 Received shutdown signal. Stopping gracefully...")
        running = False
    else:
        print("\n⚠️  Already shutting down, please wait...")
        sys.exit(1)  # Force exit on second Ctrl+C

def collect_latest_tweets():
    """Collect latest tweets from all configured accounts"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting tweet collection...")
    print("=" * 60)
    
    try:
        # Create collector with database session
        db = next(get_db())
        
        # Import here to avoid circular imports
        import tweepy
        from app.config import ACCOUNTS_TO_FOLLOW
        
        # Get before count for debug
        total_before = db.query(func.count(Tweet.id)).scalar()
        
        # Direct Twitter API collection without rate limiter interference
        bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        client = tweepy.Client(bearer_token=bearer_token)
        
        new_tweets_count = 0
        
        print("📊 Collecting newest tweets from 7 accounts...")
        
        for account in ACCOUNTS_TO_FOLLOW:
            try:
                print(f"  Checking @{account['username']}...", end='')
                
                # Get tweets for this account
                tweets = client.get_users_tweets(
                    id=account['id'],
                    max_results=50,
                    tweet_fields=['created_at', 'public_metrics', 'referenced_tweets', 'entities', 'note_tweet'],
                    media_fields=['url', 'preview_image_url', 'alt_text', 'width', 'height', 'type'],
                    expansions=['attachments.media_keys', 'referenced_tweets.id']
                )
                
                if tweets.data:
                    # Use the collector to properly save tweets
                    from app.collectors.twitter_collector import TwitterCollector
                    collector = TwitterCollector(db_session=db)
                    
                    # Process media and referenced tweets
                    media_dict = {}
                    if tweets.includes and 'media' in tweets.includes:
                        for media in tweets.includes['media']:
                            media_dict[media.media_key] = media
                    
                    referenced_tweets_dict = {}
                    if tweets.includes and 'tweets' in tweets.includes:
                        for ref_tweet in tweets.includes['tweets']:
                            referenced_tweets_dict[str(ref_tweet.id)] = ref_tweet
                    
                    # Save each tweet
                    account_new = 0
                    for tweet in tweets.data:
                        if collector._save_tweet(tweet, account, media_dict, referenced_tweets_dict):
                            account_new += 1
                            new_tweets_count += 1
                    
                    if account_new > 0:
                        print(f" ✓ ({account_new} NEW)")
                    else:
                        print(f" ✓ (already have all {len(tweets.data)})")
                else:
                    print(" ✓ (no tweets)")
                    
            except tweepy.errors.TooManyRequests:
                print(" ⚠️ RATE LIMITED")
                print(f"\n🚫 Hit Twitter rate limit after {new_tweets_count} new tweets")
                print("⏳ Will wait 15 minutes and try again...")
                db.close()
                return -429  # Special code for rate limit
            except Exception as e:
                print(f" ❌ Error: {e}")
        
        # Commit the changes
        db.commit()
        
        # Get after count and new tweets for debug
        total_after = db.query(func.count(Tweet.id)).scalar()
        
        if new_tweets_count > 0:
            print(f"\n✅ Collected {new_tweets_count} new tweets")
            print(f"🔍 DEBUG: Total tweets: {total_before} → {total_after}")
            
            # Show the newest tweets collected
            newest = db.query(Tweet).order_by(Tweet.created_at.desc()).limit(min(5, new_tweets_count)).all()
            print("📝 DEBUG: Latest collected tweets:")
            for tweet in newest:
                timestamp = tweet.created_at.strftime('%H:%M')
                text_preview = tweet.text[:60] + "..." if len(tweet.text) > 60 else tweet.text
                print(f"   @{tweet.author_username} {timestamp}: {text_preview}")
        else:
            print("\n📭 No new tweets found")
            print(f"🔍 DEBUG: Total tweets unchanged: {total_before}")
        
        # Show quick summary
        # Get latest tweet per account  
        latest_tweets = db.query(
            Tweet.author_username,
            func.max(Tweet.created_at).label('latest')
        ).group_by(Tweet.author_username).all()
        
        print("\n📈 Latest tweets per account:")
        for stat in latest_tweets:
            if stat.latest:
                latest_time = stat.latest.strftime('%m-%d %H:%M')
                # Check if it's sama and show snippet if recent
                if stat.author_username == 'sama':
                    recent_sama = db.query(Tweet).filter(
                        Tweet.author_username == 'sama'
                    ).order_by(Tweet.created_at.desc()).first()
                    snippet = recent_sama.text[:50] + "..." if recent_sama else ""
                    # Highlight if this might be the GPT-5 tweet
                    if "GPT-5" in recent_sama.text:
                        print(f"  @{stat.author_username}: {latest_time} - 🔥 {snippet}")
                    else:
                        print(f"  @{stat.author_username}: {latest_time} - {snippet}")
                else:
                    print(f"  @{stat.author_username}: {latest_time}")
            else:
                print(f"  @{stat.author_username}: No tweets")
        
        # Update collection state to track this run
        from app.models import CollectionState
        CollectionState.update_last_run(db, tweet_count=new_tweets_count)
        
        db.close()
        return new_tweets_count
        
    except Exception as e:
        print(f"❌ Error during collection: {e}")
        import traceback
        traceback.print_exc()
        return -1

def continuous_collection():
    """Run continuous tweet collection every 15 minutes"""
    print("🚀 Starting continuous tweet collection...")
    print("⏱️  Will collect tweets every 15 minutes")
    print("🛑 Press Ctrl+C to stop gracefully")
    print("=" * 60)
    
    collection_count = 0
    
    while running:
        collection_count += 1
        print(f"\n🔄 Collection cycle #{collection_count}")
        
        # Collect tweets
        result = collect_latest_tweets()
        
        if result == -429:
            print("⚠️  Rate limited - waiting 15 minutes...")
        elif result < 0:
            print("❌ Collection failed, but continuing...")
        
        if not running:
            break
            
        # Wait 15 minutes (900 seconds) with periodic status updates
        print(f"\n⏳ Waiting 15 minutes until next collection...")
        wait_time = 15 * 60  # 15 minutes in seconds
        
        # Use shorter sleep intervals for better shutdown response
        for elapsed in range(0, wait_time, 5):  # Check every 5 seconds
            if not running:
                print("\n🛑 Stopping collection loop...")
                break
                
            remaining = wait_time - elapsed
            minutes = remaining // 60
            seconds = remaining % 60
            
            # Show status every 60 seconds
            if elapsed % 60 == 0:
                if minutes > 0:
                    print(f"   ⏱️  {minutes} minutes {seconds} seconds remaining...")
                else:
                    print(f"   ⏱️  {seconds} seconds remaining...")
            
            time.sleep(5)  # Sleep only 5 seconds for responsive shutdown
        
        if not running:
            break
    
    print("\n✨ Continuous collection stopped gracefully!")

if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check environment variables
    import dotenv
    dotenv.load_dotenv()
    
    if not os.getenv('TWITTER_BEARER_TOKEN'):
        print("❌ Error: TWITTER_BEARER_TOKEN not found in .env file")
        print("Please add your Twitter Bearer Token to backend/.env")
        sys.exit(1)
    
    try:
        continuous_collection()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("👋 Tweet collector finished")