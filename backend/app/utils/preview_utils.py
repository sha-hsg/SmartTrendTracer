"""Shared preview generation for article content.

Single source of truth for turning markdown into a clean text preview.
Previously five call sites each sliced raw markdown[:500], so previews
carried Substack banners, CDN URLs and markdown autolinks — and every
collection run recreated the dirt (DEF-006). The thorough cleaner lived
only behind the manual /api/article-preview endpoints.
"""

import re


def generate_preview(markdown: str, length: int = 500) -> str:
    """Generate a clean text preview from markdown content."""
    if not markdown:
        return ""

    preview = markdown

    # Remove any CDN image references first
    cdn_patterns = [
        r'<img[^>]*src="[^"]*substackcdn\.com[^"]*"[^>]*>',
        r'<img[^>]*src="[^"]*s3\.amazonaws\.com[^"]*"[^>]*>',
        r'!\[[^\]]*\]\([^)]*substackcdn\.com[^)]*\)',
        r'!\[[^\]]*\]\([^)]*s3\.amazonaws\.com[^)]*\)',
        r'https://substackcdn\.com/image/fetch/[^\s\)\'"<]+',
        r'https://[^/]+\.s3\.amazonaws\.com/[^\s\)\'"<]+',
    ]
    for pattern in cdn_patterns:
        preview = re.sub(pattern, '', preview, flags=re.IGNORECASE)

    # Remove local and remaining image references
    preview = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', preview)

    # Remove markdown formatting. The link pattern allows an EMPTY label and
    # angle-bracket autolink targets: `[](<https://...>)` was the single
    # biggest source of preview artifacts (325 affected articles).
    preview = re.sub(r'^#+\s+', '', preview, flags=re.MULTILINE)  # Headers
    preview = re.sub(r'\*{1,3}([^\*]+)\*{1,3}', r'\1', preview)  # Bold/italic
    preview = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', preview)  # Underline emphasis
    preview = re.sub(r'\[([^\]]*)\]\(<?[^\)]*>?\)', r'\1', preview)  # Links (label may be empty)
    preview = re.sub(r'`{1,3}([^`]+)`{1,3}', r'\1', preview)  # Code blocks
    preview = re.sub(r'^>\s+', '', preview, flags=re.MULTILINE)  # Blockquotes
    preview = re.sub(r'^\*\s+', '', preview, flags=re.MULTILINE)  # Bullet points
    preview = re.sub(r'^\-\s+', '', preview, flags=re.MULTILINE)  # Dashes
    preview = re.sub(r'^\d+\.\s+', '', preview, flags=re.MULTILINE)  # Numbered lists
    preview = re.sub(r'\n{3,}', '\n\n', preview)  # Multiple newlines
    preview = re.sub(r'\n+', ' ', preview)  # Convert newlines to spaces
    preview = re.sub(r'\s+', ' ', preview)  # Multiple spaces to single

    # Clean up any HTML entities
    preview = preview.replace('&nbsp;', ' ')
    preview = preview.replace('&amp;', '&')
    preview = preview.replace('&lt;', '<')
    preview = preview.replace('&gt;', '>')
    preview = preview.replace('&quot;', '"')
    preview = preview.replace('&#39;', "'")

    # Remove any remaining HTML tags
    preview = re.sub(r'<[^>]+>', '', preview)

    # Sweep leftovers from nested image-in-link constructs whose inner URL
    # contained parentheses (CDN fetch URLs), e.g. "1600x850.png)](<...>)"
    preview = re.sub(r'\S*\.(?:png|jpe?g|gif|webp|svg)\)+\]?', '', preview, flags=re.IGNORECASE)
    preview = re.sub(r'\]?\(<?[^)>\s]*>?\)', '', preview)
    preview = re.sub(r'\s+', ' ', preview)

    # Trim to length
    preview = preview.strip()
    if len(preview) > length:
        # Try to cut at a sentence boundary
        sentences = preview[:length + 100].split('. ')
        if len(sentences) > 1:
            result = []
            current_length = 0
            for sentence in sentences:
                if current_length + len(sentence) + 2 <= length:  # +2 for ". "
                    result.append(sentence)
                    current_length += len(sentence) + 2
                else:
                    break
            if result:
                preview = '. '.join(result) + '.'
            else:
                preview = preview[:length].rsplit(' ', 1)[0] + '...'
        else:
            preview = preview[:length].rsplit(' ', 1)[0] + '...'

    return preview.strip()
