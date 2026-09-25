"""
Books facet endpoints: filter options and statistics for the faceted browser.
"""

from fastapi import APIRouter

from .utils import List, Optional, Query, logging

router = APIRouter()

logger = logging.getLogger("app.api.books.facets")

from app.services.concept_only_tag_service import ConceptOnlyTagService
concept_service = ConceptOnlyTagService()
from app.repositories import book_facets as repo


@router.get("/facets")
def get_book_facets(
    search: Optional[str] = None,
    concept_ids: Optional[List[str]] = Query(None),
    author: Optional[str] = None,
    authors: Optional[List[str]] = Query(None),
    publisher: Optional[str] = None,
    publishers: Optional[List[str]] = Query(None),
    genre: Optional[str] = None,
    genres: Optional[List[str]] = Query(None),
    subject_area: Optional[str] = None,
    subject_areas: Optional[List[str]] = Query(None),
    language: Optional[str] = None,
    languages: Optional[List[str]] = Query(None),
    reading_difficulty: Optional[str] = None,
    difficulty_levels: Optional[List[str]] = Query(None),
    processor: Optional[str] = None,
    processors: Optional[List[str]] = Query(None),
    file_type: Optional[str] = None,
    file_types: Optional[List[str]] = Query(None),
    year: Optional[int] = None,
    years: Optional[List[int]] = Query(None),
    special_filter: Optional[str] = None,
    is_processed: Optional[bool] = None
):
    """Get all available facet values for filtering books, respecting current filters"""
    return repo.get_book_facets(search=search, concept_ids=concept_ids, author=author, authors=authors, publisher=publisher, publishers=publishers, genre=genre, genres=genres, subject_area=subject_area, subject_areas=subject_areas, language=language, languages=languages, reading_difficulty=reading_difficulty, difficulty_levels=difficulty_levels, processor=processor, processors=processors, file_type=file_type, file_types=file_types, year=year, years=years, special_filter=special_filter, is_processed=is_processed, get_concepts_with_counts=concept_service.get_all_concepts_with_counts)
