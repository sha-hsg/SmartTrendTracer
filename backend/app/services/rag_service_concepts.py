"""
RAG Service using MongoDB concepts instead of SQLite tags
This replaces the old rag_service.py for full concept integration
"""

import os
import json
import pickle
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

import faiss
import numpy as np
import google.generativeai as genai
from openai import OpenAI

from app.services.concept_only_tag_service import ConceptOnlyTagService
from app.services.llm_manager import get_llm_manager

logger = logging.getLogger(__name__)

class ConceptBasedRAGService:
    """RAG Service that uses MongoDB concepts for better semantic search"""
    
    def __init__(self, db=None):
        # MongoDB connection
        from app.database.mongodb import get_client, get_database

        self.mongo_client = get_client()
        self.db = get_database()
        self.concept_service = ConceptOnlyTagService()
        self.llm_manager = get_llm_manager()
        self.user_id = "default"  # Can be parameterized later
        
        # Initialize embedding API (Google Gemini or OpenAI)
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        if not self.google_api_key:
            # Fallback to OpenAI if Google API key not found
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
            if not self.openai_api_key:
                raise ValueError("Neither GOOGLE_API_KEY nor OPENAI_API_KEY found")
            
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            self.use_gemini_embeddings = False
        else:
            genai.configure(api_key=self.google_api_key)
            self.use_gemini_embeddings = True
            logger.info("Using Gemini embeddings for concept-based RAG")
        
        # RAG index paths
        self.index_dir = Path("data/rag_index_concepts")
        self.index_dir.mkdir(exist_ok=True, parents=True)
        
        self.index_path = self.index_dir / "faiss.index"
        self.metadata_path = self.index_dir / "metadata.pkl"
        self.doc_map_path = self.index_dir / "doc_map.pkl"
        self.embeddings_cache_path = self.index_dir / "embeddings_cache.pkl"
        
        # Load or initialize index
        self.load_index()
    
    def load_index(self):
        """Load existing index or create new one"""
        try:
            if self.index_path.exists() and self.metadata_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                with open(self.metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                with open(self.doc_map_path, 'rb') as f:
                    self.doc_map = pickle.load(f)
                logger.info(f"Loaded RAG index with {self.index.ntotal} documents")
            else:
                self.index = None
                self.metadata = []
                self.doc_map = {}
                logger.info("No existing index found, will create new one")
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            self.index = None
            self.metadata = []
            self.doc_map = {}
    
    def rebuild_index(self):
        """Rebuild the entire index with concept information"""
        logger.info("Starting RAG index rebuild with concepts...")
        
        documents = []
        metadata = []
        doc_map = {}
        doc_id = 0
        
        try:
            # Process tweets from MongoDB
            tweets = list(self.db.tweets.find())
            logger.info(f"Found {len(tweets)} tweets in MongoDB")
            for tweet in tweets:
                # Get concepts for this tweet
                concepts = self.concept_service.get_tags_for_content(
                    content_type='tweet',
                    content_id=str(tweet['_id'])
                )
                concept_names = [c['display_name'] for c in concepts]
                
                # Build document text with concepts
                doc_text = f"Tweet by @{tweet.get('author_username', '')}: {tweet.get('text', '')}"
                if concept_names:
                    doc_text += f"\nConcepts: {', '.join(concept_names)}"
                
                documents.append(doc_text)
                metadata.append({
                    'type': 'tweet',
                    'id': str(tweet['_id']),
                    'author': tweet.get('author_username', ''),
                    'created_at': tweet.get('created_at'),
                    'concepts': concept_names,
                    'concept_ids': [c['id'] for c in concepts]
                })
                doc_map[doc_id] = doc_text
                doc_id += 1
            
            logger.info(f"Processed {len(tweets)} tweets")
            
            # Process articles from MongoDB
            articles = list(self.db.articles.find())
            logger.info(f"Found {len(articles)} articles in MongoDB")
            for article in articles:
                # Get concepts for this article
                concepts = self.concept_service.get_tags_for_content(
                    content_type='article',
                    content_id=str(article['_id'])
                )
                concept_names = [c['display_name'] for c in concepts]
                
                # Build document text with concepts
                doc_text = f"Article: {article.get('title', '')}\nBy: {article.get('author_name', 'Unknown')}\n"
                content = article.get('content', '')
                doc_text += f"{content[:2000]}..." if len(content) > 2000 else content
                if concept_names:
                    doc_text += f"\nConcepts: {', '.join(concept_names)}"
                
                documents.append(doc_text)
                metadata.append({
                    'type': 'article',
                    'id': str(article['_id']),
                    'title': article.get('title', ''),
                    'author': article.get('author_name'),
                    'published_at': article.get('published_at'),
                    'concepts': concept_names,
                    'concept_ids': [c['id'] for c in concepts]
                })
                doc_map[doc_id] = doc_text
                doc_id += 1
            
            logger.info(f"Processed {len(articles)} articles")
            
            # Process papers from MongoDB
            papers = list(self.db.papers.find({'processed': True}))
            logger.info(f"Found {len(papers)} processed papers in MongoDB")
            for paper in papers:
                # Get concepts for this paper
                concepts = self.concept_service.get_tags_for_content(
                    content_type='paper',
                    content_id=str(paper['_id'])
                )
                concept_names = [c['display_name'] for c in concepts]
                
                # Build document text with concepts
                doc_text = f"Paper: {paper.get('title', '')}\n"
                
                # Add authors if available
                authors = paper.get('authors', [])
                if authors:
                    # Handle both string and list formats
                    if isinstance(authors, str):
                        doc_text += f"Authors: {authors}\n"
                    elif isinstance(authors, list):
                        doc_text += f"Authors: {', '.join(str(a) for a in authors)}\n"
                
                abstract = paper.get('abstract', '')
                if abstract:
                    doc_text += f"Abstract: {abstract}\n"
                
                # MongoDB papers have content field - use more of it for better context
                content = paper.get('content', '')
                if content and len(content) > 100:  # Only add if meaningful content exists
                    # Use first 8000 chars for papers (much more than tweets/articles)
                    content_preview = content[:8000] if len(content) > 8000 else content
                    doc_text += f"\nContent: {content_preview}\n"
                    if len(content) > 8000:
                        doc_text += "... [content truncated]"
                elif not abstract:
                    # If no content and no abstract, skip this paper
                    logger.warning(f"Paper '{paper.get('title', 'Unknown')}' has no meaningful content, skipping")
                    continue
                
                if concept_names:
                    doc_text += f"\nConcepts: {', '.join(concept_names)}"
                
                documents.append(doc_text)
                metadata.append({
                    'type': 'paper',
                    'id': str(paper['_id']),
                    'title': paper.get('title', ''),
                    'year': paper.get('year'),
                    'concepts': concept_names,
                    'concept_ids': [c['id'] for c in concepts]
                })
                doc_map[doc_id] = doc_text
                doc_id += 1
            
            logger.info(f"Processed {len(papers)} papers")
            
            # Create embeddings
            if documents:
                logger.info(f"Creating embeddings for {len(documents)} documents...")
                embeddings = self._get_embeddings_batch(documents)
                
                # Create FAISS index
                dimension = 768 if self.use_gemini_embeddings else 1536
                self.index = faiss.IndexFlatL2(dimension)
                self.index.add(embeddings.astype('float32'))
                
                # Save index and metadata
                faiss.write_index(self.index, str(self.index_path))
                
                with open(self.metadata_path, 'wb') as f:
                    pickle.dump(metadata, f)
                
                with open(self.doc_map_path, 'wb') as f:
                    pickle.dump(doc_map, f)
                
                self.metadata = metadata
                self.doc_map = doc_map
                
                # Save index info
                index_info = {
                    'status': 'ready',
                    'total_documents': len(documents),
                    'tweets': len([m for m in metadata if m['type'] == 'tweet']),
                    'articles': len([m for m in metadata if m['type'] == 'article']),
                    'papers': len([m for m in metadata if m['type'] == 'paper']),
                    'last_updated': datetime.utcnow().isoformat(),
                    'embedding_model': 'text-embedding-004' if self.use_gemini_embeddings else 'text-embedding-ada-002',
                    'uses_concepts': True
                }
                
                with open(self.index_dir / 'index_info.json', 'w') as f:
                    json.dump(index_info, f, indent=2)
                
                logger.info(f"Index rebuilt successfully with {len(documents)} documents")
                return index_info
            else:
                logger.warning("No documents to index")
                return {'total_documents': 0}
            
        except Exception as e:
            logger.error(f"Error rebuilding index: {e}", exc_info=True)
            raise
    
    def search(self, query: str, k: int = 10, concept_filter: Optional[List[str]] = None, 
               content_types: Optional[List[str]] = None) -> List[Dict]:
        """
        Search the index with optional concept and content type filtering
        
        Args:
            query: Search query
            k: Number of results to return
            concept_filter: Optional list of concept IDs to filter by
            content_types: Optional list of content types to include ('tweet', 'article', 'paper')
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Index is empty, returning no results")
            return []
        
        # Encode query (with is_query=True for proper task type)
        query_embedding = self._get_embedding(query, is_query=True)
        
        # Search index - get more candidates to account for filtering
        # When filtering by content type, search ALL documents to ensure we find enough
        # Articles (65) and Papers (192) are very sparse compared to Tweets (11,422)
        if content_types:
            search_k = self.index.ntotal  # Search ALL when filtering - sparse types need it
        else:
            search_k = min(k * 5, self.index.ntotal)  # 5x for unfiltered search
        distances, indices = self.index.search(query_embedding.astype('float32'), search_k)
        
        logger.info(f"FAISS returned {len(indices[0])} candidates for k={k}")

        # Debug: count types in raw FAISS results and find first article position
        raw_type_counts = {'tweet': 0, 'article': 0, 'paper': 0, 'other': 0}
        first_article_pos = -1
        first_paper_pos = -1
        for pos, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.metadata):
                meta = self.metadata[idx]
                doc_type = meta.get('type', 'other')
                raw_type_counts[doc_type] = raw_type_counts.get(doc_type, 0) + 1
                if doc_type == 'article' and first_article_pos == -1:
                    first_article_pos = pos
                    logger.info(f"FIRST ARTICLE at position {pos}: {meta.get('title', 'Unknown')[:60]}")
                if doc_type == 'paper' and first_paper_pos == -1:
                    first_paper_pos = pos
                    logger.info(f"FIRST PAPER at position {pos}: {meta.get('title', 'Unknown')[:60]}")

        logger.info(f"RAW FAISS results by type: tweets={raw_type_counts.get('tweet', 0)}, articles={raw_type_counts.get('article', 0)}, papers={raw_type_counts.get('paper', 0)}")
        logger.info(f"First article at position: {first_article_pos}, First paper at position: {first_paper_pos}")
        logger.info(f"Content type filter applied: {content_types}")

        # When multiple content types are selected, collect results per type
        # to ensure proportional representation (sparse types like articles shouldn't be drowned out by tweets)
        results_by_type = {'tweet': [], 'article': [], 'paper': [], 'snippet': []}
        filtered_out = {'tweet': 0, 'article': 0, 'paper': 0}

        for idx, distance in zip(indices[0], distances[0]):
            if idx < 0:
                continue

            meta = self.metadata[idx]
            doc_type = meta.get('type', 'other')

            # Apply content type filter if provided
            if content_types and doc_type not in content_types:
                filtered_out[doc_type] = filtered_out.get(doc_type, 0) + 1
                continue

            # Apply concept filter if provided
            if concept_filter:
                # Check if any of the document's concepts match the filter
                doc_concept_ids = meta.get('concept_ids', [])
                if not any(cid in concept_filter for cid in doc_concept_ids):
                    continue

            result = {
                'type': doc_type,
                'id': meta['id'],
                'score': float(1 / (1 + distance)),  # Convert distance to similarity
                'content': self.doc_map.get(idx, ''),
                'metadata': meta
            }

            # Add type-specific fields
            if doc_type == 'tweet':
                result['author'] = meta.get('author')
                result['created_at'] = meta.get('created_at')
            elif doc_type == 'article':
                result['title'] = meta.get('title')
                result['author'] = meta.get('author')
            elif doc_type == 'paper':
                result['title'] = meta.get('title')
                result['year'] = meta.get('year')

            # Add concepts
            result['concepts'] = meta.get('concepts', [])

            # Collect by type for proportional blending
            if doc_type in results_by_type:
                results_by_type[doc_type].append(result)

        # Log collected results per type BEFORE blending
        logger.info(f"COLLECTED per type (before blending): tweets={len(results_by_type.get('tweet', []))}, articles={len(results_by_type.get('article', []))}, papers={len(results_by_type.get('paper', []))}")

        # Blend results proportionally when multiple content types selected
        results = []
        if content_types and len(content_types) > 1:
            # Calculate slots per type (ensure at least some from each available type)
            num_types = len(content_types)
            min_per_type = max(3, k // (num_types * 2))  # At least 3, or k/(2*num_types)
            remaining_slots = k

            # First, add minimum from each type that has results
            for ctype in content_types:
                type_results = results_by_type.get(ctype, [])
                to_add = min(min_per_type, len(type_results), remaining_slots)
                results.extend(type_results[:to_add])
                remaining_slots -= to_add
                logger.info(f"Added {to_add} {ctype}s (minimum quota)")

            # Then fill remaining slots proportionally from what's left
            if remaining_slots > 0:
                all_remaining = []
                for ctype in content_types:
                    type_results = results_by_type.get(ctype, [])
                    # Skip already-added items
                    already_added = min(min_per_type, len(type_results))
                    remaining_of_type = type_results[already_added:]
                    all_remaining.extend(remaining_of_type)

                # Sort by score and add remaining
                all_remaining.sort(key=lambda x: x['score'], reverse=True)
                results.extend(all_remaining[:remaining_slots])

            # Sort final results by score
            results.sort(key=lambda x: x['score'], reverse=True)
        else:
            # Single type or no filter - just take top k
            for ctype in (content_types or ['tweet', 'article', 'paper', 'snippet']):
                results.extend(results_by_type.get(ctype, []))
            results.sort(key=lambda x: x['score'], reverse=True)
            results = results[:k]

        # Debug: count types in final results
        final_type_counts = {'tweet': 0, 'article': 0, 'paper': 0}
        for r in results:
            rtype = r.get('type', 'other')
            final_type_counts[rtype] = final_type_counts.get(rtype, 0) + 1

        logger.info(f"FILTERED OUT by content_types: tweets={filtered_out.get('tweet', 0)}, articles={filtered_out.get('article', 0)}, papers={filtered_out.get('paper', 0)}")
        logger.info(f"FINAL results by type: tweets={final_type_counts.get('tweet', 0)}, articles={final_type_counts.get('article', 0)}, papers={final_type_counts.get('paper', 0)}")

        # Show first few articles/papers if any
        for r in results[:5]:
            if r.get('type') in ['article', 'paper']:
                logger.info(f"  - [{r.get('type')}] {r.get('metadata', {}).get('title', 'N/A')[:60]}...")

        logger.info(f"Returning {len(results)} results after filtering (requested k={k})")
        return results
    
    def ask(self, question: str, k: int = 10, use_concepts: bool = True,
            content_types: Optional[List[str]] = None,
            model: Optional[str] = None) -> Dict[str, Any]:
        """
        Answer a question using RAG with concept enhancement

        Args:
            question: The question to answer
            k: Number of documents to retrieve
            use_concepts: Whether to use concept information in the answer
            content_types: Optional list of content types to search ('tweet', 'article', 'paper')
        """
        # Check if this is a trend analysis query
        if self.is_trend_query(question):
            logger.info(f"Detected trend query, routing to trend analysis: {question}")
            # Use more documents for trend analysis (50 instead of 10)
            return self.analyze_trends(question, content_types=content_types, k=50, model=model)

        # Normal RAG search for non-trend queries
        # Search for relevant documents
        search_results = self.search(question, k=k, content_types=content_types)
        
        logger.info(f"Found {len(search_results)} search results for question: {question[:100]}")
        
        if not search_results:
            return {
                'answer': "I couldn't find relevant information to answer your question.",
                'sources': []
            }
        
        # Build context from search results
        context_parts = []
        sources = []
        
        for result in search_results:
            context_parts.append(result['content'])
            
            source = {
                'type': result['type'],
                'id': result['id'],
                'score': result['score']
            }
            
            # Add content preview (first 500 chars)
            content = result.get('content', '')
            if content:
                # Clean up the content for preview
                preview = content.replace('\n', ' ').strip()
                # Remove document type prefix if present
                if preview.startswith('Tweet: '):
                    preview = preview[7:]
                elif preview.startswith('Article: '):
                    preview = preview[9:]
                elif preview.startswith('Paper: '):
                    preview = preview[7:]
                # Limit to 500 characters
                source['content'] = preview[:500] + ('...' if len(preview) > 500 else '')
            
            if result['type'] == 'tweet':
                source['author'] = result.get('author')
            elif result['type'] in ['article', 'paper']:
                source['title'] = result.get('metadata', {}).get('title')
            
            if use_concepts and result.get('concepts'):
                source['concepts'] = result['concepts']
            
            sources.append(source)
        
        context = "\n\n---\n\n".join(context_parts)
        logger.info(f"Built context with {len(context)} characters from {len(context_parts)} documents")
        
        # Build prompt with concept awareness
        all_concepts = set()
        if use_concepts:
            # Collect all unique concepts from results
            for result in search_results:
                all_concepts.update(result.get('concepts', []))
            
            concept_context = ""
            if all_concepts:
                concept_context = f"\n\nKey concepts in the sources: {', '.join(sorted(all_concepts))}"
        else:
            concept_context = ""
        
        # Load prompt template from prompts_config.json
        with open('prompts_config.json', 'r') as f:
            prompts_config = json.load(f)
        
        rag_prompt_template = prompts_config.get('rag_query', {}).get('user_template', '')
        
        # Build the prompt with the template
        if rag_prompt_template:
            prompt = rag_prompt_template.format(
                context=context,
                question=question
            )
            # Add concept context if available
            if concept_context:
                prompt = prompt.replace("Answer:", f"{concept_context}\n\nAnswer:")
        else:
            # Fallback to simple prompt
            prompt = f"""Based on the following context, answer the question. 
If the answer cannot be found in the context, say so.{concept_context}

Context:
{context}

Question: {question}

Answer:"""
        
        # Get answer from LLM using configured RAG model (Gemini 2.5 Pro)
        # Load the model configuration from llm.json
        with open('llm.json', 'r') as f:
            llm_config = json.load(f)
        
        rag_model_config = llm_config['models'].get('rag_answer', {})

        # Log which model will be used
        if model:
            logger.info(f"Using user-selected model for RAG answer: {model}")
        else:
            logger.info("Using default model for RAG answer generation")

        # Convert prompt to OpenAI message format
        messages = [
            {"role": "user", "content": prompt}
        ]

        # Call LLM Manager with rag_answer task type
        # If user selected a model, pass it as override
        override_params = {'model': model} if model else None
        response = self.llm_manager.completion_sync(
            task_type='rag_answer',
            messages=messages,
            user_id=self.user_id,
            override_params=override_params
        )

        answer = response.choices[0].message.content
        
        return {
            'answer': answer,
            'sources': sources,
            'concepts_used': list(all_concepts) if use_concepts else []
        }

    def is_trend_query(self, question: str) -> bool:
        """
        Detect if a question is asking about trends or hot topics

        Args:
            question: The user's question

        Returns:
            True if the question is trend-related, False otherwise
        """
        question_lower = question.lower()

        # Trend-related keywords
        trend_keywords = [
            'trend', 'trending', 'hot topic', 'popular', 'key trends',
            'what are people talking about', 'what\'s happening',
            'current topics', 'latest', 'emerging', 'buzz',
            'hot', 'what\'s hot', 'popular topics', 'main topics',
            'key topics', 'biggest', 'most discussed', 'frequently mentioned'
        ]

        return any(keyword in question_lower for keyword in trend_keywords)

    def analyze_trends(self, question: str, content_types: Optional[List[str]] = None,
                      k: int = 50, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze trends across documents using LLM to identify hot topics

        Args:
            question: The trend analysis question
            content_types: Optional list of content types to analyze ('tweet', 'article', 'paper')
            k: Number of documents to retrieve for analysis (default 50 for better trend detection)
            model: Optional user-selected model for LLM generation

        Returns:
            Dictionary with trend analysis and sources
        """
        # Determine source type for the prompt
        if content_types:
            if len(content_types) == 1:
                source_type = content_types[0] + 's'  # tweet -> tweets
            else:
                source_type = ' and '.join(content_types) + 's'
        else:
            source_type = 'documents'

        logger.info(f"Analyzing trends in {source_type} with k={k}")

        # Retrieve MORE documents for better trend analysis
        search_query = "AI machine learning artificial intelligence technology"  # Broad query for trend analysis
        search_results = self.search(search_query, k=k, content_types=content_types)

        logger.info(f"Retrieved {len(search_results)} documents for trend analysis")

        if not search_results:
            return {
                'answer': f"I couldn't find enough {source_type} to analyze trends.",
                'sources': [],
                'is_trend_analysis': True
            }

        # Build documents list for LLM analysis
        documents_text = []
        sources = []

        for i, result in enumerate(search_results, 1):
            content = result.get('content', '')

            # Format document based on type
            if result['type'] == 'tweet':
                author = result.get('author', 'Unknown')
                doc_text = f"{i}. Tweet by @{author}: {content[:300]}"
            elif result['type'] == 'article':
                title = result.get('metadata', {}).get('title', 'Untitled')
                doc_text = f"{i}. Article: {title}\n{content[:500]}"
            elif result['type'] == 'paper':
                title = result.get('metadata', {}).get('title', 'Untitled')
                doc_text = f"{i}. Paper: {title}\n{content[:500]}"
            else:
                doc_text = f"{i}. {content[:300]}"

            documents_text.append(doc_text)

            # Build source reference
            source = {
                'type': result['type'],
                'id': result['id'],
                'score': result['score'],
                'content': result.get('content', '')[:300]  # Include content preview for frontend
            }

            if result['type'] == 'tweet':
                source['author'] = result.get('author')
            elif result['type'] in ['article', 'paper']:
                source['title'] = result.get('metadata', {}).get('title')

            # Add concepts
            if result.get('concepts'):
                source['concepts'] = result['concepts']

            sources.append(source)

        # Join all documents
        documents_combined = "\n\n".join(documents_text)

        # Load prompt template for trend analysis
        with open('prompts_config.json', 'r') as f:
            prompts_config = json.load(f)

        trend_prompt_template = prompts_config.get('rag_trend_analysis', {}).get('user_template', '')

        # Build the prompt
        if trend_prompt_template:
            prompt = trend_prompt_template.format(
                count=len(search_results),
                source_type=source_type,
                documents=documents_combined
            )
        else:
            # Fallback prompt
            prompt = f"""Analyze these {len(search_results)} {source_type} to identify KEY TRENDS and HOT TOPICS:

{documents_combined}

Provide a comprehensive trend analysis with:
1. Top 5 Trending Topics - Most discussed themes
2. Key Insights - Important patterns or developments
3. Notable Examples - Specific interesting cases
4. Emerging Patterns - New or growing areas

Format clearly with headers and bullet points."""

        # Get trend analysis from LLM using configured trend analysis model
        with open('llm.json', 'r') as f:
            llm_config = json.load(f)

        trend_model_config = llm_config['models'].get('trend_analysis', {})

        # Log which model will be used
        if model:
            logger.info(f"Using user-selected model for trend analysis: {model}")
        else:
            logger.info("Using default model for trend analysis")

        # Convert prompt to OpenAI message format
        messages = [
            {"role": "user", "content": prompt}
        ]

        # Call LLM Manager with trend_analysis task type
        # If user selected a model, pass it as override
        override_params = {'model': model} if model else None
        response = self.llm_manager.completion_sync(
            task_type='trend_analysis',
            messages=messages,
            user_id=self.user_id,
            override_params=override_params
        )

        analysis = response.choices[0].message.content

        return {
            'answer': analysis,
            'sources': sources,
            'is_trend_analysis': True,
            'documents_analyzed': len(search_results),
            'source_type': source_type
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the current index"""
        if self.index is None:
            return {'status': 'not_initialized', 'total_documents': 0}
        
        # Load index info if available
        index_info_path = self.index_dir / 'index_info.json'
        if index_info_path.exists():
            with open(index_info_path, 'r') as f:
                return json.load(f)
        
        # Fallback to basic stats
        return {
            'status': 'ready',
            'total_documents': self.index.ntotal if self.index else 0,
            'uses_concepts': True
        }
    
    def get_sample_questions(self) -> List[str]:
        """Get sample questions based on indexed content"""
        # Get top concepts
        top_concepts = self.concept_service.get_all_concepts_with_counts()[:5]
        concept_names = [c['display_name'] for c in top_concepts]
        
        questions = [
            "What are the latest developments in AI?",
            "What papers discuss transformer architectures?",
            "What are people saying about GPT models?",
            "Summarize recent articles about machine learning",
            "What are the key trends in AI research?"
        ]
        
        # Add concept-specific questions
        if concept_names:
            questions.extend([
                f"What do we know about {concept_names[0]}?",
                f"How is {concept_names[1]} being discussed?",
            ])
        
        return questions
    
    def _get_embedding(self, text: str, is_query: bool = False) -> np.ndarray:
        """Get embedding for a single text using API
        
        Args:
            text: Text to embed
            is_query: If True, use retrieval_query task type, else retrieval_document
        """
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Check cache if we have one (but not for queries)
        if not is_query and hasattr(self, 'embeddings_cache') and text_hash in self.embeddings_cache:
            return np.array(self.embeddings_cache[text_hash])
        
        try:
            if self.use_gemini_embeddings:
                # Use Gemini embeddings with appropriate task type
                task_type = "retrieval_query" if is_query else "retrieval_document"
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text[:8000],
                    task_type=task_type
                )
                embedding = np.array(result['embedding'])
            else:
                # Fallback to OpenAI
                response = self.openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=text[:8000]
                )
                embedding = np.array(response.data[0].embedding)
            
            # Cache if we have a cache
            if not hasattr(self, 'embeddings_cache'):
                self.embeddings_cache = {}
            self.embeddings_cache[text_hash] = embedding.tolist()
            
            return embedding.reshape(1, -1)  # Return as 2D array for FAISS
            
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            # Return zeros with correct dimension
            dimension = 768 if self.use_gemini_embeddings else 1536
            return np.zeros((1, dimension))
    
    def _get_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for multiple texts efficiently"""
        embeddings = []
        
        if self.use_gemini_embeddings:
            # Gemini batch embedding
            batch_size = 100
            
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
                    logger.error(f"Batch embedding failed, falling back to individual: {e}")
                    # Fallback to individual embeddings
                    for text in batch:
                        embedding = self._get_embedding(text)
                        embeddings.append(embedding.squeeze())  # Remove extra dimension
                
                if i + batch_size < len(texts):
                    import time
                    time.sleep(0.1)  # Rate limiting
        else:
            # OpenAI batch processing
            batch_size = 100
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                
                for text in batch:
                    embedding = self._get_embedding(text)
                    embeddings.append(embedding.squeeze())  # Remove extra dimension
                
                if i + batch_size < len(texts):
                    import time
                    time.sleep(0.1)  # Rate limiting
        
        return np.array(embeddings)
