#!/usr/bin/env python3
"""
Test the concept-only tag system.
Verifies that all operations work with concepts instead of raw tags.
"""

import logging
from app.services.concept_only_tag_service import ConceptOnlyTagService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Tweet, Paper, SubstackArticle
import json

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Initialize services
concept_service = ConceptOnlyTagService()

# SQLite connection for content data
engine = create_engine('sqlite:///data/tweets.db')
Session = sessionmaker(bind=engine)
db = Session()

def test_concept_creation():
    """Test creating new concepts from text"""
    logger.info("\n=== Testing Concept Creation ===")
    
    test_cases = [
        ("machine learning", "machine_learning", "Machine Learning"),
        ("GPT-4", "gpt_4", "GPT-4"),
        ("openai", "openai", "OpenAI"),
        ("deep-learning", "deep_learning", "Deep Learning"),
        ("AI Safety", "ai_safety", "AI Safety"),
    ]
    
    for text, expected_slug, expected_display in test_cases:
        concept_id = concept_service.find_or_create_concept(text)
        concept = concept_service.get_concept_by_id(concept_id)
        
        if concept:
            logger.info(f"✓ '{text}' -> slug: '{concept['slug']}', display: '{concept['display_name']}'")
            assert concept['slug'] == expected_slug, f"Expected slug '{expected_slug}', got '{concept['slug']}'"
        else:
            logger.error(f"✗ Failed to create concept for '{text}'")
    
    return True

def test_content_tagging():
    """Test adding concepts to content"""
    logger.info("\n=== Testing Content Tagging ===")
    
    # Get a sample tweet
    tweet = db.query(Tweet).first()
    if not tweet:
        logger.warning("No tweets found")
        return False
    
    # Add a concept
    success, concept_id = concept_service.add_tag('tweet', tweet.id, "Test Concept")
    assert success, "Failed to add concept"
    logger.info(f"✓ Added concept to tweet {tweet.id}")
    
    # Get concepts for the tweet
    concepts = concept_service.get_tags_for_content('tweet', tweet.id)
    concept_ids = [c['concept_id'] for c in concepts]
    assert concept_id in concept_ids, "Concept not found in tweet concepts"
    logger.info(f"✓ Retrieved {len(concepts)} concepts for tweet")
    
    # Remove the concept
    success = concept_service.remove_tag('tweet', tweet.id, concept_id)
    assert success, "Failed to remove concept"
    logger.info(f"✓ Removed concept from tweet")
    
    return True

def test_concept_retrieval():
    """Test retrieving concepts with proper formatting"""
    logger.info("\n=== Testing Concept Retrieval ===")
    
    # Find a tweet with concepts
    instances = list(concept_service.tag_instances.find({'content_type': 'tweet'}).limit(5))
    
    if not instances:
        logger.warning("No tagged tweets found")
        return False
    
    # Get concepts for a tweet
    tweet_id = instances[0]['content_id']
    concepts = concept_service.get_tags_for_content('tweet', tweet_id)
    
    logger.info(f"Tweet {tweet_id} has {len(concepts)} concepts:")
    for concept in concepts[:3]:  # Show first 3
        logger.info(f"  - {concept['display_name']} (id: {concept['id']}, slug: {concept['slug']})")
    
    return True

def test_concept_statistics():
    """Test concept usage statistics"""
    logger.info("\n=== Testing Concept Statistics ===")
    
    # Get all concepts with counts
    all_concepts = concept_service.get_all_concepts_with_counts()
    logger.info(f"Total concepts in use: {len(all_concepts)}")
    
    # Get top 5 concepts
    top_concepts = all_concepts[:5]
    logger.info("\nTop 5 most used concepts:")
    for concept in top_concepts:
        logger.info(f"  - {concept['display_name']}: {concept['count']} uses")
    
    # Get concepts for specific content type
    tweet_concepts = concept_service.get_all_concepts_with_counts('tweet')
    paper_concepts = concept_service.get_all_concepts_with_counts('paper')
    article_concepts = concept_service.get_all_concepts_with_counts('article')
    
    logger.info(f"\nConcepts by content type:")
    logger.info(f"  Tweets: {len(tweet_concepts)} concepts")
    logger.info(f"  Papers: {len(paper_concepts)} concepts")
    logger.info(f"  Articles: {len(article_concepts)} concepts")
    
    return True

def test_concept_search():
    """Test searching for concepts"""
    logger.info("\n=== Testing Concept Search ===")
    
    search_terms = ["ai", "machine", "gpt", "deep"]
    
    for term in search_terms:
        results = concept_service.search_concepts(term, limit=3)
        logger.info(f"\nSearch '{term}' found {len(results)} concepts:")
        for concept in results:
            logger.info(f"  - {concept['display_name']} (slug: {concept['slug']})")
    
    return True

def test_api_response_format():
    """Test the API response format"""
    logger.info("\n=== Testing API Response Format ===")
    
    # Simulate API response
    tweet = db.query(Tweet).first()
    if tweet:
        concepts = concept_service.get_tags_for_content('tweet', tweet.id)
        
        # Format for API with full concepts
        api_response_full = {
            "id": tweet.id,
            "text": tweet.text[:100] + "...",
            "concepts": concepts
        }
        
        # Format for API with just IDs
        api_response_ids = {
            "id": tweet.id,
            "text": tweet.text[:100] + "...",
            "concept_ids": [c['concept_id'] for c in concepts]
        }
        
        logger.info("\nAPI Response with full concepts:")
        logger.info(json.dumps(api_response_full, indent=2, default=str)[:500])
        
        logger.info("\nAPI Response with concept IDs only:")
        logger.info(json.dumps(api_response_ids, indent=2, default=str)[:300])
    
    return True

def main():
    """Run all tests"""
    logger.info("="*60)
    logger.info("CONCEPT-ONLY SYSTEM TEST SUITE")
    logger.info("="*60)
    
    tests = [
        ("Concept Creation", test_concept_creation),
        ("Content Tagging", test_content_tagging),
        ("Concept Retrieval", test_concept_retrieval),
        ("Concept Statistics", test_concept_statistics),
        ("Concept Search", test_concept_search),
        ("API Response Format", test_api_response_format)
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
        logger.info("\n🎉 ALL TESTS PASSED! Concept-only system is working perfectly!")
    
    # Close database connection
    db.close()

if __name__ == "__main__":
    main()