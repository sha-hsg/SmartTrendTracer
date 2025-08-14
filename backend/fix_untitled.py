#!/usr/bin/env python3
"""Fix untitled articles using email subjects"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector
from app.models import SessionLocal, SubstackArticle, SubstackAuthor
from sqlalchemy import func
import json

print('🔍 Fixing untitled articles...')

collector = GmailSubstackCollector()
db = SessionLocal()

# Load forwarded authors config
config_path = 'forwarded_authors.json'
with open(config_path, 'r') as f:
    config = json.load(f)
    forwarded_authors = config['forwarded_authors']

# First, authenticate with Gmail
print('📧 Authenticating with Gmail...')
collector.authenticate()

# Find all untitled articles
untitled_articles = db.query(SubstackArticle).filter(
    SubstackArticle.title == 'Untitled'
).all()

print(f'Found {len(untitled_articles)} untitled articles')

fixed_count = 0

for article in untitled_articles:
    # Extract Gmail ID from substack_id
    if article.substack_id and article.substack_id.startswith('gmail_'):
        gmail_id = article.substack_id.replace('gmail_', '')
        
        print(f'\n📖 Processing article ID {article.id} (Gmail: {gmail_id})')
        
        # Get the email again to extract proper title
        try:
            email_data = collector.get_email_content(gmail_id)
            
            if email_data:
                # Use email subject as title
                subject = email_data['subject']
                
                # Clean up forward prefixes
                for prefix in ['Fwd: ', 'FW: ', 'Re: ', 'RE: ']:
                    if subject.startswith(prefix):
                        subject = subject[len(prefix):]
                
                if subject and subject != 'Untitled':
                    print(f'  📝 Setting title: {subject[:60]}...')
                    article.title = subject
                    
                    # Try to identify author from content or subject
                    content = article.content_markdown or ''
                    
                    # Check for Nathan Lambert
                    if any(pattern in subject or pattern in content[:500] 
                           for pattern in ['Interconnects', 'Nathan Lambert', 'robotic']):
                        # Find or create Nathan Lambert author
                        nathan = db.query(SubstackAuthor).filter(
                            (SubstackAuthor.name.like('%Nathan Lambert%')) |
                            (SubstackAuthor.subdomain == 'robotic')
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
                        
                        article.author_id = nathan.id
                        print(f'  👤 Attributed to Nathan Lambert')
                    
                    # Check for Gary Marcus
                    elif any(pattern in subject or pattern in content[:500]
                            for pattern in ['Marcus on AI', 'Gary Marcus', 'garymarcus']):
                        # Find or create Gary Marcus author
                        gary = db.query(SubstackAuthor).filter(
                            (SubstackAuthor.name.like('%Gary Marcus%')) |
                            (SubstackAuthor.subdomain == 'garymarcus')
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
                        
                        article.author_id = gary.id
                        print(f'  👤 Attributed to Gary Marcus')
                    
                    # Check for Sebastian Raschka
                    elif any(pattern in subject or pattern in content[:500]
                            for pattern in ['Ahead of AI', 'Sebastian Raschka', 'sebastianraschka']):
                        # Find or create Sebastian Raschka author
                        sebastian = db.query(SubstackAuthor).filter(
                            (SubstackAuthor.name.like('%Sebastian Raschka%')) |
                            (SubstackAuthor.subdomain == 'sebastianraschka')
                        ).first()
                        
                        if not sebastian:
                            sebastian = SubstackAuthor(
                                subdomain='sebastianraschka',
                                name='Sebastian Raschka',
                                email='sebastianraschka@substack.com',
                                url='https://sebastianraschka.substack.com'
                            )
                            db.add(sebastian)
                            db.flush()
                        
                        article.author_id = sebastian.id
                        print(f'  👤 Attributed to Sebastian Raschka')
                    
                    fixed_count += 1
                    
        except Exception as e:
            print(f'  ❌ Error processing: {e}')

# Commit changes
if fixed_count > 0:
    db.commit()
    print(f'\n✅ Fixed {fixed_count} articles')
else:
    print('\n❌ No articles were fixed')

# Show current status
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

db.close()