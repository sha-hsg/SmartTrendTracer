#!/usr/bin/env python3
"""Collect forwarded newsletters"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector
from app.models import SessionLocal

collector = GmailSubstackCollector()
collector.authenticate()

# Search for forwarded emails with key terms
queries = [
    'from:me to:me "Interconnects"',
    'from:me to:me "Marcus on AI"',  
    'from:me to:me "Nathan Lambert"',
    'from:me to:me "Gary Marcus"',
    'from:me to:me "GPT-5"',
    'from:me to:me "GPT-OSS"'
]

print("🔍 Searching for forwarded newsletters...")
total = 0

for query in queries:
    print(f"\n🔎 {query}")
    try:
        count = collector.collect_newsletters(query=query, max_results=5)
        total += count
        if count > 0:
            print(f"  ✅ Collected {count} articles")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print(f"\n📊 Total collected: {total}")

# Show results
db = SessionLocal()
from app.models import SubstackArticle, SubstackAuthor
from sqlalchemy import func

authors_with_articles = db.query(
    SubstackAuthor.name,
    func.count(SubstackArticle.id)
).join(
    SubstackArticle, SubstackArticle.author_id == SubstackAuthor.id
).group_by(
    SubstackAuthor.name
).all()

print('\n📚 Articles by author:')
for author_name, count in authors_with_articles:
    if count > 0:
        print(f'  {author_name}: {count} articles')

# Show Nathan Lambert articles specifically
nathan = db.query(SubstackAuthor).filter(
    SubstackAuthor.name.like('%Nathan Lambert%')
).first()

if nathan:
    articles = db.query(SubstackArticle).filter_by(author_id=nathan.id).order_by(
        SubstackArticle.published_at.desc()
    ).limit(5).all()
    print(f"\n📖 Recent Nathan Lambert articles:")
    for article in articles:
        print(f"  - {article.title[:60]}... ({article.word_count} words)")

# Show Gary Marcus articles 
gary = db.query(SubstackAuthor).filter(
    SubstackAuthor.name.like('%Gary Marcus%')
).first()

if gary:
    articles = db.query(SubstackArticle).filter_by(author_id=gary.id).order_by(
        SubstackArticle.published_at.desc()
    ).limit(5).all()
    print(f"\n📖 Recent Gary Marcus articles:")
    for article in articles:
        print(f"  - {article.title[:60]}... ({article.word_count} words)")

db.close()