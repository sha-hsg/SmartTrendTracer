#!/usr/bin/env python3
"""Test image serving directly without going through the API"""

from pathlib import Path

# The image we're trying to access
image_path = "42/45/617126/figure_0_8dede0da.jpg"
paper_id = "4245617126"

print(f"Testing image path: {image_path}")
print(f"Paper ID: {paper_id}")
print("=" * 60)

# Method 1: Direct path
direct_path = Path("data/paper_images") / image_path
print(f"Direct path: {direct_path}")
print(f"  Exists: {direct_path.exists()}")

# Method 2: Hierarchical structure
path_parts = image_path.split("/")
if len(path_parts) >= 4:
    hierarchical_id = "/".join(path_parts[:3])  # "42/45/617126"
    filename = "/".join(path_parts[3:])  # "figure_0_8dede0da.jpg"
    hierarchical_path = Path("data/paper_images") / hierarchical_id / filename
    print(f"\nHierarchical path: {hierarchical_path}")
    print(f"  Exists: {hierarchical_path.exists()}")
    
    # Just the directory
    dir_path = Path("data/paper_images") / hierarchical_id
    print(f"\nDirectory: {dir_path}")
    print(f"  Exists: {dir_path.exists()}")
    if dir_path.exists():
        files = list(dir_path.glob("*.jpg"))[:5]
        print(f"  Sample files: {[f.name for f in files]}")

print("\n" + "=" * 60)
print("SUCCESS: Image file is accessible!" if direct_path.exists() else "ERROR: Image file not found")