"""
Statistics API using MongoDB concepts instead of SQLite tags
Replaces statistics.py for complete concept conversion
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text, distinct, and_, or_
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
import os
import json
from pymongo import MongoClient

from app.models import (
    get_db, Tweet, SubstackArticle, ArticleSnippet, 
    SubstackAuthor, TweetMedia
)
from app.models.papers import Paper
from app.services.concept_only_tag_service import ConceptOnlyTagService

router = APIRouter()

# Initialize MongoDB and concept service
mongo_client = MongoClient('mongodb://localhost:27017/')
db_mongo = mongo_client.smarttrendtracer
concept_service = ConceptOnlyTagService()

@router.get("/overview")
def get_statistics_overview(db: Session = Depends(get_db)):
    """Get comprehensive system statistics using MongoDB concepts"""
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
        
        # Count tweets with concepts from MongoDB
        tweets_with_concepts = db_mongo.tag_instances.count_documents({
            'content_type': 'tweet'
        })
        unique_tweet_ids = len(db_mongo.tag_instances.distinct('content_id', {
            'content_type': 'tweet'
        }))
        
        # Retweets and quotes
        retweets = db.query(func.count(Tweet.id)).filter(
            Tweet.text.like('RT @%')
        ).scalar() or 0
        
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
        
        # Paper statistics
        total_papers = db.query(func.count(Paper.id)).scalar() or 0
        
        # Papers with concepts from MongoDB
        papers_with_concepts = db_mongo.tag_instances.count_documents({
            'content_type': 'paper'
        })
        unique_paper_ids = len(db_mongo.tag_instances.distinct('content_id', {
            'content_type': 'paper'
        }))
        
        papers_this_week = db.query(func.count(Paper.id)).filter(
            Paper.created_at >= week_str
        ).scalar() or 0
        
        papers_this_month = db.query(func.count(Paper.id)).filter(
            Paper.created_at >= month_str
        ).scalar() or 0
        
        # Concept statistics from MongoDB
        all_concepts = concept_service.get_all_concepts_with_counts()
        unique_concepts = len(all_concepts)
        
        # Total concept applications (tag instances)
        total_tag_instances = db_mongo.tag_instances.count_documents({})
        tweet_instances = db_mongo.tag_instances.count_documents({'content_type': 'tweet'})
        article_instances = db_mongo.tag_instances.count_documents({'content_type': 'article'})
        paper_instances = db_mongo.tag_instances.count_documents({'content_type': 'paper'})
        
        # Get most used concepts
        concept_counts = {}
        for concept in all_concepts:
            concept_counts[concept['slug']] = concept['count']
        
        most_used_concepts = sorted(
            concept_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        most_used_tags = []
        for slug, count in most_used_concepts:
            concept = db_mongo.tag_concepts_v2.find_one({'slug': slug})
            if concept:
                # Find which content types use this concept
                sources = []
                if db_mongo.tag_instances.count_documents({'concept_slug': slug, 'content_type': 'tweet'}) > 0:
                    sources.append('tweets')
                if db_mongo.tag_instances.count_documents({'concept_slug': slug, 'content_type': 'article'}) > 0:
                    sources.append('articles')
                if db_mongo.tag_instances.count_documents({'concept_slug': slug, 'content_type': 'paper'}) > 0:
                    sources.append('papers')
                
                most_used_tags.append((
                    concept.get('display_name', slug),
                    {'count': count, 'sources': sources}
                ))
        
        # Get recently added concepts
        recent_concepts = list(db_mongo.tag_concepts_v2.find(
            {}, 
            {'slug': 1, 'display_name': 1, 'created_at': 1}
        ).sort('created_at', -1).limit(3))
        
        recent_tags = [
            c.get('display_name', c['slug']) 
            for c in recent_concepts
        ]
        
        # Estimate organized vs unorganized
        # Concepts with parents are organized, orphans are unorganized
        organized_concepts = db_mongo.tag_concepts_v2.count_documents({
            'parents': {'$exists': True, '$ne': []}
        })
        unorganized_concepts = db_mongo.tag_concepts_v2.count_documents({
            '$or': [
                {'parents': {'$exists': False}},
                {'parents': []}
            ]
        })
        
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
        
        # RAG index status
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        rag_index_path = os.path.join(base_dir, 'data', 'rag_index_concepts', 'faiss.index')
        rag_documents = total_tweets + total_articles + total_snippets + total_papers
        rag_is_ready = os.path.exists(rag_index_path)
        
        # Get actual RAG index info if available
        rag_info_path = os.path.join(base_dir, 'data', 'rag_index_concepts', 'index_info.json')
        rag_last_updated = None
        if os.path.exists(rag_info_path):
            try:
                with open(rag_info_path, 'r') as f:
                    rag_info = json.load(f)
                    rag_last_updated = rag_info.get('last_updated')
                    if 'total_documents' in rag_info:
                        rag_documents = rag_info['total_documents']
            except Exception:
                pass
        
        # Collection status
        last_tweet = db.query(Tweet).order_by(Tweet.created_at.desc()).first()
        last_article = db.query(SubstackArticle).order_by(SubstackArticle.published_at.desc()).first()
        
        # Timeline data - Tweets per day (last 7 days)
        tweets_per_day = []
        for i in range(7):
            day = now - timedelta(days=6-i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
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
        
        # Hot topics based on recent concept usage
        # Get concepts used in the last week
        week_ago = now - timedelta(days=7)
        recent_instances = list(db_mongo.tag_instances.find({
            'created_at': {'$gte': week_ago}
        }))
        
        recent_concept_counts = {}
        for instance in recent_instances:
            slug = instance.get('concept_slug')
            if slug:
                recent_concept_counts[slug] = recent_concept_counts.get(slug, 0) + 1
        
        hot_topics = []
        for slug, count in sorted(recent_concept_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            concept = db_mongo.tag_concepts_v2.find_one({'slug': slug})
            if concept:
                hot_topics.append({
                    'topic': concept.get('display_name', slug),
                    'mentions': count,
                    'entity_type': concept.get('entity_type', 'concept')
                })
        
        return {
            'tweets': {
                'total': total_tweets,
                'today': tweets_today,
                'this_week': tweets_this_week,
                'this_month': tweets_this_month,
                'with_media': tweets_with_media,
                'with_concepts': unique_tweet_ids,  # Unique tweets with concepts
                'retweets': retweets,
                'quotes': quotes,
                'per_day': tweets_per_day
            },
            'articles': {
                'total': total_articles,
                'this_week': articles_this_week,
                'this_month': articles_this_month,
                'with_summaries': articles_with_summaries,
                'snippets': total_snippets,
                'avg_reading_time': round(avg_reading_time, 1) if avg_reading_time else 0,
                'total_word_count': total_word_count or 0,
                'per_week': articles_per_week
            },
            'papers': {
                'total': total_papers,
                'with_concepts': unique_paper_ids,  # Unique papers with concepts
                'this_week': papers_this_week,
                'this_month': papers_this_month
            },
            'concepts': {
                'unique': unique_concepts,
                'total_instances': total_tag_instances,
                'tweet_instances': tweet_instances,
                'article_instances': article_instances,
                'paper_instances': paper_instances,
                'most_used': most_used_tags[:5],
                'recent': recent_tags,
                'organized': organized_concepts,
                'unorganized': unorganized_concepts
            },
            'authors': {
                'twitter': [
                    {
                        'username': author.author_username,
                        'tweet_count': author.tweet_count,
                        'latest': author.latest_tweet
                    } for author in twitter_authors
                ],
                'articles': [
                    {
                        'name': author.name,
                        'article_count': author.article_count,
                        'latest': author.latest_article.isoformat() if author.latest_article else None
                    } for author in article_authors
                ]
            },
            'system': {
                'database_size': db_size_str,
                'rag_index': {
                    'is_ready': rag_is_ready,
                    'documents': rag_documents,
                    'last_updated': rag_last_updated,
                    'uses_concepts': True  # New concept-based RAG
                },
                'mongodb': {
                    'concepts': unique_concepts,
                    'aliases': db_mongo.tag_aliases_v2.count_documents({}),
                    'instances': total_tag_instances
                }
            },
            'collection': {
                'last_tweet': last_tweet.created_at if last_tweet else None,
                'last_article': last_article.published_at.isoformat() if last_article and last_article.published_at else None
            },
            'hot_topics': hot_topics
        }
    except Exception as e:
        import traceback
        print(f"Error in statistics overview: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/growth")
def get_growth_statistics(db: Session = Depends(get_db)):
    """Get growth statistics for concepts over time"""
    try:
        now = datetime.now(timezone.utc)
        
        # Daily growth for the last 30 days
        daily_growth = []
        for i in range(30):
            day = now - timedelta(days=29-i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            # Count new concept instances on this day
            new_instances = db_mongo.tag_instances.count_documents({
                'created_at': {
                    '$gte': day_start,
                    '$lt': day_end
                }
            })
            
            daily_growth.append({
                'date': day.strftime('%Y-%m-%d'),
                'new_concepts': new_instances
            })
        
        # Top growing concepts (comparing last week to previous week)
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        
        # Get concept counts for last week
        last_week_instances = list(db_mongo.tag_instances.find({
            'created_at': {
                '$gte': week_ago,
                '$lt': now
            }
        }))
        
        # Get concept counts for previous week
        prev_week_instances = list(db_mongo.tag_instances.find({
            'created_at': {
                '$gte': two_weeks_ago,
                '$lt': week_ago
            }
        }))
        
        # Count by concept
        last_week_counts = {}
        for instance in last_week_instances:
            slug = instance.get('concept_slug')
            if slug:
                last_week_counts[slug] = last_week_counts.get(slug, 0) + 1
        
        prev_week_counts = {}
        for instance in prev_week_instances:
            slug = instance.get('concept_slug')
            if slug:
                prev_week_counts[slug] = prev_week_counts.get(slug, 0) + 1
        
        # Calculate growth
        concept_growth = []
        for slug, last_count in last_week_counts.items():
            prev_count = prev_week_counts.get(slug, 0)
            if prev_count > 0:
                growth_rate = ((last_count - prev_count) / prev_count) * 100
            else:
                growth_rate = 100 if last_count > 0 else 0
            
            if growth_rate > 0:
                concept = db_mongo.tag_concepts_v2.find_one({'slug': slug})
                if concept:
                    concept_growth.append({
                        'concept': concept.get('display_name', slug),
                        'last_week': last_count,
                        'prev_week': prev_count,
                        'growth_rate': round(growth_rate, 1)
                    })
        
        # Sort by growth rate
        concept_growth.sort(key=lambda x: x['growth_rate'], reverse=True)
        
        return {
            'daily_growth': daily_growth,
            'top_growing_concepts': concept_growth[:10]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entity-types")
def get_entity_type_statistics():
    """Get statistics grouped by entity types"""
    try:
        # Get all entity types
        entity_types = db_mongo.tag_concepts_v2.distinct('entity_type')
        
        entity_stats = {}
        for entity_type in entity_types:
            if entity_type:  # Skip None values
                # Count concepts of this type
                concept_count = db_mongo.tag_concepts_v2.count_documents({'entity_type': entity_type})
                
                # Get concepts of this type
                concepts = list(db_mongo.tag_concepts_v2.find({'entity_type': entity_type}))
                concept_slugs = [c['slug'] for c in concepts]
                
                # Count instances
                instance_count = db_mongo.tag_instances.count_documents({
                    'concept_slug': {'$in': concept_slugs}
                })
                
                entity_stats[entity_type] = {
                    'concept_count': concept_count,
                    'instance_count': instance_count,
                    'top_concepts': []
                }
                
                # Get top concepts for this entity type
                concept_counts = {}
                for slug in concept_slugs:
                    count = db_mongo.tag_instances.count_documents({'concept_slug': slug})
                    if count > 0:
                        concept_counts[slug] = count
                
                # Get top 5
                for slug, count in sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                    concept = db_mongo.tag_concepts_v2.find_one({'slug': slug})
                    if concept:
                        entity_stats[entity_type]['top_concepts'].append({
                            'name': concept.get('display_name', slug),
                            'count': count
                        })
        
        return entity_stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))