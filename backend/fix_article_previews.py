#!/usr/bin/env python3
"""
Fix article previews by regenerating them from markdown content
Specifically fixes Nathan Lambert and Sebastian Raschka articles
"""
import sys
import os
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.substack import SubstackAuthor, SubstackArticle

def clean_markdown_for_preview(markdown_text):
    """
    Clean markdown text to create a nice preview
    - Remove image tags
    - Remove HTML tags
    - Remove excessive whitespace
    - Keep plain text content
    """
    if not markdown_text:
        return ""
    
    # Remove image markdown syntax ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', markdown_text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove markdown headers but keep the text
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove markdown emphasis but keep the text
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)  # Italic
    text = re.sub(r'__([^_]+)__', r'\1', text)  # Bold
    text = re.sub(r'_([^_]+)_', r'\1', text)  # Italic
    
    # Remove markdown links but keep the text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove blockquote markers
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    
    # Remove list markers
    text = re.sub(r'^[\*\-\+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Remove code blocks
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove horizontal rules
    text = re.sub(r'^[\-\*_]{3,}$', '', text, flags=re.MULTILINE)
    
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines
    text = re.sub(r'[ \t]+', ' ', text)  # Collapse spaces
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)  # Remove leading whitespace
    
    # Remove any remaining HTML entities
    text = re.sub(r'&[a-zA-Z]+;', '', text)
    text = re.sub(r'&#\d+;', '', text)
    
    return text.strip()

def generate_preview(markdown_content, max_length=500):
    """
    Generate a clean preview from markdown content
    """
    if not markdown_content:
        return "No content available"
    
    # Clean the markdown
    clean_text = clean_markdown_for_preview(markdown_content)
    
    if not clean_text:
        # If cleaning removed everything, try to at least get some text
        # Remove only images and keep everything else
        clean_text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', markdown_content)
        clean_text = re.sub(r'<img[^>]+>', '', clean_text)
        clean_text = clean_text.strip()
    
    # Create preview
    if len(clean_text) > max_length:
        # Try to cut at a sentence boundary
        preview = clean_text[:max_length]
        
        # Look for the last sentence ending
        last_period = preview.rfind('.')
        last_question = preview.rfind('?')
        last_exclaim = preview.rfind('!')
        
        # Find the latest sentence ending
        last_sentence = max(last_period, last_question, last_exclaim)
        
        if last_sentence > max_length * 0.7:  # If we have a sentence ending in the last 30%
            preview = preview[:last_sentence + 1]
        else:
            # Otherwise, try to cut at a word boundary
            last_space = preview.rfind(' ')
            if last_space > 0:
                preview = preview[:last_space]
            preview = preview + '...'
    else:
        preview = clean_text
    
    return preview

def fix_previews(author_names=None, dry_run=True):
    """
    Fix previews for specified authors or all if none specified
    """
    db = next(get_db())
    
    try:
        # Build query
        query = db.query(SubstackArticle).join(SubstackAuthor)
        
        if author_names:
            # Fix specific authors
            query = query.filter(SubstackAuthor.name.in_(author_names))
        
        articles = query.all()
        
        print(f"🔍 Found {len(articles)} articles to check")
        print()
        
        fixed_count = 0
        
        for article in articles:
            # Check if preview needs fixing
            current_preview = article.preview or ""
            
            # Signs that preview needs fixing:
            # - Contains HTML tags
            # - Contains image markdown
            # - Is empty or very short
            # - Contains color styles or spans
            needs_fix = (
                '<' in current_preview or
                '![' in current_preview or
                len(current_preview) < 50 or
                'color:' in current_preview or
                'span' in current_preview
            )
            
            if needs_fix and article.content_markdown:
                # Generate new preview
                new_preview = generate_preview(article.content_markdown)
                
                if new_preview and new_preview != current_preview:
                    print(f"📝 {article.author.name}: {article.title[:50]}...")
                    print(f"   Old preview: {current_preview[:100]}...")
                    print(f"   New preview: {new_preview[:100]}...")
                    print()
                    
                    fixed_count += 1
                    if not dry_run:
                        article.preview = new_preview
        
        if not dry_run and fixed_count > 0:
            db.commit()
            print(f"✅ Successfully fixed {fixed_count} article previews")
        elif dry_run:
            print(f"🔍 DRY RUN - Would fix {fixed_count} previews")
            print("   Run with --execute to apply changes")
        else:
            print("✅ All previews look good!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

def show_current_previews(author_names):
    """Show current previews for specified authors"""
    db = next(get_db())
    
    try:
        for author_name in author_names:
            author = db.query(SubstackAuthor).filter(
                SubstackAuthor.name == author_name
            ).first()
            
            if not author:
                print(f"❌ Author not found: {author_name}")
                continue
            
            articles = db.query(SubstackArticle).filter(
                SubstackArticle.author_id == author.id
            ).all()
            
            print(f"\n📚 {author_name} - {len(articles)} articles:")
            print("=" * 60)
            
            for article in articles:
                print(f"\nTitle: {article.title}")
                print(f"Current preview: {article.preview[:200] if article.preview else 'NO PREVIEW'}...")
                
                if article.content_markdown:
                    new_preview = generate_preview(article.content_markdown)
                    print(f"Suggested preview: {new_preview[:200]}...")
                
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix article previews")
    parser.add_argument("--authors", nargs="+", help="Specific authors to fix (default: Nathan Lambert, Sebastian Raschka)")
    parser.add_argument("--all", action="store_true", help="Fix all authors")
    parser.add_argument("--show", action="store_true", help="Show current previews")
    parser.add_argument("--execute", action="store_true", help="Actually fix previews (not dry run)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("ARTICLE PREVIEW FIXER")
    print("=" * 60)
    print()
    
    # Default authors to fix
    target_authors = args.authors or ["Nathan Lambert", "Sebastian Raschka"]
    
    if args.show:
        show_current_previews(target_authors)
    elif args.all:
        fix_previews(author_names=None, dry_run=not args.execute)
    else:
        fix_previews(author_names=target_authors, dry_run=not args.execute)