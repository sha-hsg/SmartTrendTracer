#!/usr/bin/env python3
"""
Direct test of image extraction for Marker integration
"""
import fitz  # PyMuPDF
import os
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))
from app.services.image_manager import ImageManager

def extract_and_save_images(pdf_path: str, paper_id: int):
    """Extract images from PDF and save using ImageManager"""
    
    print(f"\n=== Testing image extraction for paper {paper_id} ===")
    print(f"PDF: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found at {pdf_path}")
        return
    
    # Initialize ImageManager
    image_manager = ImageManager()
    
    # Open PDF with PyMuPDF
    pdf_document = fitz.open(pdf_path)
    print(f"PDF has {len(pdf_document)} pages")
    
    image_files = {}
    total_extracted = 0
    
    # Extract images from each page
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        image_list = page.get_images(full=True)
        
        if image_list:
            print(f"\nPage {page_num}: Found {len(image_list)} images")
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                try:
                    # Extract image data
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Create filename matching Marker convention
                    filename = f"_page_{page_num}_Figure_{img_index}.{image_ext}"
                    
                    # Convert to base64 data URL for ImageManager
                    import base64
                    b64_data = base64.b64encode(image_bytes).decode('utf-8')
                    data_url = f"data:image/{image_ext};base64,{b64_data}"
                    
                    image_files[filename] = data_url
                    total_extracted += 1
                    
                    print(f"  - Extracted: {filename} ({len(image_bytes)} bytes)")
                    
                except Exception as e:
                    print(f"  - Error extracting image {img_index}: {e}")
    
    pdf_document.close()
    
    if image_files:
        print(f"\n=== Saving {len(image_files)} images with ImageManager ===")
        
        # Create simple markdown with image references
        markdown = "# Test Document\\n\\n"
        for filename in image_files.keys():
            markdown += f"![]({filename})\\n\\n"
        
        # Process with ImageManager
        updated_markdown, image_metadata = image_manager.process_markdown_images(
            paper_id=paper_id,
            markdown=markdown,
            image_files=image_files,
            processor="pymupdf_test"
        )
        
        print(f"\nImages saved: {len(image_metadata)}")
        if image_metadata:
            print("Saved images (first 10):")
            for img in image_metadata[:10]:
                print(f"  - {img.get('path', 'unknown')} (processor: {img.get('processor', 'unknown')})")
        
        # Check if files actually exist
        paper_image_dir = image_manager.get_paper_image_dir(paper_id)
        if paper_image_dir.exists():
            actual_files = list(paper_image_dir.glob("*"))
            print(f"\nActual files in {paper_image_dir}:")
            for f in actual_files:
                print(f"  - {f.name} ({f.stat().st_size} bytes)")
        else:
            print(f"\nWarning: Image directory not created at {paper_image_dir}")
            
    else:
        print("\nNo images found in PDF")
    
    return total_extracted

# Test with latest paper
if __name__ == "__main__":
    # Get latest paper from database
    import sqlite3
    
    conn = sqlite3.connect("data/tweets.db")
    cursor = conn.cursor()
    
    # Get papers with PDFs
    cursor.execute("""
        SELECT id, title, pdf_path 
        FROM papers 
        WHERE pdf_path IS NOT NULL 
        ORDER BY id DESC 
        LIMIT 3
    """)
    
    papers = cursor.fetchall()
    conn.close()
    
    if papers:
        for paper_id, title, pdf_path in papers:
            print(f"\n{'='*60}")
            print(f"Paper {paper_id}: {title[:50]}...")
            
            # Check if PDF exists at the path
            if os.path.exists(pdf_path):
                extracted = extract_and_save_images(pdf_path, paper_id)
                print(f"Total images extracted: {extracted}")
            else:
                print(f"PDF not found at: {pdf_path}")
                # Try alternative path
                alt_path = f"data/papers/arxiv/arxiv_{pdf_path.split('arxiv_')[-1] if 'arxiv_' in pdf_path else ''}"
                if os.path.exists(alt_path):
                    print(f"Found at alternative path: {alt_path}")
                    extracted = extract_and_save_images(alt_path, paper_id)
                    print(f"Total images extracted: {extracted}")
    else:
        print("No papers with PDFs found in database")