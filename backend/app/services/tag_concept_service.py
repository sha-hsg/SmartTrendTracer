"""
DEPRECATED: Unified Tag Concept Service - SQLite-based tag concepts

⚠️  DEPRECATED AS OF JANUARY 24, 2025 ⚠️
This service is deprecated after the complete MongoDB migration.

REPLACEMENT: Use ConceptOnlyTagService instead
- Location: app/services/concept_only_tag_service.py
- Reason: Full system migration to MongoDB eliminated SQLite dependencies
- Status: All MongoDB APIs use ConceptOnlyTagService with MongoDB collections

DO NOT USE in new code. This file is preserved for reference only.
Legacy usage found in:
- app/api/tags_unified.py (SQLite backup)
- app/services/tag_compatibility_layer.py (compatibility bridge)

Migration completed: January 24, 2025
"""
import json
import logging
from typing import List, Dict, Optional, Any, Set, Tuple
from datetime import datetime
from app.models.tweet import Tag as TweetTag
from app.models.papers import PaperTag
from app.models.substack import ArticleTag
from app.services.slug_normalizer import to_snake_case

logger = logging.getLogger(__name__)

class TagConceptService:
    """
    Central service for managing tags with the new concept-based structure.
    
    Key principles:
    1. Every tag resolves to a concept via aliases
    2. Concepts have unique IDs (c_xxxx format)
    3. Display names are used in UI, slugs internally
    4. Poly-hierarchy support (multiple parents)
    5. Entity types for semantic classification
    """
    
    def __init__(self, db: Session = None):
        self._concept_cache = {}
        self._alias_cache = {}
        self._initialize_caches()
    
    def _initialize_caches(self):
        """Load concepts and aliases into memory for fast lookup"""
        try:
            # Load all concepts
            concepts = self.db.execute(text("""
                SELECT id, slug, display_name, description, status, entity_type,
                       parents, children, level, icon, color, usage_count
                FROM tag_concepts_v2
                WHERE status = 'active'
            """)).fetchall()
            
            for row in concepts:
                concept = {
                    'id': row.id,
                    'slug': row.slug,
                    'display_name': row.display_name,
                    'description': row.description,
                    'status': row.status,
                    'entity_type': row.entity_type,
                    'parents': json.loads(row.parents) if row.parents else [],
                    'children': json.loads(row.children) if row.children else [],
                    'level': row.level,
                    'icon': row.icon,
                    'color': row.color,
                    'usage_count': row.usage_count
                }
                self._concept_cache[row.id] = concept
                self._concept_cache[row.slug] = concept  # Also index by slug
            
            # Load all aliases
            aliases = self.db.execute(text("""
                SELECT alias_text, concept_id, alias_type, confidence
                FROM tag_aliases_v2
            """)).fetchall()
            
            for row in aliases:
                # Normalize the alias for lookup
                normalized = to_snake_case(row.alias_text)
                self._alias_cache[normalized] = {
                    'concept_id': row.concept_id,
                    'alias_type': row.alias_type,
                    'confidence': row.confidence,
                    'original_text': row.alias_text
                }
                # Also store with original casing
                self._alias_cache[row.alias_text.lower()] = self._alias_cache[normalized]
            
            logger.info(f"Initialized tag concept cache with {len(self._concept_cache)} concepts and {len(self._alias_cache)} aliases")
            
        except Exception as e:
            logger.error(f"Error initializing tag concept cache: {e}")
    
    # ============= Core Resolution Methods =============
    
    def resolve_tag_to_concept(self, tag_text: str) -> Optional[Dict[str, Any]]:
        """
        Resolve any tag text to its canonical concept.
        This is the CORE method that all other services should use.
        
        Args:
            tag_text: Raw tag text from user input or database
            
        Returns:
            Concept dictionary or None if not found
        """
        if not tag_text:
            return None
        
        # Try multiple normalizations
        normalizations = [
            tag_text,  # Original
            tag_text.lower(),  # Lowercase
            to_snake_case(tag_text),  # Snake case
            tag_text.replace('-', '_'),  # Dash to underscore
            tag_text.replace(' ', '_'),  # Space to underscore
        ]
        
        for norm in normalizations:
            # Check if it's a concept ID or slug
            if norm in self._concept_cache:
                return self._concept_cache[norm]
            
            # Check aliases
            if norm in self._alias_cache:
                concept_id = self._alias_cache[norm]['concept_id']
                if concept_id in self._concept_cache:
                    return self._concept_cache[concept_id]
        
        # If not found in cache, check database
        return self._resolve_from_database(tag_text)
    
    def _resolve_from_database(self, tag_text: str) -> Optional[Dict[str, Any]]:
        """Fallback to database if not in cache"""
        try:
            # Check concepts table
            normalized = to_snake_case(tag_text)
            concept = self.db.execute(text("""
                SELECT * FROM tag_concepts_v2
                WHERE slug = :slug OR id = :id
                LIMIT 1
            """), {'slug': normalized, 'id': tag_text}).fetchone()
            
            if concept:
                return self._row_to_concept(concept)
            
            # Check aliases table
            alias = self.db.execute(text("""
                SELECT * FROM tag_aliases_v2
                WHERE LOWER(alias_text) = LOWER(:text)
                LIMIT 1
            """), {'text': tag_text}).fetchone()
            
            if alias:
                concept = self.db.execute(text("""
                    SELECT * FROM tag_concepts_v2
                    WHERE id = :concept_id
                    LIMIT 1
                """), {'concept_id': alias.concept_id}).fetchone()
                
                if concept:
                    return self._row_to_concept(concept)
            
            return None
            
        except Exception as e:
            logger.error(f"Error resolving tag from database: {e}")
            return None
    
    def _row_to_concept(self, row) -> Dict[str, Any]:
        """Convert database row to concept dictionary"""
        return {
            'id': row.id,
            'slug': row.slug,
            'display_name': row.display_name,
            'description': row.description,
            'status': row.status,
            'entity_type': row.entity_type,
            'parents': json.loads(row.parents) if row.parents else [],
            'children': json.loads(row.children) if row.children else [],
            'level': row.level,
            'icon': row.icon,
            'color': row.color,
            'usage_count': row.usage_count
        }
    
    # ============= Tag Creation and Management =============
    
    def create_or_get_tag(self, tag_text: str, auto_create: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get existing concept or create new one if auto_create is True.
        
        Args:
            tag_text: Raw tag text
            auto_create: Whether to create concept if not exists
            
        Returns:
            Concept dictionary
        """
        # Try to resolve existing
        concept = self.resolve_tag_to_concept(tag_text)
        if concept:
            return concept
        
        if not auto_create:
            return None
        
        # Create new concept
        return self.create_concept_from_tag(tag_text)
    
    def create_concept_from_tag(self, tag_text: str, entity_type: str = 'concept') -> Dict[str, Any]:
        """Create a new concept from a tag text"""
        try:
            # Generate concept ID
            concept_id = self._generate_concept_id()
            
            # Normalize to slug
            slug = to_snake_case(tag_text)
            
            # Generate display name (preserve original casing if possible)
            display_name = self._generate_display_name(tag_text)
            
            # Insert concept
            self.db.execute(text("""
                INSERT INTO tag_concepts_v2 
                (id, slug, display_name, status, entity_type, parents, children, 
                 level, usage_count, created_at, updated_at)
                VALUES (:id, :slug, :display_name, 'active', :entity_type, '[]', '[]', 
                        0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """), {
                'id': concept_id,
                'slug': slug,
                'display_name': display_name,
                'entity_type': entity_type
            })
            
            # Create alias for original text if different from slug
            if tag_text.lower() != slug:
                self.db.execute(text("""
                    INSERT INTO tag_aliases_v2 
                    (alias_text, concept_id, alias_type, confidence, created_at)
                    VALUES (:alias_text, :concept_id, 'variant', 1.0, CURRENT_TIMESTAMP)
                """), {
                    'alias_text': tag_text,
                    'concept_id': concept_id
                })
            
            self.db.commit()
            
            # Update cache
            concept = {
                'id': concept_id,
                'slug': slug,
                'display_name': display_name,
                'description': None,
                'status': 'active',
                'entity_type': entity_type,
                'parents': [],
                'children': [],
                'level': 0,
                'icon': None,
                'color': None,
                'usage_count': 0
            }
            
            self._concept_cache[concept_id] = concept
            self._concept_cache[slug] = concept
            
            logger.info(f"Created new concept: {concept_id} ({display_name})")
            return concept
            
        except Exception as e:
            logger.error(f"Error creating concept from tag: {e}")
            self.db.rollback()
            return None
    
    def _generate_concept_id(self) -> str:
        """Generate next available concept ID"""
        result = self.db.execute(text("""
            SELECT id FROM tag_concepts_v2 
            WHERE id LIKE 'c_%'
            ORDER BY id DESC LIMIT 1
        """)).fetchone()
        
        if result:
            try:
                num = int(result.id[2:]) + 1
            except:
                num = len(self._concept_cache) + 1
        else:
            num = 1
        
        return f"c_{num:04d}"
    
    def _generate_display_name(self, tag_text: str) -> str:
        """Generate human-readable display name from tag text"""
        # Preserve original casing for known patterns
        if any(c.isupper() for c in tag_text):
            # Has uppercase, likely intentional (e.g., "GPT-4", "LLMs")
            return tag_text
        
        # Otherwise, title case with smart handling
        words = tag_text.replace('_', ' ').replace('-', ' ').split()
        
        # Don't capitalize certain words
        lowercase_words = {'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}
        
        result = []
        for i, word in enumerate(words):
            if i == 0 or word.lower() not in lowercase_words:
                result.append(word.capitalize())
            else:
                result.append(word.lower())
        
        return ' '.join(result)
    
    # ============= Tag Application to Content =============
    
    def add_tag_to_content(self, content_type: str, content_id: str, 
                           tag_text: str, tag_type: str = 'manual') -> bool:
        """
        Add a tag to content (tweet, paper, article).
        Handles concept resolution and proper storage.
        
        Args:
            content_type: 'tweet', 'paper', or 'article'
            content_id: ID of the content
            tag_text: Raw tag text
            tag_type: 'manual', 'ai', 'llm', etc.
            
        Returns:
            Success boolean
        """
        try:
            # Get or create concept
            concept = self.create_or_get_tag(tag_text)
            if not concept:
                logger.error(f"Failed to create/get concept for tag: {tag_text}")
                return False
            
            # Get or create tag in tags table (for backward compatibility)
            tag_id = self._ensure_tag_exists(tag_text)
            
            # Add to appropriate junction table
            if content_type == 'tweet':
                self.db.execute(text("""
                    INSERT OR IGNORE INTO tweet_tags (tweet_id, tag_id)
                    VALUES (:content_id, :tag_id)
                """), {'content_id': content_id, 'tag_id': tag_id})
                
            elif content_type == 'paper':
                self.db.execute(text("""
                    INSERT OR IGNORE INTO paper_tags (paper_id, tag_id, tag_type)
                    VALUES (:content_id, :tag_id, :tag_type)
                """), {'content_id': content_id, 'tag_id': tag_id, 'tag_type': tag_type})
                
            elif content_type == 'article':
                self.db.execute(text("""
                    INSERT OR IGNORE INTO article_tags (article_id, tag_id)
                    VALUES (:content_id, :tag_id)
                """), {'content_id': content_id, 'tag_id': tag_id})
            
            # Update concept usage count
            self.db.execute(text("""
                UPDATE tag_concepts_v2 
                SET usage_count = usage_count + 1
                WHERE id = :concept_id
            """), {'concept_id': concept['id']})
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error adding tag to content: {e}")
            self.db.rollback()
            return False
    
    def _ensure_tag_exists(self, tag_text: str) -> int:
        """Ensure tag exists in tags table for backward compatibility"""
        # Check if exists
        result = self.db.execute(text("""
            SELECT id FROM tags WHERE tag = :tag
        """), {'tag': tag_text}).fetchone()
        
        if result:
            return result.id
        
        # Create new tag
        result = self.db.execute(text("""
            INSERT INTO tags (tag) VALUES (:tag)
        """), {'tag': tag_text})
        
        # Get the inserted ID
        tag_id = result.lastrowid
        if not tag_id:
            result = self.db.execute(text("""
                SELECT id FROM tags WHERE tag = :tag
            """), {'tag': tag_text}).fetchone()
            tag_id = result.id
        
        return tag_id
    
    # ============= Tag Retrieval and Filtering =============
    
    def get_content_tags(self, content_type: str, content_id: str) -> List[Dict[str, Any]]:
        """
        Get all tags for a piece of content with concept information.
        
        Returns:
            List of tag dictionaries with concept details
        """
        try:
            if content_type == 'tweet':
                tags = self.db.execute(text("""
                    SELECT t.tag, tt.tag_id
                    FROM tweet_tags tt
                    JOIN tags t ON tt.tag_id = t.id
                    WHERE tt.tweet_id = :content_id
                """), {'content_id': content_id}).fetchall()
                
            elif content_type == 'paper':
                tags = self.db.execute(text("""
                    SELECT t.tag, pt.tag_id, pt.tag_type
                    FROM paper_tags pt
                    JOIN tags t ON pt.tag_id = t.id
                    WHERE pt.paper_id = :content_id
                """), {'content_id': content_id}).fetchall()
                
            elif content_type == 'article':
                tags = self.db.execute(text("""
                    SELECT t.tag, at.tag_id
                    FROM article_tags at
                    JOIN tags t ON at.tag_id = t.id
                    WHERE at.article_id = :content_id
                """), {'content_id': content_id}).fetchall()
            else:
                return []
            
            # Resolve each tag to concept
            result = []
            for row in tags:
                concept = self.resolve_tag_to_concept(row.tag)
                if concept:
                    result.append({
                        'original_text': row.tag,
                        'concept_id': concept['id'],
                        'slug': concept['slug'],
                        'display_name': concept['display_name'],
                        'entity_type': concept.get('entity_type'),
                        'icon': concept.get('icon'),
                        'color': concept.get('color'),
                        'tag_type': getattr(row, 'tag_type', 'manual')
                    })
                else:
                    # Tag without concept (legacy)
                    result.append({
                        'original_text': row.tag,
                        'concept_id': None,
                        'slug': to_snake_case(row.tag),
                        'display_name': row.tag,
                        'entity_type': None,
                        'icon': None,
                        'color': None,
                        'tag_type': getattr(row, 'tag_type', 'manual')
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting content tags: {e}")
            return []
    
    def filter_content_by_tag(self, content_type: str, tag_text: str, 
                             include_descendants: bool = True) -> List[str]:
        """
        Get all content IDs that have a specific tag.
        
        Args:
            content_type: 'tweet', 'paper', or 'article'
            tag_text: Tag to filter by
            include_descendants: Include content tagged with child concepts
            
        Returns:
            List of content IDs
        """
        try:
            # Resolve to concept
            concept = self.resolve_tag_to_concept(tag_text)
            if not concept:
                # Fallback to exact match
                return self._filter_by_exact_tag(content_type, tag_text)
            
            # Get all relevant tags (concept + aliases)
            relevant_tags = self._get_concept_tags(concept['id'])
            
            # Include descendants if requested
            if include_descendants:
                for child_id in concept.get('children', []):
                    child_tags = self._get_concept_tags(child_id)
                    relevant_tags.extend(child_tags)
            
            if not relevant_tags:
                return []
            
            # Query appropriate table
            placeholders = ','.join([':tag' + str(i) for i in range(len(relevant_tags))])
            params = {f'tag{i}': tag for i, tag in enumerate(relevant_tags)}
            
            if content_type == 'tweet':
                result = self.db.execute(text(f"""
                    SELECT DISTINCT tt.tweet_id
                    FROM tweet_tags tt
                    JOIN tags t ON tt.tag_id = t.id
                    WHERE t.tag IN ({placeholders})
                """), params).fetchall()
                
            elif content_type == 'paper':
                result = self.db.execute(text(f"""
                    SELECT DISTINCT pt.paper_id
                    FROM paper_tags pt
                    JOIN tags t ON pt.tag_id = t.id
                    WHERE t.tag IN ({placeholders})
                """), params).fetchall()
                
            elif content_type == 'article':
                result = self.db.execute(text(f"""
                    SELECT DISTINCT at.article_id
                    FROM article_tags at
                    JOIN tags t ON at.tag_id = t.id
                    WHERE t.tag IN ({placeholders})
                """), params).fetchall()
            else:
                return []
            
            return [str(row[0]) for row in result]
            
        except Exception as e:
            logger.error(f"Error filtering content by tag: {e}")
            return []
    
    def _get_concept_tags(self, concept_id: str) -> List[str]:
        """Get all tag variations for a concept (including aliases)"""
        tags = []
        
        # Get concept
        concept = self._concept_cache.get(concept_id)
        if concept:
            tags.append(concept['slug'])
            tags.append(concept['display_name'])
        
        # Get aliases
        aliases = self.db.execute(text("""
            SELECT alias_text FROM tag_aliases_v2
            WHERE concept_id = :concept_id
        """), {'concept_id': concept_id}).fetchall()
        
        for row in aliases:
            tags.append(row.alias_text)
        
        return tags
    
    def _filter_by_exact_tag(self, content_type: str, tag_text: str) -> List[str]:
        """Fallback filter by exact tag match"""
        try:
            if content_type == 'tweet':
                result = self.db.execute(text("""
                    SELECT DISTINCT tt.tweet_id
                    FROM tweet_tags tt
                    JOIN tags t ON tt.tag_id = t.id
                    WHERE t.tag = :tag
                """), {'tag': tag_text}).fetchall()
                
            elif content_type == 'paper':
                result = self.db.execute(text("""
                    SELECT DISTINCT pt.paper_id
                    FROM paper_tags pt
                    JOIN tags t ON pt.tag_id = t.id
                    WHERE t.tag = :tag
                """), {'tag': tag_text}).fetchall()
                
            elif content_type == 'article':
                result = self.db.execute(text("""
                    SELECT DISTINCT at.article_id
                    FROM article_tags at
                    JOIN tags t ON at.tag_id = t.id
                    WHERE t.tag = :tag
                """), {'tag': tag_text}).fetchall()
            else:
                return []
            
            return [str(row[0]) for row in result]
            
        except Exception as e:
            logger.error(f"Error in exact tag filter: {e}")
            return []
    
    # ============= Hierarchy and Relationships =============
    
    def get_concept_hierarchy(self) -> Dict[str, Any]:
        """Get the complete concept hierarchy"""
        try:
            # Get root concepts
            roots = self.db.execute(text("""
                SELECT * FROM tag_concepts_v2
                WHERE (parents IS NULL OR parents = '[]')
                AND status = 'active'
                ORDER BY display_name
            """)).fetchall()
            
            hierarchy = []
            for root in roots:
                hierarchy.append(self._build_hierarchy_node(root))
            
            return {
                'root_concepts': hierarchy,
                'total_concepts': len(self._concept_cache),
                'total_aliases': len(self._alias_cache)
            }
            
        except Exception as e:
            logger.error(f"Error getting concept hierarchy: {e}")
            return {'root_concepts': [], 'total_concepts': 0, 'total_aliases': 0}
    
    def _build_hierarchy_node(self, row) -> Dict[str, Any]:
        """Build a hierarchy node with children"""
        node = self._row_to_concept(row)
        
        # Get children
        if node['children']:
            child_nodes = []
            for child_id in node['children']:
                child_row = self.db.execute(text("""
                    SELECT * FROM tag_concepts_v2
                    WHERE id = :id AND status = 'active'
                """), {'id': child_id}).fetchone()
                
                if child_row:
                    child_nodes.append(self._build_hierarchy_node(child_row))
            
            node['children'] = child_nodes
        
        return node
    
    # ============= Statistics and Analytics =============
    
    def get_tag_statistics(self) -> Dict[str, Any]:
        """Get comprehensive tag statistics"""
        try:
            stats = {
                'total_concepts': len(self._concept_cache),
                'total_aliases': len(self._alias_cache),
                'total_tags': 0,
                'entity_type_distribution': {},
                'top_concepts': [],
                'orphan_tags': 0,
                'coverage': {}
            }
            
            # Total tags in use
            total_tags = self.db.execute(text("""
                SELECT COUNT(DISTINCT tag) as count FROM tags
            """)).fetchone()
            stats['total_tags'] = total_tags.count
            
            # Entity type distribution
            entity_dist = self.db.execute(text("""
                SELECT entity_type, COUNT(*) as count
                FROM tag_concepts_v2
                WHERE entity_type IS NOT NULL
                GROUP BY entity_type
            """)).fetchall()
            
            for row in entity_dist:
                stats['entity_type_distribution'][row.entity_type] = row.count
            
            # Top concepts by usage
            top_concepts = self.db.execute(text("""
                SELECT id, slug, display_name, usage_count
                FROM tag_concepts_v2
                WHERE status = 'active'
                ORDER BY usage_count DESC
                LIMIT 10
            """)).fetchall()
            
            for row in top_concepts:
                stats['top_concepts'].append({
                    'id': row.id,
                    'slug': row.slug,
                    'display_name': row.display_name,
                    'usage_count': row.usage_count
                })
            
            # Calculate coverage (tags with concepts vs without)
            tags_with_concepts = 0
            all_tags = self.db.execute(text("SELECT tag FROM tags")).fetchall()
            
            for row in all_tags:
                if self.resolve_tag_to_concept(row.tag):
                    tags_with_concepts += 1
                else:
                    stats['orphan_tags'] += 1
            
            stats['coverage'] = {
                'mapped': tags_with_concepts,
                'unmapped': stats['orphan_tags'],
                'percentage': (tags_with_concepts / len(all_tags) * 100) if all_tags else 0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting tag statistics: {e}")
            return {}
    
    # ============= Migration Support =============
    
    def migrate_legacy_tags(self) -> Dict[str, int]:
        """Migrate all legacy tags to concepts"""
        stats = {
            'migrated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        try:
            # Get all unique tags
            all_tags = self.db.execute(text("""
                SELECT DISTINCT tag FROM tags
            """)).fetchall()
            
            for row in all_tags:
                tag_text = row.tag
                
                # Check if already has concept
                if self.resolve_tag_to_concept(tag_text):
                    stats['skipped'] += 1
                    continue
                
                # Create concept
                concept = self.create_concept_from_tag(tag_text)
                if concept:
                    stats['migrated'] += 1
                else:
                    stats['errors'] += 1
            
            logger.info(f"Migration complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in tag migration: {e}")
            stats['errors'] += 1
            return stats

# Singleton instance
_tag_concept_service = None

def get_tag_concept_service(db: Session = None) -> TagConceptService:
    """Get the singleton tag concept service instance"""
    global _tag_concept_service
    if _tag_concept_service is None:
        _tag_concept_service = TagConceptService(db)
    return _tag_concept_service