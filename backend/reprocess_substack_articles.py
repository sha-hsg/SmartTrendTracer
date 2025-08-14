#!/usr/bin/env python3
"""
Reprocess all existing Substack articles using the new Trafilatura + pypandoc conversion
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from sqlalchemy import func
from app.models import get_db
from app.models.substack import SubstackArticle
from app.services.document_converter import DocumentConverter
from app.services.forwarded_email_cleaner import ForwardedEmailCleaner

def clean_preview_text(text: str, max_length: int = 500) -> str:
    """Clean and truncate text for preview"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove markdown formatting for preview
    import re
    # Remove headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    # Remove emphasis
    text = re.sub(r'[*_]+([^*_]+)[*_]+', r'\1', text)
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove images
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)
    
    # Truncate
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text

def reprocess_articles():
    """Reprocess all articles with HTML content using the new converter"""
    
    print("=== Starting Substack Article Reprocessing ===")
    print(f"Time: {datetime.now()}")
    
    # Initialize services
    converter = DocumentConverter()
    cleaner = ForwardedEmailCleaner()
    
    # Get database session
    db = next(get_db())
    
    try:
        # Count articles with HTML content
        total_articles = db.query(func.count(SubstackArticle.id)).filter(
            SubstackArticle.content_html.isnot(None)
        ).scalar()
        
        print(f"\nFound {total_articles} articles with HTML content to reprocess")
        
        if total_articles == 0:
            print("No articles to process. Exiting.")
            return
        
        # Get all articles with HTML content
        articles = db.query(SubstackArticle).filter(
            SubstackArticle.content_html.isnot(None)
        ).order_by(SubstackArticle.published_at.desc()).all()
        
        success_count = 0
        error_count = 0
        improved_count = 0
        
        for idx, article in enumerate(articles, 1):
            print(f"\n[{idx}/{total_articles}] Processing: {article.title[:80]}...")
            print(f"  Author: {article.author.name}")
            print(f"  Date: {article.published_at}")
            
            try:
                # Store original for comparison
                original_markdown = article.content_markdown
                original_length = len(original_markdown) if original_markdown else 0
                
                # Convert HTML to Markdown using new converter
                html_content = article.content_html
                
                # Check if this is a forwarded article and clean if needed
                if article.author.email and "forwarded" in article.author.email.lower():
                    print("  Cleaning forwarded article...")
                    html_content = cleaner.clean_forwarded_html(html_content)
                
                # Convert to markdown
                new_markdown = converter.html_to_markdown(html_content)
                
                if not new_markdown:
                    print("  ❌ Conversion resulted in empty content, skipping")
                    error_count += 1
                    continue
                
                # Clean up the markdown
                new_markdown = new_markdown.strip()
                
                # Update the article
                article.content_markdown = new_markdown
                
                # Update preview
                article.preview = clean_preview_text(new_markdown, 500)
                
                # Calculate word count and reading time
                word_count = len(new_markdown.split())
                article.word_count = word_count
                article.reading_time_minutes = max(1, word_count // 200)  # Assuming 200 wpm
                
                # Save changes
                db.commit()
                
                new_length = len(new_markdown)
                length_diff = new_length - original_length
                
                print(f"  ✅ Successfully reprocessed")
                print(f"     Original: {original_length:,} chars")
                print(f"     New: {new_length:,} chars")
                print(f"     Difference: {length_diff:+,} chars ({length_diff/original_length*100:+.1f}%)" if original_length > 0 else "")
                
                success_count += 1
                
                # Check if the conversion improved (shorter usually means cleaner)
                if original_length > 0 and new_length < original_length * 0.9:  # At least 10% reduction
                    improved_count += 1
                    print(f"     📈 Significant improvement detected!")
                
            except Exception as e:
                print(f"  ❌ Error processing article: {str(e)}")
                error_count += 1
                db.rollback()
                continue
        
        print("\n" + "="*50)
        print("=== Reprocessing Complete ===")
        print(f"Total articles processed: {total_articles}")
        print(f"✅ Successful: {success_count}")
        print(f"📈 Improved (>10% reduction): {improved_count}")
        print(f"❌ Errors: {error_count}")
        print(f"Success rate: {success_count/total_articles*100:.1f}%")
        
        # Show some statistics about the improvements
        if improved_count > 0:
            print(f"\n{improved_count} articles showed significant improvement with cleaner markdown!")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
        print(f"\nCompleted at: {datetime.now()}")

def show_sample_comparison():
    """Show a before/after comparison for one article"""
    
    print("\n=== Sample Comparison ===")
    
    db = next(get_db())
    
    # Get an article with both HTML and markdown
    article = db.query(SubstackArticle).filter(
        SubstackArticle.content_html.isnot(None),
        SubstackArticle.content_markdown.isnot(None)
    ).first()
    
    if not article:
        print("No articles found for comparison")
        return
    
    print(f"\nArticle: {article.title}")
    print(f"Author: {article.author.name}")
    
    # Store original
    original = article.content_markdown[:1000] if article.content_markdown else ""
    
    # Convert with new method
    converter = DocumentConverter()
    new_markdown = converter.html_to_markdown(article.content_html)[:1000]
    
    print("\n--- ORIGINAL MARKDOWN (first 1000 chars) ---")
    print(original)
    
    print("\n--- NEW MARKDOWN (first 1000 chars) ---")
    print(new_markdown)
    
    db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Reprocess Substack articles with improved converter")
    parser.add_argument("--preview", action="store_true", help="Show sample comparison without processing")
    parser.add_argument("--limit", type=int, help="Limit number of articles to process")
    
    args = parser.parse_args()
    
    if args.preview:
        show_sample_comparison()
    else:
        if args.limit:
            print(f"Note: Limiting to {args.limit} articles (would need to modify code to implement)")
        reprocess_articles()