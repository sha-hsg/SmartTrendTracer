#!/usr/bin/env python3
"""
Reconnect orphaned tags to the new hierarchy
This creates synonym mappings or new concepts for tags that exist in data but not in hierarchy
"""

from app.models import get_db, Tag
from app.models.substack import ArticleTag
from app.models.tag_ontology import TagConcept, TagSynonym, TagMapping
from collections import Counter
import re

def find_best_parent(tag_name: str, concepts: dict) -> str:
    """Try to find the best parent concept for an orphaned tag"""
    
    tag_lower = tag_name.lower()
    
    # Direct mapping rules
    mappings = {
        # AI Models and Platforms
        'openai': 'OpenAI_Ecosystem',
        'gpt': 'OpenAI_Ecosystem',
        'chatgpt': 'OpenAI_Ecosystem',
        'claude': 'Anthropic_Ecosystem',
        'anthropic': 'Anthropic_Ecosystem',
        'gemini': 'Google_Ecosystem',
        'google': 'Google_Ecosystem',
        'hugging': 'Open_Source_Ecosystem',
        'microsoft': 'Other_Platforms',
        
        # Core concepts
        'llm': 'Large_Language_Models',
        'language model': 'Large_Language_Models',
        'transformer': 'Transformer_Architecture',
        'vision': 'Computer_Vision',
        'visual': 'Computer_Vision',
        'nlp': 'Natural_Language_Processing',
        'language': 'Natural_Language_Processing',
        'reinforcement': 'Reinforcement_Learning',
        'deep learning': 'Deep_Learning',
        
        # Development
        'fine-tun': 'Fine-Tuning',
        'prompt': 'Prompt_Optimization',
        'dataset': 'dataset',
        'deploy': 'deployment',
        'api': 'API',
        'mlops': 'MLOps',
        
        # Applications
        'coding': 'Coding',
        'code': 'Coding',
        'math': 'math',
        'writing': 'writing',
        'creative': 'creative-writing',
        'reasoning': 'reasoning',
        'tool': 'Tool_Use',
        'agent': 'Agentic_Tool_Use',
        'multimodal': 'multimodal',
        
        # Performance
        'performance': 'Performance',
        'benchmark': 'benchmarking',
        'evaluat': 'AI_Evaluation_Metrics',
        'smart': 'smart',
        
        # Ethics
        'ethic': 'AI_Safety_&_Ethics',
        'safety': 'AI_Safety_&_Ethics',
        'bias': 'bias',
        'responsible': 'responsible_AI',
        'transparency': 'Transparency',
        'open source': 'Open_Source',
        'open model': 'Open_Model',
        
        # Business
        'market': 'AI_Market_Dynamics',
        'business': 'AI_in_Business',
        'company': 'Company_Strategy',
        'strategy': 'AI_Strategy',
        'leadership': 'AI_Leadership',
        'talent': 'AI_Talent_Movement',
        
        # Research
        'research': 'Research_&_Development',
        'paper': 'scientific-papers',
        'stanford': 'stanford',
        'professor': 'Academic_Figures_And_Institutions',
        'academia': 'Academic_Figures_And_Institutions',
        'collaborat': 'Collaboration',
        
        # Other
        'innovat': 'innovation',
        'integrat': 'Integration',
        'custom': 'Customization',
        'user': 'User_Experience',
        'human': 'Human-AI_Interaction',
        'time': 'time_savings',
        'accessibility': 'accessibility',
        'rollout': 'rollout',
    }
    
    # Check for matches
    for key, parent in mappings.items():
        if key in tag_lower:
            if parent in concepts:
                return parent
    
    # Default categories based on patterns
    if any(x in tag_lower for x in ['model', 'gpt', 'llm', 'claude', 'gemini']):
        return 'AI_Models_And_Platforms'
    elif any(x in tag_lower for x in ['develop', 'build', 'train', 'fine-tun', 'deploy']):
        return 'AI_Development_And_Operations'
    elif any(x in tag_lower for x in ['app', 'tool', 'use', 'capabilit']):
        return 'AI_Applications_And_Capabilities'
    elif any(x in tag_lower for x in ['perform', 'evaluat', 'benchmark', 'metric']):
        return 'AI_Performance_And_Evaluation'
    elif any(x in tag_lower for x in ['ethic', 'safe', 'bias', 'responsible', 'govern']):
        return 'AI_Ethics_And_Governance'
    elif any(x in tag_lower for x in ['business', 'market', 'company', 'industry']):
        return 'AI_Industry_And_Ecosystem'
    elif any(x in tag_lower for x in ['research', 'paper', 'academic', 'study']):
        return 'AI_Research_And_Community'
    else:
        # Default to Core concepts
        return 'Core_AI_ML_Concepts'


def reconnect_orphaned_tags(auto_create: bool = False):
    """Reconnect orphaned tags to the hierarchy"""
    
    db = next(get_db())
    
    try:
        # Get all tags in use
        tweet_tags = db.query(Tag.tag).distinct().all()
        article_tags = db.query(ArticleTag.tag).distinct().all()
        all_used_tags = {t[0] for t in tweet_tags} | {t[0] for t in article_tags}
        
        # Get current hierarchy
        concepts = db.query(TagConcept).all()
        concept_dict = {c.tag: c for c in concepts}
        concept_tags = set(concept_dict.keys())
        
        # Get existing synonyms
        synonyms = db.query(TagSynonym).all()
        synonym_tags = {s.synonym_tag for s in synonyms}
        
        # Find truly orphaned tags (not in concepts or synonyms)
        orphaned_tags = all_used_tags - concept_tags - synonym_tags
        
        print(f"📊 Tag Analysis:")
        print(f"  - Total tags in use: {len(all_used_tags)}")
        print(f"  - Tags in hierarchy: {len(concept_tags)}")
        print(f"  - Existing synonyms: {len(synonym_tags)}")
        print(f"  - Orphaned tags: {len(orphaned_tags)}")
        
        if not orphaned_tags:
            print("✅ No orphaned tags found!")
            return True
        
        # Group orphaned tags by suggested parent
        suggestions = {}
        for tag in orphaned_tags:
            parent = find_best_parent(tag, concept_dict)
            if parent not in suggestions:
                suggestions[parent] = []
            suggestions[parent].append(tag)
        
        print(f"\n📋 Suggested mappings for orphaned tags:")
        for parent, tags in suggestions.items():
            parent_concept = concept_dict.get(parent)
            if parent_concept:
                print(f"\n{parent_concept.display_name} ({parent}):")
                for tag in tags[:10]:  # Show first 10
                    # Count usage
                    tweet_count = db.query(Tag).filter(Tag.tag == tag).count()
                    article_count = db.query(ArticleTag).filter(ArticleTag.tag == tag).count()
                    print(f"  - {tag} ({tweet_count} tweets, {article_count} articles)")
                if len(tags) > 10:
                    print(f"  ... and {len(tags) - 10} more")
        
        if not auto_create:
            print("\n💡 To automatically create these as:")
            print("   1. Synonyms (recommended) - run with --synonyms")
            print("   2. New child concepts - run with --concepts")
            return False
        
        # Auto-create based on flag
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def create_synonyms_for_orphans():
    """Create synonym mappings for orphaned tags"""
    
    db = next(get_db())
    
    try:
        # Get all tags in use
        tweet_tags = db.query(Tag.tag).distinct().all()
        article_tags = db.query(ArticleTag.tag).distinct().all()
        all_used_tags = {t[0] for t in tweet_tags} | {t[0] for t in article_tags}
        
        # Get current hierarchy
        concepts = db.query(TagConcept).all()
        concept_dict = {c.tag: c for c in concepts}
        concept_tags = set(concept_dict.keys())
        
        # Get existing synonyms
        existing_synonyms = db.query(TagSynonym.synonym_tag).distinct().all()
        synonym_tags = {s[0] for s in existing_synonyms}
        
        # Find truly orphaned tags
        orphaned_tags = all_used_tags - concept_tags - synonym_tags
        
        print(f"Found {len(orphaned_tags)} orphaned tags to process...")
        
        created = 0
        skipped = 0
        errors = 0
        
        for tag in orphaned_tags:
            parent_tag = find_best_parent(tag, concept_dict)
            parent_concept = concept_dict.get(parent_tag)
            
            if parent_concept:
                # Check if synonym already exists for this concept and tag
                existing = db.query(TagSynonym).filter(
                    TagSynonym.concept_id == parent_concept.id,
                    TagSynonym.synonym_tag == tag
                ).first()
                
                if existing:
                    skipped += 1
                else:
                    try:
                        # Create synonym
                        synonym = TagSynonym(
                            concept_id=parent_concept.id,
                            synonym_tag=tag
                        )
                        db.add(synonym)
                        db.flush()  # Flush to catch unique constraint violations
                        created += 1
                        
                        if created % 50 == 0:
                            print(f"  Created {created} synonyms...")
                    except Exception as e:
                        # Handle unique constraint violations
                        db.rollback()
                        errors += 1
                        print(f"  ⚠️ Could not create synonym for '{tag}': {str(e)[:50]}")
        
        db.commit()
        print(f"\n📊 Results:")
        print(f"  ✅ Created: {created} new synonym mappings")
        print(f"  ⏭️ Skipped: {skipped} (already existed)")
        print(f"  ❌ Errors: {errors}")
        
        # Rebuild mappings
        print("\n🔧 Rebuilding tag mappings...")
        TagMapping.rebuild_mappings(db)
        print("✅ Mappings rebuilt")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Reconnect orphaned tags to hierarchy')
    parser.add_argument('--synonyms', action='store_true', 
                       help='Create synonyms for orphaned tags')
    parser.add_argument('--concepts', action='store_true',
                       help='Create new concepts for orphaned tags (not implemented)')
    args = parser.parse_args()
    
    if args.synonyms:
        success = create_synonyms_for_orphans()
    elif args.concepts:
        print("Creating concepts not yet implemented")
        success = False
    else:
        success = reconnect_orphaned_tags()
    
    import sys
    sys.exit(0 if success else 1)