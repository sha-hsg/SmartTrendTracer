"""
Test entity extraction with full paper processing
"""

from app.services.entity_extraction_service import EntityExtractionService
from pymongo import MongoClient
import json

def test_entity_extraction():
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client.smarttrendtracer
    
    # Get a paper with content
    paper = db.papers.find_one({"content": {"$exists": True, "$ne": ""}})
    
    if not paper:
        print("No papers with content found in database")
        return
    
    print(f"Testing with paper: {paper.get('title', 'Unknown')}")
    print(f"Paper has {len(paper.get('content', ''))} characters of content")
    
    # Initialize entity extraction service
    print("\nInitializing entity extraction service...")
    service = EntityExtractionService(use_fast_model=False)
    
    # Get entity hierarchy
    print("\nEntity hierarchy loaded from MongoDB:")
    print(service.get_entity_hierarchy_for_prompt())
    
    # Extract entities from paper title and abstract
    test_text = f"""
    Title: {paper.get('title', '')}
    
    Authors: {', '.join(paper.get('authors', []))}
    
    Abstract: {paper.get('abstract', '')}
    
    Content (first 2000 chars): {paper.get('content', '')[:2000]}
    """
    
    print(f"\nExtracting entities from paper text ({len(test_text)} chars)...")
    entities = service.extract_entities(test_text, article_id=str(paper['_id']))
    
    print(f"\nFound {len(entities)} entities:")
    for entity in entities:
        entity_dict = entity.to_dict()
        print(f"  - {entity_dict['text']} ({entity_dict['type']}) - confidence: {entity_dict['confidence']:.2f}")
    
    # Test validation
    if entities:
        print("\nTesting entity validation...")
        entity = entities[0]
        is_valid, suggested_type, reasoning = service.validate_entity(entity)
        print(f"  Entity: {entity.text}")
        print(f"  Valid: {is_valid}")
        print(f"  Suggested type: {suggested_type}")
        print(f"  Reasoning: {reasoning}")
    
    # Test saving to ontology
    if entities:
        print("\nTesting save to ontology...")
        for entity in entities[:3]:  # Save first 3 entities
            parent_type = service._get_parent_type_for_entity(entity.entity_type)
            if parent_type:
                result = service.save_entity_to_ontology(None, entity, parent_type, user="test")
                if result:
                    print(f"  Saved: {entity.text} -> {result.get('id', 'unknown')}")
    
    print("\nTest complete!")

if __name__ == "__main__":
    test_entity_extraction()