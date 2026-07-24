"""
Migration Script: Normalize Article Authors

This script migrates all existing articles to use the new normalized author system:
1. Scans all articles for author names
2. Normalizes author names (removes suffixes, etc.)
3. Parses multi-author strings (splits "X and Y")
4. Creates/updates authors in substack_authors collection
5. Links articles to normalized author records
6. Updates article fields with proper author references

Usage:
    python migrate_article_authors.py [--dry-run] [--verbose]
"""

import sys
import argparse
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, '/Users/siehan/Documents/Development/Research/SmartTrendTracer/backend')

from app.services.author_service import AuthorService


def migrate_articles(dry_run=False, verbose=False):
    """
    Migrate all articles to normalized author system.

    Args:
        dry_run: If True, don't make any changes, just report what would be done
        verbose: If True, print detailed information
    """
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer

    # Initialize author service
    author_service = AuthorService(db)

    # Get all articles
    articles = list(db.articles.find({}))
    total_articles = len(articles)

    print(f"\n{'='*70}")
    print(f"Article Author Migration")
    print(f"{'='*70}\n")
    print(f"Found {total_articles} articles to process")
    print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (changes will be applied)'}\n")

    stats = {
        'processed': 0,
        'skipped': 0,
        'normalized': 0,
        'multi_author_split': 0,
        'authors_created': 0,
        'errors': 0
    }

    for idx, article in enumerate(articles, 1):
        article_id = article['_id']
        title = article.get('title', 'Untitled')[:50]

        if verbose:
            print(f"\n[{idx}/{total_articles}] Processing: {title}...")

        try:
            # Get author name from various fields
            author_name = article.get('author_name') or article.get('author')

            if not author_name:
                if verbose:
                    print(f"  ⚠️  No author name found, skipping")
                stats['skipped'] += 1
                continue

            # Parse author string (handles "X and Y" format)
            primary_author_name, co_author_names = author_service.parse_author_string(author_name)

            if not primary_author_name:
                if verbose:
                    print(f"  ⚠️  Could not parse author name: {author_name}")
                stats['skipped'] += 1
                continue

            # Check if normalization changed the name
            if primary_author_name != author_name:
                stats['normalized'] += 1
                if verbose:
                    print(f"  ✓ Normalized: '{author_name}' → '{primary_author_name}'")

            # Check if multi-author article
            if co_author_names:
                stats['multi_author_split'] += 1
                if verbose:
                    print(f"  ✓ Multi-author: Primary='{primary_author_name}', Co-authors={co_author_names}")

            # Find or create primary author
            primary_author_id = author_service.find_or_create_author(
                primary_author_name,
                email=article.get('author_email'),
                auto_create=True
            )

            if not primary_author_id:
                if verbose:
                    print(f"  ✗ Could not find/create primary author")
                stats['errors'] += 1
                continue

            # Check if this is a new author
            existing_author = db.substack_authors.find_one(
                {'_id': primary_author_id, 'created_at': {'$exists': True}}
            )
            if existing_author and (datetime.utcnow() - existing_author['created_at']).seconds < 1:
                stats['authors_created'] += 1
                if verbose:
                    print(f"  + Created new author: {primary_author_name}")

            # Find or create co-authors
            co_author_ids = []
            for co_author_name in co_author_names:
                co_author_id = author_service.find_or_create_author(
                    co_author_name,
                    auto_create=True
                )
                if co_author_id:
                    co_author_ids.append(co_author_id)

            # Update article with normalized author info
            update_data = {
                'primary_author_id': primary_author_id,
                'primary_author_name': primary_author_name,  # Denormalized for display
                'co_author_ids': co_author_ids,
                'co_author_names': co_author_names,  # Denormalized for display
                'author_name': primary_author_name,  # Update to normalized name
                'author_migration_date': datetime.utcnow()
            }

            if not dry_run:
                db.articles.update_one(
                    {'_id': article_id},
                    {'$set': update_data}
                )

            stats['processed'] += 1

            if verbose:
                print(f"  ✓ Updated article with author references")

        except Exception as e:
            stats['errors'] += 1
            print(f"  ✗ Error processing article {article_id}: {e}")

    # Update author statistics
    if not dry_run:
        print("\nUpdating author statistics...")
        all_authors = db.substack_authors.find({})
        for author in all_authors:
            author_service.update_author_stats(author['_id'])

    # Print summary
    print(f"\n{'='*70}")
    print(f"Migration Summary")
    print(f"{'='*70}\n")
    print(f"Total articles: {total_articles}")
    print(f"Processed: {stats['processed']}")
    print(f"Skipped (no author): {stats['skipped']}")
    print(f"Names normalized: {stats['normalized']}")
    print(f"Multi-author articles split: {stats['multi_author_split']}")
    print(f"New authors created: {stats['authors_created']}")
    print(f"Errors: {stats['errors']}")
    print()

    if dry_run:
        print("⚠️  DRY RUN MODE - No changes were made to the database")
        print("Run without --dry-run to apply changes")
    else:
        print("✓ Migration completed successfully!")

    print()


def main():
    parser = argparse.ArgumentParser(
        description='Migrate articles to normalized author system'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without making changes (preview mode)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Print detailed information for each article'
    )

    args = parser.parse_args()

    try:
        migrate_articles(dry_run=args.dry_run, verbose=args.verbose)
    except KeyboardInterrupt:
        print("\n\nMigration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
