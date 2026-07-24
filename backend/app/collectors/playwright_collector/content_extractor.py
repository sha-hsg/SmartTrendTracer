"""
Content Extractor for Playwright Article Collector

Provides site-specific CSS selectors and extraction logic for different
article platforms. Includes generic fallback for unsupported sites.
"""

import re
import logging
from typing import Dict, Optional, List
from datetime import datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# Site-specific extraction configurations
SITE_EXTRACTORS = {
    'substack': {
        'name': 'Substack',
        'selectors': {
            'title': [
                'h1.post-title',
                'h1[data-testid="post-title"]',
                'article h1',
                '.post-header h1',
            ],
            'subtitle': [
                'h3.subtitle',
                '.subtitle',
                'p.subtitle',
            ],
            'author': [
                '.author-name',
                'a.author-name',
                '.pencraft.pc-display-flex.pc-gap-4 a[href*="/profile/"]',
                '.post-header a[href*="@"]',
            ],
            'date': [
                'time[datetime]',
                '.post-date',
                'time',
            ],
            'content': [
                '.body.markup',
                '.post-content',
                'article .available-content',
                '.single-post .body',
                'div[class*="body"][class*="markup"]',
            ],
            'paywall_indicator': [
                '.paywall',
                '.paywall-container',
                '.subscriber-only',
                '[data-testid="paywall"]',
            ],
        },
        'remove_selectors': [
            '.subscribe-widget',
            '.subscription-widget',
            '.button-wrapper',
            '.share-dialog',
            '.comments-section',
            '.post-footer',
            'footer',
            '.related-posts',
        ],
    },
    'medium': {
        'name': 'Medium',
        'selectors': {
            'title': [
                'h1[data-testid="storyTitle"]',
                'article h1',
                '.pw-post-title',
            ],
            'subtitle': [
                'h2[data-testid="storySubtitle"]',
                '.pw-subtitle',
            ],
            'author': [
                'a[data-testid="authorName"]',
                '.pw-author-name',
                'a[href*="/@"]',
            ],
            'date': [
                'span[data-testid="storyPublishDate"]',
                'time',
            ],
            'content': [
                'article section',
                '.postArticle-content',
                'article',
            ],
            'paywall_indicator': [
                '.meteredContent',
                '[data-testid="paywall"]',
                '.js-postMeteredContent',
            ],
        },
        'remove_selectors': [
            '.post-actions',
            '.js-postActions',
            '.responsesWrapper',
            'footer',
        ],
    },
    'patreon': {
        'name': 'Patreon',
        'selectors': {
            'title': [
                'h1[data-tag="post-title"]',
                '.post-title h1',
                'h1',
            ],
            'author': [
                'a[data-tag="creator-name"]',
                '.creator-name',
            ],
            'date': [
                'time',
                '[data-tag="published-date"]',
            ],
            'content': [
                '[data-tag="post-content"]',
                '.post-body',
                'article',
            ],
            'paywall_indicator': [
                '[data-tag="locked-post"]',
                '.locked-post',
            ],
        },
        'remove_selectors': [
            '.comments',
            '.related-posts',
            'footer',
        ],
    },
}

# Generic extractor for unknown sites
GENERIC_EXTRACTOR = {
    'name': 'Generic',
    'selectors': {
        'title': [
            'article h1',
            'main h1',
            '.article-title',
            '.post-title',
            '.entry-title',
            'h1.title',
            'h1',
        ],
        'subtitle': [
            '.subtitle',
            '.sub-title',
            '.article-subtitle',
            'h2.subtitle',
        ],
        'author': [
            '.author',
            '.author-name',
            '.byline',
            '[rel="author"]',
            '.entry-author',
            'a[href*="/author/"]',
        ],
        'date': [
            'time[datetime]',
            '.date',
            '.published',
            '.post-date',
            '.entry-date',
            'time',
        ],
        'content': [
            'article',
            '.article-body',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.content',
            'main',
        ],
    },
    'remove_selectors': [
        'nav',
        'header',
        'footer',
        '.sidebar',
        '.comments',
        '.related',
        '.social-share',
        '.advertisement',
        '.ads',
        'script',
        'style',
        'noscript',
    ],
}


class ContentExtractor:
    """Extracts article content from HTML using site-specific selectors."""

    def __init__(self):
        """Initialize the content extractor."""
        self.extractors = SITE_EXTRACTORS
        self.generic = GENERIC_EXTRACTOR

    def detect_site(self, url: str) -> Optional[str]:
        """
        Detect which site the URL belongs to.

        Args:
            url: Article URL

        Returns:
            Site key or None for generic extraction
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        for site_key, extractor in self.extractors.items():
            site_domains = {
                'substack': ['substack.com'],
                'medium': ['medium.com'],
                'patreon': ['patreon.com'],
            }
            for site_domain in site_domains.get(site_key, []):
                if domain.endswith(site_domain) or site_domain in domain:
                    return site_key

        return None

    def get_extractor(self, site: Optional[str]) -> Dict:
        """Get the extractor config for a site."""
        if site and site in self.extractors:
            return self.extractors[site]
        return self.generic

    def _find_element(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """
        Find an element using a list of CSS selectors in priority order.

        Args:
            soup: BeautifulSoup object
            selectors: List of CSS selectors to try

        Returns:
            Text content of first matching element or None
        """
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {e}")
                continue
        return None

    def _find_element_html(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """
        Find an element and return its HTML content.

        Args:
            soup: BeautifulSoup object
            selectors: List of CSS selectors to try

        Returns:
            HTML content of first matching element or None
        """
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    return str(element)
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {e}")
                continue
        return None

    def _parse_date(self, date_str: str, soup: BeautifulSoup) -> Optional[datetime]:
        """
        Parse a date string or extract from time element.

        Args:
            date_str: Date string to parse
            soup: BeautifulSoup object for datetime attribute fallback

        Returns:
            Parsed datetime or None
        """
        if not date_str:
            return None

        # Try to find time element with datetime attribute
        time_elem = soup.select_one('time[datetime]')
        if time_elem and time_elem.get('datetime'):
            try:
                dt_str = time_elem['datetime']
                # Handle various ISO formats
                if dt_str.endswith('Z'):
                    dt_str = dt_str[:-1] + '+00:00'
                return datetime.fromisoformat(dt_str)
            except ValueError:
                pass

        # Try common date formats
        date_formats = [
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%S.%f%z',
            '%Y-%m-%d',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y',
            '%m/%d/%Y',
            '%d/%m/%Y',
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None

    def _clean_content(self, soup: BeautifulSoup, remove_selectors: List[str]) -> BeautifulSoup:
        """
        Remove unwanted elements from content.

        Args:
            soup: BeautifulSoup object
            remove_selectors: List of CSS selectors for elements to remove

        Returns:
            Cleaned BeautifulSoup object
        """
        # Remove specified elements
        for selector in remove_selectors:
            try:
                for element in soup.select(selector):
                    element.decompose()
            except Exception:
                pass

        # Remove common noise elements
        for tag in soup.find_all(['script', 'style', 'noscript', 'iframe']):
            tag.decompose()

        # Remove tracking pixels (1x1 images)
        for img in soup.find_all('img'):
            width = img.get('width', '')
            height = img.get('height', '')
            src = img.get('src', '')
            if (width == '1' and height == '1') or \
               'pixel' in src.lower() or \
               'track' in src.lower() or \
               'open?token=' in src:
                img.decompose()

        return soup

    def check_paywall(self, html: str, site: Optional[str]) -> bool:
        """
        Check if article content is behind a paywall.

        Args:
            html: HTML content
            site: Site identifier

        Returns:
            True if paywall detected
        """
        extractor = self.get_extractor(site)
        soup = BeautifulSoup(html, 'html.parser')

        paywall_selectors = extractor.get('selectors', {}).get('paywall_indicator', [])
        for selector in paywall_selectors:
            try:
                if soup.select_one(selector):
                    return True
            except Exception:
                pass

        return False

    def extract(self, html: str, url: str) -> Dict:
        """
        Extract article content from HTML.

        Args:
            html: Raw HTML content
            url: Article URL

        Returns:
            Dict with extracted content:
            - title: Article title
            - subtitle: Article subtitle (optional)
            - author: Author name
            - author_url: Author profile URL (optional)
            - date: Publication date
            - content_html: Clean HTML content
            - has_paywall: Whether paywall was detected
            - source_site: Detected site (e.g., 'substack')
        """
        site = self.detect_site(url)
        extractor = self.get_extractor(site)
        selectors = extractor.get('selectors', {})
        remove_selectors = extractor.get('remove_selectors', [])

        soup = BeautifulSoup(html, 'html.parser')

        # Extract metadata
        title = self._find_element(soup, selectors.get('title', []))

        # Fallback: try og:title meta tag if no title found
        if not title:
            og_title = soup.select_one('meta[property="og:title"]')
            if og_title:
                title = og_title.get('content')

        subtitle = self._find_element(soup, selectors.get('subtitle', []))
        author = self._find_element(soup, selectors.get('author', []))

        # Fallback: try author meta tags if no author found
        if not author:
            # Try meta author tag
            meta_author = soup.select_one('meta[name="author"]')
            if meta_author:
                author = meta_author.get('content')

        # Fallback: try twitter:creator or article:author
        if not author:
            meta_twitter = soup.select_one('meta[name="twitter:creator"]')
            if meta_twitter:
                author = meta_twitter.get('content')

        if not author:
            meta_article_author = soup.select_one('meta[property="article:author"]')
            if meta_article_author:
                author = meta_article_author.get('content')

        date_str = self._find_element(soup, selectors.get('date', []))
        date = self._parse_date(date_str, soup)

        # Try to find author URL
        author_url = None
        for selector in selectors.get('author', []):
            try:
                author_elem = soup.select_one(selector)
                if author_elem and author_elem.name == 'a':
                    author_url = author_elem.get('href')
                    break
            except Exception:
                pass

        # Extract content
        content_html = self._find_element_html(soup, selectors.get('content', []))

        if content_html:
            # Clean the content
            content_soup = BeautifulSoup(content_html, 'html.parser')
            content_soup = self._clean_content(content_soup, remove_selectors)
            content_html = str(content_soup)

        # Check for paywall
        has_paywall = self.check_paywall(html, site)

        # If no content found, try full page cleanup
        if not content_html or len(content_html) < 100:
            # Clone soup and clean entire page
            full_soup = BeautifulSoup(html, 'html.parser')
            full_soup = self._clean_content(full_soup, remove_selectors)
            # Try to find main content area
            main = full_soup.select_one('main') or full_soup.select_one('article') or full_soup.body
            if main:
                content_html = str(main)

        return {
            'title': title or self._extract_title_from_url(url),
            'subtitle': subtitle,
            'author': author,
            'author_url': author_url,
            'date': date,
            'content_html': content_html,
            'has_paywall': has_paywall,
            'source_site': site or 'generic',
        }

    def _extract_title_from_url(self, url: str) -> str:
        """Extract a title from URL as fallback."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')

        # Get last path segment
        if '/' in path:
            title = path.split('/')[-1]
        else:
            title = path

        # Clean up
        title = title.replace('-', ' ').replace('_', ' ')
        title = re.sub(r'\.[^.]+$', '', title)  # Remove extension

        return title.title() if title else 'Untitled Article'
