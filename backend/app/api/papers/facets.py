"""
Paper facets, statistics, and DBLP search route handlers.

Covers: get_facets (filter facets for papers dashboard), get_statistics
(paper collection overview), and search_dblp (DBLP bibliography search).
"""

from .utils import Any, Dict, List, Optional, APIRouter, Query

from app.repositories.paper_facet_pipelines import (
    build_author_pipeline,
    build_author_fallback_pipeline,
    build_year_pipeline,
    build_simple_field_pipeline,
    build_institution_pipeline,
    build_processor_pipeline,
    build_rating_pipeline,
    build_combined_counts_pipeline,
    build_no_affiliation_pipeline,
    extract_count,
    build_special_filters,
    build_paper_status,
    build_missing_data_counts,
    safe_object_ids_from_strings,
    build_rating_facet,
)

router = APIRouter()

from app.services.concept_only_tag_service import ConceptOnlyTagService
concept_service = ConceptOnlyTagService()
from app.repositories import paper_facets as repo


@router.get("/facets")
def get_facets(
    search: Optional[str] = None,
    concept_ids: Optional[List[str]] = Query(None),
    author: Optional[str] = None,
    conference: Optional[str] = None,
    conferences: Optional[List[str]] = Query(None),
    year: Optional[int] = None,
    years: Optional[List[int]] = Query(None),
    affiliation: Optional[str] = None,
    affiliations: Optional[List[str]] = Query(None),
    processor: Optional[str] = None,
    processors: Optional[List[str]] = Query(None),
    search_mode: Optional[str] = Query("title", regex="^(title|content|all)$"),
    paper_type: str = Query("research", description="Paper type: research or review"),
) -> Dict[str, Any]:
    """Get facets for filtering papers - facets update based on current filters"""
    return repo.get_facets(search=search, concept_ids=concept_ids, author=author, conference=conference, conferences=conferences, year=year, years=years, affiliation=affiliation, affiliations=affiliations, processor=processor, processors=processors, search_mode=search_mode, paper_type=paper_type, get_concepts_with_counts=concept_service.get_all_concepts_with_counts)


@router.get("/stats/overview")
def get_statistics(
    paper_type: str = Query("research", description="Paper type: research or review"),
) -> Dict[str, Any]:
    """Get paper statistics from MongoDB"""
    return repo.get_statistics(paper_type=paper_type, get_concepts_with_counts=concept_service.get_all_concepts_with_counts)
