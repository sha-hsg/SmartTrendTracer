"""
Playwright-based authenticated article collection endpoints
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from datetime import datetime, timezone
from app.database.mongodb import get_database
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


async def service_import_url_playwright(url: str) -> Dict[str, Any]:
    """
    Reusable service function: fetch article via Playwright with saved session,
    save to MongoDB. Used by both /import-url-playwright and the smart-dispatch
    path in /import-url.

    Returns the same dict shape as the endpoint response.
    Caller is responsible for checking _check_playwright_available() if needed.
    """
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
            'collected_at': datetime.now(timezone.utc),
            'created_at': datetime.now(timezone.utc),
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
        return await service_import_url_playwright(url)
    except Exception as e:
        logger.error(f"Failed to import article from URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))
