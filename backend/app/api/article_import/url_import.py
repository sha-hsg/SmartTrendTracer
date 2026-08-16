"""
MongoDB-compatible API endpoints for importing articles from URLs

Supports both simple HTTP requests and Playwright-based authenticated collection.
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
import html2text
# from readability import Readability  # Optional dependency
from app.database.mongodb import get_database
from app.services.author_service import AuthorService
import logging

from app.services.preview_utils import generate_preview

logger = logging.getLogger(__name__)

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
    # Smart-dispatch signal: set when URL belongs to a known auth-site but no
    # session is available, so the frontend can guide the user to the Auth tab.
    requires_auth: bool = False
    site: Optional[str] = None
    site_name: Optional[str] = None

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
                except Exception:
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
            except Exception:
                pass
        return match.group(0)

    markdown_content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', fix_image_url, markdown_content)

    return markdown_content

@router.post("/import-url", response_model=URLImportResponse)
async def import_article_from_url(request: URLImportRequest):
    """
    Import an article from a URL

    Supports:
    - Substack articles
    - Medium articles
    - Blog posts
    - General web articles

    Smart-dispatch: if the URL belongs to a known auth-site (e.g., Substack,
    Medium) and we have a saved Playwright session, transparently upgrade to
    the Playwright path. If the site is recognized but no session exists,
    return `requires_auth=True` so the frontend can guide the user to the
    Auth tab.
    """
    url = str(request.url)

    # ------------------------------------------------------------------
    # Smart-dispatch pre-flight: detect auth-sites and reuse saved session
    # ------------------------------------------------------------------
    sm = None
    SUPPORTED_SITES: Dict[str, Any] = {}
    site: Optional[str] = None
    try:
        from app.collectors.playwright_collector.session_manager import (
            SessionManager, SUPPORTED_SITES as _SUPPORTED_SITES,
        )
        SUPPORTED_SITES = _SUPPORTED_SITES
        sm = SessionManager()
        site = sm.detect_site(url)
    except Exception as e:
        logger.warning(f"Site-detection unavailable, falling back to simple fetch: {e}")

    if site and sm is not None:
        site_name = SUPPORTED_SITES.get(site, {}).get('name', site.title())
        if sm.has_session(site):
            # Saved auth available — silently delegate to Playwright path
            try:
                from app.api.article_import.conversion import (
                    service_import_url_playwright,
                    _check_playwright_available,
                )
                if not _check_playwright_available():
                    logger.warning(
                        f"URL '{url}' is a {site_name} URL with a saved session, "
                        "but Playwright is not installed — falling back to simple fetch."
                    )
                else:
                    result = await service_import_url_playwright(url)
                    # If Playwright reports auth-failure (e.g. expired session),
                    # surface as requires_auth so user can re-login.
                    if not result.get('success') and result.get('requires_auth'):
                        return URLImportResponse(
                            success=False,
                            error="auth_required",
                            requires_auth=True,
                            site=site,
                            site_name=site_name,
                        )
                    return URLImportResponse(
                        success=bool(result.get('success')),
                        article_id=result.get('article_id'),
                        title=result.get('title'),
                        author=result.get('author'),
                        word_count=result.get('word_count'),
                        error=result.get('error'),
                    )
            except Exception as e:
                logger.error(f"Playwright delegation failed for {url}: {e}")
                # Fall through to simple fetch as last resort
        else:
            # Auth-site but no session — tell frontend to open Auth tab
            return URLImportResponse(
                success=False,
                error="auth_required",
                requires_auth=True,
                site=site,
                site_name=site_name,
            )

    try:

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
            'preview': generate_preview(markdown_content) if markdown_content else '',
            'word_count': word_count,
            'publication_date': metadata['publication_date'],
            'description': metadata['description'],
            'source': 'url_import',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
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
                    'updated_at': datetime.now(timezone.utc)
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
            'preview': generate_preview(markdown_content) if markdown_content else '',
            'word_count': word_count,
            'publication_date': metadata['publication_date'],
            'description': metadata['description'],
            'source': 'enhanced_import',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
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
                    'updated_at': datetime.now(timezone.utc),
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
        # Simple heuristic - if we get redirected to a login/subscribe page
        # or get 403, it's likely paywalled
        is_paywalled = (
            response.status_code == 403 or
            'login' in response.url.lower() or
            'subscribe' in response.url.lower()
        )
        return {"is_paywalled": is_paywalled}
    except Exception:
        return {"is_paywalled": False}

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
async def import_batch(urls: list[str]):
    """Import multiple articles at once.

    Uses the same smart-dispatch path as /import-url, so each URL is checked
    for auth-site detection and the saved Playwright session is reused when
    available.
    """
    results = []
    for url in urls:
        try:
            request = URLImportRequest(url=url)  # type: ignore[arg-type]
            result = await import_article_from_url(request)
            results.append(result.model_dump())
        except Exception as e:
            results.append({
                "success": False,
                "url": url,
                "error": str(e)
            })
    return {"results": results}
