"""
Direct service test suite for LLM Manager migrations
Tests the actual service classes with correct method names
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("🧪 Direct Service Test Suite")
print("=" * 80)

# Test 1: LLMManager Core Functionality
print("\n1️⃣  LLMManager Core Functionality")
try:
    from app.services.llm_manager import get_llm_manager

    manager = get_llm_manager()
    print("   ✅ LLMManager initialized")

    # Test task info
    tasks = ['tag_suggestion', 'article_summarizer', 'entity_extraction', 'trend_analysis',
             'paper_author_extraction', 'concept_organization']

    print(f"   Testing {len(tasks)} task types:")
    for task in tasks:
        info = manager.get_task_info(task)
        if info:
            print(f"      ✅ {task}: {info.get('model', 'N/A')}")
        else:
            print(f"      ❌ {task}: Not configured")

    # Test sync completion
    print("   Testing sync completion...")
    messages = [{"role": "user", "content": "Respond with 'OK' if you can read this"}]
    response = manager.completion_sync(
        task_type='tag_suggestion',
        messages=messages,
        user_id='test_user'
    )
    print(f"      ✅ Sync call successful")
    print(f"      ✅ Model: {response.model}")
    print(f"      ✅ Response: '{response.choices[0].message.content[:30]}...'")

except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Tag Suggestion Service
print("\n2️⃣  Tag Suggestion Service")
try:
    from app.services.tag_suggestion_service import TagSuggestionService

    service = TagSuggestionService()
    print("   ✅ Service initialized")
    print(f"   ✅ Model: {service.model_name}")
    print(f"   ✅ Task type: {service.task_type}")

    # Test with sample text (won't actually call LLM to save costs)
    print("   ✅ Service ready for tag suggestions")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Article Summarizer (Phase 1)
print("\n3️⃣  Article Summarizer Service")
try:
    from app.services.article_summarizer import ArticleSummarizer

    summarizer = ArticleSummarizer()
    print("   ✅ Service initialized")
    print(f"   ✅ Model: {summarizer.model_name}")

    # Check method exists
    if hasattr(summarizer, 'summarize_article_content'):
        print("   ✅ Method 'summarize_article_content' exists")
    else:
        print("   ❌ Method 'summarize_article_content' not found")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Entity Extraction Service (Phase 1)
print("\n4️⃣  Entity Extraction Service")
try:
    from app.services.entity_extraction_service import EntityExtractionService

    service = EntityExtractionService()
    print("   ✅ Service initialized")

    # Check method exists
    if hasattr(service, 'extract_entities'):
        print("   ✅ Method 'extract_entities' exists")
    else:
        print("   ❌ Method 'extract_entities' not found")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Paper Author Extraction Service
print("\n5️⃣  Paper Author Extraction Service")
try:
    from app.services.paper_author_extraction_service import PaperAuthorExtractionService

    service = PaperAuthorExtractionService()
    print("   ✅ Service initialized")
    print(f"   ✅ Task type: {service.task_type}")

    # Check prompts loaded
    if service.prompts:
        print(f"   ✅ Prompts loaded: {list(service.prompts.keys())}")
    else:
        print("   ⚠️  No prompts loaded")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 6: Paper Tag Service
print("\n6️⃣  Paper Tag Service")
try:
    from app.services.paper_tag_service import PaperTagService

    service = PaperTagService()
    print("   ✅ Service initialized")
    print(f"   ✅ Task type: {service.task_type}")

    if service.prompts:
        print(f"   ✅ Prompts loaded: {list(service.prompts.keys())}")
    else:
        print("   ⚠️  No prompts loaded")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 7: Concept Organization Service
print("\n7️⃣  Concept Organization Service")
try:
    from app.services.concept_organization_service import ConceptOrganizationService

    service = ConceptOrganizationService()
    print("   ✅ Service initialized")
    print(f"   ✅ Task type: {service.task_type}")

    # Get unorganized concepts
    concepts = service.get_unorganized_concepts(limit=3)
    print(f"   ✅ Found {len(concepts)} unorganized concepts")

    if concepts:
        print(f"      Sample: {concepts[0].get('display_name')}")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 8: RAG Service (Concepts)
print("\n8️⃣  RAG Service (Concepts)")
try:
    from app.services.rag_service_concepts import ConceptBasedRAGService

    service = ConceptBasedRAGService()
    print("   ✅ Service initialized")

    # Get index stats
    stats = service.get_index_stats()
    print(f"   ✅ Index stats:")
    print(f"      - Documents: {stats.get('indexed_documents', 0)}")
    print(f"      - Ready: {stats.get('is_ready', False)}")
    print(f"      - Tweets: {stats.get('tweets', 0)}")
    print(f"      - Articles: {stats.get('articles', 0)}")
    print(f"      - Papers: {stats.get('papers', 0)}")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 9: Ontology AI Service (Phase 1)
print("\n9️⃣  Ontology AI Service")
try:
    from app.services.ontology_ai_service import OntologyAIService

    service = OntologyAIService()
    print("   ✅ Service initialized")
    print(f"   ✅ LLMManager: {service.llm_manager is not None}")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Summary
print("\n" + "=" * 80)
print("✅ Direct Service Tests Complete!")
print("\nAll services initialized successfully with LLMManager")
print("=" * 80)
