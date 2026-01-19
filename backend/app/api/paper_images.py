"""
API endpoints for paper image management
"""

from fastapi import APIRouter, HTTPException, Response, Path as PathParam, Depends
from fastapi.responses import FileResponse
from typing import Optional
import logging
from pathlib import Path

from ..services.image_manager import get_image_manager
from ..models.papers import Paper

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/papers",
    tags=["paper-images"]
)

@router.get("/{paper_id}/images/{image_path:path}")
async def get_paper_image(
    paper_id: int = PathParam(..., description="Paper ID"),
    image_path: str = PathParam(..., description="Image path or filename"),
):
    """
    Serve an image for a specific paper
    
    Args:
        paper_id: The paper ID
        image_path: The image filename or relative path
        
    Returns:
        The image file
    """
    # Verify paper exists
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get image manager
    image_manager = get_image_manager()
    
    # Get image path
    full_path = image_manager.get_image_path(paper_id, image_path)
    
    if not full_path or not full_path.exists():
        logger.warning(f"Image not found: paper_id={paper_id}, path={image_path}")
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Determine content type
    suffix = full_path.suffix.lower()
    content_type_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.webp': 'image/webp'
    }
    content_type = content_type_map.get(suffix, 'application/octet-stream')
    
    # Return the image file
    return FileResponse(
        path=str(full_path),
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
            "X-Paper-Id": str(paper_id)
        }
    )

@router.get("/{paper_id}/images")
async def list_paper_images(
    paper_id: int,
):
    """
    List all images for a paper
    
    Args:
        paper_id: The paper ID
        
    Returns:
        List of image metadata
    """
    # Verify paper exists
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get image manager
    image_manager = get_image_manager()
    
    # Get paper image directory
    paper_dir = image_manager.get_paper_image_dir(paper_id)
    
    if not paper_dir.exists():
        return {"images": [], "total": 0}
    
    # List all images
    images = []
    for img_file in paper_dir.glob("*"):
        if img_file.is_file() and img_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']:
            # Get relative path
            rel_path = img_file.relative_to(image_manager.base_path)
            
            # Determine type from filename
            img_type = "other"
            if "equation" in img_file.name:
                img_type = "equation"
            elif "table" in img_file.name:
                img_type = "table"
            elif "figure" in img_file.name or "diagram" in img_file.name:
                img_type = "figure"
            
            images.append({
                "filename": img_file.name,
                "path": str(rel_path),
                "url": f"/api/papers/{paper_id}/images/{rel_path}",
                "size_bytes": img_file.stat().st_size,
                "type": img_type
            })
    
    # Sort by filename
    images.sort(key=lambda x: x["filename"])
    
    return {
        "paper_id": paper_id,
        "images": images,
        "total": len(images)
    }

@router.get("/{paper_id}/image-stats")
async def get_paper_image_stats(
    paper_id: int,
):
    """
    Get image statistics for a paper
    
    Args:
        paper_id: The paper ID
        
    Returns:
        Image statistics
    """
    # Verify paper exists
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get image manager
    image_manager = get_image_manager()
    
    # Get statistics
    stats = image_manager.get_paper_image_stats(paper_id)
    
    return {
        "paper_id": paper_id,
        "paper_title": paper.title,
        **stats
    }

@router.delete("/{paper_id}/images")
async def delete_paper_images(
    paper_id: int,
):
    """
    Delete all images for a paper
    
    Args:
        paper_id: The paper ID
        
    Returns:
        Success status
    """
    # Verify paper exists
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get image manager
    image_manager = get_image_manager()
    
    # Delete images
    success = image_manager.delete_paper_images(paper_id)
    
    if success:
        return {"message": f"Deleted all images for paper {paper_id}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete images")