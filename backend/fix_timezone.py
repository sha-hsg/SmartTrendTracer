#!/usr/bin/env python3
"""
Fix timezone issues in the codebase
Replaces datetime.utcnow() with datetime.now(timezone.utc)
"""
import os
import re

def fix_file(filepath):
    """Fix timezone issues in a single file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Check if timezone is imported
    if 'from datetime import' in content and 'timezone' not in content:
        # Add timezone to imports
        content = re.sub(
            r'from datetime import ([^\\n]+)',
            lambda m: f"from datetime import {m.group(1)}, timezone" if 'timezone' not in m.group(1) else m.group(0),
            content,
            count=1
        )
    
    # Replace datetime.utcnow() with datetime.now(timezone.utc)
    content = content.replace('datetime.utcnow()', 'datetime.now(timezone.utc)')
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    print("🔧 Fixing timezone issues...")
    print("=" * 50)
    
    # Files to fix
    files_to_fix = [
        'app/models/collection_state.py',
        'app/collectors/twitter_collector.py',
        'app/rate_limiter.py',
        'app/api/collection.py',
        'app/analyzers/trend_analyzer.py',
        'app/smart_startup_collector.py',
        'app/startup_collector.py',
        'test_startup_collection.py',
        'reset_rate_limit.py',
        'collect_tweets.py'
    ]
    
    fixed_count = 0
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            if fix_file(filepath):
                print(f"✅ Fixed: {filepath}")
                fixed_count += 1
        else:
            print(f"⚠️  Not found: {filepath}")
    
    print(f"\n✅ Fixed {fixed_count} files")
    print("   All datetime.utcnow() replaced with datetime.now(timezone.utc)")

if __name__ == "__main__":
    main()