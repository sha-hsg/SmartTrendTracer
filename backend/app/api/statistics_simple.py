"""
Simple statistics endpoint that works immediately
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from datetime import datetime, timezone, timedelta
import os

from app.models import get_db, Tweet, SubstackArticle, Tag, ArticleTag

router = APIRouter()

@router.get("/quick")
def get_quick_stats(db: Session = Depends(get_db)):
    """Get quick statistics overview"""
    try:
        # Basic counts
        total_tweets = db.query(func.count(Tweet.id)).scalar() or 0
        total_articles = db.query(func.count(SubstackArticle.id)).scalar() or 0
        total_tags = db.query(func.count(distinct(Tag.tag))).scalar() or 0
        
        # Recent activity
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_str = today_start.strftime('%Y-%m-%d')
        
        tweets_today = db.query(func.count(Tweet.id)).filter(
            Tweet.created_at >= today_str
        ).scalar() or 0
        
        return {
            "status": "operational",
            "timestamp": now.isoformat(),
            "metrics": {
                "tweets": {
                    "total": total_tweets,
                    "today": tweets_today
                },
                "articles": {
                    "total": total_articles
                },
                "tags": {
                    "unique": total_tags
                }
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "metrics": {
                "tweets": {"total": 0, "today": 0},
                "articles": {"total": 0},
                "tags": {"unique": 0}
            }
        }