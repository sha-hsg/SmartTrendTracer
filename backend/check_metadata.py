#!/usr/bin/env python3
"""Check the metadata structure"""

import pickle
import os

metadata_path = "data/rag_index/metadata.pkl"

if os.path.exists(metadata_path):
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f)
    
    print(f"Metadata has {len(metadata)} entries")
    
    # Check first few entries
    for i, (doc_id, meta) in enumerate(metadata.items()):
        if i >= 3:
            break
        print(f"\nDocument ID: {doc_id}")
        print(f"  Type: {type(meta)}")
        if isinstance(meta, dict):
            print(f"  Keys: {list(meta.keys())}")
            if 'content' in meta:
                print(f"  Content preview: {meta['content'][:100]}...")
            if 'type' in meta:
                print(f"  Source type: {meta['type']}")
else:
    print("Metadata not found")