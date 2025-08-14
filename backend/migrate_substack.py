#!/usr/bin/env python3
"""
Create Substack tables in the database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import Base, engine
from app.models.substack import (
    SubstackAuthor, 
    SubstackArticle, 
    ArticleSnippet, 
    ArticleTag, 
    SnippetTag, 
    SubstackCollection
)

def create_substack_tables():
    """Create all Substack-related tables"""
    print("Creating Substack tables...")
    
    # Create tables
    Base.metadata.create_all(bind=engine, tables=[
        SubstackAuthor.__table__,
        SubstackArticle.__table__,
        ArticleSnippet.__table__,
        ArticleTag.__table__,
        SnippetTag.__table__,
        SubstackCollection.__table__
    ])
    
    print("✅ Substack tables created successfully!")
    
    # List created tables
    print("\nCreated tables:")
    print("  - substack_authors")
    print("  - substack_articles") 
    print("  - article_snippets")
    print("  - article_tags")
    print("  - snippet_tags")
    print("  - substack_collections")

if __name__ == "__main__":
    create_substack_tables()