from app.paths import ARTICLE_IMAGES
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import List, Optional, Dict
from bson import ObjectId
from pathlib import Path

from .utils import db
from .browse_helpers import (
    build_author_query_conditions,
    build_faceted_author_query_conditions,
    build_concept_id_filter,
    build_year_conditions,
    build_search_condition,
    merge_condition_into_query,
    build_sort_pipeline,
    resolve_author_for_article,
    resolve_author_for_single_article,
    get_article_concepts_and_tags,
    format_article_for_list,
    format_article_for_faceted,
    build_author_facets,
    build_concept_facets,
    build_year_facets,
)

router = APIRouter()


@router.get("/", response_model=List[Dict])
def get_articles(
    page: int = Query(1, ge=1, le=10000),
    page_size: int = Query(50, ge=1, le=200),
    author_id: Optional[str] = None,
    concept_id: Optional[str] = None,
    search: Optional[str] = None,
    search_mode: Optional[str] = Query("title", regex="^(title|content|all)$")
):
    # Build query
    query = {}

    if author_id:
        or_conditions = build_author_query_conditions(author_id)
        if or_conditions:
            query['$or'] = or_conditions

    if concept_id:
        query['concept_ids'] = concept_id

    if search:
        search_cond = build_search_condition(search, search_mode)
        if '$or' in search_cond:
            if '$and' in query:
                query['$and'].append(search_cond)
            elif query:
                query = {'$and': [query, search_cond]}
            else:
                query = search_cond
        else:
            query.update(search_cond)

    # Count total
    total = db.articles.count_documents(query)

    # Get articles with pagination
    skip = (page - 1) * page_size
    pipeline = build_sort_pipeline(query, skip, page_size)
    articles = list(db.articles.aggregate(pipeline))

    # Format response
    result = []
    for article in articles:
        author = resolve_author_for_article(article)
        concepts, tags = get_article_concepts_and_tags(article)
        result.append(format_article_for_list(article, author, concepts, tags))

    return result

@router.get("/faceted-search")
def faceted_search(
    page: int = Query(1, ge=1, le=10000),
    page_size: int = Query(50, ge=1, le=200),
    authors: Optional[List[str]] = Query(None),
    concept_ids: Optional[List[str]] = Query(None),
    years: Optional[List[int]] = Query(None),
    search: Optional[str] = None,
    search_mode: Optional[str] = Query("title", regex="^(title|content|all)$")
):
    # Build query
    query = {}

    if authors:
        or_conditions = build_faceted_author_query_conditions(authors)
        if or_conditions:
            query['$or'] = or_conditions

    if concept_ids:
        or_conditions = build_concept_id_filter(concept_ids)

        if or_conditions is None:
            # No articles with these concepts, return empty result
            return {
                "articles": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "facets": {
                    "authors": [],
                    "concepts": [],
                    "years": []
                }
            }

        if or_conditions:
            # Need to combine with existing query conditions
            if query:
                # Wrap existing conditions and new OR conditions in an AND
                new_query = {'$and': [query, {'$or': or_conditions}]}
                query = new_query
            else:
                query['$or'] = or_conditions

    if years:
        year_conditions = build_year_conditions(years)

        if year_conditions:
            if query:
                # Combine with existing query
                if '$and' in query:
                    query['$and'].append({'$or': year_conditions})
                else:
                    query = {'$and': [query, {'$or': year_conditions}]}
            else:
                query['$or'] = year_conditions

    if search:
        search_cond = build_search_condition(search, search_mode)
        query = merge_condition_into_query(query, search_cond)

    # Get total count
    total = db.articles.count_documents(query)

    # Get articles with pagination
    skip = (page - 1) * page_size
    pipeline = build_sort_pipeline(query, skip, page_size)
    articles = list(db.articles.aggregate(pipeline))

    # Build facets
    author_facets = build_author_facets(query)
    concept_facets = build_concept_facets()
    year_facets = build_year_facets(query)

    # Format articles
    result_articles = []
    for article in articles:
        author = resolve_author_for_article(article)
        concepts, tags = get_article_concepts_and_tags(article)
        result_articles.append(format_article_for_faceted(article, author, concepts, tags))

    return {
        'articles': result_articles,
        'facets': {
            'authors': author_facets,
            'concepts': concept_facets,
            'years': year_facets
        },
        'total': total,
        'page': page,
        'page_size': page_size
    }

@router.get("/{article_id}/images/{filename}")
def get_article_image(article_id: str, filename: str):
    # Construct the image path
    image_path = ARTICLE_IMAGES / filename

    # Security check: ensure the filename contains the article_id
    if not filename.startswith(f"{article_id}_"):
        raise HTTPException(status_code=403, detail="Invalid image request")

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    # Determine content type based on file extension
    ext = image_path.suffix.lower()
    content_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml'
    }

    media_type = content_types.get(ext, 'application/octet-stream')

    return FileResponse(image_path, media_type=media_type)

@router.delete("/{article_id}")
def delete_article(article_id: str):
    # Load the article first so tag instances for BOTH id variants
    # (Mongo _id and legacy old_sqlite_id) can be cleaned up.
    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
        article = None

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    db.articles.delete_one({'_id': article['_id']})

    # Delete associated tag instances for both id variants
    article_id_str = str(article['_id'])
    sqlite_id_str = str(article.get('old_sqlite_id', ''))
    db.tag_instances.delete_many({
        'content_type': 'article',
        '$or': [
            {'content_id': article_id_str},
            {'content_id': sqlite_id_str}
        ]
    })

    return {"message": "Article deleted successfully"}

@router.get("/{article_id}")
def get_article(article_id: str):
    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
        article = None

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Get author
    author_data = resolve_author_for_single_article(article)

    # Get concepts
    concepts, tags = get_article_concepts_and_tags(article)

    # Format response
    return {
        'id': str(article['_id']),
        'substack_id': article.get('substack_id'),
        'title': article.get('title'),
        'subtitle': article.get('subtitle'),
        'slug': article.get('slug'),
        'url': article.get('url'),
        'content_html': article.get('content_html'),
        'content_markdown': article.get('content_markdown', ''),
        'content': article.get('content_markdown', ''),
        'preview': article.get('preview'),
        'word_count': article.get('word_count', 0),
        'reading_time_minutes': article.get('reading_time_minutes', 0),
        'author': author_data,
        'published_at': article.get('published_at').isoformat() if article.get('published_at') else None,
        'collected_at': article.get('collected_at').isoformat() if article.get('collected_at') else None,
        'metrics': article.get('metrics', {}),
        'summary': article.get('summary'),
        'key_points': article.get('key_points', []),
        'topics': article.get('topics', []),
        'sentiment': article.get('sentiment'),
        'snippets': article.get('snippets', []),
        'concepts': concepts,
        'tags': tags,
        'processed': article.get('processed', False),
        'summarized': article.get('summarized', False)
    }
