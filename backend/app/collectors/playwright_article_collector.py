#!/usr/bin/env python3
"""
Playwright Article Collector CLI

Command-line interface for collecting authenticated articles from Substack,
Medium, and other sites using Playwright browser automation.

Usage:
    # Authenticate with a site (opens browser)
    python -m app.collectors.playwright_article_collector --auth substack

    # Check authentication status
    python -m app.collectors.playwright_article_collector --status substack

    # Import a single article
    python -m app.collectors.playwright_article_collector --url "https://..."

    # Batch import from file
    python -m app.collectors.playwright_article_collector --file urls.txt

    # List saved sessions
    python -m app.collectors.playwright_article_collector --list-sessions

    # Clear session for a site
    python -m app.collectors.playwright_article_collector --clear-session substack
"""

import argparse
import asyncio
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database.mongodb import get_database
from bson import ObjectId

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_playwright_installed() -> bool:
    """Check if Playwright is installed."""
    try:
        from playwright.async_api import async_playwright
        return True
    except ImportError:
        return False


def print_install_instructions():
    """Print Playwright installation instructions."""
    print("\n" + "="*60)
    print("Playwright is not installed!")
    print("="*60)
    print("\nPlease install Playwright by running:")
    print("  pip install playwright")
    print("  playwright install chromium")
    print("\nAlternatively, add 'playwright>=1.40.0' to requirements.txt")
    print("and run: pip install -r requirements.txt")
    print("="*60 + "\n")


def list_supported_sites():
    """Print list of supported sites."""
    from app.collectors.playwright_collector import SUPPORTED_SITES

    print("\n" + "="*60)
    print("Supported Sites")
    print("="*60)
    for key, config in SUPPORTED_SITES.items():
        print(f"\n  {key}:")
        print(f"    Name: {config['name']}")
        print(f"    Login URL: {config['login_url']}")
    print("\n" + "="*60)


def list_sessions():
    """List all saved sessions."""
    from app.collectors.playwright_collector import SessionManager

    sm = SessionManager()
    sessions = sm.list_sessions()

    print("\n" + "="*60)
    print("Saved Sessions")
    print("="*60)

    if not sessions:
        print("\nNo saved sessions found.")
    else:
        for site, info in sessions.items():
            print(f"\n  {site}:")
            if info:
                print(f"    Created: {info.get('created_at', 'Unknown')}")
                print(f"    Last Used: {info.get('last_used', 'Unknown')}")
                print(f"    Cookies: {info.get('cookie_count', 'Unknown')}")
                print(f"    Valid: {info.get('is_valid', 'Unknown')}")

    print("\n" + "="*60)


def clear_session(site: str):
    """Clear session for a site."""
    from app.collectors.playwright_collector import SessionManager

    sm = SessionManager()
    if sm.delete_session(site):
        print(f"\n Session cleared for {site}")
    else:
        print(f"\n No session found for {site}")


async def authenticate_site(site: str):
    """Authenticate with a site."""
    from app.collectors.playwright_collector import PlaywrightCollector

    collector = PlaywrightCollector(headless=False)
    try:
        success = await collector.authenticate(site)
        if success:
            print(f"\n Authentication successful for {site}!")
            print("Session has been saved and will be used for future imports.")
        else:
            print(f"\n Authentication failed or timed out for {site}")
            return False
        return success
    finally:
        await collector.close()


async def check_status(site: str):
    """Check authentication status for a site."""
    from app.collectors.playwright_collector import PlaywrightCollector

    print(f"\nChecking authentication status for {site}...")

    collector = PlaywrightCollector()
    try:
        status = await collector.check_auth_status(site)

        print("\n" + "="*60)
        print(f"Authentication Status: {site}")
        print("="*60)
        print(f"  Supported: {status.get('supported', False)}")
        print(f"  Authenticated: {status.get('authenticated', False)}")
        print(f"  Message: {status.get('message', '')}")

        if status.get('session_info'):
            info = status['session_info']
            print(f"\n  Session Info:")
            print(f"    Created: {info.get('created_at', 'Unknown')}")
            print(f"    Last Used: {info.get('last_used', 'Unknown')}")

        print("="*60)
        return status.get('authenticated', False)
    finally:
        await collector.close()


async def import_article(url: str, save_to_db: bool = True) -> dict:
    """Import a single article."""
    from app.collectors.playwright_collector import PlaywrightCollector

    print(f"\nImporting: {url}")

    collector = PlaywrightCollector()
    try:
        result = await collector.fetch_article(url)

        if not result.get('success'):
            print(f"  Failed: {result.get('error', 'Unknown error')}")

            if result.get('requires_auth'):
                site = result.get('site')
                print(f"\n  This content requires authentication.")
                print(f"  Run: python -m app.collectors.playwright_article_collector --auth {site}")
            return result

        # Print result
        print(f"  Title: {result.get('title', 'Untitled')}")
        print(f"  Author: {result.get('author', 'Unknown')}")
        print(f"  Words: {result.get('word_count', 0)}")
        print(f"  Reading Time: {result.get('reading_time_minutes', 0)} min")

        if result.get('has_paywall'):
            print(f"  Note: Partial content (paywall detected)")

        # Save to database
        if save_to_db:
            article_id = save_article_to_db(result)
            if article_id:
                print(f"  Saved: ID {article_id}")
                result['article_id'] = article_id
            else:
                print(f"  Warning: Failed to save to database")

        return result

    finally:
        await collector.close()


def save_article_to_db(article_data: dict) -> Optional[str]:
    """Save article to MongoDB."""
    try:
        db = get_database()

        # Check if article already exists by URL
        existing = db.articles.find_one({'url': article_data.get('url')})
        if existing:
            logger.info(f"Article already exists: {article_data.get('url')}")
            return str(existing['_id'])

        # Prepare article document
        doc = {
            'title': article_data.get('title'),
            'subtitle': article_data.get('subtitle'),
            'url': article_data.get('url'),
            'author_name': article_data.get('author'),
            'author_url': article_data.get('author_url'),
            'published_at': article_data.get('published_at'),
            'content_html': article_data.get('content_html'),
            'content_markdown': article_data.get('content_markdown'),
            'preview': article_data.get('preview'),
            'word_count': article_data.get('word_count', 0),
            'reading_time_minutes': article_data.get('reading_time_minutes', 0),
            'source': 'playwright_collector',
            'source_site': article_data.get('source_site'),
            'has_paywall': article_data.get('has_paywall', False),
            'collected_at': datetime.now(timezone.utc),
            'created_at': datetime.now(timezone.utc),
        }

        result = db.articles.insert_one(doc)
        return str(result.inserted_id)

    except Exception as e:
        logger.error(f"Failed to save article: {e}")
        return None


async def batch_import(file_path: str, save_to_db: bool = True) -> List[dict]:
    """Import articles from a file of URLs."""
    from app.collectors.playwright_collector import PlaywrightCollector

    # Read URLs from file
    urls = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                urls.append(line)

    if not urls:
        print(f"No URLs found in {file_path}")
        return []

    print(f"\n" + "="*60)
    print(f"Batch Import: {len(urls)} URLs from {file_path}")
    print("="*60)

    results = []
    collector = PlaywrightCollector()

    try:
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] {url}")

            result = await collector.fetch_article(url)

            if result.get('success'):
                print(f"  Title: {result.get('title', 'Untitled')}")
                print(f"  Words: {result.get('word_count', 0)}")

                if save_to_db:
                    article_id = save_article_to_db(result)
                    if article_id:
                        result['article_id'] = article_id
                        print(f"  Saved: ID {article_id}")
            else:
                print(f"  Failed: {result.get('error', 'Unknown')}")

            results.append(result)

            # Small delay between requests
            await asyncio.sleep(1)

    finally:
        await collector.close()

    # Print summary
    successful = sum(1 for r in results if r.get('success'))
    print(f"\n" + "="*60)
    print(f"Batch Import Complete")
    print(f"  Total: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {len(results) - successful}")
    print("="*60)

    return results


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Playwright Article Collector - Import authenticated articles from Substack, Medium, etc.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Authenticate with Substack (opens browser)
  python -m app.collectors.playwright_article_collector --auth substack

  # Check authentication status
  python -m app.collectors.playwright_article_collector --status substack

  # Import a single article
  python -m app.collectors.playwright_article_collector --url "https://example.substack.com/p/article"

  # Batch import from file
  python -m app.collectors.playwright_article_collector --file urls.txt

  # List all saved sessions
  python -m app.collectors.playwright_article_collector --list-sessions

  # List supported sites
  python -m app.collectors.playwright_article_collector --list-sites
        """
    )

    # Mutually exclusive main actions
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--auth', metavar='SITE',
                       help='Authenticate with a site (opens browser)')
    group.add_argument('--status', metavar='SITE',
                       help='Check authentication status for a site')
    group.add_argument('--url', metavar='URL',
                       help='Import a single article from URL')
    group.add_argument('--file', metavar='FILE',
                       help='Batch import from file (one URL per line)')
    group.add_argument('--list-sessions', action='store_true',
                       help='List all saved sessions')
    group.add_argument('--list-sites', action='store_true',
                       help='List supported sites')
    group.add_argument('--clear-session', metavar='SITE',
                       help='Clear saved session for a site')

    # Additional options
    parser.add_argument('--no-save', action='store_true',
                        help='Do not save imported articles to database')
    parser.add_argument('--json', action='store_true',
                        help='Output results as JSON')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle actions that don't require Playwright first
    if args.list_sites:
        list_supported_sites()
        return

    if args.list_sessions:
        list_sessions()
        return

    if args.clear_session:
        clear_session(args.clear_session)
        return

    # Check Playwright installation for other actions
    if not check_playwright_installed():
        print_install_instructions()
        sys.exit(1)

    # Handle authentication
    if args.auth:
        success = asyncio.get_event_loop().run_until_complete(
            authenticate_site(args.auth)
        )
        sys.exit(0 if success else 1)

    # Check status
    if args.status:
        authenticated = asyncio.get_event_loop().run_until_complete(
            check_status(args.status)
        )
        sys.exit(0 if authenticated else 1)

    # Import single URL
    if args.url:
        result = asyncio.get_event_loop().run_until_complete(
            import_article(args.url, save_to_db=not args.no_save)
        )
        if args.json:
            print(json.dumps(result, default=str, indent=2))
        sys.exit(0 if result.get('success') else 1)

    # Batch import
    if args.file:
        if not Path(args.file).exists():
            print(f"File not found: {args.file}")
            sys.exit(1)

        results = asyncio.get_event_loop().run_until_complete(
            batch_import(args.file, save_to_db=not args.no_save)
        )
        if args.json:
            print(json.dumps(results, default=str, indent=2))

        successful = sum(1 for r in results if r.get('success'))
        sys.exit(0 if successful == len(results) else 1)

    # No action specified
    parser.print_help()


if __name__ == '__main__':
    main()
