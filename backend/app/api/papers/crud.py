"""
Paper CRUD route handlers.

Covers: list papers, get single paper, upload, and delete.
"""

from app.paths import PAPERS_DIR_REL
from .utils import (
    hashlib,
    datetime,
    timezone,
    Any,
    Dict,
    List,
    Optional,
    APIRouter,
    BackgroundTasks,
    File,
    HTTPException,
    Query,
    UploadFile,
    db,
    concept_service,
    logger,
    get_paper_by_id,
)
from app.repositories.paper_queries import (
    build_search_filter,
    build_concept_filter,
    build_author_filter,
    build_multi_value_filter,
    build_year_filter,
    build_special_filters,
    build_paper_type_filter,
)
from app.repositories import papers_crud as repo
from app.repositories.papers_crud import _format_paper_list_item, _resolve_concepts_for_papers  # noqa: F401 (moved)
from app.repositories import papers_crud_queries as queries

router = APIRouter()






@router.get("/")
def get_papers(
    page: int = Query(1, ge=1, le=10000),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    search_mode: Optional[str] = Query("title", regex="^(title|content|all)$"),
    concept_id: Optional[str] = None,
    concept_ids: Optional[List[str]] = Query(None),
    author: Optional[str] = None,
    conference: Optional[str] = None,
    conferences: Optional[List[str]] = Query(None),
    journal: Optional[str] = None,
    institution: Optional[str] = None,
    affiliations: Optional[List[str]] = Query(None),
    processor: Optional[str] = None,
    processors: Optional[List[str]] = Query(None),
    year: Optional[int] = None,
    years: Optional[List[int]] = Query(None),
    special_filter: Optional[str] = None,
    is_flagged: Optional[bool] = None,
    no_processor: Optional[bool] = None,
    no_year: Optional[bool] = None,
    no_conference: Optional[bool] = None,
    no_affiliation: Optional[bool] = None,
    no_annotations: Optional[bool] = None,
    no_mollick_summary: Optional[bool] = None,
    # Rating filters
    min_rating: Optional[int] = Query(None, ge=1, le=5, description="Minimum rating (1-5)"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="Exact rating (1-5)"),
    unrated_only: bool = Query(False, description="Show only unrated papers"),
    # Sort options
    sort_by: str = Query("created_at", description="Sort field: created_at, publication_date, title, rating"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    paper_type: str = Query("research", description="Paper type: research or review"),
) -> Dict[str, Any]:
    """Get papers with filtering and pagination from MongoDB"""
    return repo.get_papers(page=page, page_size=page_size, search=search, search_mode=search_mode, concept_id=concept_id, concept_ids=concept_ids, author=author, conference=conference, conferences=conferences, journal=journal, institution=institution, affiliations=affiliations, processor=processor, processors=processors, year=year, years=years, special_filter=special_filter, is_flagged=is_flagged, no_processor=no_processor, no_year=no_year, no_conference=no_conference, no_affiliation=no_affiliation, no_annotations=no_annotations, no_mollick_summary=no_mollick_summary, min_rating=min_rating, rating=rating, unrated_only=unrated_only, sort_by=sort_by, sort_order=sort_order, paper_type=paper_type)


@router.get("/{paper_id}")
def get_paper(paper_id: str) -> Dict[str, Any]:
    """Get a specific paper by ID from MongoDB"""

    paper = get_paper_by_id(paper_id)

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Get concepts from tag_instances collection
    paper_id = str(paper['_id'])
    sqlite_id = str(paper.get('old_sqlite_id', ''))

    tag_instances = list(queries.tag_instances_find__get_paper(paper_id, sqlite_id))

    concept_ids = list(set(ti['concept_id'] for ti in tag_instances))
    concepts_lookup = concept_service.get_concepts_by_ids(concept_ids)
    concepts = []
    for cid in concept_ids:
        concept = concepts_lookup.get(str(cid))
        if concept:
            concepts.append({
                'concept_id': str(cid),
                'display_name': concept.get('display_name'),
                'slug': concept.get('slug')
            })

    readability_metrics = paper.get('readability', {})

    return {
        'id': str(paper['_id']),
        'title': paper.get('title'),
        'abstract': paper.get('abstract'),
        'content': paper.get('content'),
        'authors': paper.get('authors', []),
        'authors_detailed': paper.get('authors_detailed', []),
        'sections': paper.get('sections', []),
        'references': paper.get('references', []),
        'publication_date': paper.get('publication_date'),
        'conference': paper.get('conference'),
        'journal': paper.get('journal'),
        'arxiv_id': paper.get('arxiv_id'),
        'doi': paper.get('doi'),
        'pdf_path': paper.get('pdf_path'),
        'pdf_url': paper.get('pdf_url'),
        'page_count': paper.get('page_count', 0),
        'word_count': paper.get('word_count', 0),
        'citation_count': paper.get('citation_count', 0),
        'concepts': concepts,
        'tags': [c['display_name'] for c in concepts],
        'is_processed': paper.get('processed', False),
        'processor': paper.get('processor_used'),
        'processed': paper.get('processed', False),
        'processor_used': paper.get('processor_used'),
        'processed_with_mineru': paper.get('processor_used') == 'mineru_service',
        'processed_with_marker': paper.get('processor_used') == 'marker_service',
        'is_flagged': paper.get('is_flagged', False),
        'snippets': paper.get('snippets', []),
        'analyses': paper.get('analyses', []),
        'repository': paper.get('repository'),
        'bibtex': paper.get('bibtex'),
        'dblp_key': paper.get('dblp_key'),
        'dblp_url': paper.get('dblp_url'),
        'created_at': paper.get('created_at').isoformat() if paper.get('created_at') and hasattr(paper.get('created_at'), 'isoformat') else paper.get('created_at'),
        'updated_at': paper.get('updated_at').isoformat() if paper.get('updated_at') and hasattr(paper.get('updated_at'), 'isoformat') else paper.get('updated_at'),
        'readability': readability_metrics,
        'paper_type': paper.get('paper_type', 'research'),
        'review_deadline': paper.get('review_deadline'),
        'review_decision': paper.get('review_decision'),
        'review_notes': paper.get('review_notes'),
        'review_confidence': paper.get('review_confidence'),
    }


@router.delete("/{paper_id}")
def delete_paper(paper_id: str) -> Dict[str, Any]:
    """Delete a paper and all associated data"""
    return repo.delete_paper(paper_id=paper_id)


@router.post("/upload")
async def upload_paper(
    background_tasks: BackgroundTasks,  # noqa: ARG001 - Reserved for future background processing
    file: UploadFile = File(...),
    paper_type: str = Query("research", description="Paper type: research or review"),
) -> Dict[str, Any]:
    """Upload and process a PDF research paper (MongoDB version)"""

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")

    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(contents).hexdigest()[:8]
        safe_filename = file.filename.replace(' ', '_').replace('.pdf', '')
        new_filename = f"{timestamp}_{file_hash}_{safe_filename}.pdf"

        pdf_dir = PAPERS_DIR_REL
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = pdf_dir / new_filename

        with open(pdf_path, "wb") as f:
            f.write(contents)

        title = file.filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')

        paper_doc = {
            "title": title,
            "paper_type": paper_type,
            "authors": "",
            "authors_detailed": [],
            "abstract": "PDF uploaded. Click 'Use Marker' or 'Use MinerU' button to extract content.",
            "content": "",
            "sections": [],
            "pdf_path": str(pdf_path),
            "processed": False,
            "processing_status": "not_started",
            "processor_used": None,
            "processed_at": None,
            "created_at": datetime.now(timezone.utc),
            "publication_date": None,
            "conference": "",
            "journal": "",
            "arxiv_id": "",
            "doi": ""
        }

        result = queries.papers_insert_one__upload_paper(paper_doc)
        paper_id = str(result.inserted_id)

        logger.info(f"Paper uploaded successfully: {paper_id} - {title}")

        return {
            "id": paper_id,
            "title": title,
            "message": "Paper uploaded successfully. Use 'Use Marker' or 'Use MinerU' button to extract content.",
            "extracted_sections": 0,
            "extracted_authors": 0
        }

    except Exception as e:
        logger.error(f"Error uploading paper: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading paper: {str(e)}")
