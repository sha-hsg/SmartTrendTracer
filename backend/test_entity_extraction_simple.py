"""
Simple test for entity extraction
"""

from app.services.entity_extraction_service import EntityExtractionService

def test_simple():
    print("Initializing entity extraction service...")
    service = EntityExtractionService(use_fast_model=True)  # Use fast model
    
    print("\nEntity types loaded from MongoDB:")
    for entity_type, info in service.valid_entity_types.items():
        print(f"  - {entity_type}: {info['display_name']} (parent: {info['parent_category']})")
    
    # Simple test text
    test_text = """
    OpenAI announced GPT-4 at their conference in San Francisco. 
    Sam Altman, the CEO of OpenAI, demonstrated new capabilities.
    The model was trained on the ImageNet dataset and achieves 
    95% accuracy on the MMLU benchmark.
    """
    
    print(f"\nTest text: {test_text}")
    print("\nExtracting entities...")
    
    try:
        entities = service.extract_entities(test_text)
        print(f"\nFound {len(entities)} entities:")
        for entity in entities:
            print(f"  - {entity.text} ({entity.entity_type}) - confidence: {entity.confidence:.2f}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()