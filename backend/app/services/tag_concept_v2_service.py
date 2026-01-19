"""
DEPRECATED: Unified Tag Concept v2 Service - SQLite-based

⚠️  DEPRECATED AS OF JANUARY 24, 2025 ⚠️
This service is deprecated after the complete MongoDB migration.

REPLACEMENT: Use ConceptOnlyTagService instead
- Location: app/services/concept_only_tag_service.py
- Reason: Full system migration to MongoDB eliminated SQLite dependencies
- Status: All MongoDB APIs use ConceptOnlyTagService with native MongoDB collections

DO NOT USE in new code. This file is preserved for reference only.
Legacy usage found in:
- app/api/papers.py (SQLite backup)

Migration completed: January 24, 2025
"""
from typing import List, Dict, Any, Optional, Set
import json
import logging

logger = logging.getLogger(__name__)

class TagConceptV2Service:
    """Service for managing tags using v2 concept structure"""
    
    def __init__(self, db: Session):
        self.db = db
        self._concept_cache = {}
        self._alias_cache = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load concepts and aliases into memory for fast lookup"""
        try:
            # Load all active concepts
            result = self.db.execute(text("""
                SELECT id, slug, display_name, entity_type, parents, children
                FROM tag_concepts_v2
                WHERE status = 'active' OR status IS NULL
            """))
            
            for row in result:
                concept = {
                    'id': row[0],
                    'slug': row[1],
                    'display_name': row[2],
                    'entity_type': row[3],
                    'parents': json.loads(row[4]) if row[4] else [],
                    'children': json.loads(row[5]) if row[5] else []
                }
                self._concept_cache[row[0]] = concept
                self._concept_cache[row[1]] = concept  # Also index by slug
            
            # Load all aliases
            result = self.db.execute(text("""
                SELECT alias_text, concept_id
                FROM tag_aliases_v2
            """))
            
            for row in result:
                self._alias_cache[row[0].lower()] = row[1]
                
        except Exception as e:
            logger.error(f"Error loading concept cache: {e}")
    
    def resolve_tag_to_concept(self, tag_text: str) -> Optional[Dict[str, Any]]:
        """
        Resolve any tag text to its concept
        Returns concept with id, slug, display_name, entity_type
        """
        if not tag_text:
            return None
        
        # Normalize for lookup
        normalized = tag_text.lower().strip()
        
        # Check if it's already a concept ID
        if tag_text in self._concept_cache:
            return self._concept_cache[tag_text]
        
        # Check if it's a slug
        slug = normalized.replace(' ', '_').replace('-', '_')
        if slug in self._concept_cache:
            return self._concept_cache[slug]
        
        # Check aliases
        if normalized in self._alias_cache:
            concept_id = self._alias_cache[normalized]
            return self._concept_cache.get(concept_id)
        
        # Not found - could create new concept or return None
        logger.debug(f"Tag '{tag_text}' not found in v2 concepts")
        return None
    
    def get_or_create_concept(self, tag_text: str, entity_type: str = None) -> Dict[str, Any]:
        """Get existing concept or create a new one"""
        # Try to resolve existing
        concept = self.resolve_tag_to_concept(tag_text)
        if concept:
            return concept
        
        # Create new concept
        try:
            # Generate new ID
            result = self.db.execute(text("SELECT COUNT(*) FROM tag_concepts_v2"))
            count = result.scalar()
            new_id = f"c_{count + 1:04d}"
            
            # Normalize to slug
            slug = tag_text.lower().strip().replace(' ', '_').replace('-', '_')
            
            # Generate display name
            display_name = self._generate_display_name(tag_text)
            
            # Insert new concept
            self.db.execute(text("""
                INSERT INTO tag_concepts_v2 (
                    id, slug, display_name, entity_type, status,
                    parents, children, level, usage_count,
                    created_at, updated_at
                ) VALUES (
                    :id, :slug, :display_name, :entity_type, 'active',
                    '[]', '[]', 0, 0,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """), {
                'id': new_id,
                'slug': slug,
                'display_name': display_name,
                'entity_type': entity_type or 'concept'
            })
            
            self.db.commit()
            
            # Add to cache
            concept = {
                'id': new_id,
                'slug': slug,
                'display_name': display_name,
                'entity_type': entity_type or 'concept',
                'parents': [],
                'children': []
            }
            self._concept_cache[new_id] = concept
            self._concept_cache[slug] = concept
            
            logger.info(f"Created new concept: {new_id} - {display_name}")
            return concept
            
        except Exception as e:
            logger.error(f"Error creating concept for '{tag_text}': {e}")
            self.db.rollback()
            # Return a temporary concept
            return {
                'id': f"temp_{abs(hash(tag_text))}",
                'slug': tag_text.lower().replace(' ', '_'),
                'display_name': tag_text,
                'entity_type': entity_type or 'concept'
            }
    
    def _generate_display_name(self, tag: str) -> str:
        """Generate human-readable display name"""
        # Preserve acronyms and special casing
        if tag.isupper() and len(tag) <= 5:
            return tag  # Keep acronyms
        
        # Handle mixed case
        if any(c.isupper() for c in tag[1:]):
            return tag  # Keep intentional casing
        
        # Otherwise, create title case
        words = tag.replace('_', ' ').replace('-', ' ').split()
        return ' '.join(word.capitalize() for word in words)
    
    def add_tag_to_content(self, content_type: str, content_id: int, tag_text: str, 
                           tag_type: str = 'manual') -> bool:
        """
        Add a tag to any content type (tweet, paper, article)
        Automatically resolves to concept
        """
        try:
            # Resolve or create concept
            concept = self.get_or_create_concept(tag_text)
            
            # Determine table based on content type
            if content_type == 'tweet':
                # Add to tags table (tweets use a different structure)
                self.db.execute(text("""
                    INSERT OR IGNORE INTO tags (tweet_id, tag, tag_type)
                    VALUES (:content_id, :tag, :tag_type)
                """), {
                    'content_id': content_id,
                    'tag': concept['display_name'],  # Use display name for compatibility
                    'tag_type': tag_type
                })
            elif content_type == 'paper':
                self.db.execute(text("""
                    INSERT OR IGNORE INTO paper_tags (paper_id, tag, tag_type)
                    VALUES (:content_id, :tag, :tag_type)
                """), {
                    'content_id': content_id,
                    'tag': concept['display_name'],
                    'tag_type': tag_type
                })
            elif content_type == 'article':
                self.db.execute(text("""
                    INSERT OR IGNORE INTO article_tags (article_id, tag, tag_type)
                    VALUES (:content_id, :tag, :tag_type)
                """), {
                    'content_id': content_id,
                    'tag': concept['display_name'],
                    'tag_type': tag_type
                })
            
            # Update usage count
            self.db.execute(text("""
                UPDATE tag_concepts_v2
                SET usage_count = usage_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :concept_id
            """), {'concept_id': concept['id']})
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error adding tag '{tag_text}' to {content_type} {content_id}: {e}")
            self.db.rollback()
            return False
    
    def get_content_tags(self, content_type: str, content_id: int) -> List[Dict[str, Any]]:
        """
        Get all tags for a content item with concept information
        Returns list of tags with concept details
        """
        tags = []
        
        try:
            # Query based on content type
            if content_type == 'tweet':
                result = self.db.execute(text("""
                    SELECT DISTINCT tag, tag_type
                    FROM tags
                    WHERE tweet_id = :content_id
                """), {'content_id': content_id})
            elif content_type == 'paper':
                result = self.db.execute(text("""
                    SELECT DISTINCT tag, tag_type
                    FROM paper_tags
                    WHERE paper_id = :content_id
                """), {'content_id': content_id})
            elif content_type == 'article':
                result = self.db.execute(text("""
                    SELECT DISTINCT tag, tag_type
                    FROM article_tags
                    WHERE article_id = :content_id
                """), {'content_id': content_id})
            else:
                return tags
            
            # Resolve each tag to concept
            for row in result:
                tag_text = row[0]
                tag_type = row[1]
                
                concept = self.resolve_tag_to_concept(tag_text)
                if concept:
                    tags.append({
                        'tag': tag_text,
                        'tag_type': tag_type,
                        'concept_id': concept['id'],
                        'slug': concept['slug'],
                        'display_name': concept['display_name'],
                        'entity_type': concept.get('entity_type')
                    })
                else:
                    # Tag not in v2 system yet
                    tags.append({
                        'tag': tag_text,
                        'tag_type': tag_type,
                        'concept_id': None,
                        'slug': tag_text.lower().replace(' ', '_'),
                        'display_name': tag_text,
                        'entity_type': None
                    })
            
        except Exception as e:
            logger.error(f"Error getting tags for {content_type} {content_id}: {e}")
        
        return tags
    
    def filter_content_by_concept(self, content_type: str, concept_id: str, 
                                 include_children: bool = True) -> List[int]:
        """
        Filter content by concept ID, optionally including child concepts
        Returns list of content IDs
        """
        content_ids = set()
        
        try:
            # Get concept
            concept = self._concept_cache.get(concept_id)
            if not concept:
                return []
            
            # Build list of tags to search for
            tags_to_search = [concept['display_name'], concept['slug']]
            
            # Add aliases
            for alias_text, alias_concept_id in self._alias_cache.items():
                if alias_concept_id == concept_id:
                    tags_to_search.append(alias_text)
            
            # Add children if requested
            if include_children and concept.get('children'):
                for child_id in concept['children']:
                    child = self._concept_cache.get(child_id)
                    if child:
                        tags_to_search.append(child['display_name'])
                        tags_to_search.append(child['slug'])
            
            # Query based on content type
            if content_type == 'tweet':
                for tag in tags_to_search:
                    result = self.db.execute(text("""
                        SELECT DISTINCT tweet_id
                        FROM tags
                        WHERE LOWER(tag) = LOWER(:tag)
                    """), {'tag': tag})
                    content_ids.update(row[0] for row in result)
                    
            elif content_type == 'paper':
                for tag in tags_to_search:
                    result = self.db.execute(text("""
                        SELECT DISTINCT paper_id
                        FROM paper_tags
                        WHERE LOWER(tag) = LOWER(:tag)
                    """), {'tag': tag})
                    content_ids.update(row[0] for row in result)
                    
            elif content_type == 'article':
                for tag in tags_to_search:
                    result = self.db.execute(text("""
                        SELECT DISTINCT article_id
                        FROM article_tags
                        WHERE LOWER(tag) = LOWER(:tag)
                    """), {'tag': tag})
                    content_ids.update(row[0] for row in result)
            
        except Exception as e:
            logger.error(f"Error filtering {content_type} by concept {concept_id}: {e}")
        
        return list(content_ids)
    
    def get_all_concepts(self) -> List[Dict[str, Any]]:
        """Get all concepts with their details"""
        concepts = []
        seen_ids = set()
        
        for key, concept in self._concept_cache.items():
            if concept['id'] not in seen_ids:
                concepts.append(concept)
                seen_ids.add(concept['id'])
        
        return sorted(concepts, key=lambda x: x['display_name'])
    
    def get_concept_hierarchy(self) -> Dict[str, Any]:
        """Get the full concept hierarchy"""
        # Get root concepts (no parents)
        roots = []
        
        for concept in self.get_all_concepts():
            if not concept.get('parents') or len(concept['parents']) == 0:
                roots.append(self._build_hierarchy_node(concept))
        
        return {
            'total_concepts': len(self.get_all_concepts()),
            'root_concepts': roots
        }
    
    def _build_hierarchy_node(self, concept: Dict[str, Any]) -> Dict[str, Any]:
        """Build a hierarchy node with children"""
        node = concept.copy()
        
        # Add children recursively
        if concept.get('children'):
            node['children_concepts'] = []
            for child_id in concept['children']:
                child = self._concept_cache.get(child_id)
                if child:
                    node['children_concepts'].append(self._build_hierarchy_node(child))
        
        return node

# Singleton instance management
_service_instance = None

def get_tag_concept_v2_service(db: Session) -> TagConceptV2Service:
    """Get or create the service instance"""
    global _service_instance
    if _service_instance is None or _service_instance.db != db:
        _service_instance = TagConceptV2Service(db)
    return _service_instance