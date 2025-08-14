"""
Enhanced Substack API with tag suggestions and faceted browsing
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, and_, or_
from typing import List, Optional, Dict
from pydantic import BaseModel

from app.models import get_db
from app.models.substack import (
    SubstackAuthor, 
    SubstackArticle, 
    ArticleTag,
    ArticleSnippet
)
from app.services.llm_service import get_llm_service
from app.services.vector_store_openai import get_vector_store
from app.services.tag_normalizer import get_tag_normalizer
from app.services.article_summarizer import ArticleSummarizer
from datetime import datetime

router = APIRouter()

class TagSuggestionResponse(BaseModel):
    article_id: int
    existing_suggestions: List[Dict]
    new_suggestions: List[Dict]
    already_tagged: List[str]
    model_used: str
    total_suggestions: int

class ArticleTagCreate(BaseModel):
    tag: str
    tag_type: str = 'manual'
    confidence: float = 1.0

class FacetedSearchResponse(BaseModel):
    articles: List[Dict]
    facets: Dict
    total: int
    page: int
    page_size: int

@router.post("/articles/{article_id}/suggest-tags")
def suggest_tags_for_article(article_id: int, db: Session = Depends(get_db)):
    """Get AI-suggested tags for a Substack article using both similarity search and LLM"""
    
    # Get the article
    article = db.query(SubstackArticle).filter(SubstackArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Get vector store for similarity search
    vector_store = get_vector_store()
    
    # Get LLM service for new tag generation
    llm_service = get_llm_service()
    
    # Check which tags already exist for this article
    existing_tags_on_article = db.query(ArticleTag.tag).filter(
        ArticleTag.article_id == article_id
    ).all()
    existing_tag_names = [t[0] for t in existing_tags_on_article]
    
    # Prepare article text for analysis (combine title, subtitle, and significant content)
    article_text = f"{article.title}\n"
    if article.subtitle:
        article_text += f"{article.subtitle}\n"
    
    # For articles, use more content for better tag generation
    if article.content_markdown:
        # Use up to 5000 chars for comprehensive analysis (articles are longer)
        # This captures the main themes without overwhelming the LLM
        content_length = min(5000, len(article.content_markdown))
        article_text += article.content_markdown[:content_length]
        
        # If article is very long, also add a snippet from the middle and end
        if len(article.content_markdown) > 5000:
            # Add a middle section (helps capture topics that develop later)
            mid_point = len(article.content_markdown) // 2
            article_text += "\n...\n" + article.content_markdown[mid_point:mid_point+1000]
            
            # Add conclusion (often summarizes key points)
            article_text += "\n...\n" + article.content_markdown[-1000:]
    elif article.preview:
        article_text += article.preview
    
    # 1. Find similar existing tags from the vector store
    similar_tags = []
    try:
        # Search for tags similar to the article content
        search_results = vector_store.search_similar_tags(
            query_text=article_text,
            k=15,  # Get more candidates for articles
            min_similarity=0.40  # Lower threshold for longer, more diverse content
        )
        
        # Filter out tags already on this article
        for tag, score, count in search_results:
            if tag not in existing_tag_names:
                similar_tags.append({
                    'tag': tag,
                    'score': round(score, 3),
                    'usage_count': count,
                    'type': 'existing'
                })
        
        # Keep top 10 similar tags for articles (more comprehensive tagging)
        similar_tags = similar_tags[:10]
        
    except Exception as e:
        print(f"Error searching similar tags: {e}")
        similar_tags = []
    
    # 2. Generate new tags using LLM (optimized for articles)
    new_tags = []
    model_used = "unknown"
    
    try:
        # Use the author name if available
        author_name = article.author.name if article.author else "Unknown"
        
        # Use the dedicated article tag suggestion method for better results
        suggested_tags = llm_service.suggest_article_tags(
            article_text=article_text,
            author=author_name,
            max_tags=10  # Request up to 10 tags for articles
        )
        
        # Check if API was successfully used
        api_was_used = "__api_success__" in suggested_tags if suggested_tags else False
        
        if api_was_used:
            suggested_tags = [tag for tag in suggested_tags if tag != "__api_success__"]
            # Get model name from config
            import json
            import os
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'llm.json')
            with open(config_path, 'r') as f:
                llm_config = json.load(f)
            model_used = llm_config['models']['tag_suggestion']['model']
        else:
            model_used = "spacy-fallback" if suggested_tags else "unknown"
        
        # Filter out tags that already exist
        similar_tag_names = [t['tag'] for t in similar_tags]
        for tag in suggested_tags:
            if tag not in existing_tag_names and tag not in similar_tag_names:
                new_tags.append({
                    'tag': tag,
                    'type': 'new',
                    'model': model_used
                })
        
        # Keep top 10 new tags for articles (comprehensive coverage)
        new_tags = new_tags[:10]
        
    except Exception as e:
        print(f"Error generating new tags: {e}")
        import traceback
        traceback.print_exc()
        new_tags = []
    
    return TagSuggestionResponse(
        article_id=article_id,
        existing_suggestions=similar_tags,
        new_suggestions=new_tags,
        already_tagged=existing_tag_names,
        model_used=model_used,
        total_suggestions=len(similar_tags) + len(new_tags)
    )

@router.post("/articles/{article_id}/tags")
def add_tag_to_article(
    article_id: int, 
    tag_data: ArticleTagCreate,
    db: Session = Depends(get_db)
):
    """Add a tag to a Substack article with normalization"""
    
    # Validate tag is not empty
    if not tag_data.tag or not tag_data.tag.strip():
        raise HTTPException(status_code=400, detail="Tag cannot be empty")
    
    # Check if article exists
    article = db.query(SubstackArticle).filter(SubstackArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # For manual tags, preserve the capitalization provided by the user
    # For other types (llm, auto), normalize the tag
    if tag_data.tag_type == 'manual':
        # Just clean spaces and keep user's capitalization
        final_tag = tag_data.tag.strip()
    else:
        # Normalize the tag for non-manual sources
        normalizer = get_tag_normalizer(db)
        final_tag = normalizer.normalize_tag(tag_data.tag)
    
    # Check if tag (case-insensitive) already exists for this article
    # to avoid duplicates like "OpenAI" and "openai"
    existing = db.query(ArticleTag).filter(
        ArticleTag.article_id == article_id,
        func.lower(ArticleTag.tag) == func.lower(final_tag)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Tag already exists for this article")
    
    # Create new tag with the final form
    new_tag = ArticleTag(
        article_id=article_id,
        tag=final_tag,
        tag_type=tag_data.tag_type,
        confidence=tag_data.confidence
    )
    
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    
    return new_tag

@router.delete("/articles/{article_id}/tags/{tag}")
def remove_tag_from_article(
    article_id: int, 
    tag: str,
    db: Session = Depends(get_db)
):
    """Remove a tag from a Substack article"""
    
    tag_obj = db.query(ArticleTag).filter(
        ArticleTag.article_id == article_id,
        ArticleTag.tag == tag
    ).first()
    
    if not tag_obj:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    db.delete(tag_obj)
    db.commit()
    
    return {"message": "Tag removed successfully"}

@router.get("/articles/faceted-search")
def faceted_search_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    author_ids: Optional[List[int]] = Query(None),
    tags: Optional[List[str]] = Query(None),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Faceted search for Substack articles
    Supports filtering by multiple authors and tags simultaneously
    """
    
    # Base query - exclude deleted articles
    query = db.query(SubstackArticle).options(
        joinedload(SubstackArticle.author),
        joinedload(SubstackArticle.tags)
    ).filter(
        or_(SubstackArticle.deleted == False, SubstackArticle.deleted.is_(None))
    )
    
    # Apply author filter
    if author_ids:
        query = query.filter(SubstackArticle.author_id.in_(author_ids))
    
    # Apply tag filter (articles must have ALL specified tags)
    if tags:
        for tag in tags:
            query = query.join(ArticleTag).filter(ArticleTag.tag == tag)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                SubstackArticle.title.ilike(search_term),
                SubstackArticle.subtitle.ilike(search_term),
                SubstackArticle.preview.ilike(search_term)
            )
        )
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    skip = (page - 1) * page_size
    articles = query.order_by(desc(SubstackArticle.published_at))\
                   .offset(skip)\
                   .limit(page_size)\
                   .all()
    
    # Get facet counts
    # Author facets (exclude deleted articles)
    author_facets = db.query(
        SubstackAuthor.id,
        SubstackAuthor.name,
        func.count(SubstackArticle.id).label('count')
    ).join(SubstackArticle)\
     .filter(or_(SubstackArticle.deleted == False, SubstackArticle.deleted.is_(None)))\
     .group_by(SubstackAuthor.id, SubstackAuthor.name)\
     .all()
    
    # Tag facets (top 30 tags, exclude deleted articles)
    tag_facets = db.query(
        ArticleTag.tag,
        func.count(ArticleTag.id).label('count')
    ).join(SubstackArticle)\
     .filter(or_(SubstackArticle.deleted == False, SubstackArticle.deleted.is_(None)))\
     .group_by(ArticleTag.tag)\
     .order_by(desc('count'))\
     .limit(30)\
     .all()
    
    # Format response
    articles_data = []
    for article in articles:
        # Count snippets
        snippet_count = db.query(ArticleSnippet).filter(ArticleSnippet.article_id == article.id).count()
        
        articles_data.append({
            'id': article.id,
            'title': article.title,
            'subtitle': article.subtitle,
            'preview': article.preview,
            'author': {
                'id': article.author.id,
                'name': article.author.name,
                'subdomain': article.author.subdomain
            } if article.author else None,
            'tags': [
                {'tag': tag.tag, 'type': tag.tag_type or 'manual'} 
                for tag in article.tags if tag.tag and tag.tag.strip()
            ],
            'published_at': article.published_at.isoformat() if article.published_at else None,
            'url': article.url,
            'word_count': article.word_count,
            'reading_time_minutes': article.reading_time_minutes,
            'snippet_count': snippet_count,
            'has_summary': bool(article.summary)
        })
    
    facets = {
        'authors': [
            {'id': author_id, 'name': name, 'count': count}
            for author_id, name, count in author_facets
        ],
        'tags': [
            {'tag': tag, 'count': count}
            for tag, count in tag_facets
        ]
    }
    
    return FacetedSearchResponse(
        articles=articles_data,
        facets=facets,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/articles/{article_id}")
def get_article(article_id: int, db: Session = Depends(get_db)):
    """Get full article content with markdown"""
    article = db.query(SubstackArticle).options(
        joinedload(SubstackArticle.author),
        joinedload(SubstackArticle.tags),
        joinedload(SubstackArticle.snippets)
    ).filter(SubstackArticle.id == article_id).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return {
        "id": article.id,
        "title": article.title,
        "subtitle": article.subtitle,
        "author": {
            "id": article.author.id,
            "name": article.author.name,
            "subdomain": article.author.subdomain,
            "url": article.author.url
        } if article.author else None,
        "url": article.url,
        "content_markdown": article.content_markdown,
        "content_html": article.content_html,
        "word_count": article.word_count,
        "reading_time_minutes": article.reading_time_minutes,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "summary": article.summary,
        "tags": [
            {
                "id": t.id,
                "tag": t.tag,
                "type": t.tag_type,
                "confidence": t.confidence
            }
            for t in article.tags
        ],
        "snippets": [
            {
                "id": s.id,
                "text": s.text,
                "annotation": s.annotation,
                "category": s.category,
                "importance": s.importance,
                "start_offset": s.start_offset if hasattr(s, 'start_offset') else None,
                "end_offset": s.end_offset if hasattr(s, 'end_offset') else None
            }
            for s in article.snippets
        ]
    }

@router.get("/tags/popular")
def get_popular_article_tags(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get most popular tags for Substack articles"""
    
    tags = db.query(
        ArticleTag.tag,
        func.count(ArticleTag.id).label("count")
    ).group_by(ArticleTag.tag)\
     .order_by(desc("count"))\
     .limit(limit)\
     .all()
    
    return [{"tag": tag, "count": count} for tag, count in tags]

class SnippetCreate(BaseModel):
    text: str
    annotation: Optional[str] = None
    category: Optional[str] = None
    importance: int = 5
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None

@router.post("/articles/{article_id}/snippets")
def create_snippet(
    article_id: int,
    snippet_data: SnippetCreate,
    db: Session = Depends(get_db)
):
    """Create a new snippet for an article"""
    
    # Check if article exists
    article = db.query(SubstackArticle).filter(SubstackArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Create snippet
    snippet = ArticleSnippet(
        article_id=article_id,
        text=snippet_data.text,
        annotation=snippet_data.annotation,
        category=snippet_data.category,
        importance=snippet_data.importance,
        start_offset=snippet_data.start_offset,
        end_offset=snippet_data.end_offset,
        created_at=datetime.utcnow()
    )
    
    db.add(snippet)
    db.commit()
    db.refresh(snippet)
    
    return {
        "id": snippet.id,
        "text": snippet.text,
        "annotation": snippet.annotation,
        "category": snippet.category,
        "importance": snippet.importance,
        "created_at": snippet.created_at.isoformat()
    }

@router.post("/articles/{article_id}/summarize")
def summarize_article(article_id: int, db: Session = Depends(get_db)):
    """Generate AI summary for an article"""
    try:
        summarizer = ArticleSummarizer()
        result = summarizer.summarize_article(article_id, db)
        return {
            "success": True,
            "summary": result["summary"],
            "key_points": result.get("key_points"),
            "model_used": result.get("model_used", "gpt-4o-mini")
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content_markdown: Optional[str] = None
    subtitle: Optional[str] = None

@router.patch("/articles/{article_id}")
def update_article(
    article_id: int,
    update_data: ArticleUpdate,
    db: Session = Depends(get_db)
):
    """Update article title, content, or subtitle"""
    article = db.query(SubstackArticle).filter(SubstackArticle.id == article_id).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Update fields if provided
    if update_data.title is not None:
        article.title = update_data.title
    if update_data.content_markdown is not None:
        article.content_markdown = update_data.content_markdown
        # Update word count
        article.word_count = len(update_data.content_markdown.split())
        article.reading_time_minutes = max(1, article.word_count // 200)
    if update_data.subtitle is not None:
        article.subtitle = update_data.subtitle
    
    db.commit()
    db.refresh(article)
    
    return {"message": "Article updated successfully", "id": article_id}