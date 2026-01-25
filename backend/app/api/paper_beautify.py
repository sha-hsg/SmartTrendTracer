"""API endpoints for paper markdown beautification"""

import logging
from fastapi import APIRouter, HTTPException
from app.database.mongodb import get_database
from bson import ObjectId
import mdformat
from typing import Dict

logger = logging.getLogger(__name__)

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
        logger.warning(f"mdformat error: {e}")
        return markdown


@router.post("/beautify/{paper_id}")
async def beautify_paper_markdown(paper_id: str) -> Dict:
    """
    Beautify the markdown content of a paper
    
    Args:
        paper_id: MongoDB ObjectId as string
        
    Returns:
        Dict with success status and beautified markdown
    """
    try:
        # Validate ObjectId
        try:
            obj_id = ObjectId(paper_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid paper ID format")
        
        # Get the paper
        paper = db.papers.find_one({'_id': obj_id})
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        # Get markdown content
        markdown = paper.get('content_markdown', '')
        if not markdown:
            raise HTTPException(status_code=400, detail="Paper has no markdown content")
        
        # Beautify the markdown
        beautified = beautify_markdown(markdown)
        
        # Check if it changed
        changed = beautified != markdown
        
        if changed:
            # Update the paper with beautified markdown
            result = db.papers.update_one(
                {'_id': obj_id},
                {'$set': {'content_markdown': beautified}}
            )
            
            return {
                'success': True,
                'message': 'Markdown beautified successfully',
                'changed': True,
                'markdown_length': len(beautified)
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
