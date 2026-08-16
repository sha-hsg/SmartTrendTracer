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


# Moved to the shared helper so collectors/importers use the same cleaning
from app.services.preview_utils import generate_preview  # noqa: E402,F401


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
