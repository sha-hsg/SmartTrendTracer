#!/usr/bin/env python3
"""
Test the URL update API endpoint
"""
import requests
import json

def test_url_update():
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
    original_url = article.get('url')
    
    print(f"Testing URL update for article: {article['title'][:50]}...")
    print(f"Original URL: {original_url}")
    
    # Test updating URL
    new_url = "https://example.substack.com/p/test-article"
    
    update_response = requests.patch(
        f"{base_url}/api/substack/articles/{article_id}/url",
        json={"url": new_url}
    )
    
    if update_response.status_code == 200:
        result = update_response.json()
        print(f"✅ URL updated successfully!")
        print(f"New URL: {result['url']}")
        
        # Test clearing URL (empty string)
        clear_response = requests.patch(
            f"{base_url}/api/substack/articles/{article_id}/url",
            json={"url": ""}
        )
        
        if clear_response.status_code == 200:
            print(f"✅ URL cleared successfully!")
        
        # Restore original URL if it existed
        if original_url:
            requests.patch(
                f"{base_url}/api/substack/articles/{article_id}/url",
                json={"url": original_url}
            )
            print(f"✅ Restored original URL")
    else:
        print(f"❌ Failed to update URL: {update_response.status_code}")
        print(update_response.text)

if __name__ == "__main__":
    test_url_update()