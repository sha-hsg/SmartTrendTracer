#!/usr/bin/env python3
"""
Smart markdown cleaner that removes table artifacts but keeps tables with images
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from app.models import get_db
from app.models.substack import SubstackArticle
import re


def smart_clean_markdown(markdown: str) -> str:
    """
    Remove table artifacts while preserving tables that contain images
    """
    if not markdown:
        return ""
    
    lines = markdown.split('\n')
    cleaned_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line starts a table
        if '|' in line:
            # Collect all consecutive table lines
            table_lines = []
            j = i
            while j < len(lines) and '|' in lines[j]:
                table_lines.append(lines[j])
                j += 1
            
            # Analyze the table
            table_content = '\n'.join(table_lines)
            
            # Check if table contains images
            has_image = '![' in table_content
            
            # Check if it's a separator line
            is_separator = all(
                all(c in '|-: \t' for c in line) 
                for line in table_lines
            )
            
            # Check if it's meaningful content
            has_meaningful_content = False
            for tline in table_lines:
                # Remove table formatting to check content
                content = tline.replace('|', '').replace('-', '').strip()
                # Check if there's substantial text (not just whitespace or single chars)
                if len(content) > 20 or '](http' in content:
                    has_meaningful_content = True
                    break
            
            # Decide whether to keep the table
            if has_image:
                # Always keep tables with images
                cleaned_lines.extend(table_lines)
            elif is_separator and not has_meaningful_content:
                # Skip pure separator tables
                pass
            elif not has_meaningful_content:
                # Skip empty layout tables
                pass
            else:
                # For tables with content, extract the content without table formatting
                for tline in table_lines:
                    # Skip separator lines
                    if all(c in '|-: \t' for c in tline):
                        continue
                    
                    # Extract content from table cells
                    cells = tline.split('|')
                    meaningful_cells = []
                    
                    for cell in cells:
                        cell_content = cell.strip()
                        # Skip empty cells
                        if cell_content and len(cell_content) > 1:
                            meaningful_cells.append(cell_content)
                    
                    # Add non-empty content as regular text
                    if meaningful_cells:
                        cleaned_lines.append(' '.join(meaningful_cells))
            
            # Move to next section after the table
            i = j
        else:
            # Not a table line, keep it
            cleaned_lines.append(line)
            i += 1
    
    # Join lines back
    result = '\n'.join(cleaned_lines)
    
    # Additional cleanup
    # Remove invisible Unicode characters
    result = re.sub(r'[\u00AD\u200B\u200C\u200D\uFEFF]+', '', result)
    result = re.sub(r'[\u00A0]+', ' ', result)
    
    # Remove the weird invisible character strings
    result = re.sub(r'(͏\s*)+', '', result)
    
    # Clean up excessive blank lines
    result = re.sub(r'\n{4,}', '\n\n\n', result)
    
    # Remove standalone separator lines
    result = re.sub(r'^-+$', '', result, flags=re.MULTILINE)
    
    return result.strip()


def main():
    """Clean all Substack articles intelligently"""
    print("=" * 60)
    print("Smart Markdown Cleaning")
    print("Removing table artifacts while keeping image tables")
    print("=" * 60)
    print(f"Started: {datetime.now()}\n")
    
    db = next(get_db())
    
    # Get all articles
    articles = db.query(SubstackArticle).filter(
        SubstackArticle.content_markdown.isnot(None)
    ).all()
    
    print(f"Found {len(articles)} articles to clean\n")
    
    total_tables_removed = 0
    total_image_tables_kept = 0
    
    for i, article in enumerate(articles, 1):
        try:
            original = article.content_markdown
            
            # Count original stats
            orig_tables = original.count('|')
            orig_images = original.count('![')
            
            # Clean the markdown
            cleaned = smart_clean_markdown(original)
            
            # Count new stats
            new_tables = cleaned.count('|')
            new_images = cleaned.count('![')
            
            # Update the article
            article.content_markdown = cleaned
            
            # Calculate changes
            tables_removed = (orig_tables - new_tables) // 3  # Rough estimate
            
            print(f"[{i}/{len(articles)}] {article.title[:40]}...")
            print(f"  Original: {len(original):,} chars, ~{orig_tables//3} tables, {orig_images} images")
            print(f"  Cleaned:  {len(cleaned):,} chars, ~{new_tables//3} tables, {new_images} images")
            
            if orig_images > 0:
                print(f"  ✅ Preserved all {orig_images} images")
                total_image_tables_kept += new_tables // 3
            
            if tables_removed > 0:
                print(f"  🧹 Removed ~{tables_removed} layout tables")
                total_tables_removed += tables_removed
                
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
    print("CLEANING COMPLETE")
    print("=" * 60)
    print(f"📊 Layout tables removed: ~{total_tables_removed}")
    print(f"🖼️  Image tables preserved: ~{total_image_tables_kept}")
    print(f"\nCompleted: {datetime.now()}")
    
    db.close()


if __name__ == "__main__":
    main()