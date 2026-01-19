#!/usr/bin/env python3
"""
Fix usage counts for all concepts by counting actual usage in tweets, papers, and articles.
This script:
1. Counts tag instances for each concept
2. Includes aliases in the count
3. Updates the usage_count field for all concepts
"""

import json
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from typing import Dict, List, Optional, Set
from collections import defaultdict

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['smarttrendtracer']
concepts_collection = db['tag_concepts_v2']
aliases_collection = db['tag_aliases_v2']
instances_collection = db['tag_instances']
tweets_collection = db['tweets']
papers_collection = db['papers']
articles_collection = db['articles']

def count_concept_usage():
    """Count actual usage of each concept across all content types."""
    print("Counting concept usage across all content...")
    
    usage_counts = defaultdict(int)
    
    # Count from tag_instances collection
    print("  Counting from tag_instances...")
    instances = instances_collection.find({})
    for instance in instances:
        concept_id = instance.get('concept_id')
        if concept_id:
            # Convert string ID to ObjectId if necessary
            if isinstance(concept_id, str):
                try:
                    concept_id = ObjectId(concept_id)
                except:
                    continue
            usage_counts[concept_id] += 1
    
    # Also count direct tags in content collections
    # Check tweets for tags field
    print("  Counting from tweets...")
    tweets = tweets_collection.find({'tags': {'$exists': True, '$ne': []}}, {'tags': 1})
    for tweet in tweets:
        for tag in tweet.get('tags', []):
            # Find concept by slug or display_name
            concept = concepts_collection.find_one({
                '$or': [
                    {'slug': tag},
                    {'display_name': tag}
                ]
            })
            if concept:
                usage_counts[concept['_id']] += 1
    
    # Check papers for tags field
    print("  Counting from papers...")
    papers = papers_collection.find({'tags': {'$exists': True, '$ne': []}}, {'tags': 1})
    for paper in papers:
        for tag in paper.get('tags', []):
            concept = concepts_collection.find_one({
                '$or': [
                    {'slug': tag},
                    {'display_name': tag}
                ]
            })
            if concept:
                usage_counts[concept['_id']] += 1
    
    # Check articles for tags field
    print("  Counting from articles...")
    articles = articles_collection.find({'tags': {'$exists': True, '$ne': []}}, {'tags': 1})
    for article in articles:
        for tag in article.get('tags', []):
            concept = concepts_collection.find_one({
                '$or': [
                    {'slug': tag},
                    {'display_name': tag}
                ]
            })
            if concept:
                usage_counts[concept['_id']] += 1
    
    return usage_counts

def count_alias_usage():
    """Count usage through aliases."""
    print("Counting alias usage...")
    
    alias_usage = defaultdict(int)
    
    # Get all aliases
    aliases = aliases_collection.find({})
    alias_map = {}
    for alias in aliases:
        alias_text = alias.get('alias_text')
        if alias_text:
            alias_text = alias_text.lower()
            concept_id = alias.get('concept_id')
            if concept_id:
                alias_map[alias_text] = concept_id
    
    # Check tweets for alias usage
    print("  Checking tweets for alias usage...")
    tweets = tweets_collection.find({'tags': {'$exists': True, '$ne': []}}, {'tags': 1})
    for tweet in tweets:
        for tag in tweet.get('tags', []):
            tag_lower = tag.lower()
            if tag_lower in alias_map:
                alias_usage[alias_map[tag_lower]] += 1
    
    # Check papers for alias usage
    print("  Checking papers for alias usage...")
    papers = papers_collection.find({'tags': {'$exists': True, '$ne': []}}, {'tags': 1})
    for paper in papers:
        for tag in paper.get('tags', []):
            tag_lower = tag.lower()
            if tag_lower in alias_map:
                alias_usage[alias_map[tag_lower]] += 1
    
    # Check articles for alias usage
    print("  Checking articles for alias usage...")
    articles = articles_collection.find({'tags': {'$exists': True, '$ne': []}}, {'tags': 1})
    for article in articles:
        for tag in article.get('tags', []):
            tag_lower = tag.lower()
            if tag_lower in alias_map:
                alias_usage[alias_map[tag_lower]] += 1
    
    return alias_usage

def update_usage_counts(usage_counts: Dict[ObjectId, int], alias_usage: Dict[ObjectId, int]):
    """Update usage_count field for all concepts."""
    print("\nUpdating usage counts for all concepts...")
    
    # Combine direct usage and alias usage
    combined_counts = defaultdict(int)
    for concept_id, count in usage_counts.items():
        combined_counts[concept_id] += count
    for concept_id, count in alias_usage.items():
        combined_counts[concept_id] += count
    
    # Update all concepts
    all_concepts = concepts_collection.find({})
    updated_count = 0
    unchanged_count = 0
    
    for concept in all_concepts:
        concept_id = concept['_id']
        new_count = combined_counts.get(concept_id, 0)
        old_count = concept.get('usage_count', 0)
        
        if new_count != old_count:
            concepts_collection.update_one(
                {'_id': concept_id},
                {'$set': {'usage_count': new_count, 'usage_count_updated': datetime.utcnow()}}
            )
            updated_count += 1
            if new_count > 0:
                print(f"  ✓ {concept['display_name']}: {old_count} → {new_count}")
        else:
            unchanged_count += 1
    
    print(f"\n=== Usage Count Update Summary ===")
    print(f"Updated: {updated_count} concepts")
    print(f"Unchanged: {unchanged_count} concepts")
    print(f"Total concepts: {updated_count + unchanged_count}")

def verify_usage_counts():
    """Verify usage counts are reasonable."""
    print("\n=== Verifying Usage Counts ===")
    
    # Check concepts with highest usage
    print("\nTop 10 most used concepts:")
    top_concepts = concepts_collection.find().sort('usage_count', -1).limit(10)
    for concept in top_concepts:
        print(f"  {concept['display_name']}: {concept.get('usage_count', 0)} uses")
    
    # Check concepts with zero usage (excluding main categories)
    zero_usage = concepts_collection.count_documents({
        'usage_count': 0,
        'is_main_category': {'$ne': True}
    })
    total_non_category = concepts_collection.count_documents({
        'is_main_category': {'$ne': True}
    })
    
    print(f"\nConcepts with zero usage: {zero_usage} / {total_non_category} ({zero_usage/total_non_category*100:.1f}%)")
    
    # Check total usage across all concepts
    pipeline = [
        {'$group': {'_id': None, 'total': {'$sum': '$usage_count'}}}
    ]
    result = list(concepts_collection.aggregate(pipeline))
    total_usage = result[0]['total'] if result else 0
    
    # Compare with actual instance count
    actual_instances = instances_collection.count_documents({})
    
    print(f"\nTotal usage count: {total_usage}")
    print(f"Actual tag instances: {actual_instances}")
    print(f"Difference: {abs(total_usage - actual_instances)}")

def main():
    print("🔧 FIXING USAGE COUNTS")
    print("="*50)
    
    # Count concept usage
    usage_counts = count_concept_usage()
    print(f"Found usage in {len(usage_counts)} concepts from tag_instances")
    
    # Count alias usage
    alias_usage = count_alias_usage()
    print(f"Found usage through {len(alias_usage)} concept aliases")
    
    # Update usage counts
    update_usage_counts(usage_counts, alias_usage)
    
    # Verify the results
    verify_usage_counts()
    
    print("\n✅ Usage counts have been recalculated!")
    print("You can now proceed with fixing tag display issues.")

if __name__ == "__main__":
    main()