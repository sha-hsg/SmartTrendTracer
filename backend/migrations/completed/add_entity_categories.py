#!/usr/bin/env python3
"""
Add predefined entity categories to the tag ontology
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, TagConcept, TagSynonym
from sqlalchemy import text

def add_entity_categories():
    """Add predefined entity categories to the tag ontology"""
    db = next(get_db())
    
    try:
        # Define the new entity categories
        entities = [
            {
                'tag': 'named-entities',
                'display_name': 'Named Entities',
                'description': 'Named entities extracted from content',
                'level': 0,
                'parent_id': None
            },
            {
                'tag': 'person',
                'display_name': 'Person',
                'description': 'Individual people mentioned in content',
                'level': 1,
                'parent_tag': 'named-entities'
            },
            {
                'tag': 'organisation',
                'display_name': 'Organisation',
                'description': 'Companies, institutions, and organizations',
                'level': 1,
                'parent_tag': 'named-entities'
            },
            {
                'tag': 'location',
                'display_name': 'Location',
                'description': 'Geographic locations and places',
                'level': 1,
                'parent_tag': 'named-entities'
            },
            {
                'tag': 'event',
                'display_name': 'Event',
                'description': 'Conferences, releases, and significant events',
                'level': 1,
                'parent_tag': 'named-entities'
            },
            {
                'tag': 'research-entities',
                'display_name': 'Research Entities',
                'description': 'Research and technical entities',
                'level': 0,
                'parent_id': None
            },
            {
                'tag': 'research-topic',
                'display_name': 'Research Topic',
                'description': 'Research areas and topics',
                'level': 1,
                'parent_tag': 'research-entities'
            },
            {
                'tag': 'dataset',
                'display_name': 'Dataset',
                'description': 'Datasets used in research and development',
                'level': 1,
                'parent_tag': 'research-entities'
            },
            {
                'tag': 'benchmark',
                'display_name': 'Benchmark',
                'description': 'Performance benchmarks and evaluation metrics',
                'level': 1,
                'parent_tag': 'research-entities'
            },
            {
                'tag': 'metric',
                'display_name': 'Metric',
                'description': 'Quantitative metrics and measurements',
                'level': 1,
                'parent_tag': 'research-entities'
            },
            {
                'tag': 'method',
                'display_name': 'Method',
                'description': 'Algorithms, techniques, and methodologies',
                'level': 1,
                'parent_tag': 'research-entities'
            },
            {
                'tag': 'model',
                'display_name': 'Model',
                'description': 'AI/ML models and architectures',
                'level': 1,
                'parent_tag': 'research-entities'
            }
        ]
        
        # Add entities to the database
        for entity in entities:
            # Check if concept already exists
            existing = db.query(TagConcept).filter(TagConcept.tag == entity['tag']).first()
            if existing:
                print(f"Entity '{entity['tag']}' already exists, skipping...")
                continue
            
            # Get parent if specified
            parent_id = entity.get('parent_id')
            if 'parent_tag' in entity and not parent_id:
                parent = db.query(TagConcept).filter(TagConcept.tag == entity['parent_tag']).first()
                if parent:
                    parent_id = parent.id
                else:
                    # Create parent first if it doesn't exist
                    parent_entity = next((e for e in entities if e['tag'] == entity['parent_tag']), None)
                    if parent_entity and parent_entity.get('parent_id') is None:
                        parent = TagConcept(
                            tag=parent_entity['tag'],
                            display_name=parent_entity['display_name'],
                            description=parent_entity['description'],
                            level=parent_entity['level'],
                            parent_id=None,
                            path="/"
                        )
                        db.add(parent)
                        db.flush()
                        parent.update_path(db)
                        parent_id = parent.id
            
            # Create the concept
            concept = TagConcept(
                tag=entity['tag'],
                display_name=entity['display_name'],
                description=entity['description'],
                level=entity['level'],
                parent_id=parent_id,
                path="/"  # Will be updated after flush
            )
            db.add(concept)
            db.flush()  # Get the ID
            
            # Update the path based on parent
            concept.update_path(db)
            print(f"Added entity category: {entity['display_name']}")
        
        db.commit()
        print("\n✅ Entity categories added successfully!")
        
        # Now organize existing tags under these categories
        organize_existing_tags(db)
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding entity categories: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def organize_existing_tags(db):
    """Organize existing tags under the new entity categories"""
    print("\n📁 Organizing existing tags under entity categories...")
    
    # Get the entity concepts
    person_concept = db.query(TagConcept).filter(TagConcept.tag == 'person').first()
    org_concept = db.query(TagConcept).filter(TagConcept.tag == 'organisation').first()
    location_concept = db.query(TagConcept).filter(TagConcept.tag == 'location').first()
    event_concept = db.query(TagConcept).filter(TagConcept.tag == 'event').first()
    model_concept = db.query(TagConcept).filter(TagConcept.tag == 'model').first()
    dataset_concept = db.query(TagConcept).filter(TagConcept.tag == 'dataset').first()
    benchmark_concept = db.query(TagConcept).filter(TagConcept.tag == 'benchmark').first()
    method_concept = db.query(TagConcept).filter(TagConcept.tag == 'method').first()
    
    # Define patterns for automatic categorization
    categorizations = [
        # People
        (person_concept, [
            'sam-altman', 'sama', 'yann-lecun', 'geoffrey-hinton', 'andrew-ng',
            'ilya-sutskever', 'greg-brockman', 'demis-hassabis', 'elon-musk',
            'jensen-huang', 'satya-nadella', 'sundar-pichai'
        ]),
        # Organizations
        (org_concept, [
            'openai', 'anthropic', 'google', 'microsoft', 'meta', 'apple',
            'nvidia', 'huggingface', 'deepmind', 'google-deepmind', 'stability-ai',
            'cohere', 'inflection-ai', 'ai21-labs', 'stanford', 'mit'
        ]),
        # Models
        (model_concept, [
            'gpt', 'gpt-3', 'gpt-4', 'gpt-4o', 'gpt-5', 'claude', 'claude-3',
            'llama', 'llama-2', 'llama-3', 'gemini', 'palm', 'bert', 'roberta',
            'stable-diffusion', 'dall-e', 'midjourney', 'whisper', 'codex'
        ]),
        # Datasets
        (dataset_concept, [
            'imagenet', 'coco', 'mnist', 'cifar-10', 'glue', 'squad',
            'common-crawl', 'wikipedia', 'bookcorpus', 'openwebtext'
        ]),
        # Benchmarks
        (benchmark_concept, [
            'mmlu', 'humaneval', 'gsm8k', 'arc', 'hellaswag', 'winogrande',
            'big-bench', 'superglue', 'lambada', 'truthfulqa'
        ]),
        # Methods
        (method_concept, [
            'transformer', 'attention', 'rlhf', 'reinforcement-learning',
            'fine-tuning', 'prompt-engineering', 'few-shot', 'zero-shot',
            'chain-of-thought', 'constitutional-ai', 'rag', 'retrieval-augmented-generation'
        ])
    ]
    
    for parent_concept, tag_patterns in categorizations:
        if not parent_concept:
            continue
            
        for pattern in tag_patterns:
            # Find existing tags that match this pattern
            matching_tags = db.query(TagConcept).filter(
                TagConcept.tag.like(f'%{pattern}%'),
                TagConcept.parent_id.is_(None)  # Only uncategorized tags
            ).all()
            
            for tag in matching_tags:
                tag.parent_id = parent_concept.id
                tag.level = parent_concept.level + 1
                print(f"  Organized '{tag.tag}' under '{parent_concept.display_name}'")
    
    db.commit()
    print("✅ Existing tags organized!")

if __name__ == '__main__':
    add_entity_categories()