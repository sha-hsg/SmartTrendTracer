#!/usr/bin/env python3
"""Check the structure of doc_map in the index"""

import pickle
import os

doc_map_path = "data/rag_index/doc_map.pkl"

if os.path.exists(doc_map_path):
    with open(doc_map_path, 'rb') as f:
        doc_map = pickle.load(f)
    
    print(f"Doc map has {len(doc_map)} entries")
    
    # Check first few entries
    for i, (idx, doc) in enumerate(doc_map.items()):
        if i >= 3:
            break
        print(f"\nEntry {idx}:")
        print(f"  Type: {type(doc)}")
        if isinstance(doc, dict):
            print(f"  Keys: {doc.keys()}")
            if 'content' in doc:
                print(f"  Content preview: {doc['content'][:100]}...")
        elif isinstance(doc, str):
            print(f"  String value: {doc[:100]}...")
        elif hasattr(doc, '__dict__'):
            print(f"  Attributes: {doc.__dict__.keys()}")
            if hasattr(doc, 'content'):
                print(f"  Content preview: {doc.content[:100]}...")
else:
    print("Doc map not found")