#!/usr/bin/env python3
"""
Add missing columns to paper_analyses table
"""

import sqlite3
from datetime import datetime

def add_columns():
    """Add generated_at and updated_at columns to paper_analyses table"""
    
    # Connect to database
    conn = sqlite3.connect('data/tweets.db')
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='paper_analyses'
        """)
        
        if not cursor.fetchone():
            print("Creating paper_analyses table...")
            cursor.execute("""
                CREATE TABLE paper_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id INTEGER NOT NULL,
                    analysis_type VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    model_used VARCHAR(100),
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
                )
            """)
            
            # Create unique index
            cursor.execute("""
                CREATE UNIQUE INDEX idx_paper_analysis_type 
                ON paper_analyses(paper_id, analysis_type)
            """)
            
            print("✅ Created paper_analyses table with all columns")
        else:
            # Check which columns exist
            cursor.execute("PRAGMA table_info(paper_analyses)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            print(f"Existing columns: {column_names}")
            
            # Add missing columns
            if 'generated_at' not in column_names:
                print("Adding generated_at column...")
                cursor.execute("""
                    ALTER TABLE paper_analyses 
                    ADD COLUMN generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """)
                print("✅ Added generated_at column")
            
            if 'updated_at' not in column_names:
                print("Adding updated_at column...")
                cursor.execute("""
                    ALTER TABLE paper_analyses 
                    ADD COLUMN updated_at TIMESTAMP
                """)
                print("✅ Added updated_at column")
            
            # Update existing records to have generated_at if null
            cursor.execute("""
                UPDATE paper_analyses 
                SET generated_at = CURRENT_TIMESTAMP 
                WHERE generated_at IS NULL
            """)
            
            print("✅ Updated existing records with timestamps")
        
        # Commit changes
        conn.commit()
        
        # Show current table structure
        cursor.execute("PRAGMA table_info(paper_analyses)")
        columns = cursor.fetchall()
        print("\nFinal table structure:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Show record count
        cursor.execute("SELECT COUNT(*) FROM paper_analyses")
        count = cursor.fetchone()[0]
        print(f"\nTotal analyses in database: {count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Adding columns to paper_analyses table...")
    add_columns()
    print("\nDone!")