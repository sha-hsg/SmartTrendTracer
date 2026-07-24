#!/usr/bin/env python3
"""
Import a tag hierarchy JSON file to replace the current tag ontology
Usage: python import_tag_hierarchy.py [--file tag-reorganization.json] [--dry-run] [--clear-existing]
"""

import json
import requests
import argparse
import sys
from pathlib import Path

def import_tag_hierarchy(file_path: str, dry_run: bool = False, clear_existing: bool = False, merge_strategy: str = "replace"):
    """Import tag hierarchy from JSON file"""
    
    # Read the JSON file
    if not Path(file_path).exists():
        print(f"❌ Error: File '{file_path}' not found")
        return False
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in file: {e}")
        return False
    
    # Extract hierarchy from the JSON structure
    # The structure might be either direct hierarchy or wrapped in a proposal
    if 'hierarchy' in data:
        hierarchy = data['hierarchy']
    elif 'tags' in data:
        hierarchy = data['tags']
    else:
        # Assume the entire JSON is the hierarchy
        hierarchy = data
    
    print(f"📋 Found {len(hierarchy)} tags in hierarchy")
    
    # Prepare import request
    import_request = {
        "hierarchy": hierarchy,
        "clear_existing": clear_existing,
        "dry_run": dry_run,
        "merge_strategy": merge_strategy
    }
    
    # Send to API
    api_url = "http://localhost:8000/api/tags/reorganize/import"
    
    try:
        if dry_run:
            print("\n🔍 Running DRY RUN to preview changes...")
        else:
            print(f"\n📤 Importing with strategy: {merge_strategy}")
            if clear_existing:
                print("⚠️  WARNING: This will CLEAR all existing tags before importing!")
                confirm = input("Are you sure? Type 'yes' to continue: ")
                if confirm.lower() != 'yes':
                    print("❌ Import cancelled")
                    return False
        
        response = requests.post(api_url, json=import_request)
        
        if response.status_code == 200:
            result = response.json()
            
            if dry_run:
                print("\n✅ Dry run completed successfully!")
                changes = result.get('changes', {})
                
                if changes.get('would_clear'):
                    print("  ⚠️  Would CLEAR all existing tags")
                
                if changes.get('would_add'):
                    print(f"  ➕ Would add {len(changes['would_add'])} new tags:")
                    for tag in changes['would_add'][:10]:
                        print(f"     - {tag}")
                    if len(changes['would_add']) > 10:
                        print(f"     ... and {len(changes['would_add']) - 10} more")
                
                if changes.get('would_update'):
                    print(f"  🔄 Would update {len(changes['would_update'])} existing tags:")
                    for tag in changes['would_update'][:10]:
                        print(f"     - {tag}")
                    if len(changes['would_update']) > 10:
                        print(f"     ... and {len(changes['would_update']) - 10} more")
                
                if changes.get('would_skip'):
                    print(f"  ⏭️  Would skip {len(changes['would_skip'])} tags (already exist)")
                
                print(f"\n📊 Total tags in import: {result.get('total_tags', 0)}")
                print(f"⏱️  Duration: {result.get('duration', 0):.2f} seconds")
                
            else:
                status = result.get('status')
                if status == 'imported':
                    print("✅ Import completed successfully!")
                    
                    results = result.get('results', {})
                    print(f"\n📊 Import Results:")
                    print(f"  ✅ Concepts created: {results.get('concepts_created', 0)}")
                    print(f"  🔄 Concepts updated: {results.get('concepts_updated', 0)}")
                    print(f"  🔗 Tags merged: {results.get('tags_merged', 0)}")
                    print(f"  📝 Synonyms created: {results.get('synonyms_created', 0)}")
                    
                    if results.get('errors'):
                        print(f"\n⚠️  Errors encountered:")
                        for error in results['errors']:
                            print(f"  - {error}")
                    
                    print(f"\n⏱️  Duration: {result.get('duration', 0):.2f} seconds")
                    
                elif status == 'failed':
                    print("❌ Import failed!")
                    results = result.get('results', {})
                    if results.get('errors'):
                        print("Errors:")
                        for error in results['errors']:
                            print(f"  - {error}")
                else:
                    print(f"⚠️  Import status: {status}")
                    print(json.dumps(result, indent=2))
            
            return True
            
        else:
            print(f"❌ API error: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   {error_detail}")
            except:
                print(f"   {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API. Is the backend running on http://localhost:8000?")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='Import tag hierarchy from JSON file')
    parser.add_argument('--file', '-f', 
                       default='tag-reorganization.json',
                       help='Path to JSON file (default: tag-reorganization.json)')
    parser.add_argument('--dry-run', '-d', 
                       action='store_true',
                       help='Preview changes without applying them')
    parser.add_argument('--clear-existing', '-c',
                       action='store_true', 
                       help='Clear all existing tags before importing')
    parser.add_argument('--strategy', '-s',
                       choices=['replace', 'merge', 'append'],
                       default='replace',
                       help='Merge strategy: replace (default), merge, or append')
    
    args = parser.parse_args()
    
    print("🏷️  SmartTrendTracer Tag Hierarchy Importer")
    print("=" * 50)
    print(f"📁 File: {args.file}")
    print(f"🔧 Strategy: {args.strategy}")
    print(f"🗑️  Clear existing: {args.clear_existing}")
    print(f"👁️  Dry run: {args.dry_run}")
    print("=" * 50)
    
    success = import_tag_hierarchy(
        file_path=args.file,
        dry_run=args.dry_run,
        clear_existing=args.clear_existing,
        merge_strategy=args.strategy
    )
    
    if not success:
        sys.exit(1)
    
    if args.dry_run:
        print("\n💡 To apply these changes, run without --dry-run flag")


if __name__ == "__main__":
    main()