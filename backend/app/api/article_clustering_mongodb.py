"""
API endpoints for article clustering based on tags - MongoDB version
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging
from pymongo.database import Database
from app.database.mongodb import get_database

from app.services.article_clustering_service import ArticleClusteringService
from app.repositories import article_clustering_queries as queries

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
db: Database = get_database()

def prepare_article_data(articles: List[Dict]) -> List[Dict[str, Any]]:
    """Convert MongoDB articles to dictionaries for clustering"""
    article_data = []
    for article in articles:
        # Parse tags from MongoDB document
        tags = []
        if article.get('tags'):
            # Handle both list of strings and list of dicts
            article_tags = article['tags']
            if isinstance(article_tags, list):
                for tag in article_tags:
                    if isinstance(tag, str):
                        tags.append(tag)
                    elif isinstance(tag, dict) and 'tag' in tag:
                        tags.append(tag['tag'])
                
        article_data.append({
            'id': str(article.get('_id', '')),
            'title': article.get('title', ''),
            'author': article.get('author', 'Unknown'),
            'tags': tags,
            'url': article.get('url', ''),
            'published_date': article.get('published_at'),
            'summary': article.get('summary', '')[:200] if article.get('summary') else None
        })
    return article_data

def _get_tagged_articles(limit: int = 2000) -> List[Dict]:
    """Fetch articles that have tags, with a reasonable limit."""
    return list(queries.articles_find___get_tagged_articles().limit(limit))

@router.get("/cluster/kmeans")
async def cluster_articles_kmeans(
    n_clusters: int = Query(5, ge=2, le=20, description="Number of clusters"),
    min_tags: int = Query(1, ge=1, description="Minimum tags per article"),
) -> Dict[str, Any]:
    """
    Cluster articles using K-means algorithm based on their tags
    """
    try:
        # Fetch articles with tags from MongoDB
        articles = _get_tagged_articles()
        
        if len(articles) < n_clusters:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough articles with tags. Found {len(articles)}, need at least {n_clusters}"
            )
        
        # Prepare data
        article_data = prepare_article_data(articles)
        
        # Filter by minimum tags
        if min_tags > 1:
            article_data = [a for a in article_data if len(a['tags']) >= min_tags]

        # Re-check after min_tags filtering - the filter can shrink the
        # dataset below n_clusters, which would crash KMeans.
        if len(article_data) < n_clusters:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough articles with at least {min_tags} tags. Found {len(article_data)}, need at least {n_clusters}"
            )

        # Initialize clustering service
        service = ArticleClusteringService()
        service.prepare_articles_data(article_data)
        
        # Perform clustering
        results = service.cluster_kmeans(n_clusters=n_clusters)
        
        return {
            'success': True,
            'total_articles': len(article_data),
            'clustering_results': results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in K-means clustering: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cluster/hierarchical")
async def cluster_articles_hierarchical(
    n_clusters: Optional[int] = Query(None, ge=2, le=20, description="Number of clusters"),
    distance_threshold: Optional[float] = Query(None, ge=0.1, le=2.0, description="Distance threshold"),
) -> Dict[str, Any]:
    """
    Cluster articles using hierarchical clustering based on their tags
    """
    try:
        if n_clusters is None and distance_threshold is None:
            n_clusters = 5  # Default
            
        # Fetch articles with tags from MongoDB
        articles = _get_tagged_articles()
        
        if len(articles) < 2:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough articles with tags. Found {len(articles)}, need at least 2"
            )
        
        # Prepare data
        article_data = prepare_article_data(articles)
        
        # Initialize clustering service
        service = ArticleClusteringService()
        service.prepare_articles_data(article_data)
        
        # Perform clustering
        results = service.cluster_hierarchical(
            n_clusters=n_clusters,
            distance_threshold=distance_threshold
        )
        
        return {
            'success': True,
            'total_articles': len(article_data),
            'clustering_results': results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in hierarchical clustering: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cluster/dbscan")
async def cluster_articles_dbscan(
    eps: float = Query(0.3, ge=0.1, le=1.0, description="Maximum distance between samples"),
    min_samples: int = Query(2, ge=2, le=10, description="Minimum samples in neighborhood"),
) -> Dict[str, Any]:
    """
    Cluster articles using DBSCAN (density-based) algorithm based on their tags
    """
    try:
        # Fetch articles with tags from MongoDB
        articles = _get_tagged_articles()
        
        if len(articles) < min_samples:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough articles with tags. Found {len(articles)}, need at least {min_samples}"
            )
        
        # Prepare data
        article_data = prepare_article_data(articles)
        
        # Initialize clustering service
        service = ArticleClusteringService()
        service.prepare_articles_data(article_data)
        
        # Perform clustering
        results = service.cluster_dbscan(eps=eps, min_samples=min_samples)
        
        return {
            'success': True,
            'total_articles': len(article_data),
            'clustering_results': results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in DBSCAN clustering: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similar/{article_id}")
async def find_similar_articles(
    article_id: str,
    top_k: int = Query(5, ge=1, le=20, description="Number of similar articles"),
) -> Dict[str, Any]:
    """
    Find articles similar to a given article based on tag similarity
    """
    try:
        from bson import ObjectId
        
        # Convert string ID to ObjectId
        try:
            obj_id = ObjectId(article_id)
        except Exception:
            obj_id = article_id
            
        # Check if article exists
        target_article = queries.articles_find_one__find_similar_articles(obj_id)
        if not target_article:
            raise HTTPException(status_code=404, detail=f"Article {article_id} not found")
            
        # Fetch all articles with tags from MongoDB
        articles = _get_tagged_articles()
        
        # Prepare data
        article_data = prepare_article_data(articles)
        
        # Initialize clustering service
        service = ArticleClusteringService()
        service.prepare_articles_data(article_data)
        
        # Find similar articles
        similar = service.find_similar_articles(str(obj_id), top_k=top_k)
        
        return {
            'success': True,
            'reference_article': {
                'id': str(target_article['_id']),
                'title': target_article.get('title', ''),
                'tags': prepare_article_data([target_article])[0]['tags']
            },
            'similar_articles': similar
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tag-cooccurrence")
async def get_tag_cooccurrence() -> Dict[str, Any]:
    """
    Get tag co-occurrence matrix and relationships
    """
    try:
        # Fetch articles with tags from MongoDB
        articles = _get_tagged_articles()
        
        # Prepare data
        article_data = prepare_article_data(articles)
        
        # Initialize clustering service
        service = ArticleClusteringService()
        service.prepare_articles_data(article_data)
        
        # Get co-occurrence matrix
        cooccurrence = service.get_tag_co_occurrence_matrix()
        
        return {
            'success': True,
            'total_articles': len(article_data),
            'cooccurrence_analysis': cooccurrence
        }
        
    except Exception as e:
        logger.error(f"Error getting tag co-occurrence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_clustering_summary() -> Dict[str, Any]:
    """
    Get summary statistics for article clustering
    """
    try:
        # Fetch articles with tags from MongoDB
        articles = _get_tagged_articles()
        
        # Prepare data
        article_data = prepare_article_data(articles)
        
        # Initialize clustering service
        service = ArticleClusteringService()
        service.prepare_articles_data(article_data)
        
        # Get summary
        summary = service.get_cluster_summary()
        
        return {
            'success': True,
            'summary': summary
        }
        
    except Exception as e:
        logger.error(f"Error getting clustering summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualization-data")
async def get_visualization_data(
    method: str = Query("pca", enum=["pca", "tsne"], description="Dimensionality reduction method"),
    n_components: int = Query(2, ge=2, le=3, description="Number of dimensions"),
) -> Dict[str, Any]:
    """
    Get article coordinates for 2D/3D visualization
    """
    try:
        # Fetch articles with tags from MongoDB
        articles = _get_tagged_articles()
        
        if len(articles) < 3:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough articles for visualization. Found {len(articles)}, need at least 3"
            )
        
        # Prepare data
        article_data = prepare_article_data(articles)
        
        # Initialize clustering service
        service = ArticleClusteringService()
        service.prepare_articles_data(article_data)
        
        # Get visualization data
        viz_data = service.export_for_visualization(method=method, n_components=n_components)
        
        return {
            'success': True,
            'total_articles': len(article_data),
            'visualization': viz_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting visualization data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
