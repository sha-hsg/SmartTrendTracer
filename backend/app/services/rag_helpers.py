"""
RAG Service Helper Functions

Reusable functions for RAG (Retrieval-Augmented Generation) operations:
- Embedding functions (Gemini/OpenAI with caching)
- Index management (FAISS load/save)
- Document processing (tweets, articles, papers, snippets)
- Text utilities (chunking, hashing)
- Search utilities (result formatting, context building)
- Metadata migration helpers
"""

import os
import json
import pickle
import hashlib
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
import numpy as np

import faiss


# =============================================================================
# EMBEDDING FUNCTIONS
# =============================================================================

def get_embedding_dimension(use_gemini: bool) -> int:
    """Get embedding dimension based on provider.

    Args:
        use_gemini: True for Gemini (768), False for OpenAI (1536)

    Returns:
        Embedding dimension
    """
    return 768 if use_gemini else 1536


def create_content_hash(text: str) -> str:
    """Create MD5 hash of text for caching.

    Args:
        text: Text to hash

    Returns:
        MD5 hash string
    """
    return hashlib.md5(text.encode()).hexdigest()


def get_embedding_with_cache(
    text: str,
    cache: dict,
    use_gemini: bool,
    openai_client=None,
    max_length: int = 8000
) -> np.ndarray:
    """Get embedding for text with caching support.

    Args:
        text: Text to embed
        cache: Cache dictionary (modified in place)
        use_gemini: Whether to use Gemini (True) or OpenAI (False)
        openai_client: OpenAI client (required if use_gemini=False)
        max_length: Maximum text length to embed

    Returns:
        Embedding as numpy array
    """
    text_hash = create_content_hash(text)

    if text_hash in cache:
        return np.array(cache[text_hash])

    try:
        if use_gemini:
            import google.generativeai as genai
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text[:max_length],
                task_type="retrieval_document",
                title="Document"
            )
            embedding = np.array(result['embedding'])
        else:
            if not openai_client:
                raise ValueError("OpenAI client required when use_gemini=False")
            response = openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text[:max_length]
            )
            embedding = np.array(response.data[0].embedding)

        cache[text_hash] = embedding.tolist()
        return embedding

    except Exception as e:
        print(f"Embedding error: {e}")
        return np.zeros(get_embedding_dimension(use_gemini))


def get_embeddings_batch(
    texts: List[str],
    use_gemini: bool,
    progress_callback: Optional[Callable[[str, int], None]] = None,
    openai_client=None,
    cache: Optional[dict] = None,
    batch_size: int = 100
) -> np.ndarray:
    """Get embeddings for multiple texts efficiently.

    Args:
        texts: List of texts to embed
        use_gemini: Whether to use Gemini embeddings
        progress_callback: Optional callback(message, progress_percent)
        openai_client: OpenAI client (required if use_gemini=False)
        cache: Optional cache dictionary
        batch_size: Batch size for processing

    Returns:
        Numpy array of embeddings
    """
    import time
    embeddings = []
    cache = cache or {}

    if use_gemini:
        import google.generativeai as genai

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]

            try:
                batch_results = genai.embed_content(
                    model="models/text-embedding-004",
                    content=batch,
                    task_type="retrieval_document"
                )

                for embedding in batch_results['embedding']:
                    embeddings.append(np.array(embedding))

            except Exception as e:
                print(f"Batch embedding failed, falling back to individual: {e}")
                for text in batch:
                    embedding = get_embedding_with_cache(
                        text, cache, use_gemini, openai_client
                    )
                    embeddings.append(embedding)

            if progress_callback:
                progress = 80 + int((i / len(texts)) * 10)
                progress_callback(
                    f"Creating Gemini embeddings... ({min(i + batch_size, len(texts))}/{len(texts)})",
                    progress
                )

            if i + batch_size < len(texts):
                time.sleep(0.1)
    else:
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]

            for text in batch:
                embedding = get_embedding_with_cache(
                    text, cache, use_gemini, openai_client
                )
                embeddings.append(embedding)

            if progress_callback:
                progress = 80 + int((i / len(texts)) * 10)
                progress_callback(
                    f"Creating OpenAI embeddings... ({min(i + batch_size, len(texts))}/{len(texts)})",
                    progress
                )

            if i + batch_size < len(texts):
                time.sleep(0.1)

    return np.array(embeddings)


# =============================================================================
# INDEX MANAGEMENT FUNCTIONS
# =============================================================================

def load_faiss_index(index_path: str) -> Optional[faiss.Index]:
    """Load FAISS index from disk.

    Args:
        index_path: Path to FAISS index file

    Returns:
        FAISS index or None if not found
    """
    try:
        if os.path.exists(index_path):
            return faiss.read_index(index_path)
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
    return None


def save_faiss_index(index: faiss.Index, index_path: str) -> bool:
    """Save FAISS index to disk.

    Args:
        index: FAISS index to save
        index_path: Path to save to

    Returns:
        True if successful
    """
    try:
        faiss.write_index(index, index_path)
        return True
    except Exception as e:
        print(f"Error saving FAISS index: {e}")
        return False


def load_pickle_file(file_path: str, default: Any = None) -> Any:
    """Load pickled data from file.

    Args:
        file_path: Path to pickle file
        default: Default value if file not found

    Returns:
        Loaded data or default
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return pickle.load(f)
    except Exception as e:
        print(f"Error loading pickle file {file_path}: {e}")
    return default if default is not None else {}


def save_pickle_file(data: Any, file_path: str) -> bool:
    """Save data to pickle file.

    Args:
        data: Data to save
        file_path: Path to save to

    Returns:
        True if successful
    """
    try:
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
        return True
    except Exception as e:
        print(f"Error saving pickle file {file_path}: {e}")
        return False


def load_index_info(info_path: str) -> dict:
    """Load index info JSON file.

    Args:
        info_path: Path to index info JSON

    Returns:
        Index info dict
    """
    try:
        if os.path.exists(info_path):
            with open(info_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading index info: {e}")
    return {}


def save_index_info(info: dict, info_path: str) -> bool:
    """Save index info to JSON file.

    Args:
        info: Index info dict
        info_path: Path to save to

    Returns:
        True if successful
    """
    try:
        with open(info_path, 'w') as f:
            json.dump(info, f)
        return True
    except Exception as e:
        print(f"Error saving index info: {e}")
        return False


# =============================================================================
# DOCUMENT PROCESSING FUNCTIONS
# =============================================================================

def process_tweet_for_index(
    tweet_id: str,
    text: str,
    author_username: str,
    created_at: Any,
    tags: List[str] = None
) -> dict:
    """Process a tweet for indexing.

    Args:
        tweet_id: Tweet ID
        text: Tweet text
        author_username: Author's username
        created_at: Tweet creation timestamp
        tags: List of tags

    Returns:
        Document dict for indexing
    """
    return {
        'id': f"tweet_{tweet_id}",
        'content': text,
        'type': 'tweet',
        'metadata': {
            'author': author_username,
            'created_at': created_at,
            'tags': tags or [],
            'url': f"https://twitter.com/{author_username}/status/{tweet_id}"
        }
    }


def process_article_for_index(
    article_id: str,
    title: str,
    content: str,
    author_name: str,
    published_at: Any,
    url: str,
    chunk_size: int = 1500,
    overlap: int = 200
) -> List[dict]:
    """Process an article for indexing (with chunking for long articles).

    Args:
        article_id: Article ID
        title: Article title
        content: Article content (markdown)
        author_name: Author name
        published_at: Publication date
        url: Article URL
        chunk_size: Size of text chunks
        overlap: Overlap between chunks

    Returns:
        List of document dicts (may be multiple if chunked)
    """
    documents = []

    if len(content) > 2000:
        chunks = chunk_text(content, chunk_size, overlap)
        for i, chunk in enumerate(chunks):
            documents.append({
                'id': f"article_{article_id}_chunk_{i}",
                'content': chunk,
                'type': 'article',
                'metadata': {
                    'title': title,
                    'author': author_name,
                    'published_at': published_at.isoformat() if hasattr(published_at, 'isoformat') else published_at,
                    'url': url,
                    'chunk': i
                }
            })
    else:
        documents.append({
            'id': f"article_{article_id}",
            'content': content,
            'type': 'article',
            'metadata': {
                'title': title,
                'author': author_name,
                'published_at': published_at.isoformat() if hasattr(published_at, 'isoformat') else published_at,
                'url': url
            }
        })

    return documents


def process_snippet_for_index(
    snippet_id: str,
    text: str,
    annotation: Optional[str],
    article_id: str,
    category: str,
    created_at: Any
) -> dict:
    """Process a snippet for indexing.

    Args:
        snippet_id: Snippet ID
        text: Snippet text
        annotation: Optional annotation
        article_id: Parent article ID
        category: Snippet category
        created_at: Creation timestamp

    Returns:
        Document dict for indexing
    """
    content = f"{text}\n\nNote: {annotation}" if annotation else text

    return {
        'id': f"snippet_{snippet_id}",
        'content': content,
        'type': 'snippet',
        'metadata': {
            'article_id': article_id,
            'category': category,
            'created_at': created_at.isoformat() if hasattr(created_at, 'isoformat') else created_at
        }
    }


def process_paper_for_index(
    paper_id: str,
    title: str,
    abstract: Optional[str],
    content: Optional[str],
    authors: str,
    conference: Optional[str],
    journal: Optional[str],
    publication_date: Any,
    arxiv_id: Optional[str],
    doi: Optional[str],
    page_count: Optional[int],
    tags: List[str] = None,
    max_content_length: int = 3000
) -> Optional[dict]:
    """Process a paper for indexing.

    Args:
        paper_id: Paper ID
        title: Paper title
        abstract: Paper abstract
        content: Paper content
        authors: Paper authors
        conference: Conference name
        journal: Journal name
        publication_date: Publication date
        arxiv_id: ArXiv ID
        doi: DOI
        page_count: Number of pages
        tags: List of tags
        max_content_length: Max content chars to include

    Returns:
        Document dict for indexing or None if no content
    """
    paper_content = []
    if title:
        paper_content.append(f"Title: {title}")
    if abstract:
        paper_content.append(f"Abstract: {abstract}")
    if content:
        paper_content.append(f"Content: {content[:max_content_length]}")

    if not paper_content:
        return None

    return {
        'id': f"paper_{paper_id}",
        'content': "\n\n".join(paper_content),
        'type': 'paper',
        'metadata': {
            'title': title,
            'authors': authors,
            'conference': conference,
            'journal': journal,
            'publication_date': publication_date.isoformat() if hasattr(publication_date, 'isoformat') else publication_date,
            'arxiv_id': arxiv_id,
            'doi': doi,
            'tags': tags or [],
            'page_count': page_count
        }
    }


# =============================================================================
# TEXT UTILITIES
# =============================================================================

def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks.

    Args:
        text: Text to chunk
        chunk_size: Size of each chunk
        overlap: Overlap between chunks

    Returns:
        List of text chunks
    """
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


def truncate_content(content: str, max_length: int = 500) -> str:
    """Truncate content to max length.

    Args:
        content: Content to truncate
        max_length: Maximum length

    Returns:
        Truncated content
    """
    if len(content) <= max_length:
        return content
    return content[:max_length]


# =============================================================================
# SEARCH UTILITIES
# =============================================================================

def distance_to_similarity(distance: float) -> float:
    """Convert FAISS L2 distance to similarity score.

    Args:
        distance: L2 distance from FAISS

    Returns:
        Similarity score (0-1, higher is better)
    """
    return float(1 / (1 + distance))


def format_search_result(
    doc: dict,
    distance: float,
    rank: int,
    max_content_length: int = 500
) -> dict:
    """Format a search result for API response.

    Args:
        doc: Document dict from metadata
        distance: FAISS distance
        rank: Result rank (1-based)
        max_content_length: Max content chars to return

    Returns:
        Formatted search result dict
    """
    # Handle both dict format and legacy Document objects
    if isinstance(doc, dict):
        content = doc.get('content', '')
        doc_type = doc.get('type', 'unknown')
        metadata = doc.get('metadata', {})
    else:
        content = getattr(doc, 'content', '')
        doc_type = getattr(doc, 'source_type', 'unknown')
        metadata = getattr(doc, 'metadata', {})

    return {
        'content': truncate_content(content, max_content_length),
        'type': doc_type,
        'score': distance_to_similarity(distance),
        'metadata': metadata,
        'rank': rank
    }


def build_rag_context(
    search_results: List[dict],
    max_sources: int = 10
) -> str:
    """Build context string for RAG answer generation.

    Args:
        search_results: List of search result dicts
        max_sources: Maximum number of sources to include

    Returns:
        Context string for LLM
    """
    context_parts = []
    for result in search_results[:max_sources]:
        context_parts.append(f"[{result['type']}]: {result['content']}")

    return "\n\n".join(context_parts)


def generate_fallback_answer(query: str, search_results: List[dict]) -> str:
    """Generate a fallback answer when LLM fails.

    Args:
        query: User's query
        search_results: Search results

    Returns:
        Fallback answer string
    """
    answer = f"Based on the search results, I found {len(search_results)} relevant documents about {query}. The most relevant sources discuss:\n\n"
    for i, result in enumerate(search_results[:3], 1):
        snippet = truncate_content(result.get('content', ''), 200)
        answer += f"{i}. {snippet}...\n\n"
    answer += "Please review the source documents for more detailed information."
    return answer


# =============================================================================
# METADATA MIGRATION HELPERS
# =============================================================================

def migrate_metadata_if_needed(metadata: dict) -> tuple:
    """Migrate metadata from legacy Document objects to dicts.

    Args:
        metadata: Metadata dict (may contain legacy Document objects)

    Returns:
        Tuple of (migrated_metadata, was_migrated)
    """
    if not metadata:
        return metadata, False

    first_value = next(iter(metadata.values()), None)
    if first_value is None:
        return metadata, False

    # Check if it's a legacy Document object
    if hasattr(first_value, 'id') and hasattr(first_value, 'content'):
        print("Migrating metadata from Document objects to dicts...")
        migrated = {}
        for key, doc in metadata.items():
            if hasattr(doc, '__dict__'):
                migrated[key] = {
                    'id': doc.id,
                    'content': doc.content,
                    'type': getattr(doc, 'source_type', 'unknown'),
                    'metadata': getattr(doc, 'metadata', {})
                }
            else:
                migrated[key] = doc
        return migrated, True

    return metadata, False


def migrate_doc_map_if_needed(doc_map: dict) -> tuple:
    """Migrate doc_map from legacy Document objects to string IDs.

    Args:
        doc_map: Doc map dict (may contain legacy Document objects)

    Returns:
        Tuple of (migrated_doc_map, was_migrated)
    """
    if not doc_map:
        return doc_map, False

    needs_migration = False
    for value in doc_map.values():
        if hasattr(value, 'id'):
            needs_migration = True
            break

    if needs_migration:
        print("Migrating doc_map from Document objects to string IDs...")
        migrated = {}
        for key, value in doc_map.items():
            if hasattr(value, 'id'):
                migrated[key] = value.id
            else:
                migrated[key] = value
        return migrated, True

    return doc_map, False
