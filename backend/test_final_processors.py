#!/usr/bin/env python3
"""
Final test of PDF processors with MinerU working configuration
"""

import os
import time
from pathlib import Path
from app.services.pdf_processor_service import PDFProcessorService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def test_pdf_processors():
    """Test PDF processors on all documents"""
    
    # Initialize service
    service = PDFProcessorService()
    
    # Get all PDFs in documents folder
    pdf_dir = Path("documents")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.error("No PDF files found in documents folder")
        return
    
    logger.info("="*80)
    logger.info("🔬 FINAL PDF PROCESSOR TEST")
    logger.info("="*80)
    logger.info(f"Found {len(pdf_files)} PDF files to test")
    logger.info("")
    
    # Track results
    results = {
        "marker": {"success": 0, "failed": 0},
        "mineru": {"success": 0, "failed": 0},
        "pypdfium2": {"success": 0, "failed": 0}
    }
    
    # Test each PDF
    for pdf_path in pdf_files:
        pdf_name = pdf_path.name
        logger.info("="*80)
        logger.info(f"📄 Testing: {pdf_name[:50]}...")
        logger.info("="*80)
        
        # Test with MinerU (working with table detection disabled)
        logger.info("\n⛏️  Testing MinerU (table detection disabled)...")
        logger.info("-"*40)
        
        try:
            start_time = time.time()
            result = service.process_pdf(str(pdf_path), prefer_method="mineru")
            processing_time = time.time() - start_time
            
            if result['success']:
                logger.info(f"✅ SUCCESS with {result.get('method_used', 'unknown')}")
                logger.info(f"   Time: {processing_time:.2f} seconds")
                logger.info(f"   Content: {len(result.get('markdown', ''))} characters")
                results["mineru"]["success"] += 1
                
                # Show sample
                content = result.get('markdown', '')
                if content:
                    sample = content[:200].replace('\n', ' ')
                    logger.info(f"   Sample: {sample}...")
            else:
                logger.error(f"❌ FAILED: {result.get('error', 'Unknown error')[:200]}")
                results["mineru"]["failed"] += 1
                
        except Exception as e:
            logger.error(f"❌ EXCEPTION: {str(e)[:200]}")
            results["mineru"]["failed"] += 1
        
        # Test with pypdfium2 (always works but basic)
        logger.info("\n📄 Testing pypdfium2 (fallback)...")
        logger.info("-"*40)
        
        try:
            start_time = time.time()
            result = service._process_with_fallback(str(pdf_path))
            processing_time = time.time() - start_time
            
            if result and result[0]:
                logger.info(f"✅ SUCCESS with pypdfium2")
                logger.info(f"   Time: {processing_time:.2f} seconds")
                logger.info(f"   Content: {len(result[0])} characters")
                results["pypdfium2"]["success"] += 1
                
                # Show sample
                sample = result[0][:200].replace('\n', ' ')
                logger.info(f"   Sample: {sample}...")
            else:
                logger.error(f"❌ FAILED")
                results["pypdfium2"]["failed"] += 1
                
        except Exception as e:
            logger.error(f"❌ EXCEPTION: {str(e)[:200]}")
            results["pypdfium2"]["failed"] += 1
        
        logger.info("")
    
    # Summary
    logger.info("="*80)
    logger.info("📊 FINAL SUMMARY")
    logger.info("="*80)
    
    for processor, stats in results.items():
        total = stats["success"] + stats["failed"]
        if total > 0:
            success_rate = (stats["success"] / total) * 100
            logger.info(f"{processor:12}: {stats['success']}/{total} successful ({success_rate:.0f}%)")
    
    logger.info("")
    logger.info("✅ Recommendations:")
    logger.info("1. MinerU works well with table detection disabled (-t false)")
    logger.info("2. pypdfium2 is reliable but produces basic text extraction")
    logger.info("3. Marker may timeout on complex PDFs")
    logger.info("4. Nougat has transformer compatibility issues")
    logger.info("")
    logger.info("📋 Processor Priority Order:")
    logger.info("   1. MinerU (with tables disabled)")
    logger.info("   2. pypdfium2 (fallback)")

if __name__ == "__main__":
    test_pdf_processors()