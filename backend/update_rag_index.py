#!/usr/bin/env python3
"""
Update RAG Index Script
Convenient ways to update the RAG index when new documents are added
"""
import sys
import requests
import argparse
from datetime import datetime
import os

def update_via_api(force=False):
    """Update index via API endpoint"""
    try:
        if force:
            print("🔄 Force rebuilding RAG index via API...")
            response = requests.post("http://localhost:8000/api/rag/rebuild")
        else:
            print("📊 Updating RAG index via API...")
            response = requests.post("http://localhost:8000/api/rag/build")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result.get('message', 'Index update initiated')}")
            if 'status' in result:
                status = result['status']
                print(f"   Documents: {status.get('total_documents', 0)}")
                print(f"   Ready: {status.get('is_ready', False)}")
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"   Make sure the server is running: python -m uvicorn app.main:app --port 8000")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server")
        print("   Start the server first: python -m uvicorn app.main:app --port 8000")
        return False
    return True

def update_via_script():
    """Update index by running the build script directly"""
    print("🔨 Building RAG index directly...")
    print("   Using Gemini embeddings" if os.getenv('GOOGLE_API_KEY') else "   Using OpenAI embeddings")
    
    import subprocess
    result = subprocess.run(
        ["python", "build_rag_index.py"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Index built successfully")
        # Parse output for stats
        for line in result.stdout.split('\n'):
            if 'documents' in line.lower() or 'built' in line.lower():
                print(f"   {line.strip()}")
    else:
        print(f"❌ Build failed: {result.stderr}")
        return False
    return True

def check_status():
    """Check current index status"""
    try:
        response = requests.get("http://localhost:8000/api/rag/stats")
        if response.status_code == 200:
            stats = response.json()
            print("\n📊 Current RAG Index Status:")
            print(f"   Total documents: {stats.get('indexed_documents', 0)}")
            print(f"   Index ready: {stats.get('is_ready', False)}")
            print(f"   Building: {stats.get('is_building', False)}")
            if stats.get('current_step'):
                print(f"   Status: {stats.get('current_step')}")
            print(f"   Progress: {stats.get('progress_percent', 0)}%")
            
            # Check embedding model
            if os.getenv('GOOGLE_API_KEY'):
                print(f"   Embedding model: Gemini (text-embedding-004)")
            elif os.getenv('OPENAI_API_KEY'):
                print(f"   Embedding model: OpenAI (text-embedding-ada-002)")
            
            # Check if update needed
            last_updated = stats.get('last_updated')
            if last_updated:
                from datetime import datetime, timezone
                # Handle both ISO format with T and without Z
                if 'T' in last_updated:
                    last = datetime.fromisoformat(last_updated.replace('Z', ''))
                    if last.tzinfo is None:
                        last = last.replace(tzinfo=timezone.utc)
                else:
                    last = datetime.fromisoformat(last_updated)
                age = datetime.now(timezone.utc) - last
                hours = age.total_seconds() / 3600
                print(f"   Last updated: {hours:.1f} hours ago")
                
                if hours > 24:
                    print("\n⚠️  Index is more than 24 hours old, consider updating")
            return stats
    except Exception as e:
        print(f"❌ Could not get index status: {e}")
    return None

def main():
    parser = argparse.ArgumentParser(description='Update RAG index for SmartTrendTracer')
    parser.add_argument('--method', choices=['api', 'direct', 'auto'], default='auto',
                        help='Update method: api (via server), direct (run script), auto (try api first)')
    parser.add_argument('--force', action='store_true',
                        help='Force complete rebuild instead of incremental update')
    parser.add_argument('--status', action='store_true',
                        help='Just show current index status')
    
    args = parser.parse_args()
    
    print("🚀 SmartTrendTracer RAG Index Updater")
    print("=" * 50)
    
    # Show current status
    stats = check_status()
    
    if args.status:
        return
    
    print("\n🔄 Starting index update...")
    
    success = False
    if args.method == 'api':
        success = update_via_api(args.force)
    elif args.method == 'direct':
        success = update_via_script()
    else:  # auto
        # Try API first, fall back to direct
        success = update_via_api(args.force)
        if not success:
            print("\n📝 Falling back to direct build...")
            success = update_via_script()
    
    if success:
        print("\n✅ Index update complete!")
        # Show new status
        check_status()
    else:
        print("\n❌ Index update failed")
        print("\nTroubleshooting:")
        print("1. Make sure the server is running: python -m uvicorn app.main:app --port 8000")
        print("2. Check that GOOGLE_API_KEY or OPENAI_API_KEY is set")
        print("3. Try direct build: python build_rag_index.py")

if __name__ == "__main__":
    main()