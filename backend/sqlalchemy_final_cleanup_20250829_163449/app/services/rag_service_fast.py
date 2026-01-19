"""
Fast RAG service with proper indexing and progress feedback
"""
import os
import json
import pickle
import time
import asyncio
from typing import List, Dict, Optional, Tuple, Any, AsyncGenerator
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass, asdict
import hashlib
from concurrent.futures import ThreadPoolExecutor
import threading

import faiss
import openai
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import Tweet, SubstackArticle, ArticleSnippet, Tag
from app.models.papers import Paper, PaperTag
from app.services.llm_service import LLMService


@dataclass
class IndexStatus:
    """Status of the RAG index"""
    is_ready: bool = False
    is_building: bool = False
    total_documents: int = 0
    indexed_documents: int = 0
    last_updated: Optional[datetime] = None
    error: Optional[str] = None
    current_step: str = ""
    progress_percent: int = 0


class FastRAGService:
    """Fast RAG service with persistent index and progress feedback"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db: Session = None):
        """Singleton pattern to ensure single index instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db: Session = None):
        """Initialize fast RAG service"""
        # Skip if already initialized
        if hasattr(self, '_initialized'):
            if db:
                self.db = db
            return
        
        self.db = db
        self.llm_service = LLMService()
        self.status = IndexStatus()
        
        # Initialize Google Gemini for embeddings
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        if not self.google_api_key:
            # Fallback to OpenAI if Google API key not found
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
            if not self.openai_api_key:
                raise ValueError("Neither GOOGLE_API_KEY nor OPENAI_API_KEY found")
            
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            self.use_gemini_embeddings = False
        else:
            import google.generativeai as genai
            genai.configure(api_key=self.google_api_key)
            self.use_gemini_embeddings = True
            print("Using Gemini embeddings (text-embedding-004)")
        
        # Index paths
        self.index_dir = 'data/rag_index'
        self.index_path = os.path.join(self.index_dir, 'faiss.index')
        self.metadata_path = os.path.join(self.index_dir, 'metadata.pkl')
        self.doc_map_path = os.path.join(self.index_dir, 'doc_map.pkl')
        self.embeddings_cache_path = os.path.join(self.index_dir, 'embeddings_cache.pkl')
        self.index_info_path = os.path.join(self.index_dir, 'index_info.json')
        
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Initialize index components
        self.index = None
        self.doc_map = {}
        self.metadata = {}
        self.embeddings_cache = {}
        
        # Thread pool for background operations
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Load existing index
        self._load_index()
        
        # Mark as initialized
        self._initialized = True
    
    def get_status(self) -> Dict[str, Any]:
        """Get current index status"""
        return asdict(self.status)
    
    def _update_status(self, **kwargs):
        """Update index status"""
        for key, value in kwargs.items():
            if hasattr(self.status, key):
                setattr(self.status, key, value)
    
    def _load_index(self):
        """Load existing index if available"""
        try:
            if all(os.path.exists(p) for p in [
                self.index_path, self.metadata_path, 
                self.doc_map_path, self.index_info_path
            ]):
                self._update_status(current_step="Loading existing index...")
                
                # Load FAISS index
                self.index = faiss.read_index(self.index_path)
                
                # Load metadata
                with open(self.metadata_path, 'rb') as f:
                    loaded_metadata = pickle.load(f)
                    
                    # Check if metadata needs migration from Document objects to dicts
                    if loaded_metadata and isinstance(next(iter(loaded_metadata.values()), None), object):
                        # Check if it's a Document object (has 'id' attribute)
                        first_value = next(iter(loaded_metadata.values()))
                        if hasattr(first_value, 'id'):
                            print("Migrating metadata from Document objects to dicts...")
                            migrated_metadata = {}
                            for key, doc in loaded_metadata.items():
                                if hasattr(doc, '__dict__'):
                                    # Convert Document object to dict
                                    migrated_metadata[key] = {
                                        'id': doc.id,
                                        'content': doc.content,
                                        'type': doc.source_type,
                                        'metadata': doc.metadata
                                    }
                                else:
                                    migrated_metadata[key] = doc
                            self.metadata = migrated_metadata
                            
                            # Save the migrated version to avoid re-migration next time
                            print("Saving migrated metadata...")
                            with open(self.metadata_path, 'wb') as f:
                                pickle.dump(self.metadata, f)
                        else:
                            self.metadata = loaded_metadata
                    else:
                        self.metadata = loaded_metadata
                
                with open(self.doc_map_path, 'rb') as f:
                    loaded_doc_map = pickle.load(f)
                    
                    # Check if doc_map needs migration from Document objects to strings
                    needs_migration = False
                    for key, value in loaded_doc_map.items():
                        if hasattr(value, 'id'):
                            needs_migration = True
                            break
                    
                    if needs_migration:
                        print("Migrating doc_map from Document objects to string IDs...")
                        migrated_doc_map = {}
                        for key, value in loaded_doc_map.items():
                            if hasattr(value, 'id'):
                                migrated_doc_map[key] = value.id
                            else:
                                migrated_doc_map[key] = value
                        self.doc_map = migrated_doc_map
                        
                        # Save the migrated version to avoid re-migration next time
                        print("Saving migrated doc_map...")
                        with open(self.doc_map_path, 'wb') as f:
                            pickle.dump(self.doc_map, f)
                    else:
                        self.doc_map = loaded_doc_map
                
                # Load index info
                with open(self.index_info_path, 'r') as f:
                    info = json.load(f)
                
                # Load embeddings cache
                if os.path.exists(self.embeddings_cache_path):
                    with open(self.embeddings_cache_path, 'rb') as f:
                        self.embeddings_cache = pickle.load(f)
                
                self._update_status(
                    is_ready=True,
                    total_documents=self.index.ntotal,
                    indexed_documents=self.index.ntotal,
                    last_updated=datetime.fromisoformat(info['last_updated']),
                    current_step=f"Index ready with {self.index.ntotal} documents",
                    progress_percent=100
                )
                
                print(f"✅ Loaded RAG index with {self.index.ntotal} documents")
                return True
                
        except Exception as e:
            print(f"Could not load index: {e}")
            self._update_status(
                is_ready=False,
                current_step="Index not found, rebuild required",
                error=str(e)
            )
        
        return False
    
    def _save_index(self):
        """Save index to disk"""
        try:
            self._update_status(current_step="Saving index to disk...")
            
            # Save FAISS index
            faiss.write_index(self.index, self.index_path)
            
            # Save metadata
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            with open(self.doc_map_path, 'wb') as f:
                pickle.dump(self.doc_map, f)
            
            # Save embeddings cache
            with open(self.embeddings_cache_path, 'wb') as f:
                pickle.dump(self.embeddings_cache, f)
            
            # Save index info
            info = {
                'last_updated': datetime.now().isoformat(),
                'total_documents': self.index.ntotal,
                'embedding_model': 'text-embedding-ada-002'
            }
            with open(self.index_info_path, 'w') as f:
                json.dump(info, f)
            
            print(f"✅ Saved index with {self.index.ntotal} documents")
            
        except Exception as e:
            print(f"Error saving index: {e}")
            self._update_status(error=f"Failed to save index: {e}")
    
    def needs_rebuild(self) -> bool:
        """Check if index needs rebuilding"""
        if not self.status.is_ready:
            return True
        
        # Check if index is stale (older than 24 hours)
        if self.status.last_updated:
            age = datetime.now() - self.status.last_updated
            if age > timedelta(hours=24):
                return True
        
        # Check document count mismatch
        if self.db:
            tweet_count = self.db.query(Tweet).count()
            article_count = self.db.query(SubstackArticle).count()
            expected_min = tweet_count + article_count
            
            if self.status.total_documents < expected_min * 0.9:  # 90% threshold
                return True
        
        return False
    
    def build_index_async(self):
        """Build index in background"""
        if self.status.is_building:
            return {"status": "already_building", "progress": self.status.progress_percent}
        
        # Start background build
        future = self.executor.submit(self._build_index_internal)
        return {"status": "started", "message": "Index building started in background"}
    
    def _build_index_internal(self):
        """Internal method to build index with progress updates"""
        try:
            self._update_status(
                is_building=True,
                is_ready=False,
                error=None,
                current_step="Starting index build...",
                progress_percent=0
            )
            
            documents = []
            
            # Count total documents
            tweet_count = self.db.query(Tweet).count()
            article_count = self.db.query(SubstackArticle).count()
            snippet_count = self.db.query(ArticleSnippet).count()
            paper_count = self.db.query(Paper).count()
            total = tweet_count + article_count + snippet_count + paper_count
            
            self._update_status(
                total_documents=total,
                current_step=f"Processing {total} documents..."
            )
            
            processed = 0
            
            # Process tweets
            self._update_status(current_step=f"Processing {tweet_count} tweets...")
            tweets = self.db.query(Tweet).all()
            
            for tweet in tweets:
                tags = self.db.query(Tag).filter(Tag.tweet_id == tweet.id).all()
                tag_list = [tag.tag for tag in tags]
                
                doc_id = f"tweet_{tweet.id}"
                documents.append({
                    'id': doc_id,
                    'content': tweet.text,
                    'type': 'tweet',
                    'metadata': {
                        'author': tweet.author_username,
                        'created_at': tweet.created_at,
                        'tags': tag_list,
                        'url': f"https://twitter.com/{tweet.author_username}/status/{tweet.id}"
                    }
                })
                
                processed += 1
                if processed % 100 == 0:
                    self._update_status(
                        indexed_documents=processed,
                        progress_percent=int((processed / total) * 100)
                    )
            
            # Process articles
            self._update_status(current_step=f"Processing {article_count} articles...")
            articles = self.db.query(SubstackArticle).all()
            
            for article in articles:
                # Main article
                doc_id = f"article_{article.id}"
                content = article.content_markdown or article.preview or ""
                
                # Chunk long articles
                if len(content) > 2000:
                    chunks = self._chunk_text(content, 1500, 200)
                    for i, chunk in enumerate(chunks):
                        chunk_id = f"article_{article.id}_chunk_{i}"
                        documents.append({
                            'id': chunk_id,
                            'content': chunk,
                            'type': 'article',
                            'metadata': {
                                'title': article.title,
                                'author': article.author.name if article.author else 'Unknown',
                                'published_at': article.published_at.isoformat() if article.published_at else None,
                                'url': article.url,
                                'chunk': i
                            }
                        })
                else:
                    documents.append({
                        'id': doc_id,
                        'content': content,
                        'type': 'article',
                        'metadata': {
                            'title': article.title,
                            'author': article.author.name if article.author else 'Unknown',
                            'published_at': article.published_at.isoformat() if article.published_at else None,
                            'url': article.url
                        }
                    })
                
                processed += 1
                if processed % 10 == 0:
                    self._update_status(
                        indexed_documents=processed,
                        progress_percent=int((processed / total) * 100)
                    )
            
            # Process snippets
            self._update_status(current_step=f"Processing {snippet_count} snippets...")
            snippets = self.db.query(ArticleSnippet).all()
            
            for snippet in snippets:
                doc_id = f"snippet_{snippet.id}"
                documents.append({
                    'id': doc_id,
                    'content': f"{snippet.text}\n\nNote: {snippet.annotation}" if snippet.annotation else snippet.text,
                    'type': 'snippet',
                    'metadata': {
                        'article_id': snippet.article_id,
                        'category': snippet.category,
                        'created_at': snippet.created_at.isoformat() if snippet.created_at else None
                    }
                })
                
                processed += 1
            
            # Process papers
            self._update_status(current_step=f"Processing {paper_count} papers...")
            papers = self.db.query(Paper).filter(Paper.processed == True).all()
            
            for paper in papers:
                # Get paper tags
                tags = self.db.query(PaperTag).filter(PaperTag.paper_id == paper.id).all()
                tag_list = [tag.tag for tag in tags]
                
                # Combine title, abstract, and content for search
                paper_content = []
                if paper.title:
                    paper_content.append(f"Title: {paper.title}")
                if paper.abstract:
                    paper_content.append(f"Abstract: {paper.abstract}")
                if paper.content:
                    # Use first 3000 characters of content for efficiency
                    paper_content.append(f"Content: {paper.content[:3000]}")
                
                content = "\n\n".join(paper_content)
                
                if content:
                    doc_id = f"paper_{paper.id}"
                    documents.append({
                        'id': doc_id,
                        'content': content,
                        'type': 'paper',
                        'metadata': {
                            'title': paper.title,
                            'authors': paper.authors,
                            'conference': paper.conference,
                            'journal': paper.journal,
                            'publication_date': paper.publication_date.isoformat() if paper.publication_date else None,
                            'arxiv_id': paper.arxiv_id,
                            'doi': paper.doi,
                            'tags': tag_list,
                            'page_count': paper.page_count
                        }
                    })
                    
                    processed += 1
                    if processed % 10 == 0:
                        self._update_status(
                            indexed_documents=processed,
                            progress_percent=int((processed / total) * 80)  # Leave 20% for embeddings/index
                        )
            
            # Create embeddings
            self._update_status(
                current_step="Creating embeddings (this may take a while)...",
                progress_percent=80
            )
            
            contents = [doc['content'] for doc in documents]
            embeddings = self._get_embeddings_batch(contents)
            
            # Build FAISS index
            self._update_status(
                current_step="Building FAISS index...",
                progress_percent=90
            )
            
            # Dimension depends on embedding model
            dimension = 768 if self.use_gemini_embeddings else 1536
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings)
            
            # Store metadata
            self.doc_map = {i: doc['id'] for i, doc in enumerate(documents)}
            self.metadata = {doc['id']: doc for doc in documents}
            
            # Save index
            self._update_status(
                current_step="Saving index...",
                progress_percent=95
            )
            self._save_index()
            
            # Update status
            self._update_status(
                is_ready=True,
                is_building=False,
                total_documents=len(documents),
                indexed_documents=len(documents),
                last_updated=datetime.now(),
                current_step=f"Index ready with {len(documents)} documents",
                progress_percent=100
            )
            
            print(f"✅ Built index with {len(documents)} documents")
            
        except Exception as e:
            print(f"Error building index: {e}")
            self._update_status(
                is_building=False,
                is_ready=False,
                error=str(e),
                current_step="Index build failed",
                progress_percent=0
            )
    
    def _chunk_text(self, text: str, chunk_size: int = 1500, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('. ')
                if last_period > chunk_size - 300:
                    end = start + last_period + 1
                    chunk = text[start:end]
            
            chunks.append(chunk)
            start = end - overlap
        
        return chunks
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding with caching (Gemini or OpenAI)"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        if text_hash in self.embeddings_cache:
            return np.array(self.embeddings_cache[text_hash])
        
        try:
            if self.use_gemini_embeddings:
                # Use Gemini embeddings
                import google.generativeai as genai
                # Gemini embedding dimension is 768
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text[:8000],
                    task_type="retrieval_document",
                    title="Document"
                )
                embedding = np.array(result['embedding'])
            else:
                # Fallback to OpenAI
                response = self.openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=text[:8000]
                )
                embedding = np.array(response.data[0].embedding)
            
            self.embeddings_cache[text_hash] = embedding.tolist()
            return embedding
            
        except Exception as e:
            print(f"Embedding error: {e}")
            # Return zeros with correct dimension
            return np.zeros(768 if self.use_gemini_embeddings else 1536)
    
    def _get_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for multiple texts efficiently"""
        embeddings = []
        
        if self.use_gemini_embeddings:
            # Gemini batch embedding
            import google.generativeai as genai
            batch_size = 100  # Gemini can handle large batches
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                
                try:
                    # Gemini supports batch embedding
                    batch_results = genai.embed_content(
                        model="models/text-embedding-004",
                        content=batch,
                        task_type="retrieval_document"
                    )
                    
                    # Extract embeddings from results
                    for embedding in batch_results['embedding']:
                        embeddings.append(np.array(embedding))
                    
                except Exception as e:
                    print(f"Batch embedding failed, falling back to individual: {e}")
                    # Fallback to individual embeddings
                    for text in batch:
                        embedding = self._get_embedding(text)
                        embeddings.append(embedding)
                
                # Update progress
                progress = 80 + int((i / len(texts)) * 10)
                self._update_status(
                    current_step=f"Creating Gemini embeddings... ({min(i + batch_size, len(texts))}/{len(texts)})",
                    progress_percent=progress
                )
                
                # Small delay to respect rate limits
                if i + batch_size < len(texts):
                    import time
                    time.sleep(0.1)
        else:
            # OpenAI batch processing
            batch_size = 100
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                
                batch_embeddings = []
                for text in batch:
                    embedding = self._get_embedding(text)
                    batch_embeddings.append(embedding)
                
                embeddings.extend(batch_embeddings)
                
                # Update progress
                progress = 80 + int((i / len(texts)) * 10)
                self._update_status(
                    current_step=f"Creating OpenAI embeddings... ({min(i + batch_size, len(texts))}/{len(texts)})",
                    progress_percent=progress
                )
                
                if i + batch_size < len(texts):
                    import time
                    time.sleep(0.1)
        
        return np.array(embeddings)
    
    def search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Search the index"""
        if not self.status.is_ready:
            if self.status.is_building:
                return [{
                    'error': 'Index is currently building',
                    'progress': self.status.progress_percent,
                    'step': self.status.current_step
                }]
            else:
                return [{
                    'error': 'Index not ready. Please build the index first.'
                }]
        
        # Get query embedding
        query_embedding = self._get_embedding(query)
        query_vector = query_embedding.reshape(1, -1)
        
        # Search
        distances, indices = self.index.search(query_vector, k)
        
        # Format results
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:
                continue
            
            # Get document ID from map
            doc_id = self.doc_map.get(idx)
            
            # Handle legacy Document objects from old index
            if hasattr(doc_id, 'id'):
                # It's a Document object from the old rag_service.py
                doc_id = doc_id.id
            elif not doc_id or not isinstance(doc_id, str):
                print(f"Warning: Invalid doc_id at index {idx}: {doc_id}")
                continue
                
            # Get document from metadata
            doc = self.metadata.get(doc_id)
            if not doc:
                print(f"Warning: No metadata for doc_id: {doc_id}")
                continue
            
            # Handle both new dict format and legacy Document object format
            if isinstance(doc, dict):
                content = doc.get('content', '')
                doc_type = doc.get('type', 'unknown')
                metadata = doc.get('metadata', {})
            else:
                # Legacy Document object
                content = getattr(doc, 'content', '')
                doc_type = getattr(doc, 'source_type', 'unknown')
                metadata = getattr(doc, 'metadata', {})
            
            results.append({
                'content': content[:500] if content else '',
                'type': doc_type,
                'score': float(1 / (1 + dist)),  # Convert distance to similarity
                'metadata': metadata,
                'rank': i + 1
            })
        
        return results
    
    async def search_with_answer(self, query: str, k: int = 10) -> Dict[str, Any]:
        """Search and generate an answer"""
        # First check if index is ready
        if not self.status.is_ready:
            return {
                'error': 'Index not ready',
                'status': self.get_status()
            }
        
        # Search for relevant documents
        search_results = self.search(query, k)
        
        if not search_results:
            return {
                'answer': "No relevant information found.",
                'sources': []
            }
        
        # Prepare context for LLM
        context_parts = []
        # Use all k results for context (or max of 10 to avoid token limits)
        max_context_sources = min(k, 10)
        for result in search_results[:max_context_sources]:
            context_parts.append(f"[{result['type']}]: {result['content']}")
        
        context = "\n\n".join(context_parts)
        
        # Generate answer using configured prompts and model
        # Load prompts from configuration
        prompts_config = self.llm_service.prompts if hasattr(self.llm_service, 'prompts') else {}
        rag_config = prompts_config.get('rag_query', {})
        
        # Get system and user template from config
        system_prompt = rag_config.get('system', 'You are a helpful AI assistant.')
        user_template = rag_config.get('user_template', 
            'Based on the context, answer the question.\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:')
        
        # Format the prompt
        prompt = user_template.format(context=context, question=query)
        
        # Get model from config - prioritize rag_answer, fallback to chat_general
        try:
            models_config = self.llm_service.llm_config.get('models', {})
            model_config = models_config.get('rag_answer') or models_config.get('chat_general', {})
            model_name = model_config.get('model', None)
            if not model_name:
                raise ValueError("No rag_answer or chat_general model configured in llm.json")
            
            print(f"RAG: Using model {model_name} for answer generation")
            print(f"RAG: Prompt length: {len(prompt)} chars")
            print(f"RAG: Context sources: {min(k, 10)} (from {len(search_results)} total)")
            
            answer = await self.llm_service.generate_completion_async(
                prompt=prompt,
                model=model_name,
                temperature=model_config.get('temperature', 0.3),
                max_tokens=model_config.get('max_tokens', 2000)
            )
            
            print(f"RAG: Answer generated, length: {len(answer) if answer else 0} chars")
            
            if not answer or answer.strip() == "":
                print("Warning: Empty answer generated, using fallback")
                answer = f"Based on the search results, I found {len(search_results)} relevant documents about {query}. The most relevant sources discuss:\n\n"
                for i, result in enumerate(search_results[:3], 1):
                    snippet = result['content'][:200]
                    answer += f"{i}. {snippet}...\n\n"
                answer += "Please review the source documents for more detailed information."
            
            return {
                'answer': answer,
                'sources': search_results,  # Return all k sources
                'total_results': len(search_results)
            }
            
        except Exception as e:
            print(f"Error generating RAG answer: {e}")
            import traceback
            traceback.print_exc()
            
            # Return search results without answer on error
            return {
                'answer': f"I found {len(search_results)} relevant documents but encountered an error generating a summary: {str(e)}",
                'sources': search_results,  # Return all k sources even on error
                'total_results': len(search_results),
                'error': str(e)
            }


# Singleton instance getter
def get_rag_service(db: Session = None) -> FastRAGService:
    """Get the singleton RAG service instance"""
    return FastRAGService(db)