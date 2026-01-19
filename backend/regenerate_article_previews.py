#!/usr/bin/env python
"""Regenerate article previews from markdown content"""

from pymongo import MongoClient
import re
import argparse

def generate_preview(markdown: str, length: int = 500) -> str:
    """
    Generate a preview from markdown content.
    
    Based on the _generate_preview function from url_article_importer.py
    but with enhanced cleaning for better results.
    """
    if not markdown:
        return ""
    
    # Start with the markdown content
    preview = markdown
    
    # Remove any CDN image references first
    cdn_patterns = [
        r'<img[^>]*src="[^"]*substackcdn\.com[^"]*"[^>]*>',
        r'<img[^>]*src="[^"]*s3\.amazonaws\.com[^"]*"[^>]*>',
        r'!\[[^\]]*\]\([^)]*substackcdn\.com[^)]*\)',
        r'!\[[^\]]*\]\([^)]*s3\.amazonaws\.com[^)]*\)',
        r'https://substackcdn\.com/image/fetch/[^\s\)\'"<]+',
        r'https://[^/]+\.s3\.amazonaws\.com/[^\s\)\'"<]+',
    ]
    
    for pattern in cdn_patterns:
        preview = re.sub(pattern, '', preview, flags=re.IGNORECASE)
    
    # Remove local image references (keep text clean)
    preview = re.sub(r'!\[[^\]]*\]\(/api/articles/[^)]+\)', '', preview)
    
    # Remove markdown formatting
    preview = re.sub(r'^#+\s+', '', preview, flags=re.MULTILINE)  # Headers
    preview = re.sub(r'\*{1,3}([^\*]+)\*{1,3}', r'\1', preview)  # Bold/italic
    preview = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', preview)  # Underline emphasis
    preview = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', preview)  # Links
    preview = re.sub(r'`{1,3}([^`]+)`{1,3}', r'\1', preview)  # Code blocks
    preview = re.sub(r'^>\s+', '', preview, flags=re.MULTILINE)  # Blockquotes
    preview = re.sub(r'^\*\s+', '', preview, flags=re.MULTILINE)  # Bullet points
    preview = re.sub(r'^\-\s+', '', preview, flags=re.MULTILINE)  # Dashes
    preview = re.sub(r'^\d+\.\s+', '', preview, flags=re.MULTILINE)  # Numbered lists
    preview = re.sub(r'\n{3,}', '\n\n', preview)  # Multiple newlines
    preview = re.sub(r'\n+', ' ', preview)  # Convert newlines to spaces
    preview = re.sub(r'\s+', ' ', preview)  # Multiple spaces to single
    
    # Clean up any HTML entities
    preview = preview.replace('&nbsp;', ' ')
    preview = preview.replace('&amp;', '&')
    preview = preview.replace('&lt;', '<')
    preview = preview.replace('&gt;', '>')
    preview = preview.replace('&quot;', '"')
    preview = preview.replace('&#39;', "'")
    
    # Remove any remaining HTML tags
    preview = re.sub(r'<[^>]+>', '', preview)
    
    # Trim to length
    preview = preview.strip()
    if len(preview) > length:
        # Try to cut at a sentence boundary
        sentences = preview[:length + 100].split('. ')
        if len(sentences) > 1:
            # Take complete sentences that fit within length
            result = []
            current_length = 0
            for sentence in sentences:
                if current_length + len(sentence) + 2 <= length:  # +2 for ". "
                    result.append(sentence)
                    current_length += len(sentence) + 2
                else:
                    break
            if result:
                preview = '. '.join(result) + '.'
            else:
                # Fall back to word boundary
                preview = preview[:length].rsplit(' ', 1)[0] + '...'
        else:
            # Fall back to word boundary
            preview = preview[:length].rsplit(' ', 1)[0] + '...'
    
    return preview.strip()

def main():
    parser = argparse.ArgumentParser(description='Regenerate article previews')
    parser.add_argument('--length', type=int, default=500, 
                       help='Preview length in characters (default: 500)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be changed without updating')
    parser.add_argument('--article-id', type=str,
                       help='Regenerate preview for specific article ID')
    parser.add_argument('--limit', type=int,
                       help='Limit number of articles to process')
    args = parser.parse_args()
    
    # MongoDB connection
    client = MongoClient()
    db = client.smarttrendtracer
    
    # Build query
    query = {}
    if args.article_id:
        from bson import ObjectId
        query['_id'] = ObjectId(args.article_id)
    
    # Get articles
    articles = list(db.articles.find(query))
    
    if args.limit:
        articles = articles[:args.limit]
    
    print(f"Processing {len(articles)} articles...")
    print(f"Preview length: {args.length} characters")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'UPDATING DATABASE'}")
    print("=" * 60)
    
    updated_count = 0
    changed_count = 0
    
    for article in articles:
        title = article.get('title', 'Unknown')[:50]
        article_id = str(article['_id'])
        
        # Get markdown content
        markdown = article.get('content_markdown', '')
        if not markdown:
            print(f"\n⚠️  {title}: No markdown content, skipping")
            continue
        
        # Get current preview
        current_preview = article.get('preview', '')
        
        # Generate new preview
        new_preview = generate_preview(markdown, args.length)
        
        # Check if preview changed
        if new_preview != current_preview:
            changed_count += 1
            
            print(f"\n📝 {title}")
            print(f"   ID: {article_id}")
            
            # Show comparison
            if current_preview:
                print(f"   Old preview ({len(current_preview)} chars): {current_preview[:100]}...")
            else:
                print(f"   Old preview: (empty)")
            
            print(f"   New preview ({len(new_preview)} chars): {new_preview[:100]}...")
            
            # Check for CDN references
            if 'substackcdn.com' in current_preview or 's3.amazonaws.com' in current_preview:
                print("   ✨ Removed CDN image references")
            
            # Update if not dry run
            if not args.dry_run:
                result = db.articles.update_one(
                    {'_id': article['_id']},
                    {'$set': {'preview': new_preview}}
                )
                if result.modified_count > 0:
                    updated_count += 1
                    print("   ✅ Updated")
                else:
                    print("   ⚠️  Update failed")
        else:
            print(f"✓ {title}: Preview unchanged")
    
    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  Total articles: {len(articles)}")
    print(f"  Previews changed: {changed_count}")
    if not args.dry_run:
        print(f"  Successfully updated: {updated_count}")
    else:
        print(f"  (Dry run - no changes made)")
    
    # Verify no CDN URLs remain
    if not args.dry_run and updated_count > 0:
        print("\nVerifying results...")
        articles = list(db.articles.find({}, {'preview': 1}))
        cdn_count = 0
        for article in articles:
            preview = article.get('preview', '')
            if 'substackcdn.com' in preview or 's3.amazonaws.com' in preview:
                cdn_count += 1
        
        if cdn_count == 0:
            print("✅ No CDN URLs found in any preview fields!")
        else:
            print(f"⚠️  {cdn_count} articles still have CDN URLs")

if __name__ == "__main__":
    main()