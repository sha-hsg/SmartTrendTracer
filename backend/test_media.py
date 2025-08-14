#!/usr/bin/env python3
"""
Test media display - verify photos and videos are working
"""
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, Tweet, TweetMedia
from sqlalchemy import func

def test_media():
    print("🖼️ MEDIA TEST")
    print("=" * 60)
    
    # Check database
    db = next(get_db())
    
    # Count media types
    media_stats = db.query(
        TweetMedia.type,
        func.count(TweetMedia.id)
    ).group_by(TweetMedia.type).all()
    
    print("📊 Media in Database:")
    for media_type, count in media_stats:
        emoji = "🖼️" if media_type == "photo" else "🎬" if media_type == "video" else "🏞️"
        print(f"   {emoji} {media_type}: {count}")
    
    # Get sample tweets with photos
    tweets_with_photos = db.query(Tweet).join(TweetMedia).filter(
        TweetMedia.type == "photo"
    ).limit(3).all()
    
    print("\n🖼️ Sample Tweets with Photos:")
    for tweet in tweets_with_photos:
        print(f"\n@{tweet.author_username}:")
        print(f"  {tweet.text[:60]}...")
        for media in tweet.media:
            if media.type == "photo":
                print(f"  🖼️ Photo URL: {media.url[:50]}..." if media.url else "  No URL!")
    
    # Test API endpoint
    print("\n🌐 Testing API Endpoint:")
    try:
        response = requests.get("http://localhost:8000/api/tweets?limit=5")
        if response.status_code == 200:
            tweets = response.json()
            photos_found = 0
            videos_found = 0
            
            for tweet in tweets:
                for media in tweet.get('media', []):
                    if media['type'] == 'photo':
                        photos_found += 1
                    elif media['type'] == 'video':
                        videos_found += 1
            
            print(f"   ✅ API working!")
            print(f"   🖼️ Photos in response: {photos_found}")
            print(f"   🎬 Videos in response: {videos_found}")
            
            # Show a sample photo URL
            for tweet in tweets:
                for media in tweet.get('media', []):
                    if media['type'] == 'photo' and media.get('url'):
                        print(f"\n🖼️ Sample photo URL from API:")
                        print(f"   {media['url']}")
                        break
                else:
                    continue
                break
        else:
            print(f"   ❌ API not running or error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Cannot connect to API: {e}")
        print("   Make sure to run: python simple_server.py")
    
    print("\n" + "=" * 60)
    print("💡 TROUBLESHOOTING:")
    print("\n1. Make sure backend is running:")
    print("   python simple_server.py")
    print("\n2. Make sure frontend is running:")
    print("   cd ../frontend && npm run dev")
    print("\n3. Check browser console for errors:")
    print("   Press F12 in browser, go to Console tab")
    print("\n4. Photos should display if:")
    print("   - URL exists in database ✅")
    print("   - API returns media array ✅")
    print("   - Frontend TweetCard handles type='photo' ✅")
    
    db.close()

if __name__ == "__main__":
    test_media()