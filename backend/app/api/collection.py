"""
API endpoints for managing tweet collection
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.collectors.twitter_collector import TwitterCollector

router = APIRouter()

@router.post("/collect")
async def collect_tweets_now(
    background_tasks: BackgroundTasks,
    max_results: int = 50,
):
    """Manually trigger tweet collection"""
    
    def collect_in_background():
        try:
            collector = TwitterCollector(db_session=db)
            new_tweets = collector.collect_tweets(max_results=max_results)
            
            if new_tweets == 0:
                # Try historical if no new tweets
                collector.collect_historical_tweets(days=1)
                
        except Exception as e:
            print(f"Background collection error: {e}")
    
    # Add to background tasks
    background_tasks.add_task(collect_in_background)
    
    return {
        "message": "Collection started in background",
        "max_results": max_results
    }

@router.post("/collect/historical")
def collect_historical_tweets(
    days: int = 7,
):
    """Collect historical tweets from the past N days"""
    if days < 1 or days > 7:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 7")
    
    try:
        collector = TwitterCollector(db_session=db)
        count = collector.collect_historical_tweets(days=days)
        
        return {
            "message": f"Collected {count} historical tweets",
            "days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
def get_collection_status():
    """Get collection status and statistics"""
    
    # Get total tweets
    total_tweets = db.query(func.count(Tweet.id)).scalar()
    
    # Get tweets from last 24 hours
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    recent_tweets = db.query(func.count(Tweet.id)).filter(
        Tweet.created_at > yesterday
    ).scalar()
    
    # Get latest tweet time
    latest_tweet = db.query(Tweet).order_by(Tweet.created_at.desc()).first()
    
    # Get stats per account
    account_stats = db.query(
        Tweet.author_username,
        func.count(Tweet.id).label('count'),
        func.max(Tweet.created_at).label('latest'),
        func.min(Tweet.created_at).label('oldest')
    ).group_by(Tweet.author_username).all()
    
    accounts = []
    for stat in account_stats:
        accounts.append({
            "username": stat.author_username,
            "tweet_count": stat.count,
            "latest_tweet": stat.latest.isoformat() if stat.latest else None,
            "oldest_tweet": stat.oldest.isoformat() if stat.oldest else None
        })
    
    return {
        "total_tweets": total_tweets,
        "tweets_last_24h": recent_tweets,
        "latest_tweet": latest_tweet.created_at.isoformat() if latest_tweet else None,
        "accounts": accounts,
        "collection_enabled": True,
        "collection_interval": "30 minutes"
    }

@router.get("/gaps")
def find_collection_gaps(
    hours: int = 24,
):
    """Find gaps in tweet collection"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    gaps = []
    for username in ["OpenAI", "emollick", "stanfordnlp", "AnthropicAI", 
                     "GoogleDeepMind", "huggingface", "sama"]:
        
        latest = db.query(Tweet).filter(
            Tweet.author_username == username
        ).order_by(Tweet.created_at.desc()).first()
        
        if not latest:
            gaps.append({
                "username": username,
                "status": "no_tweets",
                "latest": None,
                "hours_since": None
            })
        else:
            hours_since = (datetime.now(timezone.utc) - latest.created_at).total_seconds() / 3600
            gaps.append({
                "username": username,
                "status": "ok" if hours_since < 24 else "stale",
                "latest": latest.created_at.isoformat(),
                "hours_since": round(hours_since, 1)
            })
    
    return {
        "gaps": gaps,
        "checked_at": datetime.now(timezone.utc).isoformat()
    }