#!/usr/bin/env python3
"""
Test script to verify PDF processing services status
"""
import requests
import sys

def test_service(name, url, port):
    """Test if a service is accessible"""
    print(f"\n{'='*50}")
    print(f"Testing {name}...")
    print(f"URL: {url}")
    print("-" * 40)
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {name} is running!")
            print(f"   Status: {data.get('status')}")
            service_key = name.lower().split()[0]  # "Marker Service" -> "marker"
            print(f"   {service_key.capitalize()}: {data.get(service_key)}")
            print(f"   Port: {port}")
            
            if data.get(service_key) == 'available':
                print(f"\n   🎉 {name} is fully operational!")
                return True
            else:
                print(f"\n   ⚠️  Service running but {service_key} not available")
                return False
        else:
            print(f"❌ Service returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {name}")
        print(f"   The service is not running on port {port}")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ {name} timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Test all PDF processing services"""
    print("\n" + "="*50)
    print("PDF PROCESSING SERVICES STATUS CHECK")
    print("="*50)
    
    services = [
        ("Marker Service", "http://localhost:8002/health", 8002),
        ("MinerU Service", "http://localhost:8003/health", 8003),
    ]
    
    results = []
    for name, url, port in services:
        results.append(test_service(name, url, port))
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("-" * 40)
    
    all_running = all(results)
    any_running = any(results)
    
    if all_running:
        print("✅ All PDF processing services are operational!")
        print("\nYour system is ready for high-quality PDF processing:")
        print("  • Marker Service: Best for general PDFs")
        print("  • MinerU Service: Best for math-heavy and complex layouts")
    elif any_running:
        print("⚠️  Some services are not running:")
        for i, (name, _, port) in enumerate(services):
            if not results[i]:
                print(f"  ❌ {name} (port {port}) - Not available")
        print("\nTo start missing services:")
        if not results[0]:  # Marker
            print("  cd marker_service && ./start_marker_service.sh")
        if not results[1]:  # MinerU
            print("  cd mineru_service && ./start_mineru_service.sh")
    else:
        print("❌ No PDF processing services are running!")
        print("\nTo start the services:")
        print("  1. Marker: cd marker_service && ./start_marker_service.sh")
        print("  2. MinerU: cd mineru_service && ./start_mineru_service.sh")
        print("\nThe system will fall back to basic PDF extraction (lower quality)")
    
    print("="*50)

if __name__ == "__main__":
    main()