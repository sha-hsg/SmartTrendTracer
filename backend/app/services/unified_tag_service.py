"""
Unified Tag Service - Provides consistent tag handling across all content types
This fixes the critical filtering and compatibility issues
"""
from typing import List, Optional, Set, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
import logging

from ..models import (
    Tag, Tweet, 
    ArticleTag, SubstackArticle,
    PaperTag, Paper,
    TagConcept, TagSynonym, TagMapping, TagOntologyService
)

logger = logging.getLogger(__name__)


class UnifiedTagService:
    """
    Unified service for handling tags across all content types.
    Provides consistent filtering and normalization.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.ontology_service = TagOntologyService(db)
    
    def find_concept_for_tag(self, tag_text: str) -> Optional[TagConcept]:
        """
        Find the concept for a given tag text.
        Checks exact match, slugified version, and synonyms.
        """
        if not tag_text:
            return None
        
        tag_text = tag_text.strip()
        
        # 1. Check exact match in concepts
        concept = self.db.query(TagConcept).filter(
            func.lower(TagConcept.tag) == func.lower(tag_text)
        ).first()
        
        if concept:
            return concept
        
        # 2. Check slugified version
        slugified = tag_text.lower().replace(' ', '-').replace('&', 'and')
        concept = self.db.query(TagConcept).filter(
            TagConcept.tag == slugified
        ).first()
        
        if concept:
            return concept
        
        # 3. Check if it's a synonym
        synonym = self.db.query(TagSynonym).filter(
            or_(
                func.lower(TagSynonym.synonym_tag) == func.lower(tag_text),
                TagSynonym.synonym_tag == slugified
            )
        ).first()
        
        if synonym:
            return synonym.concept
        
        # 4. Check display names (case-insensitive)
        concept = self.db.query(TagConcept).filter(
            func.lower(TagConcept.display_name) == func.lower(tag_text)
        ).first()
        
        return concept
    
    def get_all_tag_variations(self, tag_text: str) -> Set[str]:
        """
        Get all possible variations of a tag for filtering.
        Includes original, concept tags, synonyms, and descendants.
        """
        variations = {tag_text}
        
        # Add common variations
        variations.add(tag_text.lower())
        variations.add(tag_text.upper())
        variations.add(tag_text.title())
        
        # Add slugified versions
        slugified = tag_text.lower().replace(' ', '-')
        variations.add(slugified)
        variations.add(slugified.replace('-', '_'))
        variations.add(tag_text.replace(' ', '-'))
        variations.add(tag_text.replace(' ', '_'))
        
        # Find concept and add related tags
        concept = self.find_concept_for_tag(tag_text)
        if concept:
            # Add concept tag and display name
            variations.add(concept.tag)
            variations.add(concept.display_name)
            
            # Add all synonyms
            for synonym in concept.synonyms:
                variations.add(synonym.synonym_tag)
                # Also add de-slugified versions of synonyms
                variations.add(synonym.synonym_tag.replace('-', ' ').title())
                variations.add(synonym.synonym_tag.replace('-', ' '))
            
            # Add descendant tags if this is a parent concept
            if concept.descendant_tags:
                for desc_tag in concept.descendant_tags:
                    variations.add(desc_tag)
                    # Add de-slugified versions
                    variations.add(desc_tag.replace('-', ' ').title())
                    variations.add(desc_tag.replace('-', ' '))
            
            # Get descendants' synonyms
            descendants = concept.get_descendants(self.db)
            for desc in descendants:
                for syn in desc.synonyms:
                    variations.add(syn.synonym_tag)
                    variations.add(syn.synonym_tag.replace('-', ' ').title())
        
        # Remove None and empty strings
        variations = {v for v in variations if v}
        
        logger.debug(f"Tag variations for '{tag_text}': {variations}")
        return variations
    
    def filter_tweets_by_tag(self, query, tag_text: str, use_hierarchy: bool = True):
        """
        Filter tweets query by tag, with proper hierarchy support.
        """
        if not tag_text:
            return query
        
        if use_hierarchy:
            # Get all variations of the tag
            tag_variations = self.get_all_tag_variations(tag_text)
            
            if tag_variations:
                # Use case-insensitive matching for all variations
                return query.join(Tag).filter(
                    or_(*[
                        func.lower(Tag.tag) == func.lower(variation)
                        for variation in tag_variations
                    ])
                ).distinct()
        
        # Fallback to exact match (case-insensitive)
        return query.join(Tag).filter(
            func.lower(Tag.tag) == func.lower(tag_text)
        ).distinct()
    
    def filter_articles_by_tag(self, query, tag_text: str, use_hierarchy: bool = True):
        """
        Filter articles query by tag, with proper hierarchy support.
        """
        if not tag_text:
            return query
        
        if use_hierarchy:
            tag_variations = self.get_all_tag_variations(tag_text)
            
            if tag_variations:
                return query.join(ArticleTag).filter(
                    or_(*[
                        func.lower(ArticleTag.tag) == func.lower(variation)
                        for variation in tag_variations
                    ])
                ).distinct()
        
        return query.join(ArticleTag).filter(
            func.lower(ArticleTag.tag) == func.lower(tag_text)
        ).distinct()
    
    def filter_papers_by_tag(self, query, tag_text: str, use_hierarchy: bool = True):
        """
        Filter papers query by tag, with proper hierarchy support.
        """
        if not tag_text:
            return query
        
        if use_hierarchy:
            tag_variations = self.get_all_tag_variations(tag_text)
            
            if tag_variations:
                return query.join(PaperTag).filter(
                    or_(*[
                        func.lower(PaperTag.tag) == func.lower(variation)
                        for variation in tag_variations
                    ])
                ).distinct()
        
        return query.join(PaperTag).filter(
            func.lower(PaperTag.tag) == func.lower(tag_text)
        ).distinct()
    
    def get_tag_statistics(self, tag_text: str) -> Dict[str, int]:
        """
        Get usage statistics for a tag across all content types.
        """
        stats = {
            'tweets': 0,
            'articles': 0,
            'papers': 0,
            'total': 0
        }
        
        # Get all variations for comprehensive counting
        tag_variations = self.get_all_tag_variations(tag_text)
        
        if tag_variations:
            # Count tweets
            stats['tweets'] = self.db.query(Tag).filter(
                or_(*[
                    func.lower(Tag.tag) == func.lower(variation)
                    for variation in tag_variations
                ])
            ).count()
            
            # Count articles
            stats['articles'] = self.db.query(ArticleTag).filter(
                or_(*[
                    func.lower(ArticleTag.tag) == func.lower(variation)
                    for variation in tag_variations
                ])
            ).count()
            
            # Count papers
            stats['papers'] = self.db.query(PaperTag).filter(
                or_(*[
                    func.lower(PaperTag.tag) == func.lower(variation)
                    for variation in tag_variations
                ])
            ).count()
        else:
            # Exact match fallback
            stats['tweets'] = self.db.query(Tag).filter(
                func.lower(Tag.tag) == func.lower(tag_text)
            ).count()
            
            stats['articles'] = self.db.query(ArticleTag).filter(
                func.lower(ArticleTag.tag) == func.lower(tag_text)
            ).count()
            
            stats['papers'] = self.db.query(PaperTag).filter(
                func.lower(PaperTag.tag) == func.lower(tag_text)
            ).count()
        
        stats['total'] = stats['tweets'] + stats['articles'] + stats['papers']
        
        return stats
    
    def normalize_tag_for_storage(self, tag_text: str, preserve_case: bool = False) -> str:
        """
        Normalize a tag for storage while maintaining consistency.
        """
        if not tag_text:
            return tag_text
        
        tag_text = tag_text.strip()
        
        # If preserving case (for manual tags), just clean up spaces
        if preserve_case:
            # Replace multiple spaces with single dash
            tag_text = ' '.join(tag_text.split())
            # Optionally replace spaces with dashes for consistency
            # tag_text = tag_text.replace(' ', '-')
            return tag_text
        
        # Check if this tag exists in a concept
        concept = self.find_concept_for_tag(tag_text)
        if concept:
            # Use the concept's display name for consistency
            return concept.display_name
        
        # For new tags, use smart capitalization
        from ..services.tag_normalizer import TagNormalizer
        normalizer = TagNormalizer(self.db)
        return normalizer.normalize_tag(tag_text)
    
    def ensure_tag_consistency(self):
        """
        Ensure all tags are properly linked to concepts where possible.
        This is a maintenance function to fix existing data.
        """
        updated_count = 0
        
        # Process tweet tags
        all_tweet_tags = self.db.query(Tag.tag).distinct().all()
        for (tag_text,) in all_tweet_tags:
            concept = self.find_concept_for_tag(tag_text)
            if concept and tag_text != concept.display_name:
                # Update all instances to use concept display name
                self.db.query(Tag).filter(Tag.tag == tag_text).update(
                    {Tag.tag: concept.display_name}
                )
                updated_count += 1
        
        # Process article tags
        all_article_tags = self.db.query(ArticleTag.tag).distinct().all()
        for (tag_text,) in all_article_tags:
            concept = self.find_concept_for_tag(tag_text)
            if concept and tag_text != concept.display_name:
                self.db.query(ArticleTag).filter(ArticleTag.tag == tag_text).update(
                    {ArticleTag.tag: concept.display_name}
                )
                updated_count += 1
        
        # Process paper tags
        all_paper_tags = self.db.query(PaperTag.tag).distinct().all()
        for (tag_text,) in all_paper_tags:
            concept = self.find_concept_for_tag(tag_text)
            if concept and tag_text != concept.display_name:
                self.db.query(PaperTag).filter(PaperTag.tag == tag_text).update(
                    {PaperTag.tag: concept.display_name}
                )
                updated_count += 1
        
        self.db.commit()
        logger.info(f"Updated {updated_count} tag groups for consistency")
        
        return updated_count