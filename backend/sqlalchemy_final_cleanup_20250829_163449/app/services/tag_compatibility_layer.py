"""
Tag Compatibility Layer - Ensures backward compatibility while using new concept structure
This wraps existing tag operations and transparently uses the concept system
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.tag_concept_service import get_tag_concept_service

logger = logging.getLogger(__name__)

class TagCompatibilityLayer:
    """
    Provides backward compatibility for existing tag operations.
    All methods maintain the same interface but use concepts internally.
    """
    
    @staticmethod
    def get_or_create_tag(db: Session, tag_text: str) -> int:
        """
        Get or create a tag and return its ID (for backward compatibility).
        Creates concept if needed.
        """
        service = get_tag_concept_service(db)
        
        # Ensure tag exists in tags table
        tag_id = service._ensure_tag_exists(tag_text)
        
        # Also ensure concept exists
        service.create_or_get_tag(tag_text, auto_create=True)
        
        return tag_id
    
    @staticmethod
    def add_tag_to_tweet(db: Session, tweet_id: str, tag_text: str) -> bool:
        """Add tag to tweet using concept system"""
        service = get_tag_concept_service(db)
        return service.add_tag_to_content('tweet', tweet_id, tag_text, 'manual')
    
    @staticmethod
    def add_tag_to_paper(db: Session, paper_id: str, tag_text: str, 
                         tag_type: str = 'manual') -> bool:
        """Add tag to paper using concept system"""
        service = get_tag_concept_service(db)
        return service.add_tag_to_content('paper', paper_id, tag_text, tag_type)
    
    @staticmethod
    def add_tag_to_article(db: Session, article_id: str, tag_text: str) -> bool:
        """Add tag to article using concept system"""
        service = get_tag_concept_service(db)
        return service.add_tag_to_content('article', article_id, tag_text, 'manual')
    
    @staticmethod
    def get_tweet_tags(db: Session, tweet_id: str) -> List[str]:
        """Get tweet tags as strings (backward compatibility)"""
        service = get_tag_concept_service(db)
        tags = service.get_content_tags('tweet', tweet_id)
        return [tag['display_name'] for tag in tags]
    
    @staticmethod
    def get_paper_tags(db: Session, paper_id: str) -> List[str]:
        """Get paper tags as strings (backward compatibility)"""
        service = get_tag_concept_service(db)
        tags = service.get_content_tags('paper', paper_id)
        return [tag['display_name'] for tag in tags]
    
    @staticmethod
    def get_article_tags(db: Session, article_id: str) -> List[str]:
        """Get article tags as strings (backward compatibility)"""
        service = get_tag_concept_service(db)
        tags = service.get_content_tags('article', article_id)
        return [tag['display_name'] for tag in tags]
    
    @staticmethod
    def get_tweet_tags_with_details(db: Session, tweet_id: str) -> List[Dict[str, Any]]:
        """Get tweet tags with full concept details"""
        service = get_tag_concept_service(db)
        return service.get_content_tags('tweet', tweet_id)
    
    @staticmethod
    def get_paper_tags_with_details(db: Session, paper_id: str) -> List[Dict[str, Any]]:
        """Get paper tags with full concept details"""
        service = get_tag_concept_service(db)
        return service.get_content_tags('paper', paper_id)
    
    @staticmethod
    def get_article_tags_with_details(db: Session, article_id: str) -> List[Dict[str, Any]]:
        """Get article tags with full concept details"""
        service = get_tag_concept_service(db)
        return service.get_content_tags('article', article_id)
    
    @staticmethod
    def filter_tweets_by_tag(db: Session, tag_text: str, 
                             include_hierarchy: bool = True) -> List[str]:
        """Get tweets with a specific tag"""
        service = get_tag_concept_service(db)
        return service.filter_content_by_tag('tweet', tag_text, include_hierarchy)
    
    @staticmethod
    def filter_papers_by_tag(db: Session, tag_text: str,
                             include_hierarchy: bool = True) -> List[str]:
        """Get papers with a specific tag"""
        service = get_tag_concept_service(db)
        return service.filter_content_by_tag('paper', tag_text, include_hierarchy)
    
    @staticmethod
    def filter_articles_by_tag(db: Session, tag_text: str,
                               include_hierarchy: bool = True) -> List[str]:
        """Get articles with a specific tag"""
        service = get_tag_concept_service(db)
        return service.filter_content_by_tag('article', tag_text, include_hierarchy)
    
    @staticmethod
    def normalize_tag(tag_text: str) -> str:
        """
        Normalize tag to display name using concept resolution.
        Returns the canonical display name or original if not found.
        """
        from app.models import get_db
        db = next(get_db())
        service = get_tag_concept_service(db)
        
        concept = service.resolve_tag_to_concept(tag_text)
        if concept:
            return concept['display_name']
        return tag_text
    
    @staticmethod
    def get_tag_hierarchy() -> Dict[str, Any]:
        """Get complete tag hierarchy"""
        from app.models import get_db
        db = next(get_db())
        service = get_tag_concept_service(db)
        return service.get_concept_hierarchy()
    
    @staticmethod
    def get_all_tags_with_counts(db: Session) -> List[Dict[str, Any]]:
        """
        Get all tags with usage counts.
        Returns both legacy tags and concepts.
        """
        from sqlalchemy import text, func
        
        # Get tag usage counts from junction tables
        tweet_counts = db.execute(text("""
            SELECT t.tag, COUNT(DISTINCT tt.tweet_id) as count
            FROM tags t
            LEFT JOIN tweet_tags tt ON t.id = tt.tag_id
            GROUP BY t.tag
        """)).fetchall()
        
        paper_counts = db.execute(text("""
            SELECT t.tag, COUNT(DISTINCT pt.paper_id) as count
            FROM tags t
            LEFT JOIN paper_tags pt ON t.id = pt.tag_id
            GROUP BY t.tag
        """)).fetchall()
        
        article_counts = db.execute(text("""
            SELECT t.tag, COUNT(DISTINCT at.article_id) as count
            FROM tags t
            LEFT JOIN article_tags at ON t.id = at.tag_id
            GROUP BY t.tag
        """)).fetchall()
        
        # Combine counts
        tag_counts = {}
        
        for row in tweet_counts:
            tag_counts[row.tag] = tag_counts.get(row.tag, 0) + row.count
        
        for row in paper_counts:
            tag_counts[row.tag] = tag_counts.get(row.tag, 0) + row.count
        
        for row in article_counts:
            tag_counts[row.tag] = tag_counts.get(row.tag, 0) + row.count
        
        # Resolve to concepts and get display names
        service = get_tag_concept_service(db)
        result = []
        
        for tag, count in tag_counts.items():
            concept = service.resolve_tag_to_concept(tag)
            if concept:
                result.append({
                    'tag': tag,
                    'display_name': concept['display_name'],
                    'concept_id': concept['id'],
                    'slug': concept['slug'],
                    'count': count,
                    'entity_type': concept.get('entity_type'),
                    'icon': concept.get('icon'),
                    'color': concept.get('color')
                })
            else:
                result.append({
                    'tag': tag,
                    'display_name': tag,
                    'concept_id': None,
                    'slug': None,
                    'count': count,
                    'entity_type': None,
                    'icon': None,
                    'color': None
                })
        
        # Sort by count
        result.sort(key=lambda x: x['count'], reverse=True)
        
        return result
    
    @staticmethod
    def suggest_tags_for_text(text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Suggest tags for given text.
        Uses existing tags and concepts.
        """
        from app.models import get_db
        db = next(get_db())
        service = get_tag_concept_service(db)
        
        # This would use an LLM or similarity search
        # For now, return top used concepts
        stats = service.get_tag_statistics()
        suggestions = []
        
        for concept in stats.get('top_concepts', [])[:limit]:
            suggestions.append({
                'tag': concept['display_name'],
                'concept_id': concept['id'],
                'slug': concept['slug'],
                'confidence': 0.8,  # Placeholder
                'reason': 'Popular tag'
            })
        
        return suggestions
    
    @staticmethod
    def migrate_all_tags(db: Session) -> Dict[str, int]:
        """Migrate all existing tags to concepts"""
        service = get_tag_concept_service(db)
        return service.migrate_legacy_tags()


# Convenience functions for direct import

def add_tag(db: Session, content_type: str, content_id: str, 
            tag_text: str, tag_type: str = 'manual') -> bool:
    """Universal function to add tag to any content type"""
    service = get_tag_concept_service(db)
    return service.add_tag_to_content(content_type, content_id, tag_text, tag_type)

def get_tags(db: Session, content_type: str, content_id: str) -> List[Dict[str, Any]]:
    """Universal function to get tags for any content type"""
    service = get_tag_concept_service(db)
    return service.get_content_tags(content_type, content_id)

def resolve_tag(db: Session, tag_text: str) -> Optional[Dict[str, Any]]:
    """Resolve any tag text to its concept"""
    service = get_tag_concept_service(db)
    return service.resolve_tag_to_concept(tag_text)

def filter_by_tag(db: Session, content_type: str, tag_text: str,
                  include_hierarchy: bool = True) -> List[str]:
    """Filter content by tag"""
    service = get_tag_concept_service(db)
    return service.filter_content_by_tag(content_type, tag_text, include_hierarchy)