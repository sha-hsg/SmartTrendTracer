#!/usr/bin/env python3
"""
Setup MongoDB for tag concepts v2 structure
"""
import os
from pymongo import MongoClient, ASCENDING, TEXT
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
DB_NAME = "smarttrendtracer"

def setup_mongodb():
    """Create MongoDB collections and indexes for tag concepts v2"""
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URL)
    db = client[DB_NAME]
    
    print(f"Connected to MongoDB at {MONGODB_URL}")
    print(f"Using database: {DB_NAME}")
    
    # Create collections
    collections = {
        "tag_concepts_v2": "Main concept definitions with hierarchy",
        "tag_aliases_v2": "Aliases and synonyms for concepts",
        "tag_instances": "Actual tag usage instances on content"
    }
    
    for collection_name, description in collections.items():
        if collection_name not in db.list_collection_names():
            db.create_collection(collection_name)
            print(f"✅ Created collection: {collection_name} - {description}")
        else:
            print(f"ℹ️  Collection exists: {collection_name}")
    
    # Create indexes for tag_concepts_v2
    concepts_col = db.tag_concepts_v2
    
    # Unique index on ID
    concepts_col.create_index("id", unique=True)
    print("  - Created unique index on 'id'")
    
    # Index on slug for fast lookups
    concepts_col.create_index("slug", unique=True)
    print("  - Created unique index on 'slug'")
    
    # Text index for search
    concepts_col.create_index([("display_name", TEXT), ("description", TEXT)])
    print("  - Created text index on display_name and description")
    
    # Index on entity_type for filtering
    concepts_col.create_index("entity_type")
    print("  - Created index on 'entity_type'")
    
    # Index on parents for hierarchy queries
    concepts_col.create_index("parents")
    print("  - Created index on 'parents'")
    
    # Index on status
    concepts_col.create_index("status")
    print("  - Created index on 'status'")
    
    # Create indexes for tag_aliases_v2
    aliases_col = db.tag_aliases_v2
    
    # Index on alias_text for lookups
    aliases_col.create_index("alias_text")
    print("\n  - Created index on 'alias_text'")
    
    # Index on concept_id for reverse lookups
    aliases_col.create_index("concept_id")
    print("  - Created index on 'concept_id'")
    
    # Compound index for unique alias per concept
    aliases_col.create_index([("alias_text", ASCENDING), ("concept_id", ASCENDING)], unique=True)
    print("  - Created unique compound index on alias_text + concept_id")
    
    # Create indexes for tag_instances
    instances_col = db.tag_instances
    
    # Compound index for content lookups
    instances_col.create_index([("content_type", ASCENDING), ("content_id", ASCENDING)])
    print("\n  - Created compound index on content_type + content_id")
    
    # Index on concept_id for concept usage queries
    instances_col.create_index("concept_id")
    print("  - Created index on 'concept_id'")
    
    # Index on tag_type
    instances_col.create_index("tag_type")
    print("  - Created index on 'tag_type'")
    
    print("\n✅ MongoDB setup complete!")
    
    # Show collection stats
    print("\n" + "="*60)
    print("Collection Statistics:")
    print("="*60)
    for collection_name in collections.keys():
        count = db[collection_name].count_documents({})
        print(f"{collection_name}: {count} documents")
    
    client.close()

if __name__ == "__main__":
    setup_mongodb()