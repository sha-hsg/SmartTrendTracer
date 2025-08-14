#!/usr/bin/env python3
"""
Test the date update API endpoint
"""
import requests
import json
from datetime import datetime, timedelta

# Test the date update endpoint
def test_date_update():
    base_url = "http://localhost:8000"
    
    # First, get an article
    response = requests.get(f"{base_url}/api/substack/articles?limit=1")
    if response.status_code != 200:
        print("Failed to get articles")
        return
    
    data = response.json()
    
    # Handle both list and dict response formats
    if isinstance(data, dict):
        articles = data.get('articles', [])
    else:
        articles = data
        
    if not articles:
        print("No articles found")
        return
    
    article = articles[0]
    article_id = article['id']
    original_date = article.get('published_at')
    
    print(f"Testing date update for article: {article['title'][:50]}...")
    print(f"Original date: {original_date}")
    
    # Update to a new date (7 days earlier)
    new_date = datetime.now() - timedelta(days=7)
    
    update_response = requests.patch(
        f"{base_url}/api/substack/articles/{article_id}/date",
        json={"published_at": new_date.isoformat()}
    )
    
    if update_response.status_code == 200:
        result = update_response.json()
        print(f"✅ Date updated successfully!")
        print(f"New date: {result['published_at']}")
    else:
        print(f"❌ Failed to update date: {update_response.status_code}")
        print(update_response.text)

if __name__ == "__main__":
    test_date_update()