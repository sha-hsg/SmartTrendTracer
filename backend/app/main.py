from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging

from app.api import tweets, tags, media, trends, collection, tag_ontology, ontology_ai, analytics, substack, background
from app.api import enhanced_tweets, enhanced_substack, rag_simple, pdf_export, tag_reorganization, unified_trends, media_gallery, user_trends
from app.api import entity_extraction, statistics, papers, paper_trends, paper_advanced
from app.models import Base, engine
from app.scheduler import start_scheduler, stop_scheduler
from app.smart_startup_collector import smart_collect_on_startup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="SmartTrendTracer API",
    description="AI-powered Twitter/X topic and trend detection system",
    version="2.0.0"
)

# Global scheduler instance
scheduler = None

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for media
if os.path.exists("data/media"):
    app.mount("/media", StaticFiles(directory="data/media"), name="media")

# Include API routers
app.include_router(tweets.router, prefix="/api/tweets", tags=["tweets"])
app.include_router(tags.router, prefix="/api/tags", tags=["tags"])
app.include_router(media.router, prefix="/api/media", tags=["media"])
app.include_router(trends.router, prefix="/api/trends", tags=["trends"])
app.include_router(collection.router, prefix="/api/collection", tags=["collection"])
app.include_router(tag_ontology.router, prefix="/api/ontology", tags=["ontology"])
app.include_router(ontology_ai.router, prefix="/api/ontology/ai", tags=["ontology-ai"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(substack.router, prefix="/api/substack", tags=["substack"])
app.include_router(background.router, prefix="/api/background", tags=["background"])

# Enhanced APIs with faceted browsing
app.include_router(enhanced_tweets.router, prefix="/api/v2/tweets", tags=["enhanced-tweets"])
app.include_router(enhanced_substack.router, prefix="/api/v2/substack", tags=["enhanced-substack"])

# RAG API for AI-powered search
app.include_router(rag_simple.router, prefix="/api/rag", tags=["rag"])

# PDF Export API
app.include_router(pdf_export.router, prefix="/api/pdf", tags=["pdf-export"])

# Tag Reorganization API (Gemini 2.5 Pro)
app.include_router(tag_reorganization.router, prefix="/api/tags/reorganize", tags=["tag-reorganization"])

# Unified Trends API
app.include_router(unified_trends.router, prefix="/api/unified", tags=["unified-trends"])

# Media Gallery API
app.include_router(media_gallery.router, prefix="/api/media-gallery", tags=["media-gallery"])

# User Trends API
app.include_router(user_trends.router, prefix="/api/user-trends", tags=["user-trends"])

# Entity Extraction API
app.include_router(entity_extraction.router, prefix="/api/entities", tags=["entity-extraction"])

# Statistics API
app.include_router(statistics.router, prefix="/api/statistics", tags=["statistics"])

# Papers API
app.include_router(papers.router, tags=["papers"])

# Paper Trends API
app.include_router(paper_trends.router, tags=["paper-trends"])

# Paper Advanced Features API
app.include_router(paper_advanced.router, tags=["paper-advanced"])

@app.get("/")
def read_root():
    return {
        "message": "SmartTrendTracer API", 
        "version": "2.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    """Health check endpoint with collection status"""
    try:
        from app.background_tasks import get_collection_status
        collection_status = get_collection_status()
    except:
        collection_status = {"in_progress": False, "rate_limited": False}
    
    return {
        "status": "healthy",
        "collection": collection_status
    }

@app.on_event("startup")
async def startup_event():
    """Start the scheduler and initiate background tweet collection"""
    global scheduler
    
    # Start tweet collection in background (non-blocking)
    try:
        from app.background_tasks import start_background_collection
        await start_background_collection()
        logger.info("Background tweet collection initiated")
    except Exception as e:
        logger.error(f"Failed to start background collection: {e}")
    
    # Start the regular scheduler immediately (non-blocking)
    try:
        scheduler = start_scheduler()
        logger.info("Tweet collection scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the scheduler and background tasks"""
    global scheduler
    
    logger.info("Initiating graceful shutdown...")
    
    # Shutdown background tasks
    try:
        from app.background_tasks import shutdown_background_tasks
        shutdown_background_tasks()
        logger.info("Background tasks shutdown complete")
    except Exception as e:
        logger.error(f"Failed to shutdown background tasks: {e}")
    
    # Stop the scheduler
    if scheduler:
        try:
            stop_scheduler(scheduler)
            logger.info("Tweet collection scheduler stopped")
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {e}")
    
    # Record the shutdown time
    try:
        from app.models import CollectionState, get_db
        db = next(get_db())
        CollectionState.update_last_run(db, tweet_count=0)
        db.close()
        logger.info("Recorded shutdown time for next startup")
    except Exception as e:
        logger.error(f"Failed to record shutdown time: {e}")
    
    logger.info("Graceful shutdown complete")