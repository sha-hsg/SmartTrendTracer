"""
Full MongoDB version of main.py
All data operations use MongoDB - no SQLite dependencies
"""

from app.config import settings
from app.repositories.errors import RepositoryError
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import logging
from pymongo import ASCENDING
from app.database.mongodb import get_client, get_database

# Configure logging to both file and console
import sys
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)

# Set up file handler with rotation
file_handler = RotatingFileHandler(
    os.path.join(log_dir, 'backend.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))

# Set up console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
))

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)

# MongoDB connection with validation
mongo_client = get_client()
db = get_database()

# Validate MongoDB connection at startup (CFG-005)
try:
    # Simple ping to verify connection is working
    mongo_client.admin.command('ping')
    # Count collections to verify database is accessible
    collection_count = len(db.list_collection_names())
    logger.info(f"Connected to MongoDB (database has {collection_count} collections)")
except Exception as e:
    logger.error(f"MongoDB connection validation failed: {e}")
    logger.error("Please ensure MongoDB is running and MONGODB_URI is correct")
    raise RuntimeError(f"Cannot start application: MongoDB unavailable - {e}")

# Import MongoDB-based API modules
from app.api import tweets  # Full MongoDB tweets API (package)
from app.api import papers  # Papers API (modular package)
from app.api import books  # Books API (modular package)
from app.api import articles  # Articles API (modular package)
from app.api import substack_mongodb as substack  # Full MongoDB substack API
from app.api import reddit_mongodb as reddit  # Full MongoDB reddit API
from app.api import statistics  # MongoDB statistics (package)
from app.api import trends_mongodb as trends  # MongoDB trends API
from app.api import user_trends_mongodb as user_trends  # MongoDB user trends
from app.api import analytics_trends  # MongoDB analytics trends (package)
from app.api import trend_analysis_mongodb as trend_analysis  # Comprehensive trend analysis
from app.api import topic_explorer  # Topic Explorer for frequency and correlation analysis
from app.api import rag_concepts  # Concept-based RAG
from app.api import tag_ontology as ontology  # MongoDB ontology (package)
from app.api import ontology_graph  # Ontology visualization
from app.api import concepts_suggestions_mongodb as concepts_suggestions  # MongoDB concept suggestions

# Additional APIs that might need updating
from app.api import media_gallery_mongodb as media_gallery  # MongoDB Media gallery
from app.api import arxiv  # ArXiv import
from app.api import acl_anthology  # ACL Anthology import
from app.api import acm_import  # ACM Digital Library import
from app.api import direct_url_import  # Direct URL import
from app.api import openreview_import  # OpenReview paper import
from app.api import jair_import  # JAIR import
from app.api import article_clustering_mongodb as article_clustering  # Article clustering (MongoDB)
from app.api import concept_organization  # Concept organization for unorganized concepts
from app.api import article_import  # MongoDB Article URL import (package)
from app.api import article_preview  # Article preview regeneration
from app.api import pdf_export  # PDF export for articles - MongoDB migrated
from app.api import tag_reorganization  # Tag reorganization package (async SSE + apply + comprehensive)
from app.api import dblp_mongodb  # DBLP API - MongoDB version without SQLite dependencies
from app.api import system_stats  # Comprehensive system statistics (package)
from app.api import references  # Normalized references collection API
from app.api import entity_extraction  # Entity extraction and annotation management - MongoDB version
from app.api import llm_preferences  # LLM model preferences and management
from app.api import user_settings  # Generic per-user key-value settings (TweetDeck columns, etc.)
from app.api import authors_management  # Author management and analytics
from app.api import twitter_accounts  # Twitter account management

# Create FastAPI app
app = FastAPI(
    title="SmartTrendTracer API - MongoDB Edition",
    description="AI Content Monitoring System using MongoDB",
    version="2.0.0"
)

# Configure CORS - origins from environment variable or defaults (CFG-004)
cors_origins = settings.cors_origins

logger.info(f"CORS configured for origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware (OBS-001)
@app.middleware("http")
async def request_timing_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"
    if elapsed_ms > 1000:
        logger.warning(f"Slow request: {request.method} {request.url.path} took {elapsed_ms:.0f}ms")
    return response


# Global exception handlers — sanitize error responses to prevent leaking internals
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code >= 500:
        logger.error(f"Server error on {request.method} {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": "Internal server error"},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RepositoryError)
async def repository_error_handler(request: Request, exc: RepositoryError):
    """Map data-layer domain errors to HTTP exactly like HTTPException."""
    if exc.status_code >= 500:
        logger.error(f"Server error on {request.method} {request.url.path}: {exc.detail}")
        return JSONResponse(status_code=exc.status_code, content={"detail": "Internal server error"})
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# Include routers with MongoDB implementations
app.include_router(tweets.router, prefix="/api/tweets", tags=["tweets"])
app.include_router(papers.router, prefix="/api/papers", tags=["papers"])
app.include_router(entity_extraction.router, prefix="/api/entities", tags=["entity_extraction"])  # MongoDB entity extraction
app.include_router(llm_preferences.router, prefix="/api/llm", tags=["llm"])  # LLM preferences and model management
app.include_router(user_settings.router, prefix="/api/user-settings", tags=["user_settings"])  # Generic per-user settings (TweetDeck columns, etc.)
app.include_router(books.router, prefix="/api/books", tags=["books"])
app.include_router(articles.router, prefix="/api/articles", tags=["articles"])
app.include_router(authors_management.router, prefix="/api/authors", tags=["authors"])  # Author management and analytics
app.include_router(twitter_accounts.router, prefix="/api/twitter-accounts", tags=["twitter_accounts"])  # Twitter account management
app.include_router(substack.router, prefix="/api/substack", tags=["substack"])
app.include_router(reddit.router, prefix="/api/reddit", tags=["reddit"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["statistics"])
app.include_router(trends.router, prefix="/api/trends", tags=["trends"])
app.include_router(user_trends.router, prefix="/api/user-trends", tags=["user_trends"])
app.include_router(analytics_trends.router, prefix="/api/analytics/trends", tags=["analytics_trends"])
app.include_router(trend_analysis.router, prefix="/api/trends/analysis", tags=["trend_analysis"])
app.include_router(topic_explorer.router, prefix="/api/topics", tags=["topic_explorer"])
app.include_router(rag_concepts.router, prefix="/api/rag", tags=["rag"])
app.include_router(ontology.router, prefix="/api/ontology", tags=["ontology"])
app.include_router(ontology_graph.router, prefix="/api/ontology-graph", tags=["ontology_graph"])
app.include_router(concepts_suggestions.router, prefix="/api/concepts/suggestions", tags=["suggestions"])
app.include_router(concept_organization.router, prefix="/api/concepts/organization", tags=["concept_organization"])
app.include_router(system_stats.router)  # Comprehensive system statistics (package)
app.include_router(references.router)  # References API with normalized collection (has own prefix)
app.include_router(media_gallery.router, prefix="/api/media-gallery", tags=["media"])  # MongoDB Media gallery
app.include_router(arxiv.router, prefix="/api/arxiv", tags=["arxiv"])
app.include_router(acl_anthology.router, prefix="/api/acl-anthology", tags=["acl-anthology"])
app.include_router(acm_import.router, tags=["acm"])  # ACM Digital Library import
app.include_router(direct_url_import.router, prefix="/api/papers", tags=["direct-url"])  # Direct URL import
app.include_router(openreview_import.router, tags=["openreview"])  # OpenReview paper import
app.include_router(jair_import.router, prefix="/api/jair", tags=["jair"])  # JAIR import
app.include_router(article_clustering.router, prefix="/api/article-clustering", tags=["clustering"])
app.include_router(article_import.router, prefix="/api/v2/articles", tags=["article-import"])
app.include_router(article_preview.router, prefix="/api/article-preview", tags=["article-preview"])
app.include_router(pdf_export.router, prefix="/api/pdf", tags=["pdf-export"])  # MongoDB migrated
app.include_router(tag_reorganization.router, prefix="/api/tags/reorganize", tags=["tag-reorganization"])
app.include_router(dblp_mongodb.router, tags=["dblp"])  # MongoDB-compatible DBLP API at /api/dblp
app.include_router(dblp_mongodb.papers_router, tags=["dblp"])  # Also available at /api/papers/dblp

# Static file serving for PDFs and other documents
pdf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "papers")
if os.path.exists(pdf_dir):
    app.mount("/papers", StaticFiles(directory=pdf_dir), name="papers")
    logger.info(f"Serving PDFs from: {pdf_dir}")

books_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "book_repository")
if os.path.exists(books_dir):
    app.mount("/books", StaticFiles(directory=books_dir), name="books")
    logger.info(f"Serving books from: {books_dir}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API, MongoDB, and processing services are running"""
    import httpx

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

        # Check Marker and MinerU services (non-blocking, with short timeout)
        services = {}
        for name, port in [("marker", 8002), ("mineru", 8003)]:
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    resp = await client.get(f"http://localhost:{port}/health")
                    services[name] = "healthy" if resp.status_code == 200 else "unhealthy"
            except Exception:
                services[name] = "unavailable"
        stats["services"] = services

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
    
    # Drop legacy single-field text indexes that conflict with the combined
    # PERF-002 text indexes from app.database.mongodb._ensure_indexes
    # (MongoDB allows only ONE text index per collection, so the combined
    # papers_text_search/articles_text_search/tweets_text_search indexes can
    # only be created once these old ones are gone).
    legacy_text_indexes = [
        ("papers", "title_text"),
        ("articles", "title_text"),
        ("tweets", "text_text"),
    ]
    dropped_legacy = False
    for collection_name, index_name in legacy_text_indexes:
        try:
            existing_names = [idx["name"] for idx in db[collection_name].list_indexes()]
            if index_name in existing_names:
                db[collection_name].drop_index(index_name)
                dropped_legacy = True
                logger.info(f"Dropped legacy text index {collection_name}.{index_name}")
        except Exception as e:
            logger.warning(f"Could not drop legacy text index {collection_name}.{index_name}: {e}")

    try:
        # Not covered by app.database.mongodb._ensure_indexes
        db.book_processing_jobs.create_index([("status", ASCENDING), ("created_at", ASCENDING)])
    except Exception as e:
        logger.warning(f"Could not create book_processing_jobs index: {e}")

    if dropped_legacy:
        # Re-run the central index creation now that the conflicting legacy
        # indexes are gone, so the combined text indexes exist immediately
        # instead of only after the next restart.
        try:
            from app.database import mongodb as mongodb_module
            mongodb_module._indexes_initialized = False
            mongodb_module._ensure_indexes(db)
        except Exception as e:
            logger.warning(f"Re-running central index creation failed: {e}")

    logger.info("MongoDB indexes initialized")

    # Surface any saved LLM preferences that point to deprecated/removed models
    # (e.g., after a litellm_config.yaml rename). The frontend can then offer
    # a one-click migration via POST /api/llm/preferences/migrate.
    try:
        from app.services.llm_manager import get_llm_manager
        deprecated = get_llm_manager().find_deprecated_preferences()
        if deprecated:
            logger.warning(
                f"⚠️  {len(deprecated)} LLM preference(s) point to models that no "
                f"longer exist in litellm_config.yaml. UI will offer migration."
            )
            for d in deprecated:
                logger.warning(
                    f"   • user={d['user_id']} task={d['task_type']} "
                    f"current='{d['current_model']}' → suggested='{d['suggested_model']}' "
                    f"(source={d['suggestion_source']})"
                )
    except Exception as e:
        logger.warning(f"Could not check LLM preferences health: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up MongoDB connection on shutdown"""
    mongo_client.close()
    logger.info("MongoDB connection closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.backend_port, reload=True)
