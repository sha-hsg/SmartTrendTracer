"""API endpoints for article preview management"""

from fastapi import APIRouter, HTTPException
from app.database.mongodb import get_database
from bson import ObjectId
import re
from typing import Dict
import mdformat

router = APIRouter()

# MongoDB connection
db = get_database()


def beautify_markdown(markdown: str) -> str:
    """
    Beautify markdown content using mdformat.
    Handles tables, GFM features, frontmatter, and footnotes.
    """
    try:
        # Use mdformat with all installed plugins
        # They auto-register when installed
        beautified = mdformat.text(
            markdown,
            options={
                "wrap": 80,  # Wrap lines at 80 characters
                "number": True,  # Number ordered lists with consecutive integers
                "end_of_line": "lf"  # Use LF line endings
            }
        )
        return beautified
    except Exception as e:
        # If mdformat fails, return original
        print(f"mdformat error: {e}")
        return markdown


def generate_preview(markdown: str, length: int = 500) -> str:
    """
    Generate a preview from markdown content.
    Enhanced version with better cleaning.
    """
    if not markdown:
        return ""
    
    # Start with the markdown content
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
    
    # Remove local image references (keep text clean)
    preview = re.sub(r'!\[[^\]]*\]\(/api/articles/[^)]+\)', '', preview)
    
    # Remove markdown formatting
    preview = re.sub(r'^#+\s+', '', preview, flags=re.MULTILINE)  # Headers
    preview = re.sub(r'\*{1,3}([^\*]+)\*{1,3}', r'\1', preview)  # Bold/italic
    preview = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', preview)  # Underline emphasis
    preview = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', preview)  # Links
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
    
    # Trim to length
    preview = preview.strip()
    if len(preview) > length:
        # Try to cut at a sentence boundary
        sentences = preview[:length + 100].split('. ')
        if len(sentences) > 1:
            # Take complete sentences that fit within length
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
                # Fall back to word boundary
                preview = preview[:length].rsplit(' ', 1)[0] + '...'
        else:
            # Fall back to word boundary
            preview = preview[:length].rsplit(' ', 1)[0] + '...'
    
    return preview.strip()


@router.post("/regenerate/{article_id}")
async def regenerate_article_preview(article_id: str) -> Dict:
    """
    Regenerate preview for a specific article
    
    Args:
        article_id: MongoDB ObjectId as string
        
    Returns:
        Dict with success status and new preview
    """
    try:
        # Validate ObjectId
        try:
            obj_id = ObjectId(article_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid article ID format")
        
        # Get the article
        article = db.articles.find_one({'_id': obj_id})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Get markdown content
        markdown = article.get('content_markdown', '')
        if not markdown:
            raise HTTPException(status_code=400, detail="Article has no markdown content")
        
        # Get current preview for comparison
        old_preview = article.get('preview', '')
        
        # Generate new preview
        new_preview = generate_preview(markdown, length=500)
        
        # Update the article
        result = db.articles.update_one(
            {'_id': obj_id},
            {'$set': {'preview': new_preview}}
        )
        
        if result.modified_count == 0 and old_preview == new_preview:
            return {
                'success': True,
                'message': 'Preview unchanged',
                'preview': new_preview,
                'changed': False
            }
        elif result.modified_count > 0:
            # Check if we removed CDN references
            had_cdn = ('substackcdn.com' in old_preview or 's3.amazonaws.com' in old_preview)
            
            return {
                'success': True,
                'message': 'Preview regenerated successfully',
                'preview': new_preview,
                'changed': True,
                'removed_cdn': had_cdn,
                'old_length': len(old_preview),
                'new_length': len(new_preview)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update preview")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error regenerating preview: {str(e)}")


@router.post("/beautify/{article_id}")
async def beautify_article_markdown(article_id: str) -> Dict:
    """
    Beautify the markdown content of an article
    
    Args:
        article_id: MongoDB ObjectId as string
        
    Returns:
        Dict with success status and beautified markdown
    """
    try:
        # Validate ObjectId
        try:
            obj_id = ObjectId(article_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid article ID format")
        
        # Get the article
        article = db.articles.find_one({'_id': obj_id})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Get markdown content
        markdown = article.get('content_markdown', '')
        if not markdown:
            raise HTTPException(status_code=400, detail="Article has no markdown content")
        
        # Beautify the markdown
        beautified = beautify_markdown(markdown)
        
        # Check if it changed
        changed = beautified != markdown
        
        if changed:
            # Update the article with beautified markdown
            result = db.articles.update_one(
                {'_id': obj_id},
                {'$set': {'content_markdown': beautified}}
            )
            
            # Also regenerate the preview with beautified markdown
            new_preview = generate_preview(beautified, length=500)
            db.articles.update_one(
                {'_id': obj_id},
                {'$set': {'preview': new_preview}}
            )
            
            return {
                'success': True,
                'message': 'Markdown beautified successfully',
                'changed': True,
                'markdown_length': len(beautified),
                'preview': new_preview
            }
        else:
            return {
                'success': True,
                'message': 'Markdown is already well-formatted',
                'changed': False,
                'markdown_length': len(markdown)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error beautifying markdown: {str(e)}")
