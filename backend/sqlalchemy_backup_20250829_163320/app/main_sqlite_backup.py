"""
Updated main.py that uses MongoDB for all tag operations.
This replaces the existing main.py to complete the migration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging

# Import the concept-only API modules
from app.api import tweets_concepts as tweets  # Use concept-only version
from app.api import tags_mongodb as tags  # Use MongoDB version
from app.api import media, trends, collection, ontology_ai, analytics, background
from app.api import enhanced_tweets, enhanced_substack, pdf_export, tag_reorganization, tags_reorganization, unified_trends, media_gallery, user_trends
from app.api import rag_concepts  # Use concept-based RAG instead of rag_simple
from app.api import entity_extraction, papers_concepts, paper_trends, paper_advanced
from app.api import statistics_concepts as statistics  # Use concept-based statistics
from app.api import tags_v2  # New unified tag system
from app.api import ontology_graph  # Ontology graph visualization
from app.api import arxiv  # ArXiv import functionality
from app.api import paper_repository  # Paper repository and analyses
from app.api import article_clustering  # Article clustering based on tags
from app.api import tag_import_export  # Tag import/export functionality
from app.api import tags_unified  # Unified tag concept API

# Import substack with MongoDB support
from app.api import substack
from app.api import substack_concepts
from app.api import tag_reorganization_async

# Import the MongoDB tag service for initialization
from app.services.mongodb_tag_service import MongoDBTagService

# Import models for SQLite tables (still needed for non-tag data)
from app.models import Base, engine

# Configure logging with better format for debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize MongoDB tag service
mongo_tag_service = MongoDBTagService()
logger.info("MongoDB tag service initialized")

# Create SQLite database tables (for non-tag data)
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="SmartTrendTracer API (MongoDB Edition)",
    description="AI-powered Twitter/X topic and trend detection system with MongoDB tag management",
    version="3.0.0"
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

# Include API routers with MongoDB support
app.include_router(tweets.router, prefix="/api/tweets", tags=["tweets"])
app.include_router(tags.router, prefix="/api/tags", tags=["tags"])

# Concept suggestions API
from app.api import concepts_suggestions
app.include_router(concepts_suggestions.router, prefix="/api/concepts/suggestions", tags=["concept-suggestions"])
app.include_router(media.router, prefix="/api/media", tags=["media"])
app.include_router(trends.router, prefix="/api/trends", tags=["trends"])
app.include_router(collection.router, prefix="/api/collection", tags=["collection"])

# Use v2 ontology API with MongoDB
from app.api import tag_ontology_v2_mongodb
app.include_router(tag_ontology_v2_mongodb.router, prefix="/api/ontology", tags=["ontology"])
app.include_router(ontology_ai.router, prefix="/api/ontology/ai", tags=["ontology-ai"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(substack.router, prefix="/api/substack", tags=["substack"])
app.include_router(substack_concepts.router, prefix="/api/articles", tags=["articles-concepts"])
app.include_router(background.router, prefix="/api/background", tags=["background"])

# Enhanced APIs with faceted browsing
app.include_router(enhanced_tweets.router, prefix="/api/v2/tweets", tags=["enhanced-tweets"])
app.include_router(enhanced_substack.router, prefix="/api/v2/substack", tags=["enhanced-substack"])

# Article Import API
from app.api import article_import
app.include_router(article_import.router, prefix="/api/v2/articles", tags=["article-import"])

# Enhanced Article Import API with cookie authentication
from app.api import article_import_enhanced
app.include_router(article_import_enhanced.router, prefix="/api/v2/articles/enhanced", tags=["article-import-enhanced"])

# RAG API for AI-powered search with concept integration
app.include_router(rag_concepts.router, tags=["rag-concepts"])

# PDF Export API
app.include_router(pdf_export.router, prefix="/api/pdf", tags=["pdf-export"])

# Tag Reorganization API (GPT-5 Enhanced)
app.include_router(tag_reorganization.router, prefix="/api/tags/reorganize", tags=["tag-reorganization"])
app.include_router(tags_reorganization.router, prefix="/api/tags/comprehensive", tags=["comprehensive-reorganization"])
app.include_router(tag_reorganization_async.router, prefix="/api/tag-reorganization", tags=["tag-reorganization-async"])

# Tag Import/Export API
app.include_router(tag_import_export.router, prefix="/api/tags/io", tags=["tag-import-export"])

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

# Papers API with concepts (already has /api/papers prefix in router)
app.include_router(papers_concepts.router, tags=["papers-concepts"])

# Paper Images API
from app.api import paper_images
app.include_router(paper_images.router, tags=["paper-images"])

# Async Papers Upload API
from app.api import papers_async
app.include_router(papers_async.router, tags=["papers-async"])

# ArXiv Import API (already has /api/arxiv prefix in router)
app.include_router(arxiv.router, tags=["arxiv"])

# Paper Repository API (already has /api/papers/repository prefix in router)
app.include_router(paper_repository.router, tags=["paper-repository"])

# Paper Trends API (already has /api/papers/trends prefix in router)
app.include_router(paper_trends.router, tags=["paper-trends"])

# Paper Advanced Features API (already has /api/papers/advanced prefix in router)
app.include_router(paper_advanced.router, tags=["paper-advanced"])

# Article Clustering API
app.include_router(article_clustering.router, prefix="/api/articles/clustering", tags=["article-clustering"])

# DBLP API
from app.api import dblp
app.include_router(dblp.router, prefix="/api/dblp", tags=["dblp"])

# ACL Anthology API
from app.api import acl_anthology
app.include_router(acl_anthology.router, prefix="/api/acl-anthology", tags=["acl-anthology"])

# New Unified Tag System v2 API
app.include_router(tags_v2.router, tags=["tags-v2"])

# Unified Tag Concept API - New structure with concepts and aliases
app.include_router(tags_unified.router, prefix="/api/tags-concept", tags=["tags-concept"])

# Ontology Graph Visualization API
app.include_router(ontology_graph.router, tags=["ontology-graph"])

# Orphan Tags Assignment API (separate from full reorganization)
from app.api import orphan_tags
app.include_router(orphan_tags.router, tags=["orphan-tags"])

# Async Tag Reorganization API with SSE
app.include_router(tag_reorganization_async.router, prefix="/api/tag-reorganization", tags=["tag-reorganization-async"])

# Tag Reorganization Apply API
from app.api import tag_reorganization_apply
app.include_router(tag_reorganization_apply.router, prefix="/api/tag-reorganization", tags=["tag-reorganization-apply"])

# Comprehensive Tag Reorganization API
from app.api import tag_reorganization_comprehensive
app.include_router(tag_reorganization_comprehensive.router, prefix="/api/tag-reorganization", tags=["tag-reorganization-comprehensive"])

@app.get("/")
async def root():
    """Root endpoint with system info"""
    return {
        "message": "SmartTrendTracer API (MongoDB Edition)",
        "version": "3.0.0",
        "tag_system": "MongoDB",
        "database": {
            "tags": "MongoDB (tag_instances collection)",
            "content": "SQLite (tweets, papers, articles)"
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check MongoDB connection
        mongo_stats = {
            "total_tags": len(mongo_tag_service.get_all_tags_with_counts()),
            "orphan_tags": len(mongo_tag_service.get_orphan_tags())
        }
        
        return {
            "status": "healthy",
            "mongodb": "connected",
            "tag_stats": mongo_stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting SmartTrendTracer API with MongoDB tag system...")
    logger.info("Tag data is now stored in MongoDB tag_instances collection")
    logger.info("All tag operations use MongoDB for consistency")
    uvicorn.run(app, host="0.0.0.0", port=8000)