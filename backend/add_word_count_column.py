#!/usr/bin/env python3
"""
Add word_count column to papers table
"""
import sqlite3
import sys
from pathlib import Path

def add_word_count_column():
    """Add word_count column to papers table if it doesn't exist"""
    
    # Path to the database
    db_path = Path("data/tweets.db")
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(papers)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'word_count' in column_names:
            print("✅ word_count column already exists in papers table")
            return True
        
        # Add the column
        print("Adding word_count column to papers table...")
        cursor.execute("ALTER TABLE papers ADD COLUMN word_count INTEGER")
        
        # Calculate word counts for existing papers
        print("Calculating word counts for existing papers...")
        cursor.execute("SELECT id, content FROM papers WHERE content IS NOT NULL")
        papers = cursor.fetchall()
        
        updated = 0
        for paper_id, content in papers:
            if content:
                word_count = len(content.split())
                cursor.execute(
                    "UPDATE papers SET word_count = ? WHERE id = ?",
                    (word_count, paper_id)
                )
                updated += 1
        
        conn.commit()
        print(f"✅ Successfully added word_count column and updated {updated} papers")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(papers)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'word_count' in column_names:
            print("✅ Verified: word_count column exists")
            
            # Show some statistics
            cursor.execute("SELECT COUNT(*) FROM papers")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM papers WHERE word_count IS NOT NULL")
            with_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(word_count) FROM papers WHERE word_count IS NOT NULL")
            avg_count = cursor.fetchone()[0]
            
            print(f"\n📊 Statistics:")
            print(f"   Total papers: {total}")
            print(f"   Papers with word count: {with_count}")
            if avg_count:
                print(f"   Average word count: {int(avg_count):,} words")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error adding word_count column: {e}")
        if conn:
            conn.close()
        return False

if __name__ == "__main__":
    success = add_word_count_column()
    sys.exit(0 if success else 1)