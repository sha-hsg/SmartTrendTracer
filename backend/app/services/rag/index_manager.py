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
from bson import ObjectId
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


def _with_rate_limit_retry(call, attempts: int = 6, first_wait: float = 2.0):
    """Retry an embedding API call on HTTP 429 with exponential backoff.

    The 2026-10-03 rebuild lost 61 of 32,282 documents to transient Gemini
    quota errors because nothing was retried."""
    wait = first_wait
    for attempt in range(attempts):
        try:
            return call()
        except Exception as e:
            if '429' not in str(e) or attempt == attempts - 1:
                raise
            logger.warning(f"Embedding rate limited, retrying in {wait:.0f}s")
            time.sleep(wait)
            wait *= 2


def _normalize(vec: np.ndarray) -> np.ndarray:
    """L2-normalize so IndexFlatL2 distance ranks like cosine similarity.
    gemini-embedding-001 vectors truncated below 3072 dims are not normalized."""
    norm = np.linalg.norm(vec)
    return vec / norm if norm else vec


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


PAPER_INDEX_QUERY = {'processed': True, 'paper_type': {'$ne': 'review'}}


def _concept_fields(concepts):
    names = [c['display_name'] for c in concepts]
    ids = sorted({str(v) for c in concepts for v in (c.get('id'), c.get('concept_id')) if v})
    return names, ids


def build_tweet_doc(tweet, concepts):
    """(text, metadata) of one tweet — shared by rebuild_index and update_index."""
    concept_names, concept_ids = _concept_fields(concepts)
    doc_text = f"Tweet by @{tweet.get('author_username', '')}: {tweet.get('text', '')}"
    if concept_names:
        doc_text += f"\nConcepts: {', '.join(concept_names)}"
    return doc_text, {
        'type': 'tweet',
        'id': str(tweet['_id']),
        'author': tweet.get('author_username', ''),
        'created_at': tweet.get('created_at'),
        'concepts': concept_names,
        'concept_ids': concept_ids,
    }


def build_article_doc(article, concepts):
    concept_names, concept_ids = _concept_fields(concepts)
    doc_text = f"Article: {article.get('title', '')}\nBy: {article.get('author_name', 'Unknown')}\n"
    content = article.get('content', '')
    doc_text += f"{content[:2000]}..." if len(content) > 2000 else content
    if concept_names:
        doc_text += f"\nConcepts: {', '.join(concept_names)}"
    return doc_text, {
        'type': 'article',
        'id': str(article['_id']),
        'title': article.get('title', ''),
        'author': article.get('author_name'),
        'published_at': article.get('published_at'),
        'concepts': concept_names,
        'concept_ids': concept_ids,
    }


def build_paper_doc(paper, concepts):
    """(text, metadata) of one paper, or None when it has neither content nor abstract."""
    concept_names, concept_ids = _concept_fields(concepts)
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
        logger.warning(f"Paper '{paper.get('title', 'Unknown')}' has no meaningful content, skipping")
        return None

    if concept_names:
        doc_text += f"\nConcepts: {', '.join(concept_names)}"

    return doc_text, {
        'type': 'paper',
        'id': str(paper['_id']),
        'title': paper.get('title', ''),
        'year': paper.get('year'),
        'concepts': concept_names,
        'concept_ids': concept_ids,
    }


_BUILDERS = {'tweet': build_tweet_doc, 'article': build_article_doc, 'paper': build_paper_doc}


def collect_documents(db, concept_service, queries):
    """Build (documents, metadata) for {content_type: mongo_query}; order tweets, articles, papers."""
    documents, metadata = [], []
    collections = {'tweet': db.tweets, 'article': db.articles, 'paper': db.papers}
    for content_type in ('tweet', 'article', 'paper'):
        if content_type not in queries:
            continue
        items = list(collections[content_type].find(queries[content_type]))
        logger.info(f"Found {len(items)} {content_type}s in MongoDB")
        for item in items:
            concepts = concept_service.get_tags_for_content(
                content_type=content_type,
                content_id=str(item['_id'])
            )
            built = _BUILDERS[content_type](item, concepts)
            if built is None:
                continue
            documents.append(built[0])
            metadata.append(built[1])
    return documents, metadata


def rebuild_index(db, concept_service, use_gemini_embeddings, openai_client, paths, embeddings_cache):
    """Rebuild the entire index with concept information"""
    logger.info("Starting RAG index rebuild with concepts...")

    try:
        documents, metadata = collect_documents(
            db, concept_service, {'tweet': {}, 'article': {}, 'paper': PAPER_INDEX_QUERY})
        doc_map = {i: d for i, d in enumerate(documents)}

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
    model, dimension = _embedding_model_and_dimension(use_gemini_embeddings)
    # Key includes the model: after a model switch, cached vectors of the old
    # model must not be mixed into the new index
    text_hash = hashlib.md5(f"{model}:{dimension}:{text}".encode()).hexdigest()

    # Check cache if we have one (but not for queries)
    if not is_query and text_hash in embeddings_cache:
        return np.array(embeddings_cache[text_hash])

    try:
        if use_gemini_embeddings:
            # Use Gemini embeddings with appropriate task type
            task_type = "retrieval_query" if is_query else "retrieval_document"
            result = _with_rate_limit_retry(lambda: genai.embed_content(
                model=model,
                content=text[:8000],
                task_type=task_type,
                output_dimensionality=dimension
            ))
            embedding = _normalize(np.array(result['embedding']))
        else:
            # Fallback to OpenAI
            response = openai_client.embeddings.create(
                model=model,
                input=text[:8000]
            )
            embedding = _normalize(np.array(response.data[0].embedding))
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
        model, dimension = _embedding_model_and_dimension(use_gemini_embeddings)

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]

            try:
                # Gemini supports batch embedding
                batch_results = _with_rate_limit_retry(lambda: genai.embed_content(
                    model=model,
                    content=batch,
                    task_type="retrieval_document",
                    output_dimensionality=dimension
                ))

                # Extract embeddings from results
                for embedding in batch_results['embedding']:
                    embeddings.append(_normalize(np.array(embedding)))

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


def _active_counts(metadata) -> Dict[str, int]:
    active = [m for m in metadata if not m.get('stale')]
    return {
        'total_documents': len(active),
        'tweets': sum(m['type'] == 'tweet' for m in active),
        'articles': sum(m['type'] == 'article' for m in active),
        'papers': sum(m['type'] == 'paper' for m in active),
    }


def _changed_since(db, since: datetime) -> set:
    """(type, id) of indexed content that may have new text since `since`:
    newly tagged items (concept names are part of the document) and
    re-processed papers / updated articles."""
    changed = {(t['content_type'], str(t['content_id']))
               for t in db.tag_instances.find({'created_at': {'$gt': since}},
                                              {'content_type': 1, 'content_id': 1})}
    changed |= {('paper', str(p['_id'])) for p in db.papers.find(
        {'$or': [{'processed_at': {'$gt': since}}, {'updated_at': {'$gt': since}}]}, {'_id': 1})}
    changed |= {('article', str(a['_id'])) for a in db.articles.find({'updated_at': {'$gt': since}}, {'_id': 1})}
    return changed


def update_index(db, concept_service, use_gemini_embeddings, openai_client, paths, embeddings_cache,
                 index, metadata, doc_map):
    """Add new and changed content to the existing index without a full rebuild.

    New documents are embedded and appended. For changed or deleted content the
    old entry is marked metadata['stale'] (search skips it); a changed item also
    gets a fresh entry. Only the candidates are rebuilt and embedded, so a run
    costs a fraction of a full rebuild. Documents whose embedding fails stay
    missing and are picked up again by the next update.

    Refuses to run when the index was built with a different embedding model —
    query and index vectors would not be comparable.
    """
    if index is None or not paths['info'].exists():
        raise RuntimeError('No index yet - run a full rebuild first')
    info = json.loads(paths['info'].read_text())
    model, dimension = _embedding_model_and_dimension(use_gemini_embeddings)
    if info.get('embedding_model') != model or index.d != dimension:
        raise RuntimeError(f"Index was built with {info.get('embedding_model')} ({index.d}d), "
                           f"configured is {model} ({dimension}d) - a full rebuild is required")

    started = datetime.now(timezone.utc)
    since = datetime.fromisoformat(info.get('last_incremental_update') or info['last_updated'])
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)

    indexed = {(m['type'], m['id']): pos for pos, m in enumerate(metadata) if not m.get('stale')}
    in_db = {('tweet', str(i)) for i in db.tweets.distinct('_id')}
    in_db |= {('article', str(i)) for i in db.articles.distinct('_id')}
    in_db |= {('paper', str(i)) for i in db.papers.distinct('_id', PAPER_INDEX_QUERY)}

    new = in_db - indexed.keys()
    changed = (_changed_since(db, since) & indexed.keys()) & in_db
    deleted = indexed.keys() - in_db
    candidates = new | changed
    logger.info(f"RAG update: {len(new)} new, {len(changed)} changed, {len(deleted)} deleted since {since.isoformat()}")

    def ids_of(content_type):
        ids = [i for t, i in candidates if t == content_type]
        return ids if content_type == 'tweet' else [ObjectId(i) for i in ids if ObjectId.is_valid(i)]

    queries = {}
    for content_type in ('tweet', 'article', 'paper'):
        ids = ids_of(content_type)
        if ids:
            base = PAPER_INDEX_QUERY if content_type == 'paper' else {}
            queries[content_type] = {**base, '_id': {'$in': ids}}
    documents, new_meta = collect_documents(db, concept_service, queries) if queries else ([], [])

    failed: List[int] = []
    added = 0
    if documents:
        embeddings, failed = get_embeddings_batch(documents, use_gemini_embeddings, openai_client, embeddings_cache)
        keep = [i for i in range(len(documents)) if i not in set(failed)]
        documents = [documents[i] for i in keep]
        new_meta = [new_meta[i] for i in keep]
        if documents:
            index.add(embeddings.astype('float32'))
            for doc_text, meta in zip(documents, new_meta):
                doc_map[len(metadata)] = doc_text
                metadata.append(meta)
            added = len(documents)

    # Superseded entries: changed items that got a fresh entry, and deleted content
    refreshed = {(m['type'], m['id']) for m in new_meta}
    for key in (changed & refreshed) | deleted:
        metadata[indexed[key]]['stale'] = True

    faiss.write_index(index, str(paths['index']))
    with open(paths['metadata'], 'wb') as f:
        pickle.dump(metadata, f)
    with open(paths['doc_map'], 'wb') as f:
        pickle.dump(doc_map, f)
    info.update(_active_counts(metadata))
    info.update({
        'status': 'ready',
        'last_incremental_update': started.isoformat(),
        'stale_entries': sum(1 for m in metadata if m.get('stale')),
        'skipped_documents': len(failed),
    })
    paths['info'].write_text(json.dumps(info, indent=2))

    result = {
        'added': added - len(changed & refreshed),
        'updated': len(changed & refreshed),
        'removed': len(deleted),
        'failed': len(failed),
        **_active_counts(metadata),
    }
    logger.info(f"RAG update done: {result}")
    return index, metadata, doc_map, result
