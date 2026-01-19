#!/usr/bin/env python3
"""
Rollback Script: Revert unified tag system migration
This script safely rolls back the tag migration if issues are found.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from datetime import datetime
import shutil

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TagMigrationRollback:
    """Handles rollback of the unified tag system migration"""
    
    def __init__(self, db_path: str = "../data/tweets.db"):
        """Initialize rollback with database connection"""
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        self.stats = {
            'tables_dropped': 0,
            'views_dropped': 0,
            'triggers_dropped': 0,
            'data_preserved': False,
            'backup_created': False
        }
    
    def run_rollback(self, force: bool = False, preserve_data: bool = True):
        """
        Run the rollback process.
        
        Args:
            force: Force rollback even if data will be lost
            preserve_data: Try to preserve tag data in migration log
        """
        logger.info(f"Starting rollback (force={force}, preserve_data={preserve_data})")
        
        try:
            # Step 1: Create backup
            self._create_backup()
            
            # Step 2: Check if safe to rollback
            if not force and not self._check_rollback_safety():
                logger.error("Rollback would cause data loss. Use --force to proceed anyway.")
                return False
            
            # Step 3: Preserve data if requested
            if preserve_data:
                self._preserve_tag_data()
            
            # Step 4: Drop new views
            self._drop_views()
            
            # Step 5: Drop new triggers
            self._drop_triggers()
            
            # Step 6: Drop new tables
            self._drop_tables()
            
            # Step 7: Remove migration version
            self._remove_migration_version()
            
            # Commit changes
            self.session.commit()
            logger.info("Rollback completed successfully")
            
            # Print statistics
            self._print_statistics()
            
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            self.session.rollback()
            raise
        finally:
            self.session.close()
    
    def _create_backup(self):
        """Create a backup of the database before rollback"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.db_path}.backup_{timestamp}"
        
        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Created backup at: {backup_path}")
            self.stats['backup_created'] = True
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    def _check_rollback_safety(self) -> bool:
        """Check if rollback is safe (no data loss)"""
        # Check if new tags were added after migration
        result = self.session.execute(text("""
            SELECT COUNT(*) FROM tag_instances ti
            LEFT JOIN tag_migration_log tml ON ti.id = tml.tag_instance_id
            WHERE tml.id IS NULL
        """))
        
        new_tags = result.scalar()
        
        if new_tags > 0:
            logger.warning(f"Found {new_tags} tags created after migration")
            return False
        
        # Check if old tables still have all data
        old_count = self.session.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM tags) +
                (SELECT COUNT(*) FROM article_tags) +
                (SELECT COUNT(*) FROM paper_tags) as total
        """)).scalar()
        
        new_count = self.session.execute(text("""
            SELECT COUNT(*) FROM tag_instances WHERE deleted = 0
        """)).scalar()
        
        if new_count > old_count:
            logger.warning(f"New system has {new_count - old_count} more tags than old system")
            return False
        
        return True
    
    def _preserve_tag_data(self):
        """Preserve tag data that would be lost"""
        # Export new tags to a preservation table
        self.session.execute(text("""
            CREATE TABLE IF NOT EXISTS tag_data_preservation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_type VARCHAR(20),
                content_id VARCHAR(255),
                tag VARCHAR(255),
                concept_id INTEGER,
                raw_tag VARCHAR(255),
                tag_type VARCHAR(20),
                confidence REAL,
                created_at TIMESTAMP,
                preserved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Copy all tag instances
        self.session.execute(text("""
            INSERT INTO tag_data_preservation 
            (content_type, content_id, tag, concept_id, raw_tag, tag_type, confidence, created_at)
            SELECT 
                ti.content_type,
                ti.content_id,
                tc.display_name,
                ti.concept_id,
                ti.raw_tag,
                ti.tag_type,
                ti.confidence,
                ti.created_at
            FROM tag_instances ti
            LEFT JOIN tag_concepts tc ON ti.concept_id = tc.id
            WHERE ti.deleted = 0
        """))
        
        count = self.session.execute(text("""
            SELECT COUNT(*) FROM tag_data_preservation
        """)).scalar()
        
        logger.info(f"Preserved {count} tags in tag_data_preservation table")
        self.stats['data_preserved'] = True
    
    def _drop_views(self):
        """Drop views created during migration"""
        views = [
            'tags_view',
            'article_tags_view',
            'paper_tags_view',
            'content_tags'
        ]
        
        for view in views:
            try:
                self.session.execute(text(f"DROP VIEW IF EXISTS {view}"))
                logger.info(f"Dropped view: {view}")
                self.stats['views_dropped'] += 1
            except Exception as e:
                logger.warning(f"Failed to drop view {view}: {e}")
    
    def _drop_triggers(self):
        """Drop triggers created during migration"""
        triggers = [
            'update_tag_instances_updated_at',
            'update_tag_concept_extended_updated_at',
            'update_usage_count_on_insert',
            'update_usage_count_on_delete'
        ]
        
        for trigger in triggers:
            try:
                self.session.execute(text(f"DROP TRIGGER IF EXISTS {trigger}"))
                logger.info(f"Dropped trigger: {trigger}")
                self.stats['triggers_dropped'] += 1
            except Exception as e:
                logger.warning(f"Failed to drop trigger {trigger}: {e}")
    
    def _drop_tables(self):
        """Drop tables created during migration"""
        tables = [
            'tag_instances',
            'tag_concept_extended',
            'tag_migration_log'
        ]
        
        for table in tables:
            try:
                self.session.execute(text(f"DROP TABLE IF EXISTS {table}"))
                logger.info(f"Dropped table: {table}")
                self.stats['tables_dropped'] += 1
            except Exception as e:
                logger.warning(f"Failed to drop table {table}: {e}")
    
    def _remove_migration_version(self):
        """Remove migration version entry"""
        try:
            self.session.execute(text("""
                DELETE FROM migration_version 
                WHERE name = '001_unified_tag_system'
            """))
            logger.info("Removed migration version entry")
        except Exception as e:
            logger.warning(f"Failed to remove migration version: {e}")
    
    def _print_statistics(self):
        """Print rollback statistics"""
        print("\n" + "="*60)
        print("ROLLBACK STATISTICS")
        print("="*60)
        
        print(f"Backup created:   {'Yes' if self.stats['backup_created'] else 'No'}")
        print(f"Data preserved:   {'Yes' if self.stats['data_preserved'] else 'No'}")
        print(f"Tables dropped:   {self.stats['tables_dropped']}")
        print(f"Views dropped:    {self.stats['views_dropped']}")
        print(f"Triggers dropped: {self.stats['triggers_dropped']}")
        
        print("="*60)


def restore_from_preservation():
    """
    Restore tags from preservation table back to old system.
    Run this after rollback if you need to restore preserved data.
    """
    engine = create_engine("sqlite:///../data/tweets.db")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if preservation table exists
        result = session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='tag_data_preservation'
        """))
        
        if not result.scalar():
            logger.error("No preservation table found")
            return
        
        # Restore tweet tags
        session.execute(text("""
            INSERT OR IGNORE INTO tags (tweet_id, tag, tag_type, confidence, created_at)
            SELECT content_id, tag, tag_type, confidence, created_at
            FROM tag_data_preservation
            WHERE content_type = 'tweet'
        """))
        
        # Restore article tags
        session.execute(text("""
            INSERT OR IGNORE INTO article_tags (article_id, tag, tag_type, created_at)
            SELECT content_id, tag, tag_type, created_at
            FROM tag_data_preservation
            WHERE content_type = 'article'
        """))
        
        # Restore paper tags
        session.execute(text("""
            INSERT OR IGNORE INTO paper_tags (paper_id, tag, tag_type, created_at)
            SELECT content_id, tag, tag_type, created_at
            FROM tag_data_preservation
            WHERE content_type = 'paper'
        """))
        
        session.commit()
        
        count = session.execute(text("""
            SELECT COUNT(*) FROM tag_data_preservation
        """)).scalar()
        
        logger.info(f"Restored {count} tags from preservation table")
        
    except Exception as e:
        logger.error(f"Failed to restore from preservation: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Rollback unified tag system migration")
    parser.add_argument("--force", action="store_true", help="Force rollback even if data will be lost")
    parser.add_argument("--no-preserve", action="store_true", help="Don't preserve tag data")
    parser.add_argument("--restore", action="store_true", help="Restore from preservation table")
    parser.add_argument("--db", default="../data/tweets.db", help="Database path")
    
    args = parser.parse_args()
    
    if args.restore:
        # Restore from preservation
        restore_from_preservation()
    else:
        # Run rollback
        rollback = TagMigrationRollback(args.db)
        rollback.run_rollback(
            force=args.force,
            preserve_data=not args.no_preserve
        )


if __name__ == "__main__":
    main()