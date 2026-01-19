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