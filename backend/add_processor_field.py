#!/usr/bin/env python
"""
Add processor_used field to papers table
"""
import sqlite3
import sys

def add_processor_field():
    """Add processor_used column to papers table if it doesn't exist"""
    try:
        # Connect to database
        conn = sqlite3.connect('data/tweets.db')
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(papers)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'processor_used' in column_names:
            print("✅ processor_used column already exists in papers table")
            return
        
        # Add the column
        cursor.execute("ALTER TABLE papers ADD COLUMN processor_used VARCHAR(20)")
        conn.commit()
        
        print("✅ Successfully added processor_used column to papers table")
        
        # Show table structure
        cursor.execute("PRAGMA table_info(papers)")
        columns = cursor.fetchall()
        print("\nCurrent papers table structure:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error adding processor_used field: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_processor_field()