"""
Vector store using OpenAI embeddings for semantic similarity
More reliable than HuggingFace models and integrates with existing OpenAI setup
"""
import json
import os
import numpy as np
import faiss
import pickle
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
from datetime import datetime
from openai import OpenAI

class TagVectorStore:
    def __init__(self):
        """Initialize vector store with OpenAI embeddings"""
        # Load configuration
        with open('llm.json', 'r') as f:
            self.llm_config = json.load(f)
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=os.getenv(self.llm_config['api_settings']['api_key_env'])
        )
        
        # Use text-embedding-3-small for cost efficiency
        self.embedding_model = "text-embedding-3-small"
        self.embedding_dim = 1536  # Dimension for text-embedding-3-small
        
        # Initialize FAISS index (cosine similarity via inner product with normalized vectors)
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        
        # Storage paths
        self.data_dir = Path("data/vector_store")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata storage
        self.tag_to_id = {}  # Map tag to index ID
        self.id_to_tag = {}  # Map index ID to tag
        self.tag_contexts = {}  # Store context for each tag
        self.tag_counts = {}  # Store usage count for each tag
        
        # Embeddings cache
        self.embeddings_cache = {}
        
        # Load existing index if available
        self.load()
    
    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding for text using OpenAI API"""
        # Check cache
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
        
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            embedding = np.array(response.data[0].embedding)
            
            # Normalize for cosine similarity
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            # Cache it
            self.embeddings_cache[text] = embedding
            
            return embedding
            
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return None
    
    def get_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Get embeddings for multiple texts efficiently"""
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache first
        for i, text in enumerate(texts):
            if text in self.embeddings_cache:
                embeddings.append(self.embeddings_cache[text])
            else:
                embeddings.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Batch process uncached texts
        if uncached_texts:
            try:
                # OpenAI can handle batches efficiently
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=uncached_texts
                )
                
                for idx, embedding_data in zip(uncached_indices, response.data):
                    embedding = np.array(embedding_data.embedding)
                    
                    # Normalize
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        embedding = embedding / norm
                    
                    embeddings[idx] = embedding
                    self.embeddings_cache[texts[idx]] = embedding
                    
            except Exception as e:
                print(f"Error getting batch embeddings: {e}")
        
        return [e for e in embeddings if e is not None]
    
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
                'embedding_model': self.embedding_model
            }
            
            metadata_path = self.data_dir / "metadata.pkl"
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            # Save embeddings cache
            cache_path = self.data_dir / "embeddings_cache.pkl"
            with open(cache_path, 'wb') as f:
                pickle.dump(self.embeddings_cache, f)
            
            print(f"✅ Saved vector store with {len(self.tag_to_id)} tags")
            
        except Exception as e:
            print(f"Error saving vector store: {e}")
    
    def load(self):
        """Load vector store from disk"""
        try:
            index_path = self.data_dir / "faiss_index.bin"
            metadata_path = self.data_dir / "metadata.pkl"
            cache_path = self.data_dir / "embeddings_cache.pkl"
            
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
                
                # Load embeddings cache if available
                if cache_path.exists():
                    with open(cache_path, 'rb') as f:
                        self.embeddings_cache = pickle.load(f)
                
                print(f"✅ Loaded vector store with {len(self.tag_to_id)} tags")
                return True
                
        except Exception as e:
            print(f"Error loading vector store: {e}")
        
        return False
    
    def add_tag(self, tag: str, context: str = None, count: int = 1):
        """Add a tag to the vector store"""
        if tag in self.tag_to_id:
            # Update existing tag
            self.tag_counts[tag] = self.tag_counts.get(tag, 0) + count
            if context:
                # Update context
                existing = self.tag_contexts.get(tag, tag)
                if len(existing) < 500:  # Limit context length
                    self.tag_contexts[tag] = f"{existing} | {context[:100]}"
        else:
            # Add new tag
            text_to_embed = f"{tag}: {context}" if context else tag
            embedding = self.get_embedding(text_to_embed)
            
            if embedding is not None:
                # Add to FAISS index
                tag_id = len(self.tag_to_id)
                self.index.add(np.array([embedding]))
                
                # Update metadata
                self.tag_to_id[tag] = tag_id
                self.id_to_tag[tag_id] = tag
                self.tag_contexts[tag] = context or tag
                self.tag_counts[tag] = count
    
    def add_tags_batch(self, tags_data: List[Dict[str, Any]]):
        """Add multiple tags in batch"""
        new_tags = []
        texts_to_embed = []
        
        for data in tags_data:
            tag = data['tag']
            context = data.get('context', '')
            count = data.get('count', 1)
            
            if tag not in self.tag_to_id:
                text_to_embed = f"{tag}: {context}" if context else tag
                texts_to_embed.append(text_to_embed)
                new_tags.append((tag, context, count))
            else:
                # Update existing tag count
                self.tag_counts[tag] = self.tag_counts.get(tag, 0) + count
        
        if texts_to_embed:
            # Batch encode
            embeddings = self.get_embeddings_batch(texts_to_embed)
            
            if embeddings:
                # Add to index
                embeddings_array = np.array(embeddings)
                self.index.add(embeddings_array)
                
                # Update metadata
                for (tag, context, count) in new_tags:
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
        """Search for tags similar to query text"""
        if not query_text or self.index.ntotal == 0:
            return []
        
        # Preprocess long tweets to improve similarity matching
        processed_text = self._preprocess_tweet_for_search(query_text)
        
        # Debug logging for long tweets
        if len(query_text) > 280:
            print(f"Long tweet detected: {len(query_text)} chars -> processed to {len(processed_text)} chars")
            print(f"Similarity threshold: {min_similarity}")
        
        # Get query embedding
        query_embedding = self.get_embedding(processed_text)
        if query_embedding is None:
            return []
        
        # Search in FAISS
        query_array = np.array([query_embedding])
        scores, indices = self.index.search(query_array, min(k * 2, self.index.ntotal))
        
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
    
    def _preprocess_tweet_for_search(self, text: str) -> str:
        """Preprocess tweet text for better similarity matching"""
        # Remove RT prefix if present
        if text.startswith('RT @'):
            parts = text.split(':', 1)
            if len(parts) > 1:
                text = parts[1].strip()
        
        # Remove URLs to focus on content
        import re
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove mentions at the beginning (reply chains)
        text = re.sub(r'^(@\w+\s*)+', '', text)
        
        # Clean up extra whitespace
        text = ' '.join(text.split())
        
        # For very long tweets, use a sliding window approach
        # Take the first 500 chars and last 200 chars to capture key content
        if len(text) > 700:
            first_part = text[:500]
            last_part = text[-200:]
            # Try to find a sentence boundary
            if '. ' in first_part[-50:]:
                first_part = first_part[:first_part.rfind('. ') + 1]
            text = first_part + " ... " + last_part
        
        # If still too long, truncate to reasonable length for embedding
        # OpenAI recommends keeping under 8k tokens, ~500 chars is safe
        if len(text) > 1000:
            text = text[:1000]
        
        return text.strip()
    
    def build_from_database(self, db: Session):
        """Build vector store from ALL tags across all content types"""
        print("Building unified vector store from all content types...")
        
        from sqlalchemy import func
        
        # Dictionary to store all tags with their counts and contexts
        unified_tags = {}  # tag -> {'count': total_count, 'contexts': [], 'sources': set()}
        
        # 1. Get Twitter tags
        twitter_tags = db.query(
            Tag.tag,
            func.count(Tag.id).label('count')
        ).group_by(Tag.tag).all()
        
        print(f"Found {len(twitter_tags)} unique Twitter tags")
        
        for tag, count in twitter_tags:
            if tag not in unified_tags:
                unified_tags[tag] = {'count': 0, 'contexts': [], 'sources': set()}
            unified_tags[tag]['count'] += count
            unified_tags[tag]['sources'].add('twitter')
            
            # Get sample tweets for context
            sample_tweets = db.query(Tweet.text).join(
                Tag, Tag.tweet_id == Tweet.id
            ).filter(Tag.tag == tag).limit(3).all()
            
            for (tweet_text,) in sample_tweets:
                clean_text = tweet_text.replace('\n', ' ').strip()
                if clean_text.startswith('RT @'):
                    parts = clean_text.split(':', 1)
                    if len(parts) > 1:
                        clean_text = parts[1].strip()
                if len(clean_text) > 100:
                    clean_text = clean_text[:100]
                unified_tags[tag]['contexts'].append(clean_text)
        
        # 2. Get Paper tags
        paper_tags = db.query(
            PaperTag.tag,
            func.count(PaperTag.id).label('count')
        ).group_by(PaperTag.tag).all()
        
        print(f"Found {len(paper_tags)} unique Paper tags")
        
        for tag, count in paper_tags:
            if tag not in unified_tags:
                unified_tags[tag] = {'count': 0, 'contexts': [], 'sources': set()}
            unified_tags[tag]['count'] += count
            unified_tags[tag]['sources'].add('paper')
            
            # Get sample paper titles/abstracts for context
            sample_papers = db.query(Paper.title, Paper.abstract).join(
                PaperTag, PaperTag.paper_id == Paper.id
            ).filter(PaperTag.tag == tag).limit(2).all()
            
            for title, abstract in sample_papers:
                context = f"{title}: {abstract[:100] if abstract else ''}"
                unified_tags[tag]['contexts'].append(context[:150])
        
        # 3. Get Article tags
        article_tags = db.query(
            ArticleTag.tag,
            func.count(ArticleTag.id).label('count')
        ).group_by(ArticleTag.tag).all()
        
        print(f"Found {len(article_tags)} unique Article tags")
        
        for tag, count in article_tags:
            if tag not in unified_tags:
                unified_tags[tag] = {'count': 0, 'contexts': [], 'sources': set()}
            unified_tags[tag]['count'] += count
            unified_tags[tag]['sources'].add('article')
            
            # Get sample article titles for context
            sample_articles = db.query(SubstackArticle.title, SubstackArticle.subtitle).join(
                ArticleTag, ArticleTag.article_id == SubstackArticle.id
            ).filter(ArticleTag.tag == tag).limit(2).all()
            
            for title, subtitle in sample_articles:
                context = f"{title}: {subtitle[:100] if subtitle else ''}"
                unified_tags[tag]['contexts'].append(context[:150])
        
        print(f"\nUnified tag statistics:")
        print(f"- Total unique tags: {len(unified_tags)}")
        
        # Count tags by source
        twitter_only = sum(1 for t in unified_tags.values() if t['sources'] == {'twitter'})
        paper_only = sum(1 for t in unified_tags.values() if t['sources'] == {'paper'})
        article_only = sum(1 for t in unified_tags.values() if t['sources'] == {'article'})
        multi_source = sum(1 for t in unified_tags.values() if len(t['sources']) > 1)
        
        print(f"- Twitter only: {twitter_only}")
        print(f"- Paper only: {paper_only}")
        print(f"- Article only: {article_only}")
        print(f"- Multi-source tags: {multi_source} (used across content types)")
        
        # Prepare tags data for indexing
        tags_data = []
        for tag, info in unified_tags.items():
            # Combine contexts from all sources
            context = " | ".join(info['contexts'][:5]) if info['contexts'] else tag
            
            tags_data.append({
                'tag': tag,
                'context': context,
                'count': info['count']
            })
        
        # Clear existing index
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.tag_to_id = {}
        self.id_to_tag = {}
        self.tag_contexts = {}
        self.tag_counts = {}
        self.embeddings_cache = {}
        
        # Add all tags in batches
        batch_size = 20  # Small batches to avoid API limits
        for i in range(0, len(tags_data), batch_size):
            batch = tags_data[i:i + batch_size]
            self.add_tags_batch(batch)
            print(f"Processed {min(i + batch_size, len(tags_data))}/{len(tags_data)} tags...")
        
        # Save to disk
        self.save()
        
        print(f"✅ Built vector store with {len(self.tag_to_id)} unique tags")
    
    def get_tag_info(self, tag: str) -> Dict[str, Any]:
        """Get information about a tag"""
        if tag not in self.tag_to_id:
            return None
        
        return {
            'tag': tag,
            'count': self.tag_counts.get(tag, 0),
            'context': self.tag_contexts.get(tag, tag),
            'id': self.tag_to_id[tag]
        }
    
    def update_tag_incrementally(self, tag: str, content_type: str, context: str = None):
        """
        Update vector store when a new tag is added
        
        Args:
            tag: The tag string
            content_type: 'twitter', 'paper', or 'article'
            context: Optional context text (tweet text, paper title, article title)
        """
        try:
            # If tag already exists, just update count and context
            if tag in self.tag_to_id:
                self.tag_counts[tag] = self.tag_counts.get(tag, 0) + 1
                
                # Append new context if provided
                if context:
                    existing_context = self.tag_contexts.get(tag, tag)
                    # Limit context length to prevent it from growing too large
                    if len(existing_context) < 1000:
                        clean_context = context.replace('\n', ' ').strip()[:100]
                        self.tag_contexts[tag] = f"{existing_context} | {clean_context}"
            else:
                # New tag - add to vector store
                clean_context = context.replace('\n', ' ').strip()[:200] if context else tag
                self.add_tag(tag, clean_context, count=1)
            
            # Save to disk periodically (every 10 new tags)
            if len(self.tag_to_id) % 10 == 0:
                self.save()
            
            return True
            
        except Exception as e:
            print(f"Error updating vector store for tag '{tag}': {e}")
            return False

# Singleton instance
_vector_store = None

def get_vector_store() -> TagVectorStore:
    """Get or create vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = TagVectorStore()
    return _vector_store