#!/usr/bin/env python3
"""
Login to Substack with verification code or link and import full article
"""

import sys
import requests
from app.models import get_db
from app.services.url_article_importer_auth import AuthenticatedURLImporter
from app.models.substack import SubstackArticle


def login_with_verification(code_or_link: str, article_url: str):
    """Login with verification code or link and import article"""
    
    print("=" * 60)
    print("Substack Login and Full Article Import")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    # Check if it's a link or code
    if code_or_link.startswith('http'):
        print("🔗 Using login verification link...")
        # Follow the link to authenticate
        response = session.get(code_or_link, allow_redirects=True)
        
        if response.status_code == 200:
            print("✅ Successfully authenticated via link!")
            # The session cookies should now be set
        else:
            print(f"❌ Failed to authenticate: {response.status_code}")
            return
    else:
        # It's a verification code
        code = code_or_link.replace(' ', '')  # Remove spaces from code
        print(f"🔢 Using verification code: {code}")
        
        # Extract subdomain from article URL
        from urllib.parse import urlparse
        parsed = urlparse(article_url)
        subdomain = parsed.netloc.split('.')[0] if '.substack.com' in parsed.netloc else None
        
        # Try to submit the verification code
        if subdomain:
            verify_url = f"https://{subdomain}.substack.com/api/v1/login/verify"
            base_url = f"https://{subdomain}.substack.com"
        else:
            verify_url = "https://substack.com/api/v1/login/verify"
            base_url = "https://substack.com"
        
        # Submit verification code
        response = session.post(
            verify_url,
            json={"code": code, "email": "Siegfried.Handschuh@gmail.com"},
            headers={
                "Content-Type": "application/json",
                "Origin": base_url,
                "Referer": f"{base_url}/sign-in"
            }
        )
        
        if response.status_code == 200:
            print("✅ Successfully authenticated with verification code!")
        else:
            print(f"❌ Failed to verify code: {response.status_code}")
            # Try alternative endpoint
            response = session.post(
                f"{base_url}/api/v1/email-login/verify",
                json={"token": code},
                headers={
                    "Content-Type": "application/json",
                    "Origin": base_url,
                    "Referer": f"{base_url}/sign-in"
                }
            )
            
            if response.status_code == 200:
                print("✅ Successfully authenticated with alternative method!")
            else:
                print("❌ Could not authenticate with verification code")
                return
    
    # Now import the article with the authenticated session
    print(f"\n📥 Importing full article from: {article_url}")
    
    db = next(get_db())
    
    try:
        # Delete old truncated version if exists
        old_article = db.query(SubstackArticle).filter_by(url=article_url).first()
        if old_article:
            print(f"🗑️ Removing old truncated version (ID: {old_article.id}, {old_article.word_count} words)...")
            old_word_count = old_article.word_count
            old_length = len(old_article.content_markdown)
            db.delete(old_article)
            db.commit()
        else:
            old_word_count = 0
            old_length = 0
        
        # Import with authenticated session
        importer = AuthenticatedURLImporter(db)
        importer.session = session
        
        result = importer.import_from_url(article_url, use_auth=True)
        
        if result['success']:
            print(f"\n✅ Successfully imported full article!")
            print(f"📄 Title: {result['title']}")
            print(f"✍️ Author: {result['author']}")
            print(f"📊 Word Count: {result['word_count']:,} words")
            
            if old_word_count > 0:
                improvement = ((result['word_count'] - old_word_count) / old_word_count) * 100
                print(f"📈 Content Increase: +{improvement:.1f}% ({result['word_count'] - old_word_count:,} more words)")
            
            print(f"🆔 Article ID: {result['article_id']}")
            
            # Verify we got the full content
            article = db.query(SubstackArticle).filter_by(id=result['article_id']).first()
            if article:
                new_length = len(article.content_markdown)
                if old_length > 0:
                    length_increase = ((new_length - old_length) / old_length) * 100
                    print(f"📏 Content Length: {new_length:,} chars (+{length_increase:.1f}%)")
                else:
                    print(f"📏 Content Length: {new_length:,} characters")
                
                # Show the end to verify it's complete
                print(f"\n📝 Article ending (last 500 characters):")
                print("-" * 40)
                print(article.content_markdown[-500:])
                print("-" * 40)
                
                # Check if it looks complete
                ending = article.content_markdown[-100:].lower()
                if any(phrase in ending for phrase in ['subscribe', 'thanks for reading', 'share', 'comment']):
                    print("\n✨ Article appears complete (footer content detected)")
                elif 'references' in ending or 'bibliography' in ending:
                    print("\n✨ Article appears complete (references section detected)")
                else:
                    print("\n⚠️ Article may still be truncated - check manually")
        else:
            print(f"\n❌ Import failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    # The article to import
    article_url = "https://magazine.sebastianraschka.com/p/llm-research-papers-2025-list-one"
    
    if len(sys.argv) > 1:
        # Code or link provided as argument
        code_or_link = sys.argv[1]
    else:
        # Use the verification code you provided
        code_or_link = "529690"
        # Or use the link
        # code_or_link = "https://email.mg-tx1.substack.com/c/eJxMkslyozAQhp9G3EyhZgsHDoxjyrhilEXG9lxcQhIg9gBe4Omn4ppDzt1fdf8LZ5PMu2H26y5XrSZ8w0klA0362LVtcLHleZpsmKovuWzlwCYpLmz6NXUtTyt8jrPUzVzMMtfAFjBpcYPZIssYvGS2aWvKBwNs4wXb2AbL9nRTT7GXmh63MgsszLGnO4N1E_VSIcto8tX0wPp4TceJ8UrnXaOp8ZIN8vmMPw1XqdV-MU39iMwAQYgg_L2NIGS9QhDeMILwCa2eGhGEvGv6Wk4SmeHUVbJF5qucd5hDMp-grqKye-yXwIzLDSY0H6M2rrkZ9ynYu7_ryIlKQY5tMX0loZMceya2xXe8FRVdYiJbYSSn3fi5FcWhSW6Ruit2ChRR0XymwUzKzbyngUNoNBPa12caPEhzeJzh7OzhszgvHY5hfydlUhDK1dt6159PH4qUGzOmhzleNgah1Rg1icXXkbOnHMc0MmMa2OTr51a8RGWn-DZRbzT44RdxjBRRuzEF0adq5-lZufoj7-9KjZ_Uedt7t0NdvB-heVjz-uJ-r2h2vF6Kjw83rRA4gxRqkHxC5isCG8Kia6Q2-KOSeTYoKfSCtWLkxbVAlpH_GP1Ma7ymomuYav37_a5N_wt2HeVwUcLHpuE62PZetJsP_wIAAP__ZzTUJg"
    
    print(f"🔐 Authenticating and importing article...")
    login_with_verification(code_or_link, article_url)