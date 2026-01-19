#!/usr/bin/env python3
"""Add flag column to papers table"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
import sqlite3

def add_flag_column():
    """Add is_flagged column to papers table"""
    # Use SQLite directly
    conn = sqlite3.connect('data/tweets.db')
    cursor = conn.cursor()
    
    try:
        # Check if columns exist by querying pragma
        cursor.execute("PRAGMA table_info(papers)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'is_flagged' not in columns:
            cursor.execute("""
                ALTER TABLE papers 
                ADD COLUMN is_flagged BOOLEAN DEFAULT 0
            """)
            conn.commit()
            print("✅ Added 'is_flagged' column to papers table")
        else:
            print("Column 'is_flagged' already exists")
        
        if 'flag_notes' not in columns:
            cursor.execute("""
                ALTER TABLE papers 
                ADD COLUMN flag_notes TEXT
            """)
            conn.commit()
            print("✅ Added 'flag_notes' column to papers table")
        else:
            print("Column 'flag_notes' already exists")
            
    finally:
        conn.close()

if __name__ == "__main__":
    add_flag_column()