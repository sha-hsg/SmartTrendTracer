#!/usr/bin/env python3
"""
Authenticate directly with a specific Substack publication and import full article
"""

import requests
from bs4 import BeautifulSoup
from app.models import get_db
from app.services.url_article_importer_auth import AuthenticatedURLImporter
from app.models.substack import SubstackArticle


def authenticate_and_import_publication(article_url: str):
    """
    Try to authenticate directly with the publication
    """
    print("=" * 60)
    print("Publication-Specific Authentication")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    # First, visit the article page to get the sign-in URL
    print(f"📥 Visiting article page: {article_url}")
    response = session.get(article_url)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the sign-in button/link
    sign_in_link = None
    sign_in_button = soup.find('button', {'native': True, 'data-href': True})
    if sign_in_button:
        sign_in_link = sign_in_button.get('data-href')
    
    if not sign_in_link:
        # Try alternative selectors
        sign_in_elem = soup.find('a', string='Sign in')
        if sign_in_elem:
            sign_in_link = sign_in_elem.get('href')
    
    if sign_in_link:
        print(f"🔗 Found sign-in link: {sign_in_link}")
        
        # Request magic link for this specific publication
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(sign_in_link)
        params = parse_qs(parsed.query)
        
        # The publication info should be in the params
        for_pub = params.get('for_pub', [None])[0]
        redirect_path = params.get('redirect', [None])[0]
        
        if for_pub:
            print(f"📰 Publication: {for_pub}")
            
            # Request magic link for this specific publication
            magic_link_url = f"https://{for_pub}.substack.com/api/v1/email-login"
            
            print(f"\n📧 Requesting magic link for {for_pub}.substack.com...")
            print(f"Email: Siegfried.Handschuh@gmail.com")
            
            response = session.post(
                magic_link_url,
                json={"email": "Siegfried.Handschuh@gmail.com"},
                headers={
                    "Content-Type": "application/json",
                    "Origin": f"https://{for_pub}.substack.com",
                    "Referer": sign_in_link
                }
            )
            
            if response.status_code in [200, 201]:
                print("\n✅ Magic link requested for this specific publication!")
                print("\n📋 Next Steps:")
                print("1. Check your email for a NEW magic link from 'Ahead of AI'")
                print("2. This link will be specifically for magazine.sebastianraschka.com")
                print("3. Copy the entire URL from that email")
                print("4. Run: python complete_auth_import.py '<magic_link>' '<article_url>'")
                print("\n⚠️ Important: Use the NEW magic link, not the previous one!")
                
                # Save session info for next step
                import json
                session_data = {
                    'for_pub': for_pub,
                    'article_url': article_url,
                    'redirect_path': redirect_path
                }
                with open('session_info.json', 'w') as f:
                    json.dump(session_data, f)
                print("\n💾 Session info saved for next step")
                
                return True
            else:
                print(f"❌ Failed to request magic link: {response.status_code}")
                print(f"Response: {response.text[:500]}")
    else:
        print("❌ Could not find sign-in link on page")
        
        # Check if we're already seeing the full content
        content_elem = soup.select_one('div.body.markup')
        if content_elem:
            text_length = len(content_elem.get_text(strip=True))
            print(f"\n📏 Content found: {text_length:,} characters")
            
            # Check for paywall
            if soup.select_one('.paywall'):
                print("🔒 Paywall detected - need authentication")
            else:
                print("✅ No paywall detected - might have full content")
    
    return False


def complete_import_with_auth(magic_link: str, article_url: str):
    """
    Complete the import after authenticating with the publication-specific magic link
    """
    print("=" * 60)
    print("Completing Import with Publication Auth")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    # Follow the magic link
    print("🔐 Following magic link...")
    response = session.get(magic_link, allow_redirects=True)
    
    if response.status_code == 200:
        print("✅ Magic link followed successfully")
        
        # Now fetch the article with the authenticated session
        print(f"\n📥 Fetching article with authentication...")
        response = session.get(article_url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check if paywall is gone
            if soup.select_one('.paywall'):
                print("⚠️ Paywall still present - checking content...")
            else:
                print("✅ No paywall detected!")
            
            # Get the content
            content_elem = soup.select_one('div.body.markup') or soup.select_one('div.available-content')
            if content_elem:
                text_length = len(content_elem.get_text(strip=True))
                print(f"📏 Content length: {text_length:,} characters")
                
                # Import the article
                db = next(get_db())
                
                try:
                    # Delete old version
                    old_article = db.query(SubstackArticle).filter_by(url=article_url).first()
                    if old_article:
                        print(f"\n🗑️ Removing old version (ID: {old_article.id})")
                        old_length = len(old_article.content_markdown)
                        db.delete(old_article)
                        db.commit()
                    else:
                        old_length = 0
                    
                    # Import with authenticated session
                    importer = AuthenticatedURLImporter(db)
                    importer.session = session
                    
                    result = importer.import_from_url(article_url, use_auth=True)
                    
                    if result['success']:
                        print(f"\n✅ Import successful!")
                        print(f"📄 Title: {result['title']}")
                        print(f"📊 Word Count: {result['word_count']:,} words")
                        
                        # Check improvement
                        article = db.query(SubstackArticle).filter_by(id=result['article_id']).first()
                        if article and old_length > 0:
                            new_length = len(article.content_markdown)
                            improvement = ((new_length - old_length) / old_length) * 100
                            print(f"📈 Content increase: +{improvement:.1f}%")
                            
                            # Show the end
                            print(f"\n📝 Article ending (last 500 chars):")
                            print("-" * 40)
                            print(article.content_markdown[-500:])
                            print("-" * 40)
                    else:
                        print(f"❌ Import failed: {result.get('error')}")
                        
                except Exception as e:
                    print(f"❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    db.close()
            else:
                print("❌ Could not find content element")
    else:
        print(f"❌ Failed to follow magic link: {response.status_code}")


if __name__ == "__main__":
    import sys
    
    article_url = "https://magazine.sebastianraschka.com/p/llm-research-papers-2025-list-one"
    
    if len(sys.argv) > 1:
        # Magic link provided
        magic_link = sys.argv[1]
        complete_import_with_auth(magic_link, article_url)
    else:
        # Request new magic link
        authenticate_and_import_publication(article_url)