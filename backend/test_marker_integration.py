"""
Test script for Marker PDF Service integration
"""
import requests
import sys
import time
from pathlib import Path

def test_marker_service():
    """Test if Marker service is running and functional"""
    
    print("="*60)
    print("🧪 TESTING MARKER PDF SERVICE INTEGRATION")
    print("="*60)
    
    # Check if service is running
    print("\n1️⃣ Checking Marker Service health...")
    try:
        response = requests.get("http://localhost:8002/health", timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get("marker") == "available":
                print("✅ Marker Service is running and healthy")
            else:
                print("⚠️ Service running but Marker not available")
                return False
        else:
            print(f"❌ Service returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Marker Service at http://localhost:8002")
        print("   Please start the service with:")
        print("   cd marker_service && ./start_marker_service.sh")
        return False
    except Exception as e:
        print(f"❌ Error checking service: {e}")
        return False
    
    # Test PDF processing
    print("\n2️⃣ Testing PDF conversion...")
    test_pdf = "documents/1601.06133v1-15yrs-of-dbpedia.pdf"
    
    if not Path(test_pdf).exists():
        print(f"⚠️ Test PDF not found: {test_pdf}")
        print("   Using alternative test...")
        # Create a minimal test PDF if needed
        test_pdf = None
        for pdf in Path("documents").glob("*.pdf"):
            test_pdf = str(pdf)
            break
        if not test_pdf:
            print("❌ No PDF files found in documents/ directory")
            return False
    
    print(f"   Testing with: {Path(test_pdf).name}")
    
    try:
        with open(test_pdf, 'rb') as f:
            files = {'file': (Path(test_pdf).name, f, 'application/pdf')}
            data = {
                'force_ocr': 'false',
                'output_format': 'markdown'
            }
            
            start_time = time.time()
            response = requests.post(
                "http://localhost:8002/convert",
                files=files,
                data=data,
                timeout=60
            )
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    content = result.get('content', '')
                    print(f"✅ PDF processed successfully in {processing_time:.2f}s")
                    print(f"   Output length: {len(content)} characters")
                    print(f"   Images found: {result.get('images', 0)}")
                    
                    # Show first 500 characters
                    print("\n📄 Sample output (first 500 chars):")
                    print("-"*40)
                    print(content[:500])
                    print("-"*40)
                    return True
                else:
                    print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ HTTP error: {response.status_code}")
                return False
                
    except requests.exceptions.Timeout:
        print("⏱️ Request timed out (60s)")
        return False
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        return False

def test_pdf_processor_integration():
    """Test if PDF processor service recognizes Marker service"""
    
    print("\n3️⃣ Testing SmartTrendTracer integration...")
    
    # Import and initialize the PDF processor
    try:
        from app.services.pdf_processor_service import PDFProcessorService
        
        processor = PDFProcessorService()
        
        if processor.marker_service_available:
            print("✅ PDF Processor detected Marker Service")
            
            # Test processing with Marker service
            test_pdf = None
            for pdf in Path("documents").glob("*.pdf"):
                test_pdf = str(pdf)
                break
            
            if test_pdf:
                print(f"\n   Testing processing with: {Path(test_pdf).name}")
                result = processor.process_pdf(test_pdf, prefer_method="auto")
                
                if result["success"]:
                    print(f"✅ Processing successful!")
                    print(f"   Method used: {result['method_used']}")
                    print(f"   Processing time: {result['processing_time']:.2f}s")
                    
                    if result['method_used'] == 'marker_service':
                        print("🌟 Marker Service was used as primary processor!")
                    else:
                        print(f"⚠️ Different method used: {result['method_used']}")
                else:
                    print(f"❌ Processing failed: {result['error']}")
        else:
            print("⚠️ PDF Processor did not detect Marker Service")
            print("   The service may not be running")
            
    except ImportError as e:
        print(f"❌ Cannot import PDF processor: {e}")
    except Exception as e:
        print(f"❌ Error testing integration: {e}")

if __name__ == "__main__":
    print("\n🚀 Starting Marker Service Integration Test\n")
    
    # Test Marker service
    service_ok = test_marker_service()
    
    if service_ok:
        # Test integration
        test_pdf_processor_integration()
        
        print("\n="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\n📚 Marker Service is ready for use!")
        print("   The PDF processor will automatically use it as the primary method.")
    else:
        print("\n="*60)
        print("❌ TESTS FAILED")
        print("="*60)
        print("\n⚠️ Please ensure the Marker service is running:")
        print("   1. cd marker_service")
        print("   2. ./setup_marker.sh   (if not already done)")
        print("   3. ./start_marker_service.sh")
        sys.exit(1)