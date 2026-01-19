"""
Full MongoDB version of main.py
All data operations use MongoDB - no SQLite dependencies
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
from app.database.mongodb import get_client, get_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_client = get_client()
db = get_database()
logger.info("Connected to MongoDB")

# Import MongoDB-based API modules
from app.api import tweets_mongodb as tweets  # Full MongoDB tweets API
from app.api import papers_mongodb as papers  # Full MongoDB papers API  
from app.api import articles_mongodb as articles  # Full MongoDB articles API
from app.api import statistics_mongodb as statistics  # MongoDB statistics
from app.api import rag_concepts  # Concept-based RAG
from app.api import tag_ontology_v2_mongodb as ontology  # MongoDB ontology
from app.api import orphan_tags  # Orphan tag management
from app.api import ontology_graph  # Ontology visualization
from app.api import tag_import_export  # Tag import/export
from app.api import concept_organization  # Concept organization service
from app.api import concepts_suggestions_mongodb as concepts_suggestions  # MongoDB concept suggestions
from app.api import unified_trends_mongodb as unified_trends  # MongoDB unified trends
from app.api import trends_mongodb as trends  # MongoDB trends analysis
from app.api import user_trends_mongodb as user_trends  # MongoDB user trends
from app.api import analytics_trends_mongodb as analytics_trends  # MongoDB analytics trends

# Additional APIs that might need updating
from app.api import media_gallery  # Media gallery
from app.api import arxiv  # ArXiv import
from app.api import paper_repository  # Paper repository
from app.api import article_clustering  # Article clustering
from app.api import substack  # Substack articles API

# Create FastAPI app
app = FastAPI(
    title="SmartTrendTracer API - MongoDB Edition",
    description="AI Content Monitoring System using MongoDB",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3470", "http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with MongoDB implementations
app.include_router(tweets.router, prefix="/api/tweets", tags=["tweets"])
app.include_router(papers.router, prefix="/api/papers", tags=["papers"])
app.include_router(articles.router, prefix="/api/articles", tags=["articles"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["statistics"])
app.include_router(rag_concepts.router, prefix="/api/rag", tags=["rag"])
app.include_router(ontology.router, prefix="/api/ontology", tags=["ontology"])
app.include_router(orphan_tags.router, prefix="/api/tags/orphans", tags=["orphan_tags"])
app.include_router(ontology_graph.router, prefix="/api/ontology-graph", tags=["ontology_graph"])
app.include_router(tag_import_export.router, prefix="/api/tags/import-export", tags=["import_export"])
app.include_router(concept_organization.router, prefix="/api/concepts/organization", tags=["concept_organization"])
app.include_router(concepts_suggestions.router, prefix="/api/concepts/suggestions", tags=["suggestions"])
app.include_router(unified_trends.router, prefix="/api/unified", tags=["unified_trends"])
app.include_router(trends.router, prefix="/api/trends", tags=["trends"])
app.include_router(user_trends.router, prefix="/api/user-trends", tags=["user_trends"])
app.include_router(analytics_trends.router, prefix="/api/analytics/trends", tags=["analytics_trends"])
app.include_router(media_gallery.router, prefix="/api/media-gallery", tags=["media"])
app.include_router(arxiv.router, prefix="/api/arxiv", tags=["arxiv"])
app.include_router(paper_repository.router, prefix="/api/paper-repository", tags=["repository"])
app.include_router(article_clustering.router, prefix="/api/article-clustering", tags=["clustering"])
app.include_router(substack.router, prefix="/api/substack", tags=["substack"])

# Static file serving for PDFs and other documents
pdf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "papers")
if os.path.exists(pdf_dir):
    app.mount("/papers", StaticFiles(directory=pdf_dir), name="papers")
    logger.info(f"Serving PDFs from: {pdf_dir}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API and MongoDB are running"""
    try:
        # Check MongoDB connection
        db.command('ping')
        
        # Get some stats
        stats = {
            "status": "healthy",
            "database": "MongoDB",
            "collections": {
                "tweets": db.tweets.count_documents({}),
                "papers": db.papers.count_documents({}),
                "articles": db.articles.count_documents({}),
                "concepts": db.tag_concepts_v2.count_documents({})
            }
        }
        return stats
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "SmartTrendTracer API",
        "version": "2.0.0",
        "database": "MongoDB",
        "message": "Fully migrated to MongoDB - no SQLite dependencies",
        "endpoints": {
            "tweets": "/api/tweets",
            "papers": "/api/papers", 
            "articles": "/api/articles",
            "statistics": "/api/statistics",
            "rag": "/api/rag",
            "ontology": "/api/ontology",
            "health": "/health"
        }
    }

@app.on_event("startup")
async def startup_event():
    """Initialize MongoDB indexes on startup"""
    logger.info("Initializing MongoDB indexes...")
    
    try:
        # Ensure indexes exist (handle if they already exist)
        db.tweets.create_index([("created_at", -1)])
        db.tweets.create_index([("author_username", 1)])
        db.papers.create_index([("title", "text")])
        db.articles.create_index([("title", "text")])
        # Don't create slug index since it already exists with unique constraint
        db.tag_instances.create_index([("content_type", 1), ("content_id", 1)])
    except Exception as e:
        logger.warning(f"Some indexes may already exist: {e}")
    
    logger.info("MongoDB indexes initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up MongoDB connection on shutdown"""
    mongo_client.close()
    logger.info("MongoDB connection closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
