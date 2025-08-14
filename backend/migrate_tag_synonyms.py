#!/usr/bin/env python3
"""
Migrate tag_synonyms table to use concept_id instead of primary_tag
"""
import sqlite3
from datetime import datetime

def migrate_tag_synonyms():
    conn = sqlite3.connect('data/tweets.db')
    cursor = conn.cursor()
    
    try:
        # Check if migration is needed
        cursor.execute("PRAGMA table_info(tag_synonyms)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'concept_id' in column_names:
            print("Migration already completed - concept_id column exists")
            return
        
        print("Starting migration of tag_synonyms table...")
        
        # Create new table with correct schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tag_synonyms_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_id INTEGER NOT NULL,
                synonym_tag VARCHAR(100) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(50),
                FOREIGN KEY (concept_id) REFERENCES tag_concepts(id)
            )
        """)
        
        # Create index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tag_synonyms_synonym_new 
            ON tag_synonyms_new(synonym_tag)
        """)
        
        # Migrate existing data if any
        cursor.execute("SELECT COUNT(*) FROM tag_synonyms")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"Migrating {count} existing synonyms...")
            
            # Get all existing synonyms
            cursor.execute("SELECT * FROM tag_synonyms")
            synonyms = cursor.fetchall()
            
            for synonym in synonyms:
                # Try to find concept by primary_tag
                primary_tag = synonym[1]  # primary_tag column
                synonym_tag = synonym[2]  # synonym_tag column
                
                cursor.execute("""
                    SELECT id FROM tag_concepts 
                    WHERE tag = ? OR display_name = ?
                """, (primary_tag, primary_tag))
                
                concept = cursor.fetchone()
                if concept:
                    concept_id = concept[0]
                    cursor.execute("""
                        INSERT OR IGNORE INTO tag_synonyms_new 
                        (concept_id, synonym_tag, created_at, created_by)
                        VALUES (?, ?, ?, ?)
                    """, (concept_id, synonym_tag, synonym[3], 'migration'))
                    print(f"  Migrated synonym: {synonym_tag} -> concept {concept_id}")
                else:
                    print(f"  Warning: Could not find concept for primary_tag: {primary_tag}")
        
        # Drop old table and rename new one
        cursor.execute("DROP TABLE tag_synonyms")
        cursor.execute("ALTER TABLE tag_synonyms_new RENAME TO tag_synonyms")
        
        conn.commit()
        print("Migration completed successfully!")
        
        # Verify the new schema
        cursor.execute("PRAGMA table_info(tag_synonyms)")
        columns = cursor.fetchall()
        print("\nNew table schema:")
        for col in columns:
            print(f"  {col[1]} {col[2]}")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_tag_synonyms()