#!/usr/bin/env python3
"""Debug title extraction for Nathan Lambert vs others"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, SubstackArticle, SubstackAuthor

def main():
    db = SessionLocal()
    
    print("🔍 DEBUGGING TITLE EXTRACTION FOR FORWARDED EMAILS")
    print("=" * 80)
    
    # Get forwarded articles for each author
    forwarded_authors = ['Nathan Lambert', 'Gary Marcus', 'Sebastian Raschka']
    
    for author_name in forwarded_authors:
        print(f"\n👤 {author_name.upper()}:")
        
        # Find author
        author = db.query(SubstackAuthor).filter_by(name=author_name).first()
        if not author:
            print(f"   ❌ Author not found")
            continue
        
        # Get forwarded articles (gmail_ prefix)
        articles = db.query(SubstackArticle).filter_by(author_id=author.id).filter(
            SubstackArticle.substack_id.like('gmail_%')
        ).all()
        
        print(f"   Found {len(articles)} forwarded articles:")
        
        for article in articles:
            gmail_id = article.substack_id.replace('gmail_', '')
            print(f"\n   📧 Article: {article.title}")
            print(f"      Gmail ID: {gmail_id}")
            print(f"      Word count: {article.word_count}")
            
            # Check if title is generic
            is_generic = article.title in ['Untitled', 'Forwarded Newsletter']
            print(f"      Generic title: {is_generic}")
            
            if is_generic:
                print(f"      ❌ PROBLEM: Using generic title instead of email subject")
            else:
                print(f"      ✅ Good: Has proper title")
    
    print(f"\n" + "=" * 80)
    print("🔍 DETAILED ANALYSIS OF NATHAN LAMBERT ARTICLES:")
    
    # Get Nathan Lambert specifically
    nathan = db.query(SubstackAuthor).filter_by(name='Nathan Lambert').first()
    if nathan:
        nathan_articles = db.query(SubstackArticle).filter_by(author_id=nathan.id).all()
        
        from app.collectors.gmail_substack_collector import GmailSubstackCollector
        collector = GmailSubstackCollector()
        collector.authenticate()
        
        for article in nathan_articles:
            if article.substack_id and article.substack_id.startswith('gmail_'):
                gmail_id = article.substack_id.replace('gmail_', '')
                
                print(f"\n📧 Testing Gmail ID: {gmail_id}")
                print(f"   Current title: {article.title}")
                
                # Get the original email to see the subject
                try:
                    message = collector.service.users().messages().get(
                        userId='me',
                        id=gmail_id,
                        format='full'
                    ).execute()
                    
                    headers = message['payload'].get('headers', [])
                    header_dict = {h['name']: h['value'] for h in headers}
                    
                    subject = header_dict.get('Subject', '')
                    sender = header_dict.get('From', '')
                    
                    print(f"   Email subject: {subject}")
                    print(f"   Email sender: {sender}")
                    
                    # Test the current extraction logic
                    email_data = collector.get_email_content(gmail_id)
                    if email_data:
                        article_info = email_data.get('article', {})
                        extracted_title = article_info.get('title', 'No title extracted')
                        
                        print(f"   Extracted title: {extracted_title}")
                        print(f"   Extraction word count: {article_info.get('word_count', 0)}")
                        
                        # Check the title extraction logic flow
                        if extracted_title == 'Forwarded Newsletter':
                            print(f"   🔍 Title extraction failed, checking why...")
                            
                            # Check if email subject would be used as fallback
                            cleaned_subject = subject
                            for prefix in ['Fwd: ', 'FW: ', 'Re: ', 'RE: ']:
                                if cleaned_subject.startswith(prefix):
                                    cleaned_subject = cleaned_subject[len(prefix):]
                            
                            print(f"   Cleaned subject for fallback: '{cleaned_subject}'")
                            
                            # This is what should be the final title
                            final_title = extracted_title if extracted_title != 'Untitled' else cleaned_subject
                            print(f"   Should be final title: '{final_title}'")
                            
                except Exception as e:
                    print(f"   ❌ Error fetching email: {e}")
    
    db.close()

if __name__ == "__main__":
    main()