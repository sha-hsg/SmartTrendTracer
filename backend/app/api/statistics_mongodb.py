"""
Full MongoDB-based statistics API with complete functionality.
Provides comprehensive statistics for all content types and analytics.
"""

from fastapi import APIRouter, Query, HTTPException
from pymongo import ASCENDING, DESCENDING
from app.database.mongodb import get_database
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import logging
import re

from app.services.concept_only_tag_service import ConceptOnlyTagService

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
db = get_database()
_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = timedelta(seconds=60)


def _cached(key: str, builder):
    now = datetime.utcnow()
    entry = _cache.get(key)
    if entry and entry["expires_at"] > now:
        return entry["value"]

    value = builder()
    _cache[key] = {"value": value, "expires_at": now + CACHE_TTL}
    return value

# Initialize concept service
concept_service = ConceptOnlyTagService()

@router.get("/overview")
def get_overview_statistics():
    """Get comprehensive system statistics from MongoDB"""
    def _compute() -> Dict[str, Any]:
        total_tweets = db.tweets.count_documents({})
        total_papers = db.papers.count_documents({})
        total_articles = db.articles.count_documents({})

        unique_tweet_authors = len(db.tweets.distinct("author_username"))
        unique_article_authors = db.substack_authors.count_documents({})

        paper_author_pipeline = [
            {'$unwind': '$authors'},
            {'$group': {'_id': '$authors.name'}},
            {'$count': 'total'}
        ]
        paper_author_result = list(db.papers.aggregate(paper_author_pipeline))
        unique_paper_authors = paper_author_result[0]['total'] if paper_author_result else 0

        total_concepts = db.tag_concepts_v2.count_documents({})
        root_concepts = db.tag_concepts_v2.count_documents({'parents': []})
        poly_hierarchy_pipeline = [
            {'$match': {'parents': {'$exists': True}}},
            {'$project': {'parent_count': {'$size': '$parents'}}},
            {'$match': {'parent_count': {'$gt': 1}}},
            {'$count': 'total'}
        ]
        poly_result = list(db.tag_concepts_v2.aggregate(poly_hierarchy_pipeline))
        poly_hierarchy_concepts = poly_result[0]['total'] if poly_result else 0

        tweet_assignments = db.tag_instances.count_documents({'content_type': 'tweet'})
        paper_assignments = db.tag_instances.count_documents({'content_type': 'paper'})
        article_assignments = db.tag_instances.count_documents({'content_type': 'article'})
        orphan_assignments = db.tag_instances.count_documents({'concept_id': None})

        oldest_tweet = db.tweets.find_one({}, sort=[('created_at', ASCENDING)])
        newest_tweet = db.tweets.find_one({}, sort=[('created_at', DESCENDING)])

        oldest_paper = db.papers.find_one({}, sort=[('created_at', ASCENDING)])
        newest_paper = db.papers.find_one({}, sort=[('created_at', DESCENDING)])

        oldest_article = db.articles.find_one({}, sort=[('published_at', ASCENDING)])
        newest_article = db.articles.find_one({}, sort=[('published_at', DESCENDING)])

        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        fourteen_days_ago = now - timedelta(days=14)

        recent_tweets = db.tweets.count_documents({'created_at': {'$gte': seven_days_ago}})
        previous_tweets = db.tweets.count_documents({'created_at': {'$gte': fourteen_days_ago, '$lt': seven_days_ago}})
        tweet_growth = ((recent_tweets - previous_tweets) / max(previous_tweets, 1)) * 100 if previous_tweets else 0

        recent_papers = db.papers.count_documents({'created_at': {'$gte': seven_days_ago}})
        previous_papers = db.papers.count_documents({'created_at': {'$gte': fourteen_days_ago, '$lt': seven_days_ago}})
        paper_growth = ((recent_papers - previous_papers) / max(previous_papers, 1)) * 100 if previous_papers else 0

        recent_articles = db.articles.count_documents({'published_at': {'$gte': seven_days_ago}})
        previous_articles = db.articles.count_documents({'published_at': {'$gte': fourteen_days_ago, '$lt': seven_days_ago}})
        article_growth = ((recent_articles - previous_articles) / max(previous_articles, 1)) * 100 if previous_articles else 0

        return {
            "content": {
                "tweets": {
                    "total": total_tweets,
                    "authors": unique_tweet_authors,
                    "recent_7d": recent_tweets,
                    "growth_rate": round(tweet_growth, 1),
                    "assignments": tweet_assignments,
                    "date_range": {
                        "oldest": oldest_tweet['created_at'].isoformat() if oldest_tweet and oldest_tweet.get('created_at') else None,
                        "newest": newest_tweet['created_at'].isoformat() if newest_tweet and newest_tweet.get('created_at') else None
                    }
                },
                "papers": {
                    "total": total_papers,
                    "authors": unique_paper_authors,
                    "recent_7d": recent_papers,
                    "growth_rate": round(paper_growth, 1),
                    "assignments": paper_assignments,
                    "processed": db.papers.count_documents({'is_processed': True}),
                    "date_range": {
                        "oldest": oldest_paper['created_at'].isoformat() if oldest_paper and oldest_paper.get('created_at') else None,
                        "newest": newest_paper['created_at'].isoformat() if newest_paper and newest_paper.get('created_at') else None
                    }
                },
                "articles": {
                    "total": total_articles,
                    "authors": unique_article_authors,
                    "recent_7d": recent_articles,
                    "growth_rate": round(article_growth, 1),
                    "assignments": article_assignments,
                    "with_summary": db.articles.count_documents({'summary': {'$ne': None}}),
                    "date_range": {
                        "oldest": oldest_article['published_at'].isoformat() if oldest_article and oldest_article.get('published_at') else None,
                        "newest": newest_article['published_at'].isoformat() if newest_article and newest_article.get('published_at') else None
                    }
                }
            },
            "tagging": {
                "total_concepts": total_concepts,
                "root_concepts": root_concepts,
                "poly_hierarchy": poly_hierarchy_concepts,
                "total_assignments": tweet_assignments + paper_assignments + article_assignments,
                "orphan_assignments": orphan_assignments,
                "assignments_by_type": {
                    "tweets": tweet_assignments,
                    "papers": paper_assignments,
                    "articles": article_assignments
                },
                "average_per_content": round((tweet_assignments + paper_assignments + article_assignments) / max(total_tweets + total_papers + total_articles, 1), 2)
            },
            "database": "MongoDB",
            "last_updated": datetime.utcnow().isoformat()
        }

    return _cached("overview_stats", _compute)

@router.get("/trends/detailed")
def get_detailed_trend_statistics(
    days: int = Query(30, ge=1, le=365),
    granularity: str = Query("daily", enum=["hourly", "daily", "weekly", "monthly"])
):
    """Get detailed trend statistics with configurable granularity"""
    
    # Calculate date threshold
    date_threshold = datetime.now() - timedelta(days=days)
    
    # Define date format based on granularity
    date_formats = {
        "hourly": '%Y-%m-%d %H:00',
        "daily": '%Y-%m-%d',
        "weekly": '%Y-W%V',
        "monthly": '%Y-%m'
    }
    date_format = date_formats[granularity]
    
    # Tweet trends with engagement metrics
    tweet_pipeline = [
        {'$match': {'created_at': {'$gte': date_threshold}}},
        {'$group': {
            '_id': {
                '$dateToString': {
                    'format': date_format,
                    'date': '$created_at'
                }
            },
            'count': {'$sum': 1},
            'total_likes': {'$sum': '$metrics.like_count'},
            'total_retweets': {'$sum': '$metrics.retweet_count'},
            'total_replies': {'$sum': '$metrics.reply_count'},
            'authors': {'$addToSet': '$author_username'}
        }},
        {'$sort': {'_id': 1}}
    ]
    tweet_trends = list(db.tweets.aggregate(tweet_pipeline))
    
    # Paper trends with processing status
    paper_pipeline = [
        {'$match': {'created_at': {'$gte': date_threshold}}},
        {'$group': {
            '_id': {
                '$dateToString': {
                    'format': date_format,
                    'date': '$created_at'
                }
            },
            'count': {'$sum': 1},
            'processed': {
                '$sum': {
                    '$cond': [{'$eq': ['$is_processed', True]}, 1, 0]
                }
            },
            'with_pdf': {
                '$sum': {
                    '$cond': [{'$ne': ['$pdf_path', None]}, 1, 0]
                }
            }
        }},
        {'$sort': {'_id': 1}}
    ]
    paper_trends = list(db.papers.aggregate(paper_pipeline))
    
    # Article trends with summary status
    article_pipeline = [
        {'$match': {'published_at': {'$gte': date_threshold}}},
        {'$group': {
            '_id': {
                '$dateToString': {
                    'format': date_format,
                    'date': '$published_at'
                }
            },
            'count': {'$sum': 1},
            'with_summary': {
                '$sum': {
                    '$cond': [{'$ne': ['$summary', None]}, 1, 0]
                }
            },
            'total_word_count': {'$sum': '$word_count'}
        }},
        {'$sort': {'_id': 1}}
    ]
    article_trends = list(db.articles.aggregate(article_pipeline))
    
    # Calculate statistics
    def calculate_stats(trends):
        if not trends:
            return {}
        counts = [t['count'] for t in trends]
        return {
            'total': sum(counts),
            'average': round(sum(counts) / len(counts), 1),
            'peak': max(counts),
            'lowest': min(counts),
            'trend': 'increasing' if len(counts) > 1 and counts[-1] > counts[0] else 'stable'
        }
    
    return {
        "period_days": days,
        "granularity": granularity,
        "trends": {
            "tweets": [
                {
                    'date': t['_id'],
                    'count': t['count'],
                    'engagement': {
                        'likes': t['total_likes'],
                        'retweets': t['total_retweets'],
                        'replies': t['total_replies']
                    },
                    'unique_authors': len(t['authors'])
                } for t in tweet_trends
            ],
            "papers": [
                {
                    'date': p['_id'],
                    'count': p['count'],
                    'processed': p['processed'],
                    'with_pdf': p['with_pdf']
                } for p in paper_trends
            ],
            "articles": [
                {
                    'date': a['_id'],
                    'count': a['count'],
                    'with_summary': a['with_summary'],
                    'avg_word_count': round(a['total_word_count'] / a['count']) if a['count'] > 0 else 0
                } for a in article_trends
            ]
        },
        "statistics": {
            "tweets": calculate_stats(tweet_trends),
            "papers": calculate_stats(paper_trends),
            "articles": calculate_stats(article_trends)
        }
    }

@router.get("/concepts/detailed")
def get_detailed_concept_statistics(
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    days: Optional[int] = Query(None, ge=1, le=365, description="Limit to recent days"),
    include_hierarchy: bool = Query(True, description="Include hierarchy information")
):
    """Get detailed concept statistics with usage patterns"""
    
    # Build match conditions
    match_conditions = {}
    if content_type:
        match_conditions['content_type'] = content_type
    
    # Get concept usage statistics
    concept_pipeline = [
        {'$match': match_conditions},
        {'$group': {
            '_id': '$concept_id',
            'total_usage': {'$sum': 1},
            'content_types': {'$addToSet': '$content_type'},
            'content_ids': {'$addToSet': '$content_id'}
        }},
        {'$sort': {'total_usage': -1}}
    ]
    
    concept_usage = list(db.tag_instances.aggregate(concept_pipeline))
    
    # Get concept details and hierarchy
    detailed_concepts = []
    for usage in concept_usage[:50]:  # Top 50 concepts
        if usage['_id']:  # Skip orphans
            concept = db.tag_concepts_v2.find_one({'_id': usage['_id']})
            if concept:
                concept_data = {
                    'concept_id': str(concept['_id']),
                    'display_name': concept.get('display_name'),
                    'slug': concept.get('slug'),
                    'entity_type': concept.get('entity_type'),
                    'usage': {
                        'total': usage['total_usage'],
                        'by_type': {}
                    }
                }
                
                # Count usage by content type
                for ct in ['tweet', 'paper', 'article']:
                    count = db.tag_instances.count_documents({
                        'concept_id': usage['_id'],
                        'content_type': ct
                    })
                    if count > 0:
                        concept_data['usage']['by_type'][ct] = count
                
                # Add hierarchy info if requested
                if include_hierarchy:
                    concept_data['hierarchy'] = {
                        'parents': [str(p) for p in concept.get('parents', [])],
                        'children': [str(c) for c in concept.get('children', [])],
                        'level': len(concept.get('parents', [])),
                        'is_poly_hierarchy': len(concept.get('parents', [])) > 1
                    }
                
                # Calculate recent trend if days specified
                if days:
                    date_threshold = datetime.now() - timedelta(days=days)
                    
                    # Get content IDs with this concept from recent period
                    recent_instances = db.tag_instances.find({
                        'concept_id': usage['_id'],
                        'content_type': {'$in': ['tweet', 'paper', 'article']}
                    })
                    
                    recent_count = 0
                    for instance in recent_instances:
                        # Check if content is recent based on type
                        if instance['content_type'] == 'tweet':
                            content = db.tweets.find_one({
                                '_id': instance['content_id'],
                                'created_at': {'$gte': date_threshold}
                            })
                        elif instance['content_type'] == 'paper':
                            content = db.papers.find_one({
                                '_id': instance['content_id'],
                                'created_at': {'$gte': date_threshold}
                            })
                        else:  # article
                            content = db.articles.find_one({
                                '_id': instance['content_id'],
                                'published_at': {'$gte': date_threshold}
                            })
                        
                        if content:
                            recent_count += 1
                    
                    concept_data['recent_usage'] = {
                        'period_days': days,
                        'count': recent_count,
                        'percentage_of_total': round((recent_count / usage['total_usage']) * 100, 1) if usage['total_usage'] > 0 else 0
                    }
                
                detailed_concepts.append(concept_data)
    
    # Get orphan statistics
    orphan_count = db.tag_instances.count_documents({'concept_id': None})
    
    return {
        "content_type_filter": content_type,
        "period_days": days,
        "total_concepts_used": len(concept_usage),
        "orphan_assignments": orphan_count,
        "concepts": detailed_concepts,
        "statistics": {
            "most_used": detailed_concepts[0] if detailed_concepts else None,
            "poly_hierarchy_count": sum(1 for c in detailed_concepts if c.get('hierarchy', {}).get('is_poly_hierarchy', False)),
            "average_usage": round(sum(c['usage']['total'] for c in detailed_concepts) / len(detailed_concepts), 1) if detailed_concepts else 0
        }
    }

@router.get("/authors/detailed")
def get_detailed_author_statistics(
    top_n: int = Query(20, ge=1, le=100),
    days: Optional[int] = Query(None, ge=1, le=365)
):
    """Get detailed author statistics with activity patterns"""
    
    date_threshold = datetime.now() - timedelta(days=days) if days else None
    
    # Twitter authors with detailed metrics
    tweet_match = {'created_at': {'$gte': date_threshold}} if date_threshold else {}
    tweet_author_pipeline = [
        {'$match': tweet_match},
        {'$group': {
            '_id': '$author_username',
            'tweet_count': {'$sum': 1},
            'total_likes': {'$sum': '$metrics.like_count'},
            'total_retweets': {'$sum': '$metrics.retweet_count'},
            'total_replies': {'$sum': '$metrics.reply_count'},
            'first_tweet': {'$min': '$created_at'},
            'last_tweet': {'$max': '$created_at'},
            'tweet_ids': {'$push': '$_id'}
        }},
        {'$sort': {'tweet_count': -1}},
        {'$limit': top_n}
    ]
    tweet_authors = list(db.tweets.aggregate(tweet_author_pipeline))
    
    # Add concept usage for tweet authors
    for author in tweet_authors:
        # Get concepts used by this author
        author_concepts = db.tag_instances.aggregate([
            {'$match': {
                'content_type': 'tweet',
                'content_id': {'$in': [str(tid) for tid in author['tweet_ids']]}
            }},
            {'$group': {
                '_id': '$concept_id',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ])
        
        top_concepts = []
        for ac in author_concepts:
            if ac['_id']:
                concept = db.tag_concepts_v2.find_one({'_id': ac['_id']})
                if concept:
                    top_concepts.append({
                        'name': concept.get('display_name'),
                        'count': ac['count']
                    })
        
        author['top_concepts'] = top_concepts
        author['engagement_rate'] = round(
            (author['total_likes'] + author['total_retweets']) / max(author['tweet_count'], 1), 1
        )
        del author['tweet_ids']  # Remove internal field
    
    # Paper authors with collaboration network
    paper_match = {'created_at': {'$gte': date_threshold}} if date_threshold else {}
    paper_author_pipeline = [
        {'$match': paper_match},
        {'$unwind': '$authors'},
        {'$group': {
            '_id': '$authors.name',
            'paper_count': {'$sum': 1},
            'affiliations': {'$addToSet': '$authors.affiliation'},
            'paper_ids': {'$push': '$_id'},
            'coauthors': {'$push': '$authors'}
        }},
        {'$sort': {'paper_count': -1}},
        {'$limit': top_n}
    ]
    paper_authors = list(db.papers.aggregate(paper_author_pipeline))
    
    # Process paper authors
    for author in paper_authors:
        # Get unique coauthors
        coauthor_names = set()
        for paper_authors_list in author['coauthors']:
            if isinstance(paper_authors_list, dict):
                name = paper_authors_list.get('name')
                if name and name != author['_id']:
                    coauthor_names.add(name)
        
        author['coauthor_count'] = len(coauthor_names)
        author['affiliations'] = [a for a in author['affiliations'] if a]
        
        # Get research topics (concepts)
        author_concepts = db.tag_instances.aggregate([
            {'$match': {
                'content_type': 'paper',
                'content_id': {'$in': [str(pid) for pid in author['paper_ids']]}
            }},
            {'$group': {
                '_id': '$concept_id',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ])
        
        research_topics = []
        for ac in author_concepts:
            if ac['_id']:
                concept = db.tag_concepts_v2.find_one({'_id': ac['_id']})
                if concept:
                    research_topics.append({
                        'name': concept.get('display_name'),
                        'count': ac['count']
                    })
        
        author['research_topics'] = research_topics
        del author['paper_ids']  # Remove internal field
        del author['coauthors']  # Remove internal field
    
    # Article authors with publishing patterns
    article_authors = []
    for author_doc in db.substack_authors.find():
        article_match = {'author_id': author_doc['_id']}
        if date_threshold:
            article_match['published_at'] = {'$gte': date_threshold}
        
        articles = list(db.articles.find(article_match).sort('published_at', -1))
        
        if articles:
            # Calculate statistics
            total_words = sum(a.get('word_count', 0) for a in articles)
            
            # Get topics
            article_concepts = db.tag_instances.aggregate([
                {'$match': {
                    'content_type': 'article',
                    'content_id': {'$in': [str(a['_id']) for a in articles]}
                }},
                {'$group': {
                    '_id': '$concept_id',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}},
                {'$limit': 5}
            ])
            
            topics = []
            for ac in article_concepts:
                if ac['_id']:
                    concept = db.tag_concepts_v2.find_one({'_id': ac['_id']})
                    if concept:
                        topics.append({
                            'name': concept.get('display_name'),
                            'count': ac['count']
                        })
            
            # Calculate publishing frequency
            if len(articles) > 1:
                date_range = (articles[0]['published_at'] - articles[-1]['published_at']).days
                avg_days_between = round(date_range / (len(articles) - 1), 1) if len(articles) > 1 else 0
            else:
                avg_days_between = 0
            
            article_authors.append({
                'name': author_doc.get('name'),
                'subdomain': author_doc.get('subdomain'),
                'article_count': len(articles),
                'total_words': total_words,
                'avg_words_per_article': round(total_words / len(articles)) if articles else 0,
                'topics': topics,
                'publishing_frequency': f"Every {avg_days_between} days" if avg_days_between > 0 else "N/A",
                'latest_article': articles[0]['title'] if articles else None
            })
    
    article_authors.sort(key=lambda x: x['article_count'], reverse=True)
    
    return {
        "period_days": days,
        "top_n": top_n,
        "tweet_authors": tweet_authors,
        "paper_authors": paper_authors,
        "article_authors": article_authors[:top_n]
    }

@router.get("/activity/heatmap")
def get_activity_heatmap(
    content_type: str = Query("all", enum=["all", "tweets", "papers", "articles"]),
    days: int = Query(30, ge=7, le=90)
):
    """Get activity heatmap data for visualization"""
    
    date_threshold = datetime.now() - timedelta(days=days)
    
    # Initialize heatmap structure
    heatmap = defaultdict(lambda: defaultdict(int))
    
    # Process tweets
    if content_type in ["all", "tweets"]:
        tweets = db.tweets.find({'created_at': {'$gte': date_threshold}})
        for tweet in tweets:
            if tweet.get('created_at'):
                day = tweet['created_at'].weekday()
                hour = tweet['created_at'].hour
                heatmap[day][hour] += 1
    
    # Process papers
    if content_type in ["all", "papers"]:
        papers = db.papers.find({'created_at': {'$gte': date_threshold}})
        for paper in papers:
            if paper.get('created_at'):
                day = paper['created_at'].weekday()
                hour = paper['created_at'].hour
                heatmap[day][hour] += 1
    
    # Process articles
    if content_type in ["all", "articles"]:
        articles = db.articles.find({'published_at': {'$gte': date_threshold}})
        for article in articles:
            if article.get('published_at'):
                day = article['published_at'].weekday()
                hour = article['published_at'].hour
                heatmap[day][hour] += 1
    
    # Convert to structured format
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = []
    
    for day_idx in range(7):
        day_data = {
            'day': days_of_week[day_idx],
            'hours': []
        }
        for hour in range(24):
            day_data['hours'].append({
                'hour': hour,
                'value': heatmap[day_idx][hour],
                'time': f"{hour:02d}:00"
            })
        heatmap_data.append(day_data)
    
    # Find peak times
    max_value = 0
    peak_day = None
    peak_hour = None
    
    for day_idx, day_name in enumerate(days_of_week):
        for hour in range(24):
            if heatmap[day_idx][hour] > max_value:
                max_value = heatmap[day_idx][hour]
                peak_day = day_name
                peak_hour = hour
    
    return {
        "content_type": content_type,
        "period_days": days,
        "heatmap": heatmap_data,
        "statistics": {
            "peak_time": f"{peak_day} at {peak_hour:02d}:00" if peak_day else None,
            "peak_value": max_value,
            "total_activity": sum(sum(hours.values()) for hours in heatmap.values())
        }
    }

@router.get("/search/statistics")
def get_search_statistics():
    """Get statistics about search and RAG usage"""
    
    # Check if RAG index exists
    rag_stats = {
        "index_exists": False,
        "documents_indexed": 0,
        "last_rebuild": None
    }
    
    # You would check actual RAG index here
    # For now, return placeholder
    
    return {
        "rag": rag_stats,
        "search_capabilities": {
            "full_text_search": True,
            "concept_search": True,
            "semantic_search": False,  # Would need embeddings
            "cross_content_search": True
        }
    }

@router.get("/quality/metrics")
def get_quality_metrics():
    """Get content quality metrics"""
    
    # Calculate various quality metrics
    metrics = {
        "tweets": {
            "with_media": db.tweets.count_documents({'media': {'$ne': []}}),
            "with_urls": db.tweets.count_documents({'urls': {'$ne': []}}),
            "with_concepts": db.tag_instances.count_documents({'content_type': 'tweet'}),
            "avg_length": 0  # Would need to calculate
        },
        "papers": {
            "with_pdf": db.papers.count_documents({'pdf_path': {'$ne': None}}),
            "processed": db.papers.count_documents({'is_processed': True}),
            "with_abstracts": db.papers.count_documents({'abstract': {'$ne': None}}),
            "with_authors": db.papers.count_documents({'authors': {'$ne': []}})
        },
        "articles": {
            "with_summary": db.articles.count_documents({'summary': {'$ne': None}}),
            "avg_word_count": 0,  # Calculate average
            "with_concepts": db.tag_instances.count_documents({'content_type': 'article'})
        }
    }
    
    # Calculate average word count for articles
    avg_pipeline = [
        {'$match': {'word_count': {'$ne': None}}},
        {'$group': {
            '_id': None,
            'avg_words': {'$avg': '$word_count'}
        }}
    ]
    avg_result = list(db.articles.aggregate(avg_pipeline))
    if avg_result:
        metrics['articles']['avg_word_count'] = round(avg_result[0]['avg_words'])
    
    return metrics

@router.get("/export/summary")
def get_export_summary():
    """Get a comprehensive summary suitable for export"""
    
    summary = {
        "generated_at": datetime.now().isoformat(),
        "database": "MongoDB",
        "content_summary": {
            "tweets": db.tweets.count_documents({}),
            "papers": db.papers.count_documents({}),
            "articles": db.articles.count_documents({})
        },
        "concept_summary": {
            "total_concepts": db.tag_concepts_v2.count_documents({}),
            "total_assignments": db.tag_instances.count_documents({})
        },
        "date_range": {
            "earliest_content": None,
            "latest_content": None
        }
    }
    
    # Find earliest and latest content
    earliest_tweet = db.tweets.find_one({}, sort=[('created_at', ASCENDING)])
    earliest_paper = db.papers.find_one({}, sort=[('created_at', ASCENDING)])
    earliest_article = db.articles.find_one({}, sort=[('published_at', ASCENDING)])
    
    earliest_dates = []
    if earliest_tweet and earliest_tweet.get('created_at'):
        earliest_dates.append(earliest_tweet['created_at'])
    if earliest_paper and earliest_paper.get('created_at'):
        earliest_dates.append(earliest_paper['created_at'])
    if earliest_article and earliest_article.get('published_at'):
        earliest_dates.append(earliest_article['published_at'])
    
    if earliest_dates:
        summary['date_range']['earliest_content'] = min(earliest_dates).isoformat()
    
    latest_tweet = db.tweets.find_one({}, sort=[('created_at', DESCENDING)])
    latest_paper = db.papers.find_one({}, sort=[('created_at', DESCENDING)])
    latest_article = db.articles.find_one({}, sort=[('published_at', DESCENDING)])
    
    latest_dates = []
    if latest_tweet and latest_tweet.get('created_at'):
        latest_dates.append(latest_tweet['created_at'])
    if latest_paper and latest_paper.get('created_at'):
        latest_dates.append(latest_paper['created_at'])
    if latest_article and latest_article.get('published_at'):
        latest_dates.append(latest_article['published_at'])
    
    if latest_dates:
        summary['date_range']['latest_content'] = max(latest_dates).isoformat()
    
    return summary
