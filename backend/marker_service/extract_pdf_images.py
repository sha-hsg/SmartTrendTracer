#!/usr/bin/env python3
"""
Extract images from PDF files for Marker service
"""
import os
import io
import logging
from pathlib import Path
from typing import List, Dict, Tuple
from PIL import Image
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

def extract_images_from_pdf(pdf_path: str, output_dir: str, paper_id: int = None) -> List[Dict]:
    """
    Extract all images from a PDF file using PyMuPDF.
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save extracted images
        paper_id: Optional paper ID for naming
    
    Returns:
        List of image metadata dictionaries
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.warning("PyMuPDF not installed, trying with pdf2image...")
        return extract_images_with_pdf2image(pdf_path, output_dir, paper_id)
    
    image_metadata = []
    
    try:
        # Open PDF
        pdf_document = fitz.open(pdf_path)
        
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        image_count = 0
        
        # Iterate through pages
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            
            # Get images on this page
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                # Get image data
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Generate filename
                image_filename = f"_page_{page_num}_Figure_{img_index}.{image_ext}"
                image_path = os.path.join(output_dir, image_filename)
                
                # Save image
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)
                
                # Add to metadata
                image_metadata.append({
                    "filename": image_filename,
                    "path": image_path,
                    "page": page_num,
                    "index": img_index,
                    "format": image_ext
                })
                
                image_count += 1
                logger.info(f"Extracted image {image_filename} from page {page_num}")
        
        pdf_document.close()
        logger.info(f"Successfully extracted {image_count} images from PDF")
        
    except Exception as e:
        logger.error(f"Error extracting images with PyMuPDF: {e}")
        # Try fallback method
        return extract_images_with_pdf2image(pdf_path, output_dir, paper_id)
    
    return image_metadata


def extract_images_with_pdf2image(pdf_path: str, output_dir: str, paper_id: int = None) -> List[Dict]:
    """
    Fallback method to extract images by rendering pages as images.
    """
    image_metadata = []
    
    try:
        from pdf2image import convert_from_path
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Convert PDF pages to images
        pages = convert_from_path(pdf_path, dpi=150)
        
        for i, page in enumerate(pages):
            # Save page as image
            image_filename = f"_page_{i}_full.png"
            image_path = os.path.join(output_dir, image_filename)
            page.save(image_path, 'PNG')
            
            image_metadata.append({
                "filename": image_filename,
                "path": image_path,
                "page": i,
                "index": 0,
                "format": "png"
            })
            
            logger.info(f"Rendered page {i} as {image_filename}")
        
        logger.info(f"Rendered {len(pages)} pages as images")
        
    except ImportError:
        logger.error("pdf2image not installed, cannot extract images")
    except Exception as e:
        logger.error(f"Error extracting images with pdf2image: {e}")
    
    return image_metadata


def extract_and_match_images(pdf_path: str, markdown_text: str, temp_dir: str, paper_id: int) -> Tuple[str, List[Dict]]:
    """
    Extract images from PDF and update markdown references.
    
    Args:
        pdf_path: Path to PDF file
        markdown_text: Markdown text with image references
        temp_dir: Temporary directory for extraction
        paper_id: Paper ID for API URLs
    
    Returns:
        Updated markdown text and image metadata
    """
    import re
    from pathlib import Path
    
    # Extract images to temp directory
    image_metadata = extract_images_from_pdf(pdf_path, temp_dir, paper_id)
    
    if not image_metadata:
        logger.warning("No images extracted from PDF")
        return markdown_text, []
    
    # Find all image references in markdown
    image_refs = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', markdown_text)
    logger.info(f"Found {len(image_refs)} image references in markdown")
    
    # Create mapping of reference names to extracted images
    extracted_files = {img['filename']: img for img in image_metadata}
    
    # Update markdown with extracted images
    updated_markdown = markdown_text
    matched_images = []
    
    for alt_text, ref_path in image_refs:
        ref_name = os.path.basename(ref_path)
        
        # Try to find a matching extracted image
        matched = False
        for filename, img_data in extracted_files.items():
            # Check if reference matches extracted image
            if ref_name in filename or filename in ref_name:
                # Update markdown with API URL
                api_url = f"/api/papers/{paper_id}/images/{filename}"
                old_ref = f"]({ref_path})"
                new_ref = f"]({api_url})"
                updated_markdown = updated_markdown.replace(old_ref, new_ref)
                
                matched_images.append({
                    **img_data,
                    "url": api_url,
                    "alt_text": alt_text
                })
                matched = True
                logger.info(f"Matched {ref_name} to {filename}")
                break
        
        if not matched:
            logger.warning(f"No match found for image reference: {ref_name}")
    
    return updated_markdown, matched_images