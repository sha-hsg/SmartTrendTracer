"""
DEPRECATED: MongoDB-based tag service for managing tag instances.

⚠️  DEPRECATED AS OF JANUARY 24, 2025 ⚠️
This service is deprecated after the complete MongoDB migration.

REPLACEMENT: Use ConceptOnlyTagService instead
- Location: app/services/concept_only_tag_service.py
- Reason: This service was a transitional SQLite->MongoDB bridge
- Status: All APIs now use ConceptOnlyTagService directly

DO NOT USE in new code. This file is preserved for reference only.
Legacy usage found in:
- app/main_mongodb.py (backup file)
- test files

Migration completed: January 24, 2025
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from pymongo import ASCENDING, DESCENDING
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class MongoDBTagService:
    """Service for managing tags in MongoDB tag_instances collection"""
    
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            from app.database.mongodb import get_client, get_database

            cls._client = get_client()
            cls._db = get_database()
        return cls._instance
    
    @property
    def db(self):
        """Get database instance"""
        return self._db
    
    @property
    def tag_instances(self):
        """Get tag_instances collection"""
        return self.db.tag_instances
    
    @property
    def tag_concepts(self):
        """Get tag_concepts_v2 collection"""
        return self.db.tag_concepts_v2
    
    @property
    def tag_aliases(self):
        """Get tag_aliases_v2 collection"""
        return self.db.tag_aliases_v2
    
    def get_tags_for_content(self, content_type: str, content_id: str) -> List[Dict]:
        """
        Get all tags for a specific content item.
        
        Args:
            content_type: Type of content ('tweet', 'paper', 'article')
            content_id: ID of the content item
            
        Returns:
            List of tag dictionaries
        """
        try:
            tags = list(self.tag_instances.find({
                'content_type': content_type,
                'content_id': str(content_id)
            }))
            
            # Enrich with concept information if available
            for tag in tags:
                if tag.get('concept_id'):
                    try:
                        # Only try to convert to ObjectId if it looks like a valid ObjectId
                        concept_id = tag['concept_id']
                        if len(concept_id) == 24 and all(c in '0123456789abcdef' for c in concept_id.lower()):
                            concept = self.tag_concepts.find_one({'_id': ObjectId(concept_id)})
                            if concept:
                                tag['concept_name'] = concept.get('name', tag['tag_text'])
                                tag['concept_slug'] = concept.get('slug', tag['tag_text'])
                                tag['display_name'] = concept.get('name', tag['tag_text'])
                            else:
                                tag['display_name'] = tag['tag_text']
                                tag['concept_name'] = None
                                tag['concept_slug'] = None
                        else:
                            # Invalid concept_id format, treat as orphan
                            tag['display_name'] = tag['tag_text']
                            tag['concept_name'] = None
                            tag['concept_slug'] = None
                    except:
                        # Any error in processing concept, treat as orphan
                        tag['display_name'] = tag['tag_text']
                        tag['concept_name'] = None
                        tag['concept_slug'] = None
                else:
                    # For orphan tags, use tag_text as display name
                    tag['display_name'] = tag['tag_text']
                    tag['concept_name'] = None
                    tag['concept_slug'] = None
            
            return tags
        except Exception as e:
            logger.error(f"Error getting tags for {content_type} {content_id}: {e}")
            return []
    
    def add_tag(self, content_type: str, content_id: str, tag_text: str, 
                tag_type: str = 'manual', confidence: float = 1.0) -> bool:
        """
        Add a tag to a content item.
        
        Args:
            content_type: Type of content ('tweet', 'paper', 'article')
            content_id: ID of the content item
            tag_text: The tag text
            tag_type: Type of tag ('manual', 'auto', 'llm')
            confidence: Confidence score for the tag
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Normalize tag text
            normalized_tag = tag_text.lower().strip()
            
            # Check if tag already exists for this content
            existing = self.tag_instances.find_one({
                'content_type': content_type,
                'content_id': str(content_id),
                'tag_text': normalized_tag
            })
            
            if existing:
                logger.info(f"Tag '{normalized_tag}' already exists for {content_type} {content_id}")
                return True
            
            # Try to find matching concept
            concept_id = None
            
            # Check exact match
            concept = self.tag_concepts.find_one({
                '$or': [
                    {'slug': normalized_tag},
                    {'slug': normalized_tag.replace(' ', '-')},
                    {'name': {'$regex': f'^{normalized_tag}$', '$options': 'i'}}
                ]
            })
            
            if concept:
                concept_id = str(concept['_id'])
            else:
                # Check aliases
                alias = self.tag_aliases.find_one({'alias': normalized_tag})
                if alias:
                    concept_id = alias['concept_id']
            
            # Create tag instance
            tag_instance = {
                'content_type': content_type,
                'content_id': str(content_id),
                'tag_text': normalized_tag,
                'original_text': tag_text,  # Preserve original capitalization
                'concept_id': concept_id,
                'tag_type': tag_type,
                'confidence': confidence,
                'created_at': datetime.now().isoformat(),
                'source': 'api'
            }
            
            result = self.tag_instances.insert_one(tag_instance)
            
            if result.inserted_id:
                logger.info(f"Added tag '{tag_text}' to {content_type} {content_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error adding tag: {e}")
            return False
    
    def remove_tag(self, content_type: str, content_id: str, tag_text: str) -> bool:
        """
        Remove a tag from a content item.
        
        Args:
            content_type: Type of content ('tweet', 'paper', 'article')
            content_id: ID of the content item
            tag_text: The tag text to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            normalized_tag = tag_text.lower().strip()
            
            result = self.tag_instances.delete_one({
                'content_type': content_type,
                'content_id': str(content_id),
                'tag_text': normalized_tag
            })
            
            if result.deleted_count > 0:
                logger.info(f"Removed tag '{tag_text}' from {content_type} {content_id}")
                return True
            
            logger.warning(f"Tag '{tag_text}' not found for {content_type} {content_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error removing tag: {e}")
            return False
    
    def get_all_tags_with_counts(self, content_type: Optional[str] = None) -> List[Dict]:
        """
        Get all unique tags with their usage counts.
        
        Args:
            content_type: Optional filter by content type
            
        Returns:
            List of dictionaries with tag and count
        """
        try:
            match_filter = {}
            if content_type:
                match_filter['content_type'] = content_type
            
            pipeline = [
                {'$match': match_filter},
                {'$group': {
                    '_id': '$tag_text',
                    'count': {'$sum': 1},
                    'content_types': {'$addToSet': '$content_type'}
                }},
                {'$sort': {'count': -1}},
                {'$project': {
                    'tag': '$_id',
                    'count': 1,
                    'content_types': 1,
                    '_id': 0
                }}
            ]
            
            return list(self.tag_instances.aggregate(pipeline))
            
        except Exception as e:
            logger.error(f"Error getting tag counts: {e}")
            return []
    
    def get_content_ids_by_tag(self, tag_text: str, content_type: Optional[str] = None,
                                use_hierarchy: bool = True) -> List[str]:
        """
        Get all content IDs that have a specific tag.
        
        Args:
            tag_text: The tag to search for
            content_type: Optional filter by content type
            use_hierarchy: If True, include child concepts and aliases
            
        Returns:
            List of content IDs
        """
        try:
            normalized_tag = tag_text.lower().strip()
            
            # Build tag list to search for
            tags_to_search = [normalized_tag]
            
            if use_hierarchy:
                # Find concept
                concept = self.tag_concepts.find_one({
                    '$or': [
                        {'slug': normalized_tag},
                        {'slug': normalized_tag.replace(' ', '-')},
                        {'name': {'$regex': f'^{normalized_tag}$', '$options': 'i'}}
                    ]
                })
                
                if concept:
                    concept_id = str(concept['_id'])
                    
                    # Add aliases
                    aliases = self.tag_aliases.find({'concept_id': concept_id})
                    for alias in aliases:
                        tags_to_search.append(alias['alias'])
                    
                    # Add child concepts
                    children = self.tag_concepts.find({'parents': concept_id})
                    for child in children:
                        tags_to_search.append(child['slug'])
                        # Also add child aliases
                        child_aliases = self.tag_aliases.find({'concept_id': str(child['_id'])})
                        for alias in child_aliases:
                            tags_to_search.append(alias['alias'])
            
            # Build query
            query = {'tag_text': {'$in': tags_to_search}}
            if content_type:
                query['content_type'] = content_type
            
            # Get content IDs
            results = self.tag_instances.find(query, {'content_id': 1})
            return list(set(r['content_id'] for r in results))
            
        except Exception as e:
            logger.error(f"Error getting content IDs for tag '{tag_text}': {e}")
            return []
    
    def update_tag_concept_links(self) -> int:
        """
        Update concept_id links for orphan tags that now have matching concepts.
        
        Returns:
            Number of tags updated
        """
        try:
            updated = 0
            
            # Find all orphan tags
            orphans = self.tag_instances.find({'concept_id': None})
            
            for orphan in orphans:
                tag_text = orphan['tag_text']
                
                # Try to find matching concept
                concept = self.tag_concepts.find_one({
                    '$or': [
                        {'slug': tag_text},
                        {'slug': tag_text.replace(' ', '-')},
                        {'name': {'$regex': f'^{tag_text}$', '$options': 'i'}}
                    ]
                })
                
                if not concept:
                    # Check aliases
                    alias = self.tag_aliases.find_one({'alias': tag_text})
                    if alias:
                        concept_id = alias['concept_id']
                    else:
                        continue
                else:
                    concept_id = str(concept['_id'])
                
                # Update the tag instance
                result = self.tag_instances.update_one(
                    {'_id': orphan['_id']},
                    {'$set': {'concept_id': concept_id}}
                )
                
                if result.modified_count > 0:
                    updated += 1
            
            logger.info(f"Updated {updated} orphan tags with concept links")
            return updated
            
        except Exception as e:
            logger.error(f"Error updating concept links: {e}")
            return 0
    
    def get_orphan_tags(self) -> List[Dict]:
        """
        Get all orphan tags (tags without concept_id).
        
        Returns:
            List of orphan tag information
        """
        try:
            pipeline = [
                {'$match': {'concept_id': None}},
                {'$group': {
                    '_id': '$tag_text',
                    'count': {'$sum': 1},
                    'content_types': {'$addToSet': '$content_type'}
                }},
                {'$sort': {'count': -1}},
                {'$project': {
                    'tag': '$_id',
                    'count': 1,
                    'content_types': 1,
                    '_id': 0
                }}
            ]
            
            return list(self.tag_instances.aggregate(pipeline))
            
        except Exception as e:
            logger.error(f"Error getting orphan tags: {e}")
            return []
