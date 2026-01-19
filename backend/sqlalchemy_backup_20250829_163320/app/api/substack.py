"""
Substack API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.models import get_db
from app.models.substack import (
    SubstackAuthor, 
    SubstackArticle, 
    ArticleSnippet, 
    ArticleTag,
    SnippetTag
)
from app.services.article_summarizer import ArticleSummarizer
from app.analyzers.substack_trend_analyzer import SubstackTrendAnalyzer
from app.services.unified_tag_service import UnifiedTagService
from app.services.vector_store_openai import get_vector_store

router = APIRouter()

# Pydantic models for request/response
class ArticleTagCreate(BaseModel):
    tag: str
    tag_type: str = 'manual'
    confidence: float = 1.0

class SnippetCreate(BaseModel):
    text: str
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None
    annotation: Optional[str] = None
    category: Optional[str] = None
    importance: int = 3
    tags: List[str] = []

class SnippetUpdate(BaseModel):
    annotation: Optional[str] = None
    category: Optional[str] = None
    importance: Optional[int] = None

class ArticleDateUpdate(BaseModel):
    published_at: datetime

class ArticleUrlUpdate(BaseModel):
    url: str

@router.get("/articles")
def get_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    author_id: Optional[int] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    use_ontology: bool = Query(True, description="Use tag ontology for hierarchical filtering"),
    db: Session = Depends(get_db)
):
    """Get Substack articles with pagination and filters"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Filter out soft-deleted articles
    query = db.query(SubstackArticle).filter(
        SubstackArticle.deleted == False
    ).options(
        joinedload(SubstackArticle.author),
        joinedload(SubstackArticle.tags),
        joinedload(SubstackArticle.snippets)
    )
    
    # Apply filters
    if author_id:
        query = query.filter(SubstackArticle.author_id == author_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (SubstackArticle.title.ilike(search_term)) |
            (SubstackArticle.content_markdown.ilike(search_term))
        )
    
    if tag:
        # Use unified tag service for consistent filtering
        unified_service = UnifiedTagService(db)
        query = unified_service.filter_articles_by_tag(query, tag, use_hierarchy=use_ontology)
        logger.info(f"Filtering articles by tag: '{tag}' (hierarchy={'enabled' if use_ontology else 'disabled'})")
    
    # Order by published date
    query = query.order_by(desc(SubstackArticle.published_at))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    articles = query.offset(skip).limit(limit).all()
    
    # Format response
    result = []
    for article in articles:
        result.append({
            "id": article.id,
            "title": article.title,
            "subtitle": article.subtitle,
            "author": {
                "id": article.author.id,
                "name": article.author.name,
                "subdomain": article.author.subdomain
            },
            "url": article.url,
            "preview": article.preview,
            "word_count": article.word_count,
            "reading_time_minutes": article.reading_time_minutes,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "collected_at": article.collected_at.isoformat() if article.collected_at else None,
            "tags": [
                {"tag": t.tag, "type": t.tag_type}
                for t in article.tags
                if t.tag and t.tag.strip()
            ],
            "snippet_count": len(article.snippets),
            "has_summary": article.summary is not None,
            "likes": article.likes,
            "comments": article.comments
        })
    
    return {
        "articles": result,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/articles/{article_id}")
def get_article(article_id: int, db: Session = Depends(get_db)):
    """Get full article content with markdown"""
    article = db.query(SubstackArticle).options(
        joinedload(SubstackArticle.author),
        joinedload(SubstackArticle.tags),
        joinedload(SubstackArticle.snippets).joinedload(ArticleSnippet.snippet_tags)
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
        },
        "url": article.url,
        "content_markdown": article.content_markdown,
        "content_html": article.content_html,
        "word_count": article.word_count,
        "reading_time_minutes": article.reading_time_minutes,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "summary": article.summary,
        "key_points": article.key_points,
        "topics": article.topics,
        "sentiment": article.sentiment,
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
                "start_offset": s.start_offset,
                "end_offset": s.end_offset,
                "annotation": s.annotation,
                "category": s.category,
                "importance": s.importance,
                "created_at": s.created_at.isoformat(),
                "tags": [t.tag for t in s.snippet_tags]
            }
            for s in article.snippets
        ]
    }

@router.get("/authors")
def get_authors(db: Session = Depends(get_db)):
    """Get all Substack authors with article counts"""
    authors = db.query(
        SubstackAuthor,
        func.count(SubstackArticle.id).label('article_count'),
        func.max(SubstackArticle.published_at).label('latest_article')
    ).outerjoin(
        SubstackArticle
    ).group_by(
        SubstackAuthor.id
    ).all()
    
    result = []
    for author, article_count, latest_article in authors:
        result.append({
            "id": author.id,
            "name": author.name,
            "subdomain": author.subdomain,
            "url": author.url,
            "description": author.description,
            "article_count": article_count,
            "latest_article": latest_article.isoformat() if latest_article else None
        })
    
    return result

@router.post("/articles/{article_id}/tags")
def add_article_tag(
    article_id: int,
    tag_data: ArticleTagCreate,
    db: Session = Depends(get_db)
):
    """Add tag to article"""
    # Check article exists
    article = db.query(SubstackArticle).filter(SubstackArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check if tag already exists
    existing = db.query(ArticleTag).filter(
        ArticleTag.article_id == article_id,
        ArticleTag.tag == tag_data.tag
    ).first()
    
    if existing:
        return {"message": "Tag already exists"}
    
    # Create tag
    tag = ArticleTag(
        article_id=article_id,
        tag=tag_data.tag,
        tag_type=tag_data.tag_type,
        confidence=tag_data.confidence
    )
    db.add(tag)
    db.commit()
    
    # Update vector store with new tag
    try:
        vector_store = get_vector_store()
        # Get article title and subtitle for context
        context = f"{article.title}: {article.subtitle[:100] if article.subtitle else ''}"
        vector_store.update_tag_incrementally(tag_data.tag, 'article', context)
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to update vector store for article tag '{tag_data.tag}': {e}")
    
    return {"message": "Tag added successfully", "tag": tag_data.tag}

@router.delete("/articles/{article_id}/tags/{tag}")
def remove_article_tag(
    article_id: int,
    tag: str,
    db: Session = Depends(get_db)
):
    """Remove tag from article"""
    tag_entry = db.query(ArticleTag).filter(
        ArticleTag.article_id == article_id,
        ArticleTag.tag == tag
    ).first()
    
    if not tag_entry:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    db.delete(tag_entry)
    db.commit()
    
    return {"message": "Tag removed successfully"}

@router.patch("/articles/{article_id}/date")
def update_article_date(
    article_id: int,
    date_data: ArticleDateUpdate,
    db: Session = Depends(get_db)
):
    """Update the published date of an article"""
    # Get the article
    article = db.query(SubstackArticle).filter(SubstackArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Update the date
    article.published_at = date_data.published_at
    db.commit()
    
    return {
        "message": "Date updated successfully",
        "published_at": article.published_at.isoformat()
    }

@router.patch("/articles/{article_id}/url")
def update_article_url(
    article_id: int,
    url_data: ArticleUrlUpdate,
    db: Session = Depends(get_db)
):
    """Update the URL of an article"""
    # Get the article
    article = db.query(SubstackArticle).filter(SubstackArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Update the URL
    article.url = url_data.url
    db.commit()
    
    return {
        "message": "URL updated successfully",
        "url": article.url
    }

@router.post("/articles/{article_id}/snippets")
def create_snippet(
    article_id: int,
    snippet_data: SnippetCreate,
    db: Session = Depends(get_db)
):
    """Create a new snippet for an article"""
    # Check article exists
    article = db.query(SubstackArticle).filter(SubstackArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Create snippet
    snippet = ArticleSnippet(
        article_id=article_id,
        text=snippet_data.text,
        start_offset=snippet_data.start_offset,
        end_offset=snippet_data.end_offset,
        annotation=snippet_data.annotation,
        category=snippet_data.category,
        importance=snippet_data.importance
    )
    db.add(snippet)
    db.flush()
    
    # Add tags
    for tag_name in snippet_data.tags:
        tag = SnippetTag(
            snippet_id=snippet.id,
            tag=tag_name
        )
        db.add(tag)
    
    db.commit()
    db.refresh(snippet)
    
    return {
        "id": snippet.id,
        "text": snippet.text,
        "annotation": snippet.annotation,
        "category": snippet.category,
        "created_at": snippet.created_at.isoformat()
    }

@router.patch("/snippets/{snippet_id}")
def update_snippet(
    snippet_id: int,
    update_data: SnippetUpdate,
    db: Session = Depends(get_db)
):
    """Update snippet annotation or metadata"""
    snippet = db.query(ArticleSnippet).filter(ArticleSnippet.id == snippet_id).first()
    
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")
    
    # Update fields
    if update_data.annotation is not None:
        snippet.annotation = update_data.annotation
    if update_data.category is not None:
        snippet.category = update_data.category
    if update_data.importance is not None:
        snippet.importance = update_data.importance
    
    snippet.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(snippet)
    
    return {"message": "Snippet updated successfully"}

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

@router.delete("/articles/{article_id}")
def soft_delete_article(article_id: int, db: Session = Depends(get_db)):
    """Soft delete an article (mark as deleted but keep in database)"""
    article = db.query(SubstackArticle).filter(SubstackArticle.id == article_id).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    article.deleted = True
    db.commit()
    
    return {"message": "Article deleted successfully", "id": article_id}

@router.delete("/authors/{author_id}")
def delete_author_and_articles(
    author_id: int,
    keep_author: bool = Query(False, description="Keep author, only delete articles"),
    db: Session = Depends(get_db)
):
    """Delete all articles from an author and optionally the author itself"""
    # Find the author
    author = db.query(SubstackAuthor).filter(SubstackAuthor.id == author_id).first()
    
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    # Get all articles from this author
    articles = db.query(SubstackArticle).filter(
        SubstackArticle.author_id == author_id
    ).all()
    
    deleted_articles = 0
    deleted_snippets = 0
    deleted_tags = 0
    
    # Delete all articles and related data
    for article in articles:
        # Delete snippets
        snippets = db.query(ArticleSnippet).filter(
            ArticleSnippet.article_id == article.id
        ).all()
        for snippet in snippets:
            db.delete(snippet)
            deleted_snippets += 1
        
        # Delete tags
        tags = db.query(ArticleTag).filter(
            ArticleTag.article_id == article.id
        ).all()
        for tag in tags:
            db.delete(tag)
            deleted_tags += 1
        
        # Delete article
        db.delete(article)
        deleted_articles += 1
    
    # Delete author if requested
    author_name = author.name
    if not keep_author:
        db.delete(author)
    
    db.commit()
    
    return {
        "message": f"Successfully deleted author '{author_name}' and all related data" if not keep_author else f"Successfully deleted all articles from '{author_name}'",
        "deleted": {
            "articles": deleted_articles,
            "snippets": deleted_snippets,
            "tags": deleted_tags,
            "author": not keep_author
        }
    }

@router.post("/articles/{article_id}/restore")
def restore_article(article_id: int, db: Session = Depends(get_db)):
    """Restore a soft-deleted article"""
    article = db.query(SubstackArticle).filter(SubstackArticle.id == article_id).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    article.deleted = False
    db.commit()
    
    return {"message": "Article restored successfully", "id": article_id}

@router.delete("/snippets/{snippet_id}")
def delete_snippet(snippet_id: int, db: Session = Depends(get_db)):
    """Delete a snippet"""
    snippet = db.query(ArticleSnippet).filter(ArticleSnippet.id == snippet_id).first()
    
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")
    
    db.delete(snippet)
    db.commit()
    
    return {"message": "Snippet deleted successfully"}

@router.get("/stats")
def get_substack_stats(db: Session = Depends(get_db)):
    """Get Substack collection statistics"""
    total_articles = db.query(SubstackArticle).count()
    total_authors = db.query(SubstackAuthor).count()
    total_snippets = db.query(ArticleSnippet).count()
    total_tags = db.query(func.count(func.distinct(ArticleTag.tag))).scalar()
    
    # Recent activity
    last_week = datetime.utcnow() - timedelta(days=7)
    recent_articles = db.query(SubstackArticle).filter(
        SubstackArticle.collected_at >= last_week
    ).count()
    
    # Top authors by article count
    top_authors = db.query(
        SubstackAuthor.name,
        func.count(SubstackArticle.id).label('count')
    ).join(
        SubstackArticle
    ).group_by(
        SubstackAuthor.id
    ).order_by(
        desc('count')
    ).limit(5).all()
    
    # Most used tags
    top_tags = db.query(
        ArticleTag.tag,
        func.count(ArticleTag.id).label('count')
    ).group_by(
        ArticleTag.tag
    ).order_by(
        desc('count')
    ).limit(10).all()
    
    return {
        "total_articles": total_articles,
        "total_authors": total_authors,
        "total_snippets": total_snippets,
        "total_tags": total_tags,
        "recent_articles": recent_articles,
        "top_authors": [
            {"name": name, "count": count}
            for name, count in top_authors
        ],
        "top_tags": [
            {"tag": tag, "count": count}
            for tag, count in top_tags
        ]
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
            "key_points": result["key_points"],
            "model_used": result.get("model_used", "claude-sonnet-4-20250514")  # Include model attribution
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

@router.get("/trends")
def get_substack_trends(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get comprehensive Substack trend analysis"""
    try:
        analyzer = SubstackTrendAnalyzer(db)
        trends = analyzer.analyze_trends(days)
        
        # Ensure all required fields are present even if empty
        if not trends or trends.get("status") == "No articles found":
            from datetime import datetime, timedelta
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            trends = {
                "period": f"{days} days",
                "total_articles": 0,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "topic_trends": {
                    "top_topics": [],
                    "trending_up": []
                },
                "author_trends": {
                    "most_active": [],
                    "total_authors": 0,
                    "avg_articles_per_author": 0
                },
                "tag_trends": {
                    "top_tags": [],
                    "tag_relationships": [],
                    "unique_tags": 0
                },
                "snippet_insights": {
                    "categories": {},
                    "important_highlights": [],
                    "total_snippets": 0
                },
                "velocity_trends": [],
                "content_clusters": [],
                "emerging_themes": [],
                "summary": {
                    "key_insights": ["No articles found in the specified time period"],
                    "recommendations": ["Check back later for new content"]
                }
            }
        
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze trends: {str(e)}")

@router.get("/search")
def search_articles(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Full-text search across articles"""
    search_term = f"%{q}%"
    
    # Search in articles
    articles = db.query(SubstackArticle).filter(
        (SubstackArticle.title.ilike(search_term)) |
        (SubstackArticle.subtitle.ilike(search_term)) |
        (SubstackArticle.content_markdown.ilike(search_term))
    ).limit(limit).all()
    
    # Search in snippets
    snippets = db.query(ArticleSnippet).join(
        SubstackArticle
    ).filter(
        (ArticleSnippet.text.ilike(search_term)) |
        (ArticleSnippet.annotation.ilike(search_term))
    ).limit(limit).all()
    
    return {
        "articles": [
            {
                "id": a.id,
                "title": a.title,
                "preview": a.preview,
                "author": a.author.name
            }
            for a in articles
        ],
        "snippets": [
            {
                "id": s.id,
                "text": s.text[:200],
                "article_id": s.article_id,
                "article_title": s.article.title
            }
            for s in snippets
        ]
    }