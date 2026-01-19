#!/usr/bin/env python3
"""
Comprehensive migration script to convert all existing tags to the new concept structure.
This ensures all tags are properly mapped to concepts with aliases and hierarchy.
"""
import json
import logging
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.services.slug_normalizer import to_snake_case
from app.services.gpt5_tag_reorganizer import GPT5TagReorganizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TagConceptMigrator:
    """Migrates existing tags to the new concept structure"""
    
    def __init__(self, db_path: str = "data/tweets.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        # Statistics
        self.stats = {
            'total_tags': 0,
            'concepts_created': 0,
            'aliases_created': 0,
            'relations_created': 0,
            'tags_mapped': 0,
            'errors': 0
        }
    
    def migrate(self, use_ai_reorganization: bool = True):
        """Run the complete migration"""
        logger.info("Starting tag to concept migration...")
        
        # Step 1: Ensure v2 tables exist
        self._ensure_v2_tables()
        
        # Step 2: Collect all existing tags
        all_tags = self._collect_all_tags()
        self.stats['total_tags'] = len(all_tags)
        logger.info(f"Found {len(all_tags)} unique tags to migrate")
        
        # Step 3: Use AI reorganization if requested
        if use_ai_reorganization and len(all_tags) > 0:
            logger.info("Using AI for intelligent tag reorganization...")
            reorganization = self._ai_reorganize_tags(all_tags)
            if reorganization:
                self._apply_reorganization(reorganization)
            else:
                logger.warning("AI reorganization failed, falling back to simple migration")
                self._simple_migration(all_tags)
        else:
            self._simple_migration(all_tags)
        
        # Step 4: Verify migration
        self._verify_migration()
        
        # Step 5: Print summary
        self._print_summary()
        
        logger.info("Migration completed!")
    
    def _ensure_v2_tables(self):
        """Ensure v2 tables exist"""
        logger.info("Ensuring v2 tables exist...")
        
        # Check if tables exist
        self.cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='tag_concepts_v2'
        """)
        
        if not self.cursor.fetchone():
            logger.info("Creating v2 tables...")
            # Run the create schema script
            from create_tag_concepts_v2_schema import create_v2_schema
            create_v2_schema()
    
    def _collect_all_tags(self) -> List[Dict]:
        """Collect all unique tags from the system"""
        all_tags = {}
        
        # Get tags from tweets (tags table has tweet_id directly)
        self.cursor.execute("""
            SELECT tag, COUNT(DISTINCT tweet_id) as count
            FROM tags
            WHERE tweet_id IS NOT NULL
            GROUP BY tag
        """)
        
        for row in self.cursor.fetchall():
            tag = row['tag']
            if tag not in all_tags:
                all_tags[tag] = {'tag': tag, 'tweet_count': 0, 'paper_count': 0, 'article_count': 0}
            all_tags[tag]['tweet_count'] = row['count']
        
        # Get tags from papers
        self.cursor.execute("""
            SELECT pt.tag, COUNT(DISTINCT pt.paper_id) as count
            FROM paper_tags pt
            GROUP BY pt.tag
        """)
        
        for row in self.cursor.fetchall():
            tag = row['tag']
            if tag not in all_tags:
                all_tags[tag] = {'tag': tag, 'tweet_count': 0, 'paper_count': 0, 'article_count': 0}
            all_tags[tag]['paper_count'] = row['count']
        
        # Get tags from articles
        self.cursor.execute("""
            SELECT at.tag, COUNT(DISTINCT at.article_id) as count
            FROM article_tags at
            GROUP BY at.tag
        """)
        
        for row in self.cursor.fetchall():
            tag = row['tag']
            if tag not in all_tags:
                all_tags[tag] = {'tag': tag, 'tweet_count': 0, 'paper_count': 0, 'article_count': 0}
            all_tags[tag]['article_count'] = row['count']
        
        # Calculate total usage
        for tag_data in all_tags.values():
            tag_data['total_count'] = (
                tag_data['tweet_count'] + 
                tag_data['paper_count'] + 
                tag_data['article_count']
            )
        
        return list(all_tags.values())
    
    def _ai_reorganize_tags(self, tags: List[Dict]) -> Dict:
        """Use GPT-5 to reorganize tags intelligently"""
        try:
            # Prepare tag list for GPT-5
            tag_list = []
            for tag_data in tags:
                tag_list.append({
                    'tag': tag_data['tag'],
                    'count': tag_data['total_count'],
                    'source': 'mixed'
                })
            
            # Use GPT-5 reorganizer
            reorganizer = GPT5TagReorganizer()
            result = reorganizer.reorganize_tags(tag_list)
            
            if result and result.get('concepts'):
                logger.info(f"AI reorganization created {len(result['concepts'])} concepts")
                return result
            
        except Exception as e:
            logger.error(f"AI reorganization failed: {e}")
        
        return None
    
    def _apply_reorganization(self, reorganization: Dict):
        """Apply the AI reorganization to the database"""
        logger.info("Applying AI reorganization...")
        
        # Clear existing v2 data
        self.cursor.execute("DELETE FROM tag_concepts_v2")
        self.cursor.execute("DELETE FROM tag_aliases_v2")
        self.cursor.execute("DELETE FROM tag_relations_v2")
        
        # Insert concepts
        for concept in reorganization.get('concepts', []):
            try:
                parents_json = json.dumps(concept.get('parents', []))
                children_json = json.dumps(concept.get('children', []))
                
                self.cursor.execute("""
                    INSERT INTO tag_concepts_v2 
                    (id, slug, display_name, description, status, entity_type,
                     parents, children, level, icon, color, usage_count,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    concept['id'],
                    concept['slug'],
                    concept['display_name'],
                    concept.get('description'),
                    concept.get('status', 'active'),
                    concept.get('entity_type'),
                    parents_json,
                    children_json,
                    concept.get('level', 0),
                    concept.get('icon'),
                    concept.get('color'),
                    concept.get('usage_count', 0)
                ))
                
                self.stats['concepts_created'] += 1
                
            except Exception as e:
                logger.error(f"Error inserting concept {concept['id']}: {e}")
                self.stats['errors'] += 1
        
        # Insert aliases
        for alias in reorganization.get('aliases', []):
            try:
                # Map old alias type names to new ones
                alias_type_map = {
                    'synonym': 'synonym',
                    'variant': 'variant',
                    'misspelling': 'misspelling',
                    'abbreviation': 'abbreviation',
                    'plural': 'variant',
                    'deprecated': 'deprecated_redirect',
                    'legacy': 'deprecated_redirect'
                }
                
                alias_type = alias_type_map.get(alias.get('kind', 'synonym'), 'synonym')
                
                self.cursor.execute("""
                    INSERT OR IGNORE INTO tag_aliases_v2 
                    (alias_text, concept_id, alias_type, confidence, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    alias['alias_text'],
                    alias.get('alias_of', alias.get('concept_id')),
                    alias_type,
                    alias.get('confidence', 1.0)
                ))
                
                self.stats['aliases_created'] += 1
                
            except Exception as e:
                logger.error(f"Error inserting alias {alias['alias_text']}: {e}")
                self.stats['errors'] += 1
        
        # Insert relations
        for relation in reorganization.get('relations', []):
            try:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO tag_relations_v2 
                    (source_id, target_id, relation_type, confidence, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    relation['source'],
                    relation['target'],
                    relation['type'],
                    relation.get('confidence', 1.0)
                ))
                
                self.stats['relations_created'] += 1
                
            except Exception as e:
                logger.error(f"Error inserting relation: {e}")
                self.stats['errors'] += 1
        
        self.conn.commit()
        logger.info(f"Applied {self.stats['concepts_created']} concepts, "
                   f"{self.stats['aliases_created']} aliases, "
                   f"{self.stats['relations_created']} relations")
    
    def _simple_migration(self, tags: List[Dict]):
        """Simple migration: each tag becomes a concept"""
        logger.info("Running simple migration (1 tag = 1 concept)...")
        
        for tag_data in tags:
            try:
                tag = tag_data['tag']
                
                # Generate concept ID
                concept_id = f"c_{self.stats['concepts_created'] + 1:04d}"
                
                # Normalize to slug
                slug = to_snake_case(tag)
                
                # Generate display name
                display_name = self._generate_display_name(tag)
                
                # Guess entity type
                entity_type = self._guess_entity_type(tag)
                
                # Insert concept
                self.cursor.execute("""
                    INSERT INTO tag_concepts_v2 
                    (id, slug, display_name, status, entity_type,
                     parents, children, level, usage_count,
                     created_at, updated_at)
                    VALUES (?, ?, ?, 'active', ?, '[]', '[]', 0, ?,
                            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    concept_id,
                    slug,
                    display_name,
                    entity_type,
                    tag_data['total_count']
                ))
                
                self.stats['concepts_created'] += 1
                
                # Create alias if original differs from slug
                if tag.lower() != slug:
                    self.cursor.execute("""
                        INSERT INTO tag_aliases_v2 
                        (alias_text, concept_id, alias_type, confidence, created_at)
                        VALUES (?, ?, 'variant', 1.0, CURRENT_TIMESTAMP)
                    """, (tag, concept_id))
                    
                    self.stats['aliases_created'] += 1
                
                self.stats['tags_mapped'] += 1
                
            except Exception as e:
                logger.error(f"Error migrating tag '{tag}': {e}")
                self.stats['errors'] += 1
        
        self.conn.commit()
    
    def _generate_display_name(self, tag: str) -> str:
        """Generate human-readable display name"""
        # Preserve acronyms and special casing
        if tag.isupper() and len(tag) <= 5:
            return tag  # Keep acronyms like "AI", "LLM", "GPT"
        
        # Handle mixed case
        if any(c.isupper() for c in tag[1:]):
            return tag  # Keep intentional casing like "OpenAI", "GPT-4"
        
        # Otherwise, create title case
        words = tag.replace('_', ' ').replace('-', ' ').split()
        return ' '.join(word.capitalize() for word in words)
    
    def _guess_entity_type(self, tag: str) -> str:
        """Guess entity type based on tag content"""
        tag_lower = tag.lower()
        
        # Models
        if any(x in tag_lower for x in ['gpt', 'claude', 'llama', 'bert', 'model']):
            return 'model'
        
        # Organizations
        if any(x in tag_lower for x in ['openai', 'anthropic', 'google', 'microsoft', 
                                        'meta', 'deepmind', 'nvidia']):
            return 'organisation'
        
        # People
        if any(x in tag_lower for x in ['sam altman', 'elon', 'yann lecun', 'geoffrey hinton']):
            return 'person'
        
        # Datasets
        if any(x in tag_lower for x in ['dataset', 'corpus', 'benchmark']):
            return 'dataset'
        
        # Methods
        if any(x in tag_lower for x in ['training', 'fine-tuning', 'prompting', 
                                        'learning', 'optimization']):
            return 'method'
        
        # Research topics
        if any(x in tag_lower for x in ['research', 'study', 'analysis', 'theory']):
            return 'research-topic'
        
        # Tools
        if any(x in tag_lower for x in ['tool', 'library', 'framework', 'api']):
            return 'tool'
        
        # Default
        return 'concept'
    
    def _verify_migration(self):
        """Verify that all tags can be resolved to concepts"""
        logger.info("Verifying migration...")
        
        # Check that all tags have corresponding concepts or aliases
        # Get unique tags from all sources
        all_tags = set()
        
        # Tags from tweets
        self.cursor.execute("SELECT DISTINCT tag FROM tags WHERE tag IS NOT NULL")
        for row in self.cursor.fetchall():
            all_tags.add(row[0])
        
        # Tags from papers
        self.cursor.execute("SELECT DISTINCT tag FROM paper_tags WHERE tag IS NOT NULL")
        for row in self.cursor.fetchall():
            all_tags.add(row[0])
        
        # Tags from articles
        self.cursor.execute("SELECT DISTINCT tag FROM article_tags WHERE tag IS NOT NULL")
        for row in self.cursor.fetchall():
            all_tags.add(row[0])
        
        unmapped = []
        for tag in all_tags:
            # Check if tag has concept
            slug = to_snake_case(tag)
            self.cursor.execute("""
                SELECT id FROM tag_concepts_v2 
                WHERE slug = ? OR display_name = ?
                LIMIT 1
            """, (slug, tag))
            
            concept = self.cursor.fetchone()
            
            if not concept:
                # Check aliases
                self.cursor.execute("""
                    SELECT concept_id FROM tag_aliases_v2 
                    WHERE LOWER(alias_text) = LOWER(?)
                    LIMIT 1
                """, (tag,))
                
                alias = self.cursor.fetchone()
                if not alias:
                    unmapped.append(tag)
        
        if unmapped:
            logger.warning(f"Found {len(unmapped)} unmapped tags: {unmapped[:10]}")
        else:
            logger.info("✅ All tags successfully mapped to concepts!")
    
    def _print_summary(self):
        """Print migration summary"""
        print("\n" + "=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        print(f"Total tags processed: {self.stats['total_tags']}")
        print(f"Concepts created: {self.stats['concepts_created']}")
        print(f"Aliases created: {self.stats['aliases_created']}")
        print(f"Relations created: {self.stats['relations_created']}")
        print(f"Tags mapped: {self.stats['tags_mapped']}")
        print(f"Errors: {self.stats['errors']}")
        print("=" * 60)
        
        # Show sample concepts
        self.cursor.execute("""
            SELECT id, slug, display_name, entity_type
            FROM tag_concepts_v2
            LIMIT 10
        """)
        
        print("\nSample concepts created:")
        for row in self.cursor.fetchall():
            print(f"  {row[0]}: {row[2]} ({row[1]}) - {row[3]}")
        
        print("\n✅ Migration complete!")


def main():
    """Run the migration"""
    print("Tag to Concept Structure Migration")
    print("=" * 60)
    print("This will migrate all existing tags to the new concept structure.")
    print("It can use AI (GPT-5) for intelligent reorganization or simple 1:1 mapping.")
    print()
    
    use_ai = input("Use AI reorganization? (recommended) [y/n]: ").lower() == 'y'
    
    migrator = TagConceptMigrator()
    
    try:
        migrator.migrate(use_ai_reorganization=use_ai)
        print("\n✅ Migration completed successfully!")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())