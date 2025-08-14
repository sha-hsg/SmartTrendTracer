#!/usr/bin/env python3
"""
Final cleanup to remove remaining table artifacts while preserving images
Specifically targets:
- Lines with just "---|---|---" or similar patterns
- Lone pipe characters "|"
- Multiple consecutive "---" lines
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from app.models import get_db
from app.models.substack import SubstackArticle
import re


def clean_final_artifacts(markdown: str) -> str:
    """
    Remove final table artifacts while preserving images
    """
    if not markdown:
        return ""
    
    lines = markdown.split('\n')
    cleaned_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip table separator lines (---|---|--- patterns)
        # More specific pattern for these separators
        if ('---|' in stripped or '|---' in stripped or 
            re.match(r'^[\s\-\|]+$', stripped) and '---' in stripped and '|' in stripped):
            # Make sure this isn't part of an image table
            # Check if previous line has an image
            if i > 0 and '![' in lines[i-1]:
                # This separator is part of an image table, keep it
                cleaned_lines.append(line)
            else:
                # This is a standalone separator, skip it
                pass
        
        # Skip lone pipe characters
        elif stripped == '|':
            pass
        
        # Skip lines that are just dashes (but not markdown headers)
        elif stripped == '---' or stripped == '----' or stripped == '-----':
            # Check if this might be a markdown horizontal rule (needs blank line before)
            if i > 0 and lines[i-1].strip() == '':
                # This could be a horizontal rule, keep it
                cleaned_lines.append(line)
            else:
                # This is likely a table artifact, skip it
                pass
        
        # Skip multiple consecutive separator lines
        elif re.match(r'^-+\s*$', stripped) and len(stripped) > 5:
            # Check context
            if i > 0 and i < len(lines) - 1:
                prev_line = lines[i-1].strip()
                next_line = lines[i+1].strip() if i+1 < len(lines) else ''
                
                # If surrounded by similar lines, it's probably a table artifact
                if re.match(r'^-+\s*$', prev_line) or re.match(r'^-+\s*$', next_line):
                    pass
                else:
                    cleaned_lines.append(line)
            else:
                # Edge case, skip it
                pass
        
        # Keep all other lines
        else:
            cleaned_lines.append(line)
        
        i += 1
    
    # Join and do final cleanup
    result = '\n'.join(cleaned_lines)
    
    # Remove excessive blank lines
    result = re.sub(r'\n{4,}', '\n\n\n', result)
    
    # Remove trailing whitespace
    result = '\n'.join(line.rstrip() for line in result.split('\n'))
    
    return result.strip()


def main():
    """Clean final artifacts from all Substack articles"""
    print("=" * 60)
    print("Final Artifact Cleanup")
    print("Removing remaining table separators and lone pipes")
    print("=" * 60)
    print(f"Started: {datetime.now()}\n")
    
    db = next(get_db())
    
    # Get all articles
    articles = db.query(SubstackArticle).filter(
        SubstackArticle.content_markdown.isnot(None)
    ).all()
    
    print(f"Found {len(articles)} articles to clean\n")
    
    total_artifacts_removed = 0
    total_images_preserved = 0
    
    for i, article in enumerate(articles, 1):
        try:
            original = article.content_markdown
            
            # Count original artifacts
            orig_separators = len(re.findall(r'^.*---\|---.*$', original, re.MULTILINE))
            orig_lone_pipes = len(re.findall(r'^\s*\|\s*$', original, re.MULTILINE))
            orig_dash_lines = len(re.findall(r'^-{3,}\s*$', original, re.MULTILINE))
            orig_artifacts = orig_separators + orig_lone_pipes + orig_dash_lines
            
            # Count images
            image_count = len(re.findall(r'!\[([^\]]*)\]\(([^\)]+)\)', original))
            
            # Clean the markdown
            cleaned = clean_final_artifacts(original)
            
            # Count new artifacts
            new_separators = len(re.findall(r'^.*---\|---.*$', cleaned, re.MULTILINE))
            new_lone_pipes = len(re.findall(r'^\s*\|\s*$', cleaned, re.MULTILINE))
            new_dash_lines = len(re.findall(r'^-{3,}\s*$', cleaned, re.MULTILINE))
            new_artifacts = new_separators + new_lone_pipes + new_dash_lines
            
            # Count images after cleaning
            new_image_count = len(re.findall(r'!\[([^\]]*)\]\(([^\)]+)\)', cleaned))
            
            # Update the article
            article.content_markdown = cleaned
            
            # Calculate changes
            artifacts_removed = orig_artifacts - new_artifacts
            total_artifacts_removed += artifacts_removed
            
            print(f"[{i}/{len(articles)}] {article.title[:40]}...")
            
            if artifacts_removed > 0:
                print(f"  🧹 Removed {artifacts_removed} artifacts")
                if orig_separators > new_separators:
                    print(f"     - Table separators: {orig_separators - new_separators}")
                if orig_lone_pipes > new_lone_pipes:
                    print(f"     - Lone pipes: {orig_lone_pipes - new_lone_pipes}")
                if orig_dash_lines > new_dash_lines:
                    print(f"     - Dash lines: {orig_dash_lines - new_dash_lines}")
            
            if image_count > 0:
                if new_image_count == image_count:
                    print(f"  ✅ Preserved all {image_count} images")
                    total_images_preserved += image_count
                else:
                    print(f"  ⚠️  Image count changed: {image_count} -> {new_image_count}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Commit changes
    try:
        db.commit()
        print("\n✅ Changes saved to database")
    except Exception as e:
        print(f"\n❌ Error saving: {e}")
        db.rollback()
    
    # Summary
    print("\n" + "=" * 60)
    print("CLEANUP COMPLETE")
    print("=" * 60)
    print(f"🧹 Artifacts removed: {total_artifacts_removed}")
    print(f"🖼️  Images preserved: {total_images_preserved}")
    print(f"\nCompleted: {datetime.now()}")
    
    db.close()


if __name__ == "__main__":
    main()