#!/usr/bin/env python3
"""
Collect specific Nathan Lambert articles from Gmail
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.substack import SubstackAuthor, SubstackArticle
from app.collectors.gmail_substack_collector import GmailSubstackCollector
from datetime import datetime

def main():
    print("🔍 Searching for specific Nathan Lambert articles...")
    
    db = next(get_db())
    collector = GmailSubstackCollector(db)
    
    # Authenticate with Gmail
    if not collector.authenticate():
        print("❌ Failed to authenticate with Gmail")
        return
    
    # Search for specific articles
    searches = [
        {
            'query': 'subject:"GPT-OSS" "OpenAI validates the open ecosystem"',
            'title': 'GPT-OSS: OpenAI validates the open ecosystem (finally)'
        },
        {
            'query': 'subject:"GPT-5 and the arc of progress"',
            'title': 'GPT-5 and the arc of progress'
        },
        {
            'query': '"Nathan Lambert" "GPT-OSS"',
            'title': 'GPT-OSS article'
        },
        {
            'query': '"Nathan Lambert" "GPT-5"',
            'title': 'GPT-5 article'
        },
        {
            'query': 'from:substack.com "Interconnects" "GPT"',
            'title': 'Interconnects GPT articles'
        }
    ]
    
    found_articles = []
    
    for search in searches:
        print(f"\n📧 Searching: {search['query']}")
        
        try:
            # Search for emails
            results = collector.service.users().messages().list(
                userId='me',
                q=search['query'],
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            print(f"   Found {len(messages)} messages")
            
            for msg_data in messages:
                msg_id = msg_data['id']
                
                # Get full message
                msg = collector.service.users().messages().get(
                    userId='me',
                    id=msg_id
                ).execute()
                
                # Get headers
                headers = msg['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                from_addr = next((h['value'] for h in headers if h['name'] == 'From'), '')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                
                print(f"\n   📨 Email found:")
                print(f"      Subject: {subject}")
                print(f"      From: {from_addr}")
                print(f"      Date: {date}")
                
                # Get the email body directly
                html_body = collector._extract_html_body(msg['payload'])
                
                email_data = {
                    'msg_id': msg_id,
                    'subject': subject,
                    'sender': from_addr,
                    'date': date,
                    'html_body': html_body,
                    'author': None,
                    'article': None
                }
                
                if email_data:
                    found_articles.append({
                        'msg_id': msg_id,
                        'subject': subject,
                        'from': from_addr,
                        'data': email_data
                    })
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Now process and save the found articles
    print(f"\n\n📚 Processing {len(found_articles)} found articles...")
    
    # First ensure Nathan Lambert author exists
    author = db.query(SubstackAuthor).filter(
        SubstackAuthor.name.ilike('%nathan%lambert%')
    ).first()
    
    if not author:
        # Create Nathan Lambert author
        author = SubstackAuthor(
            name="Nathan Lambert",
            subdomain="interconnects",
            url="https://interconnects.substack.com",
            description="Interconnects newsletter by Nathan Lambert"
        )
        db.add(author)
        db.commit()
        print(f"✅ Created author: {author.name}")
    else:
        print(f"✅ Found existing author: {author.name}")
    
    saved_count = 0
    
    for article_info in found_articles:
        try:
            email_data = article_info['data']
            
            # Parse the article from the email
            article_data = collector._parse_substack_html(email_data['html_body'])
            
            if article_data:
                # Check if article already exists
                existing = db.query(SubstackArticle).filter(
                    SubstackArticle.title == article_data['title'],
                    SubstackArticle.author_id == author.id
                ).first()
                
                if not existing:
                    # Create new article
                    article = SubstackArticle(
                        title=article_data['title'],
                        subtitle=article_data.get('subtitle'),
                        url=article_data.get('url'),
                        content_html=email_data['html_body'],
                        content_markdown=article_data['content_markdown'],
                        preview=article_data['preview'],
                        word_count=article_data['word_count'],
                        reading_time_minutes=article_data.get('reading_time_minutes', article_data.get('reading_time', 1)),
                        author_id=author.id,
                        published_at=datetime.now(),
                        collected_at=datetime.now()
                    )
                    db.add(article)
                    saved_count += 1
                    print(f"   ✅ Saved: {article_data['title'][:60]}...")
                else:
                    print(f"   ⚠️ Already exists: {article_data['title'][:60]}...")
                    
        except Exception as e:
            print(f"   ❌ Error processing article: {e}")
    
    db.commit()
    
    print(f"\n✅ Saved {saved_count} new articles")
    
    # Show all Nathan Lambert articles
    articles = db.query(SubstackArticle).filter(
        SubstackArticle.author_id == author.id
    ).all()
    
    print(f"\n📚 All Nathan Lambert articles ({len(articles)} total):")
    for article in articles:
        print(f"   - {article.title}")
        if article.content_markdown:
            preview = article.content_markdown[:100].replace('\n', ' ')
            print(f"     {preview}...")
    
    db.close()

if __name__ == "__main__":
    main()