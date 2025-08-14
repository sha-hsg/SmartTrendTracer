#!/usr/bin/env python3
"""
Fix author attribution for Ethan Mollick articles
Some LumberjackAI articles were incorrectly attributed to Ethan Mollick
This script identifies and fixes these misattributions
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.substack import SubstackAuthor, SubstackArticle
from sqlalchemy import func

def analyze_ethan_mollick_articles():
    """Analyze all articles attributed to Ethan Mollick to find misattributions"""
    db = next(get_db())
    
    try:
        # Find Ethan Mollick author
        ethan = db.query(SubstackAuthor).filter(
            SubstackAuthor.name.ilike('%Ethan Mollick%')
        ).first()
        
        if not ethan:
            print("❌ Ethan Mollick author not found in database")
            return
        
        print(f"📊 Analyzing articles for author: {ethan.name} (ID: {ethan.id})")
        print(f"   Email: {ethan.email}")
        print(f"   Subdomain: {ethan.subdomain}")
        print()
        
        # Get all articles attributed to Ethan
        articles = db.query(SubstackArticle).filter(
            SubstackArticle.author_id == ethan.id
        ).order_by(SubstackArticle.published_at.desc()).all()
        
        print(f"📚 Found {len(articles)} articles attributed to Ethan Mollick")
        print()
        
        # Analyze article patterns to identify misattributions
        one_useful_thing_articles = []
        lumberjack_articles = []
        unknown_articles = []
        
        for article in articles:
            # Check for LumberjackAI patterns in title or content
            is_lumberjack = False
            is_one_useful = False
            
            # Check title patterns
            if article.title:
                title_lower = article.title.lower()
                # LumberjackAI patterns
                if any(pattern in title_lower for pattern in [
                    'alfred', 'no-code', 'n8n', 'railway', 'promptivity',
                    'lumberjack', 'automation agency', 'cognitive workflow',
                    'ugly code', 'vibe coding', 'free training', 'hackathon',
                    '100 days', 'weekend developer', 'fire your developer'
                ]):
                    is_lumberjack = True
                # One Useful Thing patterns
                elif any(pattern in title_lower for pattern in [
                    'ai tutor', 'which ai to use', 'using ai', 'ai work',
                    'personality', 'persuasion', 'empathy', 'agi', 'gpt',
                    'claude', 'research', 'search', 'elephant', 'cybernetic',
                    'present future', 'arc of progress', 'bitter lesson'
                ]):
                    is_one_useful = True
            
            # Check content patterns if title didn't match
            if not is_lumberjack and not is_one_useful and article.content_markdown:
                content_lower = article.content_markdown[:1000].lower()
                # LumberjackAI specific content patterns
                if any(pattern in content_lower for pattern in [
                    'lumberjack', 'david', 'szabo', 'alfredos', 'no-code',
                    'n8n workflow', 'automation', 'railway deploy'
                ]):
                    is_lumberjack = True
                # Ethan Mollick specific patterns
                elif any(pattern in content_lower for pattern in [
                    'wharton', 'professor', 'student', 'teaching', 'research paper',
                    'academic', 'harvard', 'mit', 'stanford'
                ]):
                    is_one_useful = True
            
            # Check for newsletter-specific markers
            if article.content_markdown:
                if 'lumberjackai.com' in article.content_markdown.lower():
                    is_lumberjack = True
                elif 'oneusefulthing.org' in article.content_markdown.lower():
                    is_one_useful = True
            
            # Categorize article
            if is_lumberjack:
                lumberjack_articles.append(article)
            elif is_one_useful:
                one_useful_thing_articles.append(article)
            else:
                unknown_articles.append(article)
        
        # Print analysis results
        print("📈 Analysis Results:")
        print(f"   ✅ One Useful Thing (Ethan Mollick): {len(one_useful_thing_articles)} articles")
        print(f"   ⚠️  LumberjackAI (misattributed): {len(lumberjack_articles)} articles")
        print(f"   ❓ Unknown/Unclear: {len(unknown_articles)} articles")
        print()
        
        # Show sample of misattributed articles
        if lumberjack_articles:
            print("🔍 Sample of LumberjackAI articles incorrectly attributed to Ethan Mollick:")
            for article in lumberjack_articles[:10]:
                print(f"   - {article.title[:60]}...")
            if len(lumberjack_articles) > 10:
                print(f"   ... and {len(lumberjack_articles) - 10} more")
            print()
        
        # Show unknown articles for manual review
        if unknown_articles:
            print("❓ Articles needing manual review:")
            for article in unknown_articles[:5]:
                print(f"   - {article.title[:60]}...")
                if article.content_markdown:
                    preview = article.content_markdown[:150].replace('\n', ' ')
                    print(f"     Preview: {preview}...")
            if len(unknown_articles) > 5:
                print(f"   ... and {len(unknown_articles) - 5} more")
            print()
        
        return {
            'ethan_author': ethan,
            'one_useful_thing': one_useful_thing_articles,
            'lumberjack': lumberjack_articles,
            'unknown': unknown_articles
        }
        
    except Exception as e:
        print(f"❌ Error analyzing articles: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def fix_attributions(dry_run=True):
    """Fix the misattributed articles"""
    db = next(get_db())
    
    try:
        # Re-run analysis with current db session to get fresh article objects
        # Find Ethan Mollick author
        ethan = db.query(SubstackAuthor).filter(
            SubstackAuthor.name.ilike('%Ethan Mollick%')
        ).first()
        
        if not ethan:
            print("❌ Ethan Mollick author not found in database")
            return
        
        # Get all articles attributed to Ethan in THIS session
        articles = db.query(SubstackArticle).filter(
            SubstackArticle.author_id == ethan.id
        ).all()
        
        print(f"📚 Found {len(articles)} articles attributed to Ethan Mollick")
        
        # Re-categorize with fresh objects
        lumberjack_articles = []
        
        for article in articles:
            is_lumberjack = False
            
            # Check title patterns
            if article.title:
                title_lower = article.title.lower()
                if any(pattern in title_lower for pattern in [
                    'alfred', 'no-code', 'n8n', 'railway', 'promptivity',
                    'lumberjack', 'automation agency', 'cognitive workflow',
                    'ugly code', 'vibe coding', 'free training', 'hackathon',
                    '100 days', 'weekend developer', 'fire your developer'
                ]):
                    is_lumberjack = True
            
            # Check content patterns
            if not is_lumberjack and article.content_markdown:
                content_lower = article.content_markdown[:1000].lower()
                if any(pattern in content_lower for pattern in [
                    'lumberjack', 'david', 'szabo', 'alfredos', 'no-code',
                    'n8n workflow', 'automation', 'railway deploy'
                ]):
                    is_lumberjack = True
            
            if is_lumberjack:
                lumberjack_articles.append(article)
        
        if not lumberjack_articles:
            print("✅ No misattributed articles found!")
            return
        
        # Find or create LumberjackAI author
        lumberjack_author = db.query(SubstackAuthor).filter(
            SubstackAuthor.email == 'lumberjackai@substack.com'
        ).first()
        
        if not lumberjack_author:
            # Create LumberjackAI author
            print("📝 Creating LumberjackAI author...")
            lumberjack_author = SubstackAuthor(
                name='David Szabo-Stuban',
                email='lumberjackai@substack.com',
                subdomain='lumberjackai',
                description='LumberjackAI - Technical AI insights and no-code automation',
                url='https://lumberjackai.substack.com'
            )
            db.add(lumberjack_author)
            db.flush()
            print(f"   Created author: {lumberjack_author.name} (ID: {lumberjack_author.id})")
        else:
            print(f"📝 Found existing LumberjackAI author: {lumberjack_author.name} (ID: {lumberjack_author.id})")
        
        if dry_run:
            print("\n🔍 DRY RUN - No changes will be made")
            print(f"   Would reassign {len(lumberjack_articles)} articles to LumberjackAI")
        else:
            print(f"\n🔧 Reassigning {len(lumberjack_articles)} articles to LumberjackAI...")
            
            for article in lumberjack_articles:
                old_author_id = article.author_id
                article.author_id = lumberjack_author.id
                print(f"   ✓ Reassigned: {article.title[:50]}...")
            
            db.commit()
            print(f"\n✅ Successfully reassigned {len(lumberjack_articles)} articles")
        
        # Summary - count actual articles remaining
        remaining_ethan = db.query(SubstackArticle).filter(
            SubstackArticle.author_id == ethan.id
        ).count()
        
        lumberjack_count = db.query(SubstackArticle).filter(
            SubstackArticle.author_id == lumberjack_author.id
        ).count()
        
        print("\n📊 Final Summary:")
        print(f"   Ethan Mollick (One Useful Thing): {remaining_ethan} articles")
        print(f"   David Szabo-Stuban (LumberjackAI): {lumberjack_count} articles")
        
    except Exception as e:
        print(f"❌ Error fixing attributions: {e}")
        db.rollback()
    finally:
        db.close()

def delete_non_ethan_articles():
    """Alternative: Delete all non-Ethan Mollick articles instead of reassigning"""
    db = next(get_db())
    
    try:
        # Analyze first
        analysis = analyze_ethan_mollick_articles()
        if not analysis:
            return
        
        to_delete = analysis['lumberjack'] + analysis['unknown']
        
        if not to_delete:
            print("✅ No articles to delete!")
            return
        
        print(f"\n⚠️  WARNING: This will DELETE {len(to_delete)} articles")
        print("Articles to delete:")
        for article in to_delete[:10]:
            print(f"   - {article.title[:60]}...")
        if len(to_delete) > 10:
            print(f"   ... and {len(to_delete) - 10} more")
        
        response = input("\nAre you sure you want to delete these articles? (yes/no): ")
        
        if response.lower() == 'yes':
            for article in to_delete:
                db.delete(article)
                print(f"   ✓ Deleted: {article.title[:50]}...")
            
            db.commit()
            print(f"\n✅ Successfully deleted {len(to_delete)} articles")
        else:
            print("\n❌ Deletion cancelled")
        
    except Exception as e:
        print(f"❌ Error deleting articles: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix Ethan Mollick article attributions")
    parser.add_argument("--analyze", action="store_true", help="Only analyze, don't fix")
    parser.add_argument("--fix", action="store_true", help="Fix misattributions (reassign to correct author)")
    parser.add_argument("--delete", action="store_true", help="Delete non-Ethan articles instead of reassigning")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("ETHAN MOLLICK ARTICLE ATTRIBUTION FIXER")
    print("=" * 60)
    print()
    
    if args.delete:
        delete_non_ethan_articles()
    elif args.fix:
        fix_attributions(dry_run=args.dry_run)
    else:
        # Default: just analyze
        analyze_ethan_mollick_articles()