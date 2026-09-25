from app.paths import ARTICLE_IMAGES
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import List, Optional, Dict

from app.repositories.article_browse import (
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
from app.repositories import articles_browse as repo

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
    return repo.get_articles(page=page, page_size=page_size, author_id=author_id, concept_id=concept_id, search=search, search_mode=search_mode)

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
    return repo.faceted_search(page=page, page_size=page_size, authors=authors, concept_ids=concept_ids, years=years, search=search, search_mode=search_mode)

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
    return repo.delete_article(article_id=article_id)

@router.get("/{article_id}")
def get_article(article_id: str):
    return repo.get_article(article_id=article_id)
