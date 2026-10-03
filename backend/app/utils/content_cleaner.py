"""
Content cleaner utility to remove or replace problematic HTML tags
"""
import re

def clean_markdown_content(content: str) -> str:
    """
    Clean markdown content to remove problematic HTML tags that break React
    
    Args:
        content: Raw markdown content
        
    Returns:
        Cleaned markdown content
    """
    if not content:
        return content
    
    # Remove <answer> tags but keep the content inside
    content = re.sub(r'<answer>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</answer>', '', content, flags=re.IGNORECASE)
    
    # Remove other potentially problematic custom tags
    # Add more patterns here if you find other tags causing issues
    problematic_tags = [
        'solution',
        'hint', 
        'question',
        'problem',
        'example'
    ]
    
    for tag in problematic_tags:
        content = re.sub(f'<{tag}>', '', content, flags=re.IGNORECASE)
        content = re.sub(f'</{tag}>', '', content, flags=re.IGNORECASE)
    
    return content

# Substack post header as it lands in converted markdown: optional avatar
# link(s), author link(s), the date line, up to three counters (likes,
# comments, restacks) and "Share". The date line is required so ordinary
# numbers in an article never match.
_SUBSTACK_BYLINE = re.compile(
    r'(?:^|\n)'
    r'(?:\[!\[[^\]\n]*avatar[^\]\n]*\]\([^)\n]*\)\]\(<?[^)\n]*>?\)[ \t]*\n+)*'   # [![X's avatar](img)](<profile>)
    r'(?:\[[^\]\n]+\]\(<?https?://(?:[\w-]+\.)?substack\.com/@[^)\n]*>?\)[^\n]*\n+)*'  # [Author](<profile>) [, and ...]
    r'(?:[A-Z][a-z]{2,8}\.? \d{1,2}, \d{4}[^\n]{0,20}\n+)'                     # Sep 29, 2026 (∙ Paid)
    r'(?:[\d.,]+[kKmM]?[ \t]*\n+){0,3}'                                          # 266 / 16 / 1,104
    r'Share[ \t]*(?:\n|$)'
)


def strip_substack_byline(markdown: str, search_chars: int = 3000) -> str:
    """Remove Substack's post header (avatar, author, date, counters, "Share")
    from the start of an article; the viewer shows author and date itself.
    Only the beginning is searched, so footers and body text are untouched."""
    if not markdown:
        return markdown
    head, tail = markdown[:search_chars], markdown[search_chars:]
    cleaned = _SUBSTACK_BYLINE.sub('\n', head, count=1)
    return re.sub(r'\n{3,}', '\n\n', cleaned) + tail if cleaned != head else markdown
