#!/usr/bin/env python3
"""Test data integrity across all MongoDB collections"""

from pymongo import MongoClient
from bson import ObjectId
from collections import defaultdict
import re

def check_data_integrity():
    """Check data integrity across all collections"""
    client = MongoClient()
    db = client.smarttrendtracer
    
    print("=== Data Integrity Verification ===\n")
    
    # 1. Check tag_instances mapping to concepts
    print("1. Tag Instance to Concept Mapping:")
    instances = db.tag_instances
    concepts = db.tag_concepts_v2
    
    all_instances = list(instances.find())
    all_concepts = list(concepts.find())
    concept_ids = {str(c['_id']) for c in all_concepts}
    
    unmapped = 0
    mapped = 0
    broken_refs = 0
    
    for instance in all_instances:
        if instance.get('concept_id'):
            concept_id_str = str(instance['concept_id'])
            if concept_id_str in concept_ids:
                mapped += 1
            else:
                broken_refs += 1
        else:
            unmapped += 1
    
    print(f"  Total instances: {len(all_instances)}")
    print(f"  Mapped to valid concepts: {mapped}")
    print(f"  Unmapped instances: {unmapped}")
    print(f"  Broken references: {broken_refs}")
    
    # 2. Check tweets tag references
    print("\n2. Tweet Tag References:")
    tweets = db.tweets
    tweet_tags = set()
    
    for tweet in tweets.find({}, {"tags": 1}):
        if tweet.get('tags'):
            tweet_tags.update(tweet['tags'])
    
    print(f"  Unique tags in tweets: {len(tweet_tags)}")
    
    # Check how many tweet tags have concepts
    tweet_tag_concepts = 0
    for tag in tweet_tags:
        # Check in tag_instances
        instance = instances.find_one({"tag": tag})
        if instance and instance.get('concept_id'):
            tweet_tag_concepts += 1
    
    print(f"  Tags with concepts: {tweet_tag_concepts}")
    print(f"  Tags without concepts: {len(tweet_tags) - tweet_tag_concepts}")
    
    # 3. Check papers tag references
    print("\n3. Paper Tag References:")
    papers = db.papers
    paper_tags = set()
    
    for paper in papers.find({}, {"tags": 1}):
        if paper.get('tags'):
            paper_tags.update(paper['tags'])
    
    print(f"  Unique tags in papers: {len(paper_tags)}")
    
    # Check how many paper tags have concepts
    paper_tag_concepts = 0
    for tag in paper_tags:
        instance = instances.find_one({"tag": tag})
        if instance and instance.get('concept_id'):
            paper_tag_concepts += 1
    
    print(f"  Tags with concepts: {paper_tag_concepts}")
    print(f"  Tags without concepts: {len(paper_tags) - paper_tag_concepts}")
    
    # 4. Check articles tag references
    print("\n4. Article Tag References:")
    articles = db.articles
    article_tags = set()
    
    for article in articles.find({}, {"tags": 1}):
        if article.get('tags'):
            article_tags.update(article['tags'])
    
    print(f"  Unique tags in articles: {len(article_tags)}")
    
    # Check how many article tags have concepts
    article_tag_concepts = 0
    for tag in article_tags:
        instance = instances.find_one({"tag": tag})
        if instance and instance.get('concept_id'):
            article_tag_concepts += 1
    
    print(f"  Tags with concepts: {article_tag_concepts}")
    print(f"  Tags without concepts: {len(article_tags) - article_tag_concepts}")
    
    # 5. Check tag_aliases mapping
    print("\n5. Tag Aliases Mapping:")
    aliases = db.tag_aliases_v2
    all_aliases = list(aliases.find())
    
    valid_aliases = 0
    broken_aliases = 0
    
    for alias in all_aliases:
        if alias.get('concept_id'):
            concept_id_str = str(alias['concept_id'])
            if concept_id_str in concept_ids:
                valid_aliases += 1
            else:
                broken_aliases += 1
    
    print(f"  Total aliases: {len(all_aliases)}")
    print(f"  Valid concept references: {valid_aliases}")
    print(f"  Broken references: {broken_aliases}")
    
    # 6. Check usage counts accuracy
    print("\n6. Usage Count Accuracy:")
    
    # Calculate actual usage counts
    actual_usage = defaultdict(int)
    
    # Count from tweets
    for tweet in tweets.find({}, {"tags": 1}):
        if tweet.get('tags'):
            for tag in tweet['tags']:
                instance = instances.find_one({"tag": tag})
                if instance and instance.get('concept_id'):
                    actual_usage[str(instance['concept_id'])] += 1
    
    # Count from papers
    for paper in papers.find({}, {"tags": 1}):
        if paper.get('tags'):
            for tag in paper['tags']:
                instance = instances.find_one({"tag": tag})
                if instance and instance.get('concept_id'):
                    actual_usage[str(instance['concept_id'])] += 1
    
    # Count from articles
    for article in articles.find({}, {"tags": 1}):
        if article.get('tags'):
            for tag in article['tags']:
                instance = instances.find_one({"tag": tag})
                if instance and instance.get('concept_id'):
                    actual_usage[str(instance['concept_id'])] += 1
    
    # Compare with stored usage counts
    mismatched = 0
    for concept in all_concepts:
        concept_id_str = str(concept['_id'])
        stored_count = concept.get('usage_count', 0)
        actual_count = actual_usage.get(concept_id_str, 0)
        
        if stored_count != actual_count:
            mismatched += 1
    
    print(f"  Concepts with mismatched counts: {mismatched}")
    print(f"  Concepts with accurate counts: {len(all_concepts) - mismatched}")
    
    # 7. Check extracted_entities consistency
    print("\n7. Extracted Entities Consistency:")
    entities = db.extracted_entities
    entity_count = entities.count_documents({})
    
    entity_types = entities.distinct("entity_type")
    print(f"  Total extracted entities: {entity_count}")
    print(f"  Entity types: {entity_types}")
    
    # Check if entities are mapped to concepts
    entity_concepts = 0
    for entity in entities.find({}):
        # Try to find corresponding concept
        entity_text = entity.get('text') or entity.get('name') or entity.get('entity', '')
        if entity_text:
            concept = concepts.find_one({"$or": [
                {"slug": entity_text.lower().replace(' ', '-')},
                {"display_name": entity_text}
            ]})
            if concept:
                entity_concepts += 1
    
    print(f"  Entities with concepts: {entity_concepts}")
    print(f"  Entities without concepts: {entity_count - entity_concepts}")
    
    # 8. Check for duplicate concepts
    print("\n8. Duplicate Concept Detection:")
    
    slug_counts = defaultdict(list)
    display_counts = defaultdict(list)
    
    for concept in all_concepts:
        slug = concept.get('slug') or concept.get('tag', 'unknown')
        display = concept.get('display_name', '')
        
        slug_counts[slug].append(str(concept['_id']))
        if display:
            display_counts[display.lower()].append(str(concept['_id']))
    
    duplicate_slugs = {k: v for k, v in slug_counts.items() if len(v) > 1}
    duplicate_displays = {k: v for k, v in display_counts.items() if len(v) > 1}
    
    print(f"  Duplicate slugs: {len(duplicate_slugs)}")
    if duplicate_slugs:
        for slug, ids in list(duplicate_slugs.items())[:3]:
            print(f"    - '{slug}': {len(ids)} duplicates")
    
    print(f"  Duplicate display names: {len(duplicate_displays)}")
    if duplicate_displays:
        for display, ids in list(duplicate_displays.items())[:3]:
            print(f"    - '{display}': {len(ids)} duplicates")
    
    # 9. Check field consistency
    print("\n9. Field Consistency Check:")
    
    # Check if concepts use consistent field names
    field_usage = defaultdict(int)
    for concept in all_concepts:
        for field in concept.keys():
            field_usage[field] += 1
    
    print(f"  Fields used in concepts:")
    common_fields = ['_id', 'slug', 'display_name', 'parents', 'children', 'usage_count']
    for field in common_fields:
        count = field_usage.get(field, 0)
        percentage = (count / len(all_concepts)) * 100
        status = "✅" if percentage > 90 else "⚠️" if percentage > 50 else "❌"
        print(f"    {status} {field}: {count}/{len(all_concepts)} ({percentage:.1f}%)")
    
    # Check for deprecated fields
    deprecated_fields = ['tag', 'alias_text', 'alias_tag']
    print(f"\n  Deprecated fields still in use:")
    for field in deprecated_fields:
        count = field_usage.get(field, 0)
        if count > 0:
            print(f"    ⚠️ {field}: {count} concepts")
    
    return {
        'total_concepts': len(all_concepts),
        'total_instances': len(all_instances),
        'mapped_instances': mapped,
        'unmapped_instances': unmapped,
        'broken_references': broken_refs + broken_aliases,
        'duplicate_concepts': len(duplicate_slugs),
        'mismatched_counts': mismatched
    }

if __name__ == "__main__":
    results = check_data_integrity()
    
    print("\n=== INTEGRITY SUMMARY ===")
    print(f"Total concepts: {results['total_concepts']}")
    print(f"Total tag instances: {results['total_instances']}")
    print(f"Data integrity score: ", end="")
    
    issues = results['unmapped_instances'] + results['broken_references'] + \
             results['duplicate_concepts'] + results['mismatched_counts']
    
    if issues == 0:
        print("✅ EXCELLENT (no issues)")
    elif issues < 10:
        print(f"⚠️ GOOD ({issues} minor issues)")
    elif issues < 100:
        print(f"⚠️ FAIR ({issues} issues need attention)")
    else:
        print(f"❌ POOR ({issues} issues require immediate attention)")