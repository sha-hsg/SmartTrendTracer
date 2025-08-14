#!/usr/bin/env python3
"""
Quick script to view recent tweets from the database
"""
import sys
import os
from datetime import datetime, timedelta, timezone
from tabulate import tabulate

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import Tweet, Tag, get_db
from sqlalchemy import func

def view_recent_tweets(limit=10):
    """Display recent tweets in a nice format"""
    db = next(get_db())
    
    # Get recent tweets
    tweets = db.query(Tweet).order_by(Tweet.created_at.desc()).limit(limit).all()
    
    if not tweets:
        print("❌ No tweets found in database")
        print("   Run: python collect_tweets.py")
        return
    
    print(f"\n📊 Showing {len(tweets)} most recent tweets")
    print("=" * 80)
    
    for tweet in tweets:
        # Calculate time ago (handle both aware and naive datetimes)
        now = datetime.now(timezone.utc)
        
        # Make tweet.created_at timezone-aware if it isn't already
        if tweet.created_at.tzinfo is None:
            tweet_time = tweet.created_at.replace(tzinfo=timezone.utc)
        else:
            tweet_time = tweet.created_at
            
        time_diff = now - tweet_time
        if time_diff.days > 0:
            time_ago = f"{time_diff.days}d ago"
        elif time_diff.seconds > 3600:
            time_ago = f"{time_diff.seconds // 3600}h ago"
        else:
            time_ago = f"{time_diff.seconds // 60}m ago"
        
        # Get tags for this tweet
        tags = db.query(Tag.tag).filter(Tag.tweet_id == tweet.id).all()
        tag_str = ", ".join([t[0] for t in tags]) if tags else "No tags"
        
        # Print tweet info
        print(f"\n🐦 @{tweet.author_username} • {time_ago}")
        print(f"📝 {tweet.text[:200]}{'...' if len(tweet.text) > 200 else ''}")
        print(f"💙 {tweet.like_count} likes • 🔁 {tweet.retweet_count} retweets")
        print(f"🏷️  Tags: {tag_str}")
        print("-" * 80)
    
    db.close()

def show_statistics():
    """Show database statistics"""
    db = next(get_db())
    
    print("\n📈 Database Statistics")
    print("=" * 80)
    
    # Total tweets
    total = db.query(func.count(Tweet.id)).scalar()
    print(f"Total tweets: {total}")
    
    # Tweets by account
    stats = db.query(
        Tweet.author_username,
        func.count(Tweet.id).label('count'),
        func.max(Tweet.created_at).label('latest')
    ).group_by(Tweet.author_username).all()
    
    # Format as table
    table_data = []
    now = datetime.now(timezone.utc)
    for stat in stats:
        # Handle timezone awareness
        if stat.latest.tzinfo is None:
            latest_time = stat.latest.replace(tzinfo=timezone.utc)
        else:
            latest_time = stat.latest
            
        time_diff = now - latest_time
        hours_ago = time_diff.total_seconds() / 3600
        status = "✅" if hours_ago < 24 else "⚠️"
        table_data.append([
            status,
            f"@{stat.author_username}",
            stat.count,
            f"{hours_ago:.1f}h ago"
        ])
    
    print("\nTweets per account:")
    print(tabulate(table_data, headers=["Status", "Account", "Tweets", "Latest"], 
                   tablefmt="grid"))
    
    # Recent activity
    last_24h = datetime.now(timezone.utc) - timedelta(days=1)
    recent_count = db.query(func.count(Tweet.id)).filter(
        Tweet.created_at > last_24h
    ).scalar()
    print(f"\nTweets in last 24 hours: {recent_count}")
    
    # Tag statistics
    tag_count = db.query(func.count(Tag.id)).scalar()
    unique_tags = db.query(func.count(func.distinct(Tag.tag))).scalar()
    print(f"Total tags: {tag_count}")
    print(f"Unique tags: {unique_tags}")
    
    db.close()

def search_tweets(keyword):
    """Search tweets by keyword"""
    db = next(get_db())
    
    tweets = db.query(Tweet).filter(
        Tweet.text.contains(keyword)
    ).order_by(Tweet.created_at.desc()).limit(10).all()
    
    if not tweets:
        print(f"❌ No tweets found containing '{keyword}'")
        return
    
    print(f"\n🔍 Found {len(tweets)} tweets containing '{keyword}'")
    print("=" * 80)
    
    for tweet in tweets:
        print(f"\n@{tweet.author_username} • {tweet.created_at.strftime('%Y-%m-%d %H:%M')}")
        # Highlight keyword in text
        text = tweet.text[:200]
        text = text.replace(keyword, f"**{keyword}**")
        print(f"{text}{'...' if len(tweet.text) > 200 else ''}")
        print(f"💙 {tweet.like_count} • 🔁 {tweet.retweet_count}")
    
    db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="View tweets from database")
    parser.add_argument("-n", "--number", type=int, default=10, 
                        help="Number of tweets to show (default: 10)")
    parser.add_argument("-s", "--stats", action="store_true", 
                        help="Show statistics instead of tweets")
    parser.add_argument("--search", type=str, 
                        help="Search tweets by keyword")
    
    args = parser.parse_args()
    
    try:
        if args.stats:
            show_statistics()
        elif args.search:
            search_tweets(args.search)
        else:
            view_recent_tweets(args.number)
            print(f"\n💡 Tips:")
            print(f"  • View more tweets: python view_tweets.py -n 20")
            print(f"  • Show statistics: python view_tweets.py -s")
            print(f"  • Search tweets: python view_tweets.py --search 'GPT'")
            print(f"  • Open dashboard: http://localhost:3000")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()