#!/usr/bin/env python3
"""
Clean Substack footers from articles
Removes copyright information and promotional content from the end of articles

Uses MongoDB for data storage (migrated from SQLite January 2026)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import UpdateOne
from app.database.mongodb import get_database
from app.collectors.substack_content_cleaners import remove_substack_footer

def clean_existing_articles():
    """Clean footers from all existing Substack articles in MongoDB"""
    db = get_database()

    try:
        # Get all articles
        articles = list(db.articles.find({}))

        print(f"🔍 Found {len(articles)} Substack articles to check")

        cleaned_count = 0
        already_clean_count = 0
        skipped_count = 0
        updates = []

        for article in articles:
            # Clean both markdown and HTML content
            cleaned_any = False
            update_fields = {}

            # Get article title for logging
            title = article.get('title', 'Untitled')[:50]

            # Clean markdown content
            content_markdown = article.get('content_markdown', '')
            if content_markdown:
                original_md = content_markdown
                cleaned_md = remove_substack_footer(original_md)

                # Only update if there was actually a change
                if cleaned_md != original_md:
                    update_fields['content_markdown'] = cleaned_md
                    cleaned_any = True
                    removed_chars = len(original_md) - len(cleaned_md)
                    print(f"  ✓ Cleaned markdown for '{title}...' (removed {removed_chars} chars)")
                elif '©' not in original_md and 'Start writing' not in original_md:
                    # Footer was likely already removed manually
                    already_clean_count += 1

            # Clean HTML content field
            content_html = article.get('content_html', '')
            if content_html:
                original_html = content_html
                cleaned_html = remove_substack_footer(original_html)

                if cleaned_html != original_html:
                    update_fields['content_html'] = cleaned_html
                    cleaned_any = True

            # Update preview if content was cleaned
            if cleaned_any:
                cleaned_count += 1
                # Regenerate preview from cleaned markdown
                new_markdown = update_fields.get('content_markdown', content_markdown)
                if new_markdown:
                    from app.services.preview_utils import generate_preview
                    update_fields['preview'] = generate_preview(new_markdown)

                # Prepare bulk update
                updates.append(UpdateOne(
                    {'_id': article['_id']},
                    {'$set': update_fields}
                ))
            elif not content_markdown and not content_html:
                skipped_count += 1

        # Execute bulk update
        if updates:
            result = db.articles.bulk_write(updates)
            print(f"\n✅ Results:")
            print(f"   - Cleaned: {cleaned_count} articles")
            print(f"   - Already clean: {already_clean_count} articles (likely manually cleaned)")
            print(f"   - Skipped (no content): {skipped_count} articles")
            print(f"   - MongoDB operations: {result.modified_count} documents modified")
        else:
            print("\n✅ All articles are already clean")
            if already_clean_count > 0:
                print(f"   - {already_clean_count} articles were already clean")

    except Exception as e:
        print(f"❌ Error cleaning articles: {e}")
        raise

def test_footer_removal():
    """Test the footer removal with sample content"""
    test_cases = [
        # Test case 1: Sebastian Raschka footer - real example
        """This is a long article about machine learning and AI research.
        It contains many paragraphs of valuable content that we want to preserve.
        The article discusses various aspects of neural networks, transformers, and
        the latest developments in the field. This content should remain intact.

        After many more paragraphs of content, we finally reach the footer section.

        © 2025 <span>Raschka AI Research (RAIR) Lab LLC</span> <br/>
        <a href="https://substack.com/redirect/...">Unsubscribe</a>
        ![Start writing](https://substackcdn.com/image/fetch/publish-button@2x.png)
        """,

        # Test case 2: Nathan Lambert footer - real example
        """Here's an interesting article about AI alignment and safety research.
        The content explores various approaches to making AI systems more reliable
        and aligned with human values. This is important work that needs attention.
        Multiple sections discuss different aspects of the problem and potential solutions.

        The main body of the article continues for many more paragraphs...

        © 2025 Interconnects AI, LLC<br/>
        1522 Western Ave STE 24060, Seattle, WA 98101<br/>
        ![Get the app](https://substackcdn.com/image/generic-app-button@2x.png)
        ![Start writing](https://substackcdn.com/image/publish-button@2x.png)
        """,

        # Test case 3: Article that was already manually cleaned
        """Main article text about GPT models and their capabilities.
        This article has been manually edited to remove the footer already.
        It ends naturally without any copyright or promotional content.

        The final paragraph concludes the discussion of the topic."""
    ]

    print("🧪 Testing footer removal...\n")

    for i, test_content in enumerate(test_cases, 1):
        print(f"Test case {i}:")
        print(f"  Original length: {len(test_content)} chars")

        cleaned = remove_substack_footer(test_content)
        print(f"  Cleaned length: {len(cleaned)} chars")
        print(f"  Removed: {len(test_content) - len(cleaned)} chars")

        # Show the cleaned ending
        if cleaned:
            ending = cleaned[-100:] if len(cleaned) > 100 else cleaned
            print(f"  Cleaned ending: ...{ending.strip()}")
        print()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Clean Substack footers from articles")
    parser.add_argument("--test", action="store_true", help="Run test cases")
    parser.add_argument("--clean", action="store_true", help="Clean existing articles in database")

    args = parser.parse_args()

    if args.test:
        test_footer_removal()
    elif args.clean:
        clean_existing_articles()
    else:
        # Default: run both test and clean
        print("=" * 60)
        print("SUBSTACK FOOTER CLEANER")
        print("=" * 60)
        print()
        test_footer_removal()
        print("\n" + "=" * 60)
        print("\nNow cleaning existing articles...")
        print("=" * 60 + "\n")
        clean_existing_articles()
