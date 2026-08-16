"""
Markdown Converter for Playwright Article Collector

Converts HTML content to clean Markdown format, preserving article structure
while removing noise like tracking pixels, scripts, and promotional content.
"""

import re
import json
import logging
from typing import Optional

from bs4 import BeautifulSoup
import html2text

logger = logging.getLogger(__name__)


class MarkdownConverter:
    """Converts HTML to clean Markdown format."""

    def __init__(self):
        """Initialize the converter with html2text settings."""
        self.h2t = html2text.HTML2Text()
        self.h2t.body_width = 0  # Don't wrap lines
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.ignore_tables = False
        self.h2t.images_to_alt = False  # Keep as markdown images
        self.h2t.unicode_snob = True
        self.h2t.wrap_links = False
        self.h2t.skip_internal_links = False
        self.h2t.single_line_break = False
        self.h2t.mark_code = True
        self.h2t.protect_links = True

        # Footer patterns to remove
        self.footer_patterns = [
            # Copyright patterns
            r'©\s*\d{4}[^©]*?(?=\n\n|\Z)',
            # Address patterns
            r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd).*?\d{5}(?:-\d{4})?',
            # Common promotional content
            r'(?i)subscribe to.*?newsletter',
            r'(?i)sign up for.*?updates',
            r'(?i)follow us on',
            r'(?i)share this article',
            r'(?i)related articles?:',
            r'(?i)you might also like:',
            r'(?i)read more:',
            # Substack specific
            r'\[Share\].*?(?=\n\n|\Z)',
            r'\[Subscribe\].*?(?=\n\n|\Z)',
            r'\[Leave a comment\].*?(?=\n\n|\Z)',
            r'Get the app.*?(?=\n\n|\Z)',
            r'Start writing.*?(?=\n\n|\Z)',
        ]

    def convert(self, html: str) -> str:
        """
        Convert HTML to Markdown.

        Args:
            html: HTML content string

        Returns:
            Clean Markdown string
        """
        if not html:
            return ''

        # Pre-process HTML
        html = self._preprocess_html(html)

        # Convert to markdown
        try:
            markdown = self.h2t.handle(html)
        except Exception as e:
            logger.error(f"html2text conversion failed: {e}")
            # Fallback to basic text extraction
            soup = BeautifulSoup(html, 'html.parser')
            markdown = soup.get_text(separator='\n\n')

        # Post-process markdown
        markdown = self._postprocess_markdown(markdown)

        return markdown

    def _preprocess_html(self, html: str) -> str:
        """
        Pre-process HTML before conversion.

        - Removes tracking pixels
        - Removes scripts and styles
        - Fixes image paths
        - Handles Substack-specific elements
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Remove scripts, styles, and other non-content
        for tag in soup.find_all(['script', 'style', 'noscript', 'iframe', 'svg']):
            tag.decompose()

        # Handle Substack images - they store URL in data-attrs JSON, not src
        for img in soup.find_all('img'):
            data_attrs = img.get('data-attrs')
            if data_attrs:
                try:
                    attrs = json.loads(data_attrs)
                    if 'src' in attrs and attrs['src']:
                        img['src'] = attrs['src']
                        # Also set alt text if available
                        if attrs.get('alt'):
                            img['alt'] = attrs['alt']
                        elif attrs.get('title'):
                            img['alt'] = attrs['title']
                        logger.debug(f"Extracted Substack image: {attrs['src'][:80]}...")
                except (json.JSONDecodeError, TypeError) as e:
                    logger.debug(f"Failed to parse data-attrs: {e}")

        # Remove tracking pixels and tiny images
        for img in soup.find_all('img'):
            src = img.get('src', '')
            width = img.get('width', '')
            height = img.get('height', '')

            # Remove tracking pixels
            if (width == '1' and height == '1') or \
               'pixel' in src.lower() or \
               'track' in src.lower() or \
               'open?token=' in src or \
               'beacon' in src.lower():
                img.decompose()
                continue

            # Remove tiny icons (but keep actual content images)
            try:
                w = int(width) if width else 999
                h = int(height) if height else 999
                if w <= 24 and h <= 24 and 'post-media' not in src:
                    img.decompose()
                    continue
            except (ValueError, TypeError):
                pass

        # Handle Substack image tables
        for table in soup.find_all('table', class_='image-wrapper'):
            img = table.find('img')
            if img:
                # Replace table with just the image
                table.replace_with(img)

        # Remove common noise elements
        noise_selectors = [
            '.share-dialog',
            '.subscribe-widget',
            '.subscription-widget',
            '.comments-section',
            '.related-posts',
            '.advertisement',
            '.social-share',
            'nav',
        ]
        for selector in noise_selectors:
            for elem in soup.select(selector):
                elem.decompose()

        # Fix relative image URLs if needed
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src.startswith('//'):
                img['src'] = 'https:' + src

        return str(soup)

    def _postprocess_markdown(self, markdown: str) -> str:
        """
        Post-process markdown for cleanup.

        - Removes excessive whitespace
        - Removes footer content
        - Fixes formatting issues
        """
        if not markdown:
            return ''

        # Remove footer patterns
        for pattern in self.footer_patterns:
            markdown = re.sub(pattern, '', markdown, flags=re.DOTALL | re.IGNORECASE)

        # Remove empty markdown links (but not images - they start with !)
        # Use negative lookbehind to avoid matching images like ![](url)
        markdown = re.sub(r'(?<!!)\[\s*\]\([^)]*\)', '', markdown)

        # Remove empty bold/italic
        markdown = re.sub(r'\*\*\s*\*\*', '', markdown)
        markdown = re.sub(r'\*\s*\*', '', markdown)

        # Fix excessive newlines
        markdown = re.sub(r'\n{4,}', '\n\n\n', markdown)

        # Remove invisible Unicode characters
        markdown = re.sub(r'[\u00AD\u200B\u200C\u200D\uFEFF]+', '', markdown)
        markdown = re.sub(r'[\u00A0]+', ' ', markdown)  # Non-breaking space to regular space

        # Clean up table artifacts (pipes without content)
        markdown = re.sub(r'^\|+\s*\|*\s*$', '', markdown, flags=re.MULTILINE)
        markdown = re.sub(r'^\s*\|\s*$', '', markdown, flags=re.MULTILINE)

        # Remove lines that are just dashes (table separators)
        markdown = re.sub(r'^[\-\|]+$', '', markdown, flags=re.MULTILINE)

        # Clean up resulting empty lines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)

        return markdown.strip()

    def extract_preview(self, markdown: str, max_length: int = 500) -> str:
        """
        Extract a preview/excerpt from markdown content.

        Args:
            markdown: Full markdown content
            max_length: Maximum length of preview

        Returns:
            Clean preview text
        """
        from app.services.preview_utils import generate_preview
        return generate_preview(markdown, length=max_length)

    def count_words(self, markdown: str) -> int:
        """
        Count words in markdown content.

        Args:
            markdown: Markdown content

        Returns:
            Word count
        """
        if not markdown:
            return 0

        # Remove markdown formatting
        text = re.sub(r'!\[.*?\]\(.*?\)', '', markdown)  # Images
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Links
        text = re.sub(r'[#*`_~]', '', text)  # Formatting chars

        # Count words
        words = text.split()
        return len(words)

    def estimate_reading_time(self, word_count: int, words_per_minute: int = 200) -> int:
        """
        Estimate reading time in minutes.

        Args:
            word_count: Number of words
            words_per_minute: Reading speed (default 200)

        Returns:
            Estimated reading time in minutes (minimum 1)
        """
        return max(1, word_count // words_per_minute)
