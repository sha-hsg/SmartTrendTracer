#!/usr/bin/env python
"""
Extract and assign URLs to all non-deleted Substack articles
Parses the original HTML content to find Substack article URLs
"""
import re
import sys
import os
from pathlib import Path
from bs4 import BeautifulSoup
from sqlalchemy import or_

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.substack import SubstackArticle

def extract_url_from_html(html_content: str) -> str:
    """
    Extract Substack article URL from HTML content
    
    Looks for various patterns:
    1. app-link URLs (most common in emails)
    2. redirect URLs with embedded article links
    3. Direct links with substack.com/p/ pattern
    4. View in browser links
    """
    if not html_content:
        return None
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Strategy 1: Look for app-link URLs (most common in email newsletters)
        # These contain publication_id and post_id which can be used to construct the URL
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Check for app-link pattern (contains post ID and publication info)
            if 'substack.com/app-link/post' in href:
                # Extract post_id and publication_id from the URL
                import urllib.parse
                parsed = urllib.parse.urlparse(href)
                params = urllib.parse.parse_qs(parsed.query)
                
                # For now, just keep the app-link URL as it redirects to the actual article
                # Clean it up by removing tracking parameters
                clean_url = href.split('&utm_source')[0] if '&utm_source' in href else href
                return clean_url
            
        # Strategy 2: Look for redirect URLs (second most common)
        # These are base64-encoded redirects that contain the actual article URL
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            if 'substack.com/redirect' in href:
                # For redirect URLs, we can keep them as-is since they redirect to the actual article
                # Or we could try to decode the embedded URL, but redirect works fine
                return href
            
        # Strategy 3: Look for direct article links
        # Pattern: https://[author].substack.com/p/[article-slug]
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Check for Substack article pattern
            if 'substack.com/p/' in href and 'redirect' not in href and 'app-link' not in href:
                # Clean up the URL (remove tracking parameters)
                if '?' in href:
                    href = href.split('?')[0]
                return href
            
            # Check for "View in browser" or "Read online" links
            link_text = link.get_text(strip=True).lower()
            if any(phrase in link_text for phrase in ['view in browser', 'read online', 'view post']):
                if 'substack.com' in href:
                    if '?' in href:
                        href = href.split('?')[0]
                    return href
        
        # Strategy 4: Look for Open Graph meta tags
        og_url = soup.find('meta', property='og:url')
        if og_url and og_url.get('content'):
            url = og_url['content']
            if 'substack.com' in url:
                return url
        
        # Strategy 5: Look for canonical link
        canonical = soup.find('link', rel='canonical')
        if canonical and canonical.get('href'):
            url = canonical['href']
            if 'substack.com' in url:
                return url
        
        # Strategy 6: Search for Substack URLs in text using regex
        # This is less reliable but can catch URLs that aren't in anchor tags
        url_pattern = r'https?://[a-zA-Z0-9\-]+\.substack\.com/p/[a-zA-Z0-9\-]+'
        matches = re.findall(url_pattern, html_content)
        if matches:
            # Return the first match, cleaned up
            url = matches[0]
            if '?' in url:
                url = url.split('?')[0]
            return url
        
    except Exception as e:
        print(f"  ⚠️ Error parsing HTML: {e}")
    
    return None

def process_articles():
    """Process all non-deleted articles and extract URLs"""
    
    print("🔍 Starting URL extraction for Substack articles...")
    print("-" * 50)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Query all non-deleted articles
        articles = db.query(SubstackArticle).filter(
            or_(
                SubstackArticle.deleted == False,
                SubstackArticle.deleted.is_(None)
            )
        ).all()
        
        print(f"📊 Found {len(articles)} non-deleted articles to process")
        print()
        
        # Counters
        updated_count = 0
        already_has_url = 0
        no_url_found = 0
        
        # Process each article
        for i, article in enumerate(articles, 1):
            # Show progress every 10 articles
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(articles)} articles processed...")
            
            # Skip if article already has a URL
            if article.url:
                already_has_url += 1
                continue
            
            # Try to extract URL from HTML content
            url = extract_url_from_html(article.content_html)
            
            if url:
                # Update the article with the extracted URL
                article.url = url
                updated_count += 1
                print(f"✅ Article {i}: '{article.title[:50]}...'")
                print(f"   URL: {url}")
            else:
                no_url_found += 1
                # Only show warnings for articles we couldn't find URLs for (limit output)
                if no_url_found <= 10:  # Show first 10 warnings only
                    print(f"⚠️ Article {i}: '{article.title[:50]}...' - No URL found")
        
        # Commit all changes
        if updated_count > 0:
            db.commit()
            print()
            print("✅ Changes saved to database")
        
        # Print summary
        print()
        print("=" * 50)
        print("📊 SUMMARY")
        print("=" * 50)
        print(f"  Total articles processed: {len(articles)}")
        print(f"  ✅ URLs extracted and added: {updated_count}")
        print(f"  ℹ️ Already had URLs: {already_has_url}")
        print(f"  ⚠️ No URL found: {no_url_found}")
        
        if no_url_found > 10:
            print(f"\n  (Showing first 10 warnings only, {no_url_found - 10} more articles without URLs)")
        
        # Provide suggestions if many articles are missing URLs
        if no_url_found > 0:
            print()
            print("💡 SUGGESTIONS:")
            print("  - Articles without URLs may be:")
            print("    • Imported from sources other than email")
            print("    • Missing the original HTML content")
            print("    • From newsletters that don't include web links")
            print("  - You can manually add URLs using the article editor")
        
    except Exception as e:
        print(f"❌ Error processing articles: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
        print()
        print("🏁 URL extraction complete!")

def verify_urls():
    """Verify that URLs were successfully added"""
    db = next(get_db())
    
    try:
        # Count articles with URLs
        total_articles = db.query(SubstackArticle).filter(
            or_(
                SubstackArticle.deleted == False,
                SubstackArticle.deleted.is_(None)
            )
        ).count()
        
        articles_with_urls = db.query(SubstackArticle).filter(
            or_(
                SubstackArticle.deleted == False,
                SubstackArticle.deleted.is_(None)
            ),
            SubstackArticle.url.isnot(None)
        ).count()
        
        print()
        print("📊 URL VERIFICATION:")
        print(f"  Total non-deleted articles: {total_articles}")
        print(f"  Articles with URLs: {articles_with_urls}")
        print(f"  Coverage: {articles_with_urls/total_articles*100:.1f}%")
        
        # Show a few sample URLs
        print()
        print("📌 Sample URLs (first 5):")
        samples = db.query(SubstackArticle).filter(
            SubstackArticle.url.isnot(None)
        ).limit(5).all()
        
        for article in samples:
            print(f"  • {article.title[:40]}...")
            print(f"    {article.url}")
        
    finally:
        db.close()

if __name__ == "__main__":
    process_articles()
    verify_urls()