#!/usr/bin/env python3
"""
Create the new tag_concepts_v2 schema to store the complete tag structure
with IDs, poly-hierarchy support, status, icons, and colors.
"""
import sqlite3
from pathlib import Path
import sys

def create_v2_schema():
    """Create the new schema for tag concepts v2"""
    
    db_path = Path("data/tweets.db")
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tag_concepts_v2 table
        print("Creating tag_concepts_v2 table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tag_concepts_v2 (
                -- Primary fields
                id TEXT PRIMARY KEY,  -- Unique ID like "c_0001"
                slug TEXT UNIQUE NOT NULL,  -- snake_case normalized name
                display_name TEXT NOT NULL,  -- Human-readable name
                description TEXT,
                
                -- Status and metadata
                status TEXT DEFAULT 'active',  -- active, deprecated, suggested
                usage_count INTEGER DEFAULT 0,
                
                -- Visual properties
                icon TEXT,  -- Emoji icon
                color TEXT,  -- Hex color code
                
                -- Hierarchy (stored as JSON for poly-hierarchy)
                parents JSON,  -- Array of parent IDs
                children JSON,  -- Array of child IDs
                level INTEGER DEFAULT 0,  -- Depth in hierarchy
                
                -- Entity type for semantic classification
                entity_type TEXT,  -- person, organisation, model, dataset, etc.
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create aliases table for backwards compatibility
        print("Creating tag_aliases_v2 table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tag_aliases_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alias_text TEXT UNIQUE NOT NULL,  -- The alias (e.g., "LLM", "GPT-4")
                concept_id TEXT NOT NULL,  -- References tag_concepts_v2.id
                alias_type TEXT NOT NULL,  -- synonym, variant, misspelling, abbreviation, plural, deprecated, legacy
                confidence REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (concept_id) REFERENCES tag_concepts_v2(id) ON DELETE CASCADE
            )
        """)
        
        # Create relations table for semantic relationships
        print("Creating tag_relations_v2 table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tag_relations_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,  -- Source concept ID
                target_id TEXT NOT NULL,  -- Target concept ID
                relation_type TEXT NOT NULL,  -- related, produces, evaluated_on, part_of, etc.
                confidence REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (source_id) REFERENCES tag_concepts_v2(id) ON DELETE CASCADE,
                FOREIGN KEY (target_id) REFERENCES tag_concepts_v2(id) ON DELETE CASCADE,
                UNIQUE(source_id, target_id, relation_type)
            )
        """)
        
        # Create reorganization proposals table
        print("Creating tag_reorganization_proposals table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tag_reorganization_proposals (
                proposal_id TEXT PRIMARY KEY,
                version TEXT,
                model_used TEXT,
                total_tags INTEGER,
                confidence_score REAL,
                reasoning TEXT,
                
                -- Store the full proposal as JSON
                concepts JSON,  -- Array of concept objects
                aliases JSON,  -- Array of alias mappings
                relations JSON,  -- Array of relations
                root_categories JSON,  -- Array of root category IDs
                merge_proposals JSON,  -- Array of merge proposals
                governance JSON,  -- Governance rules
                validation JSON,  -- Validation results
                
                -- Status tracking
                status TEXT DEFAULT 'draft',  -- draft, approved, applied, rejected
                applied_at TIMESTAMP,
                applied_by TEXT,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_concepts_v2_slug ON tag_concepts_v2(slug)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_concepts_v2_status ON tag_concepts_v2(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_concepts_v2_entity_type ON tag_concepts_v2(entity_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_aliases_v2_alias ON tag_aliases_v2(alias_text)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_aliases_v2_concept ON tag_aliases_v2(concept_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relations_v2_source ON tag_relations_v2(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relations_v2_target ON tag_relations_v2(target_id)")
        
        conn.commit()
        
        print("✅ Successfully created v2 schema tables")
        
        # Show the created tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE '%_v2%'
            ORDER BY name
        """)
        tables = cursor.fetchall()
        
        print("\n📊 Created tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} records")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating schema: {e}")
        if conn:
            conn.close()
        return False


def show_schema_info():
    """Show information about the new schema"""
    
    print("\n📋 New Tag Structure (v2) Schema:")
    print("=" * 60)
    
    print("\n1. tag_concepts_v2:")
    print("   - Stores complete concept definitions")
    print("   - Supports poly-hierarchy (multiple parents)")
    print("   - Includes visual properties (icon, color)")
    print("   - Has entity_type for semantic classification")
    
    print("\n2. tag_aliases_v2:")
    print("   - Maps all variations to canonical concepts")
    print("   - Tracks alias types (synonym, abbreviation, etc.)")
    print("   - Ensures backwards compatibility")
    
    print("\n3. tag_relations_v2:")
    print("   - Stores semantic relationships between concepts")
    print("   - Examples: 'OpenAI' --produces--> 'GPT-4'")
    print("   - Enables knowledge graph construction")
    
    print("\n4. tag_reorganization_proposals:")
    print("   - Persists GPT-5 reorganization proposals")
    print("   - Tracks approval and application status")
    print("   - Maintains full audit trail")
    
    print("\n✨ Benefits:")
    print("   - Full persistence of reorganization results")
    print("   - Support for complex hierarchies")
    print("   - Backwards compatibility via aliases")
    print("   - Rich semantic relationships")
    print("   - Visual UI enhancements")


if __name__ == "__main__":
    print("🔄 Creating Tag Concepts v2 Schema...")
    print("This will create new tables for the enhanced tag structure\n")
    
    success = create_v2_schema()
    
    if success:
        show_schema_info()
        print("\n✅ Schema creation completed successfully!")
        print("\nNext steps:")
        print("1. Update tag services to use the new tables")
        print("2. Migrate existing data to v2 structure")
        print("3. Update APIs to read/write v2 format")
    else:
        print("\n❌ Schema creation failed!")
        sys.exit(1)