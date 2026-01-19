#!/usr/bin/env python3
"""
Import Substack articles with authentication for full content
"""

import sys
import os
from app.models import get_db
from app.services.substack_auth_service import SubstackAuthService
from app.services.url_article_importer_auth import AuthenticatedURLImporter
from app.models.substack import SubstackArticle


def main():
    """Interactive import with authentication"""
    
    print("=" * 60)
    print("Substack Article Import with Authentication")
    print("=" * 60)
    
    # Step 1: Get email and send magic link
    email = input("Enter your Substack email (or press Enter to skip auth): ").strip()
    
    if email:
        auth_service = SubstackAuthService()
        
        # Extract subdomain from article URL if provided
        url = input("Enter the article URL you want to import: ").strip()
        
        # Get subdomain from URL
        from urllib.parse import urlparse
        parsed = urlparse(url)
        subdomain = parsed.netloc.split('.')[0] if '.substack.com' in parsed.netloc else None
        
        print(f"\n📧 Requesting magic link for {email}...")
        result = auth_service.request_magic_link(email, subdomain)
        
        if result['success']:
            print(f"✅ {result['message']}")
            print("\n⏳ Please check your email and find the magic link.")
            print("You can either:")
            print("1. Copy the entire magic link URL from the email")
            print("2. Copy just the verification code/token")
            print()
            
            magic_input = input("Paste the magic link URL or verification code: ").strip()
            
            # Try to authenticate
            if magic_input.startswith('http'):
                # Full URL provided
                success = auth_service.authenticate_with_link(magic_input)
            else:
                # Just token/code provided
                success = auth_service.authenticate_with_token(magic_input)
            
            if success:
                print("✅ Authentication successful!")
                
                # Save session for future use
                session_file = 'substack_session.json'
                auth_service.save_session(session_file)
                
                # Import the article with authentication
                db = next(get_db())
                
                try:
                    # Delete old version if exists
                    old_article = db.query(SubstackArticle).filter_by(url=url).first()
                    if old_article:
                        print(f"\n🗑️ Removing old truncated version...")
                        db.delete(old_article)
                        db.commit()
                    
                    print(f"\n📥 Importing article with full content...")
                    importer = AuthenticatedURLImporter(db)
                    importer.session = auth_service.get_authenticated_session()
                    
                    result = importer.import_from_url(url, use_auth=True)
                    
                    if result['success']:
                        print(f"\n✅ Successfully imported!")
                        print(f"📄 Title: {result['title']}")
                        print(f"✍️ Author: {result['author']}")
                        print(f"📊 Word Count: {result['word_count']:,} words")
                        print(f"📖 Full Content: {'Yes' if result.get('full_content') else 'Partial'}")
                        
                        # Show preview of content
                        article = db.query(SubstackArticle).filter_by(id=result['article_id']).first()
                        if article:
                            print(f"\n📝 Content Preview (last 500 chars):")
                            print("-" * 40)
                            print(article.content_markdown[-500:])
                            print("-" * 40)
                    else:
                        print(f"\n❌ Import failed: {result['error']}")
                        
                except Exception as e:
                    print(f"\n❌ Error during import: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    db.close()
            else:
                print("❌ Authentication failed. Please check the magic link and try again.")
        else:
            print(f"❌ {result['error']}")
    else:
        # Import without authentication
        print("\n⚠️ Proceeding without authentication (content may be truncated)")
        url = input("Enter the article URL to import: ").strip()
        
        if url:
            db = next(get_db())
            try:
                from app.services.url_article_importer import URLArticleImporter
                importer = URLArticleImporter(db)
                result = importer.import_from_url(url)
                
                if result['success']:
                    print(f"\n✅ Imported: {result['title']}")
                    print(f"📊 Word Count: {result['word_count']:,} words")
                else:
                    print(f"\n❌ Failed: {result['error']}")
            finally:
                db.close()


if __name__ == "__main__":
    main()