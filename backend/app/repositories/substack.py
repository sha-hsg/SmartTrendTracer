"""
Data access for app.api.substack_mongodb (extracted by the arch-audit refactor).

MongoDB-based Substack API - compatible with full MongoDB system
"""
import logging

from app.database.mongodb import get_database

db = get_database()

logger = logging.getLogger(__name__)




def substack_health():
    """Health check for Substack API"""
    try:
        article_count = db.articles.count_documents({})
        return {
            "status": "healthy",
            "articles_count": article_count,
            "database": "MongoDB"
        }
    except Exception as e:
        logger.error(f"Substack health check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

