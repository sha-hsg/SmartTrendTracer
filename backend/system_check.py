#!/usr/bin/env python3
"""
System Health Check for SmartTrendTracer
Tests all major components and reports status
"""
import sys
import requests
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import subprocess

def colored_text(text, color):
    """Return colored text for terminal output"""
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"

def check_service(name, url, expected_status=200):
    """Check if a service is running"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == expected_status:
            return True, f"{colored_text('✓', 'green')} {name} is running"
        else:
            return False, f"{colored_text('✗', 'red')} {name} returned status {response.status_code}"
    except requests.ConnectionError:
        return False, f"{colored_text('✗', 'red')} {name} is not responding"
    except Exception as e:
        return False, f"{colored_text('✗', 'red')} {name} error: {e}"

def check_database():
    """Check database connectivity and content"""
    try:
        db_path = Path("data/tweets.db")
        if not db_path.exists():
            return False, f"{colored_text('✗', 'red')} Database not found"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM tweets")
        tweet_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM substack_articles")
        article_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tags")
        tag_count = cursor.fetchone()[0]
        
        conn.close()
        
        status = f"{colored_text('✓', 'green')} Database connected"
        details = f"  - Tweets: {tweet_count}\n  - Articles: {article_count}\n  - Tags: {tag_count}"
        return True, f"{status}\n{details}"
        
    except Exception as e:
        return False, f"{colored_text('✗', 'red')} Database error: {e}"

def check_api_endpoints():
    """Test key API endpoints"""
    endpoints = [
        ("Tweets API", "http://localhost:8000/api/tweets/?limit=1"),
        ("Substack API", "http://localhost:8000/api/substack/articles?limit=1"),
        ("Tags API", "http://localhost:8000/api/tags/"),
        ("Trends API", "http://localhost:8000/api/trends/recent"),
    ]
    
    results = []
    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data:
                    results.append(f"  {colored_text('✓', 'green')} {name}")
                else:
                    results.append(f"  {colored_text('⚠', 'yellow')} {name} (empty response)")
            else:
                results.append(f"  {colored_text('✗', 'red')} {name} (status {response.status_code})")
        except Exception as e:
            results.append(f"  {colored_text('✗', 'red')} {name} (error)")
    
    return True, "\n".join(results)

def check_configuration():
    """Check configuration files"""
    configs = [
        ("LLM Config", "llm.json"),
        ("Prompts Config", "prompts_config.json"),
        ("Forwarded Authors", "forwarded_authors.json"),
        ("Environment", ".env"),
    ]
    
    results = []
    for name, filename in configs:
        path = Path(filename)
        if path.exists():
            size = path.stat().st_size
            if size > 0:
                results.append(f"  {colored_text('✓', 'green')} {name} ({size} bytes)")
            else:
                results.append(f"  {colored_text('⚠', 'yellow')} {name} (empty file)")
        else:
            results.append(f"  {colored_text('✗', 'red')} {name} (not found)")
    
    return True, "\n".join(results)

def check_recent_activity():
    """Check recent collection activity"""
    try:
        db_path = Path("data/tweets.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check latest tweet
        cursor.execute("""
            SELECT MAX(created_at) as latest, 
                   COUNT(*) as today_count 
            FROM tweets 
            WHERE date(created_at) = date('now')
        """)
        tweet_data = cursor.fetchone()
        
        # Check latest article
        cursor.execute("""
            SELECT MAX(collected_at) as latest,
                   COUNT(*) as today_count
            FROM substack_articles
            WHERE date(collected_at) = date('now')
        """)
        article_data = cursor.fetchone()
        
        conn.close()
        
        results = []
        
        if tweet_data[0]:
            results.append(f"  Latest tweet: {tweet_data[0]}")
            results.append(f"  Today's tweets: {tweet_data[1]}")
        else:
            results.append(f"  {colored_text('⚠', 'yellow')} No tweets collected today")
        
        if article_data[0]:
            results.append(f"  Latest article: {article_data[0][:19]}")
            results.append(f"  Today's articles: {article_data[1]}")
        else:
            results.append(f"  {colored_text('⚠', 'yellow')} No articles collected today")
        
        return True, "\n".join(results)
        
    except Exception as e:
        return False, f"{colored_text('✗', 'red')} Could not check activity: {e}"

def main():
    print("=" * 60)
    print(f"{colored_text('SmartTrendTracer System Health Check', 'blue')}")
    print("=" * 60)
    print(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    # Check services
    print(f"{colored_text('1. Services', 'blue')}")
    success, msg = check_service("Backend API", "http://localhost:8000/health")
    print(msg)
    success, msg = check_service("Frontend", "http://localhost:3000")
    print(msg)
    print()
    
    # Check database
    print(f"{colored_text('2. Database', 'blue')}")
    success, msg = check_database()
    print(msg)
    print()
    
    # Check API endpoints
    print(f"{colored_text('3. API Endpoints', 'blue')}")
    success, msg = check_api_endpoints()
    print(msg)
    print()
    
    # Check configuration
    print(f"{colored_text('4. Configuration Files', 'blue')}")
    success, msg = check_configuration()
    print(msg)
    print()
    
    # Check recent activity
    print(f"{colored_text('5. Recent Activity', 'blue')}")
    success, msg = check_recent_activity()
    print(msg)
    print()
    
    # Summary
    print("=" * 60)
    print(f"{colored_text('Summary:', 'blue')}")
    
    # Check if everything is working
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        health = response.json()
        
        if health['status'] == 'healthy':
            print(f"{colored_text('✓ System is operational', 'green')}")
            
            if health['collection'].get('rate_limited'):
                print(f"{colored_text('⚠ Tweet collection is rate-limited', 'yellow')}")
            
            print(f"\nYou can access the application at:")
            print(f"  {colored_text('http://localhost:3000', 'blue')}")
            print(f"\nAvailable views:")
            print(f"  - Twitter Dashboard: http://localhost:3000/")
            print(f"  - Substack Articles: http://localhost:3000/substack")
            print(f"  - Tag Management: http://localhost:3000/tags")
            print(f"  - Trends Analysis: http://localhost:3000/trends")
        else:
            print(f"{colored_text('⚠ System has issues', 'yellow')}")
            
    except:
        print(f"{colored_text('✗ Backend is not responding', 'red')}")
        print(f"\nTo start the system:")
        print(f"  1. Backend: cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload")
        print(f"  2. Frontend: cd frontend && npm start")
    
    print("=" * 60)

if __name__ == "__main__":
    main()