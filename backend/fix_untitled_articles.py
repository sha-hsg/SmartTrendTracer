#\!/usr/bin/env python3
"""
Fix Untitled articles by using email subjects and proper author attribution
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, SubstackArticle, SubstackAuthor
from app.collectors.gmail_substack_collector import GmailSubstackCollector
from sqlalchemy import func

def main():
    db = SessionLocal()
    collector = GmailSubstackCollector()
    
    try:
        # Get all Untitled articles
        untitled = db.query(SubstackArticle).filter(
            SubstackArticle.title == 'Untitled'
        ).all()
        
        print(f"Found {len(untitled)} untitled articles to fix")
        
        if untitled:
            # Re-collect to get proper titles from email subjects
            print("\n🔄 Re-collecting to get proper titles...")
            
            # Search for the emails again
            queries = [
                'from:siegfried.handschuh@unisg.ch "GPT-OSS"',
                'from:siegfried.handschuh@unisg.ch "GPT-5"',
                'from:siegfried.handschuh@unisg.ch "Nathan Lambert"',
                'from:siegfried.handschuh@unisg.ch "Gary Marcus"',
            ]
            
            for query in queries:
                print(f"  Searching: {query}")
                collector.collect_newsletters(query=query, max_results=10)
            
        # Now fix author attribution based on content
        all_articles = db.query(SubstackArticle).all()
        
        print("\n🔧 Fixing author attribution...")
        
        # Get or create authors
        nathan = db.query(SubstackAuthor).filter_by(subdomain='robotic').first()
        if not nathan:
            nathan = SubstackAuthor(
                subdomain='robotic',
                name='Nathan Lambert',
                email='robotic@substack.com',
                url='https://robotic.substack.com'
            )
            db.add(nathan)
            db.flush()
        
        gary = db.query(SubstackAuthor).filter_by(subdomain='garymarcus').first()
        if not gary:
            gary = SubstackAuthor(
                subdomain='garymarcus',
                name='Gary Marcus',
                email='garymarcus@substack.com',
                url='https://garymarcus.substack.com'
            )
            db.add(gary)
            db.flush()
        
        fixes = 0
        for article in all_articles:
            content = (article.content_markdown or '') + (article.title or '')
            
            # Check for Nathan Lambert
            if ('Nathan Lambert' in content or 
                'Interconnects' in content or
                'robotic@substack.com' in content or
                'GPT-OSS' in article.title or
                ('GPT-5' in article.title and 'arc' in article.title)):
                if article.author_id \!= nathan.id:
                    print(f"  ✅ '{article.title[:50]}...' -> Nathan Lambert")
                    article.author_id = nathan.id
                    fixes += 1
            
            # Check for Gary Marcus
            elif ('Gary Marcus' in content or 
                  'Marcus on AI' in content or
                  'garymarcus@substack.com' in content or
                  'self-driving' in article.title):
                if article.author_id \!= gary.id:
                    print(f"  ✅ '{article.title[:50]}...' -> Gary Marcus")
                    article.author_id = gary.id
                    fixes += 1
        
        db.commit()
        print(f"\n✅ Fixed {fixes} articles")
        
        # Show summary
        print("\n📊 Article Summary:")
        authors_with_articles = db.query(
            SubstackAuthor.name,
            func.count(SubstackArticle.id).label('count'),
            func.avg(SubstackArticle.word_count).label('avg_words')
        ).join(
            SubstackArticle
        ).group_by(
            SubstackAuthor.name
        ).having(
            func.count(SubstackArticle.id) > 0
        ).all()
        
        for name, count, avg_words in authors_with_articles:
            print(f"  {name}: {count} articles, avg {int(avg_words or 0)} words")
        
        # List Nathan Lambert and Gary Marcus articles specifically
        print("\n📚 Nathan Lambert articles:")
        nathan_articles = db.query(SubstackArticle).filter_by(author_id=nathan.id).all()
        for article in nathan_articles:
            print(f"  - {article.title[:70]}... ({article.word_count} words)")
        
        print("\n📚 Gary Marcus articles:")
        gary_articles = db.query(SubstackArticle).filter_by(author_id=gary.id).all()
        for article in gary_articles:
            print(f"  - {article.title[:70]}... ({article.word_count} words)")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
