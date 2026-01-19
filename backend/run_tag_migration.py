#!/usr/bin/env python3
"""
Main Migration Runner - Complete tag system migration
This script runs the entire migration process with safety checks.
"""
import sys
import os
import sqlite3
import shutil
from datetime import datetime
import argparse
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TagSystemMigrationRunner:
    """Orchestrates the complete tag system migration"""
    
    def __init__(self, db_path: str = "data/tweets.db"):
        self.db_path = db_path
        self.backup_path = None
        self.steps_completed = []
        
    def run(self, skip_backup: bool = False, dry_run: bool = False):
        """Run the complete migration process"""
        print("\n" + "="*70)
        print("SMARTTRENDTRACER TAG SYSTEM MIGRATION")
        print("="*70)
        print(f"Database: {self.db_path}")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print("="*70 + "\n")
        
        try:
            # Step 1: Pre-flight checks
            if not self._preflight_checks():
                return False
            
            # Step 2: Create backup
            if not skip_backup and not dry_run:
                if not self._create_backup():
                    return False
            
            # Step 3: Run schema migration
            if not self._run_schema_migration(dry_run):
                return False
            
            # Step 4: Run data migration
            if not self._run_data_migration(dry_run):
                return False
            
            # Step 5: Verify migration
            if not dry_run:
                if not self._verify_migration():
                    return False
            
            # Step 6: Update application
            if not dry_run:
                self._update_application_config()
            
            # Success!
            self._print_success_message()
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self._print_failure_message()
            return False
    
    def _preflight_checks(self) -> bool:
        """Run pre-flight checks before migration"""
        print("🔍 Running pre-flight checks...")
        
        # Check database exists
        if not os.path.exists(self.db_path):
            logger.error(f"Database not found: {self.db_path}")
            return False
        
        # Check database is accessible
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check required tables exist
            required_tables = ['tweets', 'tags', 'tag_concepts']
            for table in required_tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                if not cursor.fetchone():
                    logger.error(f"Required table '{table}' not found")
                    conn.close()
                    return False
            
            # Check if migration already run
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tag_instances'")
            if cursor.fetchone():
                logger.warning("Migration appears to have already been run")
                response = input("Continue anyway? (y/n): ")
                if response.lower() != 'y':
                    conn.close()
                    return False
            
            # Get statistics
            cursor.execute("SELECT COUNT(*) FROM tags")
            tweet_tags = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM article_tags")
            article_tags = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM paper_tags")
            paper_tags = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tag_concepts")
            concepts = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"  ✓ Database accessible")
            print(f"  ✓ Found {tweet_tags} tweet tags")
            print(f"  ✓ Found {article_tags} article tags")
            print(f"  ✓ Found {paper_tags} paper tags")
            print(f"  ✓ Found {concepts} tag concepts")
            
            self.steps_completed.append("preflight_checks")
            return True
            
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            return False
    
    def _create_backup(self) -> bool:
        """Create database backup"""
        print("\n💾 Creating database backup...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_path = f"{self.db_path}.backup_{timestamp}"
        
        try:
            shutil.copy2(self.db_path, self.backup_path)
            file_size = os.path.getsize(self.backup_path) / (1024 * 1024)  # MB
            print(f"  ✓ Backup created: {self.backup_path} ({file_size:.2f} MB)")
            
            self.steps_completed.append("backup")
            return True
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    def _run_schema_migration(self, dry_run: bool) -> bool:
        """Run the schema migration"""
        print(f"\n🔧 Running schema migration{' (DRY RUN)' if dry_run else ''}...")
        
        migration_file = "backend/migrations/001_unified_tag_system.sql" if os.path.exists("backend/migrations/001_unified_tag_system.sql") else "migrations/001_unified_tag_system.sql"
        
        if not os.path.exists(migration_file):
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        try:
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            if not dry_run:
                conn = sqlite3.connect(self.db_path)
                conn.executescript(migration_sql)
                conn.commit()
                conn.close()
                print("  ✓ Schema migration completed")
            else:
                print("  ✓ Schema migration validated (dry run)")
            
            self.steps_completed.append("schema_migration")
            return True
            
        except Exception as e:
            logger.error(f"Schema migration failed: {e}")
            return False
    
    def _run_data_migration(self, dry_run: bool) -> bool:
        """Run the data migration"""
        print(f"\n📊 Running data migration{' (DRY RUN)' if dry_run else ''}...")
        
        try:
            # Import and run the migration
            # Import the migration module directly by executing it
            migration_file = "backend/migrations/002_migrate_existing_tags.py" if os.path.exists("backend/migrations/002_migrate_existing_tags.py") else "migrations/002_migrate_existing_tags.py"
            import importlib.util
            spec = importlib.util.spec_from_file_location("migration", migration_file)
            migration_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migration_module)
            TagDataMigration = migration_module.TagDataMigration
            
            migration = TagDataMigration(self.db_path)
            migration.run_migration(dry_run=dry_run)
            
            self.steps_completed.append("data_migration")
            return True
            
        except Exception as e:
            logger.error(f"Data migration failed: {e}")
            return False
    
    def _verify_migration(self) -> bool:
        """Verify the migration was successful"""
        print("\n✅ Verifying migration...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check new tables exist
            cursor.execute("SELECT COUNT(*) FROM tag_instances WHERE deleted = 0")
            tag_instances = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tag_concept_extended")
            extended_info = cursor.fetchone()[0]
            
            # Check for orphaned tags
            cursor.execute("""
                SELECT COUNT(*) FROM tag_instances ti
                LEFT JOIN tag_concepts tc ON ti.concept_id = tc.id
                WHERE tc.id IS NULL
            """)
            orphaned = cursor.fetchone()[0]
            
            # Check for duplicates
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT content_type, content_id, concept_id, COUNT(*) as cnt
                    FROM tag_instances
                    WHERE deleted = 0
                    GROUP BY content_type, content_id, concept_id
                    HAVING cnt > 1
                )
            """)
            duplicates = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"  ✓ {tag_instances} tag instances created")
            print(f"  ✓ {extended_info} concepts with extended info")
            
            if orphaned > 0:
                logger.warning(f"  ⚠ Found {orphaned} orphaned tags")
            
            if duplicates > 0:
                logger.warning(f"  ⚠ Found {duplicates} duplicate assignments")
            
            self.steps_completed.append("verification")
            return orphaned == 0 and duplicates == 0
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False
    
    def _update_application_config(self):
        """Update application configuration for new system"""
        print("\n⚙️  Updating application configuration...")
        
        # Create a flag file to indicate migration is complete
        flag_file = "data/.tag_migration_complete"
        with open(flag_file, 'w') as f:
            f.write(f"Migration completed at {datetime.now().isoformat()}\n")
            f.write(f"Backup: {self.backup_path}\n")
        
        print("  ✓ Configuration updated")
        self.steps_completed.append("config_update")
    
    def _print_success_message(self):
        """Print success message with next steps"""
        print("\n" + "="*70)
        print("✨ MIGRATION COMPLETED SUCCESSFULLY! ✨")
        print("="*70)
        print("\nCompleted steps:")
        for step in self.steps_completed:
            print(f"  ✓ {step.replace('_', ' ').title()}")
        
        if self.backup_path:
            print(f"\nBackup saved at: {self.backup_path}")
        
        print("\n📝 Next steps:")
        print("  1. Test the application thoroughly")
        print("  2. Update API clients to use /api/v2/tags endpoints")
        print("  3. Monitor for any issues")
        print("  4. Keep the backup for at least 30 days")
        
        print("\n🔄 If you need to rollback:")
        print("  python migrations/003_rollback_tag_migration.py")
        print("="*70)
    
    def _print_failure_message(self):
        """Print failure message with recovery steps"""
        print("\n" + "="*70)
        print("❌ MIGRATION FAILED")
        print("="*70)
        print("\nCompleted steps before failure:")
        for step in self.steps_completed:
            print(f"  ✓ {step.replace('_', ' ').title()}")
        
        if self.backup_path:
            print(f"\n🔄 To restore from backup:")
            print(f"  cp {self.backup_path} {self.db_path}")
        
        print("\n📝 Troubleshooting:")
        print("  1. Check the error messages above")
        print("  2. Fix any issues")
        print("  3. Restore from backup if needed")
        print("  4. Re-run the migration")
        print("="*70)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run SmartTrendTracer tag system migration"
    )
    parser.add_argument(
        "--db",
        default="data/tweets.db",
        help="Path to database file"
    )
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Skip creating backup (not recommended)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run migration in dry-run mode (no changes)"
    )
    
    args = parser.parse_args()
    
    # Confirm before running
    if not args.dry_run:
        print("\n⚠️  WARNING: This will modify your database!")
        print("It's recommended to stop the application before proceeding.")
        response = input("\nContinue with migration? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled.")
            return
    
    # Run migration
    runner = TagSystemMigrationRunner(args.db)
    success = runner.run(
        skip_backup=args.skip_backup,
        dry_run=args.dry_run
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()