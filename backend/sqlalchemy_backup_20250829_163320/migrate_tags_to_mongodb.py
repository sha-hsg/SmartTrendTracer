#!/usr/bin/env python3
"""
Migrate tag concepts v2 from SQLite to MongoDB
"""
import json
import os
from datetime import datetime
from pymongo import MongoClient
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Database connections
SQLITE_PATH = "sqlite:///data/tweets.db"
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
DB_NAME = "smarttrendtracer"

def migrate_concepts():
    """Migrate tag_concepts_v2 from SQLite to MongoDB"""
    
    # Connect to SQLite
    engine = create_engine(SQLITE_PATH)
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URL)
    db = client[DB_NAME]
    concepts_col = db.tag_concepts_v2
    
    print("Migrating tag concepts...")
    
    with engine.connect() as conn:
        # Get all concepts from SQLite
        result = conn.execute(text("""
            SELECT id, slug, display_name, description, entity_type,
                   parents, children, level, icon, color, 
                   usage_count, status, created_at, updated_at
            FROM tag_concepts_v2
            ORDER BY level, display_name
        """))
        
        concepts = []
        for row in result:
            concept = {
                "id": row[0],
                "slug": row[1],
                "display_name": row[2],
                "description": row[3],
                "entity_type": row[4],
                "parents": json.loads(row[5]) if row[5] else [],
                "children": json.loads(row[6]) if row[6] else [],
                "level": row[7] if row[7] is not None else 0,
                "icon": row[8],
                "color": row[9],
                "usage_count": row[10] if row[10] else 0,
                "status": row[11] if row[11] else "active",
                "created_at": row[12] if row[12] else datetime.utcnow(),
                "updated_at": row[13] if row[13] else datetime.utcnow(),
                # Add MongoDB-specific fields
                "_id": row[0],  # Use concept ID as MongoDB _id
                "metadata": {
                    "migrated_from": "sqlite",
                    "migration_date": datetime.utcnow()
                }
            }
            concepts.append(concept)
        
        # Clear existing concepts in MongoDB
        concepts_col.delete_many({})
        
        # Insert concepts into MongoDB
        if concepts:
            concepts_col.insert_many(concepts)
            print(f"✅ Migrated {len(concepts)} concepts")
        else:
            print("⚠️  No concepts to migrate")
    
    return len(concepts)

def migrate_aliases():
    """Migrate tag_aliases_v2 from SQLite to MongoDB"""
    
    # Connect to SQLite
    engine = create_engine(SQLITE_PATH)
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URL)
    db = client[DB_NAME]
    aliases_col = db.tag_aliases_v2
    
    print("\nMigrating tag aliases...")
    
    with engine.connect() as conn:
        # Get all aliases from SQLite
        result = conn.execute(text("""
            SELECT alias_text, concept_id, alias_type, confidence, created_at
            FROM tag_aliases_v2
            ORDER BY concept_id, alias_text
        """))
        
        aliases = []
        for row in result:
            alias = {
                "alias_text": row[0],
                "concept_id": row[1],
                "alias_type": row[2] if row[2] else "synonym",
                "confidence": row[3] if row[3] else 1.0,
                "created_at": row[4] if row[4] else datetime.utcnow(),
                "metadata": {
                    "migrated_from": "sqlite",
                    "migration_date": datetime.utcnow()
                }
            }
            aliases.append(alias)
        
        # Clear existing aliases in MongoDB
        aliases_col.delete_many({})
        
        # Insert aliases into MongoDB
        if aliases:
            aliases_col.insert_many(aliases)
            print(f"✅ Migrated {len(aliases)} aliases")
        else:
            print("⚠️  No aliases to migrate")
    
    return len(aliases)

def migrate_tag_instances():
    """Migrate actual tag usages to MongoDB tag_instances collection"""
    
    # Connect to SQLite
    engine = create_engine(SQLITE_PATH)
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URL)
    db = client[DB_NAME]
    instances_col = db.tag_instances
    concepts_col = db.tag_concepts_v2
    aliases_col = db.tag_aliases_v2
    
    print("\nMigrating tag instances...")
    
    # Build lookup maps for tag resolution
    concept_by_slug = {}
    concept_by_alias = {}
    
    for concept in concepts_col.find():
        concept_by_slug[concept["slug"]] = concept["id"]
        concept_by_slug[concept["display_name"].lower()] = concept["id"]
    
    for alias in aliases_col.find():
        concept_by_alias[alias["alias_text"].lower()] = alias["concept_id"]
    
    instances = []
    
    with engine.connect() as conn:
        # Migrate tweet tags
        result = conn.execute(text("""
            SELECT tweet_id, tag, tag_type, created_at
            FROM tags
        """))
        
        for row in result:
            tag_text = row[1]
            tag_lower = tag_text.lower()
            
            # Try to resolve to concept
            concept_id = None
            if tag_lower in concept_by_alias:
                concept_id = concept_by_alias[tag_lower]
            elif tag_lower.replace(" ", "_") in concept_by_slug:
                concept_id = concept_by_slug[tag_lower.replace(" ", "_")]
            elif tag_lower in concept_by_slug:
                concept_id = concept_by_slug[tag_lower]
            
            instance = {
                "content_type": "tweet",
                "content_id": row[0],
                "tag_text": tag_text,
                "concept_id": concept_id,
                "tag_type": row[2] if row[2] else "manual",
                "created_at": row[3] if row[3] else datetime.utcnow()
            }
            instances.append(instance)
        
        print(f"  - Found {len(instances)} tweet tags")
        
        # Migrate paper tags
        paper_count = 0
        result = conn.execute(text("""
            SELECT paper_id, tag, tag_type, created_at
            FROM paper_tags
        """))
        
        for row in result:
            tag_text = row[1]
            tag_lower = tag_text.lower()
            
            # Try to resolve to concept
            concept_id = None
            if tag_lower in concept_by_alias:
                concept_id = concept_by_alias[tag_lower]
            elif tag_lower.replace(" ", "_") in concept_by_slug:
                concept_id = concept_by_slug[tag_lower.replace(" ", "_")]
            elif tag_lower in concept_by_slug:
                concept_id = concept_by_slug[tag_lower]
            
            instance = {
                "content_type": "paper",
                "content_id": row[0],
                "tag_text": tag_text,
                "concept_id": concept_id,
                "tag_type": row[2] if row[2] else "manual",
                "created_at": row[3] if row[3] else datetime.utcnow()
            }
            instances.append(instance)
            paper_count += 1
        
        print(f"  - Found {paper_count} paper tags")
        
        # Migrate article tags
        article_count = 0
        result = conn.execute(text("""
            SELECT article_id, tag, tag_type, created_at
            FROM article_tags
        """))
        
        for row in result:
            tag_text = row[1]
            tag_lower = tag_text.lower()
            
            # Try to resolve to concept
            concept_id = None
            if tag_lower in concept_by_alias:
                concept_id = concept_by_alias[tag_lower]
            elif tag_lower.replace(" ", "_") in concept_by_slug:
                concept_id = concept_by_slug[tag_lower.replace(" ", "_")]
            elif tag_lower in concept_by_slug:
                concept_id = concept_by_slug[tag_lower]
            
            instance = {
                "content_type": "article",
                "content_id": row[0],
                "tag_text": tag_text,
                "concept_id": concept_id,
                "tag_type": row[2] if row[2] else "manual",
                "created_at": row[3] if row[3] else datetime.utcnow()
            }
            instances.append(instance)
            article_count += 1
        
        print(f"  - Found {article_count} article tags")
    
    # Clear existing instances in MongoDB
    instances_col.delete_many({})
    
    # Insert instances into MongoDB
    if instances:
        instances_col.insert_many(instances)
        print(f"✅ Migrated {len(instances)} tag instances total")
        
        # Count resolved vs unresolved
        resolved = sum(1 for i in instances if i["concept_id"] is not None)
        unresolved = len(instances) - resolved
        print(f"  - {resolved} resolved to concepts")
        print(f"  - {unresolved} unresolved (orphan tags)")
    else:
        print("⚠️  No tag instances to migrate")
    
    return len(instances)

def verify_migration():
    """Verify the migration was successful"""
    
    client = MongoClient(MONGODB_URL)
    db = client[DB_NAME]
    
    print("\n" + "="*60)
    print("MIGRATION VERIFICATION")
    print("="*60)
    
    # Check concepts
    concepts_count = db.tag_concepts_v2.count_documents({})
    root_concepts = db.tag_concepts_v2.count_documents({"parents": []})
    with_children = db.tag_concepts_v2.count_documents({"children": {"$ne": []}})
    
    print(f"\nConcepts Collection:")
    print(f"  - Total concepts: {concepts_count}")
    print(f"  - Root concepts: {root_concepts}")
    print(f"  - Concepts with children: {with_children}")
    
    # Show sample concept
    sample = db.tag_concepts_v2.find_one({"children": {"$ne": []}})
    if sample:
        print(f"\nSample concept:")
        print(f"  - ID: {sample['id']}")
        print(f"  - Display Name: {sample['display_name']}")
        print(f"  - Children: {sample['children'][:3]}...")
    
    # Check aliases
    aliases_count = db.tag_aliases_v2.count_documents({})
    unique_concepts = db.tag_aliases_v2.distinct("concept_id")
    
    print(f"\nAliases Collection:")
    print(f"  - Total aliases: {aliases_count}")
    print(f"  - Concepts with aliases: {len(unique_concepts)}")
    
    # Check instances
    instances_count = db.tag_instances.count_documents({})
    by_type = {}
    for content_type in ["tweet", "paper", "article"]:
        by_type[content_type] = db.tag_instances.count_documents({"content_type": content_type})
    
    resolved = db.tag_instances.count_documents({"concept_id": {"$ne": None}})
    unresolved = db.tag_instances.count_documents({"concept_id": None})
    
    print(f"\nTag Instances Collection:")
    print(f"  - Total instances: {instances_count}")
    print(f"  - Tweet tags: {by_type['tweet']}")
    print(f"  - Paper tags: {by_type['paper']}")
    print(f"  - Article tags: {by_type['article']}")
    print(f"  - Resolved to concepts: {resolved}")
    print(f"  - Unresolved (orphans): {unresolved}")
    
    client.close()

def main():
    print("="*60)
    print("MIGRATING TAG SYSTEM TO MONGODB")
    print("="*60)
    
    # First setup MongoDB collections and indexes
    print("\nStep 1: Setting up MongoDB...")
    os.system("python setup_mongodb.py")
    
    # Migrate data
    print("\nStep 2: Migrating data...")
    concepts_count = migrate_concepts()
    aliases_count = migrate_aliases()
    instances_count = migrate_tag_instances()
    
    # Verify
    verify_migration()
    
    print("\n" + "="*60)
    print("✅ MIGRATION COMPLETE!")
    print("="*60)
    print(f"Migrated:")
    print(f"  - {concepts_count} concepts")
    print(f"  - {aliases_count} aliases")
    print(f"  - {instances_count} tag instances")
    print("\nNext steps:")
    print("  1. Update API endpoints to use MongoDB")
    print("  2. Test the new MongoDB-based tag system")
    print("  3. Consider removing old SQLite tables after verification")

if __name__ == "__main__":
    main()