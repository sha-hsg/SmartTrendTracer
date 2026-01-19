#!/usr/bin/env python3
"""
Extract and save images from Marker output
"""
import os
import re
import logging
import base64
from pathlib import Path
from typing import Dict, List, Tuple
import shutil

logger = logging.getLogger(__name__)

def extract_marker_images(rendered_output, temp_dir: str, paper_id: int) -> Tuple[str, List[Dict]]:
    """
    Extract images from Marker output and save them to the paper images directory.
    Returns updated markdown with proper image URLs.
    """
    from marker.schema import RenderedDocument
    
    # Create paper image directory
    image_base_dir = Path("../data/paper_images")
    
    # Use hierarchical structure for scalability
    id_str = str(paper_id)
    if len(id_str) >= 3:
        subdir1 = id_str[-3]
        subdir2 = id_str[-2]
        subdir3 = id_str[-1]
        paper_image_dir = image_base_dir / subdir1 / subdir2 / subdir3 / f"paper_{paper_id}"
    else:
        paper_image_dir = image_base_dir / f"paper_{paper_id}"
    
    paper_image_dir.mkdir(parents=True, exist_ok=True)
    
    markdown_text = ""
    image_metadata = []
    
    # Get markdown text
    if hasattr(rendered_output, 'markdown'):
        markdown_text = rendered_output.markdown
    elif hasattr(rendered_output, 'text'):
        markdown_text = rendered_output.text
    else:
        # Try to extract text
        try:
            from marker.renderers.markdown import MarkdownRenderer
            renderer = MarkdownRenderer()
            markdown_text = renderer(rendered_output)
        except:
            logger.warning("Could not extract markdown from rendered output")
            return "", []
    
    # Find all image references in markdown
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    image_refs = re.findall(image_pattern, markdown_text)
    
    logger.info(f"Found {len(image_refs)} image references in markdown")
    
    # Process each image reference
    for alt_text, image_path in image_refs:
        image_name = os.path.basename(image_path)
        
        # Check if image exists in temp directory
        temp_image_path = os.path.join(temp_dir, image_path)
        if not os.path.exists(temp_image_path):
            # Try without leading underscore or path
            temp_image_path = os.path.join(temp_dir, image_name)
        
        if os.path.exists(temp_image_path):
            # Copy image to paper directory
            dest_path = paper_image_dir / image_name
            try:
                shutil.copy2(temp_image_path, dest_path)
                logger.info(f"Copied image {image_name} to {dest_path}")
                
                # Update markdown with API URL
                api_url = f"/api/papers/{paper_id}/images/{image_name}"
                markdown_text = markdown_text.replace(f"]({image_path})", f"]({api_url})")
                
                # Add to metadata
                image_metadata.append({
                    "filename": image_name,
                    "path": str(dest_path),
                    "url": api_url,
                    "alt_text": alt_text
                })
            except Exception as e:
                logger.error(f"Failed to copy image {image_name}: {e}")
        else:
            logger.warning(f"Image not found in temp directory: {image_path}")
            
            # Check if Marker included the image data directly
            if hasattr(rendered_output, 'images'):
                # Look for image in rendered output
                for idx, img_data in enumerate(rendered_output.images):
                    if isinstance(img_data, dict) and 'data' in img_data:
                        # Save base64 image
                        try:
                            image_data = base64.b64decode(img_data['data'])
                            dest_path = paper_image_dir / f"image_{idx}.png"
                            with open(dest_path, 'wb') as f:
                                f.write(image_data)
                            
                            # Update markdown
                            api_url = f"/api/papers/{paper_id}/images/image_{idx}.png"
                            markdown_text = markdown_text.replace(f"]({image_path})", f"]({api_url})")
                            
                            image_metadata.append({
                                "filename": f"image_{idx}.png",
                                "path": str(dest_path),
                                "url": api_url,
                                "alt_text": alt_text
                            })
                            logger.info(f"Saved embedded image as image_{idx}.png")
                            break
                        except Exception as e:
                            logger.error(f"Failed to save embedded image: {e}")
    
    return markdown_text, image_metadata