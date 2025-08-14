#!/usr/bin/env python3
"""
Fix previews for forwarded Substack articles by extracting clean text from markdown
"""
import sys
import os
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.substack import SubstackAuthor, SubstackArticle
from bs4 import BeautifulSoup

def extract_clean_text_from_markdown(markdown_content):
    """Extract clean readable text from markdown content with HTML artifacts"""
    if not markdown_content:
        return ""
    
    # Use BeautifulSoup to parse and extract text from HTML elements
    soup = BeautifulSoup(markdown_content, 'html.parser')
    
    # Extract plain text from HTML
    text = soup.get_text()
    
    # Clean up markdown syntax
    # Remove markdown headers
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    
    # Remove markdown links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Remove markdown formatting
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
    text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__
    text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_
    text = re.sub(r'`([^`]+)`', r'\1', text)        # `code`
    
    # Remove bullet points and numbers
    text = re.sub(r'^[•\-\*]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)
    
    # Clean whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines
    text = re.sub(r'^\s+|\s+$', '', text)    # Trim
    text = re.sub(r'\s+', ' ', text)         # Multiple spaces
    
    # Remove common email artifacts
    artifacts_to_remove = [
        r'View in browser.*?(?=\n\n|\Z)',
        r'Unsubscribe.*?(?=\n\n|\Z)',
        r'You received this email.*?(?=\n\n|\Z)',
    ]
    
    for pattern in artifacts_to_remove:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Final cleanup
    text = text.strip()
    
    # Create preview (first 500 chars)
    if len(text) > 500:
        # Try to cut at sentence boundary
        cutoff = text.rfind('.', 400, 500)
        if cutoff == -1:
            cutoff = text.rfind(' ', 400, 500)
        if cutoff == -1:
            cutoff = 500
        text = text[:cutoff].strip()
        if not text.endswith('...'):
            text += '...'
    
    return text

def main():
    """Fix previews for forwarded articles"""
    db = next(get_db())
    
    # Get forwarded authors
    forwarded_authors = ['Gary Marcus', 'Nathan Lambert', 'Sebastian Raschka']
    
    print("🔧 FIXING PREVIEWS FOR FORWARDED SUBSTACK ARTICLES")
    print("=" * 60)
    print()
    
    total_fixed = 0
    
    for author_name in forwarded_authors:
        author = db.query(SubstackAuthor).filter(SubstackAuthor.name == author_name).first()
        if not author:
            print(f"❌ Author '{author_name}' not found")
            continue
        
        articles = db.query(SubstackArticle).filter(SubstackArticle.author_id == author.id).all()
        print(f"📧 Processing {author_name} ({len(articles)} articles):")
        
        fixed_for_author = 0
        for article in articles:
            # Check if preview needs fixing (has HTML artifacts or is too short)
            current_preview = article.preview or ""
            needs_fixing = (
                len(current_preview.strip()) < 50 or
                '<' in current_preview or
                'data-outlook-id' in current_preview or
                'href=' in current_preview or
                'substackcdn.com' in current_preview
            )
            
            if needs_fixing:
                # Generate clean preview from markdown content
                clean_text = extract_clean_text_from_markdown(article.content_markdown)
                
                if clean_text and len(clean_text) > 50:
                    print(f"  🔧 {article.title[:50]}...")
                    print(f"      Old: \"{current_preview[:60]}...\"")
                    print(f"      New: \"{clean_text[:60]}...\"")
                    
                    article.preview = clean_text
                    fixed_for_author += 1
                    total_fixed += 1
                else:
                    print(f"  ⚠️  Could not extract clean text: {article.title[:50]}...")
            else:
                print(f"  ✅ Already clean: {article.title[:50]}...")
        
        print(f"     └─ Fixed {fixed_for_author}/{len(articles)} articles")
        print()
    
    # Commit changes
    if total_fixed > 0:
        print(f"💾 Saving {total_fixed} preview fixes...")
        db.commit()
        print("✅ All previews fixed!")
    else:
        print("ℹ️  No previews needed fixing")
    
    # Show results
    print()
    print("🎉 RESULTS:")
    print("-" * 30)
    
    for author_name in forwarded_authors:
        author = db.query(SubstackAuthor).filter(SubstackAuthor.name == author_name).first()
        if not author:
            continue
            
        articles = db.query(SubstackArticle).filter(SubstackArticle.author_id == author.id).all()
        print(f"\n📧 {author_name}:")
        
        for article in articles:
            preview = (article.preview or '')[:80]
            has_artifacts = '<' in preview or 'data-outlook-id' in preview
            status = '❌' if has_artifacts else '✅'
            print(f"  {status} {article.title[:45]}...")
            print(f"      \"{preview}...\"")

if __name__ == "__main__":
    main()