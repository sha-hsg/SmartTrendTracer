#!/usr/bin/env python3
"""
Test working PDF processors - bypassing ones with issues
"""

import os
import time
from pathlib import Path
from app.services.pdf_processor_service import PDFProcessorService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def test_working_processors():
    """Test only the working processors"""
    
    # Initialize service
    service = PDFProcessorService()
    
    # Get all PDFs in documents folder
    pdf_dir = Path("documents")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.error("No PDF files found in documents folder")
        return
    
    logger.info("="*80)
    logger.info("🔬 PDF PROCESSOR TEST - WORKING PROCESSORS ONLY")
    logger.info("="*80)
    logger.info(f"Found {len(pdf_files)} PDF files to test")
    logger.info("")
    
    # Test with each PDF
    for pdf_path in pdf_files:
        pdf_name = pdf_path.name
        logger.info("="*80)
        logger.info(f"📄 Testing: {pdf_name[:50]}...")
        logger.info("="*80)
        
        # Test with auto mode (will try Marker -> MinerU -> Nougat -> fallback)
        logger.info("\n🤖 Testing with AUTO mode (tries all processors in order)...")
        logger.info("-"*40)
        
        try:
            start_time = time.time()
            result = service.process_pdf(str(pdf_path), prefer_method="auto")
            processing_time = time.time() - start_time
            
            if result['success']:
                logger.info(f"✅ SUCCESS with {result.get('method_used', 'unknown')}")
                logger.info(f"   Time: {processing_time:.2f} seconds")
                logger.info(f"   Content: {len(result.get('markdown', ''))} characters")
                
                # Show sample of content
                content = result.get('markdown', '')
                if content:
                    # Get first 200 characters
                    sample = content[:200].replace('\n', ' ')
                    logger.info(f"   Sample: {sample}...")
                    
                    # Look for specific content markers
                    has_headers = '##' in content or '#' in content
                    has_math = '$$' in content or '\\(' in content or '\\[' in content
                    has_tables = '|' in content and '---' in content
                    
                    logger.info(f"   Features: Headers={has_headers}, Math={has_math}, Tables={has_tables}")
            else:
                logger.error(f"❌ FAILED: {result.get('error', 'Unknown error')[:200]}")
                
        except Exception as e:
            logger.error(f"❌ EXCEPTION: {str(e)[:200]}")
        
        logger.info("")
    
    logger.info("="*80)
    logger.info("✅ Test complete!")
    logger.info("")
    logger.info("📊 Summary:")
    logger.info("- Marker: May timeout on complex PDFs (600s timeout)")
    logger.info("- MinerU: Should work with fixed command syntax")
    logger.info("- Nougat: Has compatibility issues with current transformers")
    logger.info("- pypdfium2: Always works but basic quality")

if __name__ == "__main__":
    test_working_processors()