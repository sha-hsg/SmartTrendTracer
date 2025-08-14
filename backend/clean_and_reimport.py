#!/usr/bin/env python3
"""
Clean the tag hierarchy and reimport from JSON file
This will REMOVE all existing tag concepts and replace with the new hierarchy
"""

import json
import sys
from pathlib import Path
from app.models import get_db
from app.models.tag_ontology import TagConcept, TagSynonym, TagMapping
from app.services.tag_reorganization_service import TagReorganizationService, TaxonomyReorganization, TagNode

def clean_and_reimport(file_path: str = "tag-reorganization.json", force: bool = False):
    """Clean existing hierarchy and import new one"""
    
    if not Path(file_path).exists():
        print(f"❌ Error: File '{file_path}' not found")
        return False
    
    print("=" * 60)
    print("⚠️  WARNING: This will DELETE all existing tag concepts!")
    print("=" * 60)
    
    db = next(get_db())
    
    try:
        # Show current state
        current_count = db.query(TagConcept).count()
        print(f"Current tag concepts: {current_count}")
        
        if not force:
            try:
                confirm = input("\n🔴 Are you SURE you want to delete all existing tags and import new ones? Type 'yes' to continue: ")
                if confirm.lower() != 'yes':
                    print("❌ Operation cancelled")
                    return False
            except EOFError:
                print("\n⚠️  Running in non-interactive mode, use --force to skip confirmation")
                return False
        else:
            print("\n⚠️  Force mode enabled, proceeding with cleanup...")
        
        print("\n🗑️  Deleting existing tag hierarchy...")
        
        # Delete in correct order to respect foreign keys
        db.query(TagMapping).delete()
        print("  - Deleted tag mappings")
        
        db.query(TagSynonym).delete()
        print("  - Deleted tag synonyms")
        
        db.query(TagConcept).delete()
        print("  - Deleted tag concepts")
        
        db.commit()
        print("✅ Cleanup complete")
        
        # Now import the new hierarchy
        print(f"\n📥 Importing from {file_path}...")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Extract hierarchy
        if 'hierarchy' in data:
            hierarchy = data['hierarchy']
        else:
            hierarchy = data
        
        print(f"Found {len(hierarchy)} tags to import")
        
        # Convert to TagNode objects
        imported_hierarchy = {}
        for tag_name, tag_data in hierarchy.items():
            imported_hierarchy[tag_name] = TagNode(
                name=tag_name,
                display_name=tag_data.get("display_name", tag_name),
                description=tag_data.get("description"),
                level=tag_data.get("level", 0),
                parent=tag_data.get("parent"),
                children=tag_data.get("children", []),
                synonyms=tag_data.get("synonyms", []),
                usage_count=tag_data.get("usage_count", 0)
            )
        
        # Create TaxonomyReorganization object
        import_proposal = TaxonomyReorganization(
            version="imported",
            created_at="2025-01-01T00:00:00",
            model_used="imported",
            total_tags=len(imported_hierarchy),
            hierarchy=imported_hierarchy,
            root_categories=[k for k, v in imported_hierarchy.items() if not v.parent],
            deprecated_tags=[],
            merge_proposals=[],
            new_tags_suggested=[],
            confidence_score=1.0,
            reasoning="Clean import",
            statistics={"imported_tags": len(imported_hierarchy)}
        )
        
        # Apply using the service
        service = TagReorganizationService(db)
        results = service.apply_reorganization(import_proposal, None)
        
        if results.get('success', False):
            print("\n✅ Import successful!")
            print(f"  - Created {results.get('concepts_created', 0)} concepts")
            print(f"  - Created {results.get('synonyms_created', 0)} synonyms")
            
            # Show root categories
            roots = db.query(TagConcept).filter(TagConcept.parent_id.is_(None)).all()
            print(f"\n📁 Root Categories ({len(roots)}):")
            for root in roots:
                children = db.query(TagConcept).filter(TagConcept.parent_id == root.id).count()
                print(f"  - {root.display_name} ({children} children)")
            
            # Rebuild mappings
            print("\n🔧 Rebuilding tag mappings...")
            TagMapping.rebuild_mappings(db)
            print("✅ Mappings rebuilt")
            
            return True
        else:
            print(f"❌ Import failed: {results.get('message', 'Unknown error')}")
            if results.get('errors'):
                for error in results['errors']:
                    print(f"  - {error}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean and reimport tag hierarchy')
    parser.add_argument('file', nargs='?', default='tag-reorganization.json', help='JSON file to import')
    parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()
    
    success = clean_and_reimport(args.file, force=args.force)
    sys.exit(0 if success else 1)