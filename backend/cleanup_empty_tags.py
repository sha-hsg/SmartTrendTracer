"""
Clean up empty tags from the database
"""
import sqlite3

def cleanup_empty_tags():
    conn = sqlite3.connect('data/tweets.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("CLEANING UP EMPTY TAGS")
    print("=" * 80)
    
    # Check for empty tags in tweets
    cursor.execute("""
        SELECT COUNT(*) FROM tags 
        WHERE tag IS NULL OR tag = '' OR trim(tag) = ''
    """)
    empty_tweet_tags = cursor.fetchone()[0]
    print(f"\nFound {empty_tweet_tags} empty tags in tweets")
    
    if empty_tweet_tags > 0:
        # Delete empty tags from tweets
        cursor.execute("""
            DELETE FROM tags 
            WHERE tag IS NULL OR tag = '' OR trim(tag) = ''
        """)
        print(f"  ✓ Deleted {empty_tweet_tags} empty tweet tags")
    
    # Check for empty tags in articles
    cursor.execute("""
        SELECT COUNT(*) FROM article_tags 
        WHERE tag IS NULL OR tag = '' OR trim(tag) = ''
    """)
    empty_article_tags = cursor.fetchone()[0]
    print(f"\nFound {empty_article_tags} empty tags in articles")
    
    if empty_article_tags > 0:
        # Show which articles have empty tags
        cursor.execute("""
            SELECT a.id, a.title, COUNT(*) as empty_count
            FROM substack_articles a
            JOIN article_tags t ON a.id = t.article_id
            WHERE t.tag IS NULL OR t.tag = '' OR trim(t.tag) = ''
            GROUP BY a.id, a.title
        """)
        
        articles_with_empty = cursor.fetchall()
        if articles_with_empty:
            print("\nArticles with empty tags:")
            for article_id, title, count in articles_with_empty:
                print(f"  - Article {article_id}: '{title[:50]}...' has {count} empty tag(s)")
        
        # Delete empty tags from articles
        cursor.execute("""
            DELETE FROM article_tags 
            WHERE tag IS NULL OR tag = '' OR trim(tag) = ''
        """)
        print(f"\n  ✓ Deleted {empty_article_tags} empty article tags")
    
    # Add constraint to prevent empty tags in future (if not exists)
    # Note: SQLite doesn't support adding CHECK constraints to existing tables
    # but we can document this for future schema updates
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 80)
    print("CLEANUP COMPLETE")
    print("=" * 80)
    
    if empty_tweet_tags > 0 or empty_article_tags > 0:
        print("\n✅ Successfully removed all empty tags from the database")
    else:
        print("\n✅ No empty tags found - database is clean")

if __name__ == "__main__":
    cleanup_empty_tags()