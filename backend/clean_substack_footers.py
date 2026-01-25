#!/usr/bin/env python3
"""
Clean Substack footers from articles
Removes copyright information and promotional content from the end of articles

Uses MongoDB for data storage (migrated from SQLite January 2026)
"""
import re
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import UpdateOne
from app.database.mongodb import get_database

def remove_substack_footer(content: str) -> str:
    """
    Remove Substack footer content including copyright and promotional buttons

    Patterns to remove:
    - Copyright notice (© 2025 Author/Company)
    - Address information
    - Unsubscribe/disable email links
    - "Start writing" promotional buttons
    - "Get the app" promotional buttons
    - Associated images and links
    """
    if not content:
        return content

    # Define patterns for footer detection
    footer_patterns = [
        # Copyright patterns - match © year followed by author/company name
        r'©\s*\d{4}\s*<span[^>]*>.*?</span>',
        r'©\s*\d{4}\s*[^<\n]+(?:<br\s*/?>|\n)',

        # Address patterns (e.g., "548 Market Street PMB 72296, San Francisco, CA 94104")
        r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)(?:\s+PMB\s+\d+)?[,\s]+[A-Za-z\s]+,?\s+[A-Z]{2}\s+\d{5}(?:-\d{4})?',

        # Substack specific unsubscribe/disable email links
        r'<a[^>]*href=["\']https://substack\.com/redirect/[^"\']*disable_email[^"\']*["\'][^>]*>.*?</a>',
        r'<a[^>]*href=["\']https://[^"\']*\.substack\.com/action/disable_email[^"\']*["\'][^>]*>.*?</a>',

        # "Start writing" button images and links
        r'<a[^>]*>\s*<img[^>]*(?:Start writing|publish-button)[^>]*>\s*</a>',
        r'!\[Start writing\]\([^)]+\)',

        # "Get the app" button images and links
        r'<a[^>]*>\s*<img[^>]*(?:Get the app|generic-app-button)[^>]*>\s*</a>',
        r'!\[Get the app\]\([^)]+\)',

        # Standalone promotional images
        r'<img[^>]*(?:publish-button|generic-app-button)[^>]*>',
        r'!\[(?:Start writing|Get the app)\]\([^)]+\)',

        # Substack redirect links
        r'<a[^>]*href=["\']https://substack\.com/redirect/[^"\']*signup[^"\']*["\'][^>]*>.*?</a>',
    ]

    # First, try to find where the footer starts
    # Look for copyright symbol as the main indicator
    copyright_match = re.search(r'©\s*\d{4}', content)

    if copyright_match:
        # Found copyright, remove everything from this point onwards
        footer_start = copyright_match.start()

        # Check if there's substantial content before the copyright
        # (to avoid removing the entire article if © appears early)
        if footer_start > 500:  # Only remove if copyright appears after 500 chars
            content = content[:footer_start].rstrip()
        else:
            # Copyright appears too early, try pattern-based removal instead
            for pattern in footer_patterns:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)

    # Also check for address patterns as footer indicators (even without copyright)
    address_match = re.search(r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)(?:\s+PMB\s+\d+)?[,\s]+[A-Za-z\s]+,?\s+[A-Z]{2}\s+\d{5}', content)
    if address_match and address_match.start() > 500:
        # Found an address that looks like a footer, remove from there
        content = content[:address_match.start()].rstrip()

    # Always try to remove promotional content patterns
    for pattern in footer_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)

    # Clean up any trailing whitespace, empty links, or broken markdown
    content = re.sub(r'\n{3,}', '\n\n', content)  # Remove excessive newlines
    content = re.sub(r'<a[^>]*>\s*</a>', '', content)  # Remove empty links
    content = re.sub(r'<span[^>]*>\s*</span>', '', content)  # Remove empty spans
    content = re.sub(r'(?:<br\s*/?>[\s\n]*)+$', '', content)  # Remove trailing <br> tags and whitespace
    content = re.sub(r'[\s\n]*<br\s*/?>\s*$', '', content)  # Remove final br tags

    # Final cleanup of trailing HTML artifacts
    content = re.sub(r'<a href="[^"]*">\s*$', '', content)  # Remove empty trailing links
    content = re.sub(r'\s*</?(?:span|div|p)>\s*$', '', content)  # Remove empty trailing tags

    return content.strip()

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
                    preview_text = new_markdown[:500].strip()
                    update_fields['preview'] = preview_text + '...' if len(new_markdown) > 500 else preview_text

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
