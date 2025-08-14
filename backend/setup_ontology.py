#!/usr/bin/env python3
"""
Setup tag ontology tables and import existing tags
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import Base, engine, get_db
from app.models import TagConcept, TagSynonym, TagMapping, TagOntologyService, Tag
from sqlalchemy import inspect

def create_tables():
    """Create ontology tables if they don't exist"""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Check what was created
    new_tables = []
    if 'tag_concepts' not in existing_tables:
        new_tables.append('tag_concepts')
    if 'tag_synonyms' not in existing_tables:
        new_tables.append('tag_synonyms')
    if 'tag_mappings' not in existing_tables:
        new_tables.append('tag_mappings')
    
    if new_tables:
        print(f"✅ Created new tables: {', '.join(new_tables)}")
    else:
        print("ℹ️  Ontology tables already exist")
    
    return len(new_tables) > 0

def setup_initial_hierarchy():
    """Set up initial tag hierarchy"""
    db = next(get_db())
    service = TagOntologyService(db)
    
    # Check if we already have concepts
    existing_count = db.query(TagConcept).count()
    if existing_count > 0:
        print(f"ℹ️  Found {existing_count} existing concepts")
        return
    
    print("🏗️  Setting up initial tag hierarchy...")
    
    # Create root categories
    ai_tools = service.create_concept(
        tag="ai-tools",
        display_name="AI Tools & Applications",
        description="Artificial Intelligence tools, platforms, and applications"
    )
    
    ai_research = service.create_concept(
        tag="ai-research",
        display_name="AI Research",
        description="Academic and industry research in AI"
    )
    
    ai_news = service.create_concept(
        tag="ai-news",
        display_name="AI News & Updates",
        description="News, announcements, and updates in the AI space"
    )
    
    ai_ethics = service.create_concept(
        tag="ai-ethics",
        display_name="AI Ethics & Policy",
        description="Ethical considerations, regulations, and policy discussions"
    )
    
    # Create subcategories under AI Tools
    llm = service.create_concept(
        tag="llm",
        display_name="Large Language Models",
        description="Large language models and their applications",
        parent_id=ai_tools.id
    )
    
    # Add synonym for LLM
    service.add_synonym(llm.id, "large-language-models")
    service.add_synonym(llm.id, "language-models")
    
    # Create specific LLM subcategories
    gpt = service.create_concept(
        tag="gpt",
        display_name="GPT Models",
        description="OpenAI's GPT family of models",
        parent_id=llm.id
    )
    
    service.create_concept(
        tag="gpt-4",
        display_name="GPT-4",
        description="OpenAI's GPT-4 model",
        parent_id=gpt.id
    )
    
    service.create_concept(
        tag="gpt-5",
        display_name="GPT-5",
        description="OpenAI's upcoming GPT-5 model",
        parent_id=gpt.id
    )
    
    claude = service.create_concept(
        tag="claude",
        display_name="Claude",
        description="Anthropic's Claude AI models",
        parent_id=llm.id
    )
    
    gemini = service.create_concept(
        tag="gemini",
        display_name="Gemini",
        description="Google's Gemini models",
        parent_id=llm.id
    )
    
    # Computer Vision under AI Tools
    cv = service.create_concept(
        tag="computer-vision",
        display_name="Computer Vision",
        description="Image and video processing AI",
        parent_id=ai_tools.id
    )
    
    service.add_synonym(cv.id, "cv")
    service.add_synonym(cv.id, "image-ai")
    
    # Create ML subcategory
    ml = service.create_concept(
        tag="machine-learning",
        display_name="Machine Learning",
        description="Machine learning techniques and algorithms",
        parent_id=ai_research.id
    )
    
    service.add_synonym(ml.id, "ml")
    
    # Deep Learning under ML
    dl = service.create_concept(
        tag="deep-learning",
        display_name="Deep Learning",
        description="Deep neural networks and deep learning research",
        parent_id=ml.id
    )
    
    service.add_synonym(dl.id, "dl")
    service.add_synonym(dl.id, "neural-networks")
    
    # Create company tags
    companies = service.create_concept(
        tag="ai-companies",
        display_name="AI Companies",
        description="Companies working in AI",
        parent_id=None
    )
    
    openai = service.create_concept(
        tag="openai",
        display_name="OpenAI",
        description="OpenAI company and products",
        parent_id=companies.id
    )
    
    anthropic = service.create_concept(
        tag="anthropic",
        display_name="Anthropic",
        description="Anthropic company and products",
        parent_id=companies.id
    )
    
    google_ai = service.create_concept(
        tag="google-ai",
        display_name="Google AI",
        description="Google's AI initiatives",
        parent_id=companies.id
    )
    
    service.add_synonym(google_ai.id, "google-deepmind")
    service.add_synonym(google_ai.id, "deepmind")
    
    # Rebuild mappings
    TagMapping.rebuild_mappings(db)
    
    print("✅ Initial hierarchy created successfully")
    
    # Show stats
    total_concepts = db.query(TagConcept).count()
    total_synonyms = db.query(TagSynonym).count()
    total_mappings = db.query(TagMapping).count()
    
    print(f"📊 Created {total_concepts} concepts, {total_synonyms} synonyms, {total_mappings} mappings")

def import_existing_tags():
    """Import existing tags that aren't in the hierarchy"""
    db = next(get_db())
    service = TagOntologyService(db)
    
    # Get all unique tags from the Tag table
    existing_tags = db.query(Tag.tag).distinct().all()
    
    imported = 0
    skipped = 0
    
    print(f"📥 Importing {len(existing_tags)} existing tags...")
    
    for (tag,) in existing_tags:
        normalized_tag = tag.lower().replace(' ', '-')
        
        # Check if already exists as concept or synonym
        concept = db.query(TagConcept).filter(TagConcept.tag == normalized_tag).first()
        synonym = db.query(TagSynonym).filter(TagSynonym.synonym_tag == normalized_tag).first()
        
        if not concept and not synonym:
            try:
                # Create as uncategorized concept
                new_concept = TagConcept(
                    tag=normalized_tag,
                    display_name=tag.replace('-', ' ').title(),
                    description="Auto-imported from existing tags",
                    parent_id=None,
                    path="/",
                    level=0,
                    child_count=0,
                    descendant_count=0
                )
                db.add(new_concept)
                db.commit()
                imported += 1
            except Exception as e:
                db.rollback()  # Rollback on error
                print(f"  ⚠️  Couldn't import '{tag}': {e}")
                skipped += 1
        else:
            skipped += 1
    
    if imported > 0:
        # Rebuild mappings for imported tags
        TagMapping.rebuild_mappings(db)
    
    print(f"✅ Imported {imported} tags, skipped {skipped} (already in ontology)")

if __name__ == "__main__":
    print("🚀 Setting up Tag Ontology System")
    print("=" * 60)
    
    # Create tables
    tables_created = create_tables()
    
    # Set up initial hierarchy
    setup_initial_hierarchy()
    
    # Import existing tags
    import_existing_tags()
    
    print("\n✨ Tag ontology setup complete!")
    print("\nYou can now:")
    print("1. Access the ontology API at /api/ontology/tree")
    print("2. Manage concepts at /api/ontology/concepts")
    print("3. Filter tweets using hierarchical tags")