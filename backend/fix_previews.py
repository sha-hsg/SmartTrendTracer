#!/usr/bin/env python3
"""
Fix previews for forwarded Substack articles by extracting clean text from markdown

Uses MongoDB for data storage (migrated from SQLite January 2026)
"""
import sys
import os
import re
import json
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import UpdateOne
from app.database.mongodb import get_database
from bs4 import BeautifulSoup

def extract_clean_text_from_markdown(markdown_content):
    """Extract clean readable text from markdown content with HTML artifacts"""
    if not markdown_content:
        return ""

    # Use BeautifulSoup to parse and extract text from HTML elements
    soup = BeautifulSoup(markdown_content, 'html.parser')

    # Extract plain text from HTML
    text = soup.get_text()

    # Clean up markdown syntax
    # Remove markdown headers
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)

    # Remove markdown links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Remove markdown formatting
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
    text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__
    text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_
    text = re.sub(r'`([^`]+)`', r'\1', text)        # `code`

    # Remove bullet points and numbers
    text = re.sub(r'^[•\-\*]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)

    # Clean whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines
    text = re.sub(r'^\s+|\s+$', '', text)    # Trim
    text = re.sub(r'\s+', ' ', text)         # Multiple spaces

    # Remove common email artifacts
    artifacts_to_remove = [
        r'View in browser.*?(?=\n\n|\Z)',
        r'Unsubscribe.*?(?=\n\n|\Z)',
        r'You received this email.*?(?=\n\n|\Z)',
    ]

    for pattern in artifacts_to_remove:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

    # Final cleanup
    text = text.strip()

    # Create preview (first 500 chars)
    if len(text) > 500:
        # Try to cut at sentence boundary
        cutoff = text.rfind('.', 400, 500)
        if cutoff == -1:
            cutoff = text.rfind(' ', 400, 500)
        if cutoff == -1:
            cutoff = 500
        text = text[:cutoff].strip()
        if not text.endswith('...'):
            text += '...'

    return text

def load_forwarded_authors():
    """Load forwarded author names from forwarded_authors.json (next to this script)"""
    config_path = Path(__file__).resolve().parent / 'forwarded_authors.json'
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return [author['name'] for author in config.get('forwarded_authors', [])]
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Warning: could not load {config_path} ({e}); no forwarded authors configured")
        return []

def main():
    """Fix previews for forwarded articles"""
    db = get_database()

    # Get forwarded authors from config
    forwarded_authors = load_forwarded_authors()

    print("FIXING PREVIEWS FOR FORWARDED SUBSTACK ARTICLES")
    print("=" * 60)
    print()

    total_fixed = 0
    updates = []

    for author_name in forwarded_authors:
        author = db.substack_authors.find_one({'name': author_name})
        if not author:
            print(f"Author '{author_name}' not found")
            continue

        # Find articles by this author (try multiple ways to match)
        articles = list(db.articles.find({
            '$or': [
                {'author_id': author['_id']},
                {'author_name': author_name},
                {'author_sqlite_id': author.get('old_sqlite_id')}
            ]
        }))

        print(f"Processing {author_name} ({len(articles)} articles):")

        fixed_for_author = 0
        for article in articles:
            # Check if preview needs fixing (has HTML artifacts or is too short)
            current_preview = article.get('preview', '') or ''
            needs_fixing = (
                len(current_preview.strip()) < 50 or
                '<' in current_preview or
                'data-outlook-id' in current_preview or
                'href=' in current_preview or
                'substackcdn.com' in current_preview
            )

            if needs_fixing:
                # Generate clean preview from markdown content
                content = article.get('content_markdown', '')
                clean_text = extract_clean_text_from_markdown(content)

                if clean_text and len(clean_text) > 50:
                    title = article.get('title', 'Untitled')[:50]
                    print(f"  Fixing: {title}...")
                    print(f"      Old: \"{current_preview[:60]}...\"")
                    print(f"      New: \"{clean_text[:60]}...\"")

                    updates.append(UpdateOne(
                        {'_id': article['_id']},
                        {'$set': {'preview': clean_text}}
                    ))
                    fixed_for_author += 1
                    total_fixed += 1
                else:
                    title = article.get('title', 'Untitled')[:50]
                    print(f"  Could not extract clean text: {title}...")
            else:
                title = article.get('title', 'Untitled')[:50]
                print(f"  Already clean: {title}...")

        print(f"     Fixed {fixed_for_author}/{len(articles)} articles")
        print()

    # Commit changes
    if updates:
        print(f"Saving {total_fixed} preview fixes...")
        result = db.articles.bulk_write(updates)
        print(f"All previews fixed! ({result.modified_count} modified)")
    else:
        print("No previews needed fixing")

    # Show results
    print()
    print("RESULTS:")
    print("-" * 30)

    for author_name in forwarded_authors:
        author = db.substack_authors.find_one({'name': author_name})
        if not author:
            continue

        articles = list(db.articles.find({
            '$or': [
                {'author_id': author['_id']},
                {'author_name': author_name}
            ]
        }))
        print(f"\n{author_name}:")

        for article in articles:
            preview = (article.get('preview', '') or '')[:80]
            has_artifacts = '<' in preview or 'data-outlook-id' in preview
            status = 'NEEDS FIX' if has_artifacts else 'OK'
            title = article.get('title', 'Untitled')[:45]
            print(f"  [{status}] {title}...")
            print(f"      \"{preview}...\"")

if __name__ == "__main__":
    main()
