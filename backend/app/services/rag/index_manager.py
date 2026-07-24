import os
import json
import pickle
import logging
import hashlib
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

import faiss
import numpy as np
import google.generativeai as genai
from openai import OpenAI

logger = logging.getLogger(__name__)

# backend/ directory (config files live there) - resolved from this file, not cwd
_BACKEND_DIR = Path(__file__).resolve().parents[3]

_rag_embedding_config: Optional[Dict[str, Any]] = None


def get_rag_embedding_config() -> Dict[str, Any]:
    """Load the RAG embedding configuration from backend/llm.json (models.rag_embedding).

    The config defines the primary (Gemini) and fallback (OpenAI) embedding
    models plus their dimensions. Changing them invalidates the existing index.
    """
    global _rag_embedding_config
    if _rag_embedding_config is None:
        llm_config_path = _BACKEND_DIR / 'llm.json'
        with open(llm_config_path, 'r') as f:
            llm_config = json.load(f)
        try:
            _rag_embedding_config = llm_config['models']['rag_embedding']
        except KeyError as e:
            raise KeyError(
                f"Missing 'models.rag_embedding' entry in {llm_config_path}"
            ) from e
    return _rag_embedding_config


def _embedding_model_and_dimension(use_gemini_embeddings: bool):
    """Return (model_name, dimension) for the active embedding backend."""
    config = get_rag_embedding_config()
    entry = config['primary'] if use_gemini_embeddings else config['fallback']
    return entry['model'], entry['dimension']


def init_embedding_clients(google_api_key, openai_api_key):
    """Returns (use_gemini_embeddings, openai_client) tuple."""
    if google_api_key:
        genai.configure(api_key=google_api_key)
        logger.info("Using Gemini embeddings for concept-based RAG")
        return True, None
    elif openai_api_key:
        return False, OpenAI(api_key=openai_api_key)
    else:
        raise ValueError("Neither GOOGLE_API_KEY nor OPENAI_API_KEY found")


def get_index_paths(index_dir: Path):
    index_dir.mkdir(exist_ok=True, parents=True)
    return {
        'index': index_dir / "faiss.index",
        'metadata': index_dir / "metadata.pkl",
        'doc_map': index_dir / "doc_map.pkl",
        'embeddings_cache': index_dir / "embeddings_cache.pkl",
        'info': index_dir / "index_info.json",
    }


def load_index(paths):
    """Load existing index or return empty state. Returns (index, metadata, doc_map)."""
    try:
        if paths['index'].exists() and paths['metadata'].exists():
            index = faiss.read_index(str(paths['index']))
            with open(paths['metadata'], 'rb') as f:
                metadata = pickle.load(f)
            with open(paths['doc_map'], 'rb') as f:
                doc_map = pickle.load(f)
            logger.info(f"Loaded RAG index with {index.ntotal} documents")
            return index, metadata, doc_map
        else:
            logger.info("No existing index found, will create new one")
            return None, [], {}
    except Exception as e:
        logger.error(f"Error loading index: {e}")
        return None, [], {}


def rebuild_index(db, concept_service, use_gemini_embeddings, openai_client, paths, embeddings_cache):
    """Rebuild the entire index with concept information"""
    logger.info("Starting RAG index rebuild with concepts...")

    documents = []
    metadata = []
    doc_map = {}
    doc_id = 0

    try:
        # Process tweets from MongoDB
        tweets = list(db.tweets.find())
        logger.info(f"Found {len(tweets)} tweets in MongoDB")
        for tweet in tweets:
            # Get concepts for this tweet
            concepts = concept_service.get_tags_for_content(
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
        articles = list(db.articles.find())
        logger.info(f"Found {len(articles)} articles in MongoDB")
        for article in articles:
            # Get concepts for this article
            concepts = concept_service.get_tags_for_content(
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
        papers = list(db.papers.find({'processed': True, 'paper_type': {'$ne': 'review'}}))
        logger.info(f"Found {len(papers)} processed papers in MongoDB")
        for paper in papers:
            # Get concepts for this paper
            concepts = concept_service.get_tags_for_content(
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
            embeddings, failed_indices = get_embeddings_batch(
                documents, use_gemini_embeddings, openai_client, embeddings_cache
            )

            # Drop documents whose embeddings failed (keep index/metadata in sync)
            if failed_indices:
                logger.warning(
                    f"Skipping {len(failed_indices)} of {len(documents)} documents "
                    f"due to embedding failures"
                )
                failed = set(failed_indices)
                documents = [d for i, d in enumerate(documents) if i not in failed]
                metadata = [m for i, m in enumerate(metadata) if i not in failed]
                doc_map = {i: d for i, d in enumerate(documents)}

            if not documents:
                raise RuntimeError(
                    "All embedding requests failed - index was not rebuilt"
                )

            # Create FAISS index
            embedding_model, dimension = _embedding_model_and_dimension(use_gemini_embeddings)
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings.astype('float32'))

            # Save index and metadata
            faiss.write_index(index, str(paths['index']))

            with open(paths['metadata'], 'wb') as f:
                pickle.dump(metadata, f)

            with open(paths['doc_map'], 'wb') as f:
                pickle.dump(doc_map, f)

            # Save index info
            index_info = {
                'status': 'ready',
                'total_documents': len(documents),
                'tweets': len([m for m in metadata if m['type'] == 'tweet']),
                'articles': len([m for m in metadata if m['type'] == 'article']),
                'papers': len([m for m in metadata if m['type'] == 'paper']),
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'embedding_model': embedding_model,
                'skipped_documents': len(failed_indices),
                'uses_concepts': True
            }

            with open(paths['info'], 'w') as f:
                json.dump(index_info, f, indent=2)

            logger.info(f"Index rebuilt successfully with {len(documents)} documents")
            return index, metadata, doc_map, index_info
        else:
            logger.warning("No documents to index")
            return None, [], {}, {'total_documents': 0}

    except Exception as e:
        logger.error(f"Error rebuilding index: {e}", exc_info=True)
        raise


def get_stats(index, paths):
    """Get statistics about the current index"""
    if index is None:
        return {'status': 'not_initialized', 'total_documents': 0}

    # Load index info if available
    if paths['info'].exists():
        with open(paths['info'], 'r') as f:
            return json.load(f)

    # Fallback to basic stats
    return {
        'status': 'ready',
        'total_documents': index.ntotal if index else 0,
        'uses_concepts': True
    }


def get_sample_questions(concept_service) -> List[str]:
    """Get sample questions based on indexed content"""
    # Get top concepts
    top_concepts = concept_service.get_all_concepts_with_counts()[:5]
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


def get_embedding(text: str, use_gemini_embeddings: bool, openai_client, embeddings_cache: dict,
                  is_query: bool = False) -> np.ndarray:
    """Get embedding for a single text using API

    Args:
        text: Text to embed
        use_gemini_embeddings: Whether to use Gemini or OpenAI
        openai_client: OpenAI client instance (if not using Gemini)
        embeddings_cache: Dict for caching embeddings
        is_query: If True, use retrieval_query task type, else retrieval_document

    Raises:
        Exception: Propagated API errors - callers must handle failures
        explicitly (no silent zero-vector fallback).
    """
    text_hash = hashlib.md5(text.encode()).hexdigest()

    # Check cache if we have one (but not for queries)
    if not is_query and text_hash in embeddings_cache:
        return np.array(embeddings_cache[text_hash])

    model, _ = _embedding_model_and_dimension(use_gemini_embeddings)

    try:
        if use_gemini_embeddings:
            # Use Gemini embeddings with appropriate task type
            task_type = "retrieval_query" if is_query else "retrieval_document"
            result = genai.embed_content(
                model=model,
                content=text[:8000],
                task_type=task_type
            )
            embedding = np.array(result['embedding'])
        else:
            # Fallback to OpenAI
            response = openai_client.embeddings.create(
                model=model,
                input=text[:8000]
            )
            embedding = np.array(response.data[0].embedding)
    except Exception as e:
        logger.error(f"Embedding error ({model}): {e}")
        raise

    # Cache
    embeddings_cache[text_hash] = embedding.tolist()

    return embedding.reshape(1, -1)  # Return as 2D array for FAISS


def get_embeddings_batch(texts: List[str], use_gemini_embeddings: bool, openai_client,
                         embeddings_cache: dict):
    """Get embeddings for multiple texts efficiently.

    Returns:
        Tuple (embeddings, failed_indices): embeddings is a np.ndarray of
        successfully embedded texts (in original order, failures removed);
        failed_indices lists the positions in `texts` whose embedding failed.
    """
    embeddings = []
    failed_indices: List[int] = []
    batch_size = 100

    if use_gemini_embeddings:
        model, _ = _embedding_model_and_dimension(use_gemini_embeddings)

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]

            try:
                # Gemini supports batch embedding
                batch_results = genai.embed_content(
                    model=model,
                    content=batch,
                    task_type="retrieval_document"
                )

                # Extract embeddings from results
                for embedding in batch_results['embedding']:
                    embeddings.append(np.array(embedding))

            except Exception as e:
                logger.error(f"Batch embedding failed, falling back to individual: {e}")
                # Fallback to individual embeddings; skip and record failures
                for offset, text in enumerate(batch):
                    try:
                        embedding = get_embedding(text, use_gemini_embeddings, openai_client, embeddings_cache)
                        embeddings.append(embedding.squeeze())  # Remove extra dimension
                    except Exception as embed_error:
                        logger.warning(
                            f"Skipping document {i + offset}: embedding failed ({embed_error})"
                        )
                        failed_indices.append(i + offset)

            if i + batch_size < len(texts):
                time.sleep(0.1)  # Rate limiting
    else:
        # OpenAI batch processing
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]

            for offset, text in enumerate(batch):
                try:
                    embedding = get_embedding(text, use_gemini_embeddings, openai_client, embeddings_cache)
                    embeddings.append(embedding.squeeze())  # Remove extra dimension
                except Exception as embed_error:
                    logger.warning(
                        f"Skipping document {i + offset}: embedding failed ({embed_error})"
                    )
                    failed_indices.append(i + offset)

            if i + batch_size < len(texts):
                time.sleep(0.1)  # Rate limiting

    if failed_indices:
        logger.warning(f"{len(failed_indices)} of {len(texts)} embeddings failed")

    return np.array(embeddings), failed_indices
