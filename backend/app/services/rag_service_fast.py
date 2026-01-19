"""
Fast RAG service with proper indexing and progress feedback
"""
import os
import time
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import threading

import faiss

from app.services.llm_service import LLMService
from app.services.rag_helpers import (
    # Embedding functions
    get_embedding_dimension,
    get_embedding_with_cache,
    get_embeddings_batch,
    # Index management
    load_faiss_index,
    save_faiss_index,
    load_pickle_file,
    save_pickle_file,
    load_index_info,
    save_index_info,
    # Document processing
    process_tweet_for_index,
    process_article_for_index,
    process_snippet_for_index,
    process_paper_for_index,
    # Text utilities
    chunk_text,
    # Search utilities
    format_search_result,
    build_rag_context,
    generate_fallback_answer,
    # Migration helpers
    migrate_metadata_if_needed,
    migrate_doc_map_if_needed,
)


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

    def __new__(cls, db=None):
        """Singleton pattern to ensure single index instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db=None):
        """Initialize fast RAG service"""
        # Skip if already initialized
        if hasattr(self, '_initialized'):
            if db:
                self.db = db
            return

        self.db = db
        self.llm_service = LLMService()
        self.status = IndexStatus()

        # Initialize embedding provider
        self._init_embedding_provider()

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

    def _init_embedding_provider(self):
        """Initialize Google Gemini or OpenAI for embeddings"""
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        if not self.google_api_key:
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
            if not self.openai_api_key:
                raise ValueError("Neither GOOGLE_API_KEY nor OPENAI_API_KEY found")

            from openai import OpenAI
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            self.use_gemini_embeddings = False
        else:
            import google.generativeai as genai
            genai.configure(api_key=self.google_api_key)
            self.openai_client = None
            self.use_gemini_embeddings = True
            print("Using Gemini embeddings (text-embedding-004)")

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
            if not all(os.path.exists(p) for p in [
                self.index_path, self.metadata_path,
                self.doc_map_path, self.index_info_path
            ]):
                self._update_status(
                    is_ready=False,
                    current_step="Index not found, rebuild required"
                )
                return False

            self._update_status(current_step="Loading existing index...")

            # Load FAISS index
            self.index = load_faiss_index(self.index_path)
            if self.index is None:
                raise Exception("Failed to load FAISS index")

            # Load metadata with migration
            loaded_metadata = load_pickle_file(self.metadata_path, {})
            self.metadata, metadata_migrated = migrate_metadata_if_needed(loaded_metadata)
            if metadata_migrated:
                save_pickle_file(self.metadata, self.metadata_path)

            # Load doc_map with migration
            loaded_doc_map = load_pickle_file(self.doc_map_path, {})
            self.doc_map, doc_map_migrated = migrate_doc_map_if_needed(loaded_doc_map)
            if doc_map_migrated:
                save_pickle_file(self.doc_map, self.doc_map_path)

            # Load index info
            info = load_index_info(self.index_info_path)

            # Load embeddings cache
            self.embeddings_cache = load_pickle_file(self.embeddings_cache_path, {})

            self._update_status(
                is_ready=True,
                total_documents=self.index.ntotal,
                indexed_documents=self.index.ntotal,
                last_updated=datetime.fromisoformat(info['last_updated']) if 'last_updated' in info else None,
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

            save_faiss_index(self.index, self.index_path)
            save_pickle_file(self.metadata, self.metadata_path)
            save_pickle_file(self.doc_map, self.doc_map_path)
            save_pickle_file(self.embeddings_cache, self.embeddings_cache_path)

            info = {
                'last_updated': datetime.now().isoformat(),
                'total_documents': self.index.ntotal,
                'embedding_model': 'text-embedding-ada-002'
            }
            save_index_info(info, self.index_info_path)

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

        return False

    def build_index_async(self):
        """Build index in background"""
        if self.status.is_building:
            return {"status": "already_building", "progress": self.status.progress_percent}

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
            processed = 0

            # Get counts from MongoDB
            tweet_count = self.db.tweets.count_documents({})
            article_count = self.db.articles.count_documents({})
            snippet_count = self.db.article_snippets.count_documents({}) if 'article_snippets' in self.db.list_collection_names() else 0
            paper_count = self.db.papers.count_documents({'processed': True})
            total = tweet_count + article_count + snippet_count + paper_count

            self._update_status(
                total_documents=total,
                current_step=f"Processing {total} documents..."
            )

            # Process tweets
            self._update_status(current_step=f"Processing {tweet_count} tweets...")
            for tweet in self.db.tweets.find():
                # Get tags for tweet
                tag_instances = list(self.db.tag_instances.find({
                    'content_type': 'tweet',
                    'content_id': str(tweet['_id'])
                }))
                tag_ids = [ti.get('concept_id') for ti in tag_instances if ti.get('concept_id')]
                tags = []
                for tag_id in tag_ids:
                    concept = self.db.tag_concepts_v2.find_one({'_id': tag_id})
                    if concept:
                        tags.append(concept.get('name', ''))

                doc = process_tweet_for_index(
                    tweet_id=str(tweet['_id']),
                    text=tweet.get('text', ''),
                    author_username=tweet.get('author_username', ''),
                    created_at=tweet.get('created_at'),
                    tags=tags
                )
                documents.append(doc)

                processed += 1
                if processed % 100 == 0:
                    self._update_status(
                        indexed_documents=processed,
                        progress_percent=int((processed / total) * 100)
                    )

            # Process articles
            self._update_status(current_step=f"Processing {article_count} articles...")
            for article in self.db.articles.find():
                content = article.get('content_markdown') or article.get('preview') or ""
                author_name = 'Unknown'
                if article.get('author_id'):
                    author = self.db.substack_authors.find_one({'_id': article['author_id']})
                    if author:
                        author_name = author.get('name', 'Unknown')

                article_docs = process_article_for_index(
                    article_id=str(article['_id']),
                    title=article.get('title', ''),
                    content=content,
                    author_name=author_name,
                    published_at=article.get('published_at'),
                    url=article.get('url', '')
                )
                documents.extend(article_docs)

                processed += 1
                if processed % 10 == 0:
                    self._update_status(
                        indexed_documents=processed,
                        progress_percent=int((processed / total) * 100)
                    )

            # Process snippets
            if snippet_count > 0:
                self._update_status(current_step=f"Processing {snippet_count} snippets...")
                for snippet in self.db.article_snippets.find():
                    doc = process_snippet_for_index(
                        snippet_id=str(snippet['_id']),
                        text=snippet.get('text', ''),
                        annotation=snippet.get('annotation'),
                        article_id=str(snippet.get('article_id', '')),
                        category=snippet.get('category', ''),
                        created_at=snippet.get('created_at')
                    )
                    documents.append(doc)
                    processed += 1

            # Process papers
            self._update_status(current_step=f"Processing {paper_count} papers...")
            for paper in self.db.papers.find({'processed': True}):
                # Get tags for paper
                tag_instances = list(self.db.tag_instances.find({
                    'content_type': 'paper',
                    'content_id': str(paper['_id'])
                }))
                tag_ids = [ti.get('concept_id') for ti in tag_instances if ti.get('concept_id')]
                tags = []
                for tag_id in tag_ids:
                    concept = self.db.tag_concepts_v2.find_one({'_id': tag_id})
                    if concept:
                        tags.append(concept.get('name', ''))

                doc = process_paper_for_index(
                    paper_id=str(paper['_id']),
                    title=paper.get('title'),
                    abstract=paper.get('abstract'),
                    content=paper.get('content'),
                    authors=paper.get('authors', ''),
                    conference=paper.get('conference'),
                    journal=paper.get('journal'),
                    publication_date=paper.get('publication_date'),
                    arxiv_id=paper.get('arxiv_id'),
                    doi=paper.get('doi'),
                    page_count=paper.get('page_count'),
                    tags=tags
                )
                if doc:
                    documents.append(doc)

                processed += 1
                if processed % 10 == 0:
                    self._update_status(
                        indexed_documents=processed,
                        progress_percent=int((processed / total) * 80)
                    )

            # Create embeddings
            self._update_status(
                current_step="Creating embeddings (this may take a while)...",
                progress_percent=80
            )

            contents = [doc['content'] for doc in documents]
            embeddings = get_embeddings_batch(
                texts=contents,
                use_gemini=self.use_gemini_embeddings,
                progress_callback=lambda msg, pct: self._update_status(current_step=msg, progress_percent=pct),
                openai_client=self.openai_client,
                cache=self.embeddings_cache
            )

            # Build FAISS index
            self._update_status(
                current_step="Building FAISS index...",
                progress_percent=90
            )

            dimension = get_embedding_dimension(self.use_gemini_embeddings)
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

    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding with caching"""
        return get_embedding_with_cache(
            text=text,
            cache=self.embeddings_cache,
            use_gemini=self.use_gemini_embeddings,
            openai_client=self.openai_client
        )

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

            doc_id = self.doc_map.get(idx)

            # Handle legacy Document objects
            if hasattr(doc_id, 'id'):
                doc_id = doc_id.id
            elif not doc_id or not isinstance(doc_id, str):
                print(f"Warning: Invalid doc_id at index {idx}: {doc_id}")
                continue

            doc = self.metadata.get(doc_id)
            if not doc:
                print(f"Warning: No metadata for doc_id: {doc_id}")
                continue

            result = format_search_result(doc, dist, i + 1)
            results.append(result)

        return results

    async def search_with_answer(self, query: str, k: int = 10) -> Dict[str, Any]:
        """Search and generate an answer"""
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

        # Build context for LLM
        max_context_sources = min(k, 10)
        context = build_rag_context(search_results, max_context_sources)

        # Generate answer using configured prompts and model
        prompts_config = self.llm_service.prompts if hasattr(self.llm_service, 'prompts') else {}
        rag_config = prompts_config.get('rag_query', {})

        system_prompt = rag_config.get('system', 'You are a helpful AI assistant.')
        user_template = rag_config.get('user_template',
            'Based on the context, answer the question.\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:')

        prompt = user_template.format(context=context, question=query)

        try:
            models_config = self.llm_service.llm_config.get('models', {})
            model_config = models_config.get('rag_answer') or models_config.get('chat_general', {})
            model_name = model_config.get('model', None)
            if not model_name:
                raise ValueError("No rag_answer or chat_general model configured in llm.json")

            print(f"RAG: Using model {model_name} for answer generation")
            print(f"RAG: Prompt length: {len(prompt)} chars")
            print(f"RAG: Context sources: {max_context_sources} (from {len(search_results)} total)")

            answer = await self.llm_service.generate_completion_async(
                prompt=prompt,
                model=model_name,
                temperature=model_config.get('temperature', 0.3),
                max_tokens=model_config.get('max_tokens', 2000)
            )

            print(f"RAG: Answer generated, length: {len(answer) if answer else 0} chars")

            if not answer or answer.strip() == "":
                print("Warning: Empty answer generated, using fallback")
                answer = generate_fallback_answer(query, search_results)

            return {
                'answer': answer,
                'sources': search_results,
                'total_results': len(search_results)
            }

        except Exception as e:
            print(f"Error generating RAG answer: {e}")
            import traceback
            traceback.print_exc()

            return {
                'answer': f"I found {len(search_results)} relevant documents but encountered an error generating a summary: {str(e)}",
                'sources': search_results,
                'total_results': len(search_results),
                'error': str(e)
            }


# Singleton instance getter
def get_rag_service(db=None) -> FastRAGService:
    """Get the singleton RAG service instance"""
    return FastRAGService(db)
