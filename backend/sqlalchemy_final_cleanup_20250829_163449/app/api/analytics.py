from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import json

from app.models import get_db, Tweet, Tag
from app.services.llm_service import LLMService

router = APIRouter()

@router.get("/trends/timeline")
def get_trend_timeline(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Get tweet volume timeline for trend visualization
    Returns daily counts for the specified period
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Get daily tweet counts
    daily_counts = db.query(
        func.date(Tweet.created_at).label('date'),
        func.count(Tweet.id).label('count')
    ).filter(
        Tweet.created_at >= start_date
    ).group_by(
        func.date(Tweet.created_at)
    ).order_by('date').all()
    
    # Get hourly counts for last 24 hours
    hourly_start = end_date - timedelta(hours=24)
    hourly_counts = db.query(
        func.strftime('%Y-%m-%d %H:00', Tweet.created_at).label('hour'),
        func.count(Tweet.id).label('count')
    ).filter(
        Tweet.created_at >= hourly_start
    ).group_by(
        func.strftime('%Y-%m-%d %H:00', Tweet.created_at)
    ).order_by('hour').all()
    
    # Get per-account trends
    account_trends = db.query(
        Tweet.author_username,
        func.date(Tweet.created_at).label('date'),
        func.count(Tweet.id).label('count')
    ).filter(
        Tweet.created_at >= start_date
    ).group_by(
        Tweet.author_username,
        func.date(Tweet.created_at)
    ).all()
    
    # Format for frontend charting
    result = {
        "daily": [
            {"date": str(item.date), "count": item.count}
            for item in daily_counts
        ],
        "hourly": [
            {"hour": item.hour, "count": item.count}
            for item in hourly_counts
        ],
        "by_account": {}
    }
    
    # Group by account
    for item in account_trends:
        if item.author_username not in result["by_account"]:
            result["by_account"][item.author_username] = []
        result["by_account"][item.author_username].append({
            "date": str(item.date),
            "count": item.count
        })
    
    return result

@router.get("/trends/tags")
def get_tag_trends(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get trending tags with counts over time
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Get top tags by frequency
    top_tags = db.query(
        Tag.tag,
        func.count(Tag.id).label('total_count')
    ).join(
        Tweet
    ).filter(
        Tweet.created_at >= start_date
    ).group_by(
        Tag.tag
    ).order_by(
        func.count(Tag.id).desc()
    ).limit(limit).all()
    
    # Get daily counts for each top tag
    tag_timeline = {}
    for tag_name, _ in top_tags:
        daily_counts = db.query(
            func.date(Tweet.created_at).label('date'),
            func.count(Tag.id).label('count')
        ).join(
            Tag
        ).filter(
            and_(
                Tag.tag == tag_name,
                Tweet.created_at >= start_date
            )
        ).group_by(
            func.date(Tweet.created_at)
        ).all()
        
        tag_timeline[tag_name] = [
            {"date": str(item.date), "count": item.count}
            for item in daily_counts
        ]
    
    return {
        "top_tags": [
            {"tag": tag, "count": count}
            for tag, count in top_tags
        ],
        "timeline": tag_timeline
    }

@router.post("/summarize")
def summarize_tweets(
    period: Optional[str] = Query(None, description="Period: today, 3days, week"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    author: Optional[str] = Query(None, description="Filter by author"),
    db: Session = Depends(get_db)
):
    """
    Summarize tweets based on filters using LLM
    """
    # Build query
    query = db.query(Tweet)
    
    # Apply time filter
    if period:
        if period == "today":
            start_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        elif period == "3days":
            start_date = datetime.now(timezone.utc) - timedelta(days=3)
        elif period == "week":
            start_date = datetime.now(timezone.utc) - timedelta(days=7)
        else:
            start_date = datetime.now(timezone.utc) - timedelta(days=1)
        
        query = query.filter(Tweet.created_at >= start_date)
    
    # Apply tag filter
    if tags:
        query = query.join(Tag).filter(Tag.tag.in_(tags))
    
    # Apply author filter
    if author:
        query = query.filter(Tweet.author_username == author)
    
    # Get tweets
    tweets = query.order_by(Tweet.created_at.desc()).limit(100).all()
    
    if not tweets:
        return {"summary": "No tweets found for the specified filters.", "stats": {}, "filters": {}}
    
    # Prepare tweets for summarization
    tweet_texts = []
    for tweet in tweets[:50]:  # Limit to 50 for LLM context
        tweet_texts.append(f"@{tweet.author_username}: {tweet.text}")
    
    # Use LangChain LLM service for proper configuration-driven summarization
    from app.services.langchain_llm_service import get_langchain_llm_service
    
    model_used = 'unknown'
    
    try:
        # Use the LangChain service which properly handles all configurations
        llm_service = get_langchain_llm_service()
        
        # Create tweet context for summarization
        tweet_context = {
            "tweets": [
                {
                    "author": tweet.author_username,
                    "text": tweet.text,
                    "likes": tweet.like_count,
                    "retweets": tweet.retweet_count
                }
                for tweet in tweets[:50]  # Limit to 50 for context
            ],
            "period": period or "recent",
            "total_count": len(tweets)
        }
        
        # Use the configured summarization method
        summary = llm_service.summarize_tweets(tweet_context)
        
        # Get the model that was used
        model_config = llm_service.llm_config.get('models', {}).get('summarization', {})
        model_used = model_config.get('model', 'claude-sonnet-4-20250514')
        
        # Check if summary is None or empty
        if not summary or summary.strip() == "":
            raise ValueError("Empty summary returned")
        
    except Exception as e:
        # Fallback to basic summary
        summary = f"Collection of {len(tweets)} tweets"
        if tags:
            summary += f" tagged with {', '.join(tags)}"
        if author:
            summary += f" from @{author}"
        if period:
            summary += f" from the last {period}"
        
        # Add basic stats
        total_likes = sum(t.like_count for t in tweets)
        total_retweets = sum(t.retweet_count for t in tweets)
        summary += f". Total engagement: {total_likes} likes, {total_retweets} retweets."
    
    # Get statistics
    stats = {
        "tweet_count": len(tweets),
        "unique_authors": len(set(t.author_username for t in tweets)),
        "total_likes": sum(t.like_count for t in tweets),
        "total_retweets": sum(t.retweet_count for t in tweets),
        "time_range": {
            "start": None,
            "end": None
        }
    }
    
    # Handle datetime comparison safely
    if tweets:
        # Ensure all datetimes are timezone-aware
        tweet_times = []
        for t in tweets:
            if t.created_at:
                # If datetime is naive, make it aware (assume UTC)
                if t.created_at.tzinfo is None:
                    tweet_times.append(t.created_at.replace(tzinfo=timezone.utc))
                else:
                    tweet_times.append(t.created_at)
        
        if tweet_times:
            stats["time_range"]["start"] = min(tweet_times).isoformat()
            stats["time_range"]["end"] = max(tweet_times).isoformat()
    
    # Ensure summary is not None or empty
    if not summary or summary.strip() == "":
        summary = f"Summary generation completed. Found {len(tweets)} tweets from {stats['unique_authors']} authors with {stats['total_likes']} total likes."
    
    return {
        "summary": summary,
        "stats": stats,
        "filters": {
            "period": period,
            "tags": tags,
            "author": author
        },
        "model_used": model_used  # Include model attribution
    }