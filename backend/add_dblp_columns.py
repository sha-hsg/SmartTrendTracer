#!/usr/bin/env python3
"""
Add DBLP integration columns to papers table
"""
import sqlite3
import sys
from pathlib import Path

def add_dblp_columns():
    """Add dblp_key, dblp_url, and bibtex columns to papers table"""
    
    # Database path
    db_path = Path(__file__).parent / "data" / "tweets.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(papers)")
        columns = [col[1] for col in cursor.fetchall()]
        
        columns_to_add = []
        
        if 'dblp_key' not in columns:
            columns_to_add.append(('dblp_key', 'TEXT'))
            print("Adding column 'dblp_key'...")
        else:
            print("Column 'dblp_key' already exists")
        
        if 'dblp_url' not in columns:
            columns_to_add.append(('dblp_url', 'TEXT'))
            print("Adding column 'dblp_url'...")
        else:
            print("Column 'dblp_url' already exists")
        
        if 'bibtex' not in columns:
            columns_to_add.append(('bibtex', 'TEXT'))
            print("Adding column 'bibtex'...")
        else:
            print("Column 'bibtex' already exists")
        
        # Add the columns
        for col_name, col_type in columns_to_add:
            cursor.execute(f"ALTER TABLE papers ADD COLUMN {col_name} {col_type}")
            print(f"✓ Added column '{col_name}'")
        
        # Create index on dblp_key for faster lookups
        if 'dblp_key' in [col[0] for col in columns_to_add]:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_papers_dblp_key ON papers(dblp_key)")
            print("✓ Created index on dblp_key")
        
        conn.commit()
        
        if columns_to_add:
            print(f"\n✅ Successfully added {len(columns_to_add)} columns to papers table")
        else:
            print("\n✅ All DBLP columns already exist")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = add_dblp_columns()
    sys.exit(0 if success else 1)