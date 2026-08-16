import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def search(index, metadata, doc_map, use_gemini_embeddings, openai_client, embeddings_cache,
           query: str, k: int = 10, concept_filter: Optional[List[str]] = None,
           content_types: Optional[List[str]] = None) -> List[Dict]:
    """
    Search the index with optional concept and content type filtering

    Args:
        index: FAISS index
        metadata: List of document metadata dicts
        doc_map: Dict mapping doc IDs to text
        use_gemini_embeddings: Whether to use Gemini or OpenAI
        openai_client: OpenAI client instance (if not using Gemini)
        embeddings_cache: Dict for caching embeddings
        query: Search query
        k: Number of results to return
        concept_filter: Optional list of concept IDs to filter by
        content_types: Optional list of content types to include ('tweet', 'article', 'paper')
    """
    from app.services.rag.index_manager import get_embedding

    if index is None or index.ntotal == 0:
        logger.warning("Index is empty, returning no results")
        return []

    # Encode query (with is_query=True for proper task type)
    query_embedding = get_embedding(query, use_gemini_embeddings, openai_client, embeddings_cache, is_query=True)

    # Search index - get more candidates to account for filtering
    # When filtering by content type, search ALL documents to ensure we find enough
    # Articles (65) and Papers (192) are very sparse compared to Tweets (11,422)
    if content_types:
        search_k = index.ntotal  # Search ALL when filtering - sparse types need it
    else:
        search_k = min(k * 5, index.ntotal)  # 5x for unfiltered search
    distances, indices = index.search(query_embedding.astype('float32'), search_k)

    logger.info(f"FAISS returned {len(indices[0])} candidates for k={k}")

    # Debug: count types in raw FAISS results and find first article position
    raw_type_counts = {'tweet': 0, 'article': 0, 'paper': 0, 'other': 0}
    first_article_pos = -1
    first_paper_pos = -1
    for pos, idx in enumerate(indices[0]):
        if idx >= 0 and idx < len(metadata):
            meta = metadata[idx]
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
    concept_filtered = 0

    for idx, distance in zip(indices[0], distances[0]):
        if idx < 0 or idx >= len(metadata):
            continue

        meta = metadata[idx]
        doc_type = meta.get('type', 'other')

        # Apply content type filter if provided
        if content_types and doc_type not in content_types:
            filtered_out[doc_type] = filtered_out.get(doc_type, 0) + 1
            continue

        # Apply concept filter if provided
        if concept_filter:
            # Check if any of the document's concepts match the filter
            doc_concept_ids = meta.get('concept_ids', [])
            if not any(str(cid) in concept_filter for cid in doc_concept_ids):
                concept_filtered += 1
                continue

        result = {
            'type': doc_type,
            'id': meta['id'],
            'score': float(1 / (1 + distance)),  # Convert distance to similarity
            'content': doc_map.get(idx, ''),
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
    results = _blend_results(results_by_type, content_types, k)

    # Debug: count types in final results
    final_type_counts = {'tweet': 0, 'article': 0, 'paper': 0}
    for r in results:
        rtype = r.get('type', 'other')
        final_type_counts[rtype] = final_type_counts.get(rtype, 0) + 1

    logger.info(f"FILTERED OUT by content_types: tweets={filtered_out.get('tweet', 0)}, articles={filtered_out.get('article', 0)}, papers={filtered_out.get('paper', 0)}")
    if concept_filter:
        logger.info(f"FILTERED OUT by concept_filter: {concept_filtered}")
    logger.info(f"FINAL results by type: tweets={final_type_counts.get('tweet', 0)}, articles={final_type_counts.get('article', 0)}, papers={final_type_counts.get('paper', 0)}")

    # Show first few articles/papers if any
    for r in results[:5]:
        if r.get('type') in ['article', 'paper']:
            logger.info(f"  - [{r.get('type')}] {r.get('metadata', {}).get('title', 'N/A')[:60]}...")

    logger.info(f"Returning {len(results)} results after filtering (requested k={k})")
    return results


def _blend_results(results_by_type: Dict, content_types: Optional[List[str]], k: int) -> List[Dict]:
    results = []
    if content_types and len(content_types) > 1:
        # Quota phase: hand out slots round-robin, one per type per round, so a
        # small k can never starve the last type (the old block-wise allocation
        # gave e.g. k=5 over 3 types as 3/2/0). For k=10 over 3 types the
        # outcome is unchanged (3/3/3 + 1 pooled).
        num_types = len(content_types)
        min_per_type = max(3, k // (num_types * 2))  # At least 3, or k/(2*num_types)
        taken = {ctype: 0 for ctype in content_types}
        remaining_slots = k

        for _ in range(min_per_type):
            if remaining_slots <= 0:
                break
            for ctype in content_types:
                if remaining_slots <= 0:
                    break
                type_results = results_by_type.get(ctype, [])
                if taken[ctype] < len(type_results):
                    results.append(type_results[taken[ctype]])
                    taken[ctype] += 1
                    remaining_slots -= 1

        for ctype in content_types:
            logger.info(f"Added {taken[ctype]} {ctype}s (minimum quota)")

        # Then fill remaining slots by score from what's left
        if remaining_slots > 0:
            all_remaining = []
            for ctype in content_types:
                all_remaining.extend(results_by_type.get(ctype, [])[taken[ctype]:])
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

    return results
