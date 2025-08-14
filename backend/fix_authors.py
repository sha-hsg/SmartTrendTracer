#!/usr/bin/env python3
"""
Fix author attribution for Substack articles
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, SubstackArticle, SubstackAuthor
from sqlalchemy import func

def main():
    db = SessionLocal()
    
    try:
        # Check for articles that might be from Nathan Lambert or Gary Marcus
        # based on content
        articles = db.query(SubstackArticle).all()
        
        print("Checking articles for correct author attribution...")
        
        for article in articles:
            updated = False
            
            # Check content for author indicators
            content = (article.content_markdown or '') + (article.title or '')
            
            # Nathan Lambert / Interconnects
            if ('Nathan Lambert' in content or 
                'Interconnects' in content or
                'robotic@substack.com' in content):
                
                # Get or create Nathan Lambert author
                nathan = db.query(SubstackAuthor).filter_by(subdomain='robotic').first()
                if not nathan:
                    nathan = SubstackAuthor(
                        subdomain='robotic',
                        name='Nathan Lambert from Interconnects',
                        email='robotic@substack.com',
                        url='https://robotic.substack.com'
                    )
                    db.add(nathan)
                    db.flush()
                
                if article.author_id != nathan.id:
                    print(f"  Fixing: '{article.title[:50]}...' -> Nathan Lambert")
                    article.author_id = nathan.id
                    updated = True
            
            # Gary Marcus / Marcus on AI
            elif ('Gary Marcus' in content or 
                  'Marcus on AI' in content or
                  'garymarcus@substack.com' in content):
                
                # Get or create Gary Marcus author
                gary = db.query(SubstackAuthor).filter_by(subdomain='garymarcus').first()
                if not gary:
                    gary = SubstackAuthor(
                        subdomain='garymarcus',
                        name='Gary Marcus from Marcus on AI',
                        email='garymarcus@substack.com',
                        url='https://garymarcus.substack.com'
                    )
                    db.add(gary)
                    db.flush()
                
                if article.author_id != gary.id:
                    print(f"  Fixing: '{article.title[:50]}...' -> Gary Marcus")
                    article.author_id = gary.id
                    updated = True
            
            # Sebastian Raschka / Ahead of AI
            elif ('Sebastian Raschka' in content or 
                  'Ahead of AI' in content or
                  'sebastianraschka@substack.com' in content):
                
                # Get or create Sebastian Raschka author
                sebastian = db.query(SubstackAuthor).filter_by(subdomain='sebastianraschka').first()
                if not sebastian:
                    sebastian = SubstackAuthor(
                        subdomain='sebastianraschka',
                        name='Sebastian Raschka from Ahead of AI',
                        email='sebastianraschka@substack.com',
                        url='https://sebastianraschka.substack.com'
                    )
                    db.add(sebastian)
                    db.flush()
                
                if article.author_id != sebastian.id:
                    print(f"  Fixing: '{article.title[:50]}...' -> Sebastian Raschka")
                    article.author_id = sebastian.id
                    updated = True
        
        db.commit()
        
        # Show summary
        print("\n📊 Author Summary:")
        authors = db.query(SubstackAuthor).all()
        for author in authors:
            if any(name in author.name for name in ['Nathan', 'Gary', 'Sebastian', 'Ethan']):
                count = db.query(SubstackArticle).filter_by(author_id=author.id).count()
                if count > 0:
                    avg_words = db.query(SubstackArticle).filter_by(
                        author_id=author.id
                    ).filter(SubstackArticle.word_count > 0).with_entities(
                        func.avg(SubstackArticle.word_count)
                    ).scalar()
                    print(f"  {author.name}: {count} articles, avg {int(avg_words or 0)} words")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()