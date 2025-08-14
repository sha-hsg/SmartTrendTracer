#!/usr/bin/env python3
"""
Collect only today's Substack articles (both forwarded and direct)
This script fetches articles from Gmail that were received today only.
"""
import sys
import os
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.collectors.gmail_substack_collector import GmailSubstackCollector
from app.models import get_db
from app.models.substack import SubstackArticle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect_todays_articles(include_forwarded=True, include_direct=True):
    """
    Collect only articles from today
    
    Args:
        include_forwarded: Whether to collect forwarded articles
        include_direct: Whether to collect direct subscriptions
    """
    logger.info("=== Starting Today's Article Collection ===")
    
    # Calculate today's date range (midnight to now)
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    logger.info(f"Collection date: {today_start.strftime('%Y-%m-%d')}")
    logger.info(f"Time range: {today_start.strftime('%H:%M')} to {now.strftime('%H:%M')} UTC")
    
    # Initialize collector
    collector = GmailSubstackCollector()
    
    # Build the Gmail query for today only
    # Gmail uses dates in the format: after:2025/1/11 before:2025/1/12
    today_str = today_start.strftime('%Y/%m/%d')
    tomorrow = (today_start + timedelta(days=1))
    tomorrow_str = tomorrow.strftime('%Y/%m/%d')
    
    # Base query for Substack emails received today
    date_filter = f"after:{today_str} before:{tomorrow_str}"
    
    # Statistics
    stats = {
        'forwarded': 0,
        'direct': 0,
        'duplicates': 0,
        'errors': 0,
        'total': 0
    }
    
    try:
        # Build the query based on what we want to collect
        query_parts = []
        
        if include_forwarded:
            # Include forwarded emails from university account
            query_parts.extend([
                f'(from:siegfried.handschuh@unisg.ch AND substack)',
                f'(from:me to:me AND substack)',
                f'"@substack.com"'
            ])
            logger.info("Including forwarded articles in search")
        
        if include_direct:
            # Include direct Substack emails
            query_parts.append('from:substack.com')
            logger.info("Including direct subscription articles in search")
        
        if not query_parts:
            logger.error("No collection type specified!")
            return stats
        
        # Combine with date filter
        full_query = f"({' OR '.join(query_parts)}) AND {date_filter}"
        logger.info(f"Gmail query: {full_query}")
        
        # Use the collector's main method with our custom query
        logger.info("Starting collection...")
        articles_collected = collector.collect_newsletters(
            query=full_query,
            max_results=100  # Should be enough for one day
        )
        
        logger.info(f"Collection completed: {articles_collected} articles processed")
        
        # Get detailed statistics from the database
        db = next(get_db())
        
        # Count today's articles by type
        today_articles = db.query(SubstackArticle).filter(
            SubstackArticle.collected_at >= today_start
        ).all()
        
        for article in today_articles:
            # Check if forwarded or direct based on author
            if article.author and article.author.email in ['robotic@substack.com', 'garymarcus@substack.com', 'sebastianraschka@substack.com']:
                stats['forwarded'] += 1
            else:
                stats['direct'] += 1
        
        stats['total'] = len(today_articles)
        
        # Calculate totals
        stats['total'] = stats['forwarded'] + stats['direct']
        
        # Print summary
        logger.info("\n=== Collection Summary ===")
        logger.info(f"Date: {today_start.strftime('%Y-%m-%d')}")
        logger.info(f"New articles collected: {stats['total']}")
        if include_forwarded:
            logger.info(f"  - Forwarded: {stats['forwarded']}")
        if include_direct:
            logger.info(f"  - Direct: {stats['direct']}")
        logger.info(f"Duplicates skipped: {stats['duplicates']}")
        if stats['errors'] > 0:
            logger.warning(f"Errors encountered: {stats['errors']}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Fatal error during collection: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return stats
    finally:
        if 'db' in locals():
            db.close()


def main():
    """Main entry point with command-line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Collect today's Substack articles from Gmail"
    )
    parser.add_argument(
        '--forwarded-only',
        action='store_true',
        help='Collect only forwarded articles'
    )
    parser.add_argument(
        '--direct-only', 
        action='store_true',
        help='Collect only direct subscription articles'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine what to collect
    include_forwarded = True
    include_direct = True
    
    if args.forwarded_only:
        include_direct = False
        logger.info("Collecting ONLY forwarded articles")
    elif args.direct_only:
        include_forwarded = False
        logger.info("Collecting ONLY direct subscription articles")
    else:
        logger.info("Collecting BOTH forwarded and direct articles")
    
    # Run collection
    stats = collect_todays_articles(
        include_forwarded=include_forwarded,
        include_direct=include_direct
    )
    
    # Exit with appropriate code
    if stats['total'] > 0:
        logger.info(f"\n✅ Successfully collected {stats['total']} new articles from today")
        sys.exit(0)
    elif stats['duplicates'] > 0:
        logger.info("\n⚠️ No new articles found (all were duplicates)")
        sys.exit(0)
    else:
        logger.warning("\n⚠️ No articles found from today")
        sys.exit(1)


if __name__ == "__main__":
    main()