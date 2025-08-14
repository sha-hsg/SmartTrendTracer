#!/usr/bin/env python3
"""
Test Entity Extraction functionality
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/entities"

def colored(text: str, color: str) -> str:
    """Add color to terminal output"""
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"

def test_endpoint(name: str, method: str, endpoint: str, data: Dict[str, Any] = None) -> bool:
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            return False
        
        if response.status_code == 200:
            print(f"{colored('✓', 'green')} {name}: {colored('SUCCESS', 'green')}")
            return True
        else:
            print(f"{colored('✗', 'red')} {name}: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"{colored('✗', 'red')} {name}: {str(e)}")
        return False

def test_extraction():
    """Test entity extraction with sample text"""
    print(f"\n{colored('Testing Entity Extraction:', 'blue')}")
    
    test_text = "OpenAI announced GPT-5 today. Sam Altman presented it at Microsoft headquarters."
    
    response = requests.post(
        f"{BASE_URL}/extract",
        json={"text": test_text}
    )
    
    if response.status_code == 200:
        data = response.json()
        entities = data.get('entities', [])
        print(f"{colored('✓', 'green')} Extracted {len(entities)} entities:")
        for entity in entities:
            print(f"  - {entity['text']} ({entity['type']}) - {entity['confidence']:.2f} confidence")
        return True
    else:
        print(f"{colored('✗', 'red')} Extraction failed: {response.status_code}")
        return False

def test_article_extraction():
    """Test entity extraction for an article"""
    print(f"\n{colored('Testing Article Entity Extraction:', 'blue')}")
    
    # Get first article ID
    articles_response = requests.get("http://localhost:8000/api/substack/articles?limit=1")
    if articles_response.status_code == 200:
        articles = articles_response.json().get('articles', [])
        if articles:
            article_id = articles[0]['id']
            print(f"Testing with article ID: {article_id}")
            
            response = requests.post(
                f"{BASE_URL}/extract",
                json={"article_id": article_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                entities = data.get('entities', [])
                print(f"{colored('✓', 'green')} Extracted {len(entities)} entities from article")
                
                # Show first 5 entities
                for entity in entities[:5]:
                    print(f"  - {entity['text']} ({entity['type']}) - {entity['confidence']:.2f}")
                
                if len(entities) > 5:
                    print(f"  ... and {len(entities) - 5} more")
                return True
            else:
                print(f"{colored('✗', 'red')} Article extraction failed: {response.status_code}")
                return False
        else:
            print(f"{colored('⚠', 'yellow')} No articles found in database")
            return False
    else:
        print(f"{colored('✗', 'red')} Failed to get articles")
        return False

def main():
    print("=" * 60)
    print(f"{colored('Entity Extraction System Test', 'blue')}")
    print("=" * 60)
    
    # Test endpoints
    tests = [
        ("Schema Endpoint", "GET", "/schema"),
        ("Stats Endpoint", "GET", "/stats"),
    ]
    
    print(f"\n{colored('Testing Basic Endpoints:', 'blue')}")
    results = []
    for test in tests:
        result = test_endpoint(*test)
        results.append(result)
    
    # Test extraction
    results.append(test_extraction())
    
    # Test article extraction
    results.append(test_article_extraction())
    
    # Summary
    print("\n" + "=" * 60)
    print(f"{colored('Summary:', 'blue')}")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"{colored('✓ All tests passed!', 'green')} ({passed}/{total})")
        print(f"\n{colored('Entity Extraction is fully operational!', 'green')}")
        print(f"You can now use the 'Automatic Annotation' feature in the UI.")
    else:
        print(f"{colored('⚠ Some tests failed', 'yellow')} ({passed}/{total} passed)")
        print(f"Check the errors above for details.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()