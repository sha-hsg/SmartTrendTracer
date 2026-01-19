#!/usr/bin/env python3
"""
Comprehensive PDF Processing Test
Tests the complete processing chain with all available services
"""

import sys
import os
import time
import requests
import logging
from pathlib import Path

# Add backend to path
sys.path.append('.')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_service(name: str, url: str, health_endpoint: str = "/health") -> bool:
    """Check if a service is running"""
    try:
        response = requests.get(f"{url}{health_endpoint}", timeout=2)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ {name} is running: {data}")
            return True
        else:
            logger.warning(f"❌ {name} returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.warning(f"❌ {name} is not running at {url}")
        return False
    except Exception as e:
        logger.error(f"❌ {name} check failed: {e}")
        return False

def test_marker_service(pdf_path: str) -> dict:
    """Test Marker service directly"""
    logger.info("\n" + "="*60)
    logger.info("🌟 Testing Marker Service (Best Quality)")
    logger.info("="*60)
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
            data = {
                'force_ocr': 'false',
                'output_format': 'markdown'
            }
            
            logger.info("📤 Sending request to Marker service...")
            response = requests.post(
                "http://localhost:8002/convert",
                files=files,
                data=data,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    content_len = len(result.get('content', ''))
                    logger.info(f"✅ SUCCESS: Processed {content_len} characters")
                    logger.info(f"   Metadata: {result.get('metadata', {})}")
                    logger.info(f"   First 200 chars: {result.get('content', '')[:200]}")
                    return result
                else:
                    logger.error(f"❌ Processing failed: {result.get('error')}")
            else:
                logger.error(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    
    return {"success": False}

def test_mineru_service(pdf_path: str) -> dict:
    """Test MinerU service directly"""
    logger.info("\n" + "="*60)
    logger.info("⭐ Testing MinerU Service (Second Best)")
    logger.info("="*60)
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
            data = {
                'parse_tables': 'false',
                'output_format': 'markdown'
            }
            
            logger.info("📤 Sending request to MinerU service...")
            response = requests.post(
                "http://localhost:8003/convert",
                files=files,
                data=data,
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    content_len = len(result.get('content', ''))
                    logger.info(f"✅ SUCCESS: Processed {content_len} characters")
                    logger.info(f"   Metadata: {result.get('metadata', {})}")
                    logger.info(f"   First 200 chars: {result.get('content', '')[:200]}")
                    return result
                else:
                    logger.error(f"❌ Processing failed: {result.get('message')}")
            else:
                logger.error(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    
    return {"success": False}

def test_pdf_processor_service(pdf_path: str) -> dict:
    """Test the main PDF processor service with fallback chain"""
    logger.info("\n" + "="*60)
    logger.info("🔄 Testing PDF Processor Service (With Fallback Chain)")
    logger.info("="*60)
    
    try:
        from app.services.pdf_processor_service import get_pdf_processor_service
        
        processor = get_pdf_processor_service()
        logger.info(f"📊 Service Status:")
        logger.info(f"   Marker Service: {processor.marker_service_available}")
        logger.info(f"   MinerU Service: {processor.mineru_service_available}")
        logger.info(f"   Fallback (pypdfium2): {processor.fallback_available}")
        
        logger.info("\n🔄 Processing PDF...")
        result = processor.process_pdf(pdf_path)
        
        if result.get('success'):
            logger.info(f"✅ SUCCESS with {result.get('method_used')}")
            logger.info(f"   Time: {result.get('processing_time', 0):.2f}s")
            logger.info(f"   Content: {len(result.get('markdown', ''))} characters")
            logger.info(f"   First 200 chars: {result.get('markdown', '')[:200]}")
        else:
            logger.error(f"❌ FAILED: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

def test_async_processor(pdf_path: str):
    """Test the async PDF processor"""
    logger.info("\n" + "="*60)
    logger.info("⚡ Testing Async PDF Processor")
    logger.info("="*60)
    
    try:
        import asyncio
        from app.services.async_pdf_processor import get_async_pdf_processor
        
        async def run_test():
            processor = get_async_pdf_processor()
            logger.info("🔄 Processing PDF asynchronously...")
            result = await processor.process_pdf_async(pdf_path)
            return result
        
        result = asyncio.run(run_test())
        
        if result.get('success'):
            logger.info(f"✅ SUCCESS with {result.get('method_used')}")
            logger.info(f"   Content: {len(result.get('markdown', ''))} characters")
        else:
            logger.error(f"❌ FAILED: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

def main():
    """Run comprehensive PDF processing tests"""
    
    # Check for test PDF
    test_pdfs = [
        "/var/folders/8_/t8m7dznx1sl_svlp8m33ydw40000gn/T/arxiv_2507.18103.pdf",
        "data/papers/test.pdf",
        "test.pdf"
    ]
    
    pdf_path = None
    for path in test_pdfs:
        if os.path.exists(path):
            pdf_path = path
            break
    
    if not pdf_path:
        logger.error("❌ No test PDF found. Please provide a PDF file path.")
        logger.info("   Usage: python test_pdf_processing_complete.py [pdf_path]")
        if len(sys.argv) > 1:
            pdf_path = sys.argv[1]
            if not os.path.exists(pdf_path):
                logger.error(f"❌ File not found: {pdf_path}")
                return
        else:
            return
    
    logger.info("="*60)
    logger.info("🚀 COMPREHENSIVE PDF PROCESSING TEST")
    logger.info("="*60)
    logger.info(f"📄 Test PDF: {pdf_path}")
    logger.info(f"📏 File size: {os.path.getsize(pdf_path) / 1024:.1f} KB")
    
    # Check services
    logger.info("\n" + "="*60)
    logger.info("🔍 CHECKING SERVICES")
    logger.info("="*60)
    
    services = {
        "Marker Service": ("http://localhost:8002", True),
        "MinerU Service": ("http://localhost:8003", True),
        "Main API": ("http://localhost:8000", False)
    }
    
    service_status = {}
    for name, (url, required) in services.items():
        is_running = check_service(name, url)
        service_status[name] = is_running
        if required and not is_running:
            logger.warning(f"⚠️  {name} is required but not running")
            logger.info(f"   Start with: cd {name.lower().replace(' ', '_')} && ./start_{name.lower().split()[0]}_service.sh")
    
    # Run tests
    results = {}
    
    # Test individual services if running
    if service_status.get("Marker Service"):
        results["Marker Service"] = test_marker_service(pdf_path)
    
    if service_status.get("MinerU Service"):
        results["MinerU Service"] = test_mineru_service(pdf_path)
    
    # Test main processor (with fallback chain)
    results["PDF Processor"] = test_pdf_processor_service(pdf_path)
    
    # Test async processor
    results["Async Processor"] = test_async_processor(pdf_path)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*60)
    
    for test_name, result in results.items():
        if result.get('success'):
            method = result.get('method_used', 'unknown')
            content_len = len(result.get('markdown', result.get('content', '')))
            logger.info(f"✅ {test_name}: SUCCESS ({method}, {content_len} chars)")
        else:
            error = result.get('error', 'Unknown error')[:50]
            logger.info(f"❌ {test_name}: FAILED ({error})")
    
    # Recommendations
    logger.info("\n" + "="*60)
    logger.info("💡 RECOMMENDATIONS")
    logger.info("="*60)
    
    if not service_status.get("Marker Service"):
        logger.info("1. Start Marker Service for best quality:")
        logger.info("   cd marker_service && ./start_marker_service.sh")
    
    if not service_status.get("MinerU Service"):
        logger.info("2. Start MinerU Service as fallback:")
        logger.info("   cd mineru_service && ./start_mineru_service.sh")
    
    if all(service_status.values()):
        logger.info("✅ All services are running! You have the best setup.")
    
    # Test the complete chain
    logger.info("\n" + "="*60)
    logger.info("🔗 TESTING COMPLETE FALLBACK CHAIN")
    logger.info("="*60)
    
    if service_status.get("Marker Service"):
        logger.info("1️⃣  Marker Service (Best) → ✅ Available")
    else:
        logger.info("1️⃣  Marker Service (Best) → ❌ Not running")
    
    if service_status.get("MinerU Service"):
        logger.info("2️⃣  MinerU Service (Good) → ✅ Available")
    else:
        logger.info("2️⃣  MinerU Service (Good) → ❌ Not running")
    
    logger.info("3️⃣  pypdfium2 (Basic) → ✅ Always available")
    
    logger.info("\n✨ Processing will use the first available option")

if __name__ == "__main__":
    main()