#!/usr/bin/env python3
"""
Run the SmartTrendTracer backend server
"""
import uvicorn
from app.config import API_HOST, API_PORT

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 SmartTrendTracer Backend Starting...")
    print("=" * 60)
    print(f"📡 API Server: http://{API_HOST}:{API_PORT}")
    print(f"📚 API Docs: http://localhost:{API_PORT}/docs")
    print(f"🎨 Dashboard: http://localhost:3470")
    print("=" * 60 + "\n")
    
    uvicorn.run(
        "app.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )