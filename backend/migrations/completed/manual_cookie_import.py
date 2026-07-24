#!/usr/bin/env python3
"""
Manual approach: Use browser cookies to import full article
"""

import requests
from bs4 import BeautifulSoup
from app.models import get_db
from app.models.substack import SubstackArticle
from app.services.url_article_importer import URLArticleImporter


def import_with_browser_session(article_url: str):
    """
    Instructions for manual authentication and import
    """
    print("=" * 60)
    print("Manual Browser Authentication Method")
    print("=" * 60)
    print("\n📋 Instructions:")
    print("1. Open your web browser (Chrome/Firefox/Safari)")
    print("2. Go to: https://magazine.sebastianraschka.com")
    print("3. Click 'Sign in' and use the magic link from your email")
    print("4. Once logged in, navigate to the article:")
    print(f"   {article_url}")
    print("5. Verify you can see the FULL article (no paywall message)")
    print("6. Open Developer Tools (F12 or right-click → Inspect)")
    print("7. Go to the 'Network' tab")
    print("8. Refresh the page")
    print("9. Find the request to 'llm-research-papers-2025-list-one'")
    print("10. Right-click it → Copy → Copy as cURL")
    print("\n✂️ Then paste the cURL command below:")
    print("=" * 60)
    
    curl_command = input("\nPaste cURL command here (or 'skip' to try basic import): ").strip()
    
    if curl_command.lower() == 'skip':
        print("\nTrying basic import without authentication...")
        basic_import(article_url)
        return
    
    # Parse cookies from cURL command
    import re
    cookie_match = re.search(r"-H 'cookie: ([^']+)'", curl_command, re.IGNORECASE)
    if not cookie_match:
        cookie_match = re.search(r'-H "cookie: ([^"]+)"', curl_command, re.IGNORECASE)
    
    if cookie_match:
        cookie_string = cookie_match.group(1)
        print(f"\n✅ Found cookies: {cookie_string[:50]}...")
        
        # Parse cookies into dict
        cookies = {}
        for cookie in cookie_string.split('; '):
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookies[key] = value
        
        # Create session with cookies
        session = requests.Session()
        session.cookies.update(cookies)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        # Fetch the article
        print(f"\n📥 Fetching article with your session...")
        response = session.get(article_url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for paywall
            if soup.select_one('.paywall'):
                print("⚠️ Paywall still detected")
            else:
                print("✅ No paywall detected!")
            
            # Find content
            content_elem = soup.select_one('div.body.markup') or soup.select_one('div.available-content')
            
            if content_elem:
                text_length = len(content_elem.get_text(strip=True))
                print(f"📏 Content length: {text_length:,} characters")
                
                # Save the HTML for processing
                with open('authenticated_article.html', 'w', encoding='utf-8') as f:
                    f.write(str(content_elem))
                
                print("\n💾 Content saved to authenticated_article.html")
                
                # Import to database
                import_authenticated_content(article_url, str(content_elem))
            else:
                print("❌ Could not find content element")
        else:
            print(f"❌ Failed to fetch article: {response.status_code}")
    else:
        print("❌ Could not find cookies in cURL command")
        print("Make sure you copied the full cURL command from browser DevTools")


def import_authenticated_content(article_url: str, html_content: str):
    """Import the authenticated content to database"""
    
    db = next(get_db())
    
    try:
        # Delete old version
        old_article = db.query(SubstackArticle).filter_by(url=article_url).first()
        if old_article:
            print(f"\n🗑️ Removing old truncated version (ID: {old_article.id})")
            old_word_count = old_article.word_count
            db.delete(old_article)
            db.commit()
        else:
            old_word_count = 0
        
        # Process the HTML content
        from app.services.url_article_importer import URLArticleImporter
        importer = URLArticleImporter(db)
        
        # Clean and convert to markdown
        cleaned_html = importer._clean_article_content(html_content)
        markdown_content = importer._html_to_markdown(cleaned_html)
        markdown_content = importer._clean_markdown_footers(markdown_content)
        
        # Extract title from the article URL or content
        soup = BeautifulSoup(html_content, 'html.parser')
        title = "LLM Research Papers: The 2025 List (January to June)"
        
        # Create author
        author = importer._get_or_create_author({
            'name': 'Sebastian Raschka, PhD',
            'subdomain': 'magazine.sebastianraschka',
            'url': 'https://magazine.sebastianraschka.com'
        })
        
        # Create article
        article = SubstackArticle(
            author_id=author.id,
            title=title,
            subtitle="A topic-organized collection of 200+ LLM research papers from 2025",
            substack_id=f"authenticated_import_{datetime.now().isoformat()}",
            slug="llm-research-papers-2025-list-one",
            url=article_url,
            content_html=cleaned_html,
            content_markdown=markdown_content,
            preview=importer._generate_preview(markdown_content),
            published_at=datetime(2025, 7, 1),
            word_count=len(markdown_content.split()),
            reading_time_minutes=max(1, len(markdown_content.split()) // 200),
            processed=True,
            deleted=False
        )
        
        db.add(article)
        db.commit()
        
        print(f"\n✅ Successfully imported authenticated content!")
        print(f"📄 Title: {article.title}")
        print(f"📊 Word Count: {article.word_count:,} words")
        
        if old_word_count > 0:
            improvement = ((article.word_count - old_word_count) / old_word_count) * 100
            print(f"📈 Content Increase: +{improvement:.1f}% more words")
        
        print(f"🆔 Article ID: {article.id}")
        
        # Show the end
        print(f"\n📝 Article ending (last 500 chars):")
        print("-" * 40)
        print(markdown_content[-500:])
        print("-" * 40)
        
        # Check completeness
        if 'references' in markdown_content.lower()[-2000:]:
            print("\n✨ Article appears complete (References section found)")
        elif len(markdown_content) > 50000:
            print("\n✨ Article appears complete (very long content)")
        else:
            print("\n⚠️ Verify the article is complete")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def basic_import(article_url: str):
    """Try basic import without authentication"""
    db = next(get_db())
    try:
        importer = URLArticleImporter(db)
        result = importer.import_from_url(article_url)
        if result['success']:
            print(f"✅ Imported: {result['title']}")
            print(f"📊 Words: {result['word_count']:,}")
        else:
            print(f"❌ Failed: {result.get('error')}")
    finally:
        db.close()


if __name__ == "__main__":
    from datetime import datetime
    
    article_url = "https://magazine.sebastianraschka.com/p/llm-research-papers-2025-list-one"
    import_with_browser_session(article_url)