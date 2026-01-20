"""
MongoDB-compatible API endpoints for importing articles from URLs

Supports both simple HTTP requests and Playwright-based authenticated collection.
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import html2text
# from readability import Readability  # Optional dependency
from app.database.mongodb import get_database
from app.services.author_service import AuthorService
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


def _check_playwright_available() -> bool:
    """Check if Playwright is installed."""
    try:
        from playwright.async_api import async_playwright
        return True
    except ImportError:
        return False

router = APIRouter()

# MongoDB connection
db = get_database()

# Initialize author service
author_service = AuthorService(db)

class URLImportRequest(BaseModel):
    url: HttpUrl
    
class URLImportResponse(BaseModel):
    success: bool
    article_id: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    word_count: Optional[int] = None
    error: Optional[str] = None

class EnhancedImportRequest(BaseModel):
    url: Optional[HttpUrl] = None  # Optional - can be extracted from curl_command
    curl_command: Optional[str] = None
    cookies: Optional[Dict[str, str]] = None

def extract_article_metadata(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
    """Extract metadata from article HTML"""
    metadata = {
        'title': None,
        'author': None,
        'publication_date': None,
        'description': None
    }
    
    # Try to get title
    if soup.find('meta', property='og:title'):
        metadata['title'] = soup.find('meta', property='og:title')['content']
    elif soup.find('title'):
        metadata['title'] = soup.find('title').text
    
    # Try to get author
    if soup.find('meta', attrs={'name': 'author'}):
        metadata['author'] = soup.find('meta', attrs={'name': 'author'})['content']
    elif soup.find('meta', attrs={'property': 'article:author'}):
        metadata['author'] = soup.find('meta', attrs={'property': 'article:author'})['content']
    elif soup.find('a', class_='author-name'):
        metadata['author'] = soup.find('a', class_='author-name').text
    
    # Try to get publication date
    if soup.find('meta', property='article:published_time'):
        metadata['publication_date'] = soup.find('meta', property='article:published_time')['content']
    elif soup.find('time'):
        time_elem = soup.find('time')
        if time_elem.get('datetime'):
            metadata['publication_date'] = time_elem['datetime']
    
    # Try to get description
    if soup.find('meta', attrs={'name': 'description'}):
        metadata['description'] = soup.find('meta', attrs={'name': 'description'})['content']
    elif soup.find('meta', property='og:description'):
        metadata['description'] = soup.find('meta', property='og:description')['content']
    
    return metadata

def clean_article_content(html_content: str) -> str:
    """Clean and convert HTML to markdown"""
    import urllib.parse
    
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup.find_all(["script", "style"]):
        script.decompose()
    
    # Fix image URLs that might be double-encoded
    for img in soup.find_all('img'):
        if img.get('src'):
            src = img['src']
            # Decode URL if it appears to be encoded
            if '%' in src:
                try:
                    decoded_src = urllib.parse.unquote(src)
                    # Check if it was double-encoded
                    if '%' in decoded_src and decoded_src != src:
                        decoded_src = urllib.parse.unquote(decoded_src)
                    img['src'] = decoded_src
                except:
                    pass  # Keep original if decode fails
    
    # Try to find main content areas
    main_content = None
    content_selectors = [
        'article', 
        'main',
        'div.post-content',
        'div.entry-content',
        'div.content',
        'div.body',
        'div[role="main"]'
    ]
    
    for selector in content_selectors:
        main_content = soup.select_one(selector)
        if main_content:
            break
    
    # If no main content found, use the whole body
    if not main_content:
        main_content = soup.find('body') or soup
    
    # Convert to markdown
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0  # Don't wrap lines
    h.protect_links = True  # Don't escape URLs
    
    markdown_content = h.handle(str(main_content))
    
    # Clean up common artifacts
    markdown_content = markdown_content.replace('\\n', '\n')
    markdown_content = markdown_content.replace('\\_', '_')
    
    # Fix any remaining double-encoded URLs in markdown image syntax
    import re
    def fix_image_url(match):
        url = match.group(2)
        if '%' in url:
            try:
                decoded = urllib.parse.unquote(url)
                if '%' in decoded and decoded != url:
                    decoded = urllib.parse.unquote(decoded)
                return f"![{match.group(1)}]({decoded})"
            except:
                pass
        return match.group(0)
    
    markdown_content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', fix_image_url, markdown_content)
    
    return markdown_content

@router.post("/import-url", response_model=URLImportResponse)
def import_article_from_url(request: URLImportRequest):
    """
    Import an article from a URL
    
    Supports:
    - Substack articles
    - Medium articles
    - Blog posts
    - General web articles
    """
    try:
        url = str(request.url)
        
        # Fetch the article
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract metadata
        metadata = extract_article_metadata(soup, url)
        
        # Clean and convert content to markdown
        markdown_content = clean_article_content(response.text)
        
        # Calculate word count
        word_count = len(markdown_content.split())
        
        # Determine author for Substack
        author = metadata['author']
        if 'substack.com' in url and not author:
            # Try to extract from URL
            import re
            match = re.match(r'https://([^.]+)\.substack\.com', url)
            if match:
                author = match.group(1)

        # Normalize author with AuthorService
        author_raw = author or 'Unknown'
        primary_author_name, co_author_names = author_service.parse_author_string(author_raw)

        # Find or create author records
        primary_author_id = author_service.find_or_create_author(primary_author_name, auto_create=True)
        co_author_ids = [
            author_service.find_or_create_author(name, auto_create=True)
            for name in co_author_names
        ]

        # Create article document with normalized authors
        article_doc = {
            'title': metadata['title'] or 'Untitled',
            'author': author or 'Unknown',  # Keep original for backwards compatibility
            'author_name': primary_author_name,  # Normalized primary author
            'primary_author_id': primary_author_id,  # Reference to authors collection
            'primary_author_name': primary_author_name,  # Denormalized for display
            'co_author_ids': co_author_ids,  # References to co-authors
            'co_author_names': co_author_names,  # Denormalized for display
            'url': url,
            'content_markdown': markdown_content,
            'preview': markdown_content[:500] if markdown_content else '',
            'word_count': word_count,
            'publication_date': metadata['publication_date'],
            'description': metadata['description'],
            'source': 'url_import',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'concept_ids': [],
            'snippets': [],
            'summary': None
        }
        
        # Check if article already exists
        existing = db.articles.find_one({'url': url})
        if existing:
            # Update existing article
            db.articles.update_one(
                {'_id': existing['_id']},
                {'$set': {
                    'content_markdown': markdown_content,
                    'word_count': word_count,
                    'updated_at': datetime.utcnow()
                }}
            )
            article_id = str(existing['_id'])
        else:
            # Insert new article
            result = db.articles.insert_one(article_doc)
            article_id = str(result.inserted_id)

            # Update author statistics
            author_service.update_author_stats(primary_author_id)
            for co_author_id in co_author_ids:
                author_service.update_author_stats(co_author_id)

        return URLImportResponse(
            success=True,
            article_id=article_id,
            title=metadata['title'],
            author=author,
            word_count=word_count
        )
        
    except Exception as e:
        logger.error(f"Error importing article from {request.url}: {e}")
        return URLImportResponse(
            success=False,
            error=str(e)
        )

@router.post("/enhanced-import", response_model=URLImportResponse)
def import_article_enhanced(request: EnhancedImportRequest):
    """
    Enhanced import with authentication support
    
    Allows importing articles behind paywalls using:
    - cURL command with cookies
    - Direct cookie dictionary
    """
    try:
        import shlex
        import re

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        # Parse cookies and URL from curl command if provided
        cookies = {}
        url = str(request.url) if request.url else None

        if request.curl_command:
            # Parse curl command
            parts = shlex.split(request.curl_command)

            # Extract URL from curl command if not provided
            if not url:
                for part in parts:
                    # URL is usually the last argument or after 'curl'
                    if part.startswith('http://') or part.startswith('https://'):
                        url = part
                        break
                # Also check for URL in quotes
                if not url:
                    url_match = re.search(r'["\']?(https?://[^\s"\']+)["\']?', request.curl_command)
                    if url_match:
                        url = url_match.group(1)

            # Extract cookies from headers
            for i, part in enumerate(parts):
                if part == '-H' and i + 1 < len(parts):
                    header = parts[i + 1]
                    if header.startswith('Cookie:'):
                        cookie_str = header[7:].strip()
                        for cookie_pair in cookie_str.split(';'):
                            if '=' in cookie_pair:
                                key, value = cookie_pair.strip().split('=', 1)
                                cookies[key] = value
        elif request.cookies:
            cookies = request.cookies

        # Validate URL
        if not url:
            return URLImportResponse(
                success=False,
                error="No URL provided. Either provide a URL or a cURL command containing the URL."
            )
        
        # Fetch the article with cookies
        response = requests.get(url, headers=headers, cookies=cookies)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract metadata
        metadata = extract_article_metadata(soup, url)
        
        # For Substack, try to get better content extraction
        content = None
        if 'substack.com' in url:
            # Try to find the main article content
            article_elem = soup.find('div', class_='post-content')
            if not article_elem:
                article_elem = soup.find('div', class_='body')
            if not article_elem:
                article_elem = soup.find('article')
            
            if article_elem:
                # Remove unwanted elements
                for elem in article_elem.find_all(['script', 'style', 'button', 'form']):
                    elem.decompose()
                content = str(article_elem)
        
        # If no specific content found, use full HTML
        if not content:
            content = response.text
        
        # Clean and convert content to markdown
        markdown_content = clean_article_content(content)
        
        # Calculate word count
        word_count = len(markdown_content.split())
        
        # Determine author
        author = metadata['author']
        if 'substack.com' in url and not author:
            # Try to extract from URL
            import re
            match = re.match(r'https://([^.]+)\.substack\.com', url)
            if match:
                author = match.group(1)

        # Normalize author with AuthorService
        author_raw = author or 'Unknown'
        primary_author_name, co_author_names = author_service.parse_author_string(author_raw)

        # Find or create author records
        primary_author_id = author_service.find_or_create_author(primary_author_name, auto_create=True)
        co_author_ids = [
            author_service.find_or_create_author(name, auto_create=True)
            for name in co_author_names
        ]

        # Create article document with normalized authors
        article_doc = {
            'title': metadata['title'] or 'Untitled',
            'author': author or 'Unknown',  # Keep original for backwards compatibility
            'author_name': primary_author_name,  # Normalized primary author
            'primary_author_id': primary_author_id,  # Reference to authors collection
            'primary_author_name': primary_author_name,  # Denormalized for display
            'co_author_ids': co_author_ids,  # References to co-authors
            'co_author_names': co_author_names,  # Denormalized for display
            'url': url,
            'content_markdown': markdown_content,
            'preview': markdown_content[:500] if markdown_content else '',
            'word_count': word_count,
            'publication_date': metadata['publication_date'],
            'description': metadata['description'],
            'source': 'enhanced_import',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'concept_ids': [],
            'snippets': [],
            'summary': None,
            'authenticated': bool(cookies)  # Mark if we used authentication
        }
        
        # Check if article already exists
        existing = db.articles.find_one({'url': url})
        if existing:
            # Update existing article
            db.articles.update_one(
                {'_id': existing['_id']},
                {'$set': {
                    'content_markdown': markdown_content,
                    'word_count': word_count,
                    'updated_at': datetime.utcnow(),
                    'authenticated': bool(cookies)
                }}
            )
            article_id = str(existing['_id'])
        else:
            # Insert new article
            result = db.articles.insert_one(article_doc)
            article_id = str(result.inserted_id)

            # Update author statistics
            author_service.update_author_stats(primary_author_id)
            for co_author_id in co_author_ids:
                author_service.update_author_stats(co_author_id)

        return URLImportResponse(
            success=True,
            article_id=article_id,
            title=metadata['title'],
            author=author,
            word_count=word_count
        )
        
    except Exception as e:
        logger.error(f"Error in enhanced import for {request.url}: {e}")
        return URLImportResponse(
            success=False,
            error=str(e)
        )

@router.post("/enhanced/check-paywall")
def check_paywall(request: URLImportRequest):
    """Check if an article is behind a paywall"""
    try:
        response = requests.head(str(request.url), allow_redirects=True)
        # Simple heuristic - if we get redirected to a login page or get 403, it's likely paywalled
        is_paywalled = (
            response.status_code == 403 or
            'login' in response.url.lower() or
            'subscribe' in response.url.lower() or
            'paywall' in response.headers.get('x-frame-options', '').lower()
        )
        return {"is_paywalled": is_paywalled}
    except:
        return {"is_paywalled": False}

@router.post("/enhanced/import-basic")
def import_basic(request: URLImportRequest):
    """Basic import without authentication (same as regular import)"""
    return import_article_from_url(request)

@router.post("/enhanced/import-with-cookie-string")
def import_with_cookie_string(request: dict):
    """Import with cookie string"""
    url = request.get('url')
    cookie_string = request.get('cookieString', '')
    
    # Parse cookie string
    cookies = {}
    for cookie_pair in cookie_string.split(';'):
        if '=' in cookie_pair:
            key, value = cookie_pair.strip().split('=', 1)
            cookies[key] = value
    
    enhanced_request = EnhancedImportRequest(
        url=url,
        cookies=cookies
    )
    return import_article_enhanced(enhanced_request)

@router.post("/enhanced/import-with-cookies")
def import_with_cookies(request: dict):
    """Import with parsed cookies dictionary"""
    url = request.get('url')
    cookies = request.get('cookies', {})
    
    enhanced_request = EnhancedImportRequest(
        url=url,
        cookies=cookies
    )
    return import_article_enhanced(enhanced_request)

@router.post("/import-batch")
def import_batch(urls: list[str]):
    """Import multiple articles at once"""
    results = []
    for url in urls:
        try:
            request = URLImportRequest(url=url)
            result = import_article_from_url(request)
            results.append(result.dict())
        except Exception as e:
            results.append({
                "success": False,
                "url": url,
                "error": str(e)
            })
    return {"results": results}

@router.get("/test")
def test_import_endpoint():
    """Test if the import endpoints are working"""
    return {"status": "ok", "message": "Article import endpoints are active"}


# ============================================================================
# Playwright-based authenticated article collection endpoints
# ============================================================================

@router.get("/auth-sites")
def list_supported_auth_sites():
    """
    List sites that support authenticated collection.

    Returns list of supported sites with their login URLs and session status.
    """
    try:
        from app.collectors.playwright_collector.session_manager import (
            SessionManager, SUPPORTED_SITES
        )

        sm = SessionManager()
        sessions = sm.list_sessions()

        sites = []
        for key, config in SUPPORTED_SITES.items():
            sites.append({
                'key': key,
                'name': config['name'],
                'login_url': config['login_url'],
                'has_session': key in sessions,
                'session_info': sessions.get(key)
            })

        return {
            'sites': sites,
            'playwright_installed': _check_playwright_available()
        }

    except Exception as e:
        logger.error(f"Failed to list auth sites: {e}")
        return {
            'sites': [],
            'playwright_installed': _check_playwright_available(),
            'error': str(e)
        }


@router.get("/auth-status/{site}")
async def get_auth_status(site: str):
    """
    Check authentication status for a site.

    Returns whether we have valid saved credentials for sites like
    Substack, Medium, etc.

    Path params:
    - site: Site identifier (substack, medium, patreon)
    """
    if not _check_playwright_available():
        return {
            'site': site,
            'supported': False,
            'authenticated': False,
            'error': "Playwright not installed"
        }

    try:
        from app.collectors.playwright_collector import PlaywrightCollector

        collector = PlaywrightCollector()
        try:
            status = await collector.check_auth_status(site)
            return status
        finally:
            await collector.close()

    except Exception as e:
        logger.error(f"Failed to check auth status: {e}")
        return {
            'site': site,
            'supported': False,
            'authenticated': False,
            'error': str(e)
        }


@router.post("/start-auth/{site}")
async def start_auth_flow(site: str):
    """
    Start interactive authentication flow - opens a browser window.

    This endpoint spawns a visible browser for the user to log in.
    Works because frontend and backend run on the same local machine.

    Path params:
    - site: Site identifier (substack, medium, patreon)
    """
    if not _check_playwright_available():
        raise HTTPException(
            status_code=503,
            detail="Playwright not installed. Run: pip install playwright && playwright install chromium"
        )

    try:
        from app.collectors.playwright_collector.session_manager import SUPPORTED_SITES
        from app.collectors.playwright_collector import PlaywrightCollector

        site_config = SUPPORTED_SITES.get(site)
        if not site_config:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown site: {site}. Supported: {list(SUPPORTED_SITES.keys())}"
            )

        # Open browser for authentication (headless=False shows the window)
        collector = PlaywrightCollector(headless=False)
        try:
            logger.info(f"Starting interactive authentication for {site}")
            success = await collector.authenticate(site, timeout_seconds=300)

            return {
                'success': success,
                'site': site,
                'name': site_config['name'],
                'message': f"Authentication {'successful' if success else 'failed or timed out'} for {site_config['name']}"
            }
        finally:
            await collector.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to authenticate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/auth/{site}")
def clear_auth_session(site: str):
    """
    Clear saved authentication session for a site.

    Path params:
    - site: Site identifier (substack, medium, patreon)
    """
    try:
        from app.collectors.playwright_collector.session_manager import SessionManager

        sm = SessionManager()
        success = sm.delete_session(site)

        return {
            'success': success,
            'message': f"Session cleared for {site}" if success else f"No session found for {site}"
        }

    except Exception as e:
        logger.error(f"Failed to clear session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-url-playwright")
async def import_article_playwright(request: Dict[str, Any] = Body(...)):
    """
    Import an article from URL using Playwright browser automation.

    Uses saved session cookies for authenticated access to Substack, Medium, etc.

    Request body:
    - url: Article URL to import

    Returns:
    - success: Whether import was successful
    - article_id: MongoDB ID if saved
    - title, author, word_count, etc.
    - requires_auth: True if authentication is needed
    - site: Site that requires auth (e.g., 'substack')
    """
    if not _check_playwright_available():
        raise HTTPException(
            status_code=503,
            detail="Playwright not installed. Run: pip install playwright && playwright install chromium"
        )

    url = request.get('url')
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    try:
        from app.collectors.playwright_collector import PlaywrightCollector

        collector = PlaywrightCollector()
        try:
            result = await collector.fetch_article(url)

            if not result.get('success'):
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to fetch article'),
                    'requires_auth': result.get('requires_auth', False),
                    'site': result.get('site'),
                    'auth_url': result.get('auth_url')
                }

            # Check if article already exists
            existing = db.articles.find_one({'url': url})
            if existing:
                return {
                    'success': True,
                    'article_id': str(existing['_id']),
                    'title': existing.get('title'),
                    'author': existing.get('author_name'),
                    'word_count': existing.get('word_count', 0),
                    'already_exists': True
                }

            # Save to database
            doc = {
                'title': result.get('title'),
                'subtitle': result.get('subtitle'),
                'url': url,
                'author_name': result.get('author'),
                'author_url': result.get('author_url'),
                'published_at': result.get('published_at'),
                'content_html': result.get('content_html'),
                'content_markdown': result.get('content_markdown'),
                'preview': result.get('preview'),
                'word_count': result.get('word_count', 0),
                'reading_time_minutes': result.get('reading_time_minutes', 0),
                'source': 'playwright_collector',
                'source_site': result.get('source_site'),
                'has_paywall': result.get('has_paywall', False),
                'collected_at': datetime.utcnow(),
                'created_at': datetime.utcnow(),
            }

            insert_result = db.articles.insert_one(doc)

            return {
                'success': True,
                'article_id': str(insert_result.inserted_id),
                'title': result.get('title'),
                'author': result.get('author'),
                'word_count': result.get('word_count', 0),
                'reading_time_minutes': result.get('reading_time_minutes', 0),
                'has_paywall': result.get('has_paywall', False)
            }

        finally:
            await collector.close()

    except Exception as e:
        logger.error(f"Failed to import article from URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))
