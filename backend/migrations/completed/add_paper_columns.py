"""
Add missing columns to papers table
"""
import sqlite3
import sys

def add_columns():
    """Add missing columns to papers table"""
    
    db_path = "data/tweets.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if papers table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='papers'
        """)
        
        if not cursor.fetchone():
            print("Papers table doesn't exist. Creating it...")
            # Create papers table with all columns
            cursor.execute("""
                CREATE TABLE papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    authors TEXT,
                    abstract TEXT,
                    content TEXT,
                    arxiv_id TEXT UNIQUE,
                    pdf_url TEXT,
                    published_date TEXT,
                    categories TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Papers table created")
        else:
            # Table exists, check for missing columns
            cursor.execute("PRAGMA table_info(papers)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Add missing columns
            if 'arxiv_id' not in columns:
                cursor.execute("ALTER TABLE papers ADD COLUMN arxiv_id TEXT UNIQUE")
                print("✅ Added arxiv_id column")
            
            if 'pdf_url' not in columns:
                cursor.execute("ALTER TABLE papers ADD COLUMN pdf_url TEXT")
                print("✅ Added pdf_url column")
            
            if 'published_date' not in columns:
                cursor.execute("ALTER TABLE papers ADD COLUMN published_date TEXT")
                print("✅ Added published_date column")
            
            if 'categories' not in columns:
                cursor.execute("ALTER TABLE papers ADD COLUMN categories TEXT")
                print("✅ Added categories column")
        
        # Create paper_repository table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_repository (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER NOT NULL UNIQUE,
                pdf_original_path TEXT,
                pdf_processed_path TEXT,
                markdown_path TEXT,
                images_path TEXT,
                pdf_processed BOOLEAN DEFAULT FALSE,
                markdown_generated BOOLEAN DEFAULT FALSE,
                analyses_completed TEXT,
                pdf_size_bytes INTEGER,
                processor_used TEXT,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (paper_id) REFERENCES papers (id)
            )
        """)
        print("✅ Paper repository table ready")
        
        # Create paper_analyses table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER NOT NULL,
                analysis_type TEXT NOT NULL,
                analysis_name TEXT,
                content TEXT,
                model_used TEXT,
                word_count INTEGER,
                tokens_used INTEGER,
                is_latest BOOLEAN DEFAULT TRUE,
                user_rating INTEGER,
                user_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paper_id) REFERENCES papers (id)
            )
        """)
        print("✅ Paper analyses table ready")
        
        # Create analysis_prompts table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_key TEXT UNIQUE NOT NULL,
                prompt_name TEXT NOT NULL,
                system_prompt TEXT,
                template TEXT NOT NULL,
                description TEXT,
                category TEXT,
                icon TEXT,
                color TEXT,
                display_order INTEGER DEFAULT 0,
                is_fixed BOOLEAN DEFAULT TRUE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Analysis prompts table ready")
        
        conn.commit()
        print("\n✅ All database updates complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    add_columns()