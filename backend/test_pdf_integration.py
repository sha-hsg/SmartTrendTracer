#!/usr/bin/env python3
"""
Test PDF processing integration in SmartTrendTracer
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.pdf_processor_service import PDFProcessorService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def test_integration():
    """Test PDF processor integration"""
    
    logger.info("="*80)
    logger.info("🔧 TESTING PDF PROCESSOR INTEGRATION")
    logger.info("="*80)
    
    # Initialize the service
    logger.info("\n1️⃣ Initializing PDF Processor Service...")
    service = PDFProcessorService()
    
    # Check if MinerU is available
    if not service.mineru_available:
        logger.error("❌ MinerU is not available! Please ensure it's installed.")
        logger.error("   Run: pip install mineru")
        return False
    
    logger.info("✅ MinerU is available and configured as primary processor")
    
    # Test with a sample PDF
    pdf_files = list(Path("documents").glob("*.pdf"))
    if not pdf_files:
        logger.warning("⚠️  No PDF files found in documents folder")
        return False
    
    # Test the first PDF
    test_pdf = pdf_files[0]
    logger.info(f"\n2️⃣ Testing with: {test_pdf.name[:50]}...")
    
    result = service.process_pdf(str(test_pdf))
    
    if result['success']:
        logger.info(f"✅ SUCCESS!")
        logger.info(f"   Method used: {result['method_used']}")
        logger.info(f"   Processing time: {result['processing_time']:.2f}s")
        logger.info(f"   Content length: {len(result['markdown'])} characters")
        
        # Check if it used MinerU
        if result['method_used'] == 'mineru':
            logger.info("✅ MinerU was used as expected")
        else:
            logger.warning(f"⚠️  Used {result['method_used']} instead of MinerU")
        
        return True
    else:
        logger.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
        return False

def check_dependencies():
    """Check all required dependencies"""
    
    logger.info("\n3️⃣ Checking Dependencies...")
    logger.info("-"*40)
    
    dependencies = {
        "mineru": "MinerU CLI",
        "pypdfium2": "Fallback processor",
        "rapid_table": "Table detection (should be v1.0.5)"
    }
    
    all_ok = True
    
    for module, description in dependencies.items():
        try:
            if module == "mineru":
                import subprocess
                result = subprocess.run(['mineru', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    logger.info(f"✅ {description}: Available")
                else:
                    logger.error(f"❌ {description}: Not available")
                    all_ok = False
            else:
                __import__(module)
                logger.info(f"✅ {description}: Installed")
        except (ImportError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.error(f"❌ {description}: Not installed")
            all_ok = False
    
    return all_ok

def main():
    """Main test function"""
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Test integration
    integration_ok = test_integration()
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("📊 INTEGRATION TEST SUMMARY")
    logger.info("="*80)
    
    if deps_ok and integration_ok:
        logger.info("✅ All tests passed! PDF processing is ready.")
        logger.info("\n📝 Configuration:")
        logger.info("   - Primary processor: MinerU (with table detection disabled)")
        logger.info("   - Fallback processor: pypdfium2")
        logger.info("   - Output format: Markdown with preserved LaTeX formulas")
        logger.info("   - Image extraction: Enabled")
    else:
        logger.error("❌ Some tests failed. Please check the errors above.")
        if not deps_ok:
            logger.error("\n🔧 Fix dependencies:")
            logger.error("   pip install mineru")
            logger.error("   pip install rapid_table==1.0.5")

if __name__ == "__main__":
    main()