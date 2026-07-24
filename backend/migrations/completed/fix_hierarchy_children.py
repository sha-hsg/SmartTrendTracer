#!/usr/bin/env python3
"""
Fix the hierarchy by updating children arrays based on parent relationships
"""
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
engine = create_engine('sqlite:///data/tweets.db')
Session = sessionmaker(bind=engine)
session = Session()

def fix_hierarchy():
    """Fix parent-child relationships in tag_concepts_v2"""
    
    # First, clear all children arrays
    print("Clearing existing children arrays...")
    session.execute(text("""
        UPDATE tag_concepts_v2 
        SET children = '[]'
    """))
    session.commit()
    
    # Get all concepts with their parents
    result = session.execute(text("""
        SELECT id, slug, display_name, parents
        FROM tag_concepts_v2
        WHERE status = 'active' OR status IS NULL
    """))
    
    concepts = []
    for row in result:
        concepts.append({
            'id': row[0],
            'slug': row[1],
            'display_name': row[2],
            'parents': json.loads(row[3]) if row[3] else []
        })
    
    # Build parent-to-children mapping
    parent_children = {}
    for concept in concepts:
        if concept['parents']:
            for parent_id in concept['parents']:
                if parent_id not in parent_children:
                    parent_children[parent_id] = []
                parent_children[parent_id].append(concept['id'])
    
    # Update children arrays
    print(f"\nUpdating children for {len(parent_children)} parent concepts...")
    for parent_id, children_ids in parent_children.items():
        children_json = json.dumps(children_ids)
        session.execute(text("""
            UPDATE tag_concepts_v2
            SET children = :children
            WHERE id = :parent_id
        """), {'children': children_json, 'parent_id': parent_id})
        print(f"  {parent_id}: {len(children_ids)} children")
    
    session.commit()
    
    # Show hierarchy summary
    print("\n" + "="*60)
    print("HIERARCHY SUMMARY")
    print("="*60)
    
    # Get root concepts
    result = session.execute(text("""
        SELECT id, display_name, children
        FROM tag_concepts_v2
        WHERE (parents IS NULL OR parents = '[]')
        AND (status = 'active' OR status IS NULL)
        ORDER BY display_name
    """))
    
    root_concepts = []
    for row in result:
        children = json.loads(row[2]) if row[2] else []
        root_concepts.append({
            'id': row[0],
            'display_name': row[1],
            'children': children
        })
    
    print(f"\nFound {len(root_concepts)} root concepts:")
    for root in root_concepts:
        print(f"\n{root['display_name']} ({root['id']})")
        if root['children']:
            print(f"  └─ {len(root['children'])} direct children")
            
            # Show first few children
            for child_id in root['children'][:3]:
                child_result = session.execute(text("""
                    SELECT display_name FROM tag_concepts_v2 WHERE id = :id
                """), {'id': child_id})
                child_name = child_result.scalar()
                if child_name:
                    print(f"     • {child_name}")
            if len(root['children']) > 3:
                print(f"     • ... and {len(root['children']) - 3} more")
    
    # Count total concepts
    total_result = session.execute(text("""
        SELECT COUNT(*) FROM tag_concepts_v2
        WHERE status = 'active' OR status IS NULL
    """))
    total = total_result.scalar()
    
    # Count concepts with children
    with_children_result = session.execute(text("""
        SELECT COUNT(*) FROM tag_concepts_v2
        WHERE children != '[]' AND children IS NOT NULL
        AND (status = 'active' OR status IS NULL)
    """))
    with_children = with_children_result.scalar()
    
    # Count concepts with parents
    with_parents_result = session.execute(text("""
        SELECT COUNT(*) FROM tag_concepts_v2
        WHERE parents != '[]' AND parents IS NOT NULL
        AND (status = 'active' OR status IS NULL)
    """))
    with_parents = with_parents_result.scalar()
    
    print(f"\n{'='*60}")
    print("STATISTICS")
    print(f"{'='*60}")
    print(f"Total concepts: {total}")
    print(f"Root concepts: {len(root_concepts)}")
    print(f"Concepts with children: {with_children}")
    print(f"Concepts with parents: {with_parents}")
    print(f"Leaf concepts: {total - with_children}")
    
    session.close()
    print("\n✅ Hierarchy fixed successfully!")

if __name__ == "__main__":
    fix_hierarchy()