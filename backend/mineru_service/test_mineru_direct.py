#!/usr/bin/env python3
"""
Test MinerU directly in the isolated environment to see where images go
"""
import subprocess
import tempfile
from pathlib import Path
import os
import sys

def test_direct():
    """Run MinerU directly and explore output"""
    
    pdf_path = "../data/papers/20250820_210655_063c556c_2025.acl-long.423.pdf"
    
    if not Path(pdf_path).exists():
        print(f"PDF not found: {pdf_path}")
        return
    
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Output dir: {tmpdir}")
        
        # Run MinerU
        cmd = ['./mineru_env/bin/mineru', '-p', pdf_path, '-o', tmpdir, '-t', 'false']
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return
        
        print("Success! Exploring output...")
        
        # Walk the directory tree
        for root, dirs, files in os.walk(tmpdir):
            level = root.replace(tmpdir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                size = os.path.getsize(os.path.join(root, file))
                print(f'{subindent}{file} ({size} bytes)')
        
        # Look for images specifically
        print("\n" + "="*40)
        print("Image files found:")
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.gif']:
            for img in Path(tmpdir).rglob(ext):
                print(f"  {img.relative_to(tmpdir)}")

if __name__ == "__main__":
    test_direct()