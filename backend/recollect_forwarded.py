#!/usr/bin/env python3
"""Recollect forwarded newsletters with better parsing"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector
from app.models import SessionLocal, SubstackArticle, SubstackAuthor

print("🔍 Looking for specific forwarded newsletters...")

collector = GmailSubstackCollector()
collector.authenticate()

# Search for specific article titles
specific_searches = [
    '"GPT-OSS: OpenAI validates the open ecosystem"',
    '"GPT-5 and the arc of progress"',
    '"AI Agents have, so far, mostly been a dud"',
    '"GPT-5 hot take"',
    '"From GPT-2 to gpt-oss"',
    # Try broader searches
    'subject:"GPT-OSS" from:me to:me',
    'subject:"GPT-5" from:me to:me',
    'subject:"AI Agents" from:me to:me',
    # Try with author names
    'from:me to:me "Nathan Lambert" after:2025/1/1',
    'from:me to:me "Gary Marcus" after:2025/1/1',
    'from:me to:me "Interconnects" after:2025/1/1',
    'from:me to:me "Marcus on AI" after:2025/1/1'
]

collected = []

for query in specific_searches:
    print(f"\n🔎 Searching: {query}")
    try:
        message_ids = collector.search_substack_emails(query=query, max_results=3)
        if message_ids:
            print(f"  Found {len(message_ids)} emails")
            for msg_id in message_ids:
                email_data = collector.get_email_content(msg_id)
                if email_data:
                    subject = email_data.get('subject', 'No subject')
                    # Clean forward prefixes
                    for prefix in ['Fwd: ', 'FW: ', 'Re: ', 'RE: ']:
                        if subject.startswith(prefix):
                            subject = subject[len(prefix):]
                    
                    print(f"    - {subject[:60]}...")
                    
                    # Check if this looks like actual newsletter content
                    article_info = email_data.get('article', {})
                    if article_info:
                        word_count = article_info.get('word_count', 0)
                        if word_count > 500:  # Likely real content
                            article = collector.save_article(email_data)
                            if article:
                                collected.append((subject, word_count))
    except Exception as e:
        print(f"  ❌ Error: {e}")

print(f"\n📊 Successfully collected {len(collected)} articles with content:")
for title, words in collected:
    print(f"  - {title[:60]}... ({words} words)")

# Update attribution
db = SessionLocal()

# Get authors
nathan = db.query(SubstackAuthor).filter(
    SubstackAuthor.name == 'Nathan Lambert'
).first()

gary = db.query(SubstackAuthor).filter(
    SubstackAuthor.name == 'Gary Marcus'
).first()

# Fix any remaining attribution issues
recent_articles = db.query(SubstackArticle).filter(
    SubstackArticle.word_count < 100
).all()

print(f"\n🔧 Checking {len(recent_articles)} articles with minimal content...")

for article in recent_articles:
    if article.word_count < 100:
        print(f"  ⚠️  Low content: {article.title[:50]}... ({article.word_count} words)")
        # These might need re-collection

db.close()