#!/usr/bin/env python3
"""
Migrate existing tags from kebab-case to snake_case normalization
while preserving original display names
"""
import sqlite3
import sys
from pathlib import Path
import json
from typing import Dict, List, Tuple

def kebab_to_snake(tag: str) -> str:
    """Convert kebab-case to snake_case"""
    # Replace hyphens with underscores
    snake = tag.replace('-', '_')
    # Convert to lowercase
    snake = snake.lower()
    # Replace spaces with underscores
    snake = snake.replace(' ', '_')
    # Remove any non-alphanumeric characters except underscores
    snake = ''.join(c if c.isalnum() or c == '_' else '_' for c in snake)
    # Replace multiple underscores with single
    while '__' in snake:
        snake = snake.replace('__', '_')
    # Remove leading/trailing underscores
    snake = snake.strip('_')
    return snake

def create_display_name(original_tag: str) -> str:
    """Create a human-readable display name from the original tag"""
    # Common acronyms that should stay uppercase
    acronyms = {
        'ai', 'ml', 'llm', 'llms', 'gpt', 'bert', 'api', 'url', 'uri', 'http', 'https',
        'nlp', 'cv', 'rl', 'gan', 'gans', 'vae', 'cnn', 'rnn', 'lstm', 'gru', 'mlp',
        'agi', 'sota', 'rlhf', 'sft', 'dpo', 'ppo', 'kl', 'elbo', 'vqvae', 'clip',
        'gpu', 'cpu', 'tpu', 'ram', 'vram', 'cuda', 'rocm', 'onnx', 'gguf', 'ggml',
        'pdf', 'html', 'xml', 'json', 'yaml', 'csv', 'sql', 'aws', 'gcp', 'azure'
    }
    
    # Handle special cases like GPT-4, GPT-5, etc.
    if original_tag.lower().startswith('gpt-'):
        return original_tag.upper().replace('GPT-', 'GPT-')
    if original_tag.lower().startswith('gpt_'):
        return 'GPT-' + original_tag[4:].upper()
    
    # Split by hyphens or underscores
    parts = original_tag.replace('_', '-').split('-')
    
    # Process each part
    display_parts = []
    for part in parts:
        if part.lower() in acronyms:
            display_parts.append(part.upper())
        elif part and part[0].isupper() and part[1:].islower():
            # Already properly capitalized
            display_parts.append(part)
        elif part.isupper() and len(part) > 1:
            # All caps, likely an acronym
            display_parts.append(part)
        else:
            # Capitalize first letter
            display_parts.append(part.capitalize() if part else '')
    
    # Join with spaces for display
    display = ' '.join(display_parts)
    
    # Handle parentheses for acronyms
    if len(display_parts) == 1 and display_parts[0].isupper() and len(display_parts[0]) <= 5:
        # Just an acronym, no need for expansion
        return display
    
    return display

def migrate_tags_table():
    """Add slug and display_name columns to tag tables"""
    db_path = Path("data/tweets.db")
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all unique tags from different sources
        all_tags = set()
        
        # Tweet tags
        cursor.execute("SELECT DISTINCT tag FROM tags")
        tweet_tags = cursor.fetchall()
        all_tags.update([t[0] for t in tweet_tags if t[0]])
        
        # Paper tags
        cursor.execute("SELECT DISTINCT tag FROM paper_tags")
        paper_tags = cursor.fetchall()
        all_tags.update([t[0] for t in paper_tags if t[0]])
        
        # Article tags
        cursor.execute("SELECT DISTINCT tag FROM article_tags")
        article_tags = cursor.fetchall()
        all_tags.update([t[0] for t in article_tags if t[0]])
        
        print(f"Found {len(all_tags)} unique tags to migrate")
        
        # Create mapping table for tag normalization
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tag_normalization (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_tag TEXT UNIQUE NOT NULL,
                slug TEXT NOT NULL,
                display_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create mappings for all tags
        mappings = []
        for tag in all_tags:
            slug = kebab_to_snake(tag)
            display = create_display_name(tag)
            mappings.append((tag, slug, display))
            
        # Insert mappings
        cursor.executemany(
            "INSERT OR IGNORE INTO tag_normalization (original_tag, slug, display_name) VALUES (?, ?, ?)",
            mappings
        )
        
        conn.commit()
        print(f"✅ Created {len(mappings)} tag mappings")
        
        # Show some examples
        print("\n📊 Sample migrations:")
        for i, (orig, slug, display) in enumerate(mappings[:10]):
            print(f"  {orig:30} → {slug:30} | Display: {display}")
        
        # Show statistics
        print(f"\n📈 Migration statistics:")
        print(f"  Total unique tags: {len(all_tags)}")
        print(f"  Tweet tags: {len(tweet_tags)}")
        print(f"  Paper tags: {len(paper_tags)}")
        print(f"  Article tags: {len(article_tags)}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if conn:
            conn.close()
        return False

def update_tag_concepts():
    """Update tag_concepts table with slugs"""
    db_path = Path("data/tweets.db")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tag_concepts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tag_concepts'")
        if not cursor.fetchone():
            print("ℹ️ tag_concepts table doesn't exist yet, skipping concept updates")
            conn.close()
            return True
        
        # Add slug column if it doesn't exist
        cursor.execute("PRAGMA table_info(tag_concepts)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'slug' not in column_names:
            print("Adding slug column to tag_concepts...")
            cursor.execute("ALTER TABLE tag_concepts ADD COLUMN slug TEXT")
        
        # Update slugs for existing concepts
        cursor.execute("SELECT id, tag FROM tag_concepts")
        concepts = cursor.fetchall()
        
        for concept_id, tag in concepts:
            slug = kebab_to_snake(tag)
            cursor.execute(
                "UPDATE tag_concepts SET slug = ? WHERE id = ?",
                (slug, concept_id)
            )
        
        conn.commit()
        print(f"✅ Updated {len(concepts)} tag concepts with slugs")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"⚠️ Could not update tag_concepts: {e}")
        if conn:
            conn.close()
        return True  # Not critical if this fails

if __name__ == "__main__":
    print("🔄 Starting tag normalization migration...")
    print("Converting from kebab-case to snake_case\n")
    
    success = migrate_tags_table()
    if success:
        update_tag_concepts()
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Update tag services to use the new normalization")
        print("2. Update UI components to use display_name")
        print("3. Test tag filtering and search")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)