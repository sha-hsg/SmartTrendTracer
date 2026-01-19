#!/usr/bin/env python3
"""
Test script to verify Marker service is running and accessible
"""
import requests
import sys

def test_marker_service():
    """Test if Marker service is accessible"""
    url = "http://localhost:8002/health"
    
    print("Testing Marker Service...")
    print(f"URL: {url}")
    print("-" * 40)
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Marker Service is running!")
            print(f"Status: {data.get('status')}")
            print(f"Marker: {data.get('marker')}")
            print(f"Service: {data.get('service')}")
            print(f"Port: {data.get('port')}")
            
            if data.get('marker') == 'available':
                print("\n🎉 Marker is fully operational and ready to process PDFs!")
            else:
                print("\n⚠️  Marker service is running but Marker is not available")
                print("   Run: cd marker_service && ./setup_marker.sh")
        else:
            print(f"❌ Service returned status code: {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Marker Service")
        print("   The service is not running.")
        print("\n   To start it:")
        print("   1. cd marker_service")
        print("   2. ./start_marker_service.sh")
    except requests.exceptions.Timeout:
        print("❌ Service timeout - took too long to respond")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("-" * 40)

if __name__ == "__main__":
    test_marker_service()