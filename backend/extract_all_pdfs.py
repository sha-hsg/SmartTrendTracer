#!/usr/bin/env python3
"""
Extract all PDFs to markdown using MinerU and save to pdf_outputs directory
"""

import os
import subprocess
from pathlib import Path
import shutil

def extract_pdfs():
    """Extract all PDFs and save markdown to pdf_outputs"""
    
    # Create output directory
    output_base = Path("pdf_outputs")
    output_base.mkdir(exist_ok=True)
    
    # Get all PDFs
    pdf_dir = Path("documents")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    print("="*80)
    print("📚 EXTRACTING ALL PDFS TO MARKDOWN")
    print("="*80)
    print(f"Found {len(pdf_files)} PDF files")
    print(f"Output directory: {output_base.absolute()}")
    print("="*80)
    
    for pdf_path in pdf_files:
        pdf_name = pdf_path.stem
        print(f"\n📄 Processing: {pdf_name[:50]}...")
        print("-"*40)
        
        # Run MinerU
        temp_output = f"/tmp/mineru_{pdf_name.replace(' ', '_')}"
        cmd = ['mineru', '-p', str(pdf_path), '-o', temp_output, '-t', 'false']
        
        print(f"Running: {' '.join(cmd[:3])}...")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Find the markdown file
                md_file = Path(temp_output) / pdf_name / "auto" / f"{pdf_name}.md"
                
                if md_file.exists():
                    # Copy to output directory
                    dest = output_base / f"{pdf_name}.md"
                    shutil.copy2(md_file, dest)
                    
                    # Get file stats
                    size = dest.stat().st_size
                    lines = len(dest.read_text().splitlines())
                    
                    print(f"✅ SUCCESS!")
                    print(f"   Output: {dest.name}")
                    print(f"   Size: {size:,} bytes")
                    print(f"   Lines: {lines:,}")
                    
                    # Also copy images if they exist
                    images_dir = Path(temp_output) / pdf_name / "auto" / "images"
                    if images_dir.exists():
                        dest_images = output_base / f"{pdf_name}_images"
                        if dest_images.exists():
                            shutil.rmtree(dest_images)
                        shutil.copytree(images_dir, dest_images)
                        print(f"   Images: Copied to {dest_images.name}")
                else:
                    print(f"❌ Markdown file not found at expected location")
            else:
                print(f"❌ MinerU failed: {result.stderr[:200]}")
                
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout after 300 seconds")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"Output directory: {output_base.absolute()}")
    
    # List all markdown files
    md_files = list(output_base.glob("*.md"))
    if md_files:
        print(f"\n✅ Generated {len(md_files)} markdown files:")
        for md in md_files:
            print(f"   - {md.name}")
    else:
        print("\n❌ No markdown files generated")

if __name__ == "__main__":
    extract_pdfs()