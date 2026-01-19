#!/usr/bin/env python3
"""
Test script to verify complete MongoDB migration.
Tests all CRUD operations for tags across tweets, papers, and articles.
"""

import random
import logging
from app.services.mongodb_tag_service import MongoDBTagService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Tweet, Paper, SubstackArticle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
mongo_service = MongoDBTagService()

# SQLite connection for content data
engine = create_engine('sqlite:///data/tweets.db')
Session = sessionmaker(bind=engine)
db = Session()

def test_tweet_tags():
    """Test tag operations for tweets"""
    logger.info("\n=== Testing Tweet Tags ===")
    
    # Get a random tweet
    tweet = db.query(Tweet).first()
    if not tweet:
        logger.warning("No tweets found in database")
        return False
    
    tweet_id = tweet.id
    logger.info(f"Testing with tweet ID: {tweet_id}")
    
    # Add a test tag
    test_tag = f"test-tag-{random.randint(1000, 9999)}"
    success = mongo_service.add_tag('tweet', tweet_id, test_tag, 'test')
    assert success, "Failed to add tag to tweet"
    logger.info(f"✓ Added tag '{test_tag}' to tweet")
    
    # Get tags for tweet
    tags = mongo_service.get_tags_for_content('tweet', tweet_id)
    tag_texts = [t['tag_text'] for t in tags]
    assert test_tag in tag_texts, f"Tag '{test_tag}' not found in tweet tags"
    logger.info(f"✓ Retrieved {len(tags)} tags for tweet")
    
    # Remove the test tag
    success = mongo_service.remove_tag('tweet', tweet_id, test_tag)
    assert success, "Failed to remove tag from tweet"
    logger.info(f"✓ Removed tag '{test_tag}' from tweet")
    
    # Verify removal
    tags = mongo_service.get_tags_for_content('tweet', tweet_id)
    tag_texts = [t['tag_text'] for t in tags]
    assert test_tag not in tag_texts, f"Tag '{test_tag}' still present after removal"
    logger.info("✓ Verified tag removal")
    
    return True

def test_paper_tags():
    """Test tag operations for papers"""
    logger.info("\n=== Testing Paper Tags ===")
    
    # Get a random paper
    paper = db.query(Paper).first()
    if not paper:
        logger.warning("No papers found in database")
        return False
    
    paper_id = str(paper.id)
    logger.info(f"Testing with paper ID: {paper_id}")
    
    # Add a test tag
    test_tag = f"test-paper-tag-{random.randint(1000, 9999)}"
    success = mongo_service.add_tag('paper', paper_id, test_tag, 'test')
    assert success, "Failed to add tag to paper"
    logger.info(f"✓ Added tag '{test_tag}' to paper")
    
    # Get tags for paper
    tags = mongo_service.get_tags_for_content('paper', paper_id)
    tag_texts = [t['tag_text'] for t in tags]
    assert test_tag in tag_texts, f"Tag '{test_tag}' not found in paper tags"
    logger.info(f"✓ Retrieved {len(tags)} tags for paper")
    
    # Remove the test tag
    success = mongo_service.remove_tag('paper', paper_id, test_tag)
    assert success, "Failed to remove tag from paper"
    logger.info(f"✓ Removed tag '{test_tag}' from paper")
    
    return True

def test_article_tags():
    """Test tag operations for articles"""
    logger.info("\n=== Testing Article Tags ===")
    
    # Get a random article
    article = db.query(SubstackArticle).first()
    if not article:
        logger.warning("No articles found in database")
        return False
    
    article_id = str(article.id)
    logger.info(f"Testing with article ID: {article_id}")
    
    # Add a test tag
    test_tag = f"test-article-tag-{random.randint(1000, 9999)}"
    success = mongo_service.add_tag('article', article_id, test_tag, 'test')
    assert success, "Failed to add tag to article"
    logger.info(f"✓ Added tag '{test_tag}' to article")
    
    # Get tags for article
    tags = mongo_service.get_tags_for_content('article', article_id)
    tag_texts = [t['tag_text'] for t in tags]
    assert test_tag in tag_texts, f"Tag '{test_tag}' not found in article tags"
    logger.info(f"✓ Retrieved {len(tags)} tags for article")
    
    # Remove the test tag
    success = mongo_service.remove_tag('article', article_id, test_tag)
    assert success, "Failed to remove tag from article"
    logger.info(f"✓ Removed tag '{test_tag}' from article")
    
    return True

def test_tag_statistics():
    """Test tag statistics and aggregation"""
    logger.info("\n=== Testing Tag Statistics ===")
    
    # Get all tags with counts
    all_tags = mongo_service.get_all_tags_with_counts()
    logger.info(f"✓ Found {len(all_tags)} unique tags across all content")
    
    # Get tags by content type
    tweet_tags = mongo_service.get_all_tags_with_counts('tweet')
    paper_tags = mongo_service.get_all_tags_with_counts('paper')
    article_tags = mongo_service.get_all_tags_with_counts('article')
    
    logger.info(f"✓ Tweet tags: {len(tweet_tags)}")
    logger.info(f"✓ Paper tags: {len(paper_tags)}")
    logger.info(f"✓ Article tags: {len(article_tags)}")
    
    # Get orphan tags
    orphans = mongo_service.get_orphan_tags()
    logger.info(f"✓ Orphan tags (no concept): {len(orphans)}")
    
    # Update concept links
    updated = mongo_service.update_tag_concept_links()
    logger.info(f"✓ Updated {updated} orphan tags with concept links")
    
    return True

def test_hierarchy_search():
    """Test hierarchical tag search"""
    logger.info("\n=== Testing Hierarchical Tag Search ===")
    
    # Test with a known tag
    test_tag = "machine-learning"
    
    # Get content with hierarchy
    with_hierarchy = mongo_service.get_content_ids_by_tag(test_tag, use_hierarchy=True)
    logger.info(f"✓ Found {len(with_hierarchy)} items with '{test_tag}' (hierarchy enabled)")
    
    # Get content without hierarchy
    without_hierarchy = mongo_service.get_content_ids_by_tag(test_tag, use_hierarchy=False)
    logger.info(f"✓ Found {len(without_hierarchy)} items with '{test_tag}' (hierarchy disabled)")
    
    # Hierarchy should find more or equal items
    assert len(with_hierarchy) >= len(without_hierarchy), "Hierarchy should find more items"
    
    return True

def main():
    """Run all tests"""
    logger.info("="*60)
    logger.info("MongoDB TAG MIGRATION TEST SUITE")
    logger.info("="*60)
    
    tests = [
        ("Tweet Tags", test_tweet_tags),
        ("Paper Tags", test_paper_tags),
        ("Article Tags", test_article_tags),
        ("Tag Statistics", test_tag_statistics),
        ("Hierarchy Search", test_hierarchy_search)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "PASSED" if result else "SKIPPED"))
        except Exception as e:
            logger.error(f"Test '{test_name}' failed: {e}")
            results.append((test_name, "FAILED"))
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    for test_name, status in results:
        symbol = "✅" if status == "PASSED" else "⚠️" if status == "SKIPPED" else "❌"
        logger.info(f"{symbol} {test_name}: {status}")
    
    passed = sum(1 for _, s in results if s == "PASSED")
    total = len(results)
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 ALL TESTS PASSED! MongoDB migration is complete and working!")
    elif passed > 0:
        logger.info("\n⚠️ Some tests passed. Check warnings above.")
    else:
        logger.error("\n❌ Tests failed. Migration may be incomplete.")
    
    # Close database connection
    db.close()

if __name__ == "__main__":
    main()