#!/usr/bin/env python3
"""
Fix existing articles by reconverting HTML to Markdown using markdownify
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from markdownify import markdownify as md
from app.models import get_db
from app.models.substack import SubstackArticle
from bs4 import BeautifulSoup

def fix_markdown_conversion():
    """Reconvert all HTML content to Markdown using markdownify"""
    print("🔧 Fixing Markdown conversion for all articles...")
    
    db = next(get_db())
    
    # Markdownify options for better conversion
    markdown_options = {
        'heading_style': 'ATX',  # Use # for headings
        'bullets': '-',  # Use - for bullets
        'strong_em_symbol': '**',  # Use ** for bold
        'wrap': False,  # Don't wrap lines
        'strip': ['script', 'style', 'meta', 'noscript']  # Remove these tags
    }
    
    # Get all articles with HTML content
    articles = db.query(SubstackArticle).filter(
        SubstackArticle.content_html != None,
        SubstackArticle.content_html != ''
    ).all()
    
    print(f"Found {len(articles)} articles to process")
    
    fixed_count = 0
    error_count = 0
    
    for article in articles:
        try:
            # Parse HTML
            soup = BeautifulSoup(article.content_html, 'html.parser')
            
            # Remove script and style tags
            for tag in soup(['script', 'style', 'meta', 'noscript']):
                tag.decompose()
            
            # Convert to markdown
            markdown = md(str(soup), **markdown_options)
            
            # Clean up excessive whitespace
            lines = markdown.split('\n')
            cleaned_lines = []
            prev_empty = False
            
            for line in lines:
                line = line.strip()
                if line:
                    cleaned_lines.append(line)
                    prev_empty = False
                elif not prev_empty:
                    cleaned_lines.append('')
                    prev_empty = True
            
            markdown = '\n'.join(cleaned_lines)
            
            # Update article
            article.content_markdown = markdown
            
            # Update preview if needed
            if markdown:
                article.preview = markdown[:500].strip() + '...' if len(markdown) > 500 else markdown
                article.word_count = len(markdown.split())
                article.reading_time_minutes = max(1, article.word_count // 200)
            
            fixed_count += 1
            
            # Show progress
            if fixed_count % 10 == 0:
                print(f"  Processed {fixed_count}/{len(articles)} articles...")
                
        except Exception as e:
            error_count += 1
            print(f"  ❌ Error processing article {article.id}: {e}")
    
    # Commit changes
    db.commit()
    
    print(f"\n✅ Fixed {fixed_count} articles")
    if error_count > 0:
        print(f"⚠️  {error_count} articles had errors")
    
    # Show sample of fixed content
    print("\n📝 Sample of fixed articles:")
    sample_articles = db.query(SubstackArticle).filter(
        SubstackArticle.content_markdown != None
    ).limit(3).all()
    
    for article in sample_articles:
        preview = article.content_markdown[:200] if article.content_markdown else "No content"
        print(f"\n{article.title}:")
        print(f"  {preview}...")
    
    db.close()

if __name__ == "__main__":
    fix_markdown_conversion()