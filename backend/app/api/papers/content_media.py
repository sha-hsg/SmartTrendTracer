"""
Paper content media route handlers.

Covers: image serving for processed papers (Marker, MinerU).
"""

import os
from pathlib import Path
from typing import Any, Dict

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from .utils import (
    db,
    logger,
)

router = APIRouter()


@router.get("/{paper_id}/images/{image_path:path}")
def get_paper_image(
    paper_id: str,
    image_path: str
) -> FileResponse:
    """Serve an image for a specific paper"""

    logger.info(f"=== IMAGE REQUEST DEBUG ===")
    logger.info(f"Paper ID: {paper_id}")
    logger.info(f"Image path requested: {image_path}")

    # Get the paper to find its processor and image directory
    paper = None  # Initialize paper variable first
    try:
        # Try to convert to ObjectId if it's a valid format (24 hex chars)
        if len(paper_id) == 24:
            try:
                paper = db.papers.find_one({'_id': ObjectId(paper_id)})
                logger.info(f"Found paper by ObjectId: {paper is not None}")
            except Exception:
                # Not a valid ObjectId, try as old SQLite ID
                paper = None

        # If not found by ObjectId, try as old SQLite ID (integer)
        if paper is None:
            try:
                paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
                logger.info(f"Found paper by SQLite ID {paper_id}: {paper is not None}")
            except Exception:
                logger.warning(f"Could not parse {paper_id} as integer for SQLite ID")
                paper = None

        # If still not found, this might be a converted MongoDB ID (like 4245617128)
        # Search for papers where this could be the converted ID
        if paper is None and paper_id.isdigit():
            # This could be a paper where we converted the last 8 hex chars to int
            # We need to find papers where int(str(_id)[-8:], 16) == int(paper_id)
            # This is expensive, so we'll do a targeted search
            logger.info(f"Searching for paper with converted ID {paper_id}")

            # Get all papers and check their converted IDs
            for p in db.papers.find({}, {'_id': 1, 'title': 1, 'processor_used': 1}):
                mongo_id = str(p['_id'])
                converted_id = int(mongo_id[-8:], 16)
                if converted_id == int(paper_id):
                    logger.info(f"Found paper by converted ID! MongoDB ID: {mongo_id}, converted: {converted_id}")
                    paper = db.papers.find_one({'_id': p['_id']})
                    break

    except Exception as e:
        logger.error(f"Error finding paper: {e}")
        paper = None

    if not paper:
        logger.error(f"Paper not found for ID: {paper_id}")
        raise HTTPException(status_code=404, detail="Paper not found")

    # Determine base path based on processor
    processor = paper.get('processor_used', 'marker')
    logger.info(f"Processor used: {processor}")
    logger.info(f"Paper title: {paper.get('title', 'N/A')}")

    # Check if this is an old paper with SQLite ID (needed for all processors)
    old_sqlite_id = paper.get('old_sqlite_id')
    logger.info(f"Old SQLite ID: {old_sqlite_id}")

    if processor == 'marker' or processor == 'marker_service':
        # Check if we have the marker session ID stored (for old papers)
        marker_metadata = paper.get('marker_metadata', {})
        logger.info(f"Marker metadata: {marker_metadata}")
        session_id = marker_metadata.get('session_id')
        logger.info(f"Session ID: {session_id}")

        # Determine which ID to use for ImageManager
        if old_sqlite_id is not None:
            # This is an old paper migrated from SQLite
            # Images are stored under the old SQLite ID
            paper_id_for_images = old_sqlite_id
            logger.info(f"Using old SQLite ID for images: {paper_id_for_images}")
        else:
            # This is a new paper created after MongoDB migration
            # Convert MongoDB ObjectId to integer for ImageManager
            if len(paper_id) == 24:
                # MongoDB ObjectId - convert to a stable integer
                # Use last 8 hex chars converted to int for uniqueness (same as when calling Marker)
                paper_id_for_images = int(paper_id[-8:], 16)
            else:
                paper_id_for_images = int(paper_id)
            logger.info(f"Using converted MongoDB ID for images: {paper_id_for_images}")

        # Check ImageManager's hierarchical structure
        id_str = str(paper_id_for_images).zfill(6)  # Pad to 6 digits
        image_manager_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) / "data" / "paper_images" / id_str[:2] / id_str[2:4] / id_str[4:]
        logger.info(f"Checking ImageManager path: {image_manager_path}")
        logger.info(f"ImageManager path exists: {image_manager_path.exists()}")

        if image_manager_path.exists():
            # Use ImageManager's location
            base_path = image_manager_path
            logger.info(f"Using ImageManager path: {base_path}")
        elif session_id:
            # Fall back to old session-based directory
            # Use the specific session directory
            marker_base = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) / "marker_service" / "debug_runs" / session_id
            logger.info(f"Marker base path: {marker_base}")
            logger.info(f"Marker base exists: {marker_base.exists()}")

            # Find the subdirectory containing the images
            if marker_base.exists():
                # Look for subdirectories
                subdirs = [d for d in marker_base.iterdir() if d.is_dir()]
                logger.info(f"Found {len(subdirs)} subdirectories: {[str(d.name) for d in subdirs]}")
                if subdirs:
                    # Use the first (and likely only) subdirectory
                    base_path = subdirs[0]
                    logger.info(f"Using subdirectory: {base_path}")
                else:
                    base_path = marker_base
                    logger.info(f"No subdirs, using marker base: {base_path}")
            else:
                # Fallback: try ImageManager path anyway
                base_path = image_manager_path
                logger.warning(f"Session directory not found, using ImageManager path")
        else:
            # No session ID stored, use ImageManager path
            base_path = image_manager_path
            logger.info(f"No session ID in metadata, using ImageManager path: {base_path}")
    elif processor == 'mineru' or processor == 'mineru_service':
        # MinerU uses ImageManager to save images in the same structure as Marker
        # Images are saved in data/paper_images/XX/YY/ZZZZZZ/ format
        logger.info(f"Processing MinerU image, original image_path: {image_path}")

        # First, check if this is a hierarchical path (e.g., "42/45/617126/figure_0_8dede0da.jpg")
        if "/" in image_path and image_path.count("/") >= 3:
            # This looks like a hierarchical path with the ID structure
            # Extract the hierarchical ID from the path
            path_parts = image_path.split("/")
            logger.info(f"Path parts: {path_parts}")

            if len(path_parts) >= 4:  # Should be XX/YY/ZZZZZZ/filename.ext
                hierarchical_id = "/".join(path_parts[:3])  # "42/45/617126"
                filename = "/".join(path_parts[3:])  # "figure_0_8dede0da.jpg"
                base_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) / "data" / "paper_images" / hierarchical_id
                # Update image_path to just the filename for later processing
                image_path = filename
                logger.info(f"Using MinerU hierarchical path: {base_path}")
                logger.info(f"Extracted filename: {filename}")
                logger.info(f"Updated image_path to: {image_path}")
            else:
                # Fallback to standard path
                base_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) / "data" / "paper_images"
                logger.info(f"Using MinerU standard path: {base_path}")
        else:
            # No hierarchy in path, use standard ImageManager location based on paper ID
            # Determine which ID to use for ImageManager
            if old_sqlite_id is not None:
                paper_id_for_images = old_sqlite_id
            else:
                # Convert MongoDB ObjectId to integer for ImageManager
                if len(paper_id) == 24:
                    paper_id_for_images = int(paper_id[-8:], 16)
                else:
                    paper_id_for_images = int(paper_id)

            # Check ImageManager's hierarchical structure
            id_str = str(paper_id_for_images).zfill(6)  # Pad to 6 digits
            base_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) / "data" / "paper_images" / id_str[:2] / id_str[2:4] / id_str[4:]
            logger.info(f"Using MinerU ImageManager path: {base_path}")
    else:
        # Fallback to old paper_images path
        base_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) / "data" / "paper_images"
        logger.info(f"Using fallback path: {base_path}")

    # Now construct the full image path
    # The base_path should already be set correctly above
    # and image_path should be the filename (or relative path within base_path)
    full_image_path = base_path / image_path
    logger.info(f"Trying path: {full_image_path}")
    logger.info(f"Path exists: {full_image_path.exists()}")

    # Get the filename for various fallback attempts
    filename = Path(image_path).name

    # If not found, try just the filename in the base directory
    if not full_image_path.exists():
        full_image_path = base_path / filename
        logger.info(f"Trying filename only: {full_image_path}")
        logger.info(f"Filename path exists: {full_image_path.exists()}")

    # If still not found, check for alternative naming patterns
    if not full_image_path.exists():
        # Try without leading underscore (Marker style names like _page_4_Figure_0.jpeg)
        if filename.startswith('_'):
            alt_filename = filename[1:]
            full_image_path = base_path / alt_filename
            logger.info(f"Trying without underscore: {full_image_path}")
            logger.info(f"Alt path exists: {full_image_path.exists()}")

    # For old papers, try the figure_X_hash.jpeg format
    if not full_image_path.exists() and old_sqlite_id is not None:
        # Old papers might have images like figure_0_1c48ce93.jpeg
        # Try to match by pattern
        # Extract the base name without extension
        base_name = Path(filename).stem
        # Try to find any matching file
        if base_path.exists():
            for file in base_path.iterdir():
                if file.is_file() and base_name in file.name:
                    full_image_path = file
                    logger.info(f"Found matching file by pattern: {full_image_path}")
                    break

    # List files in the directory to help debug
    if not full_image_path.exists() and base_path.exists():
        try:
            files_in_dir = list(base_path.glob("*.jpeg")) + list(base_path.glob("*.jpg")) + list(base_path.glob("*.png"))
            logger.info(f"Files in {base_path}: {[f.name for f in files_in_dir[:10]]}")
        except Exception as e:
            logger.error(f"Error listing directory: {e}")

    if not full_image_path.exists():
        logger.error(f"Image not found after all attempts: {image_path}")
        logger.error(f"Final path tried: {full_image_path}")
        raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")

    # Determine media type based on file extension
    suffix = full_image_path.suffix.lower()
    media_type_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.webp': 'image/webp'
    }
    media_type = media_type_map.get(suffix, 'application/octet-stream')

    # Return the image file
    logger.info(f"=== SERVING IMAGE SUCCESSFULLY ===")
    logger.info(f"Image path: {full_image_path}")
    logger.info(f"Media type: {media_type}")
    logger.info(f"File size: {full_image_path.stat().st_size} bytes")

    return FileResponse(
        path=str(full_image_path),
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=31536000",  # Cache for 1 year
        }
    )
