"""
Test script for enhanced article tag suggestions
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.substack import SubstackArticle
from app.services.llm_service import get_llm_service

def test_article_tag_suggestions():
    """Test the enhanced article tag suggestion system"""
    
    print("=" * 80)
    print("ARTICLE TAG SUGGESTION TEST")
    print("=" * 80)
    
    # Get database session
    db = next(get_db())
    
    # Get a sample article
    article = db.query(SubstackArticle).filter(
        SubstackArticle.content_markdown.isnot(None)
    ).first()
    
    if not article:
        print("No articles with content found in database")
        db.close()
        return
    
    print(f"\n📄 Testing with article: {article.title}")
    print(f"   Author: {article.author.name if article.author else 'Unknown'}")
    print(f"   Content length: {len(article.content_markdown) if article.content_markdown else 0} chars")
    
    # Prepare article text similar to the API
    article_text = f"{article.title}\n"
    if article.subtitle:
        article_text += f"{article.subtitle}\n"
    
    if article.content_markdown:
        # Use the enhanced content selection strategy
        content_length = min(5000, len(article.content_markdown))
        article_text += article.content_markdown[:content_length]
        
        if len(article.content_markdown) > 5000:
            # Add middle section
            mid_point = len(article.content_markdown) // 2
            article_text += "\n...\n" + article.content_markdown[mid_point:mid_point+1000]
            
            # Add conclusion
            article_text += "\n...\n" + article.content_markdown[-1000:]
    
    print(f"   Text prepared for analysis: {len(article_text)} chars")
    
    # Test the LLM service
    llm_service = get_llm_service()
    
    print("\n1. Testing Tweet Tag Suggestion (old method, limited):")
    print("-" * 40)
    
    try:
        tweet_tags = llm_service.suggest_tags(
            tweet_text=article_text[:500],  # Limited input
            author=article.author.name if article.author else "Unknown"
        )
        
        # Remove API marker
        if "__api_success__" in tweet_tags:
            tweet_tags.remove("__api_success__")
            api_used = True
        else:
            api_used = False
        
        print(f"   Tags generated: {len(tweet_tags)}")
        print(f"   API used: {api_used}")
        print(f"   Tags: {tweet_tags}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n2. Testing Article Tag Suggestion (new method, comprehensive):")
    print("-" * 40)
    
    try:
        article_tags = llm_service.suggest_article_tags(
            article_text=article_text,  # Full content
            author=article.author.name if article.author else "Unknown",
            max_tags=10
        )
        
        # Remove API marker
        if "__api_success__" in article_tags:
            article_tags.remove("__api_success__")
            api_used = True
        else:
            api_used = False
        
        print(f"   Tags generated: {len(article_tags)}")
        print(f"   API used: {api_used}")
        print(f"   Tags: {article_tags}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test with different max_tags values
    print("\n3. Testing with different max_tags values:")
    print("-" * 40)
    
    for max_tags in [5, 7, 10, 15]:
        try:
            tags = llm_service.suggest_article_tags(
                article_text=article_text,
                author=article.author.name if article.author else "Unknown",
                max_tags=max_tags
            )
            
            if "__api_success__" in tags:
                tags.remove("__api_success__")
            
            print(f"   max_tags={max_tags}: Generated {len(tags)} tags")
            
        except Exception as e:
            print(f"   max_tags={max_tags}: Error - {e}")
    
    # Test vector similarity search
    print("\n4. Testing Vector Similarity Search for existing tags:")
    print("-" * 40)
    
    try:
        from app.services.vector_store_openai import get_vector_store
        
        vector_store = get_vector_store()
        
        # Search with different k values
        for k in [5, 10, 15]:
            search_results = vector_store.search_similar_tags(
                query_text=article_text,
                k=k,
                min_similarity=0.40  # Lower threshold for articles
            )
            
            print(f"   k={k}: Found {len(search_results)} similar tags")
            if search_results[:3]:  # Show top 3
                for tag, score, count in search_results[:3]:
                    print(f"      - '{tag}' (score: {score:.3f}, used: {count}x)")
    
    except Exception as e:
        print(f"   Error with vector search: {e}")
    
    db.close()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nSummary:")
    print("- Articles can now receive up to 10 tags from LLM (vs 5 for tweets)")
    print("- Articles can receive up to 10 similar existing tags (vs 5 for tweets)")
    print("- Article content analysis uses up to 7000 chars (vs 500 for tweets)")
    print("- Total potential tags per article: 20 (10 new + 10 existing)")

if __name__ == "__main__":
    test_article_tag_suggestions()