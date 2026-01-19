"""
Vector store for efficient semantic similarity search
Uses FAISS for indexing and sentence-transformers for embeddings
"""
import json
import os
import numpy as np
import faiss
import pickle
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
from sentence_transformers import SentenceTransformer
from datetime import datetime

class TagVectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize vector store for tag similarity
        
        Args:
            model_name: Sentence transformer model to use
        """
        # Initialize sentence transformer
        import os
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        
        # Try to load the model
        try:
            self.model = SentenceTransformer(model_name)
            print(f"✅ Loaded embedding model: {model_name}")
        except Exception as e:
            print(f"Warning: Could not load {model_name}: {e}")
            # Fallback to a simple model
            print("Using fallback embedding model...")
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
        
        # Storage paths
        self.data_dir = Path("data/vector_store")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata storage
        self.tag_to_id = {}  # Map tag to index ID
        self.id_to_tag = {}  # Map index ID to tag
        self.tag_contexts = {}  # Store context for each tag
        self.tag_counts = {}  # Store usage count for each tag
        
        # Load existing index if available
        self.load()
    
    def save(self):
        """Save vector store to disk"""
        try:
            # Save FAISS index
            index_path = self.data_dir / "faiss_index.bin"
            faiss.write_index(self.index, str(index_path))
            
            # Save metadata
            metadata = {
                'tag_to_id': self.tag_to_id,
                'id_to_tag': self.id_to_tag,
                'tag_contexts': self.tag_contexts,
                'tag_counts': self.tag_counts,
                'embedding_dim': self.embedding_dim,
                'model_name': self.model.model_name_or_path
            }
            
            metadata_path = self.data_dir / "metadata.pkl"
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            print(f"✅ Saved vector store with {len(self.tag_to_id)} tags")
            
        except Exception as e:
            print(f"Error saving vector store: {e}")
    
    def load(self):
        """Load vector store from disk"""
        try:
            index_path = self.data_dir / "faiss_index.bin"
            metadata_path = self.data_dir / "metadata.pkl"
            
            if index_path.exists() and metadata_path.exists():
                # Load FAISS index
                self.index = faiss.read_index(str(index_path))
                
                # Load metadata
                with open(metadata_path, 'rb') as f:
                    metadata = pickle.load(f)
                
                self.tag_to_id = metadata['tag_to_id']
                self.id_to_tag = metadata['id_to_tag']
                self.tag_contexts = metadata.get('tag_contexts', {})
                self.tag_counts = metadata.get('tag_counts', {})
                
                print(f"✅ Loaded vector store with {len(self.tag_to_id)} tags")
                return True
                
        except Exception as e:
            print(f"Error loading vector store: {e}")
        
        return False
    
    def add_tag(self, tag: str, context: str = None, count: int = 1):
        """
        Add a tag to the vector store
        
        Args:
            tag: The tag to add
            context: Optional context/description for the tag
            count: Usage count for the tag
        """
        if tag in self.tag_to_id:
            # Update existing tag
            tag_id = self.tag_to_id[tag]
            self.tag_counts[tag] = self.tag_counts.get(tag, 0) + count
            if context:
                # Append to existing context
                existing = self.tag_contexts.get(tag, tag)
                self.tag_contexts[tag] = f"{existing} | {context}"
        else:
            # Add new tag
            # Create embedding from tag and context
            text_to_embed = f"{tag}: {context}" if context else tag
            embedding = self.model.encode([text_to_embed], normalize_embeddings=True)
            
            # Add to FAISS index
            tag_id = len(self.tag_to_id)
            self.index.add(embedding)
            
            # Update metadata
            self.tag_to_id[tag] = tag_id
            self.id_to_tag[tag_id] = tag
            self.tag_contexts[tag] = context or tag
            self.tag_counts[tag] = count
    
    def add_tags_batch(self, tags_data: List[Dict[str, Any]]):
        """
        Add multiple tags in batch
        
        Args:
            tags_data: List of dicts with 'tag', 'context', and 'count' keys
        """
        new_tags = []
        new_embeddings = []
        
        for data in tags_data:
            tag = data['tag']
            context = data.get('context', '')
            count = data.get('count', 1)
            
            if tag not in self.tag_to_id:
                # Prepare for batch embedding
                text_to_embed = f"{tag}: {context}" if context else tag
                new_tags.append((tag, context, count))
                new_embeddings.append(text_to_embed)
            else:
                # Update existing tag count
                self.tag_counts[tag] = self.tag_counts.get(tag, 0) + count
        
        if new_embeddings:
            # Batch encode
            embeddings = self.model.encode(new_embeddings, normalize_embeddings=True)
            
            # Add to index
            self.index.add(embeddings)
            
            # Update metadata
            for (tag, context, count), embedding in zip(new_tags, embeddings):
                tag_id = len(self.tag_to_id)
                self.tag_to_id[tag] = tag_id
                self.id_to_tag[tag_id] = tag
                self.tag_contexts[tag] = context or tag
                self.tag_counts[tag] = count
    
    def search_similar_tags(
        self, 
        query_text: str, 
        k: int = 5,
        min_similarity: float = 0.5
    ) -> List[Tuple[str, float, int]]:
        """
        Search for tags similar to query text
        
        Args:
            query_text: Text to find similar tags for
            k: Number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of (tag, similarity_score, usage_count) tuples
        """
        if not query_text or self.index.ntotal == 0:
            return []
        
        # Encode query
        query_embedding = self.model.encode([query_text], normalize_embeddings=True)
        
        # Search in FAISS
        scores, indices = self.index.search(query_embedding, min(k * 2, self.index.ntotal))
        
        # Process results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and score >= min_similarity:
                tag = self.id_to_tag[idx]
                count = self.tag_counts.get(tag, 0)
                results.append((tag, float(score), count))
        
        # Sort by score * log(count + 1) to favor popular tags
        results.sort(key=lambda x: x[1] * np.log1p(x[2]), reverse=True)
        
        return results[:k]
    
    def build_from_database(self, db: Session):
        """
        Build vector store from existing database tags
        
        Args:
            db: Database session
        """
        print("Building vector store from database...")
        
        # Get all unique tags with counts and sample tweets
        from sqlalchemy import func
        
        # Get tag counts
        tag_stats = db.query(
            Tag.tag,
            func.count(Tag.id).label('count')
        ).group_by(Tag.tag).all()
        
        tags_data = []
        
        for tag, count in tag_stats:
            # Get sample tweets for context
            sample_tweets = db.query(Tweet.text).join(
                Tag, Tag.tweet_id == Tweet.id
            ).filter(Tag.tag == tag).limit(5).all()
            
            # Create context from sample tweets
            context_parts = []
            for (tweet_text,) in sample_tweets:
                # Clean and truncate tweet
                clean_text = tweet_text.replace('\n', ' ').strip()
                if clean_text.startswith('RT @'):
                    # Extract core content from RT
                    parts = clean_text.split(':', 1)
                    if len(parts) > 1:
                        clean_text = parts[1].strip()
                
                if len(clean_text) > 100:
                    clean_text = clean_text[:100]
                
                context_parts.append(clean_text)
            
            context = " | ".join(context_parts) if context_parts else tag
            
            tags_data.append({
                'tag': tag,
                'context': context,
                'count': count
            })
        
        # Clear existing index
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.tag_to_id = {}
        self.id_to_tag = {}
        self.tag_contexts = {}
        self.tag_counts = {}
        
        # Add all tags
        self.add_tags_batch(tags_data)
        
        # Save to disk
        self.save()
        
        print(f"✅ Built vector store with {len(self.tag_to_id)} unique tags")
    
    def update_tag_context(self, tag: str, new_tweet_text: str):
        """
        Update tag context with a new tweet
        
        Args:
            tag: The tag to update
            new_tweet_text: New tweet text using this tag
        """
        if tag not in self.tag_to_id:
            # Add new tag
            self.add_tag(tag, context=new_tweet_text, count=1)
        else:
            # Update count
            self.tag_counts[tag] = self.tag_counts.get(tag, 0) + 1
            
            # Update context (keep it manageable)
            existing_context = self.tag_contexts.get(tag, tag)
            if len(existing_context) < 500:  # Limit context length
                clean_text = new_tweet_text.replace('\n', ' ').strip()[:100]
                self.tag_contexts[tag] = f"{existing_context} | {clean_text}"
                
                # Re-embed with new context
                tag_id = self.tag_to_id[tag]
                text_to_embed = f"{tag}: {self.tag_contexts[tag]}"
                new_embedding = self.model.encode([text_to_embed], normalize_embeddings=True)
                
                # Update in FAISS (this is inefficient, but ok for small updates)
                # For production, consider periodic rebuilds instead
                # Note: FAISS doesn't support direct update, so we'd need to rebuild
                # For now, we'll just update the context metadata
        
        # Periodically save
        if len(self.tag_to_id) % 10 == 0:
            self.save()
    
    def get_tag_info(self, tag: str) -> Dict[str, Any]:
        """
        Get information about a tag
        
        Args:
            tag: The tag to look up
            
        Returns:
            Dict with tag information
        """
        if tag not in self.tag_to_id:
            return None
        
        return {
            'tag': tag,
            'count': self.tag_counts.get(tag, 0),
            'context': self.tag_contexts.get(tag, tag),
            'id': self.tag_to_id[tag]
        }

# Singleton instance
_vector_store = None

def get_vector_store() -> TagVectorStore:
    """Get or create vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = TagVectorStore()
    return _vector_store