#!/usr/bin/env python3
"""
Migrate to concept-only system:
1. Create concepts for all orphan tags
2. Convert kebab-case to snake_case slugs
3. Generate proper display names
4. Update all tag_instances to use concept_ids only
"""

import re
import logging
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConceptMigration:
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client.smarttrendtracer
        self.tag_instances = self.db.tag_instances
        self.tag_concepts = self.db.tag_concepts_v2
        self.tag_aliases = self.db.tag_aliases_v2
        
        # Track migration stats
        self.stats = {
            'orphans_found': 0,
            'concepts_created': 0,
            'concepts_matched': 0,
            'instances_updated': 0,
            'errors': 0
        }
        
    def kebab_to_snake_case(self, text: str) -> str:
        """Convert kebab-case to snake_case"""
        # Replace hyphens with underscores
        return text.replace('-', '_')
    
    def generate_display_name(self, slug: str) -> str:
        """Generate a proper display name from a slug"""
        # Special cases for acronyms and known terms
        special_cases = {
            'ai': 'AI',
            'ml': 'ML',
            'llm': 'LLM',
            'llms': 'LLMs',
            'nlp': 'NLP',
            'rag': 'RAG',
            'api': 'API',
            'apis': 'APIs',
            'gpt': 'GPT',
            'bert': 'BERT',
            'lstm': 'LSTM',
            'rnn': 'RNN',
            'cnn': 'CNN',
            'gan': 'GAN',
            'gans': 'GANs',
            'vae': 'VAE',
            'rl': 'RL',
            'dl': 'DL',
            'gpu': 'GPU',
            'cpu': 'CPU',
            'tpu': 'TPU',
            'aws': 'AWS',
            'gcp': 'GCP',
            'ui': 'UI',
            'ux': 'UX',
            'id': 'ID',
            'ids': 'IDs',
            'url': 'URL',
            'uri': 'URI',
            'pdf': 'PDF',
            'html': 'HTML',
            'css': 'CSS',
            'js': 'JS',
            'ts': 'TS',
            'usa': 'USA',
            'uk': 'UK',
            'eu': 'EU',
            'sf': 'SF',
            'nyc': 'NYC',
            'mit': 'MIT',
            'ceo': 'CEO',
            'cto': 'CTO',
            'vp': 'VP',
            'hr': 'HR',
            'pr': 'PR',
            'qa': 'QA',
            'ci': 'CI',
            'cd': 'CD',
            'devops': 'DevOps',
            'mlops': 'MLOps',
            'openai': 'OpenAI',
            'deepmind': 'DeepMind',
            'huggingface': 'HuggingFace',
        }
        
        # Split by underscore
        parts = slug.split('_')
        
        # Process each part
        result_parts = []
        for part in parts:
            # Check if it's a special case (case-insensitive)
            lower_part = part.lower()
            if lower_part in special_cases:
                result_parts.append(special_cases[lower_part])
            # Check if it's a number
            elif part.isdigit():
                result_parts.append(part)
            # Check if it contains a number (like "gpt4" or "v2")
            elif any(c.isdigit() for c in part):
                # Handle cases like "gpt4" -> "GPT-4"
                if lower_part.startswith('gpt') and len(part) > 3:
                    result_parts.append(f"GPT-{part[3:]}")
                elif lower_part.startswith('v') and part[1:].isdigit():
                    result_parts.append(part.upper())
                else:
                    result_parts.append(part.capitalize())
            # Regular word
            else:
                result_parts.append(part.capitalize())
        
        return ' '.join(result_parts)
    
    def generate_concept_id(self) -> str:
        """Generate a unique concept ID in format c_XXXX"""
        # Get the highest existing concept ID
        last_concept = self.tag_concepts.find_one(
            {"id": {"$regex": "^c_\\d+$"}},
            sort=[("id", -1)]
        )
        
        if last_concept and 'id' in last_concept:
            # Extract number and increment
            last_num = int(last_concept['id'].split('_')[1])
            new_num = last_num + 1
        else:
            # Start from 1000 to leave room for manual entries
            new_num = 1000
        
        # Ensure uniqueness
        while True:
            new_id = f"c_{new_num:04d}"
            if not self.tag_concepts.find_one({"id": new_id}):
                return new_id
            new_num += 1
    
    def find_or_create_concept(self, tag_text: str) -> Tuple[str, bool]:
        """
        Find existing concept or create new one.
        Returns (concept_id, is_new)
        """
        # Normalize the tag text
        normalized = tag_text.lower().strip()
        
        # Convert kebab-case to snake_case
        slug = self.kebab_to_snake_case(normalized)
        
        # Check if concept already exists with this slug
        existing = self.tag_concepts.find_one({"slug": slug})
        if existing:
            self.stats['concepts_matched'] += 1
            return str(existing['_id']), False
        
        # Check aliases
        alias = self.tag_aliases.find_one({"alias": slug})
        if alias:
            self.stats['concepts_matched'] += 1
            return alias['concept_id'], False
        
        # Create new concept
        display_name = self.generate_display_name(slug)
        
        new_concept = {
            "id": self.generate_concept_id(),
            "slug": slug,
            "name": display_name,
            "display_name": display_name,
            "description": f"Auto-generated concept for '{display_name}'",
            "parents": [],  # Orphan concepts start without parents
            "entity_type": "topic",  # Default entity type
            "created_at": datetime.now().isoformat(),
            "created_by": "migration_script",
            "auto_generated": True,
            "original_tag_text": normalized  # Keep track of original
        }
        
        result = self.tag_concepts.insert_one(new_concept)
        self.stats['concepts_created'] += 1
        
        logger.info(f"Created concept: {display_name} (slug: {slug}, id: {new_concept['id']})")
        
        return str(result.inserted_id), True
    
    def migrate_orphan_tags(self):
        """Find all orphan tags and create concepts for them"""
        logger.info("Finding orphan tags...")
        
        # Get all unique orphan tags
        orphan_pipeline = [
            {"$match": {"concept_id": None}},
            {"$group": {
                "_id": "$tag_text",
                "count": {"$sum": 1},
                "instances": {"$push": "$_id"}
            }},
            {"$sort": {"count": -1}}
        ]
        
        orphans = list(self.tag_instances.aggregate(orphan_pipeline))
        self.stats['orphans_found'] = len(orphans)
        
        logger.info(f"Found {len(orphans)} unique orphan tags")
        
        # Process each orphan tag
        for i, orphan in enumerate(orphans, 1):
            tag_text = orphan['_id']
            instance_ids = orphan['instances']
            count = orphan['count']
            
            if i % 100 == 0:
                logger.info(f"Progress: {i}/{len(orphans)} orphan tags processed")
            
            try:
                # Find or create concept
                concept_id, is_new = self.find_or_create_concept(tag_text)
                
                # Update all instances with this tag
                result = self.tag_instances.update_many(
                    {"_id": {"$in": instance_ids}},
                    {"$set": {"concept_id": concept_id}}
                )
                
                self.stats['instances_updated'] += result.modified_count
                
                if is_new:
                    logger.debug(f"Created concept for '{tag_text}' ({count} instances)")
                else:
                    logger.debug(f"Matched existing concept for '{tag_text}' ({count} instances)")
                    
            except Exception as e:
                logger.error(f"Error processing orphan tag '{tag_text}': {e}")
                self.stats['errors'] += 1
    
    def update_existing_concepts(self):
        """Update existing concepts to ensure they have proper IDs and snake_case slugs"""
        logger.info("Updating existing concepts...")
        
        concepts = self.tag_concepts.find({})
        updated = 0
        
        for concept in concepts:
            updates = {}
            
            # Ensure concept has an ID
            if 'id' not in concept:
                updates['id'] = self.generate_concept_id()
            
            # Ensure slug is snake_case
            if 'slug' in concept and '-' in concept['slug']:
                updates['slug'] = self.kebab_to_snake_case(concept['slug'])
            
            # Ensure display_name exists
            if 'display_name' not in concept:
                if 'name' in concept:
                    updates['display_name'] = concept['name']
                elif 'slug' in concept:
                    updates['display_name'] = self.generate_display_name(concept['slug'])
            
            if updates:
                self.tag_concepts.update_one(
                    {"_id": concept['_id']},
                    {"$set": updates}
                )
                updated += 1
        
        logger.info(f"Updated {updated} existing concepts")
    
    def clean_tag_instances(self):
        """Remove redundant fields from tag_instances"""
        logger.info("Cleaning tag_instances collection...")
        
        # Remove tag_text and original_text fields as they're now redundant
        result = self.tag_instances.update_many(
            {},
            {"$unset": {"tag_text": "", "original_text": ""}}
        )
        
        logger.info(f"Cleaned {result.modified_count} tag instances")
    
    def verify_migration(self):
        """Verify that all tag instances now have concept_ids"""
        orphan_count = self.tag_instances.count_documents({"concept_id": None})
        total_count = self.tag_instances.count_documents({})
        
        logger.info("\n" + "="*60)
        logger.info("MIGRATION VERIFICATION")
        logger.info("="*60)
        logger.info(f"Total tag instances: {total_count}")
        logger.info(f"Instances with concept_id: {total_count - orphan_count}")
        logger.info(f"Remaining orphans: {orphan_count}")
        logger.info(f"Concepts created: {self.stats['concepts_created']}")
        logger.info(f"Concepts matched: {self.stats['concepts_matched']}")
        logger.info(f"Instances updated: {self.stats['instances_updated']}")
        logger.info(f"Errors: {self.stats['errors']}")
        
        if orphan_count == 0:
            logger.info("\n✅ SUCCESS: All tag instances now have concept_ids!")
        else:
            logger.warning(f"\n⚠️  WARNING: {orphan_count} instances still lack concept_ids")
    
    def run(self):
        """Run the complete migration"""
        logger.info("Starting concept-only migration...")
        logger.info("="*60)
        
        try:
            # Step 1: Update existing concepts
            self.update_existing_concepts()
            
            # Step 2: Migrate orphan tags to concepts
            self.migrate_orphan_tags()
            
            # Step 3: Clean redundant fields
            self.clean_tag_instances()
            
            # Step 4: Verify migration
            self.verify_migration()
            
            logger.info("\n🎉 Migration to concept-only system complete!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    migration = ConceptMigration()
    migration.run()