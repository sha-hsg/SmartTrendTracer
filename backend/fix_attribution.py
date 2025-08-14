#!/usr/bin/env python3
"""Fix author attribution for articles"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, SubstackArticle, SubstackAuthor
from sqlalchemy import func

db = SessionLocal()

# Find articles without proper author attribution
unattributed = db.query(SubstackArticle).filter(
    SubstackArticle.author_id.in_(
        db.query(SubstackAuthor.id).filter(
            (SubstackAuthor.name == '') |
            (SubstackAuthor.name == None) |
            (SubstackAuthor.name == 'siegfried.handschuh@unisg.ch')
        )
    )
).all()

print(f"Found {len(unattributed)} articles needing attribution")

# Get or create proper authors
nathan = db.query(SubstackAuthor).filter(
    SubstackAuthor.name == 'Nathan Lambert'
).first()

if not nathan:
    nathan = SubstackAuthor(
        subdomain='robotic',
        name='Nathan Lambert',
        email='robotic@substack.com',
        url='https://robotic.substack.com'
    )
    db.add(nathan)
    db.flush()

gary = db.query(SubstackAuthor).filter(
    SubstackAuthor.name == 'Gary Marcus'
).first()

if not gary:
    gary = SubstackAuthor(
        subdomain='garymarcus',
        name='Gary Marcus',
        email='garymarcus@substack.com',
        url='https://garymarcus.substack.com'
    )
    db.add(gary)
    db.flush()

# Fix attribution based on content
for article in unattributed:
    title = article.title or ''
    content = (article.content_markdown or '')[:1000]
    
    # Check for Nathan Lambert / Interconnects
    if any(marker in title + content for marker in [
        'Interconnects', 'Nathan Lambert', 'robotic@substack', 'GPT-OSS', 'GPT-5 and the arc'
    ]):
        print(f"  Attributing to Nathan Lambert: {title[:50]}...")
        article.author_id = nathan.id
    
    # Check for Gary Marcus
    elif any(marker in title + content for marker in [
        'Marcus on AI', 'Gary Marcus', 'garymarcus@substack', 'AI Agents have', 'GPT-5 hot take'
    ]):
        print(f"  Attributing to Gary Marcus: {title[:50]}...")
        article.author_id = gary.id

db.commit()

# Delete empty author entries
empty_authors = db.query(SubstackAuthor).filter(
    (SubstackAuthor.name == '') |
    (SubstackAuthor.name == None)
).all()

for author in empty_authors:
    # First reassign any articles
    articles = db.query(SubstackArticle).filter_by(author_id=author.id).all()
    for article in articles:
        # Try to determine correct author
        if 'Nathan' in (article.title or '') or 'Interconnects' in (article.title or ''):
            article.author_id = nathan.id
        elif 'Marcus' in (article.title or ''):
            article.author_id = gary.id
    
    db.delete(author)

db.commit()

# Show updated stats
authors_with_articles = db.query(
    SubstackAuthor.name,
    func.count(SubstackArticle.id)
).join(
    SubstackArticle, SubstackArticle.author_id == SubstackAuthor.id
).group_by(
    SubstackAuthor.name
).all()

print('\n📚 Updated articles by author:')
for author_name, count in authors_with_articles:
    if count > 0:
        print(f'  {author_name}: {count} articles')

# Show specific Nathan Lambert articles
nathan_articles = db.query(SubstackArticle).filter_by(author_id=nathan.id).order_by(
    SubstackArticle.published_at.desc()
).limit(5).all()

print(f"\n📖 Nathan Lambert articles ({len(nathan_articles)} total):")
for article in nathan_articles:
    print(f"  - {article.title[:60]}... ({article.word_count} words)")

# Show specific Gary Marcus articles
gary_articles = db.query(SubstackArticle).filter_by(author_id=gary.id).order_by(
    SubstackArticle.published_at.desc()
).limit(5).all()

print(f"\n📖 Gary Marcus articles ({len(gary_articles)} total):")
for article in gary_articles:
    print(f"  - {article.title[:60]}... ({article.word_count} words)")

db.close()