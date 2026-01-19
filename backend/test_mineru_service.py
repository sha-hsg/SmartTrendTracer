#!/usr/bin/env python3
"""
Test script to verify MinerU service is running and accessible
"""
import requests
import sys

def test_mineru_service():
    """Test if MinerU service is accessible"""
    url = "http://localhost:8003/health"
    
    print("Testing MinerU Service...")
    print(f"URL: {url}")
    print("-" * 40)
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ MinerU Service is running!")
            print(f"Status: {data.get('status')}")
            print(f"MinerU: {data.get('mineru')}")
            print(f"Service: {data.get('service')}")
            print(f"Port: {data.get('port')}")
            
            if data.get('mineru') == 'available':
                print("\n🎉 MinerU is fully operational and ready to process PDFs!")
            else:
                print("\n⚠️  MinerU service is running but MinerU CLI is not available")
                print("   Run: cd mineru_service && ./setup_mineru.sh")
        else:
            print(f"❌ Service returned status code: {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to MinerU Service")
        print("   The service is not running.")
        print("\n   To start it:")
        print("   1. cd mineru_service")
        print("   2. ./start_mineru_service.sh")
    except requests.exceptions.Timeout:
        print("❌ Service timeout - took too long to respond")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("-" * 40)

if __name__ == "__main__":
    test_mineru_service()