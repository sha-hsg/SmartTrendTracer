#!/usr/bin/env python3
"""Debug subdomain parsing for different authors"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector

def main():
    collector = GmailSubstackCollector()
    
    # Test different email formats
    test_cases = [
        ('David Szabo-Stuban from Lumberjack <lumberjackai@substack.com>', 'lumberjackai@substack.com'),
        ('Ethan Mollick from One Useful Thing <oneusefulthing@substack.com>', 'oneusefulthing@substack.com'),
        ('Gary Marcus from Marcus on AI <garymarcus@substack.com>', 'garymarcus@substack.com'),
        ('Nathan Lambert from Interconnects <robotic@substack.com>', 'robotic@substack.com'),
    ]
    
    print("🔍 DEBUGGING SUBDOMAIN PARSING")
    print("=" * 80)
    
    for sender, expected_email in test_cases:
        print(f"\nTesting: {sender}")
        
        # Parse author info
        author_info = collector._parse_author_from_sender(sender)
        
        print(f"  Result:")
        print(f"    Name: {author_info['name']}")
        print(f"    Subdomain: {author_info['subdomain']}")
        print(f"    Email: {author_info['email']}")
        print(f"    Expected email: {expected_email}")
        print(f"    Email match: {author_info['email'] == expected_email}")
        
        # This is what would be used for database lookup
        print(f"    Database query: SubstackAuthor.filter_by(subdomain='{author_info['subdomain']}')")
    
    print(f"\n" + "=" * 80)
    print("🔍 CHECKING ACTUAL DATABASE AUTHORS:")
    
    from app.models import SessionLocal, SubstackAuthor
    db = SessionLocal()
    
    authors = db.query(SubstackAuthor).all()
    for author in authors:
        print(f"\nDatabase Author:")
        print(f"  Name: {author.name}")
        print(f"  Email: {author.email}")
        print(f"  Subdomain: {author.subdomain}")
        print(f"  Would match these parsed subdomains:")
        
        # Check which parsed emails would match this database author
        for sender, expected_email in test_cases:
            parsed = collector._parse_author_from_sender(sender)
            if parsed['subdomain'] == author.subdomain:
                print(f"    ✓ {expected_email} (subdomain: {parsed['subdomain']})")
    
    db.close()

if __name__ == "__main__":
    main()