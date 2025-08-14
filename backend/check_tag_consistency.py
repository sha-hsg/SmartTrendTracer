#!/usr/bin/env python3
"""
Check and fix tag consistency across all content types
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from app.models import get_db, Tag, TagConcept, TagSynonym
from app.models.substack import ArticleTag
from app.models.papers import PaperTag
from app.services.unified_tag_service import UnifiedTagService
from collections import defaultdict
import argparse

def get_database_session():
    """Get a database session"""
    from app.models import SessionLocal
    return SessionLocal()

def analyze_tag_inconsistencies(db: Session):
    """Analyze tag inconsistencies across the system"""
    
    print("\n" + "="*60)
    print("TAG CONSISTENCY ANALYSIS")
    print("="*60)
    
    # 1. Get all unique tags from each content type
    tweet_tags = set(db.query(Tag.tag).distinct().all())
    tweet_tags = {t[0] for t in tweet_tags if t[0]}
    
    article_tags = set(db.query(ArticleTag.tag).distinct().all())
    article_tags = {t[0] for t in article_tags if t[0]}
    
    paper_tags = set(db.query(PaperTag.tag).distinct().all())
    paper_tags = {t[0] for t in paper_tags if t[0]}
    
    concept_tags = set(db.query(TagConcept.tag).distinct().all())
    concept_tags = {t[0] for t in concept_tags if t[0]}
    
    print(f"\nTag Counts by Content Type:")
    print(f"  Tweets:   {len(tweet_tags)} unique tags")
    print(f"  Articles: {len(article_tags)} unique tags")
    print(f"  Papers:   {len(paper_tags)} unique tags")
    print(f"  Concepts: {len(concept_tags)} concepts in ontology")
    
    # 2. Find tags not in ontology
    all_content_tags = tweet_tags | article_tags | paper_tags
    tags_without_concepts = all_content_tags - concept_tags
    
    print(f"\nTags without concepts: {len(tags_without_concepts)}")
    if tags_without_concepts and len(tags_without_concepts) < 20:
        for tag in sorted(list(tags_without_concepts))[:20]:
            print(f"  - {tag}")
    
    # 3. Check capitalization inconsistencies
    print("\nCapitalization Inconsistencies:")
    
    # Group tags by lowercase version
    tag_variations = defaultdict(set)
    for tag in all_content_tags:
        tag_variations[tag.lower()].add(tag)
    
    inconsistent_count = 0
    for lower_tag, variations in tag_variations.items():
        if len(variations) > 1:
            inconsistent_count += 1
            if inconsistent_count <= 10:  # Show first 10
                print(f"  '{lower_tag}' has variations: {sorted(variations)}")
    
    if inconsistent_count > 10:
        print(f"  ... and {inconsistent_count - 10} more")
    
    print(f"\nTotal tags with capitalization variations: {inconsistent_count}")
    
    # 4. Check for similar tags (potential duplicates)
    print("\nPotential Duplicate Tags (similar names):")
    
    from difflib import SequenceMatcher
    all_tags_list = sorted(list(all_content_tags))
    potential_duplicates = []
    
    for i, tag1 in enumerate(all_tags_list):
        for tag2 in all_tags_list[i+1:]:
            # Skip if already same when lowercased
            if tag1.lower() == tag2.lower():
                continue
            
            # Check similarity
            similarity = SequenceMatcher(None, tag1.lower(), tag2.lower()).ratio()
            if similarity > 0.85:  # 85% similar
                potential_duplicates.append((tag1, tag2, similarity))
    
    if potential_duplicates:
        for tag1, tag2, sim in sorted(potential_duplicates, key=lambda x: -x[2])[:10]:
            print(f"  '{tag1}' <-> '{tag2}' (similarity: {sim:.0%})")
    else:
        print("  No potential duplicates found")
    
    # 5. Check synonym relationships
    print("\nSynonym Analysis:")
    synonym_count = db.query(TagSynonym).count()
    print(f"  Total synonyms defined: {synonym_count}")
    
    # Find tags that could be synonyms
    unified_service = UnifiedTagService(db)
    tags_with_concepts = 0
    tags_without_concepts_list = []
    
    for tag in list(all_content_tags)[:100]:  # Check first 100 for speed
        concept = unified_service.find_concept_for_tag(tag)
        if concept:
            tags_with_concepts += 1
        else:
            tags_without_concepts_list.append(tag)
    
    print(f"  Tags mapped to concepts (sample of 100): {tags_with_concepts}/100")
    
    return {
        'tweet_tags': len(tweet_tags),
        'article_tags': len(article_tags),
        'paper_tags': len(paper_tags),
        'concept_tags': len(concept_tags),
        'tags_without_concepts': len(tags_without_concepts),
        'capitalization_issues': inconsistent_count,
        'potential_duplicates': len(potential_duplicates)
    }

def fix_tag_consistency(db: Session, dry_run: bool = True):
    """Fix tag consistency issues"""
    
    print("\n" + "="*60)
    print(f"TAG CONSISTENCY FIX ({'DRY RUN' if dry_run else 'APPLYING CHANGES'})")
    print("="*60)
    
    unified_service = UnifiedTagService(db)
    
    if dry_run:
        print("\nDRY RUN MODE - No changes will be made")
    else:
        print("\nAPPLYING FIXES - Database will be modified")
    
    # Run the consistency fix
    if not dry_run:
        updated_count = unified_service.ensure_tag_consistency()
        print(f"\nUpdated {updated_count} tag groups for consistency")
    else:
        print("\nWould update tags to use consistent capitalization from concepts")
        print("Run with --fix to apply changes")
    
    return True

def test_tag_filtering(db: Session, test_tag: str = None):
    """Test tag filtering with the unified service"""
    
    print("\n" + "="*60)
    print("TAG FILTERING TEST")
    print("="*60)
    
    if not test_tag:
        # Use a common tag for testing
        test_tag = "AI"
    
    print(f"\nTesting filtering with tag: '{test_tag}'")
    
    unified_service = UnifiedTagService(db)
    
    # Get all variations
    variations = unified_service.get_all_tag_variations(test_tag)
    print(f"\nTag variations found: {variations}")
    
    # Get statistics
    stats = unified_service.get_tag_statistics(test_tag)
    print(f"\nUsage statistics:")
    print(f"  Tweets:   {stats['tweets']}")
    print(f"  Articles: {stats['articles']}")
    print(f"  Papers:   {stats['papers']}")
    print(f"  Total:    {stats['total']}")
    
    # Find concept
    concept = unified_service.find_concept_for_tag(test_tag)
    if concept:
        print(f"\nMapped to concept: '{concept.tag}' (display: '{concept.display_name}')")
        print(f"  Level: {concept.level}")
        if concept.parent_id:
            parent = db.query(TagConcept).filter(TagConcept.id == concept.parent_id).first()
            if parent:
                print(f"  Parent: '{parent.display_name}'")
        
        # Show synonyms
        synonyms = db.query(TagSynonym).filter(TagSynonym.concept_id == concept.id).all()
        if synonyms:
            print(f"  Synonyms: {[s.synonym_tag for s in synonyms]}")
    else:
        print(f"\nNo concept found for tag '{test_tag}'")

def main():
    parser = argparse.ArgumentParser(description='Check and fix tag consistency')
    parser.add_argument('--analyze', action='store_true', help='Analyze tag inconsistencies')
    parser.add_argument('--fix', action='store_true', help='Fix tag consistency issues')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be fixed without making changes')
    parser.add_argument('--test', type=str, help='Test tag filtering with a specific tag')
    
    args = parser.parse_args()
    
    # Default to analyze if no action specified
    if not args.analyze and not args.fix and not args.test:
        args.analyze = True
    
    # Get database session
    db = get_database_session()
    
    try:
        if args.analyze:
            stats = analyze_tag_inconsistencies(db)
            print("\n" + "="*60)
            print("SUMMARY")
            print("="*60)
            print(f"Total unique tags across all content: {stats['tweet_tags'] + stats['article_tags'] + stats['paper_tags']}")
            print(f"Tags without concepts: {stats['tags_without_concepts']}")
            print(f"Capitalization issues: {stats['capitalization_issues']}")
            print(f"Potential duplicates: {stats['potential_duplicates']}")
        
        if args.fix or args.dry_run:
            fix_tag_consistency(db, dry_run=args.dry_run or not args.fix)
        
        if args.test:
            test_tag_filtering(db, args.test)
        
        print("\n✓ Tag consistency check complete")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())