#!/usr/bin/env python3
"""Debug forwarded email content extraction"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector
from app.models import SessionLocal, SubstackArticle

def main():
    collector = GmailSubstackCollector()
    collector.authenticate()
    
    # Get a failing article to find its original email
    db = SessionLocal()
    
    # Get one of the empty Gary Marcus articles
    article = db.query(SubstackArticle).filter(
        SubstackArticle.title == "GPT-5 hot take"
    ).first()
    
    if not article:
        print("Article not found")
        return
    
    print(f"Debugging article: {article.title}")
    print(f"Substack ID: {article.substack_id}")
    print(f"Word count: {article.word_count}")
    print(f"Content length: {len(article.content_markdown or '')}")
    
    # Extract Gmail ID from substack_id
    if article.substack_id and article.substack_id.startswith('gmail_'):
        gmail_id = article.substack_id.replace('gmail_', '')
        
        print(f"\nFetching original email: {gmail_id}")
        
        # Get the raw email content
        email_data = collector.get_email_content(gmail_id)
        
        if email_data:
            print("\n" + "="*60)
            print("EMAIL METADATA:")
            print(f"Subject: {email_data['subject']}")
            print(f"Sender: {email_data['sender']}")
            print(f"Date: {email_data['date']}")
            
            print("\n" + "="*60)  
            print("AUTHOR INFO:")
            author_info = email_data.get('author', {})
            print(f"Name: {author_info.get('name')}")
            print(f"Subdomain: {author_info.get('subdomain')}")
            print(f"Email: {author_info.get('email')}")
            
            print("\n" + "="*60)
            print("ARTICLE EXTRACTION:")
            article_info = email_data.get('article', {})
            print(f"Title: {article_info.get('title')}")
            print(f"Word count: {article_info.get('word_count')}")
            print(f"Content length: {len(article_info.get('content_markdown', ''))}")
            
            # Show more of the HTML body to find the actual content
            html_body = email_data.get('html_body', '')
            print(f"\n" + "="*60)
            print("RAW HTML (first 2000 chars):")
            print(html_body[:2000])
            print("...")
            
            if len(html_body) > 2000:
                print(f"\n" + "="*60)
                print("RAW HTML (middle section):")
                mid_start = len(html_body) // 2 - 1000
                mid_end = len(html_body) // 2 + 1000
                print(html_body[mid_start:mid_end])
                print("...")
            
            # Show first 500 chars of extracted content
            content = article_info.get('content_markdown', '')
            print(f"\n" + "="*60)
            print("EXTRACTED CONTENT (first 500 chars):")
            print(repr(content[:500]))
            
            # Try to find any text content in the HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_body, 'html.parser')
            all_text = soup.get_text(strip=True)
            print(f"\n" + "="*60)
            print("ALL TEXT CONTENT (first 1000 chars):")
            print(all_text[:1000])
            
        else:
            print("Failed to fetch email")
    
    db.close()

if __name__ == "__main__":
    main()