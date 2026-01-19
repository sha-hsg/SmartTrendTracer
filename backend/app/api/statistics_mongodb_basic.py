"""
Complete MongoDB-based statistics API.
All data operations use MongoDB - no SQLite dependencies.
"""

from fastapi import APIRouter, Query
from pymongo import ASCENDING, DESCENDING
from app.database.mongodb import get_database
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

from app.services.concept_only_tag_service import ConceptOnlyTagService

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
db = get_database()

# Initialize concept service
concept_service = ConceptOnlyTagService()

@router.get("/overview")
def get_overview_statistics():
    """Get overall system statistics from MongoDB"""
    
    # Count documents
    total_tweets = db.tweets.count_documents({})
    total_papers = db.papers.count_documents({})
    total_articles = db.articles.count_documents({})
    
    # Count unique authors
    unique_tweet_authors = len(db.tweets.distinct("author_username"))
    unique_article_authors = db.substack_authors.count_documents({})
    
    # Count paper authors
    paper_author_pipeline = [
        {'$unwind': '$authors'},
        {'$group': {'_id': '$authors.name'}},
        {'$count': 'total'}
    ]
    paper_author_result = list(db.papers.aggregate(paper_author_pipeline))
    unique_paper_authors = paper_author_result[0]['total'] if paper_author_result else 0
    
    # Count concepts
    total_concepts = db.tag_concepts_v2.count_documents({})
    
    # Count concept assignments
    total_assignments = db.tag_instances.count_documents({})
    
    # Get date ranges
    oldest_tweet = db.tweets.find_one({}, sort=[('created_at', ASCENDING)])
    newest_tweet = db.tweets.find_one({}, sort=[('created_at', DESCENDING)])
    
    oldest_paper = db.papers.find_one({}, sort=[('created_at', ASCENDING)])
    newest_paper = db.papers.find_one({}, sort=[('created_at', DESCENDING)])
    
    oldest_article = db.articles.find_one({}, sort=[('published_at', ASCENDING)])
    newest_article = db.articles.find_one({}, sort=[('published_at', DESCENDING)])
    
    return {
        "content": {
            "tweets": {
                "total": total_tweets,
                "authors": unique_tweet_authors,
                "date_range": {
                    "oldest": oldest_tweet['created_at'].isoformat() if oldest_tweet and oldest_tweet.get('created_at') else None,
                    "newest": newest_tweet['created_at'].isoformat() if newest_tweet and newest_tweet.get('created_at') else None
                }
            },
            "papers": {
                "total": total_papers,
                "authors": unique_paper_authors,
                "date_range": {
                    "oldest": oldest_paper['created_at'].isoformat() if oldest_paper and oldest_paper.get('created_at') else None,
                    "newest": newest_paper['created_at'].isoformat() if newest_paper and newest_paper.get('created_at') else None
                }
            },
            "articles": {
                "total": total_articles,
                "authors": unique_article_authors,
                "date_range": {
                    "oldest": oldest_article['published_at'].isoformat() if oldest_article and oldest_article.get('published_at') else None,
                    "newest": newest_article['published_at'].isoformat() if newest_article and newest_article.get('published_at') else None
                }
            }
        },
        "tagging": {
            "total_concepts": total_concepts,
            "total_assignments": total_assignments,
            "average_per_content": total_assignments / max(total_tweets + total_papers + total_articles, 1)
        },
        "database": "MongoDB"
    }

@router.get("/trends")
def get_trend_statistics(days: int = Query(7, ge=1, le=365)):
    """Get trend statistics over time from MongoDB"""
    
    # Calculate date threshold
    date_threshold = datetime.now() - timedelta(days=days)
    
    # Tweet trends
    tweet_pipeline = [
        {'$match': {'created_at': {'$gte': date_threshold}}},
        {'$group': {
            '_id': {
                '$dateToString': {
                    'format': '%Y-%m-%d',
                    'date': '$created_at'
                }
            },
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': 1}}
    ]
    tweet_trends = list(db.tweets.aggregate(tweet_pipeline))
    
    # Paper trends
    paper_pipeline = [
        {'$match': {'created_at': {'$gte': date_threshold}}},
        {'$group': {
            '_id': {
                '$dateToString': {
                    'format': '%Y-%m-%d',
                    'date': '$created_at'
                }
            },
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': 1}}
    ]
    paper_trends = list(db.papers.aggregate(paper_pipeline))
    
    # Article trends
    article_pipeline = [
        {'$match': {'published_at': {'$gte': date_threshold}}},
        {'$group': {
            '_id': {
                '$dateToString': {
                    'format': '%Y-%m-%d',
                    'date': '$published_at'
                }
            },
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': 1}}
    ]
    article_trends = list(db.articles.aggregate(article_pipeline))
    
    return {
        "period_days": days,
        "trends": {
            "tweets": [{'date': t['_id'], 'count': t['count']} for t in tweet_trends],
            "papers": [{'date': p['_id'], 'count': p['count']} for p in paper_trends],
            "articles": [{'date': a['_id'], 'count': a['count']} for a in article_trends]
        }
    }

@router.get("/top-concepts")
def get_top_concepts(
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    limit: int = Query(20, ge=1, le=100)
):
    """Get top concepts by usage from MongoDB"""
    
    # Get concepts with counts
    concepts = concept_service.get_all_concepts_with_counts(content_type=content_type)
    
    # Format and limit
    top_concepts = []
    for concept in concepts[:limit]:
        top_concepts.append({
            'concept_id': concept.get('concept_id'),
            'display_name': concept.get('display_name'),
            'slug': concept.get('slug'),
            'entity_type': concept.get('entity_type'),
            'count': concept.get('count', 0),
            'content_types': concept.get('content_types', [])
        })
    
    return {
        "content_type": content_type,
        "limit": limit,
        "top_concepts": top_concepts
    }

@router.get("/authors")
def get_author_statistics():
    """Get author statistics from MongoDB"""
    
    # Top tweet authors
    tweet_author_pipeline = [
        {'$group': {
            '_id': '$author_username',
            'tweet_count': {'$sum': 1},
            'total_likes': {'$sum': '$metrics.like_count'},
            'total_retweets': {'$sum': '$metrics.retweet_count'}
        }},
        {'$sort': {'tweet_count': -1}},
        {'$limit': 10}
    ]
    top_tweet_authors = list(db.tweets.aggregate(tweet_author_pipeline))
    
    # Top paper authors
    paper_author_pipeline = [
        {'$unwind': '$authors'},
        {'$group': {
            '_id': '$authors.name',
            'paper_count': {'$sum': 1},
            'affiliations': {'$addToSet': '$authors.affiliation'}
        }},
        {'$sort': {'paper_count': -1}},
        {'$limit': 10}
    ]
    top_paper_authors = list(db.papers.aggregate(paper_author_pipeline))
    
    # Article authors with stats
    article_authors = []
    for author in db.substack_authors.find():
        article_count = db.articles.count_documents({'author_id': author['_id']})
        if article_count > 0:
            article_authors.append({
                'name': author.get('name'),
                'subdomain': author.get('subdomain'),
                'article_count': article_count
            })
    
    article_authors.sort(key=lambda x: x['article_count'], reverse=True)
    
    return {
        "tweet_authors": [
            {
                'username': a['_id'],
                'tweet_count': a['tweet_count'],
                'total_likes': a['total_likes'],
                'total_retweets': a['total_retweets']
            }
            for a in top_tweet_authors
        ],
        "paper_authors": [
            {
                'name': a['_id'],
                'paper_count': a['paper_count'],
                'affiliations': [aff for aff in a['affiliations'] if aff]
            }
            for a in top_paper_authors
        ],
        "article_authors": article_authors[:10]
    }

@router.get("/media")
def get_media_statistics():
    """Get media usage statistics from MongoDB"""
    
    # Tweets with media
    tweets_with_media = db.tweets.count_documents({'media': {'$ne': []}})
    total_tweets = db.tweets.count_documents({})
    
    # Media type breakdown
    media_type_pipeline = [
        {'$unwind': '$media'},
        {'$group': {
            '_id': '$media.type',
            'count': {'$sum': 1}
        }}
    ]
    media_types = list(db.tweets.aggregate(media_type_pipeline))
    
    # Papers with PDFs
    papers_with_pdf = db.papers.count_documents({'pdf_path': {'$ne': None}})
    total_papers = db.papers.count_documents({})
    
    return {
        "tweets": {
            "total": total_tweets,
            "with_media": tweets_with_media,
            "percentage": (tweets_with_media / total_tweets * 100) if total_tweets > 0 else 0,
            "media_types": {
                mt['_id']: mt['count'] 
                for mt in media_types
            }
        },
        "papers": {
            "total": total_papers,
            "with_pdf": papers_with_pdf,
            "percentage": (papers_with_pdf / total_papers * 100) if total_papers > 0 else 0
        }
    }

@router.get("/database")
def get_database_statistics():
    """Get MongoDB database statistics"""
    
    # Get database stats
    db_stats = db.command("dbStats")
    
    # Get collection stats
    collections = {}
    for collection_name in db.list_collection_names():
        coll_stats = db.command("collStats", collection_name)
        collections[collection_name] = {
            "count": coll_stats.get("count", 0),
            "size": coll_stats.get("size", 0),
            "avgObjSize": coll_stats.get("avgObjSize", 0),
            "indexes": coll_stats.get("nindexes", 0)
        }
    
    return {
        "database": "MongoDB",
        "name": db_stats.get("db"),
        "collections": len(collections),
        "objects": db_stats.get("objects"),
        "dataSize": db_stats.get("dataSize"),
        "storageSize": db_stats.get("storageSize"),
        "indexes": db_stats.get("indexes"),
        "indexSize": db_stats.get("indexSize"),
        "collection_details": collections
    }
