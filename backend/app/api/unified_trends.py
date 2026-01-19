"""
Unified Trends API
Provides tag-based trends and clustering for tweets and articles
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

from app.analyzers.unified_trend_analyzer import UnifiedTrendAnalyzer

router = APIRouter()

@router.get("/tweets/tags")
def get_tweet_tag_trends(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    limit: int = Query(20, ge=5, le=50, description="Maximum number of tags to return"),
):
    """
    Get tag-based trends for tweets
    Includes tag frequencies, velocities, and relationships
    """
    analyzer = UnifiedTrendAnalyzer(db)
    return analyzer.analyze_tweet_tag_trends(days=days, limit=limit)

@router.get("/articles/tags")
def get_article_tag_trends(
    days: int = Query(30, ge=1, le=180, description="Number of days to analyze"),
    limit: int = Query(20, ge=5, le=50, description="Maximum number of tags to return"),
):
    """
    Get tag-based trends for articles
    Includes tag frequencies, velocities, and relationships
    """
    analyzer = UnifiedTrendAnalyzer(db)
    return analyzer.analyze_article_tag_trends(days=days, limit=limit)

@router.get("/tweets/clusters")
def cluster_tweets(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    n_clusters: Optional[int] = Query(None, ge=2, le=20, description="Number of clusters (auto if not specified)"),
):
    """
    Cluster tweets based on content similarity
    Uses TF-IDF and K-means clustering
    """
    analyzer = UnifiedTrendAnalyzer(db)
    return analyzer.cluster_tweets(days=days, n_clusters=n_clusters)

@router.get("/articles/clusters")
def cluster_articles(
    days: int = Query(30, ge=7, le=180, description="Number of days to analyze"),
    n_clusters: Optional[int] = Query(None, ge=2, le=15, description="Number of clusters (auto if not specified)"),
):
    """
    Cluster articles based on content similarity
    Uses enhanced TF-IDF with bigrams and K-means clustering
    """
    analyzer = UnifiedTrendAnalyzer(db)
    return analyzer.cluster_articles(days=days, n_clusters=n_clusters)

@router.get("/comparison")
def compare_trends(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
):
    """
    Compare trends between tweets and articles
    Shows common themes and divergent topics
    """
    analyzer = UnifiedTrendAnalyzer(db)
    
    # Get trends for both
    tweet_trends = analyzer.analyze_tweet_tag_trends(days=days, limit=30)
    article_trends = analyzer.analyze_article_tag_trends(days=days, limit=30)
    
    # Extract top tags
    tweet_tags = {t['tag'] for t in tweet_trends['top_tags']}
    article_tags = {t['tag'] for t in article_trends['top_tags']}
    
    # Find commonalities and differences
    common_tags = tweet_tags & article_tags
    tweet_only = tweet_tags - article_tags
    article_only = article_tags - tweet_tags
    
    # Get velocity comparison for common tags
    velocity_comparison = []
    tweet_velocities = {t['tag']: t for t in tweet_trends['tag_velocities']}
    article_velocities = {t['tag']: t for t in article_trends['tag_velocities']}
    
    for tag in common_tags:
        tweet_vel = tweet_velocities.get(tag, {})
        article_vel = article_velocities.get(tag, {})
        
        velocity_comparison.append({
            'tag': tag,
            'tweet_velocity': tweet_vel.get('velocity', 0),
            'tweet_trend': tweet_vel.get('trend', 'stable'),
            'article_velocity': article_vel.get('velocity', 0),
            'article_trend': article_vel.get('trend', 'stable'),
            'alignment': 'aligned' if tweet_vel.get('trend') == article_vel.get('trend') else 'divergent'
        })
    
    # Sort by alignment and velocity
    velocity_comparison.sort(key=lambda x: (x['alignment'] == 'divergent', abs(x['tweet_velocity'] + x['article_velocity'])), reverse=True)
    
    return {
        'period_days': days,
        'common_tags': list(common_tags),
        'tweet_exclusive_tags': list(tweet_only)[:10],
        'article_exclusive_tags': list(article_only)[:10],
        'velocity_comparison': velocity_comparison[:15],
        'summary': {
            'total_tweet_tags': len(tweet_tags),
            'total_article_tags': len(article_tags),
            'common_tag_count': len(common_tags),
            'overlap_percentage': (len(common_tags) / max(len(tweet_tags), len(article_tags)) * 100) if tweet_tags or article_tags else 0
        }
    }

@router.get("/dashboard")
def get_unified_dashboard(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
):
    """
    Get comprehensive dashboard data for both tweets and articles
    Includes trends, clusters, and comparisons
    """
    analyzer = UnifiedTrendAnalyzer(db)
    
    # Get all analyses
    tweet_trends = analyzer.analyze_tweet_tag_trends(days=days, limit=10)
    article_trends = analyzer.analyze_article_tag_trends(days=days, limit=10)
    tweet_clusters = analyzer.cluster_tweets(days=days)
    article_clusters = analyzer.cluster_articles(days=days)
    
    # Extract key metrics
    dashboard = {
        'period_days': days,
        'tweets': {
            'top_tags': tweet_trends['top_tags'][:5],
            'rising_tags': tweet_trends['rising_tags'][:3],
            'cluster_count': tweet_clusters.get('n_clusters', 0),
            'cluster_quality': tweet_clusters.get('quality_rating', 'unknown'),
            'total_analyzed': tweet_clusters.get('total_tweets', 0)
        },
        'articles': {
            'top_tags': article_trends['top_tags'][:5],
            'rising_tags': article_trends['rising_tags'][:3],
            'cluster_count': article_clusters.get('n_clusters', 0),
            'cluster_quality': article_clusters.get('quality_rating', 'unknown'),
            'total_analyzed': article_clusters.get('total_articles', 0)
        },
        'insights': {
            'most_active_content': 'tweets' if tweet_clusters.get('total_tweets', 0) > article_clusters.get('total_articles', 0) * 10 else 'articles',
            'clustering_better_for': 'tweets' if tweet_clusters.get('silhouette_score', 0) > article_clusters.get('silhouette_score', 0) else 'articles',
            'trend_alignment': self._calculate_trend_alignment(tweet_trends, article_trends)
        }
    }
    
    return dashboard

def _calculate_trend_alignment(tweet_trends, article_trends):
    """Calculate how aligned the trends are between tweets and articles"""
    tweet_rising = {t['tag'] for t in tweet_trends.get('rising_tags', [])}
    article_rising = {t['tag'] for t in article_trends.get('rising_tags', [])}
    
    if not tweet_rising and not article_rising:
        return 'no trends'
    
    overlap = len(tweet_rising & article_rising)
    total = len(tweet_rising | article_rising)
    
    if total == 0:
        return 'no data'
    
    alignment_score = overlap / total
    
    if alignment_score > 0.5:
        return 'highly aligned'
    elif alignment_score > 0.2:
        return 'partially aligned'
    else:
        return 'divergent'