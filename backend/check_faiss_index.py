#!/usr/bin/env python3
"""Check FAISS index dimensions and diagnose issues"""

import faiss
import numpy as np
import pickle
import os
from openai import OpenAI

def check_index():
    """Check the FAISS index dimensions"""
    index_path = "data/rag_index/faiss.index"
    
    if not os.path.exists(index_path):
        print(f"Index file not found: {index_path}")
        return
    
    try:
        # Load the index
        index = faiss.read_index(index_path)
        print(f"Index loaded successfully")
        print(f"Index dimension: {index.d}")
        print(f"Total vectors: {index.ntotal}")
        
        # Test with a query embedding
        client = OpenAI()
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input="test query"
        )
        test_embedding = np.array(response.data[0].embedding, dtype=np.float32)
        print(f"Test embedding dimension: {len(test_embedding)}")
        
        # Reshape and normalize
        test_embedding = test_embedding.reshape(1, -1)
        faiss.normalize_L2(test_embedding)
        
        # Try to search
        print(f"Attempting search with embedding shape: {test_embedding.shape}")
        scores, indices = index.search(test_embedding, min(5, index.ntotal))
        print(f"Search successful! Found {len(indices[0])} results")
        
    except AssertionError as e:
        print(f"Dimension mismatch error: {e}")
        print("The index dimension doesn't match the query embedding dimension")
        print("This usually means the index was built with a different embedding model")
        print("\nRecommendation: Rebuild the index")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_index()