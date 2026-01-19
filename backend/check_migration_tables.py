#!/usr/bin/env python3
"""
Check what's in the old vs new tag tables after migration
"""
import sqlite3
from pathlib import Path

def check_tables():
    db_path = "data/tweets.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("CHECKING TAG TABLES AFTER MIGRATION")
    print("=" * 60)
    
    # Check OLD tables
    print("\n1. OLD TABLES (what Tag Ontology Manager reads):")
    print("-" * 40)
    
    # tag_concepts (old)
    cursor.execute("SELECT COUNT(*) FROM tag_concepts")
    old_concepts = cursor.fetchone()[0]
    print(f"tag_concepts: {old_concepts} records")
    
    cursor.execute("SELECT id, tag, display_name FROM tag_concepts LIMIT 5")
    for row in cursor.fetchall():
        print(f"  - {row}")
    
    # Check NEW v2 tables
    print("\n2. NEW V2 TABLES (where migration wrote to):")
    print("-" * 40)
    
    # tag_concepts_v2
    cursor.execute("SELECT COUNT(*) FROM tag_concepts_v2")
    new_concepts = cursor.fetchone()[0]
    print(f"tag_concepts_v2: {new_concepts} records")
    
    cursor.execute("SELECT id, slug, display_name, entity_type FROM tag_concepts_v2 LIMIT 5")
    for row in cursor.fetchall():
        print(f"  - {row}")
    
    # tag_aliases_v2
    cursor.execute("SELECT COUNT(*) FROM tag_aliases_v2")
    aliases = cursor.fetchone()[0]
    print(f"\ntag_aliases_v2: {aliases} records")
    
    cursor.execute("SELECT alias_text, concept_id, alias_type FROM tag_aliases_v2 LIMIT 5")
    for row in cursor.fetchall():
        print(f"  - {row}")
    
    # tag_relations_v2
    cursor.execute("SELECT COUNT(*) FROM tag_relations_v2")
    relations = cursor.fetchone()[0]
    print(f"\ntag_relations_v2: {relations} records")
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"OLD tag_concepts table: {old_concepts} records")
    print(f"NEW tag_concepts_v2 table: {new_concepts} records")
    print(f"NEW tag_aliases_v2 table: {aliases} records")
    print(f"NEW tag_relations_v2 table: {relations} records")
    print("=" * 60)
    
    if old_concepts > 0 and new_concepts > 0:
        print("\n⚠️  WARNING: Both old and new tables have data!")
        print("The Tag Ontology Manager is reading from OLD tables")
        print("but the migration wrote to NEW v2 tables.")
        print("\nTo see the new data in the UI, either:")
        print("1. Update the API to read from v2 tables")
        print("2. Copy v2 data to old tables")
    
    conn.close()

if __name__ == "__main__":
    check_tables()