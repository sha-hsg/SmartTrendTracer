#!/usr/bin/env python3
"""
Rebuild tag mappings after importing hierarchy
This ensures the ontology tree and filtering work correctly
"""

from app.models import get_db
from app.models.tag_ontology import TagMapping, TagConcept
import time

def rebuild_mappings():
    """Rebuild all tag mappings for efficient queries"""
    print("🔧 Rebuilding tag mappings...")
    start_time = time.time()
    
    # Get database session
    db = next(get_db())
    
    try:
        # Rebuild the mappings
        TagMapping.rebuild_mappings(db)
        
        # Count results
        mapping_count = db.query(TagMapping).count()
        concept_count = db.query(TagConcept).count()
        
        # Update descendant caches for all concepts
        print("📊 Updating descendant caches...")
        concepts = db.query(TagConcept).all()
        for concept in concepts:
            concept.update_descendant_cache(db)
        
        db.commit()
        
        duration = time.time() - start_time
        
        print(f"✅ Successfully rebuilt mappings!")
        print(f"   - {concept_count} tag concepts")
        print(f"   - {mapping_count} tag mappings")
        print(f"   - Duration: {duration:.2f} seconds")
        
        # Show root categories
        root_concepts = db.query(TagConcept).filter(TagConcept.parent_id.is_(None)).all()
        if root_concepts:
            print(f"\n📁 Root Categories ({len(root_concepts)}):")
            for concept in root_concepts[:10]:
                child_count = db.query(TagConcept).filter(TagConcept.parent_id == concept.id).count()
                print(f"   - {concept.display_name} ({concept.tag}) - {child_count} direct children")
        
        return True
        
    except Exception as e:
        print(f"❌ Error rebuilding mappings: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    rebuild_mappings()