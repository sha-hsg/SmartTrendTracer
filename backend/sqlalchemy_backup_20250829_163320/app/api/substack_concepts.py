"""
Updated Substack API using concept-only tag system.
Returns concept IDs and metadata instead of raw tag text.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import List, Optional, Dict
from datetime import datetime
import json
import logging

from app.models import get_db
from app.models.substack import SubstackAuthor, SubstackArticle, ArticleSnippet
from app.services.concept_only_tag_service import ConceptOnlyTagService
from app.services.article_summarizer import ArticleSummarizer

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize concept service
concept_service = ConceptOnlyTagService()

@router.get("/", response_model=List[Dict])
def get_articles(
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    concept_id: Optional[str] = Query(None, description="Filter by concept ID"),
    include_concepts: bool = Query(True, description="Include full concept details"),
    db: Session = Depends(get_db)
):
    """Get recent articles with concept-based tags"""
    # Filter out soft-deleted articles
    query = db.query(SubstackArticle).filter(
        SubstackArticle.deleted == False
    ).options(
        joinedload(SubstackArticle.author),
        joinedload(SubstackArticle.snippets)
    )
    
    # Filter by concept if provided
    if concept_id:
        logger.info(f"Filtering articles by concept: '{concept_id}'")
        
        # Get article IDs that have this concept
        instances = concept_service.tag_instances.find({
            'content_type': 'article',
            'concept_id': concept_id
        })
        article_ids = [inst['content_id'] for inst in instances]
        
        if article_ids:
            query = query.filter(SubstackArticle.id.in_(article_ids))
        else:
            return []
    
    # Execute query
    try:
        articles = query.order_by(desc(SubstackArticle.published_at)).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error executing article query: {e}")
        articles = []
    
    # Convert to response model with concepts
    result = []
    for article in articles:
        # Get concepts for this article
        concepts = concept_service.get_tags_for_content('article', str(article.id))
        
        article_dict = {
            "id": article.id,
            "title": article.title,
            "author": {
                "id": article.author.id,
                "name": article.author.name,
                "email": article.author.email
            } if article.author else None,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "url": article.url,
            "preview": article.preview,
            "content_length": len(article.content_markdown) if article.content_markdown else 0,
            "snippet_count": len(article.snippets),
            "summary": article.summary,
            "created_at": article.collected_at.isoformat() if article.collected_at else None
        }
        
        if include_concepts:
            # Include full concept details
            article_dict["concepts"] = concepts
        else:
            # Just include concept IDs
            article_dict["concept_ids"] = [c['concept_id'] for c in concepts]
        
        result.append(article_dict)
    
    return result

@router.get("/faceted-search")
def faceted_search(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    authors: Optional[List[str]] = Query(None),
    concept_ids: Optional[List[str]] = Query(None),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Faceted search for articles with concept-based filtering
    """
    
    # Base query - filter out soft-deleted articles
    query = db.query(SubstackArticle).filter(
        SubstackArticle.deleted == False
    ).options(
        joinedload(SubstackArticle.author),
        joinedload(SubstackArticle.snippets)
    )
    
    # Apply author filter
    if authors:
        query = query.filter(SubstackArticle.author.has(SubstackAuthor.name.in_(authors)))
    
    # Apply concept filter
    if concept_ids:
        # Get article IDs that have ANY of the selected concepts
        instances = concept_service.tag_instances.find({
            'content_type': 'article',
            'concept_id': {'$in': concept_ids}
        })
        article_ids = list(set([inst['content_id'] for inst in instances]))
        
        if article_ids:
            # Convert to integers since article IDs are integers
            article_ids = [int(aid) for aid in article_ids if aid.isdigit()]
            if article_ids:
                query = query.filter(SubstackArticle.id.in_(article_ids))
            else:
                # No valid article IDs
                return {
                    "articles": [],
                    "facets": {"authors": [], "concepts": []},
                    "total": 0,
                    "page": page,
                    "page_size": page_size
                }
        else:
            # No articles with these concepts
            return {
                "articles": [],
                "facets": {"authors": [], "concepts": []},
                "total": 0,
                "page": page,
                "page_size": page_size
            }
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (SubstackArticle.title.ilike(search_term)) |
            (SubstackArticle.content_markdown.ilike(search_term))
        )
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    skip = (page - 1) * page_size
    articles = query.order_by(desc(SubstackArticle.published_at)).offset(skip).limit(page_size).all()
    
    # Build facets - get all articles for facet counts (not just current page)
    all_articles_query = db.query(SubstackArticle).filter(SubstackArticle.deleted == False)
    if search:
        all_articles_query = all_articles_query.filter(
            (SubstackArticle.title.ilike(f"%{search}%")) |
            (SubstackArticle.content_markdown.ilike(f"%{search}%"))
        )
    
    # Author facets
    author_counts = db.query(
        SubstackAuthor.name,
        func.count(SubstackArticle.id).label('count')
    ).join(
        SubstackArticle, SubstackAuthor.id == SubstackArticle.author_id
    ).filter(
        SubstackArticle.deleted == False
    )
    
    if search:
        author_counts = author_counts.filter(
            (SubstackArticle.title.ilike(f"%{search}%")) |
            (SubstackArticle.content_markdown.ilike(f"%{search}%"))
        )
    
    author_facets = [
        {"name": name, "count": count}
        for name, count in author_counts.group_by(SubstackAuthor.name).all()
    ]
    
    # Concept facets - get all concepts with counts
    concept_facets = []
    all_concepts = concept_service.get_all_concepts_with_counts(content_type='article')
    
    # Only include concepts that appear in the current filtered set
    if search or authors:
        # Get article IDs from current filter
        filtered_article_ids = [str(a.id) for a in all_articles_query.all()]
        
        # Filter concepts to only those on filtered articles
        for concept in all_concepts:
            # Count how many of the filtered articles have this concept
            count = concept_service.tag_instances.count_documents({
                'content_type': 'article',
                'concept_id': concept['concept_id'],
                'content_id': {'$in': filtered_article_ids}
            })
            if count > 0:
                concept_facets.append({
                    **concept,
                    'count': count
                })
    else:
        concept_facets = all_concepts[:50]  # Top 50 concepts
    
    # Sort concept facets by count
    concept_facets.sort(key=lambda x: x['count'], reverse=True)
    
    # Convert articles to response format
    article_results = []
    for article in articles:
        concepts = concept_service.get_tags_for_content('article', str(article.id))
        
        article_results.append({
            "id": article.id,
            "title": article.title,
            "author": {
                "id": article.author.id,
                "name": article.author.name,
                "email": article.author.email
            } if article.author else None,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "url": article.url,
            "preview": article.preview,
            "content_length": len(article.content_markdown) if article.content_markdown else 0,
            "snippet_count": len(article.snippets),
            "summary": article.summary,
            "created_at": article.collected_at.isoformat() if article.collected_at else None,
            "concepts": concepts,
            "concept_ids": [c['concept_id'] for c in concepts]
        })
    
    return {
        "articles": article_results,
        "facets": {
            "authors": author_facets,
            "concepts": concept_facets[:50]  # Limit to top 50
        },
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{article_id}")
def get_article(article_id: int, include_concepts: bool = True, db: Session = Depends(get_db)):
    """Get a specific article by ID with concepts"""
    article = db.query(SubstackArticle).options(
        joinedload(SubstackArticle.author),
        joinedload(SubstackArticle.snippets)
    ).filter(SubstackArticle.id == article_id).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Get concepts
    concepts = concept_service.get_tags_for_content('article', str(article_id))
    
    # Build response
    result = {
        "id": article.id,
        "title": article.title,
        "author": {
            "id": article.author.id,
            "name": article.author.name,
            "email": article.author.email
        } if article.author else None,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "url": article.url,
        "content_markdown": article.content_markdown,
        "preview": article.preview,
        "summary": article.summary,
        "snippet_count": len(article.snippets),
        "created_at": article.collected_at.isoformat() if article.collected_at else None
    }
    
    if include_concepts:
        result["concepts"] = concepts
    else:
        result["concept_ids"] = [c['concept_id'] for c in concepts]
    
    return result

@router.post("/{article_id}/concepts")
def add_concept_to_article(
    article_id: int,
    text: str = Query(..., description="Text to create/find concept from"),
    db: Session = Depends(get_db)
):
    """Add a concept to an article (creates concept if needed)"""
    
    # Check if article exists
    article = db.query(SubstackArticle).filter(SubstackArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Add concept - preserve the exact text as display_name
    success, concept_id = concept_service.add_tag('article', str(article_id), text, preserve_display_name=True)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add concept")
    
    # Get concept details
    concept = concept_service.get_concept_by_id(concept_id)
    
    return {
        "message": "Concept added successfully",
        "concept": {
            "concept_id": concept_id,
            "id": concept.get('id'),
            "slug": concept.get('slug'),
            "display_name": concept.get('display_name')
        }
    }

@router.delete("/{article_id}/concepts/{concept_id}")
def remove_concept_from_article(article_id: int, concept_id: str):
    """Remove a concept from an article"""
    
    success = concept_service.remove_tag('article', str(article_id), concept_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Concept not found on this article")
    
    return {"message": "Concept removed successfully"}

@router.post("/{article_id}/summarize")
def summarize_article(article_id: int, db: Session = Depends(get_db)):
    """Generate AI summary for an article"""
    article = db.query(SubstackArticle).filter(SubstackArticle.id == article_id).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if not article.content_markdown:
        raise HTTPException(status_code=400, detail="Article has no content to summarize")
    
    # Generate summary
    summarizer = ArticleSummarizer()
    summary = summarizer.summarize(article.content_markdown)
    
    # Save to database
    article.summary = summary
    db.commit()
    
    return {"summary": summary}

@router.get("/concepts/hierarchy")
def get_concept_hierarchy():
    """Get concepts organized in hierarchy for faceted browsing"""
    
    # Get all concepts with their hierarchy
    all_concepts = concept_service.concepts.find({})
    
    # Build hierarchy structure
    root_concepts = []
    concept_map = {}
    
    # First pass: Create concept map
    for concept in all_concepts:
        concept_id = str(concept['_id'])
        concept_map[concept_id] = {
            "concept_id": concept_id,
            "id": concept.get('id'),
            "slug": concept.get('slug'),
            "display_name": concept.get('display_name'),
            "entity_type": concept.get('entity_type'),
            "parents": concept.get('parents', []),
            "children": [],
            "count": 0  # Will be populated later
        }
    
    # Second pass: Build hierarchy
    for concept_id, concept_data in concept_map.items():
        if not concept_data['parents']:
            # Root concept
            root_concepts.append(concept_data)
        else:
            # Add to parent's children
            for parent_id in concept_data['parents']:
                if parent_id in concept_map:
                    concept_map[parent_id]['children'].append(concept_data)
    
    # Third pass: Add counts for articles
    for concept_id in concept_map:
        count = concept_service.tag_instances.count_documents({
            'content_type': 'article',
            'concept_id': concept_id
        })
        concept_map[concept_id]['count'] = count
    
    return root_concepts