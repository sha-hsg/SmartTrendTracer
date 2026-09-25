from fastapi import APIRouter, Query
from typing import List, Optional, Dict

from app.repositories.tweet_browse import (
    build_concept_id_filter,
    get_tweet_ids_for_concepts,
    build_search_conditions,
    apply_annotation_status_filter,
    build_facets,
    tweet_to_response_dict,
    build_hierarchy_tree,
)
from app.repositories import tweets_browse as repo

router = APIRouter()


@router.get("/", response_model=List[Dict])
def get_tweets(
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0, le=100000),
    with_media_only: bool = False,
    concept_id: Optional[str] = Query(None, description="Filter by concept ID"),
    include_concepts: bool = Query(True, description="Include full concept details")
):
    return repo.get_tweets(limit=limit, skip=skip, with_media_only=with_media_only, concept_id=concept_id, include_concepts=include_concepts)

@router.get("/faceted-search")
def faceted_search(
    page: int = Query(1, ge=1, le=10000),
    page_size: int = Query(50, ge=1, le=200),
    authors: Optional[List[str]] = Query(None),
    concept_ids: Optional[List[str]] = Query(None),
    years: Optional[List[int]] = Query(None),
    search: Optional[str] = None,
    exclude_retweets: bool = Query(False),
    annotation_status: Optional[str] = Query(None, description="Filter by annotation status: 'annotated' or 'not_annotated'")
):
    return repo.faceted_search(page=page, page_size=page_size, authors=authors, concept_ids=concept_ids, years=years, search=search, exclude_retweets=exclude_retweets, annotation_status=annotation_status)

@router.get("/hierarchy-facets")
def get_hierarchy_facets():
    return build_hierarchy_tree()

@router.get("/{tweet_id}")
def get_tweet(tweet_id: str, include_concepts: bool = True):
    return repo.get_tweet(tweet_id=tweet_id, include_concepts=include_concepts)
