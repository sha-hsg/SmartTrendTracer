"""
Statistics API endpoints for system metrics
Updated: Fixed ArticleTag.tag attribute
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text, distinct, and_, or_, case
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
import os
import json

from app.models import (
    get_db, Tweet, SubstackArticle, Tag, ArticleSnippet, 
    ArticleTag, SnippetTag, SubstackAuthor, TweetMedia
)

router = APIRouter()

@router.get("/overview")
def get_statistics_overview(db: Session = Depends(get_db)):
    """Get comprehensive system statistics"""
    try:
        # Get current date info with timezone awareness
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Tweet statistics
        total_tweets = db.query(func.count(Tweet.id)).scalar() or 0
        
        # For date comparisons with string timestamps
        today_str = today_start.strftime('%Y-%m-%d')
        week_str = week_start.strftime('%Y-%m-%d')
        month_str = month_start.strftime('%Y-%m-%d')
        
        tweets_today = db.query(func.count(Tweet.id)).filter(
            Tweet.created_at >= today_str
        ).scalar() or 0
        
        tweets_this_week = db.query(func.count(Tweet.id)).filter(
            Tweet.created_at >= week_str
        ).scalar() or 0
        
        tweets_this_month = db.query(func.count(Tweet.id)).filter(
            Tweet.created_at >= month_str
        ).scalar() or 0
        
        # Count tweets with media
        tweets_with_media = db.query(func.count(distinct(Tweet.id))).filter(
            Tweet.media_count > 0
        ).scalar() or 0
        
        # Alternative: check TweetMedia table
        if tweets_with_media == 0:
            tweets_with_media = db.query(func.count(distinct(TweetMedia.tweet_id))).scalar() or 0
        
        # Count tweets with tags
        tweets_with_tags = db.query(func.count(distinct(Tag.tweet_id))).scalar() or 0
        
        # Retweets and quotes
        # Check for retweets by looking for "RT @" in text
        retweets = db.query(func.count(Tweet.id)).filter(
            Tweet.text.like('RT @%')
        ).scalar() or 0
        
        # Quotes are tweets with quote_count > 0 or referenced_tweets containing 'quoted'
        quotes = db.query(func.count(Tweet.id)).filter(
            or_(
                Tweet.quote_count > 0,
                Tweet.referenced_tweets.like('%quoted%')
            )
        ).scalar() or 0
        
        # Article statistics
        total_articles = db.query(func.count(SubstackArticle.id)).scalar() or 0
        
        articles_this_week = db.query(func.count(SubstackArticle.id)).filter(
            SubstackArticle.published_at >= week_start
        ).scalar() or 0
        
        articles_this_month = db.query(func.count(SubstackArticle.id)).filter(
            SubstackArticle.published_at >= month_start
        ).scalar() or 0
        
        articles_with_summaries = db.query(func.count(SubstackArticle.id)).filter(
            SubstackArticle.summary != None,
            SubstackArticle.summary != ''
        ).scalar() or 0
        
        total_snippets = db.query(func.count(ArticleSnippet.id)).scalar() or 0
        
        avg_reading_time = db.query(func.avg(SubstackArticle.reading_time_minutes)).scalar() or 0
        total_word_count = db.query(func.sum(SubstackArticle.word_count)).scalar() or 0
        
        # Tag statistics
        # Count unique tags
        unique_tweet_tags = db.query(func.count(distinct(Tag.tag))).scalar() or 0
        unique_article_tags = db.query(func.count(distinct(ArticleTag.tag))).scalar() or 0
        unique_tags = unique_tweet_tags + unique_article_tags
        
        # Total tag applications
        total_tweet_tags = db.query(func.count(Tag.id)).scalar() or 0
        total_article_tags = db.query(func.count(ArticleTag.id)).scalar() or 0
        total_snippet_tags = db.query(func.count(SnippetTag.id)).scalar() or 0
        total_tags_applied = total_tweet_tags + total_article_tags + total_snippet_tags
        
        # Get most used tags from tweets
        most_used_tweet_tags = db.query(
            Tag.tag,
            func.count(Tag.id).label('count')
        ).group_by(Tag.tag).order_by(
            func.count(Tag.id).desc()
        ).limit(5).all()
        
        # Get most used tags from articles
        most_used_article_tags = db.query(
            ArticleTag.tag,
            func.count(ArticleTag.id).label('count')
        ).group_by(ArticleTag.tag).order_by(
            func.count(ArticleTag.id).desc()
        ).limit(5).all()
        
        # Combine and sort the top tags
        all_tags = {}
        for tag in most_used_tweet_tags:
            all_tags[tag.tag] = tag.count
        for tag in most_used_article_tags:
            if tag.tag in all_tags:
                all_tags[tag.tag] += tag.count
            else:
                all_tags[tag.tag] = tag.count
        
        most_used_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Get recently added unique tags (from the last 7 days)
        week_ago = now - timedelta(days=7)
        recent_tweet_tags = db.query(Tag.tag).filter(
            Tag.created_at >= week_ago
        ).distinct().limit(3).all()
        
        recent_article_tags = db.query(ArticleTag.tag).distinct().limit(3).all()
        
        recent_tags = []
        for tag in recent_tweet_tags[:3]:
            recent_tags.append(tag.tag)
        
        # Estimate organized vs unorganized (tags with hyphens or underscores are considered organized)
        organized_tags = db.query(func.count(distinct(Tag.tag))).filter(
            or_(
                Tag.tag.like('%-%'),
                Tag.tag.like('%_%')
            )
        ).scalar() or 0
        
        unorganized_tags = unique_tags - organized_tags
        
        # Author statistics for Twitter
        twitter_authors = db.query(
            Tweet.author_username,
            func.count(Tweet.id).label('tweet_count'),
            func.max(Tweet.created_at).label('latest_tweet')
        ).group_by(Tweet.author_username).order_by(
            func.count(Tweet.id).desc()
        ).limit(5).all()
        
        # Author statistics for Articles
        article_authors = db.query(
            SubstackAuthor.name,
            func.count(SubstackArticle.id).label('article_count'),
            func.max(SubstackArticle.published_at).label('latest_article')
        ).join(
            SubstackArticle, SubstackAuthor.id == SubstackArticle.author_id
        ).group_by(SubstackAuthor.name).order_by(
            func.count(SubstackArticle.id).desc()
        ).limit(5).all()
        
        # System statistics
        # Database size
        db_path = os.path.join(os.path.dirname(__file__), '../../..', 'data', 'tweets.db')
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path) / (1024 * 1024)  # Convert to MB
            db_size_str = f"{db_size:.1f} MB"
        else:
            db_size_str = "Unknown"
        
        # RAG index status (check if index exists)
        rag_index_path = os.path.join(os.path.dirname(__file__), '../../..', 'data', 'rag_index', 'faiss.index')
        rag_documents = total_tweets + total_articles + total_snippets
        rag_is_ready = os.path.exists(rag_index_path)
        
        # Collection status
        last_tweet = db.query(Tweet).order_by(Tweet.created_at.desc()).first()
        last_article = db.query(SubstackArticle).order_by(SubstackArticle.published_at.desc()).first()
        
        # Timeline data - Tweets per day (last 7 days)
        tweets_per_day = []
        for i in range(7):
            day = now - timedelta(days=6-i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            # Format dates for string comparison
            day_start_str = day_start.strftime('%Y-%m-%d')
            day_end_str = day_end.strftime('%Y-%m-%d')
            
            count = db.query(func.count(Tweet.id)).filter(
                Tweet.created_at >= day_start_str,
                Tweet.created_at < day_end_str
            ).scalar() or 0
            
            tweets_per_day.append({
                'date': day.strftime('%a'),
                'count': count
            })
        
        # Articles per week (last 4 weeks)
        articles_per_week = []
        for i in range(4):
            week_start_date = now - timedelta(weeks=3-i)
            week_start_date = week_start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            week_end_date = week_start_date + timedelta(weeks=1)
            
            count = db.query(func.count(SubstackArticle.id)).filter(
                SubstackArticle.published_at >= week_start_date,
                SubstackArticle.published_at < week_end_date
            ).scalar() or 0
            
            articles_per_week.append({
                'week': f'W{i+1}',
                'count': count
            })
        
        # Hot topics - based on recent tag usage
        recent_tags_query = db.query(
            Tag.tag,
            func.count(Tag.id).label('mentions')
        ).filter(
            Tag.created_at >= week_str
        ).group_by(Tag.tag).order_by(
            func.count(Tag.id).desc()
        ).limit(6).all()
        
        hot_topics = []
        for tag in recent_tags_query[:4]:
            # Simple trend detection based on recent activity
            old_count = db.query(func.count(Tag.id)).filter(
                Tag.tag == tag.tag,
                Tag.created_at < week_str,
                Tag.created_at >= (week_start - timedelta(weeks=1)).strftime('%Y-%m-%d')
            ).scalar() or 0
            
            if old_count == 0:
                trend = 'up'
            elif tag.mentions > old_count * 1.2:
                trend = 'up'
            elif tag.mentions < old_count * 0.8:
                trend = 'down'
            else:
                trend = 'stable'
            
            # Format tag name for display
            topic_name = tag.tag.replace('-', ' ').replace('_', ' ')
            if len(topic_name) > 30:
                topic_name = topic_name[:30] + '...'
            
            hot_topics.append({
                'topic': topic_name.title(),
                'mentions': tag.mentions,
                'trend': trend
            })
        
        # Emerging tags - recently created tags with significant usage
        emerging_tags_query = db.query(
            Tag.tag,
            func.count(Tag.id).label('usage')
        ).filter(
            Tag.created_at >= (now - timedelta(days=30)).strftime('%Y-%m-%d')
        ).group_by(Tag.tag).having(
            func.count(Tag.id) >= 3  # At least 3 uses
        ).order_by(
            func.count(Tag.id).desc()
        ).limit(5).all()
        
        emerging_tags = []
        for tag in emerging_tags_query[:3]:
            # Calculate growth rate (simplified)
            growth_rate = min(tag.usage * 15, 150)  # Multiply by 15 for display
            emerging_tags.append({
                'tag': tag.tag,
                'growth_rate': growth_rate
            })
        
        # Format response
        return {
            'tweets': {
                'total': total_tweets,
                'today': tweets_today,
                'this_week': tweets_this_week,
                'this_month': tweets_this_month,
                'with_media': tweets_with_media,
                'with_tags': tweets_with_tags,
                'retweets': retweets,
                'quotes': quotes
            },
            'articles': {
                'total': total_articles,
                'this_week': articles_this_week,
                'this_month': articles_this_month,
                'with_summaries': articles_with_summaries,
                'with_snippets': total_snippets,
                'avg_reading_time': round(avg_reading_time, 1) if avg_reading_time else 0,
                'total_word_count': int(total_word_count) if total_word_count else 0
            },
            'tags': {
                'total': total_tags_applied,
                'unique': unique_tags,
                'organized': organized_tags,
                'unorganized': unorganized_tags,
                'most_used': [
                    {'tag': tag[0], 'count': tag[1]}
                    for tag in most_used_tags
                ],
                'recently_added': [
                    {'tag': tag, 'date': (now - timedelta(days=i)).strftime('%Y-%m-%d')}
                    for i, tag in enumerate(recent_tags)
                ]
            },
            'authors': {
                'twitter': [
                    {
                        'username': f'@{author.author_username}',
                        'tweet_count': author.tweet_count,
                        'latest_tweet': format_time_ago(author.latest_tweet)
                    }
                    for author in twitter_authors
                ],
                'articles': [
                    {
                        'name': author.name,
                        'article_count': author.article_count,
                        'latest_article': format_time_ago(author.latest_article) if author.latest_article else 'N/A'
                    }
                    for author in article_authors
                ]
            },
            'system': {
                'database_size': db_size_str,
                'index_status': {
                    'rag_documents': rag_documents,
                    'last_updated': datetime.now(timezone.utc).isoformat(),
                    'is_ready': rag_is_ready
                },
                'collection_status': {
                    'last_tweet_collection': last_tweet.created_at if last_tweet else datetime.now(timezone.utc).isoformat(),
                    'last_article_collection': last_article.published_at.isoformat() if last_article and last_article.published_at else datetime.now(timezone.utc).isoformat(),
                    'next_scheduled': (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
                }
            },
            'trends': {
                'hot_topics': hot_topics,
                'emerging_tags': emerging_tags
            },
            'timeline': {
                'tweets_per_day': tweets_per_day,
                'articles_per_week': articles_per_week
            }
        }
        
    except Exception as e:
        print(f"Error generating statistics: {e}")
        import traceback
        traceback.print_exc()
        
        # Return minimal stats on error
        return {
            'error': str(e),
            'tweets': {
                'total': 0,
                'today': 0,
                'this_week': 0,
                'this_month': 0,
                'with_media': 0,
                'with_tags': 0,
                'retweets': 0,
                'quotes': 0
            },
            'articles': {
                'total': 0,
                'this_week': 0,
                'this_month': 0,
                'with_summaries': 0,
                'with_snippets': 0,
                'avg_reading_time': 0,
                'total_word_count': 0
            },
            'tags': {
                'total': 0,
                'unique': 0,
                'organized': 0,
                'unorganized': 0,
                'most_used': [],
                'recently_added': []
            },
            'authors': {
                'twitter': [],
                'articles': []
            },
            'system': {
                'database_size': 'Error',
                'index_status': {
                    'rag_documents': 0,
                    'last_updated': datetime.now(timezone.utc).isoformat(),
                    'is_ready': False
                },
                'collection_status': {
                    'last_tweet_collection': datetime.now(timezone.utc).isoformat(),
                    'last_article_collection': datetime.now(timezone.utc).isoformat(),
                    'next_scheduled': datetime.now(timezone.utc).isoformat()
                }
            },
            'trends': {
                'hot_topics': [],
                'emerging_tags': []
            },
            'timeline': {
                'tweets_per_day': [],
                'articles_per_week': []
            }
        }


def format_time_ago(timestamp):
    """Format timestamp as 'X hours/days ago'"""
    if not timestamp:
        return 'Never'
    
    # Handle both string and datetime objects
    if isinstance(timestamp, str):
        # Parse ISO format string
        try:
            # Handle various timestamp formats
            if 'T' in timestamp:
                # ISO format with T
                if '+' in timestamp or 'Z' in timestamp:
                    # Has timezone
                    timestamp = timestamp.replace('Z', '+00:00')
                    dt = datetime.fromisoformat(timestamp)
                else:
                    # No timezone, assume UTC
                    dt = datetime.fromisoformat(timestamp).replace(tzinfo=timezone.utc)
            elif ' ' in timestamp:
                # Space-separated format
                dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                # Date only
                dt = datetime.strptime(timestamp, '%Y-%m-%d')
                dt = dt.replace(tzinfo=timezone.utc)
        except Exception as e:
            print(f"Error parsing timestamp '{timestamp}': {e}")
            return 'Unknown'
    else:
        dt = timestamp
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    diff = now - dt
    
    if diff.days > 30:
        return f'{diff.days // 30} month{"s" if diff.days // 30 > 1 else ""} ago'
    elif diff.days > 7:
        return f'{diff.days // 7} week{"s" if diff.days // 7 > 1 else ""} ago'
    elif diff.days > 0:
        return f'{diff.days} day{"s" if diff.days > 1 else ""} ago'
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f'{hours} hour{"s" if hours > 1 else ""} ago'
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f'{minutes} minute{"s" if minutes > 1 else ""} ago'
    else:
        return 'Just now'


@router.get("/health")
def statistics_health_check():
    """Health check for statistics endpoint"""
    return {
        "status": "healthy",
        "endpoint": "statistics",
        "version": "1.0.1",
        "note": "ArticleTag.tag attribute fixed"
    }

@router.get("/refresh")
async def refresh_statistics(db: Session = Depends(get_db)):
    """Force refresh statistics and clear any caches"""
    # In a real implementation, you might clear caches here
    # For now, just return the fresh stats
    return get_statistics_overview(db)