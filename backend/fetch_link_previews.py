#!/usr/bin/env python3
"""
Fetch link preview data (Twitter Cards) for tweets with URLs
"""

import tweepy
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import time

load_dotenv()
client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
if not BEARER_TOKEN:
    print('❌ No bearer token')
    exit(1)

twitter_client = tweepy.Client(bearer_token=BEARER_TOKEN)

def fetch_link_preview(tweet_id):
    """
    Fetch link preview data for a tweet
    """
    try:
        # Get tweet with card data
        response = twitter_client.get_tweet(
            tweet_id,
            tweet_fields=['entities'],
            expansions=['attachments.poll_ids'],  # We need to use a valid expansion
            media_fields=['url', 'preview_image_url']
        )
        
        if response and response.data:
            tweet_data = response.data.data
            
            # Extract URL entities with their preview data
            if 'entities' in tweet_data and 'urls' in tweet_data['entities']:
                urls_with_previews = []
                for url in tweet_data['entities']['urls']:
                    url_info = {
                        'url': url.get('url'),
                        'expanded_url': url.get('expanded_url'),
                        'display_url': url.get('display_url'),
                        'title': url.get('title'),
                        'description': url.get('description'),
                        'unwound_url': url.get('unwound_url'),
                        # Twitter Card images if available
                        'images': url.get('images', []),
                        'status': url.get('status'),
                        'media_key': url.get('media_key')
                    }
                    urls_with_previews.append(url_info)
                
                return urls_with_previews
    except Exception as e:
        print(f"Error fetching preview for {tweet_id}: {e}")
    
    return None

# Update the specific tweet
tweet_id = '1961561723501953131'
print(f'🔍 Fetching link preview for tweet {tweet_id}')

previews = fetch_link_preview(tweet_id)
if previews:
    print(f'\\n📸 Found {len(previews)} URL(s) with preview data:')
    for preview in previews:
        print(f"  URL: {preview['expanded_url']}")
        print(f"  Title: {preview.get('title', 'No title')}")
        print(f"  Description: {preview.get('description', 'No description')}")
        if preview.get('images'):
            print(f"  Preview images: {len(preview['images'])} image(s)")
            for img in preview['images']:
                print(f"    - {img.get('url', 'No URL')}")
    
    # Update in database
    result = db.tweets.update_one(
        {'_id': tweet_id},
        {'$set': {
            'link_previews': previews,
            'has_link_preview': True
        }}
    )
    print(f'\\n✅ Updated database: {result.modified_count} document(s)')
else:
    print('❌ No preview data available')

# Now let's use a different approach - fetch the Open Graph data from the website directly
print('\\n🌐 Fetching Open Graph data from the website...')

import requests
from bs4 import BeautifulSoup

def fetch_opengraph_data(url):
    """
    Fetch Open Graph metadata from a URL
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            og_data = {}
            
            # Find Open Graph meta tags
            og_title = soup.find('meta', property='og:title')
            if og_title:
                og_data['title'] = og_title.get('content')
            
            og_description = soup.find('meta', property='og:description')
            if og_description:
                og_data['description'] = og_description.get('content')
            
            og_image = soup.find('meta', property='og:image')
            if og_image:
                og_data['image'] = og_image.get('content')
            
            og_site = soup.find('meta', property='og:site_name')
            if og_site:
                og_data['site_name'] = og_site.get('content')
            
            # Also check for Twitter Card tags
            twitter_image = soup.find('meta', {'name': 'twitter:image'})
            if twitter_image and not og_data.get('image'):
                og_data['image'] = twitter_image.get('content')
            
            return og_data
    except Exception as e:
        print(f"Error fetching OG data: {e}")
    
    return None

# Fetch OG data for the epoch.ai link
url = 'https://epoch.ai/data-insights/gpt-capabilities-progress'
print(f'Fetching Open Graph data from: {url}')

og_data = fetch_opengraph_data(url)
if og_data:
    print('\\n📋 Open Graph data found:')
    for key, value in og_data.items():
        print(f'  {key}: {value[:100] if len(str(value)) > 100 else value}')
    
    # Create a link preview from OG data
    link_preview = {
        'url': 'https://t.co/pr6LUFy0dv',
        'expanded_url': url,
        'display_url': 'epoch.ai/data-insights/…',
        'preview_title': og_data.get('title'),
        'preview_description': og_data.get('description'),
        'preview_image_url': og_data.get('image'),
        'preview_site_name': og_data.get('site_name', 'epoch.ai')
    }
    
    # Update the tweet with link preview
    result = db.tweets.update_one(
        {'_id': tweet_id},
        {'$set': {
            'link_preview': link_preview,
            'has_link_preview': True
        }}
    )
    print(f'\\n✅ Updated tweet with link preview data')
    
    # Verify
    check = db.tweets.find_one({'_id': tweet_id})
    if check and check.get('link_preview'):
        print(f'\\n📊 Verification:')
        print(f"  Preview image: {check['link_preview'].get('preview_image_url')}")