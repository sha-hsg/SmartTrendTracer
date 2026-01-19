"""
API endpoints for paper trends and analytics
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..services.paper_trends_service import PaperTrendsService

router = APIRouter(prefix="/api/papers/trends", tags=["paper-trends"])
trends_service = PaperTrendsService()

@router.get("/popular")
def get_popular_papers(
    days: int = Query(30, description="Time window in days"),
    limit: int = Query(10, description="Number of papers to return"),
) -> Dict[str, Any]:
    """Get most popular papers by engagement metrics"""
    try:
        papers = trends_service.get_popular_papers(db, days=days, limit=limit)
        return {
            "papers": papers,
            "time_window_days": days,
            "count": len(papers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emerging-topics")
def get_emerging_topics(
    days_window: int = Query(7, description="Recent time window in days"),
    min_papers: int = Query(2, description="Minimum papers for a topic"),
) -> Dict[str, Any]:
    """Identify emerging research topics based on recent activity"""
    try:
        topics = trends_service.identify_emerging_topics(
            db, 
            days_window=days_window,
            min_papers=min_papers
        )
        return {
            "emerging_topics": topics,
            "time_window_days": days_window,
            "min_papers_threshold": min_papers,
            "count": len(topics)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active-authors")
def get_active_authors(
    limit: int = Query(10, description="Number of authors to return"),
) -> Dict[str, Any]:
    """Get most active authors and their research topics"""
    try:
        authors = trends_service.analyze_author_activity(db, limit=limit)
        return {
            "authors": authors,
            "count": len(authors)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cross-mentions/{paper_id}")
def get_cross_source_mentions(
    paper_id: int,
) -> Dict[str, Any]:
    """Find mentions of a paper in tweets and articles"""
    try:
        mentions = trends_service.find_cross_source_mentions(db, paper_id)
        if not mentions:
            raise HTTPException(status_code=404, detail="Paper not found")
        return mentions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/topic-evolution")
def get_topic_evolution(
    tag: str = Query(..., description="Tag to analyze"),
    days: int = Query(90, description="Time window in days"),
) -> Dict[str, Any]:
    """Track how a research topic has evolved over time"""
    try:
        evolution = trends_service.get_topic_evolution(db, tag, days)
        return evolution
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/citation-network/{paper_id}")
def get_citation_network(
    paper_id: int,
    depth: int = Query(2, description="Network depth", le=3),
) -> Dict[str, Any]:
    """Get citation network around a paper"""
    try:
        network = trends_service.get_citation_network(db, paper_id, depth)
        if not network:
            raise HTTPException(status_code=404, detail="Paper not found")
        return network
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unified-timeline")
def get_unified_timeline(
    days: int = Query(30, description="Time window in days"),
) -> Dict[str, Any]:
    """Get unified timeline of papers, tweets, and articles"""
    try:
        from datetime import timedelta
        from ..models import Paper, Tweet, SubstackArticle
        
        cutoff = datetime.now() - timedelta(days=days)
        
        # Get recent papers
        papers = db.query(Paper).filter(
            Paper.created_at >= cutoff
        ).order_by(Paper.created_at.desc()).limit(20).all()
        
        # Get recent tweets
        tweets = db.query(Tweet).filter(
            Tweet.created_at >= cutoff
        ).order_by(Tweet.created_at.desc()).limit(50).all()
        
        # Get recent articles
        articles = db.query(SubstackArticle).filter(
            SubstackArticle.created_at >= cutoff
        ).order_by(SubstackArticle.created_at.desc()).limit(20).all()
        
        # Combine into timeline
        timeline = []
        
        for paper in papers:
            timeline.append({
                "type": "paper",
                "id": paper.id,
                "title": paper.title,
                "timestamp": paper.created_at.isoformat() if paper.created_at else None,
                "publication_date": paper.publication_date.isoformat() if paper.publication_date else None,
                "authors": [a.name for a in paper.authors[:3]]
            })
        
        for tweet in tweets:
            timeline.append({
                "type": "tweet",
                "id": tweet.id,
                "text": tweet.text[:200],
                "timestamp": tweet.created_at.isoformat() if tweet.created_at else None,
                "author": tweet.author_username
            })
        
        for article in articles:
            timeline.append({
                "type": "article",
                "id": article.id,
                "title": article.title,
                "timestamp": article.created_at.isoformat() if article.created_at else None,
                "author": article.author.name if article.author else None
            })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {
            "timeline": timeline[:100],  # Limit to 100 most recent items
            "counts": {
                "papers": len(papers),
                "tweets": len(tweets),
                "articles": len(articles)
            },
            "time_window_days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/research-impact/{paper_id}")
def get_research_impact(
    paper_id: int,
) -> Dict[str, Any]:
    """Analyze the impact of a research paper across all sources"""
    try:
        from ..models import Paper, PaperTag, PaperSnippet
        
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        # Get cross-source mentions
        mentions = trends_service.find_cross_source_mentions(db, paper_id)
        
        # Get tags
        tags = db.query(PaperTag.tag).filter(
            PaperTag.paper_id == paper_id
        ).all()
        
        # Get snippets
        snippets = db.query(PaperSnippet).filter(
            PaperSnippet.paper_id == paper_id
        ).all()
        
        # Calculate impact score
        impact_score = (
            (paper.citation_count or 0) * 10 +
            len(mentions.get("tweet_mentions", [])) * 5 +
            len(mentions.get("article_mentions", [])) * 8 +
            len(tags) * 2 +
            len(snippets) * 3
        )
        
        return {
            "paper": {
                "id": paper.id,
                "title": paper.title,
                "publication_date": paper.publication_date.isoformat() if paper.publication_date else None,
                "citation_count": paper.citation_count
            },
            "impact_metrics": {
                "impact_score": impact_score,
                "citation_count": paper.citation_count or 0,
                "tweet_mentions": len(mentions.get("tweet_mentions", [])),
                "article_mentions": len(mentions.get("article_mentions", [])),
                "tag_count": len(tags),
                "snippet_count": len(snippets)
            },
            "tags": [t[0] for t in tags],
            "social_mentions": mentions,
            "engagement": {
                "snippets": [
                    {
                        "id": s.id,
                        "content": s.content[:100],
                        "category": s.category
                    }
                    for s in snippets[:5]
                ]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))