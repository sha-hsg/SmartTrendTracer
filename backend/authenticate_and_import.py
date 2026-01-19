#!/usr/bin/env python3
"""
Authenticate with magic link and import full article
"""

import sys
from app.models import get_db
from app.services.substack_auth_service import SubstackAuthService
from app.services.url_article_importer_auth import AuthenticatedURLImporter
from app.models.substack import SubstackArticle


def authenticate_and_import(magic_link: str, article_url: str):
    """Authenticate with magic link and import article with full content"""
    
    print("=" * 60)
    print("Authenticating and Importing Full Article")
    print("=" * 60)
    
    # Step 1: Authenticate with the magic link
    auth_service = SubstackAuthService()
    
    print("🔐 Authenticating with magic link...")
    success = auth_service.authenticate_with_link(magic_link)
    
    if not success:
        print("❌ Authentication failed. Trying alternative method...")
        # Try just following the link
        response = auth_service.session.get(magic_link, allow_redirects=True)
        if response.status_code == 200:
            print("✅ Magic link followed successfully")
            success = True
    
    if success:
        # Save session for future use
        auth_service.save_session('substack_session.json')
        
        # Step 2: Import the article with authentication
        db = next(get_db())
        
        try:
            # Delete old truncated version if exists
            old_article = db.query(SubstackArticle).filter_by(url=article_url).first()
            if old_article:
                print(f"\n🗑️ Removing old truncated version (ID: {old_article.id})...")
                old_word_count = old_article.word_count
                db.delete(old_article)
                db.commit()
            else:
                old_word_count = 0
            
            print(f"\n📥 Importing article with full subscriber content...")
            print(f"🔗 URL: {article_url}")
            
            # Use authenticated session for import
            importer = AuthenticatedURLImporter(db)
            importer.session = auth_service.get_authenticated_session()
            
            result = importer.import_from_url(article_url, use_auth=True)
            
            if result['success']:
                print(f"\n✅ Successfully imported full article!")
                print(f"📄 Title: {result['title']}")
                print(f"✍️ Author: {result['author']}")
                print(f"📊 Word Count: {result['word_count']:,} words")
                if old_word_count > 0:
                    improvement = ((result['word_count'] - old_word_count) / old_word_count) * 100
                    print(f"📈 Content Increase: {improvement:.1f}% more content than truncated version")
                print(f"🆔 Article ID: {result['article_id']}")
                
                # Show the end of the article to verify it's complete
                article = db.query(SubstackArticle).filter_by(id=result['article_id']).first()
                if article:
                    print(f"\n📝 Article ending (last 500 characters):")
                    print("-" * 40)
                    print(article.content_markdown[-500:])
                    print("-" * 40)
                    print(f"\n✨ Total content length: {len(article.content_markdown):,} characters")
            else:
                print(f"\n❌ Import failed: {result['error']}")
                
        except Exception as e:
            print(f"\n❌ Error during import: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()
    else:
        print("❌ Could not authenticate with the provided magic link")
        print("Please make sure you copied the entire URL from the email")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python authenticate_and_import.py '<magic_link>' '<article_url>'")
        print("\nExample:")
        print("python authenticate_and_import.py 'https://substack.com/sign-in#eyJ...' 'https://magazine.sebastianraschka.com/p/llm-research-papers-2025-list-one'")
        sys.exit(1)
    
    magic_link = sys.argv[1]
    article_url = sys.argv[2]
    
    authenticate_and_import(magic_link, article_url)