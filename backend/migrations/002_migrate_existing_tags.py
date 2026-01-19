#!/usr/bin/env python3
"""
Data Migration Script: Migrate existing tags to unified tag system
This script migrates all existing tags from the old tables to the new unified structure.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging
from typing import Dict, Optional, Set
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TagDataMigration:
    """Handles migration of existing tags to the new unified system"""
    
    def __init__(self, db_path: str = "../data/tweets.db"):
        """Initialize migration with database connection"""
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Track migration statistics
        self.stats = {
            'tweets': {'total': 0, 'migrated': 0, 'failed': 0, 'skipped': 0},
            'articles': {'total': 0, 'migrated': 0, 'failed': 0, 'skipped': 0},
            'papers': {'total': 0, 'migrated': 0, 'failed': 0, 'skipped': 0},
            'concepts_created': 0,
            'concepts_reused': 0
        }
        
        # Cache for concept lookups
        self.concept_cache = {}
        self.synonym_cache = {}
        
    def run_migration(self, dry_run: bool = False):
        """Run the complete migration process"""
        logger.info(f"Starting tag migration (dry_run={dry_run})")
        
        try:
            # Step 1: Load existing concepts and synonyms
            self._load_concept_cache()
            
            # Step 2: Migrate tweet tags
            logger.info("Migrating tweet tags...")
            self._migrate_tweet_tags(dry_run)
            
            # Step 3: Migrate article tags
            logger.info("Migrating article tags...")
            self._migrate_article_tags(dry_run)
            
            # Step 4: Migrate paper tags
            logger.info("Migrating paper tags...")
            self._migrate_paper_tags(dry_run)
            
            # Step 5: Create extended info for all concepts
            logger.info("Creating extended concept info...")
            self._create_extended_concept_info(dry_run)
            
            # Step 6: Update usage counts
            logger.info("Updating usage counts...")
            self._update_usage_counts(dry_run)
            
            if not dry_run:
                self.session.commit()
                logger.info("Migration committed successfully")
            else:
                self.session.rollback()
                logger.info("Dry run completed, changes rolled back")
            
            # Print statistics
            self._print_statistics()
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.session.rollback()
            raise
        finally:
            self.session.close()
    
    def _load_concept_cache(self):
        """Load all existing concepts and synonyms into cache"""
        # Load concepts
        result = self.session.execute(text("""
            SELECT id, tag, display_name FROM tag_concepts
        """))
        
        for row in result:
            concept_id, tag, display_name = row
            # Cache by multiple keys for faster lookup
            self.concept_cache[tag.lower()] = concept_id
            self.concept_cache[display_name.lower()] = concept_id
            
            # Also cache variations
            self.concept_cache[tag.replace('-', ' ').lower()] = concept_id
            self.concept_cache[tag.replace('_', ' ').lower()] = concept_id
        
        # Load synonyms
        result = self.session.execute(text("""
            SELECT synonym_tag, concept_id FROM tag_synonyms
        """))
        
        for row in result:
            synonym, concept_id = row
            self.synonym_cache[synonym.lower()] = concept_id
            self.synonym_cache[synonym.replace('-', ' ').lower()] = concept_id
        
        logger.info(f"Loaded {len(self.concept_cache)} concepts and {len(self.synonym_cache)} synonyms")
    
    def _find_or_create_concept(self, tag_text: str, dry_run: bool = False) -> Optional[int]:
        """Find existing concept or create new one"""
        tag_lower = tag_text.lower()
        tag_slugified = tag_lower.replace(' ', '-').replace('&', 'and')
        
        # Check cache first
        if tag_lower in self.concept_cache:
            self.stats['concepts_reused'] += 1
            return self.concept_cache[tag_lower]
        
        if tag_slugified in self.concept_cache:
            self.stats['concepts_reused'] += 1
            return self.concept_cache[tag_slugified]
        
        if tag_lower in self.synonym_cache:
            self.stats['concepts_reused'] += 1
            return self.synonym_cache[tag_lower]
        
        # Create new concept if not found
        if not dry_run:
            # Determine display name (preserve original capitalization for proper nouns)
            display_name = self._smart_capitalize(tag_text)
            
            # Generate path for root concepts
            path = f"/{tag_slugified}"
            
            result = self.session.execute(text("""
                INSERT INTO tag_concepts (tag, display_name, path, parent_id, level, child_count, descendant_count, descendant_tags)
                VALUES (:tag, :display_name, :path, NULL, 0, 0, 0, '[]')
                RETURNING id
            """), {
                'tag': tag_slugified,
                'display_name': display_name,
                'path': path
            })
            
            concept_id = result.scalar()
            
            # Update cache
            self.concept_cache[tag_lower] = concept_id
            self.concept_cache[tag_slugified] = concept_id
            
            logger.debug(f"Created new concept: {display_name} (id={concept_id})")
            self.stats['concepts_created'] += 1
            
            return concept_id
        else:
            # In dry run, return a placeholder
            self.stats['concepts_created'] += 1
            return -1
    
    def _smart_capitalize(self, tag: str) -> str:
        """Smart capitalization for display names"""
        # List of words that should stay uppercase
        acronyms = {'AI', 'ML', 'NLP', 'GPT', 'GPU', 'API', 'AWS', 'GCP', 'LLM', 'RAG', 'AGI'}
        
        # List of words that should stay lowercase (unless at start)
        lowercase_words = {'and', 'or', 'the', 'a', 'an', 'of', 'in', 'on', 'for', 'with', 'to'}
        
        words = tag.split()
        result = []
        
        for i, word in enumerate(words):
            word_upper = word.upper()
            
            # Check if it's an acronym
            if word_upper in acronyms:
                result.append(word_upper)
            # Check if it should be lowercase (but not first word)
            elif i > 0 and word.lower() in lowercase_words:
                result.append(word.lower())
            # Otherwise, capitalize first letter
            else:
                result.append(word.capitalize())
        
        return ' '.join(result)
    
    def _migrate_tweet_tags(self, dry_run: bool = False):
        """Migrate tags from tweets table"""
        result = self.session.execute(text("""
            SELECT id, tweet_id, tag, tag_type, confidence, created_at
            FROM tags
            ORDER BY created_at
        """))
        
        for row in result:
            tag_id, tweet_id, tag, tag_type, confidence, created_at = row
            self.stats['tweets']['total'] += 1
            
            try:
                # Find or create concept
                concept_id = self._find_or_create_concept(tag, dry_run)
                
                if concept_id and not dry_run:
                    # Check if already migrated
                    exists = self.session.execute(text("""
                        SELECT 1 FROM tag_instances 
                        WHERE content_type = 'tweet' 
                        AND content_id = :tweet_id 
                        AND concept_id = :concept_id
                        LIMIT 1
                    """), {
                        'tweet_id': tweet_id,
                        'concept_id': concept_id
                    }).scalar()
                    
                    if not exists:
                        # Insert into tag_instances
                        self.session.execute(text("""
                            INSERT INTO tag_instances 
                            (content_type, content_id, concept_id, raw_tag, tag_type, confidence, created_at)
                            VALUES ('tweet', :tweet_id, :concept_id, :raw_tag, :tag_type, :confidence, :created_at)
                        """), {
                            'tweet_id': tweet_id,
                            'concept_id': concept_id,
                            'raw_tag': tag,
                            'tag_type': tag_type or 'manual',
                            'confidence': confidence or 1.0,
                            'created_at': created_at
                        })
                        
                        # Log migration
                        self.session.execute(text("""
                            INSERT INTO tag_migration_log
                            (source_table, source_id, original_tag, original_content_id, concept_id, migration_status)
                            VALUES ('tags', :source_id, :tag, :tweet_id, :concept_id, 'success')
                        """), {
                            'source_id': tag_id,
                            'tag': tag,
                            'tweet_id': tweet_id,
                            'concept_id': concept_id
                        })
                        
                        self.stats['tweets']['migrated'] += 1
                    else:
                        self.stats['tweets']['skipped'] += 1
                        logger.debug(f"Skipped duplicate: tweet {tweet_id}, tag {tag}")
                else:
                    self.stats['tweets']['migrated'] += 1  # Count for dry run
                    
            except Exception as e:
                logger.error(f"Failed to migrate tweet tag {tag_id}: {e}")
                self.stats['tweets']['failed'] += 1
                
                # Log failure
                if not dry_run:
                    self.session.execute(text("""
                        INSERT INTO tag_migration_log
                        (source_table, source_id, original_tag, original_content_id, migration_status, migration_notes)
                        VALUES ('tags', :source_id, :tag, :tweet_id, 'failed', :notes)
                    """), {
                        'source_id': tag_id,
                        'tag': tag,
                        'tweet_id': tweet_id,
                        'notes': str(e)
                    })
    
    def _migrate_article_tags(self, dry_run: bool = False):
        """Migrate tags from article_tags table"""
        result = self.session.execute(text("""
            SELECT id, article_id, tag, tag_type, created_at
            FROM article_tags
            ORDER BY created_at
        """))
        
        for row in result:
            tag_id, article_id, tag, tag_type, created_at = row
            self.stats['articles']['total'] += 1
            
            try:
                concept_id = self._find_or_create_concept(tag, dry_run)
                
                if concept_id and not dry_run:
                    # Check if already migrated
                    exists = self.session.execute(text("""
                        SELECT 1 FROM tag_instances 
                        WHERE content_type = 'article' 
                        AND content_id = :article_id 
                        AND concept_id = :concept_id
                        LIMIT 1
                    """), {
                        'article_id': str(article_id),
                        'concept_id': concept_id
                    }).scalar()
                    
                    if not exists:
                        self.session.execute(text("""
                            INSERT INTO tag_instances 
                            (content_type, content_id, concept_id, raw_tag, tag_type, created_at)
                            VALUES ('article', :article_id, :concept_id, :raw_tag, :tag_type, :created_at)
                        """), {
                            'article_id': str(article_id),
                            'concept_id': concept_id,
                            'raw_tag': tag,
                            'tag_type': tag_type or 'manual',
                            'created_at': created_at
                        })
                        
                        self.stats['articles']['migrated'] += 1
                    else:
                        self.stats['articles']['skipped'] += 1
                else:
                    self.stats['articles']['migrated'] += 1  # Count for dry run
                    
            except Exception as e:
                logger.error(f"Failed to migrate article tag {tag_id}: {e}")
                self.stats['articles']['failed'] += 1
    
    def _migrate_paper_tags(self, dry_run: bool = False):
        """Migrate tags from paper_tags table"""
        result = self.session.execute(text("""
            SELECT id, paper_id, tag, tag_type, created_at
            FROM paper_tags
            ORDER BY created_at
        """))
        
        for row in result:
            tag_id, paper_id, tag, tag_type, created_at = row
            self.stats['papers']['total'] += 1
            
            try:
                concept_id = self._find_or_create_concept(tag, dry_run)
                
                if concept_id and not dry_run:
                    # Check if already migrated
                    exists = self.session.execute(text("""
                        SELECT 1 FROM tag_instances 
                        WHERE content_type = 'paper' 
                        AND content_id = :paper_id 
                        AND concept_id = :concept_id
                        LIMIT 1
                    """), {
                        'paper_id': str(paper_id),
                        'concept_id': concept_id
                    }).scalar()
                    
                    if not exists:
                        self.session.execute(text("""
                            INSERT INTO tag_instances 
                            (content_type, content_id, concept_id, raw_tag, tag_type, created_at)
                            VALUES ('paper', :paper_id, :concept_id, :raw_tag, :tag_type, :created_at)
                        """), {
                            'paper_id': str(paper_id),
                            'concept_id': concept_id,
                            'raw_tag': tag,
                            'tag_type': tag_type or 'manual',
                            'created_at': created_at
                        })
                        
                        self.stats['papers']['migrated'] += 1
                    else:
                        self.stats['papers']['skipped'] += 1
                else:
                    self.stats['papers']['migrated'] += 1  # Count for dry run
                    
            except Exception as e:
                logger.error(f"Failed to migrate paper tag {tag_id}: {e}")
                self.stats['papers']['failed'] += 1
    
    def _create_extended_concept_info(self, dry_run: bool = False):
        """Create extended info for all concepts"""
        if dry_run:
            return
        
        # Get all concepts that don't have extended info yet
        result = self.session.execute(text("""
            SELECT c.id 
            FROM tag_concepts c
            LEFT JOIN tag_concept_extended e ON c.id = e.concept_id
            WHERE e.id IS NULL
        """))
        
        for (concept_id,) in result:
            self.session.execute(text("""
                INSERT INTO tag_concept_extended (concept_id, usage_count, quality_score)
                VALUES (:concept_id, 0, 1.0)
            """), {'concept_id': concept_id})
    
    def _update_usage_counts(self, dry_run: bool = False):
        """Update usage counts for all concepts"""
        if dry_run:
            return
        
        # Update counts based on tag_instances
        self.session.execute(text("""
            UPDATE tag_concept_extended
            SET usage_count = (
                SELECT COUNT(*) 
                FROM tag_instances 
                WHERE concept_id = tag_concept_extended.concept_id 
                AND deleted = 0
            ),
            last_used_at = (
                SELECT MAX(created_at)
                FROM tag_instances
                WHERE concept_id = tag_concept_extended.concept_id
                AND deleted = 0
            )
        """))
    
    def _print_statistics(self):
        """Print migration statistics"""
        print("\n" + "="*60)
        print("MIGRATION STATISTICS")
        print("="*60)
        
        print(f"\nConcepts:")
        print(f"  Created: {self.stats['concepts_created']}")
        print(f"  Reused:  {self.stats['concepts_reused']}")
        
        for content_type in ['tweets', 'articles', 'papers']:
            stats = self.stats[content_type]
            print(f"\n{content_type.capitalize()}:")
            print(f"  Total:    {stats['total']}")
            print(f"  Migrated: {stats['migrated']}")
            print(f"  Skipped:  {stats['skipped']}")
            print(f"  Failed:   {stats['failed']}")
        
        total_migrated = sum(s['migrated'] for s in [
            self.stats['tweets'], 
            self.stats['articles'], 
            self.stats['papers']
        ])
        
        total_items = sum(s['total'] for s in [
            self.stats['tweets'], 
            self.stats['articles'], 
            self.stats['papers']
        ])
        
        print(f"\nTotal items migrated: {total_migrated}/{total_items}")
        print("="*60)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate existing tags to unified system")
    parser.add_argument("--dry-run", action="store_true", help="Run without making changes")
    parser.add_argument("--db", default="../data/tweets.db", help="Database path")
    
    args = parser.parse_args()
    
    # Run migration
    migration = TagDataMigration(args.db)
    migration.run_migration(dry_run=args.dry_run)


if __name__ == "__main__":
    main()