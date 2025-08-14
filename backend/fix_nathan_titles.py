#!/usr/bin/env python3
"""Fix Nathan Lambert article titles to use email subjects"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, SubstackArticle, SubstackAuthor
from app.collectors.gmail_substack_collector import GmailSubstackCollector

def main():
    db = SessionLocal()
    collector = GmailSubstackCollector()
    collector.authenticate()
    
    print("🔧 FIXING NATHAN LAMBERT ARTICLE TITLES")
    print("=" * 60)
    
    # Find Nathan Lambert
    nathan = db.query(SubstackAuthor).filter_by(name='Nathan Lambert').first()
    if not nathan:
        print("❌ Nathan Lambert not found")
        return
    
    # Get his articles with generic titles
    generic_articles = db.query(SubstackArticle).filter_by(author_id=nathan.id).filter(
        SubstackArticle.title == 'Forwarded Newsletter'
    ).all()
    
    print(f"Found {len(generic_articles)} Nathan Lambert articles with generic titles")
    
    # Update each article
    updated_count = 0
    for article in generic_articles:
        if not article.substack_id or not article.substack_id.startswith('gmail_'):
            print(f"  ⚠️  Skipping non-Gmail article: {article.title}")
            continue
        
        gmail_id = article.substack_id.replace('gmail_', '')
        
        print(f"\n📧 Updating article: {gmail_id}")
        print(f"   Current title: {article.title}")
        
        try:
            # Get email subject
            message = collector.service.users().messages().get(
                userId='me',
                id=gmail_id,
                format='full'
            ).execute()
            
            headers = message['payload'].get('headers', [])
            header_dict = {h['name']: h['value'] for h in headers}
            
            subject = header_dict.get('Subject', '')
            print(f"   Email subject: {subject}")
            
            # Clean up subject (remove forward prefixes)
            cleaned_subject = subject
            for prefix in ['Fwd: ', 'FW: ', 'Re: ', 'RE: ']:
                if cleaned_subject.startswith(prefix):
                    cleaned_subject = cleaned_subject[len(prefix):]
            
            print(f"   Cleaned subject: {cleaned_subject}")
            
            if cleaned_subject and cleaned_subject != article.title:
                article.title = cleaned_subject
                updated_count += 1
                print(f"   ✅ Updated to: {cleaned_subject}")
            else:
                print(f"   ⚪ No change needed")
                
        except Exception as e:
            print(f"   ❌ Error fetching email: {e}")
    
    if updated_count > 0:
        db.commit()
        print(f"\n✅ Updated {updated_count} article titles")
    else:
        print(f"\n⚪ No titles needed updating")
    
    # Show final state
    print(f"\n📊 Final Nathan Lambert articles:")
    all_nathan_articles = db.query(SubstackArticle).filter_by(author_id=nathan.id).all()
    for article in all_nathan_articles:
        print(f"  - {article.title}")
    
    db.close()

if __name__ == "__main__":
    main()