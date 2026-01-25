#!/usr/bin/env python3
"""
Test article summarization functionality

Uses MongoDB for data storage (migrated from SQLite January 2026)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pymongo import UpdateOne
from bson import ObjectId
from app.database.mongodb import get_database
from app.services.article_summarizer import ArticleSummarizer


def main():
    print("=" * 60)
    print("Article Summarization Test")
    print("=" * 60)

    db = get_database()
    summarizer = ArticleSummarizer()

    # Get unsummarized articles
    # Filter for articles that haven't been summarized and aren't deleted
    query = {
        '$or': [
            {'summarized': False},
            {'summarized': {'$exists': False}},
            {'summary': {'$exists': False}},
            {'summary': None},
            {'summary': ''}
        ],
        'deleted': {'$ne': True}
    }

    unsummarized = list(db.articles.find(query).limit(5))

    if not unsummarized:
        print("\n✅ All articles are already summarized!")
        # Show some stats
        total = db.articles.count_documents({})
        summarized = db.articles.count_documents({'summarized': True})
        print(f"   Total articles: {total}")
        print(f"   Summarized: {summarized}")
        return

    print(f"\n Found {len(unsummarized)} unsummarized articles")

    updates = []
    for i, article in enumerate(unsummarized, 1):
        title = article.get('title', 'Untitled')
        print(f"\n{i}. {title[:60]}...")

        # Get author info
        author_name = article.get('author_name', 'Unknown')
        if not author_name or author_name == 'Unknown':
            # Try to look up author
            author_id = article.get('author_id')
            if author_id:
                try:
                    if isinstance(author_id, ObjectId) or (isinstance(author_id, str) and len(author_id) == 24):
                        author = db.substack_authors.find_one({'_id': ObjectId(author_id) if isinstance(author_id, str) else author_id})
                    else:
                        # Try numeric ID
                        author = db.substack_authors.find_one({'old_sqlite_id': int(author_id)})
                    if author:
                        author_name = author.get('name', 'Unknown')
                except:
                    pass

        print(f"   Author: {author_name}")

        # Get word count
        content = article.get('content_markdown', '') or article.get('content_html', '')
        word_count = len(content.split()) if content else 0
        print(f"   Words: {word_count}")

        if not content or len(content.strip()) < 100:
            print("   ⚠️ Skipping - insufficient content")
            continue

        try:
            print("   ⏳ Generating summary...")
            result = summarizer.summarize_article_content(
                content=content,
                title=title,
                author=author_name
            )
            print("   ✅ Summary generated!")
            print(f"   Key points: {len(result.get('key_points', []))}")
            print(f"   Model: {result.get('model_used', 'unknown')}")

            # Prepare update
            updates.append(UpdateOne(
                {'_id': article['_id']},
                {'$set': {
                    'summary': result['summary'],
                    'key_points': result.get('key_points', []),
                    'summarized': True,
                    'summary_model': result.get('model_used', 'unknown')
                }}
            ))

        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Apply all updates
    if updates:
        result = db.articles.bulk_write(updates)
        print(f"\n✅ Updated {result.modified_count} articles in MongoDB")


def summarize_all(limit: int = 50):
    """Summarize all unsummarized articles up to a limit"""
    print("=" * 60)
    print(f"Batch Article Summarization (limit: {limit})")
    print("=" * 60)

    db = get_database()
    summarizer = ArticleSummarizer()

    # Get unsummarized articles
    query = {
        '$or': [
            {'summarized': False},
            {'summarized': {'$exists': False}},
            {'summary': {'$exists': False}},
            {'summary': None},
            {'summary': ''}
        ],
        'deleted': {'$ne': True}
    }

    unsummarized = list(db.articles.find(query).limit(limit))

    if not unsummarized:
        print("\n✅ All articles are already summarized!")
        return

    print(f"\n Found {len(unsummarized)} unsummarized articles")

    success_count = 0
    error_count = 0
    updates = []

    for i, article in enumerate(unsummarized, 1):
        title = article.get('title', 'Untitled')
        author_name = article.get('author_name', 'Unknown')
        content = article.get('content_markdown', '') or article.get('content_html', '')

        print(f"\n[{i}/{len(unsummarized)}] {title[:50]}...")

        if not content or len(content.strip()) < 100:
            print("   ⚠️ Skipping - insufficient content")
            continue

        try:
            result = summarizer.summarize_article_content(
                content=content,
                title=title,
                author=author_name
            )

            updates.append(UpdateOne(
                {'_id': article['_id']},
                {'$set': {
                    'summary': result['summary'],
                    'key_points': result.get('key_points', []),
                    'summarized': True,
                    'summary_model': result.get('model_used', 'unknown')
                }}
            ))
            success_count += 1
            print(f"   ✅ Done ({len(result.get('key_points', []))} key points)")

        except Exception as e:
            error_count += 1
            print(f"   ❌ Error: {e}")

    # Apply all updates
    if updates:
        result = db.articles.bulk_write(updates)
        print(f"\n{'=' * 60}")
        print(f"✅ Batch Complete:")
        print(f"   Successful: {success_count}")
        print(f"   Errors: {error_count}")
        print(f"   MongoDB updated: {result.modified_count}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Summarize Substack articles")
    parser.add_argument("--all", action="store_true", help="Summarize all unsummarized articles")
    parser.add_argument("--limit", type=int, default=50, help="Limit for batch mode (default: 50)")

    args = parser.parse_args()

    if args.all:
        summarize_all(limit=args.limit)
    else:
        main()
