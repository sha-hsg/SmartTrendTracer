#!/usr/bin/env python3
"""
Test article summarization
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.substack import SubstackArticle
from app.services.article_summarizer import ArticleSummarizer

def main():
    print("=" * 60)
    print("🤖 Testing Article Summarization")
    print("=" * 60)
    
    db = next(get_db())
    
    # Get an article with content
    article = db.query(SubstackArticle).filter(
        SubstackArticle.content_markdown != None,
        SubstackArticle.deleted == False
    ).first()
    
    if not article:
        print("❌ No articles with content found")
        return
    
    print(f"\n📄 Article: {article.title[:60]}...")
    print(f"   Author: {article.author.name}")
    print(f"   Words: {article.word_count}")
    
    # Check content
    content = article.content_markdown or article.preview or ""
    print(f"   Content length: {len(content)} characters")
    print(f"   Content preview: {content[:200]}...")
    
    if len(content.strip()) < 50:
        print("❌ Content too short for summarization")
        return
    
    # Test summarization
    try:
        print("\n⏳ Generating summary...")
        summarizer = ArticleSummarizer()
        result = summarizer.summarize_article(article.id, db)
        
        print("\n✅ Summary generated successfully!")
        print("\n📝 Summary:")
        print(result['summary'][:500] + "..." if len(result['summary']) > 500 else result['summary'])
        
        print(f"\n🔑 Key Points ({len(result['key_points'])}):")
        for i, point in enumerate(result['key_points'][:3], 1):
            print(f"   {i}. {point}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    db.close()

if __name__ == "__main__":
    main()