import requests
import tempfile
import os

# Test Marker with a simple PDF to see how it handles images
test_pdf = "data/papers/20250815_220149_4226a804_Chiang_and_Lee_-_2023_-_Can_Large_Language_Models_Be_an_Alternative_to_Hum.pdf"

with open(test_pdf, 'rb') as f:
    files = {'file': ('test.pdf', f, 'application/pdf')}
    data = {
        'output_format': 'markdown',
        'paper_id': '999'  # Test paper ID
    }
    
    response = requests.post(
        "http://localhost:8002/convert",
        files=files,
        data=data,
        timeout=420
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success')}")
        print(f"Images extracted: {result.get('images_extracted', 0)}")
        print(f"Total images: {result.get('images', 0)}")
        
        # Check markdown for image references
        content = result.get('content', '')
        
        # Count image references in markdown
        import re
        img_refs = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
        print(f"\nImage references in markdown: {len(img_refs)}")
        if img_refs:
            print("First few image references:")
            for i, (alt, src) in enumerate(img_refs[:3]):
                print(f"  {i+1}. Alt: '{alt}', Src: '{src}'")
        
        # Save to file for inspection
        with open('test_marker_output.md', 'w') as f:
            f.write(content)
        print("\nMarkdown saved to test_marker_output.md")
    else:
        print(f"Error: {response.status_code}")
