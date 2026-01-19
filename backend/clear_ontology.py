#!/usr/bin/env python3
"""
Clear the existing tag ontology to start fresh with a complete Gemini reorganization
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.tag_ontology import TagConcept, TagSynonym, TagMapping

def clear_ontology(confirm=False):
    """Clear all tag ontology data"""
    db = next(get_db())
    
    # Count existing data
    concepts_count = db.query(TagConcept).count()
    synonyms_count = db.query(TagSynonym).count()
    mappings_count = db.query(TagMapping).count()
    
    print("=" * 60)
    print("TAG ONTOLOGY CLEANUP")
    print("=" * 60)
    print(f"\nCurrent ontology contains:")
    print(f"  - {concepts_count} tag concepts")
    print(f"  - {synonyms_count} tag synonyms")
    print(f"  - {mappings_count} tag mappings")
    
    if not confirm:
        print("\n⚠️  This will DELETE all tag ontology data!")
        print("Your raw tags in tweets, articles, and papers will NOT be affected.")
        print("\nTo proceed, run with --confirm flag:")
        print("python clear_ontology.py --confirm")
        return
    
    print("\n🗑️  Clearing ontology...")
    
    # Clear in correct order due to foreign keys
    db.query(TagMapping).delete()
    print("  ✓ Tag mappings cleared")
    
    db.query(TagSynonym).delete()
    print("  ✓ Tag synonyms cleared")
    
    db.query(TagConcept).delete()
    print("  ✓ Tag concepts cleared")
    
    db.commit()
    
    print("\n✅ Ontology cleared successfully!")
    print("\nNext steps:")
    print("1. Go to the Gemini Tag Reorganizer in the UI")
    print("2. Click 'Generate Reorganization Proposal'")
    print("3. Review the proposal (it should now include ALL 731 tags)")
    print("4. Click 'Apply All Changes' to create a complete hierarchy")
    
    db.close()

if __name__ == "__main__":
    confirm = "--confirm" in sys.argv
    clear_ontology(confirm=confirm)