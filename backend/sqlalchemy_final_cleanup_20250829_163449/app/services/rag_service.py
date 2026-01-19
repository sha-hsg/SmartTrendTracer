"""
RAG (Retrieval-Augmented Generation) service for querying tweets and articles
"""
import os
import json
import pickle
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import numpy as np
from dataclasses import dataclass
import hashlib
from dotenv import load_dotenv

import faiss
import openai
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import Tweet, SubstackArticle, ArticleSnippet, Tag
from app.models.papers import Paper, PaperTag, PaperSnippet
from app.services.llm_service import LLMService

# Load environment variables
load_dotenv()


@dataclass
class Document:
    """Represents a document chunk for RAG"""
    id: str
    content: str
    source_type: str  # 'tweet', 'article', 'snippet'
    source_id: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None


@dataclass
class SearchResult:
    """Represents a search result with source information"""
    content: str
    source_type: str
    source_id: str
    score: float
    metadata: Dict[str, Any]
    highlight: Optional[str] = None


class RAGService:
    """Service for RAG-based question answering"""
    
    def __init__(self, db: Session):
        """Initialize RAG service with database session"""
        self.db = db
        self.llm_service = LLMService()
        
        # Load prompts configuration
        prompts_config_path = 'prompts_config.json'
        if os.path.exists(prompts_config_path):
            with open(prompts_config_path, 'r') as f:
                self.prompts_config = json.load(f)
        else:
            self.prompts_config = {}
        
        # Initialize OpenAI client for embeddings
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        from openai import OpenAI
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # Paths for persisted indices
        self.index_dir = 'data/rag_index'
        self.index_path = os.path.join(self.index_dir, 'faiss.index')
        self.metadata_path = os.path.join(self.index_dir, 'metadata.pkl')
        self.doc_map_path = os.path.join(self.index_dir, 'doc_map.pkl')
        self.embeddings_cache_path = os.path.join(self.index_dir, 'embeddings_cache.pkl')
        
        # Ensure index directory exists
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Load or create index
        self.index = None
        self.doc_map = {}
        self.metadata = {}
        self.embeddings_cache = {}
        self._load_embeddings_cache()
        self._load_or_create_index()
    
    def _load_embeddings_cache(self):
        """Load cached embeddings"""
        if os.path.exists(self.embeddings_cache_path):
            try:
                with open(self.embeddings_cache_path, 'rb') as f:
                    self.embeddings_cache = pickle.load(f)
                print(f"Loaded {len(self.embeddings_cache)} cached embeddings")
            except:
                self.embeddings_cache = {}
    
    def _save_embeddings_cache(self):
        """Save embeddings cache"""
        try:
            with open(self.embeddings_cache_path, 'wb') as f:
                pickle.dump(self.embeddings_cache, f)
        except Exception as e:
            print(f"Error saving embeddings cache: {e}")
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using Gemini API with caching"""
        # Create a hash of the text for caching
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Check cache
        if text_hash in self.embeddings_cache:
            return np.array(self.embeddings_cache[text_hash])
        
        # Try Gemini first, fallback to OpenAI
        try:
            # Check if we have Google API key
            google_api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
            if google_api_key:
                # Use Gemini embeddings
                import google.generativeai as genai
                genai.configure(api_key=google_api_key)
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text[:8000],
                    task_type="retrieval_document"
                )
                embedding = np.array(result['embedding'])
            else:
                # Fallback to OpenAI
                response = self.openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=text[:8000]
                )
                embedding = np.array(response.data[0].embedding)
            
            # Cache the embedding
            self.embeddings_cache[text_hash] = embedding.tolist()
            
            return embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            # Return zero vector as fallback (768 for Gemini, 1536 for OpenAI)
            google_api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
            return np.zeros(768 if google_api_key else 1536)
    
    def _get_embeddings_batch(self, texts: List[str], batch_size: int = 20) -> np.ndarray:
        """Get embeddings for multiple texts with batching"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_embeddings = []
            
            for text in batch:
                embedding = self._get_embedding(text)
                batch_embeddings.append(embedding)
            
            embeddings.extend(batch_embeddings)
            
            # Save cache periodically
            if (i + batch_size) % 100 == 0:
                self._save_embeddings_cache()
                print(f"Processed {i + batch_size}/{len(texts)} embeddings")
        
        # Final cache save
        self._save_embeddings_cache()
        
        return np.array(embeddings)
    
    def _load_or_create_index(self):
        """Load existing index or create new one"""
        if os.path.exists(self.index_path) and os.path.exists(self.doc_map_path):
            print("Loading existing RAG index...")
            self.index = faiss.read_index(self.index_path)
            with open(self.doc_map_path, 'rb') as f:
                self.doc_map = pickle.load(f)
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            print(f"Loaded index with {self.index.ntotal} documents")
        else:
            print("Creating new RAG index...")
            self._build_index()
    
    def _build_index(self):
        """Build FAISS index from tweets and articles"""
        documents = []
        
        # Process tweets
        print("Processing tweets...")
        tweets = self.db.query(Tweet).all()
        for tweet in tweets:
            # Get tags for this tweet
            tags = self.db.query(Tag).filter(Tag.tweet_id == tweet.id).all()
            tag_list = [tag.tag for tag in tags]
            
            doc_id = f"tweet_{tweet.id}"
            doc = Document(
                id=doc_id,
                content=tweet.text,
                source_type='tweet',
                source_id=tweet.id,
                metadata={
                    'author': tweet.author_username,
                    'created_at': tweet.created_at,
                    'tags': tag_list,
                    'retweet_count': tweet.retweet_count,
                    'like_count': tweet.like_count,
                    'url': f"https://twitter.com/{tweet.author_username}/status/{tweet.id}"
                }
            )
            documents.append(doc)
        
        # Process articles
        print("Processing articles...")
        articles = self.db.query(SubstackArticle).all()
        for article in articles:
            # Split article into chunks (for long articles)
            chunks = self._chunk_article(article)
            for i, chunk in enumerate(chunks):
                doc_id = f"article_{article.id}_chunk_{i}"
                doc = Document(
                    id=doc_id,
                    content=chunk,
                    source_type='article',
                    source_id=str(article.id),
                    metadata={
                        'title': article.title,
                        'author': article.author.name if article.author else 'Unknown',
                        'published_date': article.published_at.isoformat() if article.published_at else None,
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'summary': article.summary[:200] if article.summary else None
                    }
                )
                documents.append(doc)
        
        # Process papers
        print("Processing papers...")
        papers = self.db.query(Paper).all()
        for paper in papers:
            # Get tags for this paper
            paper_tags = self.db.query(PaperTag).filter(PaperTag.paper_id == paper.id).all()
            tag_list = [tag.tag for tag in paper_tags]
            
            # Create document from paper
            paper_content = []
            if paper.title:
                paper_content.append(f"Title: {paper.title}")
            if paper.abstract:
                paper_content.append(f"Abstract: {paper.abstract}")
            if paper.content:
                # Use first part of content (to avoid token limits)
                paper_content.append(paper.content[:3000])
            
            doc_id = f"paper_{paper.id}"
            doc = Document(
                id=doc_id,
                content="\n\n".join(paper_content),
                source_type='paper',
                source_id=str(paper.id),
                metadata={
                    'title': paper.title,
                    'authors': paper.authors.split(', ') if paper.authors and isinstance(paper.authors, str) else [],
                    'tags': tag_list,
                    'conference': paper.conference,
                    'journal': paper.journal,
                    'arxiv_id': paper.arxiv_id,
                    'doi': paper.doi,
                    'publication_date': paper.publication_date.isoformat() if paper.publication_date else None,
                    'created_at': paper.created_at.isoformat() if paper.created_at else None
                }
            )
            documents.append(doc)
        
        # Process snippets
        print("Processing snippets...")
        snippets = self.db.query(ArticleSnippet).all()
        for snippet in snippets:
            doc_id = f"snippet_{snippet.id}"
            doc = Document(
                id=doc_id,
                content=snippet.text,
                source_type='snippet',
                source_id=str(snippet.id),
                metadata={
                    'article_id': snippet.article_id,
                    'annotation': snippet.annotation,
                    'created_at': snippet.created_at.isoformat() if snippet.created_at else None,
                    'tags': snippet.snippet_tags if hasattr(snippet, 'snippet_tags') else []
                }
            )
            documents.append(doc)
        
        if not documents:
            print("No documents to index")
            # Create empty index
            self.index = faiss.IndexFlatIP(1536)  # OpenAI ada-002 dimension
            return
        
        # Create embeddings
        print(f"Creating embeddings for {len(documents)} documents...")
        texts = [doc.content for doc in documents]
        embeddings = self._get_embeddings_batch(texts)
        
        # Ensure embeddings are float32 and C-contiguous
        embeddings = np.array(embeddings, dtype=np.float32)
        if not embeddings.flags['C_CONTIGUOUS']:
            embeddings = np.ascontiguousarray(embeddings)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create FAISS index
        # Check which embedding model we're using
        google_api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        dimension = 768 if google_api_key else 1536  # Gemini: 768, OpenAI: 1536
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        self.index.add(embeddings)
        
        # Store document mappings
        for i, doc in enumerate(documents):
            self.doc_map[i] = doc
            self.metadata[doc.id] = doc.metadata
        
        # Save index
        print("Saving index...")
        faiss.write_index(self.index, self.index_path)
        with open(self.doc_map_path, 'wb') as f:
            pickle.dump(self.doc_map, f)
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
        
        print(f"Index built with {len(documents)} documents")
    
    def _chunk_article(self, article: SubstackArticle, chunk_size: int = 500) -> List[str]:
        """Split article into chunks for processing"""
        # SubstackArticle has content_markdown field
        content = article.content_markdown or article.preview or ""
        
        # Simple chunking by paragraphs
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para.split())
            if current_size + para_size > chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        # If no chunks or content too small, return as single chunk
        if not chunks:
            chunks = [content]
        
        return chunks
    
    def search(self, query: str, k: int = 10) -> List[SearchResult]:
        """Search for relevant documents using vector similarity"""
        if self.index is None or self.index.ntotal == 0:
            return []
        
        # Get query embedding
        query_embedding = self._get_embedding(query).reshape(1, -1)
        # Ensure embedding is float32 and C-contiguous
        query_embedding = np.array(query_embedding, dtype=np.float32)
        if not query_embedding.flags['C_CONTIGUOUS']:
            query_embedding = np.ascontiguousarray(query_embedding)
        faiss.normalize_L2(query_embedding)
        
        # Search in FAISS
        scores, indices = self.index.search(query_embedding, min(k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for padding
                continue
                
            doc_id = self.doc_map.get(idx)
            if doc_id:
                # Get metadata for this document
                doc_metadata = self.metadata.get(doc_id, {})
                if doc_metadata:
                    result = SearchResult(
                        content=doc_metadata.get('content', ''),
                        source_type=doc_metadata.get('type', 'unknown'),
                        source_id=doc_id.split('_', 1)[1] if '_' in doc_id else doc_id,
                        score=float(score),
                        metadata=doc_metadata.get('metadata', {})
                    )
                    results.append(result)
        
        return results
    
    def answer_question(self, question: str, k: int = 5) -> Dict[str, Any]:
        """Answer a question using RAG"""
        # Search for relevant documents
        search_results = self.search(question, k=k)
        
        if not search_results:
            return {
                'answer': "I couldn't find relevant information to answer your question.",
                'sources': [],
                'model_used': None
            }
        
        # Prepare context from search results
        context_parts = []
        for i, result in enumerate(search_results, 1):
            source_type = result.source_type
            if source_type == 'tweet':
                author = result.metadata.get('author', 'Unknown')
                context_parts.append(f"[Tweet {i} by @{author}]: {result.content}")
            elif source_type == 'article':
                title = result.metadata.get('title', 'Untitled')
                author = result.metadata.get('author', 'Unknown')
                context_parts.append(f"[Article {i} - \"{title}\" by {author}]: {result.content}")
            elif source_type == 'paper':
                title = result.metadata.get('title', 'Untitled')
                authors = result.metadata.get('authors', [])
                author_str = ', '.join(authors[:3]) if authors else 'Unknown'
                if len(authors) > 3:
                    author_str += f' et al.'
                context_parts.append(f"[Paper {i} - \"{title}\" by {author_str}]: {result.content}")
            elif source_type == 'snippet':
                context_parts.append(f"[Snippet {i}]: {result.content}")
        
        context = "\n\n".join(context_parts)
        
        # Get prompts from configuration
        rag_config = self.prompts_config.get('rag_query', {})
        
        if not rag_config:
            # Use default prompt if not configured
            rag_config = {
                'user_template': 'Based on the following context, provide a detailed answer to the question.\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:'
            }
        
        # Format prompt from template
        user_template = rag_config.get('user_template', 
            'Based on the following context, provide a detailed answer to the question.\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:')
        
        prompt = user_template.format(context=context, question=question)
        
        # Get answer from LLM
        try:
            # Use the rag_answer model config, fallback to chat_general
            models = self.llm_service.llm_config.get('models', {})
            model_config = models.get('rag_answer') or models.get('chat_general') or models.get('summarization')
            if not model_config:
                raise ValueError("No suitable model configured for RAG")
            answer = self.llm_service._call_llm(prompt, model_config)
            model_used = model_config.get('model', 'unknown')
        except Exception as e:
            print(f"Error getting LLM answer: {e}")
            answer = "I found relevant information but couldn't generate a complete answer. Please check the sources below."
            model_used = None
        
        # Format sources for display
        sources = []
        for result in search_results:
            source_info = {
                'type': result.source_type,
                'id': result.source_id,
                'score': result.score,
                'content_preview': result.content[:200] + '...' if len(result.content) > 200 else result.content,
                'metadata': result.metadata
            }
            
            # Add navigation info
            if result.source_type == 'tweet':
                source_info['navigate_to'] = f"/tweet/{result.source_id}"
                source_info['display_title'] = f"@{result.metadata.get('author', 'Unknown')}"
                source_info['url'] = result.metadata.get('url')
            elif result.source_type == 'article':
                source_info['navigate_to'] = f"/substack/article/{result.source_id}"
                source_info['display_title'] = result.metadata.get('title', 'Untitled Article')
            elif result.source_type == 'snippet':
                source_info['navigate_to'] = f"/substack/article/{result.metadata.get('article_id')}"
                source_info['display_title'] = "Article Snippet"
            
            sources.append(source_info)
        
        return {
            'question': question,
            'answer': answer,
            'sources': sources,
            'model_used': model_used,
            'timestamp': datetime.now().isoformat()
        }
    
    def rebuild_index(self):
        """Rebuild the entire index from scratch"""
        print("Rebuilding RAG index...")
        
        # Clear existing index
        self.index = None
        self.doc_map = {}
        self.metadata = {}
        
        # Remove old index files
        for file in [self.index_path, self.metadata_path, self.doc_map_path]:
            if os.path.exists(file):
                os.remove(file)
        
        # Build new index
        self._build_index()
        
        return {"success": True, "message": f"Index rebuilt with {self.index.ntotal} documents"}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG index"""
        if self.index is None:
            return {"total_documents": 0, "index_exists": False}
        
        # Count by type
        type_counts = {'tweet': 0, 'article': 0, 'snippet': 0}
        for doc in self.doc_map.values():
            type_counts[doc.source_type] = type_counts.get(doc.source_type, 0) + 1
        
        return {
            "total_documents": self.index.ntotal,
            "index_exists": True,
            "documents_by_type": type_counts,
            "index_dimension": self.index.d if hasattr(self.index, 'd') else 1536,
            "index_path": self.index_path
        }