"""
Tag normalization and migration script
- Creates tag_synonyms table for sameAs relationships
- Migrates tags to proper capitalized forms
- Reassigns tweets and articles to normalized tags
"""
import sqlite3
import json
from datetime import datetime

def create_tag_synonyms_table(conn):
    """Create table for tag synonym relationships"""
    cursor = conn.cursor()
    
    # Drop old table if exists to ensure clean schema
    cursor.execute("DROP TABLE IF EXISTS tag_synonyms")
    
    # Create tag_synonyms table
    cursor.execute("""
        CREATE TABLE tag_synonyms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            primary_tag TEXT NOT NULL,
            synonym_tag TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(primary_tag, synonym_tag)
        )
    """)
    
    # Create index for efficient lookups
    cursor.execute("""
        CREATE INDEX idx_tag_synonyms_primary 
        ON tag_synonyms(primary_tag)
    """)
    
    cursor.execute("""
        CREATE INDEX idx_tag_synonyms_synonym 
        ON tag_synonyms(synonym_tag)
    """)
    
    conn.commit()
    print("✓ Created tag_synonyms table")

def backup_tags(conn):
    """Create backup of current tags before migration"""
    cursor = conn.cursor()
    
    # Create backup tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags_backup AS 
        SELECT * FROM tags
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS article_tags_backup AS 
        SELECT * FROM article_tags
    """)
    
    conn.commit()
    print("✓ Created backup of tags tables")

def migrate_tags(conn, proper_forms, needs_sameas):
    """Migrate tags to their proper forms"""
    cursor = conn.cursor()
    
    migration_log = []
    
    # Process tags with clear proper forms
    for tag_lower, proper_form in proper_forms.items():
        # Get all variants of this tag
        cursor.execute("""
            SELECT DISTINCT tag FROM tags 
            WHERE LOWER(tag) = ? AND tag != ?
        """, (tag_lower, proper_form))
        
        variants = [row[0] for row in cursor.fetchall()]
        
        if variants:
            print(f"\nMigrating '{tag_lower}' variants to '{proper_form}':")
            
            for variant in variants:
                # Count affected tweets
                cursor.execute("SELECT COUNT(*) FROM tags WHERE tag = ?", (variant,))
                tweet_count = cursor.fetchone()[0]
                
                # Count affected articles
                cursor.execute("SELECT COUNT(*) FROM article_tags WHERE tag = ?", (variant,))
                article_count = cursor.fetchone()[0]
                
                print(f"  '{variant}' → '{proper_form}' (tweets: {tweet_count}, articles: {article_count})")
                
                # Update tweets tags - check for duplicates first
                cursor.execute("""
                    SELECT t1.id, t1.tweet_id 
                    FROM tags t1
                    WHERE t1.tag = ?
                    AND EXISTS (
                        SELECT 1 FROM tags t2 
                        WHERE t2.tweet_id = t1.tweet_id 
                        AND t2.tag = ?
                    )
                """, (variant, proper_form))
                
                duplicate_tweet_tags = cursor.fetchall()
                
                if duplicate_tweet_tags:
                    # Delete duplicate entries (keeping the proper form)
                    for tag_id, tweet_id in duplicate_tweet_tags:
                        cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
                        print(f"    Removed duplicate tag for tweet {tweet_id}")
                
                # Update remaining entries
                cursor.execute("""
                    UPDATE tags 
                    SET tag = ? 
                    WHERE tag = ?
                """, (proper_form, variant))
                
                # Update article tags - check for duplicates first
                cursor.execute("""
                    SELECT a1.id, a1.article_id 
                    FROM article_tags a1
                    WHERE a1.tag = ?
                    AND EXISTS (
                        SELECT 1 FROM article_tags a2 
                        WHERE a2.article_id = a1.article_id 
                        AND a2.tag = ?
                    )
                """, (variant, proper_form))
                
                duplicate_article_tags = cursor.fetchall()
                
                if duplicate_article_tags:
                    # Delete duplicate entries (keeping the proper form)
                    for tag_id, article_id in duplicate_article_tags:
                        cursor.execute("DELETE FROM article_tags WHERE id = ?", (tag_id,))
                        print(f"    Removed duplicate tag for article {article_id}")
                
                # Update remaining entries
                cursor.execute("""
                    UPDATE article_tags 
                    SET tag = ? 
                    WHERE tag = ?
                """, (proper_form, variant))
                
                migration_log.append({
                    'from': variant,
                    'to': proper_form,
                    'tweet_count': tweet_count,
                    'article_count': article_count,
                    'action': 'migrated'
                })
    
    # Process tags needing sameAs relations
    for tag_group in needs_sameas:
        tags = [v for v in tag_group]
        if len(tags) >= 2:
            # Use the most common variant as primary
            primary = tags[0]  # Already sorted by usage
            print(f"\nCreating sameAs relations for '{primary}':")
            
            for synonym in tags[1:]:
                cursor.execute("""
                    INSERT OR IGNORE INTO tag_synonyms (primary_tag, synonym_tag)
                    VALUES (?, ?)
                """, (primary, synonym))
                print(f"  '{synonym}' → sameAs → '{primary}'")
                
                migration_log.append({
                    'primary': primary,
                    'synonym': synonym,
                    'action': 'sameAs'
                })
    
    conn.commit()
    
    # Save migration log
    with open('tag_migration_log.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'migrations': migration_log
        }, f, indent=2)
    
    print(f"\n✓ Migration complete. Log saved to tag_migration_log.json")
    return migration_log

def verify_migration(conn):
    """Verify the migration was successful"""
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print("MIGRATION VERIFICATION")
    print("=" * 80)
    
    # Check for remaining case variants
    cursor.execute("""
        SELECT tag, COUNT(*) as count 
        FROM tags 
        GROUP BY LOWER(tag)
        HAVING COUNT(DISTINCT tag) > 1
    """)
    
    remaining_variants = cursor.fetchall()
    
    if remaining_variants:
        print("\n⚠️  Remaining case variants in tweets:")
        for tag, count in remaining_variants:
            print(f"  {tag}: {count}")
    else:
        print("\n✓ No case variants remaining in tweet tags")
    
    # Check article tags
    cursor.execute("""
        SELECT tag, COUNT(*) as count 
        FROM article_tags 
        GROUP BY LOWER(tag)
        HAVING COUNT(DISTINCT tag) > 1
    """)
    
    remaining_article_variants = cursor.fetchall()
    
    if remaining_article_variants:
        print("\n⚠️  Remaining case variants in articles:")
        for tag, count in remaining_article_variants:
            print(f"  {tag}: {count}")
    else:
        print("\n✓ No case variants remaining in article tags")
    
    # Count tag synonyms
    cursor.execute("SELECT COUNT(*) FROM tag_synonyms")
    synonym_count = cursor.fetchone()[0]
    print(f"\n✓ Created {synonym_count} tag synonym relationships")
    
    # Show new tag statistics
    cursor.execute("SELECT COUNT(DISTINCT tag) FROM tags")
    unique_tweet_tags = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT tag) FROM article_tags")
    unique_article_tags = cursor.fetchone()[0]
    
    print(f"\n📊 Final Statistics:")
    print(f"  Unique tweet tags: {unique_tweet_tags}")
    print(f"  Unique article tags: {unique_article_tags}")

def main():
    # Load normalization plan
    with open('tag_normalization_plan.json', 'r') as f:
        plan = json.load(f)
    
    print("=" * 80)
    print("TAG NORMALIZATION MIGRATION")
    print("=" * 80)
    print(f"Tags to migrate: {len(plan['proper_forms'])}")
    print(f"Tags needing sameAs: {len(plan['needs_sameas'])}")
    
    # Connect to database
    conn = sqlite3.connect('data/tweets.db')
    
    try:
        # Create backup
        backup_tags(conn)
        
        # Create synonyms table
        create_tag_synonyms_table(conn)
        
        # Run migration
        migrate_tags(conn, plan['proper_forms'], plan['needs_sameas'])
        
        # Verify results
        verify_migration(conn)
        
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        print("Rolling back changes...")
        conn.rollback()
        
        # Offer to restore from backup
        print("\nTo restore from backup, run:")
        print("  DROP TABLE tags;")
        print("  CREATE TABLE tags AS SELECT * FROM tags_backup;")
        print("  DROP TABLE article_tags;")
        print("  CREATE TABLE article_tags AS SELECT * FROM article_tags_backup;")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()