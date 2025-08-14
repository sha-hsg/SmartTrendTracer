#!/usr/bin/env python3
"""
Fix duplicate tags in the database
- Removes duplicate tag entries for the same tweet
- Adds unique constraint to prevent future duplicates
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from sqlalchemy import text
from collections import defaultdict

def analyze_duplicates(db):
    """Analyze duplicate tags in the database"""
    print("🔍 ANALYZING DUPLICATE TAGS")
    print("=" * 60)
    
    # Find all duplicates
    result = db.execute(text("""
        SELECT tweet_id, tag, COUNT(*) as count, GROUP_CONCAT(id) as ids
        FROM tags 
        GROUP BY tweet_id, tag 
        HAVING COUNT(*) > 1 
        ORDER BY count DESC
        LIMIT 20
    """))
    
    duplicates = result.fetchall()
    
    if not duplicates:
        print("✅ No duplicate tags found!")
        return False
    
    print(f"Found {len(duplicates)} unique tag duplications")
    print("\nTop duplicates:")
    for tweet_id, tag, count, ids in duplicates[:5]:
        print(f"  Tweet {tweet_id}: '{tag}' appears {count} times (IDs: {ids})")
    
    # Get total counts
    result = db.execute(text("""
        SELECT 
            COUNT(DISTINCT tweet_id) as affected_tweets,
            SUM(count - 1) as duplicate_entries,
            COUNT(*) as unique_duplications
        FROM (
            SELECT tweet_id, tag, COUNT(*) as count
            FROM tags 
            GROUP BY tweet_id, tag 
            HAVING COUNT(*) > 1
        )
    """))
    
    stats = result.fetchone()
    print(f"\n📊 Statistics:")
    print(f"  - Affected tweets: {stats[0]}")
    print(f"  - Duplicate entries to remove: {stats[1]}")
    print(f"  - Unique tag duplications: {stats[2]}")
    
    return True

def remove_duplicates(db):
    """Remove duplicate tags, keeping the earliest entry"""
    print("\n🧹 REMOVING DUPLICATES")
    print("=" * 60)
    
    # First, get count of tags before
    result = db.execute(text("SELECT COUNT(*) FROM tags"))
    count_before = result.scalar()
    print(f"Tags before cleanup: {count_before}")
    
    # Get duplicates with their IDs
    result = db.execute(text("""
        SELECT tweet_id, tag, GROUP_CONCAT(id) as ids, COUNT(*) as count
        FROM tags 
        GROUP BY tweet_id, tag 
        HAVING COUNT(*) > 1
    """))
    
    duplicates = result.fetchall()
    total_removed = 0
    
    for tweet_id, tag, ids_str, count in duplicates:
        # Parse IDs and keep only the minimum (earliest)
        ids = [int(id_str) for id_str in ids_str.split(',')]
        min_id = min(ids)
        ids_to_remove = [id for id in ids if id != min_id]
        
        # Remove duplicates
        for id_to_remove in ids_to_remove:
            db.execute(text("DELETE FROM tags WHERE id = :id"), {"id": id_to_remove})
            total_removed += 1
    
    # Commit the changes
    db.commit()
    
    # Get count after
    result = db.execute(text("SELECT COUNT(*) FROM tags"))
    count_after = result.scalar()
    
    print(f"✅ Removed {total_removed} duplicate entries")
    print(f"Tags after cleanup: {count_after}")
    print(f"Reduction: {count_before - count_after} tags")
    
    return total_removed

def add_unique_constraint(db):
    """Add unique constraint to prevent future duplicates"""
    print("\n🔒 ADDING UNIQUE CONSTRAINT")
    print("=" * 60)
    
    try:
        # Check if index already exists
        result = db.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name='idx_tweet_tag_unique'
        """))
        
        if result.fetchone():
            print("ℹ️  Unique constraint already exists")
            return False
        
        # Create unique index
        db.execute(text("""
            CREATE UNIQUE INDEX idx_tweet_tag_unique 
            ON tags(tweet_id, tag)
        """))
        db.commit()
        
        print("✅ Added unique constraint on (tweet_id, tag)")
        print("   Future duplicate tags will be prevented at database level")
        return True
        
    except Exception as e:
        print(f"⚠️  Could not add constraint: {e}")
        return False

def verify_fix(db):
    """Verify no duplicates remain"""
    print("\n✓ VERIFICATION")
    print("=" * 60)
    
    result = db.execute(text("""
        SELECT COUNT(*) as duplicate_count
        FROM (
            SELECT tweet_id, tag, COUNT(*) as count
            FROM tags 
            GROUP BY tweet_id, tag 
            HAVING COUNT(*) > 1
        )
    """))
    
    duplicate_count = result.scalar()
    
    if duplicate_count == 0:
        print("✅ No duplicate tags found - database is clean!")
        
        # Show sample of current tags
        result = db.execute(text("""
            SELECT t.author_username, COUNT(DISTINCT g.tag) as unique_tags
            FROM tweets t
            JOIN tags g ON t.id = g.tweet_id
            GROUP BY t.author_username
            ORDER BY unique_tags DESC
        """))
        
        print("\n📊 Tags by author:")
        for username, tag_count in result.fetchall():
            print(f"  @{username}: {tag_count} unique tags")
            
    else:
        print(f"❌ Still found {duplicate_count} duplicates - manual intervention needed")
    
    return duplicate_count == 0

def main():
    """Main function to fix duplicate tags"""
    print("🛠️  DUPLICATE TAG FIX UTILITY")
    print("=" * 60)
    print()
    
    db = next(get_db())
    
    try:
        # 1. Analyze the problem
        has_duplicates = analyze_duplicates(db)
        
        if not has_duplicates:
            print("\n🎉 No duplicates found - nothing to fix!")
            return
        
        # 2. Confirm before proceeding
        print("\n⚠️  This will remove duplicate tags from the database.")
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
        
        # 3. Remove duplicates
        removed = remove_duplicates(db)
        
        # 4. Add constraint
        add_unique_constraint(db)
        
        # 5. Verify
        if verify_fix(db):
            print("\n🎉 SUCCESS! All duplicate tags have been removed.")
            print("   The database now has a unique constraint to prevent future duplicates.")
        else:
            print("\n⚠️  Some issues remain. Please check manually.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()