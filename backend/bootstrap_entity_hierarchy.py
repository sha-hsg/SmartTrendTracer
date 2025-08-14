#!/usr/bin/env python3
"""
Bootstrap script to preload top_level.json entity types into the hierarchical tagging system.
This ensures that when annotations are accepted, they can be properly placed under the correct parent types.
"""

import json
import sys
from pathlib import Path
from app.models import get_db
from app.models.tag_ontology import TagConcept, TagOntologyService

def load_top_level_schema():
    """Load the top_level.json schema"""
    schema_path = Path("top_level.json")
    if not schema_path.exists():
        print("❌ Error: top_level.json not found in current directory")
        sys.exit(1)
    
    with open(schema_path, 'r') as f:
        return json.load(f)

def bootstrap_entity_hierarchy():
    """Bootstrap the entity hierarchy from top_level.json"""
    print("🚀 Bootstrapping entity hierarchy from top_level.json...")
    
    # Load schema
    schema = load_top_level_schema()
    entity_types = schema.get('entity_types', {})
    
    if not entity_types:
        print("❌ Error: No entity_types found in top_level.json")
        return
    
    # Initialize database session
    db = next(get_db())
    manager = TagOntologyService(db)
    
    created_concepts = {}
    updated_count = 0
    
    try:
        # First pass: Create top-level categories
        for category_key, category_data in entity_types.items():
            tag = category_data.get('tag', category_key)
            display_name = category_data.get('display_name', tag.title())
            description = category_data.get('description', f'{display_name} category')
            
            # Check if already exists
            existing = db.query(TagConcept).filter(TagConcept.tag == tag).first()
            if existing:
                print(f"📍 Category '{tag}' already exists (ID: {existing.id})")
                created_concepts[category_key] = existing
                updated_count += 1
            else:
                # Create new top-level category
                concept = manager.create_concept(
                    tag=tag,
                    display_name=display_name,
                    description=description,
                    parent_id=None  # Top-level
                )
                print(f"✅ Created top-level category: {tag} (ID: {concept.id})")
                created_concepts[category_key] = concept
        
        # Second pass: Create child entities
        for category_key, category_data in entity_types.items():
            category_concept = created_concepts[category_key]
            children = category_data.get('children', {})
            
            for child_key, child_data in children.items():
                child_tag = child_data.get('tag', child_key)
                child_display_name = child_data.get('display_name', child_tag.title())
                child_description = child_data.get('description', f'{child_display_name} entity type')
                
                # Check if already exists
                existing_child = db.query(TagConcept).filter(TagConcept.tag == child_tag).first()
                if existing_child:
                    print(f"📍 Child entity '{child_tag}' already exists (ID: {existing_child.id})")
                    # Update parent if needed
                    if existing_child.parent_id != category_concept.id:
                        print(f"🔄 Moving '{child_tag}' under '{category_concept.tag}'")
                        manager.move_concept(existing_child.id, category_concept.id)
                    updated_count += 1
                else:
                    # Create new child entity
                    child_concept = manager.create_concept(
                        tag=child_tag,
                        display_name=child_display_name,
                        description=child_description,
                        parent_id=category_concept.id
                    )
                    print(f"✅ Created child entity: {child_tag} under {category_concept.tag} (ID: {child_concept.id})")
                
                created_concepts[f"{category_key}.{child_key}"] = existing_child or child_concept
        
        # Update statistics
        print(f"\n📊 Bootstrap Summary:")
        print(f"   • Top-level categories: {len(entity_types)}")
        total_children = sum(len(cat.get('children', {})) for cat in entity_types.values())
        print(f"   • Child entities: {total_children}")
        print(f"   • Total entities processed: {len(entity_types) + total_children}")
        print(f"   • Already existed: {updated_count}")
        print(f"   • Newly created: {len(created_concepts) - updated_count}")
        
        print(f"\n✨ Entity hierarchy is now ready for annotation integration!")
        print(f"   When entities are accepted, they will be placed under the appropriate parent types:")
        
        for category_key, category_data in entity_types.items():
            category_tag = category_data.get('tag', category_key)
            children = category_data.get('children', {})
            if children:
                child_tags = [child.get('tag', key) for key, child in children.items()]
                print(f"   • {category_tag}: {', '.join(child_tags)}")
        
    except Exception as e:
        print(f"❌ Error during bootstrap: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    bootstrap_entity_hierarchy()