"""
Simplified FastAPI server without tweet collection
Tweet collection is handled by separate service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging

from app.api import tweets, tags, media, trends, collection, tag_ontology, ontology_ai, analytics, substack, export
from app.api import enhanced_tweets, enhanced_substack, unified_trends, entity_extraction, media_gallery, user_trends
from app.api import rag_simple
from app.models import Base, engine

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
app.include_router(entity_extraction.router, prefix="/api/entities", tags=["entity-extraction"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(substack.router, prefix="/api/substack", tags=["substack"])
app.include_router(export.router, prefix="/api/export", tags=["export"])

# Enhanced APIs with faceted browsing
app.include_router(enhanced_tweets.router, prefix="/api/v2/tweets", tags=["enhanced-tweets"])
app.include_router(enhanced_substack.router, prefix="/api/v2/substack", tags=["enhanced-substack"])

# Unified trends and clustering API
app.include_router(unified_trends.router, prefix="/api/unified", tags=["unified-trends"])

# Media Gallery API
app.include_router(media_gallery.router, prefix="/api/media-gallery", tags=["media-gallery"])

# User Trends API
app.include_router(user_trends.router, prefix="/api/user-trends", tags=["user-trends"])

@app.get("/")
def read_root():
    return {
        "message": "SmartTrendTracer API", 
        "version": "2.0.0",
        "docs": "/docs",
        "note": "Tweet collection runs in separate service"
    }

@app.get("/health")
def health_check():
    """Simple health check"""
    return {
        "status": "healthy",
        "server": "running",
        "note": "Tweet collection handled by separate service"
    }

@app.on_event("startup")
async def startup_event():
    """Server startup - no tweet collection"""
    logger.info("SmartTrendTracer API server started")
    logger.info("Tweet collection is handled by separate service (tweet_collector_service.py)")

@app.on_event("shutdown")
async def shutdown_event():
    """Server shutdown"""
    logger.info("SmartTrendTracer API server shutting down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)