"""
Playwright-based Article Collector

This module provides browser automation to collect authenticated articles from
Substack, Medium, and other sites that require login.

Components:
- SessionManager: Manages browser session/cookie persistence
- ContentExtractor: Site-specific content extraction
- MarkdownConverter: HTML to Markdown conversion
- PlaywrightCollector: Main orchestration class
"""

from .session_manager import SessionManager, SUPPORTED_SITES
from .content_extractor import ContentExtractor
from .markdown_converter import MarkdownConverter
from .collector import PlaywrightCollector

__all__ = [
    'SessionManager',
    'SUPPORTED_SITES',
    'ContentExtractor',
    'MarkdownConverter',
    'PlaywrightCollector'
]
