"""
Content cleaning helpers for Substack email parsing.

Contains:
- remove_substack_footer: Strip footer content (copyright, promo buttons)
- clean_markdown: Remove table artifacts and clean up converted markdown
- validate_and_fix_content: Check conversion quality and fix bad output
"""

import re
import logging

from app.services.aggressive_html_cleaner import AggressiveHTMLCleaner

logger = logging.getLogger(__name__)


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


def clean_markdown(markdown: str) -> str:
    """Clean up converted markdown and remove table artifacts"""
    if not markdown:
        return ""

    # First pass: Remove leading pipe prefixes from lines
    lines = markdown.split('\n')
    depipe_lines = []
    for line in lines:
        # Remove leading pipes while preserving content
        # Patterns like "| | | content" become just "content"
        cleaned_line = re.sub(r'^\s*\|+(\s*\|)*\s*', '', line)

        # If line becomes empty after removing pipes, check if it was originally empty
        if cleaned_line.strip() == '' and line.strip() != '':
            # This was a line with just pipes, skip it
            continue
        depipe_lines.append(cleaned_line)

    # Second pass: Clean image tables (remove pipes around images and their separators)
    lines = depipe_lines
    image_cleaned_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check if this line is an image wrapped in table formatting
        if re.match(r'^\|?\s*!\[.*?\]\(.*?\)\s*\|?\s*$', stripped):
            # Extract just the image markdown
            image_match = re.search(r'!\[.*?\]\(.*?\)', line)
            if image_match:
                image_cleaned_lines.append(image_match.group(0))
                # Check if next line is a separator and skip it
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if ('---|' in next_line or '|---' in next_line or
                        re.match(r'^[\s\-\|]+$', next_line)):
                        i += 1  # Skip the separator
            i += 1
            continue

        # Keep the line for further processing
        image_cleaned_lines.append(line)
        i += 1

    # Third pass: Remove other table artifacts
    lines = image_cleaned_lines
    cleaned_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip table separator lines (---|---|--- patterns)
        if ('---|' in stripped or '|---' in stripped or
            re.match(r'^[\s\-\|]+$', stripped) and '---' in stripped and '|' in stripped):
            # Check if previous line has an image (keep separator if part of image table)
            if i > 0 and '![' in lines[i-1]:
                cleaned_lines.append(line)
            else:
                i += 1
                continue  # Skip this separator
            i += 1
            continue

        # Skip lone pipe characters or pipes with just spaces
        if re.match(r'^\|+\s*\|*\s*\|*$', stripped) or stripped == '|':
            i += 1
            continue

        # Skip lines that are just pipes and spaces (like "| |" or "| | |")
        if re.match(r'^[\|\s]+$', stripped) and '|' in stripped:
            i += 1
            continue

        # Skip lines that are just dashes (but not markdown headers)
        if stripped in ['---', '----', '-----', '------'] or re.match(r'^-+$', stripped):
            # Check if this might be a markdown horizontal rule (needs blank line before)
            # Also check if it's between image links (part of image layout)
            is_hr = i > 0 and lines[i-1].strip() == ''
            is_image_separator = (i > 0 and '![' in lines[i-1]) or (i < len(lines) - 1 and '![' in lines[i+1])

            if is_hr and not is_image_separator:
                # This is a legitimate horizontal rule, keep it
                cleaned_lines.append(line)
            elif is_image_separator:
                # This is part of image layout, skip it
                pass
            # Skip this artifact
            i += 1
            continue

        # Skip multiple consecutive separator lines
        if re.match(r'^-+\s*$', stripped) and len(stripped) > 5:
            # Check context
            if i > 0 and i < len(lines) - 1:
                prev_line = lines[i-1].strip()
                next_line = lines[i+1].strip() if i+1 < len(lines) else ''

                # If surrounded by similar lines, it's probably a table artifact
                if re.match(r'^-+\s*$', prev_line) or re.match(r'^-+\s*$', next_line):
                    i += 1
                    continue

            # Otherwise keep it
            cleaned_lines.append(line)
        else:
            # Keep all other lines
            cleaned_lines.append(line)

        i += 1

    # Join lines back
    markdown = '\n'.join(cleaned_lines)

    # Remove excessive newlines
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)

    # Remove invisible Unicode characters
    markdown = re.sub(r'[\u00AD\u200B\u200C\u200D\uFEFF]+', '', markdown)
    markdown = re.sub(r'[\u00A0]+', ' ', markdown)

    # Remove the weird invisible character strings
    markdown = re.sub(r'(\u034F\s*)+', '', markdown)

    # Remove email footer stuff
    patterns_to_remove = [
        r'Unsubscribe.*?$',
        r'View this email in your browser.*?$',
        r'You received this email because.*?$',
        r'Update your email preferences.*?$'
    ]

    for pattern in patterns_to_remove:
        markdown = re.sub(pattern, '', markdown, flags=re.MULTILINE | re.IGNORECASE)

    return markdown.strip()


def validate_and_fix_content(markdown: str, is_forwarded: bool, check_only: bool = False) -> str:
    """
    Validate that we have actual article content and fix if needed

    Args:
        markdown: The converted markdown
        is_forwarded: Whether this was a forwarded email
        check_only: If True, suppress warnings (used when checking existing articles)

    Returns:
        Validated and potentially fixed markdown
    """
    if not markdown:
        return markdown

    # First, clean invisible characters from the markdown
    # This ensures word counts are accurate and content is clean
    # Note: \u034F is U+034F (COMBINING GRAPHEME JOINER)
    markdown = re.sub(r'[\u00AD\u200B\u200C\u200D\uFEFF\u00A0\u034F]+', ' ', markdown)
    # Preserve line breaks while cleaning extra spaces within lines
    lines = markdown.split('\n')
    cleaned_lines = []
    for line in lines:
        # Clean extra spaces within each line
        cleaned_line = re.sub(r'\s+', ' ', line).strip()
        cleaned_lines.append(cleaned_line)
    markdown = '\n'.join(cleaned_lines)

    # Check for common artifacts that indicate bad conversion
    bad_patterns = [
        r'^\s*:::',  # CSS/div markers
        r'^\s*\|\s*\|\s*$',  # Empty table rows
        r'\{[^}]{20,}\}',  # Long CSS blocks
        r'outlook-id=',  # Outlook artifacts
        r'style=.*font-family',  # Inline styles
        r'#[a-z0-9-]{30,}',  # Long CSS IDs
    ]

    # Count how many bad patterns we find
    bad_pattern_count = 0
    for pattern in bad_patterns:
        if re.search(pattern, markdown[:1000], re.MULTILINE | re.IGNORECASE):
            bad_pattern_count += 1

    # If we have too many artifacts, the conversion failed
    if bad_pattern_count >= 3:
        if not check_only:
            print("  Warning: Detected poor conversion quality, applying aggressive text extraction...")

        # Use aggressive cleaner directly on the markdown to extract just text
        cleaner = AggressiveHTMLCleaner()
        # Convert markdown back to simple HTML for cleaning
        simple_html = markdown.replace('\n', '<br>')
        clean_text = cleaner.extract_clean_text(f"<html><body>{simple_html}</body></html>")

        if clean_text and len(clean_text.split()) > 50:
            markdown = clean_text
            # Clean the extracted text as well
            markdown = re.sub(r'[\u00AD\u200B\u200C\u200D\uFEFF\u00A0\u034F]+', ' ', markdown)
            # Preserve line breaks while cleaning extra spaces within lines
            lines = markdown.split('\n')
            cleaned_lines = []
            for line in lines:
                cleaned_line = re.sub(r'\s+', ' ', line).strip()
                cleaned_lines.append(cleaned_line)
            markdown = '\n'.join(cleaned_lines)
        else:
            if not check_only:
                print("  Error: Could not extract meaningful content from article")

    # Validation: check if we have actual content
    words = markdown.split()

    if len(words) < 50 and not check_only:
        print(f"  Warning: Article seems too short ({len(words)} words)")

    # Check if content is mostly formatting/artifacts
    actual_text = re.sub(r'[^a-zA-Z0-9\s]', '', markdown)
    if len(actual_text) < len(markdown) * 0.3 and not check_only:  # Less than 30% actual text
        print("  Warning: Article contains mostly formatting/special characters")

    return markdown
