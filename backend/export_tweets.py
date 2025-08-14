#!/usr/bin/env python3
"""
Export all tweets to see their full content
"""
import sys
import os
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, Tweet, TweetMedia
from sqlalchemy import func

def export_tweets(format='text', author=None, limit=None):
    """Export tweets in various formats"""
    
    db = next(get_db())
    
    # Build query
    query = db.query(Tweet)
    
    if author:
        query = query.filter(Tweet.author_username == author)
    
    query = query.order_by(Tweet.created_at.desc())
    
    if limit:
        query = query.limit(limit)
    
    tweets = query.all()
    
    print(f"Found {len(tweets)} tweets to export")
    print("=" * 80)
    
    if format == 'text':
        # Simple text format
        for tweet in tweets:
            print(f"\n📅 {tweet.created_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"👤 @{tweet.author_username}")
            print(f"📊 ❤️ {tweet.like_count} 🔁 {tweet.retweet_count}")
            print(f"📝 Length: {len(tweet.text)} chars")
            print("-" * 40)
            print(tweet.text)
            print("-" * 80)
            
    elif format == 'json':
        # JSON format with all fields
        data = []
        for tweet in tweets:
            # Get media for this tweet
            media = db.query(TweetMedia).filter(TweetMedia.tweet_id == tweet.id).all()
            
            tweet_data = {
                'id': tweet.id,
                'author': tweet.author_username,
                'created_at': tweet.created_at.isoformat(),
                'text': tweet.text,
                'text_length': len(tweet.text),
                'metrics': {
                    'likes': tweet.like_count,
                    'retweets': tweet.retweet_count,
                    'replies': tweet.reply_count,
                    'quotes': tweet.quote_count
                },
                'media': [
                    {
                        'type': m.type,
                        'url': m.url,
                        'alt_text': m.alt_text
                    } for m in media
                ] if media else []
            }
            data.append(tweet_data)
        
        # Save to file
        filename = f"tweets_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported to {filename}")
        
    elif format == 'csv':
        # CSV format
        import csv
        
        filename = f"tweets_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Author', 'Text', 'Length', 'Likes', 'Retweets', 'Replies'])
            
            for tweet in tweets:
                writer.writerow([
                    tweet.created_at.strftime('%Y-%m-%d %H:%M'),
                    f"@{tweet.author_username}",
                    tweet.text,
                    len(tweet.text),
                    tweet.like_count,
                    tweet.retweet_count,
                    tweet.reply_count
                ])
        
        print(f"✅ Exported to {filename}")
    
    # Show truncation statistics
    truncated_count = sum(1 for t in tweets if t.text.endswith('...'))
    long_count = sum(1 for t in tweets if len(t.text) > 280)
    
    print(f"\n📊 Statistics:")
    print(f"  Total tweets: {len(tweets)}")
    print(f"  Possibly truncated (ending with ...): {truncated_count}")
    print(f"  Long tweets (>280 chars): {long_count}")
    
    if truncated_count > 0:
        print(f"\n💡 Tip: Run 'python update_truncated_tweets.py' to fetch full text for truncated tweets")
    
    db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Export tweets with full content')
    parser.add_argument('--format', choices=['text', 'json', 'csv'], default='text',
                       help='Export format (default: text)')
    parser.add_argument('--author', help='Filter by author username (e.g., sama)')
    parser.add_argument('--limit', type=int, help='Limit number of tweets')
    
    args = parser.parse_args()
    
    print(f"📤 Exporting tweets in {args.format} format...")
    
    export_tweets(format=args.format, author=args.author, limit=args.limit)