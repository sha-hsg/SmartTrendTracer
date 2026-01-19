#!/usr/bin/env python3
"""
Comprehensive test of all PDF processors on all documents
Tests Marker, MinerU, and Nougat on each PDF in the documents folder
"""

import os
import time
import json
from pathlib import Path
from app.services.pdf_processor_service import PDFProcessorService
from tabulate import tabulate
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def test_all_processors():
    """Test all PDF processors on all documents"""
    
    # Initialize service
    service = PDFProcessorService()
    
    # Get all PDFs in documents folder
    pdf_dir = Path("documents")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.error("No PDF files found in documents folder")
        return
    
    logger.info("="*80)
    logger.info("🔬 COMPREHENSIVE PDF PROCESSOR TEST")
    logger.info("="*80)
    logger.info(f"Found {len(pdf_files)} PDF files to test")
    logger.info("")
    
    # Processors to test
    processors = ["marker", "mineru", "nougat"]
    
    # Results storage
    results = {}
    
    # Test each PDF with each processor
    for pdf_path in pdf_files:
        pdf_name = pdf_path.name
        logger.info("="*80)
        logger.info(f"📄 Testing: {pdf_name}")
        logger.info("="*80)
        
        results[pdf_name] = {}
        
        for processor in processors:
            logger.info(f"\n🔧 Testing with {processor.upper()}...")
            logger.info("-"*40)
            
            try:
                # Process the PDF
                start_time = time.time()
                result = service.process_pdf(str(pdf_path), prefer_method=processor)
                processing_time = time.time() - start_time
                
                if result['success']:
                    # Store results
                    results[pdf_name][processor] = {
                        'success': True,
                        'method_used': result.get('method_used', processor),
                        'processing_time': round(processing_time, 2),
                        'content_length': len(result.get('markdown', '')),
                        'sample': result.get('markdown', '')[:200] + '...' if result.get('markdown') else 'No content',
                        'error': None
                    }
                    
                    logger.info(f"✅ SUCCESS with {result.get('method_used', processor)}")
                    logger.info(f"   Time: {processing_time:.2f} seconds")
                    logger.info(f"   Content: {len(result.get('markdown', ''))} characters")
                    logger.info(f"   Sample: {result.get('markdown', '')[:100]}...")
                else:
                    results[pdf_name][processor] = {
                        'success': False,
                        'method_used': None,
                        'processing_time': round(processing_time, 2),
                        'content_length': 0,
                        'sample': None,
                        'error': result.get('error', 'Unknown error')
                    }
                    logger.error(f"❌ FAILED: {result.get('error', 'Unknown error')[:100]}")
                    
            except Exception as e:
                results[pdf_name][processor] = {
                    'success': False,
                    'method_used': None,
                    'processing_time': 0,
                    'content_length': 0,
                    'sample': None,
                    'error': str(e)
                }
                logger.error(f"❌ EXCEPTION: {str(e)[:100]}")
            
            # Small delay between processors
            time.sleep(1)
    
    # Generate comparison report
    logger.info("\n" + "="*80)
    logger.info("📊 COMPARISON REPORT")
    logger.info("="*80)
    
    # Create summary table
    table_data = []
    headers = ["PDF File", "Marker", "MinerU", "Nougat", "Best Processor"]
    
    for pdf_name, pdf_results in results.items():
        row = [pdf_name[:30] + "..." if len(pdf_name) > 30 else pdf_name]
        
        best_processor = None
        best_content_length = 0
        
        for processor in processors:
            if processor in pdf_results:
                result = pdf_results[processor]
                if result['success']:
                    status = f"✅ {result['content_length']} chars"
                    status += f" ({result['processing_time']}s)"
                    
                    # Track best processor (most content extracted)
                    if result['content_length'] > best_content_length:
                        best_content_length = result['content_length']
                        best_processor = processor
                else:
                    status = f"❌ Failed"
            else:
                status = "⏭️ Skipped"
            row.append(status)
        
        # Add best processor
        if best_processor:
            row.append(f"⭐ {best_processor.upper()}")
        else:
            row.append("❌ All failed")
        
        table_data.append(row)
    
    # Print table
    print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Calculate statistics
    logger.info("\n📈 STATISTICS:")
    logger.info("-"*40)
    
    for processor in processors:
        successful = sum(1 for pdf_results in results.values() 
                        if processor in pdf_results and pdf_results[processor]['success'])
        total = len(results)
        success_rate = (successful / total * 100) if total > 0 else 0
        
        avg_time = 0
        avg_content = 0
        if successful > 0:
            times = [pdf_results[processor]['processing_time'] 
                    for pdf_results in results.values() 
                    if processor in pdf_results and pdf_results[processor]['success']]
            contents = [pdf_results[processor]['content_length'] 
                       for pdf_results in results.values() 
                       if processor in pdf_results and pdf_results[processor]['success']]
            avg_time = sum(times) / len(times)
            avg_content = sum(contents) / len(contents)
        
        logger.info(f"\n{processor.upper()}:")
        logger.info(f"  Success Rate: {success_rate:.1f}% ({successful}/{total})")
        if successful > 0:
            logger.info(f"  Avg Time: {avg_time:.2f} seconds")
            logger.info(f"  Avg Content: {avg_content:.0f} characters")
    
    # Save detailed results to JSON
    output_file = "pdf_processor_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n💾 Detailed results saved to: {output_file}")
    logger.info("\n✅ Test complete!")

if __name__ == "__main__":
    test_all_processors()