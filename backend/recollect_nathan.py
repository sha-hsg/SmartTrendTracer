#!/usr/bin/env python3
"""
Recollect Nathan Lambert's Substack articles
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.collectors.gmail_substack_collector import GmailSubstackCollector

def main():
    print("🔍 Recollecting Nathan Lambert's Interconnects newsletter...")
    
    db = next(get_db())
    collector = GmailSubstackCollector(db)
    
    # Authenticate with Gmail
    if not collector.authenticate():
        print("❌ Failed to authenticate with Gmail")
        return
    
    # Search specifically for Nathan Lambert / Interconnects
    queries = [
        'from:nathan@interconnects.ai',
        'from:noreply@substack.com "Interconnects"',
        'from:substack.com "Nathan Lambert"',
        'subject:"Interconnects" from:substack.com'
    ]
    
    total_collected = 0
    
    for query in queries:
        print(f"\n📧 Searching: {query}")
        
        try:
            # Search for emails
            message_ids = collector.search_substack_emails(query, max_results=10)
            print(f"   Found {len(message_ids)} emails")
            
            if not message_ids:
                continue
            
            # Process each email
            for msg_id in message_ids:
                try:
                    # Get the email
                    msg = collector.service.users().messages().get(
                        userId='me',
                        id=msg_id
                    ).execute()
                    
                    # Parse it
                    article_data = collector.parse_substack_email(msg)
                    
                    if article_data:
                        # Check if it's actually Nathan Lambert
                        if 'interconnects' in article_data.get('author_subdomain', '').lower() or \
                           'nathan' in article_data.get('author_name', '').lower() or \
                           'interconnects' in article_data.get('title', '').lower():
                            
                            # Save to database
                            saved = collector.save_article(article_data)
                            if saved:
                                print(f"   ✅ Saved: {article_data.get('title', 'Untitled')[:60]}...")
                                total_collected += 1
                            else:
                                print(f"   ⚠️ Already exists: {article_data.get('title', 'Untitled')[:60]}...")
                        
                except Exception as e:
                    print(f"   ❌ Error processing message: {e}")
                    
        except Exception as e:
            print(f"   ❌ Search error: {e}")
    
    db.commit()
    print(f"\n✅ Collected {total_collected} new articles from Nathan Lambert")
    
    # Show what we have now
    from app.models.substack import SubstackAuthor, SubstackArticle
    
    author = db.query(SubstackAuthor).filter(
        SubstackAuthor.name.ilike('%nathan%lambert%')
    ).first()
    
    if author:
        article_count = db.query(SubstackArticle).filter(
            SubstackArticle.author_id == author.id
        ).count()
        print(f"\n📚 Total articles for {author.name}: {article_count}")
    
    db.close()

if __name__ == "__main__":
    main()