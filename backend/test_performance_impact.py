#!/usr/bin/env python3
"""Test performance impact of hierarchy changes"""

from pymongo import MongoClient
from bson import ObjectId
import time
import statistics

def benchmark_query(func, iterations=10):
    """Benchmark a query function"""
    times = []
    for _ in range(iterations):
        start = time.time()
        result = func()
        elapsed = (time.time() - start) * 1000  # Convert to ms
        times.append(elapsed)
    
    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0,
        'min': min(times),
        'max': max(times)
    }

def test_performance():
    """Test query performance with new hierarchy"""
    client = MongoClient()
    db = client.smarttrendtracer
    
    print("=== Performance Impact Assessment ===\n")
    
    # Test 1: Root category queries
    print("1. Root Category Queries:")
    
    def query_roots():
        return list(db.tag_concepts_v2.find({"parents": []}))
    
    results = benchmark_query(query_roots)
    print(f"  Mean: {results['mean']:.2f}ms")
    print(f"  Median: {results['median']:.2f}ms")
    print(f"  Std Dev: {results['stdev']:.2f}ms")
    print(f"  Range: {results['min']:.2f}ms - {results['max']:.2f}ms")
    
    # Test 2: Get all children of a category
    print("\n2. Get Children of Category (AI/ML Fundamentals):")
    
    # First find the AI/ML Fundamentals category
    ai_ml = db.tag_concepts_v2.find_one({"slug": "ai-ml-fundamentals"})
    if ai_ml:
        ai_ml_id = str(ai_ml['_id'])
        
        def query_children():
            return list(db.tag_concepts_v2.find({"parents": ai_ml_id}))
        
        results = benchmark_query(query_children)
        print(f"  Mean: {results['mean']:.2f}ms")
        print(f"  Median: {results['median']:.2f}ms")
        print(f"  Std Dev: {results['stdev']:.2f}ms")
    else:
        print("  AI/ML Fundamentals category not found")
    
    # Test 3: Full hierarchy traversal
    print("\n3. Full Hierarchy Traversal:")
    
    def traverse_hierarchy():
        all_concepts = list(db.tag_concepts_v2.find())
        concept_map = {str(c['_id']): c for c in all_concepts}
        
        # Build adjacency lists
        children_map = {}
        for concept in all_concepts:
            for parent_id in concept.get('parents', []):
                parent_id_str = str(parent_id)
                if parent_id_str not in children_map:
                    children_map[parent_id_str] = []
                children_map[parent_id_str].append(str(concept['_id']))
        
        return len(children_map)
    
    results = benchmark_query(traverse_hierarchy, iterations=5)
    print(f"  Mean: {results['mean']:.2f}ms")
    print(f"  Median: {results['median']:.2f}ms")
    print(f"  Std Dev: {results['stdev']:.2f}ms")
    
    # Test 4: Aggregation pipeline for usage stats
    print("\n4. Usage Statistics Aggregation:")
    
    def aggregate_usage():
        pipeline = [
            {"$match": {"parents": []}},  # Root categories only
            {"$lookup": {
                "from": "tag_concepts_v2",
                "let": {"parent_id": {"$toString": "$_id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$in": ["$$parent_id", "$parents"]}}},
                    {"$group": {
                        "_id": None,
                        "total_usage": {"$sum": "$usage_count"}
                    }}
                ],
                "as": "children_stats"
            }},
            {"$project": {
                "slug": 1,
                "display_name": 1,
                "usage_count": 1,
                "children_usage": {
                    "$ifNull": [
                        {"$arrayElemAt": ["$children_stats.total_usage", 0]},
                        0
                    ]
                }
            }}
        ]
        return list(db.tag_concepts_v2.aggregate(pipeline))
    
    results = benchmark_query(aggregate_usage, iterations=5)
    print(f"  Mean: {results['mean']:.2f}ms")
    print(f"  Median: {results['median']:.2f}ms")
    print(f"  Std Dev: {results['stdev']:.2f}ms")
    
    # Test 5: Search by display name (case-insensitive)
    print("\n5. Search by Display Name:")
    
    def search_concepts():
        return list(db.tag_concepts_v2.find(
            {"display_name": {"$regex": "learning", "$options": "i"}},
            limit=10
        ))
    
    results = benchmark_query(search_concepts)
    print(f"  Mean: {results['mean']:.2f}ms")
    print(f"  Median: {results['median']:.2f}ms")
    print(f"  Std Dev: {results['stdev']:.2f}ms")
    
    # Test 6: Get concept with all relationships
    print("\n6. Get Concept with Full Context:")
    
    def get_full_concept():
        # Get a concept with multiple parents (poly-hierarchy)
        concept = db.tag_concepts_v2.find_one({"$expr": {"$gt": [{"$size": "$parents"}, 1]}})
        if not concept:
            concept = db.tag_concepts_v2.find_one({"slug": "machine-learning"})
        
        if concept:
            # Get parent concepts
            parent_ids = [ObjectId(p) if isinstance(p, str) else p for p in concept.get('parents', [])]
            parents = list(db.tag_concepts_v2.find({"_id": {"$in": parent_ids}}))
            
            # Get child concepts
            concept_id_str = str(concept['_id'])
            children = list(db.tag_concepts_v2.find({"parents": concept_id_str}))
            
            # Get aliases
            aliases = list(db.tag_aliases_v2.find({"concept_id": concept['_id']}))
            
            # Get usage instances
            instances = db.tag_instances.count_documents({"concept_id": concept['_id']})
            
            return {
                'concept': concept,
                'parents': parents,
                'children': children,
                'aliases': aliases,
                'instances': instances
            }
        return None
    
    results = benchmark_query(get_full_concept, iterations=5)
    print(f"  Mean: {results['mean']:.2f}ms")
    print(f"  Median: {results['median']:.2f}ms")
    print(f"  Std Dev: {results['stdev']:.2f}ms")
    
    # Test 7: Index effectiveness
    print("\n7. Index Effectiveness Check:")
    
    # Check existing indexes
    indexes = db.tag_concepts_v2.list_indexes()
    print("  Current indexes on tag_concepts_v2:")
    for index in indexes:
        print(f"    - {index['name']}: {index.get('key', {})}")
    
    # Test query with and without index
    print("\n  Query performance comparison:")
    
    # Query that should use index
    def indexed_query():
        return db.tag_concepts_v2.find_one({"slug": "machine-learning"})
    
    indexed_results = benchmark_query(indexed_query)
    print(f"    Indexed query (by slug): {indexed_results['mean']:.2f}ms")
    
    # Query that might not use index efficiently
    def unindexed_query():
        return list(db.tag_concepts_v2.find({"usage_count": {"$gt": 100}}))
    
    unindexed_results = benchmark_query(unindexed_query)
    print(f"    Range query (usage_count > 100): {unindexed_results['mean']:.2f}ms")
    
    # Summary
    print("\n=== PERFORMANCE SUMMARY ===")
    
    # Determine performance grade
    if indexed_results['mean'] < 5 and unindexed_results['mean'] < 50:
        grade = "✅ EXCELLENT"
        desc = "All queries very fast"
    elif indexed_results['mean'] < 10 and unindexed_results['mean'] < 100:
        grade = "✅ GOOD"
        desc = "Acceptable performance"
    elif indexed_results['mean'] < 20 and unindexed_results['mean'] < 200:
        grade = "⚠️ FAIR"
        desc = "Could benefit from optimization"
    else:
        grade = "❌ POOR"
        desc = "Needs immediate optimization"
    
    print(f"Performance Grade: {grade}")
    print(f"Assessment: {desc}")
    
    # Recommendations
    print("\n=== RECOMMENDATIONS ===")
    
    recommendations = []
    
    # Check if slug index exists
    has_slug_index = any('slug' in str(idx.get('key', {})) for idx in indexes)
    if not has_slug_index:
        recommendations.append("Create index on 'slug' field for faster lookups")
    
    # Check if parents index exists
    has_parents_index = any('parents' in str(idx.get('key', {})) for idx in indexes)
    if not has_parents_index:
        recommendations.append("Create index on 'parents' field for hierarchy queries")
    
    # Check if usage_count index exists
    has_usage_index = any('usage_count' in str(idx.get('key', {})) for idx in indexes)
    if not has_usage_index and unindexed_results['mean'] > 50:
        recommendations.append("Consider index on 'usage_count' if frequently queried")
    
    # Check collection size
    total_concepts = db.tag_concepts_v2.count_documents({})
    if total_concepts > 10000:
        recommendations.append("Consider sharding for collections over 10K documents")
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
    else:
        print("No immediate optimizations needed")

if __name__ == "__main__":
    test_performance()