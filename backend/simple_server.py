#!/usr/bin/env python3
"""
Simple server without complex startup collection
Just serves the API, no automatic collection
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

from app.api import tweets, tags, media, trends, collection, analytics
from app.models import Base, engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="SmartTrendTracer API (Simple Mode)",
    description="Simple API server without auto-collection",
    version="2.0.0"
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(tweets.router, prefix="/api/tweets", tags=["tweets"])
app.include_router(tags.router, prefix="/api/tags", tags=["tags"])
app.include_router(media.router, prefix="/api/media", tags=["media"])
app.include_router(trends.router, prefix="/api/trends", tags=["trends"])
app.include_router(collection.router, prefix="/api/collection", tags=["collection"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

@app.get("/")
def read_root():
    return {
        "message": "SmartTrendTracer Simple API",
        "mode": "simple",
        "collection": "manual only",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "mode": "simple"}

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 SmartTrendTracer SIMPLE Server")
    print("=" * 60)
    print("📡 API Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🎨 Dashboard: http://localhost:3000")
    print("\n⚠️  Simple Mode:")
    print("  • NO automatic collection on startup")
    print("  • NO scheduled collection")
    print("  • NO rate limiter waits")
    print("\n📝 To collect tweets manually:")
    print("  python collect_tweets.py")
    print("\n🛑 To stop: Just press Ctrl+C (works immediately!)")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")