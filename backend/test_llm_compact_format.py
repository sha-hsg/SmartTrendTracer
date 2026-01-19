#!/usr/bin/env python3
"""Test LLM processing readiness with compact format"""

from pymongo import MongoClient
from bson import ObjectId
import json
import tiktoken

def build_compact_hierarchy():
    """Build compact hierarchy for LLM processing"""
    client = MongoClient()
    db = client.smarttrendtracer
    concepts = db.tag_concepts_v2
    
    # Get all concepts
    all_concepts = list(concepts.find())
    concept_map = {str(c['_id']): c for c in all_concepts}
    
    # Build compact format
    compact = {
        "v": 2,
        "c": []
    }
    
    for concept in all_concepts:
        # Get parent and children tags
        parent_tags = []
        if concept.get('parents'):
            for parent_id in concept['parents']:
                parent_id_str = str(parent_id)
                if parent_id_str in concept_map:
                    parent = concept_map[parent_id_str]
                    parent_tags.append(parent.get('slug') or parent.get('tag', parent_id_str))
        
        children_tags = []
        if concept.get('children'):
            for child_id in concept['children']:
                child_id_str = str(child_id)
                if child_id_str in concept_map:
                    child = concept_map[child_id_str]
                    children_tags.append(child.get('slug') or child.get('tag', child_id_str))
        
        # Build compact concept
        compact_concept = {
            "t": concept.get('slug') or concept.get('tag', 'unknown'),
            "d": concept.get('display_name', ''),
            "p": parent_tags,
            "ch": children_tags,
            "cnt": concept.get('usage_count', 0)
        }
        
        # Add entity type if present
        if concept.get('entity_type'):
            compact_concept["e"] = concept['entity_type']
        
        compact["c"].append(compact_concept)
    
    return compact, all_concepts

def calculate_token_usage(text, model="gpt-4"):
    """Calculate token usage for given text"""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except:
        encoding = tiktoken.get_encoding("cl100k_base")  # Default for GPT-4
    
    tokens = encoding.encode(text)
    return len(tokens)

def test_llm_readiness():
    """Test if the hierarchy is ready for LLM processing"""
    print("=== LLM Processing Readiness Test ===\n")
    
    # Build compact hierarchy
    compact, all_concepts = build_compact_hierarchy()
    
    # Convert to JSON
    compact_json = json.dumps(compact, separators=(',', ':'))
    verbose_json = json.dumps([{
        "tag": c.get('slug') or c.get('tag', 'unknown'),
        "display_name": c.get('display_name', ''),
        "parents": [],  # Would need to resolve
        "children": [],  # Would need to resolve
        "usage_count": c.get('usage_count', 0),
        "entity_type": c.get('entity_type')
    } for c in all_concepts], indent=2)
    
    # Calculate sizes
    compact_size = len(compact_json)
    verbose_size = len(verbose_json)
    reduction = (1 - compact_size/verbose_size) * 100
    
    print(f"Total concepts: {len(all_concepts)}")
    print(f"\nData Size Comparison:")
    print(f"  Verbose format: {verbose_size:,} bytes")
    print(f"  Compact format: {compact_size:,} bytes")
    print(f"  Reduction: {reduction:.1f}%")
    
    # Calculate token usage
    compact_tokens = calculate_token_usage(compact_json)
    verbose_tokens = calculate_token_usage(verbose_json)
    token_reduction = (1 - compact_tokens/verbose_tokens) * 100
    
    print(f"\nToken Usage Comparison:")
    print(f"  Verbose format: {verbose_tokens:,} tokens")
    print(f"  Compact format: {compact_tokens:,} tokens")
    print(f"  Token reduction: {token_reduction:.1f}%")
    
    # Check context window fit
    print(f"\nContext Window Compatibility:")
    models = [
        ("GPT-4", 8_192),
        ("GPT-4-32k", 32_768),
        ("GPT-4-turbo", 128_000),
        ("GPT-5 (estimated)", 400_000),
        ("Gemini 1.5 Pro", 2_000_000),
        ("Claude 3", 200_000)
    ]
    
    for model_name, context_size in models:
        fit_percentage = (compact_tokens / context_size) * 100
        status = "✅" if compact_tokens < context_size else "❌"
        print(f"  {model_name} ({context_size:,} tokens): {status} Uses {fit_percentage:.1f}% of context")
    
    # Test JSON parsing variations
    print(f"\n=== JSON Structure Validation ===")
    
    # Check for valid JSON
    try:
        parsed = json.loads(compact_json)
        print("✅ Valid JSON structure")
    except:
        print("❌ Invalid JSON structure")
    
    # Check hierarchy consistency
    print(f"\n=== Hierarchy Consistency ===")
    
    # Build concept lookup
    concept_lookup = {c["t"]: c for c in compact["c"]}
    
    # Check parent-child relationships
    inconsistencies = []
    for concept in compact["c"]:
        tag = concept["t"]
        
        # Check if all parents list this as child
        for parent_tag in concept["p"]:
            if parent_tag in concept_lookup:
                parent = concept_lookup[parent_tag]
                if tag not in parent.get("ch", []):
                    inconsistencies.append(f"{tag} lists {parent_tag} as parent, but {parent_tag} doesn't list it as child")
        
        # Check if all children list this as parent
        for child_tag in concept["ch"]:
            if child_tag in concept_lookup:
                child = concept_lookup[child_tag]
                if tag not in child.get("p", []):
                    inconsistencies.append(f"{tag} lists {child_tag} as child, but {child_tag} doesn't list it as parent")
    
    if inconsistencies:
        print(f"❌ Found {len(inconsistencies)} consistency issues:")
        for issue in inconsistencies[:5]:  # Show first 5
            print(f"  - {issue}")
    else:
        print("✅ All parent-child relationships are bidirectional")
    
    # Check for orphans
    root_concepts = [c for c in compact["c"] if not c["p"]]
    orphan_concepts = []
    
    for concept in compact["c"]:
        if concept["p"]:  # Has parents
            all_parents_exist = all(p in concept_lookup for p in concept["p"])
            if not all_parents_exist:
                orphan_concepts.append(concept["t"])
    
    print(f"\n=== Orphan Analysis ===")
    print(f"Root concepts (no parents): {len(root_concepts)}")
    print(f"Orphaned concepts (invalid parents): {len(orphan_concepts)}")
    
    if orphan_concepts:
        print(f"  Examples: {orphan_concepts[:5]}")
    
    # Check for circular references
    print(f"\n=== Circular Reference Check ===")
    
    def has_circular_reference(tag, visited=None):
        if visited is None:
            visited = set()
        
        if tag in visited:
            return True
        
        if tag not in concept_lookup:
            return False
        
        visited.add(tag)
        concept = concept_lookup[tag]
        
        for parent in concept.get("p", []):
            if has_circular_reference(parent, visited.copy()):
                return True
        
        return False
    
    circular_refs = [tag for tag in concept_lookup if has_circular_reference(tag)]
    
    if circular_refs:
        print(f"❌ Found {len(circular_refs)} concepts with circular references")
        print(f"  Examples: {circular_refs[:5]}")
    else:
        print("✅ No circular references detected")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Total concepts: {len(all_concepts)}")
    print(f"Compact format size: {compact_size:,} bytes ({compact_tokens:,} tokens)")
    print(f"Token reduction: {token_reduction:.1f}%")
    print(f"Fits in GPT-5 context: {'✅ Yes' if compact_tokens < 400_000 else '❌ No'}")
    print(f"Fits in Gemini context: {'✅ Yes' if compact_tokens < 2_000_000 else '❌ No'}")
    print(f"Hierarchy consistency: {'✅ Good' if not inconsistencies else f'⚠️ {len(inconsistencies)} issues'}")
    print(f"Circular references: {'✅ None' if not circular_refs else f'❌ {len(circular_refs)} found'}")
    
    return compact_json, compact_tokens

if __name__ == "__main__":
    compact_json, tokens = test_llm_readiness()