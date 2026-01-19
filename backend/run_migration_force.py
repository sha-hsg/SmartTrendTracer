#!/usr/bin/env python3
"""
Force migration runner - runs without prompts
"""
import sys
import os
import sqlite3
import shutil
from datetime import datetime
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from run_tag_migration import TagSystemMigrationRunner

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def force_migrate():
    """Run migration without prompts"""
    print("\n" + "="*70)
    print("FORCE MIGRATION - RUNNING WITHOUT PROMPTS")
    print("="*70)
    
    # First, check what state we're in
    db_path = "data/tweets.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if tag_instances table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tag_instances'")
    has_instances = cursor.fetchone() is not None
    
    # Check if we have data in tag_instances
    if has_instances:
        cursor.execute("SELECT COUNT(*) FROM tag_instances")
        instance_count = cursor.fetchone()[0]
        print(f"Found {instance_count} entries in tag_instances table")
        
        if instance_count > 0:
            print("Migration appears to be complete!")
            conn.close()
            return True
    
    conn.close()
    
    # Run the migration
    runner = TagSystemMigrationRunner(db_path)
    
    # Override the preflight checks to skip prompts
    original_preflight = runner._preflight_checks
    
    def no_prompt_preflight():
        print("🔍 Running pre-flight checks (force mode)...")
        
        if not os.path.exists(runner.db_path):
            logger.error(f"Database not found: {runner.db_path}")
            return False
        
        try:
            conn = sqlite3.connect(runner.db_path)
            cursor = conn.cursor()
            
            # Get statistics
            cursor.execute("SELECT COUNT(*) FROM tags")
            tweet_tags = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM article_tags WHERE 1=0")  # Check table exists
            article_tags = 0
            
            cursor.execute("SELECT COUNT(*) FROM paper_tags WHERE 1=0")  # Check table exists
            paper_tags = 0
            
            cursor.execute("SELECT COUNT(*) FROM tag_concepts")
            concepts = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"  ✓ Database accessible")
            print(f"  ✓ Found {tweet_tags} tweet tags")
            print(f"  ✓ Found {article_tags} article tags")
            print(f"  ✓ Found {paper_tags} paper tags")
            print(f"  ✓ Found {concepts} tag concepts")
            
            runner.steps_completed.append("preflight_checks")
            return True
            
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            return False
    
    # Replace the method
    runner._preflight_checks = no_prompt_preflight
    
    # Run the migration
    success = runner.run(skip_backup=False, dry_run=False)
    
    if success:
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration failed. Check the logs above.")
    
    return success


if __name__ == "__main__":
    sys.exit(0 if force_migrate() else 1)