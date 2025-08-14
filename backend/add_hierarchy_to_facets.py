#!/usr/bin/env python3
"""
Add hierarchy concepts to the tag facets so they appear in the UI
This will create "virtual" tag entries for the parent concepts
"""

from app.models import get_db, Tag
from app.models.tag_ontology import TagConcept
from sqlalchemy import func

def show_hierarchy_usage():
    """Show how many tweets each hierarchy concept covers"""
    
    db = next(get_db())
    
    # Get all root concepts
    root_concepts = db.query(TagConcept).filter(TagConcept.parent_id.is_(None)).all()
    
    print("📊 Hierarchy Concepts and Their Coverage:")
    print("=" * 60)
    
    for concept in root_concepts:
        # Get all synonyms for this concept and its children
        from app.models.tag_ontology import TagOntologyService
        service = TagOntologyService(db)
        related_tags = service.get_tags_for_filtering(concept.tag)
        
        # Count tweets with these tags
        tweet_count = db.query(func.count(func.distinct(Tag.tweet_id))).filter(
            Tag.tag.in_(related_tags)
        ).scalar()
        
        print(f"\n{concept.display_name} ({concept.tag})")
        print(f"  Coverage: {tweet_count} tweets")
        print(f"  Maps to {len(related_tags)} tags")
        
        # Show children
        children = db.query(TagConcept).filter(TagConcept.parent_id == concept.id).all()
        for child in children[:5]:
            child_tags = service.get_tags_for_filtering(child.tag)
            child_count = db.query(func.count(func.distinct(Tag.tweet_id))).filter(
                Tag.tag.in_(child_tags)
            ).scalar()
            print(f"    └─ {child.display_name}: {child_count} tweets")
    
    print("\n💡 To make these visible in the faceted browser:")
    print("   1. The backend now expands parent tags to include children")
    print("   2. But the UI only shows tags that exist in the data")
    print("   3. You can click on child tags that exist (like 'OpenAI', 'Claude')")
    print("   4. Or use the Tag Organization view to see the full hierarchy")

if __name__ == "__main__":
    show_hierarchy_usage()