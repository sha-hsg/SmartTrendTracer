"""
Embeddings service for semantic similarity matching
Uses OpenAI embeddings API for vector representations
"""
import json
import os
import numpy as np
from typing import List, Dict, Tuple, Optional
from openai import OpenAI
from datetime import datetime, timedelta
import hashlib
import pickle
from pathlib import Path

class EmbeddingsService:
    def __init__(self):
        """Initialize embeddings service with OpenAI client"""
        # Load configuration
        with open('llm.json', 'r') as f:
            self.llm_config = json.load(f)
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=os.getenv(self.llm_config['api_settings']['api_key_env'])
        )
        
        # Use text-embedding-3-small for cost efficiency
        self.embedding_model = "text-embedding-3-small"
        
        # Cache directory for embeddings
        self.cache_dir = Path("data/embeddings_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self._embeddings_cache = {}
        self._load_cache()
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.md5(f"{self.embedding_model}:{text}".encode()).hexdigest()
    
    def _load_cache(self):
        """Load embeddings cache from disk"""
        cache_file = self.cache_dir / "embeddings.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    self._embeddings_cache = pickle.load(f)
                print(f"Loaded {len(self._embeddings_cache)} cached embeddings")
            except Exception as e:
                print(f"Error loading embeddings cache: {e}")
                self._embeddings_cache = {}
    
    def _save_cache(self):
        """Save embeddings cache to disk"""
        cache_file = self.cache_dir / "embeddings.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(self._embeddings_cache, f)
        except Exception as e:
            print(f"Error saving embeddings cache: {e}")
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding vector for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if error
        """
        # Check cache first
        cache_key = self._get_cache_key(text)
        if cache_key in self._embeddings_cache:
            return self._embeddings_cache[cache_key]
        
        try:
            # Get embedding from OpenAI
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            
            embedding = response.data[0].embedding
            
            # Cache the result
            self._embeddings_cache[cache_key] = embedding
            self._save_cache()
            
            return embedding
            
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return None
    
    def get_embeddings_batch(self, texts: List[str]) -> Dict[str, List[float]]:
        """
        Get embeddings for multiple texts efficiently
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Dict mapping text to embedding
        """
        results = {}
        uncached_texts = []
        
        # Check cache first
        for text in texts:
            cache_key = self._get_cache_key(text)
            if cache_key in self._embeddings_cache:
                results[text] = self._embeddings_cache[cache_key]
            else:
                uncached_texts.append(text)
        
        # Batch process uncached texts
        if uncached_texts:
            try:
                # OpenAI allows up to 2048 embeddings per request
                # But we'll do smaller batches for safety
                batch_size = 100
                for i in range(0, len(uncached_texts), batch_size):
                    batch = uncached_texts[i:i + batch_size]
                    
                    response = self.client.embeddings.create(
                        model=self.embedding_model,
                        input=batch
                    )
                    
                    # Store results
                    for text, embedding_data in zip(batch, response.data):
                        embedding = embedding_data.embedding
                        results[text] = embedding
                        
                        # Cache it
                        cache_key = self._get_cache_key(text)
                        self._embeddings_cache[cache_key] = embedding
                
                # Save cache after batch
                self._save_cache()
                
            except Exception as e:
                print(f"Error getting batch embeddings: {e}")
        
        return results
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1: First embedding vector
            vec2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Ensure it's between -1 and 1 (handle floating point errors)
        similarity = max(-1.0, min(1.0, similarity))
        
        # Convert to 0-1 scale
        return (similarity + 1) / 2
    
    def find_similar_tags(
        self, 
        tweet_text: str, 
        existing_tags: List[str], 
        top_k: int = 5,
        min_similarity: float = 0.7
    ) -> List[Tuple[str, float]]:
        """
        Find existing tags most similar to tweet content
        
        Args:
            tweet_text: The tweet content
            existing_tags: List of existing tags to compare
            top_k: Number of top similar tags to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of (tag, similarity_score) tuples
        """
        if not tweet_text or not existing_tags:
            return []
        
        # Get embedding for tweet
        tweet_embedding = self.get_embedding(tweet_text)
        if not tweet_embedding:
            return []
        
        # Get embeddings for all existing tags
        tag_embeddings = self.get_embeddings_batch(existing_tags)
        
        # Calculate similarities
        similarities = []
        for tag in existing_tags:
            if tag in tag_embeddings:
                tag_embedding = tag_embeddings[tag]
                similarity = self.cosine_similarity(tweet_embedding, tag_embedding)
                if similarity >= min_similarity:
                    similarities.append((tag, similarity))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def find_similar_from_tag_descriptions(
        self,
        tweet_text: str,
        tag_descriptions: Dict[str, str],
        top_k: int = 5,
        min_similarity: float = 0.7
    ) -> List[Tuple[str, float]]:
        """
        Find tags based on similarity to tag descriptions
        
        Args:
            tweet_text: The tweet content
            tag_descriptions: Dict mapping tag to its description/context
            top_k: Number of top similar tags to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of (tag, similarity_score) tuples
        """
        if not tweet_text or not tag_descriptions:
            return []
        
        # Get embedding for tweet
        tweet_embedding = self.get_embedding(tweet_text)
        if not tweet_embedding:
            return []
        
        # Get embeddings for tag descriptions
        descriptions = list(tag_descriptions.values())
        desc_embeddings = self.get_embeddings_batch(descriptions)
        
        # Calculate similarities
        similarities = []
        for tag, description in tag_descriptions.items():
            if description in desc_embeddings:
                desc_embedding = desc_embeddings[description]
                similarity = self.cosine_similarity(tweet_embedding, desc_embedding)
                if similarity >= min_similarity:
                    similarities.append((tag, similarity))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def create_tag_context(self, tag: str, sample_tweets: List[str]) -> str:
        """
        Create context for a tag based on sample tweets using it
        
        Args:
            tag: The tag
            sample_tweets: Sample tweets that use this tag
            
        Returns:
            Context string for the tag
        """
        if not sample_tweets:
            return tag
        
        # Combine tag with sample context
        context_parts = [tag]
        
        # Add first few tweets as context (limit to avoid too long text)
        for tweet in sample_tweets[:3]:
            # Clean tweet text
            clean_tweet = tweet.replace('\n', ' ').strip()
            if len(clean_tweet) > 100:
                clean_tweet = clean_tweet[:100] + "..."
            context_parts.append(clean_tweet)
        
        return " | ".join(context_parts)


# Singleton instance
_embeddings_service = None

def get_embeddings_service() -> EmbeddingsService:
    """Get or create embeddings service instance"""
    global _embeddings_service
    if _embeddings_service is None:
        _embeddings_service = EmbeddingsService()
    return _embeddings_service