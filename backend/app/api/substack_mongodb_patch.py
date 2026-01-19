"""
Patch functions for Substack API to use MongoDB for tag management.
These functions replace specific tag-related operations in substack.py
"""

from typing import List, Dict, Optional
from app.services.mongodb_tag_service import MongoDBTagService
import logging

logger = logging.getLogger(__name__)

# Initialize MongoDB tag service
mongo_tag_service = MongoDBTagService()

def get_article_tags_mongodb(article_id: int) -> List[str]:
    """Get all tags for an article from MongoDB"""
    tags = mongo_tag_service.get_tags_for_content('article', str(article_id))
    return [tag.get('original_text', tag['tag_text']) for tag in tags]

def add_article_tag_mongodb(article_id: int, tag_text: str, tag_type: str = 'manual', confidence: float = 1.0) -> bool:
    """Add a tag to an article using MongoDB"""
    return mongo_tag_service.add_tag(
        content_type='article',
        content_id=str(article_id),
        tag_text=tag_text,
        tag_type=tag_type,
        confidence=confidence
    )

def remove_article_tag_mongodb(article_id: int, tag_text: str) -> bool:
    """Remove a tag from an article using MongoDB"""
    return mongo_tag_service.remove_tag(
        content_type='article',
        content_id=str(article_id),
        tag_text=tag_text
    )

def get_articles_by_tag_mongodb(tag_text: str, use_hierarchy: bool = True) -> List[int]:
    """Get all article IDs that have a specific tag from MongoDB"""
    content_ids = mongo_tag_service.get_content_ids_by_tag(
        tag_text=tag_text,
        content_type='article',
        use_hierarchy=use_hierarchy
    )
    # Convert string IDs back to integers
    return [int(id) for id in content_ids if id.isdigit()]

def get_article_tag_stats_mongodb() -> Dict:
    """Get article tag statistics from MongoDB"""
    all_tags = mongo_tag_service.get_all_tags_with_counts(content_type='article')
    
    # Get top 10 tags
    sorted_tags = sorted(all_tags, key=lambda x: x['count'], reverse=True)[:10]
    top_tags = [
        {"tag": tag['tag'], "count": tag['count']}
        for tag in sorted_tags
    ]
    
    # Count total unique tags
    total_tags = len(all_tags)
    
    return {
        "total_unique_tags": total_tags,
        "top_tags": top_tags
    }

def format_article_response_with_mongodb_tags(article, include_tags: bool = True) -> Dict:
    """Format an article response with tags from MongoDB"""
    article_dict = {
        "id": article.id,
        "title": article.title,
        "author_id": article.author_id,
        "author": article.author.name if article.author else None,
        "url": article.url,
        "published_date": article.published_date.isoformat() if article.published_date else None,
        "collected_at": article.collected_at.isoformat() if article.collected_at else None,
        "preview": article.preview,
        "content": article.content,
        "summary": article.summary,
        "summary_generated_at": article.summary_generated_at.isoformat() if article.summary_generated_at else None
    }
    
    if include_tags:
        # Get tags from MongoDB instead of SQLite
        article_dict["tags"] = get_article_tags_mongodb(article.id)
    else:
        article_dict["tags"] = []
    
    return article_dict