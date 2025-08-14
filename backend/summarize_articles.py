#!/usr/bin/env python3
"""
Test article summarization functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.services.article_summarizer import ArticleSummarizer
from app.models.substack import SubstackArticle

def main():
    print("=" * 60)
    print("📝 Article Summarization Test")
    print("=" * 60)
    
    db = next(get_db())
    summarizer = ArticleSummarizer()
    
    # Get unsummarized articles
    unsummarized = db.query(SubstackArticle).filter(
        SubstackArticle.summarized == False,
        SubstackArticle.deleted == False
    ).limit(5).all()
    
    if not unsummarized:
        print("\n✅ All articles are already summarized!")
        return
    
    print(f"\n📚 Found {len(unsummarized)} unsummarized articles")
    
    for i, article in enumerate(unsummarized, 1):
        print(f"\n{i}. {article.title[:60]}...")
        print(f"   Author: {article.author.name}")
        print(f"   Words: {article.word_count}")
        
        try:
            print("   ⏳ Generating summary...")
            result = summarizer.summarize_article(article.id, db)
            print("   ✅ Summary generated!")
            print(f"   Key points: {len(result['key_points'])}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    main()