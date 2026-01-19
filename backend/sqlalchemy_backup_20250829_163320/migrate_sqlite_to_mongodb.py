#!/usr/bin/env python3
"""
Migrate tag data from SQLite to MongoDB
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import logging
from app.database.mongodb import get_mongodb
from app.models.mongodb_models import (
    TagConcept, TagAlias, TagRelation, 
    TagInstance, ReorganizationProposal,
    ConceptStatus, EntityType, AliasType, RelationType
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SQLiteToMongoDBMigrator:
    """Migrate tag data from SQLite to MongoDB"""
    
    def __init__(self, sqlite_path: str = "data/tweets.db"):
        self.sqlite_path = sqlite_path
        self.mongo = get_mongodb()
        self.stats = {
            "concepts": 0,
            "aliases": 0,
            "relations": 0,
            "instances": 0,
            "proposals": 0
        }
    
    def migrate_all(self):
        """Run complete migration"""
        logger.info("Starting SQLite to MongoDB migration...")
        
        # Connect to SQLite
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Clear existing MongoDB collections (optional)
            if input("Clear existing MongoDB data? (y/n): ").lower() == 'y':
                self._clear_collections()
            
            # Migrate each type of data
            self._migrate_concepts(cursor)
            self._migrate_aliases(cursor)
            self._migrate_relations(cursor)
            self._migrate_proposals(cursor)
            self._migrate_tag_instances(cursor)
            
            logger.info("Migration completed successfully!")
            self._print_stats()
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            conn.close()
    
    def _clear_collections(self):
        """Clear all MongoDB collections"""
        logger.info("Clearing MongoDB collections...")
        self.mongo.concepts.delete_many({})
        self.mongo.aliases.delete_many({})
        self.mongo.relations.delete_many({})
        self.mongo.proposals.delete_many({})
        self.mongo.instances.delete_many({})
    
    def _migrate_concepts(self, cursor):
        """Migrate tag_concepts_v2 to MongoDB"""
        logger.info("Migrating tag concepts...")
        
        cursor.execute("""
            SELECT * FROM tag_concepts_v2 
            ORDER BY created_at
        """)
        
        for row in cursor.fetchall():
            try:
                # Parse JSON fields
                parents = json.loads(row['parents']) if row['parents'] else []
                children = json.loads(row['children']) if row['children'] else []
                
                # Map status
                status = ConceptStatus.ACTIVE
                if row['status'] == 'deprecated':
                    status = ConceptStatus.DEPRECATED
                elif row['status'] == 'suggested':
                    status = ConceptStatus.SUGGESTED
                elif row['status'] == 'draft':
                    status = ConceptStatus.DRAFT
                
                # Map entity type
                entity_type = None
                if row['entity_type']:
                    entity_type_map = {
                        'person': EntityType.PERSON,
                        'organisation': EntityType.ORGANISATION,
                        'location': EntityType.LOCATION,
                        'event': EntityType.EVENT,
                        'model': EntityType.MODEL,
                        'method': EntityType.METHOD,
                        'dataset': EntityType.DATASET,
                        'benchmark': EntityType.BENCHMARK,
                        'metric': EntityType.METRIC,
                        'research-topic': EntityType.RESEARCH_TOPIC,
                        'paper': EntityType.PAPER,
                        'tool': EntityType.TOOL,
                        'concept': EntityType.CONCEPT
                    }
                    entity_type = entity_type_map.get(row['entity_type'])
                
                # Create concept document
                concept = {
                    "id": row['id'],
                    "slug": row['slug'],
                    "display_name": row['display_name'],
                    "description": row['description'],
                    "status": status.value,
                    "entity_type": entity_type.value if entity_type else None,
                    "usage_count": row['usage_count'] or 0,
                    "parents": parents,
                    "children": children,
                    "level": row['level'] or 0,
                    "icon": row['icon'],
                    "color": row['color'],
                    "metadata": {},
                    "created_at": datetime.fromisoformat(row['created_at'].replace(' ', 'T')),
                    "updated_at": datetime.fromisoformat(row['updated_at'].replace(' ', 'T'))
                }
                
                # Insert into MongoDB
                self.mongo.concepts.replace_one(
                    {"id": concept["id"]},
                    concept,
                    upsert=True
                )
                self.stats["concepts"] += 1
                
            except Exception as e:
                logger.error(f"Failed to migrate concept {row['id']}: {e}")
    
    def _migrate_aliases(self, cursor):
        """Migrate tag_aliases_v2 to MongoDB"""
        logger.info("Migrating tag aliases...")
        
        cursor.execute("""
            SELECT * FROM tag_aliases_v2
            ORDER BY created_at
        """)
        
        for row in cursor.fetchall():
            try:
                # Map alias type
                alias_type_map = {
                    'synonym': AliasType.SYNONYM,
                    'variant': AliasType.VARIANT,
                    'misspelling': AliasType.MISSPELLING,
                    'abbreviation': AliasType.ABBREVIATION,
                    'plural': AliasType.PLURAL,
                    'deprecated': AliasType.DEPRECATED,
                    'legacy': AliasType.LEGACY
                }
                alias_type = alias_type_map.get(row['alias_type'], AliasType.SYNONYM)
                
                # Create alias document
                alias = {
                    "alias_text": row['alias_text'],
                    "concept_id": row['concept_id'],
                    "alias_type": alias_type.value,
                    "confidence": row['confidence'] or 1.0,
                    "created_at": datetime.fromisoformat(row['created_at'].replace(' ', 'T'))
                }
                
                # Insert into MongoDB
                self.mongo.aliases.replace_one(
                    {"alias_text": alias["alias_text"]},
                    alias,
                    upsert=True
                )
                self.stats["aliases"] += 1
                
            except Exception as e:
                logger.error(f"Failed to migrate alias {row['alias_text']}: {e}")
    
    def _migrate_relations(self, cursor):
        """Migrate tag_relations_v2 to MongoDB"""
        logger.info("Migrating tag relations...")
        
        cursor.execute("""
            SELECT * FROM tag_relations_v2
            ORDER BY created_at
        """)
        
        for row in cursor.fetchall():
            try:
                # Map relation type
                relation_type_map = {
                    'child_of': RelationType.CHILD_OF,
                    'related': RelationType.RELATED,
                    'produces': RelationType.PRODUCES,
                    'evaluated_on': RelationType.EVALUATED_ON,
                    'part_of': RelationType.PART_OF,
                    'instance_of': RelationType.INSTANCE_OF,
                    'same_as': RelationType.SAME_AS,
                    'replaces': RelationType.REPLACES
                }
                relation_type = relation_type_map.get(row['relation_type'], RelationType.RELATED)
                
                # Create relation document
                relation = {
                    "source_id": row['source_id'],
                    "target_id": row['target_id'],
                    "relation_type": relation_type.value,
                    "confidence": row['confidence'] or 1.0,
                    "metadata": {},
                    "created_at": datetime.fromisoformat(row['created_at'].replace(' ', 'T'))
                }
                
                # Insert into MongoDB
                self.mongo.relations.replace_one(
                    {
                        "source_id": relation["source_id"],
                        "target_id": relation["target_id"],
                        "relation_type": relation["relation_type"]
                    },
                    relation,
                    upsert=True
                )
                self.stats["relations"] += 1
                
            except Exception as e:
                logger.error(f"Failed to migrate relation: {e}")
    
    def _migrate_proposals(self, cursor):
        """Migrate tag_reorganization_proposals to MongoDB"""
        logger.info("Migrating reorganization proposals...")
        
        cursor.execute("""
            SELECT * FROM tag_reorganization_proposals
            ORDER BY created_at
        """)
        
        for row in cursor.fetchall():
            try:
                # Parse JSON fields
                concepts = json.loads(row['concepts']) if row['concepts'] else []
                aliases = json.loads(row['aliases']) if row['aliases'] else []
                relations = json.loads(row['relations']) if row['relations'] else []
                root_categories = json.loads(row['root_categories']) if row['root_categories'] else []
                merge_proposals = json.loads(row['merge_proposals']) if row['merge_proposals'] else []
                governance = json.loads(row['governance']) if row['governance'] else {}
                validation = json.loads(row['validation']) if row['validation'] else {}
                
                # Create proposal document
                proposal = {
                    "proposal_id": row['proposal_id'],
                    "version": row['version'],
                    "model_used": row['model_used'],
                    "total_tags": row['total_tags'],
                    "confidence_score": row['confidence_score'],
                    "reasoning": row['reasoning'],
                    "concepts": concepts,
                    "aliases": aliases,
                    "relations": relations,
                    "root_categories": root_categories,
                    "merge_proposals": merge_proposals,
                    "governance": governance,
                    "validation": validation,
                    "status": row['status'],
                    "applied_at": datetime.fromisoformat(row['applied_at'].replace(' ', 'T')) if row['applied_at'] else None,
                    "applied_by": row['applied_by'],
                    "created_at": datetime.fromisoformat(row['created_at'].replace(' ', 'T'))
                }
                
                # Insert into MongoDB
                self.mongo.proposals.replace_one(
                    {"proposal_id": proposal["proposal_id"]},
                    proposal,
                    upsert=True
                )
                self.stats["proposals"] += 1
                
            except Exception as e:
                logger.error(f"Failed to migrate proposal {row['proposal_id']}: {e}")
    
    def _migrate_tag_instances(self, cursor):
        """Migrate actual tag usage from tweets, papers, and articles"""
        logger.info("Migrating tag instances...")
        
        # Migrate tweet tags
        cursor.execute("""
            SELECT 
                'tweet' as content_type,
                tt.tweet_id as content_id,
                t.tag as original_text,
                t.tag as display_name,
                'manual' as tag_type
            FROM tweet_tags tt
            JOIN tags t ON tt.tag_id = t.id
        """)
        
        for row in cursor.fetchall():
            try:
                # Try to find concept_id from aliases
                alias = self.mongo.aliases.find_one({"alias_text": row['original_text']})
                concept_id = alias['concept_id'] if alias else None
                
                # Create instance document
                instance = {
                    "content_type": row['content_type'],
                    "content_id": str(row['content_id']),
                    "concept_id": concept_id,
                    "original_text": row['original_text'],
                    "display_name": row['display_name'],
                    "tag_type": row['tag_type'],
                    "metadata": {},
                    "created_at": datetime.utcnow()
                }
                
                # Insert into MongoDB
                self.mongo.instances.insert_one(instance)
                self.stats["instances"] += 1
                
            except Exception as e:
                logger.error(f"Failed to migrate tag instance: {e}")
        
        # Migrate paper tags
        cursor.execute("""
            SELECT 
                'paper' as content_type,
                pt.paper_id as content_id,
                t.tag as original_text,
                t.tag as display_name,
                pt.tag_type
            FROM paper_tags pt
            JOIN tags t ON pt.tag_id = t.id
        """)
        
        for row in cursor.fetchall():
            try:
                # Try to find concept_id from aliases
                alias = self.mongo.aliases.find_one({"alias_text": row['original_text']})
                concept_id = alias['concept_id'] if alias else None
                
                # Create instance document
                instance = {
                    "content_type": row['content_type'],
                    "content_id": str(row['content_id']),
                    "concept_id": concept_id,
                    "original_text": row['original_text'],
                    "display_name": row['display_name'],
                    "tag_type": row['tag_type'] or 'manual',
                    "metadata": {},
                    "created_at": datetime.utcnow()
                }
                
                # Insert into MongoDB
                self.mongo.instances.insert_one(instance)
                self.stats["instances"] += 1
                
            except Exception as e:
                logger.error(f"Failed to migrate paper tag instance: {e}")
        
        # Migrate article tags
        cursor.execute("""
            SELECT 
                'article' as content_type,
                at.article_id as content_id,
                t.tag as original_text,
                t.tag as display_name,
                'manual' as tag_type
            FROM article_tags at
            JOIN tags t ON at.tag_id = t.id
        """)
        
        for row in cursor.fetchall():
            try:
                # Try to find concept_id from aliases
                alias = self.mongo.aliases.find_one({"alias_text": row['original_text']})
                concept_id = alias['concept_id'] if alias else None
                
                # Create instance document
                instance = {
                    "content_type": row['content_type'],
                    "content_id": str(row['content_id']),
                    "concept_id": concept_id,
                    "original_text": row['original_text'],
                    "display_name": row['display_name'],
                    "tag_type": row['tag_type'],
                    "metadata": {},
                    "created_at": datetime.utcnow()
                }
                
                # Insert into MongoDB
                self.mongo.instances.insert_one(instance)
                self.stats["instances"] += 1
                
            except Exception as e:
                logger.error(f"Failed to migrate article tag instance: {e}")
    
    def _print_stats(self):
        """Print migration statistics"""
        print("\n📊 Migration Statistics:")
        print("=" * 40)
        for key, value in self.stats.items():
            print(f"  {key.capitalize()}: {value}")
        print("=" * 40)
        
        # Show MongoDB counts
        print("\n🗄️ MongoDB Collection Counts:")
        print(f"  Concepts: {self.mongo.concepts.count_documents({})}")
        print(f"  Aliases: {self.mongo.aliases.count_documents({})}")
        print(f"  Relations: {self.mongo.relations.count_documents({})}")
        print(f"  Proposals: {self.mongo.proposals.count_documents({})}")
        print(f"  Instances: {self.mongo.instances.count_documents({})}")


def main():
    """Run the migration"""
    print("🔄 SQLite to MongoDB Migration Tool")
    print("=" * 40)
    print("This will migrate tag data from SQLite to MongoDB")
    print("Make sure MongoDB is running locally or update connection in .env")
    print()
    
    migrator = SQLiteToMongoDBMigrator()
    
    try:
        migrator.migrate_all()
        print("\n✅ Migration completed successfully!")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())