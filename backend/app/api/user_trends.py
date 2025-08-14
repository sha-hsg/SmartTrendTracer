"""
API endpoints for per-user Twitter trend analysis
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from collections import defaultdict

from app.models import get_db, Tweet, Tag

router = APIRouter()


@router.get("/per-user")
def get_per_user_trends(
    hours: int = Query(168, description="Hours to look back (default: 7 days)"),
    db: Session = Depends(get_db)
):
    """Get trend analysis broken down by Twitter user"""
    
    # Use timezone-aware datetime
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(hours=hours)
    
    # Get all tracked users
    users = db.query(Tweet.author_username).distinct().all()
    user_list = [u[0] for u in users]
    
    user_analysis = {}
    
    for username in user_list:
        # Get user's tweets in timeframe
        user_tweets = db.query(Tweet).filter(
            and_(
                Tweet.author_username == username,
                Tweet.created_at >= cutoff_time
            )
        ).all()
        
        tweet_count = len(user_tweets)
        
        # Get latest tweet
        latest_tweet = db.query(Tweet).filter(
            Tweet.author_username == username
        ).order_by(desc(Tweet.created_at)).first()
        
        # Get top tags for this user
        user_tags = db.query(
            Tag.tag,
            func.count(Tag.id).label("count")
        ).join(Tweet).filter(
            and_(
                Tweet.author_username == username,
                Tweet.created_at >= cutoff_time
            )
        ).group_by(Tag.tag).order_by(
            desc("count")
        ).limit(10).all()
        
        # Calculate activity by day
        daily_activity = defaultdict(int)
        for tweet in user_tweets:
            if tweet.created_at:
                day = tweet.created_at.date()
                daily_activity[str(day)] += 1
        
        user_analysis[username] = {
            "tweet_count": tweet_count,
            "latest_tweet": latest_tweet.created_at.isoformat() if latest_tweet and latest_tweet.created_at else None,
            "latest_text": latest_tweet.text[:200] if latest_tweet else None,
            "top_tags": [{"tag": tag, "count": count} for tag, count in user_tags],
            "daily_activity": dict(daily_activity),
            "avg_daily": tweet_count / max(hours / 24, 1)
        }
    
    # Sort users by recent activity
    sorted_users = sorted(
        user_analysis.items(),
        key=lambda x: x[1]["latest_tweet"] if x[1]["latest_tweet"] else "",
        reverse=True
    )
    
    return {
        "period_hours": hours,
        "users": dict(sorted_users),
        "total_users": len(user_list),
        "last_updated": now.isoformat()
    }


@router.get("/user/{username}")
def get_user_trend_details(
    username: str,
    days: int = Query(30, description="Days to analyze"),
    db: Session = Depends(get_db)
):
    """Get detailed trend analysis for a specific user"""
    
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(days=days)
    
    # Get user's tweets
    tweets = db.query(Tweet).filter(
        and_(
            Tweet.author_username == username,
            Tweet.created_at >= cutoff_time
        )
    ).order_by(desc(Tweet.created_at)).all()
    
    if not tweets:
        return {
            "username": username,
            "error": "No tweets found for this user in the specified period"
        }
    
    # Tag frequency over time
    tag_timeline = defaultdict(lambda: defaultdict(int))
    
    for tweet in tweets:
        if tweet.created_at:
            week = tweet.created_at.isocalendar()[1]  # Week number
            tags = db.query(Tag).filter(Tag.tweet_id == tweet.id).all()
            for tag in tags:
                tag_timeline[tag.tag][f"week_{week}"] += 1
    
    # Calculate tag velocity (growth/decline)
    recent_cutoff = now - timedelta(days=7)
    older_cutoff = now - timedelta(days=14)
    
    recent_tags = db.query(
        Tag.tag,
        func.count(Tag.id).label("count")
    ).join(Tweet).filter(
        and_(
            Tweet.author_username == username,
            Tweet.created_at >= recent_cutoff
        )
    ).group_by(Tag.tag).all()
    
    older_tags = db.query(
        Tag.tag,
        func.count(Tag.id).label("count")
    ).join(Tweet).filter(
        and_(
            Tweet.author_username == username,
            Tweet.created_at >= older_cutoff,
            Tweet.created_at < recent_cutoff
        )
    ).group_by(Tag.tag).all()
    
    older_dict = {tag: count for tag, count in older_tags}
    
    tag_velocity = []
    for tag, recent_count in recent_tags:
        older_count = older_dict.get(tag, 0)
        if older_count > 0:
            change = ((recent_count - older_count) / older_count) * 100
            tag_velocity.append({
                "tag": tag,
                "recent_count": recent_count,
                "older_count": older_count,
                "change_percent": round(change, 1),
                "trend": "up" if change > 0 else "down"
            })
        else:
            tag_velocity.append({
                "tag": tag,
                "recent_count": recent_count,
                "older_count": 0,
                "change_percent": 100,
                "trend": "new"
            })
    
    # Sort by absolute change
    tag_velocity.sort(key=lambda x: abs(x["change_percent"]), reverse=True)
    
    # Engagement metrics
    total_likes = sum(t.like_count or 0 for t in tweets)
    total_retweets = sum(t.retweet_count or 0 for t in tweets)
    avg_likes = total_likes / len(tweets) if tweets else 0
    avg_retweets = total_retweets / len(tweets) if tweets else 0
    
    # Most engaged tweets
    top_tweets = sorted(tweets, key=lambda t: (t.like_count or 0) + (t.retweet_count or 0), reverse=True)[:5]
    
    return {
        "username": username,
        "period_days": days,
        "total_tweets": len(tweets),
        "avg_tweets_per_day": len(tweets) / days,
        "tag_velocity": tag_velocity[:20],
        "tag_timeline": dict(tag_timeline),
        "engagement": {
            "total_likes": total_likes,
            "total_retweets": total_retweets,
            "avg_likes": round(avg_likes, 1),
            "avg_retweets": round(avg_retweets, 1)
        },
        "top_tweets": [
            {
                "id": t.id,
                "text": t.text[:280],
                "likes": t.like_count or 0,
                "retweets": t.retweet_count or 0,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in top_tweets
        ],
        "latest_activity": tweets[0].created_at.isoformat() if tweets and tweets[0].created_at else None
    }


@router.get("/compare-users")
def compare_user_trends(
    users: str = Query(..., description="Comma-separated usernames"),
    days: int = Query(7, description="Days to analyze"),
    db: Session = Depends(get_db)
):
    """Compare trends between multiple users"""
    
    usernames = [u.strip() for u in users.split(",")]
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(days=days)
    
    comparison = {}
    
    for username in usernames:
        # Get user metrics
        tweet_count = db.query(Tweet).filter(
            and_(
                Tweet.author_username == username,
                Tweet.created_at >= cutoff_time
            )
        ).count()
        
        # Get top tags
        top_tags = db.query(
            Tag.tag,
            func.count(Tag.id).label("count")
        ).join(Tweet).filter(
            and_(
                Tweet.author_username == username,
                Tweet.created_at >= cutoff_time
            )
        ).group_by(Tag.tag).order_by(
            desc("count")
        ).limit(5).all()
        
        comparison[username] = {
            "tweet_count": tweet_count,
            "avg_per_day": round(tweet_count / days, 1),
            "top_tags": [{"tag": tag, "count": count} for tag, count in top_tags]
        }
    
    # Find common tags
    all_tags = defaultdict(list)
    for username, data in comparison.items():
        for tag_data in data["top_tags"]:
            all_tags[tag_data["tag"]].append(username)
    
    common_tags = {tag: users for tag, users in all_tags.items() if len(users) > 1}
    
    return {
        "period_days": days,
        "users": comparison,
        "common_tags": common_tags,
        "most_active": max(comparison.items(), key=lambda x: x[1]["tweet_count"])[0] if comparison else None
    }