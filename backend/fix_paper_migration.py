#!/usr/bin/env python3
"""
Fix and migrate the 18 papers that failed during initial migration.
The issue was that authors were stored as plain text instead of JSON.
"""

import sqlite3
import json
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

def parse_authors_text(authors_text):
    """Parse plain text authors into structured format"""
    if not authors_text:
        return []
    
    # Split by comma and clean up
    author_names = [name.strip() for name in authors_text.split(',')]
    
    # Create structured author objects
    authors = []
    for name in author_names:
        if name:
            authors.append({
                "name": name,
                "affiliation": None
            })
    
    return authors

def parse_sections_text(sections_text):
    """Parse sections text or JSON"""
    if not sections_text:
        return []
    
    # Try JSON first
    try:
        return json.loads(sections_text)
    except:
        # Fallback: treat as plain text section
        return [{
            "title": "Content",
            "content": sections_text
        }]

def parse_references_text(references_text):
    """Parse references text or JSON"""
    if not references_text:
        return []
    
    # Try JSON first
    try:
        return json.loads(references_text)
    except:
        # Fallback: split by newlines
        refs = []
        for line in references_text.split('\n'):
            line = line.strip()
            if line:
                refs.append({"title": line})
        return refs

def migrate_missing_papers():
    """Migrate papers that failed in the initial migration"""
    
    # Connect to databases
    mongo_client = MongoClient("mongodb://localhost:27017/")
    db = mongo_client.smarttrendtracer
    
    conn = sqlite3.connect("data/tweets.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get papers not in MongoDB
    cursor.execute("SELECT id FROM papers")
    sqlite_paper_ids = [row['id'] for row in cursor.fetchall()]
    
    mongo_paper_ids = [doc['old_sqlite_id'] for doc in db.papers.find({}, {'old_sqlite_id': 1})]
    missing_ids = set(sqlite_paper_ids) - set(mongo_paper_ids)
    
    print(f"Found {len(missing_ids)} papers to migrate")
    
    success_count = 0
    error_count = 0
    
    for paper_id in missing_ids:
        try:
            # Get paper from SQLite
            cursor.execute("""
                SELECT id, title, abstract, content, authors,
                       publication_date, published_date, conference, journal, arxiv_id, doi, 
                       pdf_path, pdf_url, page_count, word_count, citation_count,
                       categories, created_at, updated_at, processed, processor_used
                FROM papers 
                WHERE id = ?
            """, (paper_id,))
            
            paper = cursor.fetchone()
            if not paper:
                print(f"Paper {paper_id} not found in SQLite")
                continue
            
            # Parse authors (handle plain text format)
            authors = parse_authors_text(paper['authors'])
            
            # Since sections and references don't exist in SQLite, use empty lists
            sections = []
            references = []
            
            # Get tags for this paper
            cursor.execute("""
                SELECT tag FROM paper_tags WHERE paper_id = ?
            """, (paper_id,))
            tag_rows = cursor.fetchall()
            
            # Get concept IDs from MongoDB
            # For papers, we'll store the raw tags as concept_ids temporarily
            concept_ids = [row['tag'] for row in tag_rows]
            
            # Create MongoDB document
            paper_doc = {
                "old_sqlite_id": paper['id'],
                "title": paper['title'],
                "abstract": paper['abstract'],
                "content": paper['content'],
                "authors": authors,
                "sections": sections,
                "references": references,
                "publication_date": paper['publication_date'] or paper['published_date'],
                "conference": paper['conference'],
                "journal": paper['journal'],
                "arxiv_id": paper['arxiv_id'],
                "doi": paper['doi'],
                "pdf_path": paper['pdf_path'],
                "pdf_url": paper['pdf_url'],
                "page_count": paper['page_count'] or 0,
                "word_count": paper['word_count'] or 0,
                "citation_count": paper['citation_count'] or 0,
                "categories": paper['categories'],
                "processed": paper['processed'],
                "processor_used": paper['processor_used'],
                "concept_ids": concept_ids,
                "created_at": datetime.fromisoformat(paper['created_at']) if paper['created_at'] else datetime.now(),
                "updated_at": datetime.fromisoformat(paper['updated_at']) if paper['updated_at'] else datetime.now()
            }
            
            # Insert into MongoDB
            result = db.papers.insert_one(paper_doc)
            print(f"✓ Migrated paper {paper_id}: {paper['title'][:50]}...")
            success_count += 1
            
        except Exception as e:
            print(f"✗ Error migrating paper {paper_id}: {e}")
            error_count += 1
    
    print(f"\nMigration complete:")
    print(f"  Successfully migrated: {success_count}")
    print(f"  Errors: {error_count}")
    
    # Verify final counts
    total_in_mongo = db.papers.count_documents({})
    cursor.execute("SELECT COUNT(*) as count FROM papers")
    total_in_sqlite = cursor.fetchone()['count']
    
    print(f"\nFinal counts:")
    print(f"  SQLite papers: {total_in_sqlite}")
    print(f"  MongoDB papers: {total_in_mongo}")
    print(f"  Difference: {total_in_sqlite - total_in_mongo}")
    
    conn.close()
    mongo_client.close()

if __name__ == "__main__":
    migrate_missing_papers()