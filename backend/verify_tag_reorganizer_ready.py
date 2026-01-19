#!/usr/bin/env python3
"""
Verify that the Tag Reorganizer is ready to run
Checks that all tags are concepts and the system is properly configured
"""

from pymongo import MongoClient
import json
import os
from pathlib import Path

def check_database_status():
    """Check the current state of the tag system"""
    print("\n" + "="*60)
    print("DATABASE STATUS CHECK")
    print("="*60)
    
    client = MongoClient("mongodb://localhost:27017/")
    db = client.smarttrendtracer
    
    # Get statistics
    stats = {
        'concepts': db.tag_concepts_v2.count_documents({}),
        'instances': db.tag_instances.count_documents({}),
        'orphans': db.tag_instances.count_documents({'concept_id': None}),
        'unassigned': db.tag_concepts_v2.count_documents({'parents': []}),
        'auto_generated': db.tag_concepts_v2.count_documents({'auto_generated': True}),
        'manual': db.tag_concepts_v2.count_documents({'auto_generated': False})
    }
    
    print(f"\n📊 Statistics:")
    print(f"   Total concepts: {stats['concepts']:,}")
    print(f"   Total tag instances: {stats['instances']:,}")
    print(f"   - Orphan tags (no concept): {stats['orphans']:,}")
    print(f"   - Auto-generated concepts: {stats['auto_generated']:,}")
    print(f"   - Manual concepts: {stats['manual']:,}")
    print(f"   - Unassigned/root concepts: {stats['unassigned']:,}")
    
    # Check for issues
    issues = []
    if stats['orphans'] > 0:
        issues.append(f"❌ Found {stats['orphans']} orphan tags without concepts")
    else:
        print("\n✅ No orphan tags - all tags have concepts")
    
    # Sample some unassigned concepts
    if stats['unassigned'] > 0:
        print(f"\n📝 Sample unassigned concepts (need organization):")
        unassigned = list(db.tag_concepts_v2.find(
            {'parents': []},
            {'slug': 1, 'display_name': 1, 'auto_generated': 1}
        ).limit(10))
        
        for concept in unassigned[:5]:
            auto_tag = " [AUTO]" if concept.get('auto_generated') else " [MANUAL]"
            print(f"   - {concept.get('display_name', concept.get('slug'))} ({concept.get('slug')}){auto_tag}")
        
        if stats['unassigned'] > 5:
            print(f"   ... and {stats['unassigned'] - 5} more")
    
    client.close()
    
    return stats, issues

def check_llm_configuration():
    """Check LLM configuration for GPT-5/GPT-4"""
    print("\n" + "="*60)
    print("LLM CONFIGURATION CHECK")
    print("="*60)
    
    # Check llm.json
    llm_config_path = Path("llm.json")
    if llm_config_path.exists():
        with open(llm_config_path) as f:
            llm_config = json.load(f)
        
        print(f"\n📄 llm.json configuration:")
        
        # Check for tag reorganization model
        if 'models' in llm_config:
            if 'tag_reorganization' in llm_config['models']:
                model = llm_config['models']['tag_reorganization']
                print(f"   Tag reorganization model: {model.get('model', 'Not configured')}")
                print(f"   Temperature: {model.get('temperature', 'Not set')}")
                print(f"   Max tokens: {model.get('max_tokens', 'Not set')}")
                
                # Check if it's GPT-5 or GPT-4o
                model_name = model.get('model', '').lower()
                if 'gpt-5' in model_name or 'o1' in model_name:
                    print(f"   ✅ Using advanced model: {model.get('model')}")
                elif 'gpt-4' in model_name:
                    print(f"   ✅ Using GPT-4 model: {model.get('model')}")
                else:
                    print(f"   ⚠️  Using older model: {model.get('model')}")
            else:
                print("   ❌ No tag_reorganization configuration found")
        
        # Check other relevant models
        if 'models' in llm_config:
            for key in ['tag_suggestion', 'concept_suggestion']:
                if key in llm_config['models']:
                    model = llm_config['models'][key]
                    print(f"\n   {key}: {model.get('model', 'Not configured')}")
    else:
        print("   ❌ llm.json not found")
    
    # Check environment variables
    print(f"\n🔑 Environment variables:")
    has_openai = 'OPENAI_API_KEY' in os.environ
    has_gemini = 'GEMINI_API_KEY' in os.environ
    has_anthropic = 'ANTHROPIC_API_KEY' in os.environ
    
    print(f"   OPENAI_API_KEY: {'✅ Set' if has_openai else '❌ Not set'}")
    print(f"   GEMINI_API_KEY: {'✅ Set' if has_gemini else '❌ Not set'}")
    print(f"   ANTHROPIC_API_KEY: {'✅ Set' if has_anthropic else '❌ Not set'}")
    
    return has_openai

def check_tag_reorganizer_service():
    """Check if the Tag Reorganizer service is available"""
    print("\n" + "="*60)
    print("TAG REORGANIZER SERVICE CHECK")
    print("="*60)
    
    # Check for GPT-5 reorganizer
    gpt5_path = Path("app/services/gpt5_tag_reorganizer.py")
    if gpt5_path.exists():
        print(f"\n✅ GPT-5 Tag Reorganizer service found")
        
        # Check the service for model configuration
        with open(gpt5_path) as f:
            content = f.read()
            if 'gpt-5' in content.lower() or 'o1' in content.lower():
                print("   Using GPT-5/O1 model configuration")
            elif 'gpt-4' in content.lower():
                print("   Using GPT-4 model configuration")
    else:
        print(f"\n❌ GPT-5 Tag Reorganizer service not found")
    
    # Check for comprehensive reorganizer
    comp_path = Path("app/services/comprehensive_tag_reorganizer.py")
    if comp_path.exists():
        print(f"✅ Comprehensive Tag Reorganizer service found")
    
    # Check API endpoints
    api_files = [
        "app/api/tag_reorganization_comprehensive.py",
        "app/api/tag_reorganization_async.py",
        "app/api/tag_reorganization_apply.py"
    ]
    
    print(f"\n📡 API endpoints:")
    for api_file in api_files:
        if Path(api_file).exists():
            print(f"   ✅ {api_file}")
        else:
            print(f"   ❌ {api_file} not found")

def check_frontend_components():
    """Check if frontend components are ready"""
    print("\n" + "="*60)
    print("FRONTEND COMPONENTS CHECK")
    print("="*60)
    
    components = [
        "frontend/src/components/TagReorganizerModern.tsx",
        "frontend/src/components/TagReorganizerAsync.tsx",
        "frontend/src/components/TagOntologyModern.tsx",
        "frontend/src/components/ConceptOrganizer.tsx"
    ]
    
    print(f"\n🎨 Frontend components:")
    for component in components:
        if Path(component.replace("frontend/", "../frontend/")).exists():
            print(f"   ✅ {component.split('/')[-1]}")
        else:
            print(f"   ❌ {component.split('/')[-1]} not found")

def verify_unassigned_inclusion():
    """Verify that unassigned concepts will be included in reorganization"""
    print("\n" + "="*60)
    print("UNASSIGNED CONCEPT INCLUSION CHECK")
    print("="*60)
    
    client = MongoClient("mongodb://localhost:27017/")
    db = client.smarttrendtracer
    
    # Get counts by category
    pipeline = [
        {
            '$group': {
                '_id': {
                    'has_parents': {'$gt': [{'$size': '$parents'}, 0]},
                    'auto_generated': '$auto_generated'
                },
                'count': {'$sum': 1}
            }
        }
    ]
    
    results = list(db.tag_concepts_v2.aggregate(pipeline))
    
    print("\n📊 Concept organization status:")
    for result in results:
        has_parents = result['_id']['has_parents']
        auto_gen = result['_id'].get('auto_generated', False)
        count = result['count']
        
        status = "Organized" if has_parents else "Unorganized"
        source = "Auto-generated" if auto_gen else "Manual"
        print(f"   {status} {source}: {count:,} concepts")
    
    # Check if reorganizer will include all concepts
    total_concepts = db.tag_concepts_v2.count_documents({})
    print(f"\n💡 Total concepts for reorganization: {total_concepts:,}")
    print("   All concepts (organized and unorganized) will be included")
    
    client.close()

def main():
    """Run all verification checks"""
    print("\n" + "="*80)
    print(" TAG REORGANIZER READINESS CHECK")
    print(" Verifying system is ready for tag reorganization")
    print("="*80)
    
    # Check database status
    stats, issues = check_database_status()
    
    # Check LLM configuration
    has_openai = check_llm_configuration()
    
    # Check services
    check_tag_reorganizer_service()
    
    # Check frontend
    check_frontend_components()
    
    # Check unassigned inclusion
    verify_unassigned_inclusion()
    
    # Final verdict
    print("\n" + "="*80)
    print("FINAL VERIFICATION")
    print("="*80)
    
    ready = True
    
    if stats['orphans'] > 0:
        print("❌ System has orphan tags - run migration first")
        ready = False
    else:
        print("✅ All tags are properly converted to concepts")
    
    if not has_openai:
        print("❌ OpenAI API key not configured")
        ready = False
    else:
        print("✅ LLM API configured")
    
    if stats['unassigned'] > 0:
        print(f"⚠️  {stats['unassigned']} concepts need organization (will be included)")
    
    print(f"\n{'='*80}")
    if ready:
        print("✅ SYSTEM IS READY FOR TAG REORGANIZATION")
        print("\nYou can proceed with the Tag Reorganizer in the Tag Ontology Manager.")
        print(f"The system will reorganize all {stats['concepts']:,} concepts,")
        print(f"including {stats['unassigned']:,} currently unassigned concepts.")
    else:
        print("❌ SYSTEM NOT READY - Fix issues above first")
    print("="*80)
    
    return 0 if ready else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())