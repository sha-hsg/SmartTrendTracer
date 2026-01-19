#!/usr/bin/env python3
"""
Analyze orphan tags that weren't included in the Gemini reorganization
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import func
from app.models import get_db
from app.models.tag_ontology import TagConcept

def analyze_orphans():
    """Analyze orphan tags and why they exist"""
    db = next(get_db())
    
    # Get all root-level concepts
    orphans = db.query(TagConcept).filter(
        TagConcept.parent_id == None
    ).all()
    
    print(f"Total root-level concepts: {len(orphans)}")
    print("=" * 60)
    
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
    
    print(f"\n✅ Main taxonomy roots (with children): {len(main_roots)}")
    print("-" * 60)
    for i, (root, count) in enumerate(main_roots, 1):
        print(f"{i:2}. {root.tag} ({root.display_name})")
        print(f"    └─ {count} direct children")
        if root.description:
            print(f"    └─ {root.description[:100]}...")
    
    print(f"\n❌ Orphan tags (no parent, no children): {len(actual_orphans)}")
    print("-" * 60)
    
    if actual_orphans:
        print("\nSample orphan tags (first 30):")
        for orphan in actual_orphans[:30]:
            print(f"  - {orphan.tag} ({orphan.display_name})")
        
        if len(actual_orphans) > 30:
            print(f"\n  ... and {len(actual_orphans) - 30} more orphan tags")
    
    # Analysis summary
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Total tags in ontology: {len(orphans)}")
    print(f"Properly organized roots: {len(main_roots)} ({len(main_roots)/len(orphans)*100:.1f}%)")
    print(f"Orphan tags: {len(actual_orphans)} ({len(actual_orphans)/len(orphans)*100:.1f}%)")
    
    print("\n⚠️  ISSUE: Many tags were not included in the Gemini reorganization")
    print("This happens because the reorganization service was filtering tags")
    print("and only sending frequently-used tags to Gemini.")
    print("\n✅ SOLUTION: The code has been updated to send ALL tags to Gemini.")
    print("Run a new reorganization to properly organize all tags.")
    
    db.close()
    return main_roots, actual_orphans

if __name__ == "__main__":
    analyze_orphans()