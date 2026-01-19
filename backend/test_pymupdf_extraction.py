#!/usr/bin/env python3
"""
Test PyMuPDF image extraction directly
"""
import fitz  # PyMuPDF
import os
from pathlib import Path

def test_extract_images(pdf_path: str):
    """Test extracting images from a PDF"""
    print(f"Testing image extraction from: {pdf_path}")
    
    # Open PDF
    pdf_document = fitz.open(pdf_path)
    total_images = 0
    
    # Check each page
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        
        # Get images on this page
        image_list = page.get_images(full=True)
        
        if image_list:
            print(f"\nPage {page_num}: Found {len(image_list)} images")
            for img_index, img in enumerate(image_list):
                xref = img[0]
                try:
                    # Extract image
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    print(f"  - Image {img_index}: {len(image_bytes)} bytes, format: {image_ext}")
                    total_images += 1
                except Exception as e:
                    print(f"  - Image {img_index}: Error extracting - {e}")
    
    pdf_document.close()
    print(f"\nTotal images found: {total_images}")
    return total_images

# Test with one of our papers
test_pdf = "data/papers/20250815_220149_4226a804_Chiang_and_Lee_-_2023_-_Can_Large_Language_Models_Be_an_Alternative_to_Hum.pdf"

if os.path.exists(test_pdf):
    images_found = test_extract_images(test_pdf)
    if images_found == 0:
        print("\nNo images found in PDF. The PDF might have:")
        print("- Embedded vector graphics instead of raster images")
        print("- Images that are part of the page content stream")
        print("- Content that looks like images but is actually rendered text/shapes")
else:
    print(f"Test PDF not found: {test_pdf}")
    print("\nTrying to find any PDF in papers directory...")
    papers_dir = Path("data/papers")
    if papers_dir.exists():
        pdfs = list(papers_dir.glob("*.pdf"))
        if pdfs:
            print(f"Found {len(pdfs)} PDFs, testing first one: {pdfs[0]}")
            test_extract_images(str(pdfs[0]))