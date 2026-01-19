#!/usr/bin/env python3
"""
Fix orphan tags by assigning them to appropriate parent categories
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import func
from app.models import get_db
from app.models.tag_ontology import TagConcept, TagOntologyService

def analyze_orphans():
    """Analyze orphan tags"""
    db = next(get_db())
    
    # Get all root-level concepts
    orphans = db.query(TagConcept).filter(
        TagConcept.parent_id == None
    ).all()
    
    print(f"Total root-level concepts: {len(orphans)}")
    
    # Identify the main taxonomy roots (should have children)
    main_roots = []
    actual_orphans = []
    
    for concept in orphans:
        child_count = db.query(func.count(TagConcept.id)).filter(
            TagConcept.parent_id == concept.id
        ).scalar()
        
        if child_count > 0:
            main_roots.append((concept, child_count))
        else:
            actual_orphans.append(concept)
    
    # Sort main roots by child count
    main_roots.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\nMain taxonomy roots (with children):")
    for root, count in main_roots[:10]:
        print(f"  - {root.tag} ({root.display_name}): {count} children")
    
    print(f"\nActual orphan tags (no children): {len(actual_orphans)}")
    print("\nSample orphan tags:")
    for orphan in actual_orphans[:20]:
        print(f"  - {orphan.tag} ({orphan.display_name})")
    
    return main_roots, actual_orphans

def suggest_parents(orphans, main_roots):
    """Suggest parent categories for orphan tags"""
    suggestions = {}
    
    # Use the actual main roots from the database
    # Map keywords to the actual parent categories that exist
    parent_map = {
        'AI_ML_Core_Concepts': ['ai', 'ml', 'artificial', 'intelligence', 'core', 'fundamental'],
        'Model_Development_Lifecycle': ['development', 'training', 'deployment', 'lifecycle', 'build', 'test'],
        'AI_Models_Architectures': ['model', 'architecture', 'network', 'transformer', 'llm', 'gpt', 'claude', 'gemini'],
        'Responsible_AI': ['responsible', 'ethics', 'safety', 'bias', 'fairness', 'governance'],
        'Research_Community_And_Process': ['research', 'paper', 'study', 'academic', 'conference', 'publication'],
        'AI_Ecosystem': ['ecosystem', 'company', 'platform', 'tool', 'service', 'api', 'framework'],
        'Industry_And_Ecosystem': ['industry', 'business', 'enterprise', 'startup', 'market'],
    }
    
    # Add special handling for known companies/platforms
    company_keywords = ['hugging', 'openai', 'anthropic', 'google', 'meta', 'microsoft', 'nvidia', 'apple']
    model_keywords = ['gpt', 'llm', 'bert', 'clip', 'dalle', 'stable', 'diffusion', 'whisper']
    tool_keywords = ['tool', 'app', 'cli', 'api', 'sdk', 'library', 'framework', 'platform']
    
    for orphan in orphans:
        tag_lower = orphan.tag.lower()
        suggested_parent = None
        
        # First check for special cases
        if any(keyword in tag_lower for keyword in company_keywords):
            suggested_parent = 'AI_Ecosystem'
        elif any(keyword in tag_lower for keyword in model_keywords):
            suggested_parent = 'AI_Models_Architectures'
        elif any(keyword in tag_lower for keyword in tool_keywords):
            suggested_parent = 'AI_Ecosystem'
        elif 'paper' in tag_lower or 'research' in tag_lower:
            suggested_parent = 'Research_Community_And_Process'
        elif 'ethic' in tag_lower or 'safety' in tag_lower or 'bias' in tag_lower:
            suggested_parent = 'Responsible_AI'
        else:
            # Check each parent category's keywords
            for parent_tag, keywords in parent_map.items():
                for keyword in keywords:
                    if keyword in tag_lower:
                        suggested_parent = parent_tag
                        break
                if suggested_parent:
                    break
        
        # Default to AI_ML_Core_Concepts if no match
        if not suggested_parent:
            suggested_parent = 'AI_ML_Core_Concepts'
        
        suggestions[orphan.tag] = suggested_parent
    
    return suggestions

def fix_orphans(apply_fixes=False):
    """Fix orphan tags by assigning them to parent categories"""
    db = next(get_db())
    
    main_roots, orphans = analyze_orphans()
    
    if not orphans:
        print("\nNo orphan tags to fix!")
        return
    
    # Get suggestions
    suggestions = suggest_parents(orphans, main_roots)
    
    print(f"\n{'='*60}")
    print("Suggested parent assignments:")
    print(f"{'='*60}")
    
    # Group by suggested parent
    by_parent = {}
    for tag, parent in suggestions.items():
        if parent not in by_parent:
            by_parent[parent] = []
        by_parent[parent].append(tag)
    
    for parent, tags in by_parent.items():
        print(f"\n{parent}: ({len(tags)} tags)")
        for tag in tags[:10]:  # Show first 10
            print(f"  - {tag}")
        if len(tags) > 10:
            print(f"  ... and {len(tags) - 10} more")
    
    if apply_fixes:
        print(f"\n{'='*60}")
        print("Applying fixes...")
        print(f"{'='*60}")
        
        fixed = 0
        errors = 0
        
        for orphan in orphans:
            suggested_parent = suggestions[orphan.tag]
            
            # Find the parent concept
            parent = db.query(TagConcept).filter(
                TagConcept.tag == suggested_parent
            ).first()
            
            if parent:
                orphan.parent_id = parent.id
                orphan.update_path(db)
                fixed += 1
                if fixed % 20 == 0:
                    print(f"Fixed {fixed} tags...")
            else:
                print(f"Warning: Parent '{suggested_parent}' not found for '{orphan.tag}'")
                errors += 1
        
        db.commit()
        
        # Update descendant caches
        print("\nUpdating descendant caches...")
        for root, _ in main_roots[:10]:
            root.update_descendant_cache(db)
        db.commit()
        
        # Rebuild mappings
        from app.models.tag_ontology import TagMapping
        print("Rebuilding tag mappings...")
        TagMapping.rebuild_mappings(db)
        
        print(f"\n✅ Fixed {fixed} orphan tags")
        if errors:
            print(f"⚠️  {errors} tags could not be fixed (parent not found)")
    else:
        print(f"\n{'='*60}")
        print("To apply these fixes, run with --apply flag:")
        print("python fix_orphan_tags.py --apply")
    
    db.close()

if __name__ == "__main__":
    apply = "--apply" in sys.argv
    fix_orphans(apply_fixes=apply)