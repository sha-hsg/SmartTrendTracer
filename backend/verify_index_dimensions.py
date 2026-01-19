#!/usr/bin/env python3
"""Verify the dimensions of the FAISS index"""

import faiss
import os

index_path = "data/rag_index/faiss.index"

if os.path.exists(index_path):
    index = faiss.read_index(index_path)
    print(f"Index dimension: {index.d}")
    print(f"Total vectors: {index.ntotal}")
    
    if index.d == 768:
        print("✅ Correct! Using Gemini text-embedding-004 (768 dimensions)")
    elif index.d == 1536:
        print("⚠️ Using OpenAI text-embedding-ada-002 (1536 dimensions)")
    else:
        print(f"❓ Unknown embedding model with {index.d} dimensions")
else:
    print("No index found")