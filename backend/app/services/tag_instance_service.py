"""
Tag Instance Service - Core service for the new unified tag system
Replaces the old tag services with a clean, efficient implementation
"""
from typing import List, Optional, Dict, Any, Set, Tuple
from datetime import datetime
import logging

    TagInstance, ContentType, TagType, 
    TagConceptExtended, TagMigrationLog
)
from app.services.tag_normalizer import TagNormalizer

logger = logging.getLogger(__name__)

class TagInstanceService:
    """
    Unified service for managing tags across all content types.
    This is the primary interface for all tagging operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.normalizer = TagNormalizer(db)
        self.ontology_service = TagOntologyService(db)
    
    # ==================== Core Tag Operations ====================
    
    def add_tag(
        self,
        content_type: ContentType,
        content_id: str,
        tag_text: str,
        tag_type: TagType = TagType.MANUAL,
        confidence: float = 1.0,
        created_by: Optional[str] = None
    ) -> TagInstance:
        """
        Add a tag to content. This is the primary method for tagging.
        
        Args:
            content_type: Type of content (tweet, article, paper)
            content_id: ID of the content
            tag_text: The tag text to add
            tag_type: Type of tag (manual, ai_suggested, auto, system)
            confidence: Confidence score (for AI tags)
            created_by: User or system that created the tag
        
        Returns:
            The created TagInstance
        """
        # Find or create concept
        concept = self._find_or_create_concept(tag_text, tag_type)
        
        # Check if tag already exists for this content
        existing = self.db.query(TagInstance).filter(
            TagInstance.content_type == content_type,
            TagInstance.content_id == content_id,
            TagInstance.concept_id == concept.id,
            TagInstance.deleted == False
        ).first()
        
        if existing:
            logger.debug(f"Tag already exists: {content_type.value}:{content_id} -> {tag_text}")
            return existing
        
        # Create new tag instance
        tag_instance = TagInstance(
            content_type=content_type,
            content_id=content_id,
            concept_id=concept.id,
            raw_tag=tag_text,
            tag_type=tag_type,
            confidence=confidence,
            created_by=created_by
        )
        
        self.db.add(tag_instance)
        
        # Update concept usage
        self._update_concept_usage(concept.id, increment=True)
        
        logger.info(f"Added tag: {content_type.value}:{content_id} -> {tag_text} (concept_id={concept.id})")
        
        return tag_instance
    
    def remove_tag(
        self,
        content_type: ContentType,
        content_id: str,
        tag_text: str
    ) -> bool:
        """
        Remove a tag from content (soft delete).
        
        Returns:
            True if tag was removed, False if not found
        """
        # Find the concept
        concept = self._find_concept(tag_text)
        if not concept:
            return False
        
        # Find the tag instance
        tag_instance = self.db.query(TagInstance).filter(
            TagInstance.content_type == content_type,
            TagInstance.content_id == content_id,
            TagInstance.concept_id == concept.id,
            TagInstance.deleted == False
        ).first()
        
        if not tag_instance:
            return False
        
        # Soft delete
        tag_instance.deleted = True
        tag_instance.deleted_at = datetime.utcnow()
        
        # Update concept usage
        self._update_concept_usage(concept.id, increment=False)
        
        logger.info(f"Removed tag: {content_type.value}:{content_id} -> {tag_text}")
        
        return True
    
    def get_tags(
        self,
        content_type: ContentType,
        content_id: str,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all tags for a piece of content.
        
        Returns:
            List of tag dictionaries with concept info
        """
        query = self.db.query(TagInstance).filter(
            TagInstance.content_type == content_type,
            TagInstance.content_id == content_id
        )
        
        if not include_deleted:
            query = query.filter(TagInstance.deleted == False)
        
        query = query.options(joinedload(TagInstance.concept))
        
        tags = []
        for instance in query.all():
            tags.append({
                'id': instance.id,
                'tag': instance.display_tag,
                'raw_tag': instance.raw_tag,
                'concept_id': instance.concept_id,
                'concept_tag': instance.concept.tag if instance.concept else None,
                'tag_type': instance.tag_type.value,
                'confidence': instance.confidence,
                'created_at': instance.created_at.isoformat() if instance.created_at else None,
                'created_by': instance.created_by
            })
        
        return tags
    
    # ==================== Filtering Operations ====================
    
    def filter_by_tag(
        self,
        query,
        tag_text: str,
        content_type: Optional[ContentType] = None,
        use_hierarchy: bool = True
    ):
        """
        Filter a query by tag, with optional hierarchy support.
        This is the primary filtering method for all content types.
        
        Args:
            query: SQLAlchemy query to filter
            tag_text: Tag to filter by
            content_type: Optional content type filter
            use_hierarchy: Whether to include child tags and synonyms
        
        Returns:
            Filtered query
        """
        # Find the concept
        concept = self._find_concept(tag_text)
        
        if not concept:
            # No concept found, try exact match on raw_tag
            tag_filter = self.db.query(TagInstance).filter(
                func.lower(TagInstance.raw_tag) == func.lower(tag_text),
                TagInstance.deleted == False
            )
            
            if content_type:
                tag_filter = tag_filter.filter(TagInstance.content_type == content_type)
            
            # Get content IDs
            content_ids = [ti.content_id for ti in tag_filter.all()]
            
            if content_type == ContentType.TWEET:
                from ..models import Tweet
                return query.filter(Tweet.tweet_id.in_(content_ids))
            elif content_type == ContentType.ARTICLE:
                from ..models.substack import SubstackArticle
                return query.filter(SubstackArticle.id.in_(content_ids))
            elif content_type == ContentType.PAPER:
                from ..models import Paper
                return query.filter(Paper.id.in_(content_ids))
            
            return query
        
        # Get all related concept IDs if using hierarchy
        if use_hierarchy:
            concept_ids = self._get_related_concept_ids(concept)
        else:
            concept_ids = {concept.id}
        
        # Build filter for tag instances
        tag_filter = self.db.query(TagInstance).filter(
            TagInstance.concept_id.in_(concept_ids),
            TagInstance.deleted == False
        )
        
        if content_type:
            tag_filter = tag_filter.filter(TagInstance.content_type == content_type)
        
        # Get content IDs
        content_ids = [ti.content_id for ti in tag_filter.all()]
        
        # Apply filter based on content type
        if content_type == ContentType.TWEET:
            from ..models import Tweet
            return query.filter(Tweet.tweet_id.in_(content_ids))
        elif content_type == ContentType.ARTICLE:
            from ..models.substack import SubstackArticle
            return query.filter(SubstackArticle.id.in_(content_ids))
        elif content_type == ContentType.PAPER:
            from ..models import Paper
            return query.filter(Paper.id.in_(content_ids))
        
        return query
    
    # ==================== Tag Statistics ====================
    
    def get_tag_statistics(self, tag_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive tag statistics.
        
        Args:
            tag_text: Optional specific tag to get stats for
        
        Returns:
            Dictionary with tag statistics
        """
        if tag_text:
            concept = self._find_concept(tag_text)
            if not concept:
                return {
                    'tag': tag_text,
                    'found': False,
                    'total': 0,
                    'by_type': {}
                }
            
            # Get stats for specific tag
            stats = self.db.query(
                TagInstance.content_type,
                func.count(TagInstance.id)
            ).filter(
                TagInstance.concept_id == concept.id,
                TagInstance.deleted == False
            ).group_by(TagInstance.content_type).all()
            
            by_type = {ct.value: 0 for ct in ContentType}
            for content_type, count in stats:
                by_type[content_type.value] = count
            
            total = sum(by_type.values())
            
            # Get extended info
            extended = self.db.query(TagConceptExtended).filter(
                TagConceptExtended.concept_id == concept.id
            ).first()
            
            return {
                'tag': concept.display_name,
                'concept_id': concept.id,
                'found': True,
                'total': total,
                'by_type': by_type,
                'quality_score': extended.quality_score if extended else 1.0,
                'last_used': extended.last_used_at.isoformat() if extended and extended.last_used_at else None
            }
        else:
            # Get overall statistics
            total_tags = self.db.query(func.count(TagInstance.id)).filter(
                TagInstance.deleted == False
            ).scalar()
            
            total_concepts = self.db.query(func.count(TagConcept.id)).scalar()
            
            by_type = {}
            for content_type in ContentType:
                count = self.db.query(func.count(TagInstance.id)).filter(
                    TagInstance.content_type == content_type,
                    TagInstance.deleted == False
                ).scalar()
                by_type[content_type.value] = count
            
            # Get most popular tags
            popular = self.db.query(
                TagConcept.display_name,
                func.count(TagInstance.id).label('count')
            ).join(
                TagInstance, TagInstance.concept_id == TagConcept.id
            ).filter(
                TagInstance.deleted == False
            ).group_by(TagConcept.id).order_by(
                desc('count')
            ).limit(10).all()
            
            return {
                'total_tags': total_tags,
                'total_concepts': total_concepts,
                'by_type': by_type,
                'popular_tags': [
                    {'tag': tag, 'count': count}
                    for tag, count in popular
                ]
            }
    
    def get_tag_cloud(
        self,
        content_type: Optional[ContentType] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get tag cloud data with counts.
        
        Returns:
            List of tags with usage counts
        """
        query = self.db.query(
            TagConcept.display_name,
            TagConcept.id,
            func.count(TagInstance.id).label('count')
        ).join(
            TagInstance, TagInstance.concept_id == TagConcept.id
        ).filter(
            TagInstance.deleted == False
        )
        
        if content_type:
            query = query.filter(TagInstance.content_type == content_type)
        
        query = query.group_by(TagConcept.id).order_by(
            desc('count')
        ).limit(limit)
        
        results = []
        for display_name, concept_id, count in query.all():
            results.append({
                'tag': display_name,
                'concept_id': concept_id,
                'count': count
            })
        
        return results
    
    # ==================== Tag Suggestions ====================
    
    def suggest_tags(
        self,
        text: str,
        content_type: ContentType,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Suggest tags for content based on text.
        
        Returns:
            List of suggested tags with metadata
        """
        suggestions = []
        
        # Get existing similar tags using vector search or text similarity
        # This would integrate with your existing vector store
        similar_concepts = self._find_similar_concepts(text, limit=limit//2)
        
        for concept, score in similar_concepts:
            suggestions.append({
                'tag': concept.display_name,
                'concept_id': concept.id,
                'type': 'existing',
                'score': score,
                'usage_count': self._get_concept_usage(concept.id)
            })
        
        # Get AI-generated suggestions if needed
        if len(suggestions) < limit:
            # This would call your LLM service
            # ai_tags = self._generate_ai_tags(text, limit - len(suggestions))
            # suggestions.extend(ai_tags)
            pass
        
        return suggestions
    
    # ==================== Private Helper Methods ====================
    
    def _find_concept(self, tag_text: str) -> Optional[TagConcept]:
        """Find a concept for the given tag text"""
        if not tag_text:
            return None
        
        tag_lower = tag_text.lower()
        tag_slugified = tag_lower.replace(' ', '-').replace('&', 'and')
        
        # Try exact match on display name
        concept = self.db.query(TagConcept).filter(
            func.lower(TagConcept.display_name) == tag_lower
        ).first()
        
        if concept:
            return concept
        
        # Try slugified version
        concept = self.db.query(TagConcept).filter(
            TagConcept.tag == tag_slugified
        ).first()
        
        if concept:
            return concept
        
        # Try synonyms
        synonym = self.db.query(TagSynonym).filter(
            func.lower(TagSynonym.synonym_tag) == tag_lower
        ).first()
        
        if synonym:
            return synonym.concept
        
        return None
    
    def _find_or_create_concept(
        self,
        tag_text: str,
        tag_type: TagType
    ) -> TagConcept:
        """Find existing concept or create new one"""
        # Try to find existing
        concept = self._find_concept(tag_text)
        
        if concept:
            return concept
        
        # Create new concept
        tag_slugified = tag_text.lower().replace(' ', '-').replace('&', 'and')
        
        # Determine display name
        if tag_type == TagType.MANUAL:
            # Preserve user's capitalization for manual tags
            display_name = tag_text
        else:
            # Use smart capitalization for auto-generated tags
            display_name = self.normalizer.normalize_tag(tag_text)
        
        concept = TagConcept(
            tag=tag_slugified,
            display_name=display_name,
            parent_id=None,
            descendant_tags=[]
        )
        
        self.db.add(concept)
        self.db.flush()  # Get the ID
        
        # Create extended info
        extended = TagConceptExtended(
            concept_id=concept.id,
            auto_created=(tag_type != TagType.MANUAL),
            verified=(tag_type == TagType.MANUAL)
        )
        
        self.db.add(extended)
        
        logger.info(f"Created new concept: {display_name} (id={concept.id})")
        
        return concept
    
    def _get_related_concept_ids(self, concept: TagConcept) -> Set[int]:
        """Get all related concept IDs (self, children, synonyms)"""
        concept_ids = {concept.id}
        
        # Add descendant concepts
        descendants = concept.get_descendants(self.db)
        concept_ids.update(d.id for d in descendants)
        
        return concept_ids
    
    def _update_concept_usage(self, concept_id: int, increment: bool = True):
        """Update concept usage statistics"""
        extended = self.db.query(TagConceptExtended).filter(
            TagConceptExtended.concept_id == concept_id
        ).first()
        
        if not extended:
            extended = TagConceptExtended(
                concept_id=concept_id,
                usage_count=0
            )
            self.db.add(extended)
        
        if increment:
            extended.usage_count += 1
            extended.last_used_at = datetime.utcnow()
        else:
            extended.usage_count = max(0, extended.usage_count - 1)
    
    def _get_concept_usage(self, concept_id: int) -> int:
        """Get usage count for a concept"""
        extended = self.db.query(TagConceptExtended).filter(
            TagConceptExtended.concept_id == concept_id
        ).first()
        
        if extended:
            return extended.usage_count
        
        # Fallback to counting instances
        return self.db.query(func.count(TagInstance.id)).filter(
            TagInstance.concept_id == concept_id,
            TagInstance.deleted == False
        ).scalar()
    
    def _find_similar_concepts(
        self,
        text: str,
        limit: int = 5
    ) -> List[Tuple[TagConcept, float]]:
        """Find similar concepts using text similarity"""
        # This is a placeholder - integrate with your vector store
        # For now, return empty list
        return []
    
    # ==================== Migration Support ====================
    
    def migrate_legacy_tag(
        self,
        source_table: str,
        source_id: int,
        content_type: ContentType,
        content_id: str,
        tag_text: str,
        tag_type: Optional[str] = None,
        created_at: Optional[datetime] = None
    ) -> bool:
        """
        Migrate a single tag from legacy system.
        Used during migration process.
        """
        try:
            # Add the tag using the new system
            tag_instance = self.add_tag(
                content_type=content_type,
                content_id=content_id,
                tag_text=tag_text,
                tag_type=TagType(tag_type) if tag_type else TagType.MANUAL,
                created_by='migration'
            )
            
            # Override created_at if provided
            if created_at:
                tag_instance.created_at = created_at
            
            # Log migration
            log_entry = TagMigrationLog(
                source_table=source_table,
                source_id=source_id,
                original_tag=tag_text,
                original_content_id=content_id,
                tag_instance_id=tag_instance.id,
                concept_id=tag_instance.concept_id,
                migration_status='success'
            )
            
            self.db.add(log_entry)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate tag: {e}")
            
            # Log failure
            log_entry = TagMigrationLog(
                source_table=source_table,
                source_id=source_id,
                original_tag=tag_text,
                original_content_id=content_id,
                migration_status='failed',
                migration_notes=str(e)
            )
            
            self.db.add(log_entry)
            
            return False