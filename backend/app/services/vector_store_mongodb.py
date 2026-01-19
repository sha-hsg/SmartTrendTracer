"""
Vector store service for MongoDB
Handles tag embeddings and similarity search
"""
import os
import pickle
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import openai
import faiss
from pymongo.database import Database
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.database.mongodb import get_database

logger = logging.getLogger(__name__)

class TagVectorStore:
    """Vector store for tag similarity search using MongoDB"""
    
    def __init__(self, 
                 index_path: str = "data/vector_store/faiss_index.bin",
                 metadata_path: str = "data/vector_store/metadata.pkl",
                 embeddings_cache_path: str = "data/vector_store/embeddings_cache.pkl"):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.embeddings_cache_path = embeddings_cache_path
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Load or create index
        self.index = None
        self.metadata = []
        self.embeddings_cache = {}
        
        self.load()
    
    def load(self):
        """Load existing index and metadata"""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                    
                if os.path.exists(self.embeddings_cache_path):
                    with open(self.embeddings_cache_path, 'rb') as f:
                        self.embeddings_cache = pickle.load(f)
                        
                print(f"Loaded vector store with {len(self.metadata)} tags")
            except Exception as e:
                print(f"Error loading vector store: {e}")
                self.index = None
                self.metadata = []
    
    def save(self):
        """Save index and metadata to disk"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
            
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
            
        with open(self.embeddings_cache_path, 'wb') as f:
            pickle.dump(self.embeddings_cache, f)
            
        print(f"Saved vector store with {len(self.metadata)} tags")
    
    def get_embedding(self, text: str, use_cache: bool = True) -> Optional[np.ndarray]:
        """Get embedding for text using OpenAI API"""
        if use_cache and text in self.embeddings_cache:
            return self.embeddings_cache[text]
        
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            embedding = np.array(response.data[0].embedding, dtype=np.float32)
            
            # Cache the embedding
            self.embeddings_cache[text] = embedding
            
            return embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return None
    
    def build_from_mongodb(self):
        """Build vector store from MongoDB collections"""
        print("Building unified vector store from MongoDB...")
        
        # Connect to MongoDB
        db = get_database()
        
        # Dictionary to store all tags with their counts and contexts
        unified_tags = {}  # tag -> {'count': total_count, 'contexts': [], 'sources': set()}
        
        # 1. Get tag concepts from MongoDB
        concepts = db.tag_concepts_v2.find({})
        concept_count = 0
        
        for concept in concepts:
            tag = concept.get('slug', '').replace('-', ' ')
            display_name = concept.get('display_name', tag)
            
            if tag not in unified_tags:
                unified_tags[tag] = {'count': 0, 'contexts': [], 'sources': set()}
            
            # Count usage from tag_instances
            usage_count = db.tag_instances.count_documents({'concept_id': concept['_id']})
            unified_tags[tag]['count'] += usage_count
            unified_tags[tag]['sources'].add('concepts')
            
            # Add display name as alias
            if display_name != tag and display_name:
                if display_name not in unified_tags:
                    unified_tags[display_name] = {'count': 0, 'contexts': [], 'sources': set()}
                unified_tags[display_name]['count'] += usage_count
                unified_tags[display_name]['sources'].add('concepts')
            
            concept_count += 1
        
        print(f"Found {concept_count} concepts in MongoDB")
        
        # 2. Get aliases
        aliases = db.tag_aliases_v2.find({})
        alias_count = 0
        
        for alias in aliases:
            alias_text = alias.get('alias_text', '')
            if alias_text and alias_text not in unified_tags:
                unified_tags[alias_text] = {'count': 1, 'contexts': [], 'sources': {'aliases'}}
            alias_count += 1
        
        print(f"Found {alias_count} aliases in MongoDB")
        
        # Build the FAISS index
        embeddings = []
        new_metadata = []
        
        print(f"Generating embeddings for {len(unified_tags)} unique tags...")

        def _embed(tag_key):
            return tag_key, self.get_embedding(tag_key)

        tags_list = list(unified_tags.items())
        with ThreadPoolExecutor(max_workers=min(8, len(tags_list) or 1)) as executor:
            futures = {executor.submit(_embed, tag): (tag, info) for tag, info in tags_list}
            for idx, future in enumerate(as_completed(futures)):
                tag, info = futures[future]
                if idx % 20 == 0:
                    print(f"Processing tag {idx}/{len(tags_list)}...")
                try:
                    _, embedding = future.result()
                except Exception as exc:  # pragma: no cover - defensive logging
                    print(f"Error embedding tag {tag}: {exc}")
                    embedding = None

                if embedding is not None:
                    embeddings.append(embedding)
                    new_metadata.append({
                        'tag': tag,
                        'count': info['count'],
                        'sources': list(info['sources'])
                    })
        
        if embeddings:
            # Create FAISS index
            dimension = len(embeddings[0])
            self.index = faiss.IndexFlatL2(dimension)
            embeddings_array = np.array(embeddings, dtype=np.float32)
            self.index.add(embeddings_array)
            
            self.metadata = new_metadata
            self.save()
            
            print(f"Built vector store with {len(self.metadata)} tags")
        else:
            print("No embeddings generated")
    
    def search_similar(self, query: str, k: int = 10, threshold: float = 0.5) -> List[Dict]:
        """Search for similar tags"""
        if self.index is None or len(self.metadata) == 0:
            print("Vector store not initialized")
            return []
        
        # Get query embedding
        query_embedding = self.get_embedding(query)
        if query_embedding is None:
            return []
        
        # Search in FAISS
        query_embedding = query_embedding.reshape(1, -1)
        distances, indices = self.index.search(query_embedding, min(k * 2, len(self.metadata)))
        
        # Filter and format results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                # Convert L2 distance to similarity score (0-1)
                # Assuming embeddings are normalized, max distance is ~2
                similarity = max(0, 1 - (dist / 2))
                
                if similarity >= threshold:
                    result = self.metadata[idx].copy()
                    result['score'] = float(similarity)
                    results.append(result)
        
        # Sort by score and limit
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:k]

# Singleton instance
_vector_store = None

def get_vector_store() -> TagVectorStore:
    """Get or create vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = TagVectorStore()
    return _vector_store
