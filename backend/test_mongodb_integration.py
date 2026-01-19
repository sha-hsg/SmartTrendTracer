#!/usr/bin/env python3
"""
Test MongoDB integration for tag system
"""
import logging
from datetime import datetime
from app.database.mongodb import get_mongodb
from app.services.tag_service_mongodb import get_tag_service_mongodb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mongodb_connection():
    """Test basic MongoDB connection"""
    logger.info("Testing MongoDB connection...")
    
    try:
        mongo = get_mongodb()
        
        # Test server info
        info = mongo.db.client.server_info()
        logger.info(f"✅ Connected to MongoDB version {info['version']}")
        
        # List collections
        collections = mongo.db.list_collection_names()
        logger.info(f"Collections: {collections}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return False

def test_create_concept():
    """Test creating a new concept"""
    logger.info("\nTesting concept creation...")
    
    try:
        service = get_tag_service_mongodb()
        
        # Create a test concept
        concept_id = service.create_concept({
            "id": "c_test_001",
            "slug": "test_concept",
            "display_name": "Test Concept",
            "description": "A test concept for MongoDB integration",
            "status": "active",
            "icon": "🧪",
            "color": "#FF6B6B"
        })
        
        logger.info(f"✅ Created concept with ID: {concept_id}")
        
        # Verify it was created
        concept = service.get_concept_by_id(concept_id)
        if concept:
            logger.info(f"✅ Verified concept: {concept['display_name']}")
            return True
        else:
            logger.error("❌ Could not retrieve created concept")
            return False
            
    except Exception as e:
        logger.error(f"❌ Concept creation failed: {e}")
        return False

def test_create_alias():
    """Test creating aliases"""
    logger.info("\nTesting alias creation...")
    
    try:
        service = get_tag_service_mongodb()
        
        # Create aliases for the test concept
        success = service.create_alias("test", "c_test_001", "abbreviation")
        if success:
            logger.info("✅ Created alias 'test'")
        
        success = service.create_alias("testing", "c_test_001", "synonym")
        if success:
            logger.info("✅ Created alias 'testing'")
        
        # Test retrieval by alias
        concept = service.get_concept_by_alias("test")
        if concept:
            logger.info(f"✅ Found concept by alias: {concept['display_name']}")
            return True
        else:
            logger.error("❌ Could not find concept by alias")
            return False
            
    except Exception as e:
        logger.error(f"❌ Alias creation failed: {e}")
        return False

def test_hierarchy():
    """Test parent-child relationships"""
    logger.info("\nTesting hierarchy...")
    
    try:
        service = get_tag_service_mongodb()
        
        # Create parent concept
        parent_id = service.create_concept({
            "id": "c_parent_001",
            "slug": "parent_concept",
            "display_name": "Parent Concept",
            "description": "A parent concept"
        })
        
        # Create child concept
        child_id = service.create_concept({
            "id": "c_child_001",
            "slug": "child_concept",
            "display_name": "Child Concept",
            "description": "A child concept",
            "parents": [parent_id]
        })
        
        # Verify relationships
        children = service.get_concept_children(parent_id)
        if children and len(children) > 0:
            logger.info(f"✅ Parent has {len(children)} children")
            logger.info(f"   Child: {children[0]['display_name']}")
            return True
        else:
            logger.error("❌ Parent-child relationship not established")
            return False
            
    except Exception as e:
        logger.error(f"❌ Hierarchy test failed: {e}")
        return False

def test_tag_instances():
    """Test recording tag usage"""
    logger.info("\nTesting tag instances...")
    
    try:
        service = get_tag_service_mongodb()
        
        # Record some tag usage
        success = service.record_tag_instance("tweet", "12345", "test", "manual")
        if success:
            logger.info("✅ Recorded tag instance for tweet")
        
        success = service.record_tag_instance("paper", "67890", "test", "ai")
        if success:
            logger.info("✅ Recorded tag instance for paper")
        
        # Get usage stats
        stats = service.get_concept_usage_stats("c_test_001")
        logger.info(f"✅ Usage stats: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Tag instance test failed: {e}")
        return False

def test_search():
    """Test concept search"""
    logger.info("\nTesting search...")
    
    try:
        service = get_tag_service_mongodb()
        
        # Search for concepts
        results = service.search_concepts("test")
        logger.info(f"✅ Found {len(results)} concepts matching 'test'")
        
        for concept in results:
            logger.info(f"   - {concept['display_name']} ({concept['slug']})")
        
        return len(results) > 0
        
    except Exception as e:
        logger.error(f"❌ Search test failed: {e}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    logger.info("\nCleaning up test data...")
    
    try:
        mongo = get_mongodb()
        
        # Remove test concepts
        result = mongo.concepts.delete_many({
            "id": {"$in": ["c_test_001", "c_parent_001", "c_child_001"]}
        })
        logger.info(f"Deleted {result.deleted_count} test concepts")
        
        # Remove test aliases
        result = mongo.aliases.delete_many({
            "concept_id": {"$in": ["c_test_001", "c_parent_001", "c_child_001"]}
        })
        logger.info(f"Deleted {result.deleted_count} test aliases")
        
        # Remove test instances
        result = mongo.instances.delete_many({
            "concept_id": "c_test_001"
        })
        logger.info(f"Deleted {result.deleted_count} test instances")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("MongoDB Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("MongoDB Connection", test_mongodb_connection),
        ("Create Concept", test_create_concept),
        ("Create Alias", test_create_alias),
        ("Hierarchy", test_hierarchy),
        ("Tag Instances", test_tag_instances),
        ("Search", test_search)
    ]
    
    results = []
    for name, test_func in tests:
        logger.info(f"\nRunning: {name}")
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            logger.error(f"Test failed with exception: {e}")
            results.append((name, False))
    
    # Cleanup
    cleanup_test_data()
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name:30} {status}")
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)