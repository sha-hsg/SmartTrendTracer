"""
Patch functions for papers API to use MongoDB for tag management.
These functions replace specific tag-related operations in papers.py
"""

from typing import List, Dict, Optional
from app.services.mongodb_tag_service import MongoDBTagService
import logging

logger = logging.getLogger(__name__)

# Initialize MongoDB tag service
mongo_tag_service = MongoDBTagService()

def get_paper_tags_mongodb(paper_id: int) -> List[str]:
    """Get all tags for a paper from MongoDB"""
    tags = mongo_tag_service.get_tags_for_content('paper', str(paper_id))
    return [tag.get('original_text', tag['tag_text']) for tag in tags]

def add_paper_tag_mongodb(paper_id: int, tag_text: str, tag_type: str = 'manual', confidence: float = 1.0) -> bool:
    """Add a tag to a paper using MongoDB"""
    return mongo_tag_service.add_tag(
        content_type='paper',
        content_id=str(paper_id),
        tag_text=tag_text,
        tag_type=tag_type,
        confidence=confidence
    )

def remove_paper_tag_mongodb(paper_id: int, tag_text: str) -> bool:
    """Remove a tag from a paper using MongoDB"""
    return mongo_tag_service.remove_tag(
        content_type='paper',
        content_id=str(paper_id),
        tag_text=tag_text
    )

def get_papers_by_tag_mongodb(tag_text: str, use_hierarchy: bool = True) -> List[int]:
    """Get all paper IDs that have a specific tag from MongoDB"""
    content_ids = mongo_tag_service.get_content_ids_by_tag(
        tag_text=tag_text,
        content_type='paper',
        use_hierarchy=use_hierarchy
    )
    # Convert string IDs back to integers
    return [int(id) for id in content_ids if id.isdigit()]

def get_paper_tag_facets_mongodb() -> List[Dict]:
    """Get tag facet counts for papers from MongoDB"""
    all_tags = mongo_tag_service.get_all_tags_with_counts(content_type='paper')
    # Sort by count and limit to top 30
    sorted_tags = sorted(all_tags, key=lambda x: x['count'], reverse=True)[:30]
    return [
        {"value": tag['tag'], "count": tag['count'], "label": tag['tag']}
        for tag in sorted_tags
    ]

def format_paper_response_with_mongodb_tags(paper, include_tags: bool = True) -> Dict:
    """Format a paper response with tags from MongoDB"""
    paper_dict = {
        "id": paper.id,
        "title": paper.title,
        "abstract": paper.abstract,
        "authors": [
            {"name": a.name, "email": a.email, "affiliation": a.affiliation}
            for a in paper.author_details
        ],
        "publication_date": paper.publication_date,
        "conference": paper.conference,
        "journal": paper.journal,
        "arxiv_id": paper.arxiv_id,
        "doi": paper.doi,
        "page_count": paper.page_count,
        "word_count": paper.word_count if hasattr(paper, 'word_count') else 0,
        "created_at": paper.created_at,
        "processed": paper.processed,
        "processor_used": paper.processor_used,
        "is_flagged": paper.is_flagged if hasattr(paper, 'is_flagged') else False,
        "flag_notes": paper.flag_notes if hasattr(paper, 'flag_notes') else None
    }
    
    if include_tags:
        # Get tags from MongoDB instead of SQLite
        paper_dict["tags"] = get_paper_tags_mongodb(paper.id)
    else:
        paper_dict["tags"] = []
    
    return paper_dict