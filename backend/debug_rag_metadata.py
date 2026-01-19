#!/usr/bin/env python3
"""
Debug script to check RAG metadata structure
"""
import pickle
import os

def debug_metadata():
    """Check the structure of metadata in the RAG index"""
    
    metadata_path = 'data/rag_index/metadata.pkl'
    doc_map_path = 'data/rag_index/doc_map.pkl'
    
    print("="*60)
    print("RAG METADATA DEBUG")
    print("="*60)
    
    if not os.path.exists(metadata_path):
        print("❌ Metadata file not found")
        return
    
    # Load metadata
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f)
    
    print(f"Total metadata entries: {len(metadata)}")
    
    # Check first few entries
    for i, (key, value) in enumerate(list(metadata.items())[:3]):
        print(f"\n--- Entry {i+1} ---")
        print(f"Key: {key}")
        print(f"Value type: {type(value)}")
        
        if hasattr(value, '__dict__'):
            # It's an object
            print("Object attributes:")
            for attr, val in value.__dict__.items():
                if attr == 'content':
                    print(f"  {attr}: {str(val)[:100]}...")
                elif attr == 'metadata':
                    print(f"  {attr}: {type(val)}")
                else:
                    print(f"  {attr}: {val}")
        elif isinstance(value, dict):
            # It's a dict
            print("Dict keys:", list(value.keys()))
            for k, v in value.items():
                if k == 'content':
                    print(f"  {k}: {str(v)[:100]}...")
                elif k == 'metadata':
                    print(f"  {k}: {type(v)}")
                else:
                    print(f"  {k}: {v}")
        else:
            print(f"Unexpected type: {value}")
    
    # Check if all entries are the same type
    types = set()
    for value in metadata.values():
        types.add(type(value).__name__)
    
    print(f"\nUnique value types in metadata: {types}")
    
    # Check doc_map
    if os.path.exists(doc_map_path):
        with open(doc_map_path, 'rb') as f:
            doc_map = pickle.load(f)
        print(f"\nDoc map entries: {len(doc_map)}")
        
        # Check a sample
        sample_key = list(doc_map.keys())[0]
        sample_value = doc_map[sample_key]
        print(f"Sample doc_map entry: key={sample_key}, value type={type(sample_value)}, value={sample_value if isinstance(sample_value, str) else 'object'}")

if __name__ == "__main__":
    debug_metadata()