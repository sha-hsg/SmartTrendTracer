"""
Playwright Article Collector

Main orchestration class that uses Playwright for browser automation to
collect articles from authenticated sources like Substack and Medium.
"""

import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Check if Playwright is available
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Run: pip install playwright && playwright install chromium")

from .session_manager import SessionManager, SUPPORTED_SITES
from .content_extractor import ContentExtractor
from .markdown_converter import MarkdownConverter


class PlaywrightCollector:
    """
    Collects articles from authenticated web sources using Playwright.

    Features:
    - Session persistence (login once, collect many times)
    - Site-specific content extraction
    - Paywall detection
    - HTML to Markdown conversion
    """

    def __init__(self, sessions_dir: Optional[str] = None, headless: bool = True):
        """
        Initialize the collector.

        Args:
            sessions_dir: Directory for session storage
            headless: Run browser in headless mode
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is not installed. Please run:\n"
                "  pip install playwright\n"
                "  playwright install chromium"
            )

        self.session_manager = SessionManager(sessions_dir)
        self.content_extractor = ContentExtractor()
        self.markdown_converter = MarkdownConverter()
        self.headless = headless

        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    async def _ensure_browser(self) -> Browser:
        """Ensure browser is running and return it."""
        if self._browser is None or not self._browser.is_connected():
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(headless=self.headless)
        return self._browser

    async def _get_context(self, site: Optional[str] = None) -> BrowserContext:
        """
        Get a browser context, optionally with saved session state.

        Args:
            site: Site to load session for (if available)

        Returns:
            BrowserContext with or without saved session
        """
        browser = await self._ensure_browser()

        # Check for saved session
        if site:
            state_path = self.session_manager.get_storage_state_path(site)
            if state_path:
                try:
                    return await browser.new_context(storage_state=state_path)
                except Exception as e:
                    logger.warning(f"Failed to load saved session for {site}: {e}")

        # Create fresh context
        return await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

    async def close(self):
        """Close browser and cleanup."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None

    async def authenticate(self, site: str, timeout_seconds: int = 300) -> bool:
        """
        Perform interactive authentication for a site.

        Opens a browser window for the user to log in manually.
        Saves session cookies after successful authentication.

        Args:
            site: Site identifier (e.g., 'substack', 'medium')
            timeout_seconds: Max time to wait for authentication

        Returns:
            True if authentication successful
        """
        site_config = SUPPORTED_SITES.get(site)
        if not site_config:
            raise ValueError(f"Unknown site: {site}. Supported: {list(SUPPORTED_SITES.keys())}")

        login_url = site_config['login_url']
        test_url = site_config['test_url']
        auth_indicator = site_config['auth_indicator']

        logger.info(f"Starting authentication for {site_config['name']}")
        print(f"\n{'='*60}")
        print(f"Authentication for {site_config['name']}")
        print(f"{'='*60}")
        print(f"\nA browser window will open to: {login_url}")
        print(f"Please log in using your account.")
        print(f"The browser will close automatically once authenticated.")
        print(f"\nWaiting for login (timeout: {timeout_seconds}s)...")

        # Launch visible browser for interactive login
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1200, 'height': 800},
        )
        page = await context.new_page()

        try:
            # Navigate to login page (use 'load' instead of 'networkidle' - Substack has constant tracking)
            await page.goto(login_url, wait_until='load', timeout=60000)
            # Give JavaScript time to render
            await asyncio.sleep(2)

            # Wait for user to complete login
            # We check for authentication by looking at cookies, NOT by navigating away
            start_time = asyncio.get_event_loop().time()
            authenticated = False
            initial_url = page.url

            print(f"\nPlease log in using the browser window...")
            print(f"Waiting for authentication (timeout: {timeout_seconds}s)...")

            while asyncio.get_event_loop().time() - start_time < timeout_seconds:
                try:
                    # Check cookies for authentication indicators (non-intrusive)
                    cookies = await context.cookies()
                    cookie_names = [c['name'] for c in cookies]

                    # Substack uses 'substack.sid' cookie when logged in
                    # Trust the cookie - if it's there, user is logged in
                    if 'substack.sid' in cookie_names:
                        print(f"\n🔑 Substack session cookie detected!")
                        authenticated = True
                        break

                    # For other sites, check generic auth cookies
                    auth_cookies = ['sid', 'connect.sid', 'session', 'auth_token']
                    if any(name in cookie_names for name in auth_cookies):
                        print(f"\n🔑 Auth cookie detected!")
                        authenticated = True
                        break

                except Exception as e:
                    logger.debug(f"Auth check error: {e}")

                await asyncio.sleep(3)  # Check every 3 seconds

            if authenticated:
                # Save session state
                state = await context.storage_state()
                self.session_manager.save_storage_state(site, state)
                logger.info(f"Session saved for {site}")
                return True
            else:
                print(f"\n Authentication timed out.")
                return False

        finally:
            await context.close()
            await browser.close()
            await playwright.stop()

    async def check_auth_status(self, site: str) -> Dict:
        """
        Check if we have valid authentication for a site.

        Args:
            site: Site identifier

        Returns:
            Dict with authentication status info
        """
        site_config = SUPPORTED_SITES.get(site)
        if not site_config:
            return {
                'site': site,
                'supported': False,
                'authenticated': False,
                'message': f"Unknown site: {site}"
            }

        session_info = self.session_manager.get_session_info(site)
        if not session_info or not self.session_manager.has_session(site):
            return {
                'site': site,
                'supported': True,
                'authenticated': False,
                'message': f"No saved session for {site_config['name']}"
            }

        # Validate session by loading test page
        context = await self._get_context(site)
        page = await context.new_page()

        try:
            test_url = site_config['test_url']
            await page.goto(test_url, wait_until='load', timeout=20000)
            content = await page.content()

            is_valid = self.session_manager.validate_session(site, content)

            return {
                'site': site,
                'supported': True,
                'authenticated': is_valid,
                'session_info': session_info,
                'message': 'Session valid' if is_valid else 'Session expired or invalid'
            }

        except Exception as e:
            logger.error(f"Failed to validate session for {site}: {e}")
            return {
                'site': site,
                'supported': True,
                'authenticated': False,
                'message': f"Failed to validate: {str(e)}"
            }

        finally:
            await context.close()

    async def fetch_article(self, url: str) -> Dict:
        """
        Fetch an article using Playwright with saved session.

        Args:
            url: Article URL

        Returns:
            Dict with article data or error info
        """
        site = self.session_manager.detect_site(url)
        logger.info(f"Fetching article: {url} (site: {site or 'generic'})")

        # Get context with session if available
        context = await self._get_context(site)
        page = await context.new_page()

        try:
            # Navigate to article
            response = await page.goto(url, wait_until='load', timeout=45000)

            if not response:
                return {'success': False, 'error': 'Failed to load page'}

            if response.status >= 400:
                return {'success': False, 'error': f'HTTP {response.status}'}

            # Wait for dynamic content to render (Substack uses React)
            # Try to wait for the main content selector to appear
            if site == 'substack':
                try:
                    # Wait for article body to render (max 10 seconds)
                    await page.wait_for_selector('.body.markup', timeout=10000)
                    logger.info("Substack article content loaded")
                except Exception as e:
                    logger.warning(f"Content selector not found, proceeding anyway: {e}")
                    # Give a short delay as fallback
                    await asyncio.sleep(2)

            # Get page content
            html = await page.content()

            # Extract article content
            extracted = self.content_extractor.extract(html, url)

            # Check for paywall
            if extracted.get('has_paywall'):
                logger.warning(f"Paywall detected for {url}")

                # Check if we're authenticated
                if site and not self.session_manager.has_session(site):
                    return {
                        'success': False,
                        'error': 'Content behind paywall',
                        'requires_auth': True,
                        'site': site,
                        'auth_url': SUPPORTED_SITES.get(site, {}).get('login_url')
                    }

            # Convert to markdown
            content_markdown = self.markdown_converter.convert(extracted.get('content_html', ''))
            preview = self.markdown_converter.extract_preview(content_markdown)
            word_count = self.markdown_converter.count_words(content_markdown)
            reading_time = self.markdown_converter.estimate_reading_time(word_count)

            return {
                'success': True,
                'url': url,
                'title': extracted.get('title'),
                'subtitle': extracted.get('subtitle'),
                'author': extracted.get('author'),
                'author_url': extracted.get('author_url'),
                'published_at': extracted.get('date'),
                'content_html': extracted.get('content_html'),
                'content_markdown': content_markdown,
                'preview': preview,
                'word_count': word_count,
                'reading_time_minutes': reading_time,
                'source_site': extracted.get('source_site'),
                'has_paywall': extracted.get('has_paywall', False),
                'collected_at': datetime.now(timezone.utc),
            }

        except Exception as e:
            logger.error(f"Failed to fetch article {url}: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

        finally:
            await context.close()

    def fetch_article_sync(self, url: str) -> Dict:
        """
        Synchronous wrapper for fetch_article.

        Args:
            url: Article URL

        Returns:
            Dict with article data or error info
        """
        return asyncio.get_event_loop().run_until_complete(self.fetch_article(url))

    def authenticate_sync(self, site: str, timeout_seconds: int = 300) -> bool:
        """
        Synchronous wrapper for authenticate.

        Args:
            site: Site identifier
            timeout_seconds: Max time to wait

        Returns:
            True if authentication successful
        """
        return asyncio.get_event_loop().run_until_complete(
            self.authenticate(site, timeout_seconds)
        )

    def check_auth_status_sync(self, site: str) -> Dict:
        """
        Synchronous wrapper for check_auth_status.

        Args:
            site: Site identifier

        Returns:
            Dict with authentication status info
        """
        return asyncio.get_event_loop().run_until_complete(
            self.check_auth_status(site)
        )


# Convenience functions for non-async usage
def fetch_article(url: str, sessions_dir: Optional[str] = None) -> Dict:
    """
    Fetch an article using default settings.

    Args:
        url: Article URL
        sessions_dir: Optional sessions directory

    Returns:
        Dict with article data
    """
    collector = PlaywrightCollector(sessions_dir=sessions_dir)
    try:
        return collector.fetch_article_sync(url)
    finally:
        asyncio.get_event_loop().run_until_complete(collector.close())


def authenticate(site: str, sessions_dir: Optional[str] = None) -> bool:
    """
    Perform interactive authentication.

    Args:
        site: Site identifier
        sessions_dir: Optional sessions directory

    Returns:
        True if successful
    """
    collector = PlaywrightCollector(sessions_dir=sessions_dir, headless=False)
    try:
        return collector.authenticate_sync(site)
    finally:
        asyncio.get_event_loop().run_until_complete(collector.close())


def check_status(site: str, sessions_dir: Optional[str] = None) -> Dict:
    """
    Check authentication status for a site.

    Args:
        site: Site identifier
        sessions_dir: Optional sessions directory

    Returns:
        Dict with status info
    """
    collector = PlaywrightCollector(sessions_dir=sessions_dir)
    try:
        return collector.check_auth_status_sync(site)
    finally:
        asyncio.get_event_loop().run_until_complete(collector.close())
