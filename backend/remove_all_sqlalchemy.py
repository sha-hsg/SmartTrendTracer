#!/usr/bin/env python3
"""
Remove ALL SQLAlchemy imports from the entire codebase.
This is a more aggressive cleanup for unused files.
"""

import os
import re
import shutil
from datetime import datetime

# Create backup directory
backup_dir = f"sqlalchemy_final_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.makedirs(backup_dir, exist_ok=True)
print(f"Created backup directory: {backup_dir}")

# Find all Python files with SQLAlchemy imports
files_to_clean = []
for root, dirs, files in os.walk("app/"):
    # Skip __pycache__ directories
    if "__pycache__" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            file_path = os.path.join(root, file)
            with open(file_path, 'r') as f:
                content = f.read()
                if 'sqlalchemy' in content.lower() or 'sessionlocal' in content.lower() or 'get_db' in content.lower():
                    files_to_clean.append(file_path)

print(f"\nFound {len(files_to_clean)} files with SQLAlchemy references")

# Clean each file
for file_path in files_to_clean:
    # Backup first
    backup_path = os.path.join(backup_dir, file_path)
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    shutil.copy2(file_path, backup_path)
    
    # Read file
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_lines = content.count('\n')
    
    # Remove SQLAlchemy imports and related code
    patterns_to_remove = [
        r'^from sqlalchemy.*\n',
        r'^import sqlalchemy.*\n',
        r'^from \.database import.*\n',
        r'^from app\.models\.database import.*\n',
        r'^from \.\.models\.database import.*\n',
        r'^from \.models import.*\n',
        r'^from \.\.models import.*\n',
        r'^from app\.models import.*\n',
        r'^.*SessionLocal.*\n',
        r'^.*get_db.*\n',
        r'^.*Base\.\w+.*\n',
        r'^from app\.models\.\w+ import.*\n',
    ]
    
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content, flags=re.MULTILINE)
    
    # Clean up excessive blank lines
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    # Write cleaned file
    with open(file_path, 'w') as f:
        f.write(content)
    
    new_lines = content.count('\n')
    if new_lines < original_lines:
        print(f"✓ Cleaned: {file_path} (removed {original_lines - new_lines} lines)")

print(f"\n✅ Cleanup complete!")
print(f"📁 Backup saved to: {backup_dir}")
print(f"📁 To restore if needed: cp -r {backup_dir}/* .")