#!/usr/bin/env python3
"""Check what types of content are in the RAG index"""

import pickle
import os
from collections import Counter

metadata_path = "data/rag_index/metadata.pkl"

if os.path.exists(metadata_path):
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f)
    
    print(f"Total documents in index: {len(metadata)}")
    
    # Count document types
    type_counts = Counter()
    paper_samples = []
    
    for doc_id, meta in metadata.items():
        doc_type = meta.get('type', 'unknown')
        type_counts[doc_type] += 1
        
        # Collect some paper samples
        if doc_type == 'paper' and len(paper_samples) < 5:
            paper_samples.append({
                'id': doc_id,
                'title': meta.get('metadata', {}).get('title', 'No title'),
                'content_preview': meta.get('content', '')[:200]
            })
    
    print("\nDocument types in index:")
    for doc_type, count in type_counts.most_common():
        print(f"  - {doc_type}: {count}")
    
    if paper_samples:
        print(f"\nSample papers in index:")
        for paper in paper_samples:
            print(f"\n  ID: {paper['id']}")
            print(f"  Title: {paper['title']}")
            print(f"  Content: {paper['content_preview'][:100]}...")
    else:
        print("\n⚠️ NO PAPERS FOUND IN INDEX!")
        
    # Check for any document IDs that look like papers
    paper_like_ids = [doc_id for doc_id in metadata.keys() if 'paper' in doc_id.lower()]
    print(f"\nDocument IDs containing 'paper': {len(paper_like_ids)}")
    if paper_like_ids and len(paper_like_ids) <= 10:
        print("  IDs:", paper_like_ids[:10])
        
else:
    print("Metadata file not found")