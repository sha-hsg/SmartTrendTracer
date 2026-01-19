#!/usr/bin/env python3
"""
Remove SQLAlchemy legacy code from the SmartTrendTracer backend.
This script:
1. Backs up files before removing
2. Removes SQLAlchemy model files
3. Removes SQLAlchemy imports from remaining files
4. Cleans up requirements.txt
"""

import os
import shutil
from datetime import datetime
import re

# Create backup directory
backup_dir = f"sqlalchemy_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.makedirs(backup_dir, exist_ok=True)
print(f"Created backup directory: {backup_dir}")

# Files to completely remove (SQLAlchemy models and database configs)
files_to_remove = [
    "app/models/database.py",  # SQLAlchemy database config
    "app/models/collection_state.py",  # SQLAlchemy model
    "app/models/cross_references.py",  # SQLAlchemy model
    "app/models/paper_analysis.py",  # SQLAlchemy model
    "app/models/papers.py",  # SQLAlchemy model
    "app/models/substack.py",  # SQLAlchemy model
    "app/models/tag_instance.py",  # SQLAlchemy model
    "app/models/tag_ontology.py",  # SQLAlchemy model
    "app/models/tag_synonym.py",  # SQLAlchemy model
    "app/models/tweet.py",  # SQLAlchemy model
    "app/models/__init__.py",  # Imports SQLAlchemy models
    
    # Old backup files
    "app/main_sqlite_backup.py",
    "tweet_collector_service_sqlite_backup.py",
    
    # Migration scripts that are no longer needed
    "migrate_sqlite_to_mongodb.py",
    "migrate_sqlite_to_mongodb_complete.py",
    "migrate_tags_to_mongodb.py",
    "migrate_papers_to_concepts.py",
    "remove_sqlite_tag_tables.py",
    "test_mongodb_migration.py",
    
    # Old concept test files
    "test_concept_only_system.py",
    "test_concept_detail.py",
]

# Files that need SQLAlchemy imports removed (but file should remain)
files_to_clean = [
    "app/api/tag_reorganization_async.py",
    "app/api/tag_ontology_v2.py",
    "app/api/tag_ontology_v2_mongodb.py",
    "app/api/papers.py",
    "app/api/substack.py",
    "app/api/orphan_tags.py",
    "app/api/tweets_concepts.py",
    "app/api/papers_concepts.py",
    "app/api/substack_concepts.py",
    "app/api/statistics_concepts.py",
    "app/api/concepts_suggestions.py",
    "app/api/substack_mongodb_patch.py",
    "app/api/papers_mongodb_patch.py",
    "app/services/tag_concept_v2_service.py",
    "app/services/tag_concept_service.py",
    "app/services/tag_service_v2.py",
    "app/services/unified_tag_service.py",
    "app/services/article_summarizer.py",
    "app/services/llm_service.py",
    "app/services/entity_extraction_service.py",
    "app/services/orphan_tag_assigner.py",
]

print("\n=== REMOVING SQLALCHEMY FILES ===")
for file_path in files_to_remove:
    if os.path.exists(file_path):
        # Backup first
        backup_path = os.path.join(backup_dir, file_path)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(file_path, backup_path)
        # Remove file
        os.remove(file_path)
        print(f"✓ Removed: {file_path}")
    else:
        print(f"  Skipped (not found): {file_path}")

print("\n=== CLEANING SQLALCHEMY IMPORTS ===")
for file_path in files_to_clean:
    if os.path.exists(file_path):
        # Backup first
        backup_path = os.path.join(backup_dir, file_path)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(file_path, backup_path)
        
        # Read file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Remove SQLAlchemy imports
        patterns_to_remove = [
            r'^from sqlalchemy.*\n',
            r'^import sqlalchemy.*\n',
            r'^from \.database import.*\n',
            r'^from app\.models\.database import.*\n',
            r'^from \.\.models import.*\n',
            r'^from app\.models import.*\n',
            r'^.*SessionLocal.*\n',
            r'^.*get_db.*\n',
            r'^.*Base.*\n',
        ]
        
        original_lines = content.count('\n')
        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content, flags=re.MULTILINE)
        
        # Remove empty import blocks
        content = re.sub(r'\n\n\n+', '\n\n', content)
        
        # Write cleaned file
        with open(file_path, 'w') as f:
            f.write(content)
        
        new_lines = content.count('\n')
        if new_lines < original_lines:
            print(f"✓ Cleaned: {file_path} (removed {original_lines - new_lines} lines)")
        else:
            print(f"  No changes: {file_path}")
    else:
        print(f"  Skipped (not found): {file_path}")

print("\n=== REMOVING SQLITE DATABASE FILES ===")
sqlite_files = [
    "data/tweets.db",
    "data/substack.db",
    "tweets.db",
    "accounts.db",
]

for db_file in sqlite_files:
    if os.path.exists(db_file):
        # Backup first
        backup_path = os.path.join(backup_dir, db_file)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(db_file, backup_path)
        os.remove(db_file)
        print(f"✓ Removed: {db_file}")
    else:
        print(f"  Not found: {db_file}")

print("\n=== CLEANING REQUIREMENTS.TXT ===")
if os.path.exists("requirements.txt"):
    with open("requirements.txt", 'r') as f:
        lines = f.readlines()
    
    # Backup
    shutil.copy2("requirements.txt", os.path.join(backup_dir, "requirements.txt"))
    
    # Remove SQLAlchemy-related packages
    sqlalchemy_packages = ['sqlalchemy', 'alembic', 'sqlite3']
    cleaned_lines = []
    removed_packages = []
    
    for line in lines:
        package_name = line.split('==')[0].split('>=')[0].split('[')[0].strip().lower()
        if package_name not in sqlalchemy_packages:
            cleaned_lines.append(line)
        else:
            removed_packages.append(line.strip())
    
    with open("requirements.txt", 'w') as f:
        f.writelines(cleaned_lines)
    
    if removed_packages:
        print(f"✓ Removed from requirements.txt:")
        for pkg in removed_packages:
            print(f"  - {pkg}")
    else:
        print("  No SQLAlchemy packages found in requirements.txt")

print("\n=== SUMMARY ===")
print(f"✅ Backup created in: {backup_dir}")
print(f"✅ Removed {len([f for f in files_to_remove if os.path.exists(f)])} SQLAlchemy files")
print(f"✅ Cleaned {len(files_to_clean)} files")
print(f"✅ Removed SQLite database files")
print(f"✅ Updated requirements.txt")

print("\n⚠️  IMPORTANT: Run the following commands to verify:")
print("1. cd backend && python app/main.py  # Test the API")
print("2. python tweet_collector_service.py  # Test tweet collector")
print("3. cd ../frontend && npm start  # Test the UI")

print("\n📁 To restore if needed:")
print(f"cp -r {backup_dir}/* .")