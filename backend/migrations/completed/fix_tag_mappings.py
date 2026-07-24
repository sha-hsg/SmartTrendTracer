#!/usr/bin/env python3
"""
Fix duplicate tag mappings and synonyms in the database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import get_db
from app.models.tag_ontology import TagMapping, TagSynonym, TagConcept

def fix_duplicate_mappings():
    """Remove duplicate tag mappings"""
    db = next(get_db())
    
    print("Checking for duplicate tag mappings...")
    
    # Find duplicates
    duplicates = db.execute(text("""
        SELECT source_tag, mapped_tag, COUNT(*) as count
        FROM tag_mappings
        GROUP BY source_tag, mapped_tag
        HAVING COUNT(*) > 1
    """)).fetchall()
    
    if duplicates:
        print(f"Found {len(duplicates)} duplicate tag mapping pairs")
        for dup in duplicates:
            print(f"  - {dup.source_tag} -> {dup.mapped_tag}: {dup.count} duplicates")
        
        # Remove duplicates, keeping only one of each
        print("\nRemoving duplicates...")
        db.execute(text("""
            DELETE FROM tag_mappings
            WHERE rowid NOT IN (
                SELECT MIN(rowid)
                FROM tag_mappings
                GROUP BY source_tag, mapped_tag
            )
        """))
        db.commit()
        print("Duplicates removed")
    else:
        print("No duplicate tag mappings found")
    
    # Check for duplicate synonyms
    print("\nChecking for duplicate synonyms...")
    dup_synonyms = db.execute(text("""
        SELECT synonym_tag, COUNT(*) as count
        FROM tag_synonyms
        GROUP BY synonym_tag
        HAVING COUNT(*) > 1
    """)).fetchall()
    
    if dup_synonyms:
        print(f"Found {len(dup_synonyms)} duplicate synonyms")
        for dup in dup_synonyms:
            print(f"  - {dup.synonym_tag}: {dup.count} duplicates")
        
        # For duplicate synonyms, we need to be more careful
        # Keep the one with the lowest concept_id (oldest)
        print("\nRemoving duplicate synonyms...")
        db.execute(text("""
            DELETE FROM tag_synonyms
            WHERE rowid NOT IN (
                SELECT MIN(rowid)
                FROM tag_synonyms
                GROUP BY synonym_tag
            )
        """))
        db.commit()
        print("Duplicate synonyms removed")
    else:
        print("No duplicate synonyms found")
    
    # Rebuild mappings cleanly
    print("\nRebuilding tag mappings...")
    TagMapping.rebuild_mappings(db)
    print("Tag mappings rebuilt successfully")
    
    db.close()

def check_synonym_conflicts():
    """Check for synonym conflicts before applying reorganization"""
    db = next(get_db())
    
    print("\nChecking for potential synonym conflicts...")
    
    # Get all existing synonyms
    existing = db.query(TagSynonym.synonym_tag).distinct().all()
    existing_set = {s[0] for s in existing}
    
    # Get all tag concepts that might conflict
    concepts = db.query(TagConcept.tag).all()
    concept_set = {c[0] for c in concepts}
    
    # Find overlaps
    overlaps = existing_set & concept_set
    if overlaps:
        print(f"WARNING: {len(overlaps)} tags are both concepts and synonyms:")
        for tag in list(overlaps)[:10]:
            print(f"  - {tag}")
    else:
        print("No conflicts found between concepts and synonyms")
    
    db.close()

if __name__ == "__main__":
    print("=== Tag Mapping and Synonym Fix ===")
    fix_duplicate_mappings()
    check_synonym_conflicts()
    print("\n✅ Fix complete!")