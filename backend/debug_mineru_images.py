#!/usr/bin/env python3
"""
Debug MinerU image extraction to see what's happening
"""
import subprocess
import tempfile
from pathlib import Path
import os

def debug_mineru_extraction():
    """Debug MinerU's image extraction process"""
    
    # Find a test PDF
    pdf_dir = Path("data/papers")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found")
        return
    
    # Use a PDF that likely has images
    test_pdf = pdf_files[0]
    print(f"Testing with: {test_pdf.name}")
    print("=" * 60)
    
    # Create temp directory for output
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Output directory: {tmpdir}")
        
        # Run MinerU directly
        cmd = ['mineru', '-p', str(test_pdf), '-o', tmpdir, '-t', 'false']
        print(f"Running command: {' '.join(cmd)}")
        print("-" * 40)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"MinerU failed: {result.stderr}")
            return
        
        print("MinerU completed successfully!")
        print("-" * 40)
        
        # Explore the output structure
        output_path = Path(tmpdir)
        
        # Find all generated files
        print("\nGenerated file structure:")
        for root, dirs, files in os.walk(tmpdir):
            level = root.replace(tmpdir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files[:10]:  # Limit to first 10 files per dir
                print(f'{subindent}{file}')
            if len(files) > 10:
                print(f'{subindent}... and {len(files) - 10} more files')
        
        print("\n" + "-" * 40)
        
        # Look specifically for images
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(output_path.rglob(f'*{ext}'))
        
        print(f"\nFound {len(image_files)} image files:")
        for img in image_files[:10]:
            rel_path = img.relative_to(output_path)
            print(f"  - {rel_path} ({img.stat().st_size} bytes)")
        
        if len(image_files) > 10:
            print(f"  ... and {len(image_files) - 10} more images")
        
        # Check markdown file for image references
        md_files = list(output_path.rglob("*.md"))
        if md_files:
            print(f"\n{'-' * 40}")
            print(f"Found {len(md_files)} markdown file(s)")
            
            # Read first markdown file
            md_content = md_files[0].read_text(encoding='utf-8')
            
            # Find image references
            import re
            img_refs = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', md_content)
            
            print(f"\nImage references in markdown: {len(img_refs)}")
            for i, (alt, path) in enumerate(img_refs[:5], 1):
                print(f"  {i}. Alt: '{alt[:30]}...', Path: '{path}'")
            
            if len(img_refs) > 5:
                print(f"  ... and {len(img_refs) - 5} more references")
            
            # Check if referenced images exist
            print(f"\n{'-' * 40}")
            print("Checking if referenced images exist:")
            missing = 0
            found = 0
            for alt, img_path in img_refs[:10]:
                # Try to resolve the path
                if img_path.startswith('/'):
                    full_path = output_path / img_path[1:]
                else:
                    full_path = md_files[0].parent / img_path
                
                if full_path.exists():
                    print(f"  ✓ {img_path} -> EXISTS")
                    found += 1
                else:
                    print(f"  ✗ {img_path} -> NOT FOUND")
                    missing += 1
            
            print(f"\nSummary: {found} found, {missing} missing")

if __name__ == "__main__":
    debug_mineru_extraction()