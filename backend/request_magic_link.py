#!/usr/bin/env python3
"""
Request a Substack magic link for authentication
"""

from app.services.substack_auth_service import SubstackAuthService

def request_magic_link(email: str, article_url: str = None):
    """Request magic link for Substack authentication"""
    
    print("=" * 60)
    print("Requesting Substack Magic Link")
    print("=" * 60)
    
    auth_service = SubstackAuthService()
    
    # Extract subdomain if article URL provided
    subdomain = None
    if article_url:
        from urllib.parse import urlparse
        parsed = urlparse(article_url)
        if '.substack.com' in parsed.netloc:
            subdomain = parsed.netloc.split('.')[0]
            print(f"📰 Publication: {subdomain}")
    
    print(f"📧 Email: {email}")
    print(f"🔗 Requesting magic link...")
    
    result = auth_service.request_magic_link(email, subdomain)
    
    if result['success']:
        print(f"\n✅ {result['message']}")
        print("\n📋 Next Steps:")
        print("1. Check your email for the magic link from Substack")
        print("2. Copy the entire URL from the email")
        print("3. Run: python authenticate_and_import.py '<magic_link_url>' '<article_url>'")
    else:
        print(f"\n❌ {result['error']}")
    
    return result['success'] if result else False


if __name__ == "__main__":
    # Your email
    email = "Siegfried.Handschuh@gmail.com"
    
    # The article you want to import
    article_url = "https://magazine.sebastianraschka.com/p/llm-research-papers-2025-list-one"
    
    request_magic_link(email, article_url)