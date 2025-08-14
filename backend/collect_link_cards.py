#!/usr/bin/env python3
"""
Collect link preview cards (Twitter Cards) for tweets with URLs
These are the preview images that Twitter generates for external links
"""
import sys
import os
import json
import tweepy
from datetime import datetime
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, Tweet, TweetMedia

load_dotenv()

def collect_link_cards():
    """Find tweets with URLs but no media and extract link card images"""
    
    db = next(get_db())
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    client = tweepy.Client(bearer_token=bearer_token)
    
    # Find tweets with URLs but no media
    tweets_with_urls = db.query(Tweet).filter(
        Tweet.urls.isnot(None),
        Tweet.urls != '[]'
    ).order_by(Tweet.created_at.desc()).limit(200).all()
    
    print(f"Found {len(tweets_with_urls)} tweets with URLs")
    
    tweets_needing_cards = []
    for tweet in tweets_with_urls:
        # Check if this tweet has media
        media_count = db.query(TweetMedia).filter(TweetMedia.tweet_id == tweet.id).count()
        
        # Parse URLs to see if there are external links
        try:
            urls = json.loads(tweet.urls) if tweet.urls else []
            has_external_url = any(
                url.get('expanded_url', '').startswith('http') and 
                not url.get('expanded_url', '').startswith('https://twitter.com')
                for url in urls
            )
            
            if media_count == 0 and has_external_url:
                tweets_needing_cards.append(tweet)
        except:
            continue
    
    print(f"Found {len(tweets_needing_cards)} tweets that might have link cards")
    
    if not tweets_needing_cards:
        print("No tweets need link card processing")
        return
    
    # Process in batches
    batch_size = 100
    total_cards_added = 0
    
    for i in range(0, len(tweets_needing_cards), batch_size):
        batch = tweets_needing_cards[i:i+batch_size]
        tweet_ids = [t.id for t in batch]
        
        try:
            print(f"\n📥 Fetching link cards for batch {i//batch_size + 1} ({len(tweet_ids)} tweets)...")
            
            # Fetch tweets with entities
            response = client.get_tweets(
                ids=tweet_ids,
                tweet_fields=['entities'],
                expansions=[]
            )
            
            if not response.data:
                continue
            
            # Process each tweet
            for tweet_data in response.data:
                db_tweet = next((t for t in batch if t.id == str(tweet_data.id)), None)
                if not db_tweet:
                    continue
                
                # Check entities for link preview images
                if hasattr(tweet_data, 'entities') and tweet_data.entities:
                    urls = tweet_data.entities.get('urls', [])
                    
                    cards_added = 0
                    for url_data in urls:
                        # Check if this URL has preview images (Twitter Card)
                        if 'images' in url_data and url_data['images']:
                            for idx, image in enumerate(url_data['images']):
                                # Create a media record for the link card image
                                # Use URL as media_key since these don't have real media keys
                                media_key = f"card_{tweet_data.id}_{idx}"
                                
                                # Check if already exists
                                existing = db.query(TweetMedia).filter(
                                    TweetMedia.tweet_id == db_tweet.id,
                                    TweetMedia.media_key == media_key
                                ).first()
                                
                                if not existing:
                                    tweet_media = TweetMedia(
                                        tweet_id=db_tweet.id,
                                        media_key=media_key,
                                        type='link_card',  # Special type for link preview cards
                                        url=image.get('url'),
                                        alt_text=url_data.get('title', 'Link preview'),
                                        width=image.get('width'),
                                        height=image.get('height')
                                    )
                                    db.add(tweet_media)
                                    cards_added += 1
                                    total_cards_added += 1
                                
                                # Usually only save the first/largest image
                                break
                    
                    if cards_added > 0:
                        print(f"  ✅ Added {cards_added} link card(s) for @{db_tweet.author_username}")
                        
        except tweepy.errors.TooManyRequests:
            print("⚠️  Rate limited! Saving progress...")
            db.commit()
            print(f"Added {total_cards_added} link cards before rate limit")
            print("Please wait 15 minutes and run again.")
            return
        except Exception as e:
            print(f"❌ Error processing batch: {e}")
            continue
    
    # Commit all changes
    db.commit()
    
    print(f"\n✅ Successfully added {total_cards_added} link card images!")
    
    # Show statistics
    total_with_media = db.query(TweetMedia.tweet_id).distinct().count()
    link_cards = db.query(TweetMedia).filter(TweetMedia.type == 'link_card').count()
    print(f"📊 Total tweets with media: {total_with_media}")
    print(f"🔗 Total link cards: {link_cards}")
    
    db.close()

if __name__ == "__main__":
    print("🔗 Collecting link preview cards for tweets...")
    print("=" * 60)
    collect_link_cards()