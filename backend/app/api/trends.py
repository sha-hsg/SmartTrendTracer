from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta
from typing import List, Dict

router = APIRouter()

@router.get("/")
def get_trends(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(10, ge=1, le=50),
):
    """Get trending topics in the last N hours"""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get trending hashtags from tweet text
    recent_tweets = db.query(Tweet).filter(
        Tweet.created_at >= cutoff_time
    ).all()
    
    hashtag_counts = {}
    for tweet in recent_tweets:
        # Simple hashtag extraction
        words = tweet.text.split()
        hashtags = [w for w in words if w.startswith('#')]
        for hashtag in hashtags:
            hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1
    
    # Sort by count
    trending = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    return {
        "period_hours": hours,
        "trends": [
            {"topic": topic, "mentions": count}
            for topic, count in trending
        ],
        "total_tweets_analyzed": len(recent_tweets)
    }

@router.get("/topics")
def get_topics(
    limit: int = 20,
):
    """Get all topics with statistics"""
    topics = db.query(Topic).order_by(Topic.mention_count.desc()).limit(limit).all()
    
    return [
        {
            "id": topic.id,
            "name": topic.name,
            "category": topic.category,
            "mention_count": topic.mention_count,
            "first_seen": topic.first_seen,
            "last_seen": topic.last_seen
        }
        for topic in topics
    ]

@router.get("/analysis")
def get_trend_analysis(
):
    """Get comprehensive trend analysis"""
    now = datetime.utcnow()
    
    # Different time windows
    windows = {
        "last_hour": now - timedelta(hours=1),
        "last_6_hours": now - timedelta(hours=6),
        "last_24_hours": now - timedelta(hours=24),
        "last_week": now - timedelta(days=7)
    }
    
    analysis = {}
    
    for window_name, cutoff in windows.items():
        tweet_count = db.query(Tweet).filter(Tweet.created_at >= cutoff).count()
        
        # Get top tags in this window
        top_tags = db.query(
            Tag.tag,
            func.count(Tag.id).label("count")
        ).join(Tweet).filter(
            Tweet.created_at >= cutoff
        ).group_by(Tag.tag).order_by(
            func.count(Tag.id).desc()
        ).limit(5).all()
        
        analysis[window_name] = {
            "tweet_count": tweet_count,
            "top_tags": [{"tag": tag, "count": count} for tag, count in top_tags]
        }
    
    # Get velocity (growth rate) for tags
    yesterday = now - timedelta(days=1)
    two_days_ago = now - timedelta(days=2)
    
    # Tags from last 24 hours
    recent_tags = db.query(
        Tag.tag,
        func.count(Tag.id).label("count")
    ).join(Tweet).filter(
        Tweet.created_at >= yesterday
    ).group_by(Tag.tag).all()
    
    # Tags from previous 24 hours
    previous_tags = db.query(
        Tag.tag,
        func.count(Tag.id).label("count")
    ).join(Tweet).filter(
        and_(Tweet.created_at >= two_days_ago, Tweet.created_at < yesterday)
    ).group_by(Tag.tag).all()
    
    previous_dict = {tag: count for tag, count in previous_tags}
    
    # Calculate velocity
    trending_up = []
    trending_down = []
    
    for tag, current_count in recent_tags:
        previous_count = previous_dict.get(tag, 0)
        if previous_count > 0:
            change_rate = ((current_count - previous_count) / previous_count) * 100
            if change_rate > 50:  # More than 50% increase
                trending_up.append({"tag": tag, "growth": f"{change_rate:.1f}%"})
            elif change_rate < -30:  # More than 30% decrease
                trending_down.append({"tag": tag, "decline": f"{abs(change_rate):.1f}%"})
    
    analysis["trending_up"] = trending_up[:5]
    analysis["trending_down"] = trending_down[:5]
    
    return analysis